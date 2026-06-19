from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy import case, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import require_patient
from app.db.database import get_db
from app.models import (
    Appointment,
    AppointmentStatus,
    Doctor,
    DoctorSlot,
    PatientProfile,
    SlotStatus,
    User,
)
from app.schemas import (
    AppointmentBookRequest,
    AppointmentResponse,
    MessageResponse,
    PatientProfileCreate,
    PatientProfileResponse,
)
from app.notifications.appointment_tasks import send_appointment_booked_notifications
from app.notifications.notification_service import notify_appointment_cancelled
from app.notifications.reminder_scheduler import cancel_pending_reminders
from app.security.audit_logger import log_security_event
from app.services import doctor_to_response, get_or_create_patient_profile

router = APIRouter(tags=["Patient"])


def _get_current_patient_profile(db: Session, user: User) -> PatientProfile:
    return get_or_create_patient_profile(db, user)


def _appointment_response(appointment: Appointment) -> dict:
    return {
        "id": appointment.id,
        "patient_id": appointment.patient_id,
        "patient_name": appointment.patient.user.full_name if appointment.patient and appointment.patient.user else None,
        "patient_email": appointment.patient.user.email if appointment.patient and appointment.patient.user else None,
        "doctor_id": appointment.doctor_id,
        "slot_id": appointment.slot_id,
        "status": appointment.status,
        "symptoms": appointment.symptoms,
        "patient_notes": appointment.patient_notes,
        "doctor_notes": appointment.doctor_notes,
        "triage_session_id": appointment.triage_session_id,
        "doctor_summary": appointment.doctor_summary,
        "urgency_level": appointment.triage_session.urgency_level.value if appointment.triage_session else None,
        "red_flag_status": appointment.triage_session.red_flag_status if appointment.triage_session else None,
        "created_at": appointment.created_at,
        "updated_at": appointment.updated_at,
        "doctor": doctor_to_response(appointment.doctor),
        "slot": appointment.slot,
    }


@router.post("/patients/profile", response_model=PatientProfileResponse)
def upsert_profile(
    payload: PatientProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient),
):
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == current_user.id).first()
    values = payload.model_dump()
    if profile:
        for key, value in values.items():
            setattr(profile, key, value)
    else:
        profile = PatientProfile(user_id=current_user.id, **values)
        db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/patients/profile", response_model=PatientProfileResponse)
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient),
):
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == current_user.id).first()
    if profile is None:
        profile = PatientProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.get("/patients/dashboard")
