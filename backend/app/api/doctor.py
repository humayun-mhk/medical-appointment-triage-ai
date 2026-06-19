from datetime import datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import require_doctor
from app.db.database import get_db
from app.models import Appointment, AppointmentStatus, Doctor, DoctorSlot, PatientProfile, SlotStatus, SymptomSession, User
from app.schemas import (
    DoctorAppointmentResponse,
    DoctorAvailabilityResponse,
    DoctorNotesRequest,
    DoctorStatusUpdateRequest,
    SlotCreateRequest,
)
from app.notifications.notification_service import notify_appointment_cancelled, notify_doctor_notes_added
from app.notifications.reminder_scheduler import cancel_pending_reminders
from app.security.audit_logger import log_security_event
from app.services import create_doctor_slot, doctor_appointment_to_response

router = APIRouter(prefix="/doctor", tags=["Doctor"])


def _get_doctor_profile(db: Session, current_user: User) -> Doctor:
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor profile not found")
    return doctor


def _get_owned_appointment(db: Session, doctor_id: int, appointment_id: int) -> Appointment:
    appointment = (
        db.query(Appointment)
        .options(
            joinedload(Appointment.patient).joinedload(PatientProfile.user),
            joinedload(Appointment.doctor).joinedload(Doctor.user),
            joinedload(Appointment.slot),
            joinedload(Appointment.triage_session).joinedload(SymptomSession.recommended_specialty),
        )
        .filter(Appointment.id == appointment_id, Appointment.doctor_id == doctor_id)
        .first()
    )
    if appointment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    return appointment


@router.get("/appointments", response_model=list[DoctorAppointmentResponse])
def doctor_appointments(
    request: Request,
    filter: str | None = Query(default=None, pattern="^(today|upcoming|completed|cancelled)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor),
):
    doctor = _get_doctor_profile(db, current_user)
    query = (
        db.query(Appointment)
        .options(
            joinedload(Appointment.patient).joinedload(PatientProfile.user),
            joinedload(Appointment.slot),
            joinedload(Appointment.triage_session).joinedload(SymptomSession.recommended_specialty),
        )
        .filter(Appointment.doctor_id == doctor.id)
        .join(DoctorSlot, Appointment.slot_id == DoctorSlot.id)
    )

    now = datetime.now(timezone.utc)
    if filter == "today":
        start = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)
        end = start + timedelta(days=1)
        query = query.filter(DoctorSlot.start_time >= start, DoctorSlot.start_time < end)
    elif filter == "upcoming":
        query = query.filter(
            DoctorSlot.start_time >= now,
            Appointment.status == AppointmentStatus.booked,
        )
    elif filter == "completed":
        query = query.filter(Appointment.status == AppointmentStatus.completed)
    elif filter == "cancelled":
        query = query.filter(Appointment.status == AppointmentStatus.cancelled)

    appointments = query.order_by(DoctorSlot.start_time.asc()).all()
    log_security_event(
        db,
        action="appointment_viewed",
        resource_type="appointment",
        request=request,
        user_id=current_user.id,
        metadata={"scope": "doctor_appointments", "filter": filter},
    )
    db.commit()
    return [doctor_appointment_to_response(appointment) for appointment in appointments]


@router.get("/appointments/{appointment_id}", response_model=DoctorAppointmentResponse)
def doctor_appointment_detail(
    appointment_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor),
):
    doctor = _get_doctor_profile(db, current_user)
    appointment = _get_owned_appointment(db, doctor.id, appointment_id)
    log_security_event(
        db,
        action="doctor_notes_viewed",
        resource_type="appointment",
        resource_id=appointment.id,
        request=request,
        user_id=current_user.id,
    )
    db.commit()
    return doctor_appointment_to_response(appointment)


@router.post("/appointments/{appointment_id}/notes", response_model=DoctorAppointmentResponse)
def update_notes(
    appointment_id: int,
    payload: DoctorNotesRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor),
):
    doctor = _get_doctor_profile(db, current_user)
    appointment = _get_owned_appointment(db, doctor.id, appointment_id)
    appointment.doctor_notes = payload.doctor_notes
    notify_doctor_notes_added(db, appointment)
    log_security_event(
        db,
        action="doctor_notes_added",
        resource_type="appointment",
        resource_id=appointment.id,
        request=request,
        user_id=current_user.id,
    )
    db.commit()
    db.refresh(appointment)
    return doctor_appointment_to_response(appointment)


@router.post("/appointments/{appointment_id}/status", response_model=DoctorAppointmentResponse)
def update_status(
    appointment_id: int,
    payload: DoctorStatusUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor),
):
    doctor = _get_doctor_profile(db, current_user)
    appointment = _get_owned_appointment(db, doctor.id, appointment_id)
    appointment.status = payload.status
    if payload.status == AppointmentStatus.cancelled and appointment.slot.status == SlotStatus.booked:
        appointment.slot.status = SlotStatus.available
        cancel_pending_reminders(appointment.id, db)
        notify_appointment_cancelled(db, appointment)
    log_security_event(
        db,
        action="appointment_status_updated",
        resource_type="appointment",
        resource_id=appointment.id,
        request=request,
        user_id=current_user.id,
        metadata={"status": payload.status.value},
    )
    db.commit()
    db.refresh(appointment)
    return doctor_appointment_to_response(appointment)


@router.get("/availability", response_model=list[DoctorAvailabilityResponse])
def get_availability(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor),
):
    doctor = _get_doctor_profile(db, current_user)
    return (
        db.query(DoctorSlot)
        .filter(DoctorSlot.doctor_id == doctor.id)
        .order_by(DoctorSlot.start_time.asc())
        .all()
    )


@router.post("/availability", response_model=DoctorAvailabilityResponse, status_code=status.HTTP_201_CREATED)
def create_availability(
    payload: SlotCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor),
):
    doctor = _get_doctor_profile(db, current_user)
    return create_doctor_slot(db, doctor.id, payload.start_time, payload.end_time)