def patient_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient),
):
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == current_user.id).first()
    if profile is None:
        return {
            "stats": {
                "upcoming": 0,
                "total": 0,
                "cancelled": 0,
                "completed": 0,
            },
            "upcoming_appointments": [],
        }

    now = datetime.now(timezone.utc)
    stats_row = (
        db.query(
            func.count(Appointment.id).label("total"),
            func.coalesce(
                func.sum(case((Appointment.status == AppointmentStatus.cancelled, 1), else_=0)),
                0,
            ).label("cancelled"),
            func.coalesce(
                func.sum(case((Appointment.status == AppointmentStatus.completed, 1), else_=0)),
                0,
            ).label("completed"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            (Appointment.status == AppointmentStatus.booked)
                            & (DoctorSlot.start_time >= now),
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("upcoming"),
        )
        .select_from(Appointment)
        .join(DoctorSlot, Appointment.slot_id == DoctorSlot.id)
        .filter(Appointment.patient_id == profile.id)
        .one()
    )

    upcoming_appointments = []
    if stats_row.upcoming:
        upcoming_appointments = (
            db.query(Appointment)
            .options(
                joinedload(Appointment.patient).joinedload(PatientProfile.user),
                joinedload(Appointment.doctor).joinedload(Doctor.user),
                joinedload(Appointment.doctor).joinedload(Doctor.specialty),
                joinedload(Appointment.slot),
                joinedload(Appointment.triage_session),
            )
            .filter(
                Appointment.patient_id == profile.id,
                Appointment.status == AppointmentStatus.booked,
            )
            .join(DoctorSlot, Appointment.slot_id == DoctorSlot.id)
            .filter(DoctorSlot.start_time >= now)
            .order_by(DoctorSlot.start_time.asc())
            .limit(5)
            .all()
        )
    return {
        "stats": {
            "upcoming": stats_row.upcoming,
            "total": stats_row.total,
            "cancelled": stats_row.cancelled,
            "completed": stats_row.completed,
        },
        "upcoming_appointments": [_appointment_response(appointment) for appointment in upcoming_appointments],
    }


@router.post("/appointments/book", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def book_appointment(
    payload: AppointmentBookRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient),
):
    profile = _get_current_patient_profile(db, current_user)
    slot = (
        db.query(DoctorSlot)
        .filter(DoctorSlot.id == payload.slot_id)
        .with_for_update()
        .first()
    )
    if slot is None or slot.doctor_id != payload.doctor_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")
    if slot.status != SlotStatus.available:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slot is not available")

    existing = db.query(Appointment).filter(Appointment.slot_id == payload.slot_id).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slot is already booked")

    slot.status = SlotStatus.booked
    appointment = Appointment(
        patient_id=profile.id,
        doctor_id=payload.doctor_id,
        slot_id=slot.id,
        symptoms=payload.symptoms,
        patient_notes=payload.patient_notes,
        status=AppointmentStatus.booked,
    )
    db.add(appointment)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slot is already booked")

    appointment = (
        db.query(Appointment)
        .options(
            joinedload(Appointment.patient).joinedload(PatientProfile.user),
            joinedload(Appointment.doctor).joinedload(Doctor.user),
            joinedload(Appointment.doctor).joinedload(Doctor.specialty),
            joinedload(Appointment.slot),
            joinedload(Appointment.triage_session),
        )
        .filter(Appointment.id == appointment.id)
        .first()
    )
    response_payload = _appointment_response(appointment)
    log_security_event(
        db,
        action="appointment_booked",
        resource_type="appointment",
        resource_id=appointment.id,
        request=request,
        user_id=current_user.id,
        metadata={"doctor_id": appointment.doctor_id, "slot_id": appointment.slot_id},
    )
    db.commit()
    background_tasks.add_task(send_appointment_booked_notifications, appointment.id)
    return response_payload


@router.get("/appointments/my", response_model=list[AppointmentResponse])
def my_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient),
):
    profile = _get_current_patient_profile(db, current_user)
    appointments = (
        db.query(Appointment)
        .options(
            joinedload(Appointment.patient).joinedload(PatientProfile.user),
            joinedload(Appointment.doctor).joinedload(Doctor.user),
            joinedload(Appointment.doctor).joinedload(Doctor.specialty),
            joinedload(Appointment.slot),
            joinedload(Appointment.triage_session),
        )
        .filter(Appointment.patient_id == profile.id)
        .join(DoctorSlot, Appointment.slot_id == DoctorSlot.id)
        .order_by(DoctorSlot.start_time.desc())
        .all()
    )
    return [_appointment_response(appointment) for appointment in appointments]


@router.post("/appointments/{appointment_id}/cancel", response_model=MessageResponse)
def cancel_appointment(
    appointment_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient),
):
    profile = _get_current_patient_profile(db, current_user)
    appointment = (
        db.query(Appointment)
        .options(
            joinedload(Appointment.slot),
            joinedload(Appointment.patient).joinedload(PatientProfile.user),
            joinedload(Appointment.doctor).joinedload(Doctor.user),
        )
        .filter(Appointment.id == appointment_id, Appointment.patient_id == profile.id)
        .first()
    )
    if appointment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    if appointment.status != AppointmentStatus.booked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only booked appointments can be cancelled",
        )
    appointment.status = AppointmentStatus.cancelled
    appointment.slot.status = SlotStatus.available
    cancel_pending_reminders(appointment.id, db)
    notify_appointment_cancelled(db, appointment)
    log_security_event(
        db,
        action="appointment_cancelled",
        resource_type="appointment",
        resource_id=appointment.id,
        request=request,
        user_id=current_user.id,
        metadata={"actor": "patient"},
    )
    db.commit()
    return {"message": "Appointment cancelled successfully"}
