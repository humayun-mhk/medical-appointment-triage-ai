from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.ai.safety import medical_disclaimer
from app.ai.triage_orchestrator import session_to_result
from app.models import (
    Appointment,
    AppointmentStatus,
    Doctor,
    DoctorSlot,
    PatientProfile,
    SlotStatus,
    SymptomSession,
    TriageUrgency,
    User,
    UserRole,
)


def get_or_create_patient_profile(db: Session, user: User) -> PatientProfile:
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user.id).first()
    if profile is None:
        profile = PatientProfile(user_id=user.id)
        db.add(profile)
        db.flush()
    return profile


def get_patient_profile_or_404(db: Session, user: User) -> PatientProfile:
    return get_or_create_patient_profile(db, user)


def create_symptom_session(db: Session, patient_id: int, raw_input: str) -> SymptomSession:
    cleaned = (raw_input or "").strip()
    if not cleaned:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="raw_input is required")
    if len(cleaned) > 3000:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="raw_input is too long")
    session = SymptomSession(
        patient_id=patient_id,
        raw_input=cleaned,
        structured_symptoms={},
        urgency_level=TriageUrgency.routine,
        safety_message=medical_disclaimer(),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session_with_details(db: Session, session_id: int) -> SymptomSession:
    session = (
        db.query(SymptomSession)
        .options(
            joinedload(SymptomSession.patient).joinedload(PatientProfile.user),
            joinedload(SymptomSession.recommended_specialty),
            joinedload(SymptomSession.secondary_specialty),
            joinedload(SymptomSession.audit_logs),
        )
        .filter(SymptomSession.id == session_id)
        .first()
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Triage session not found")
    return session


def ensure_session_visible_to_user(db: Session, session: SymptomSession, user: User) -> None:
    if user.role == UserRole.admin:
        return
    if user.role == UserRole.patient and session.patient.user_id == user.id:
        return
    if user.role == UserRole.doctor:
        linked = (
            db.query(Appointment)
            .join(Doctor, Appointment.doctor_id == Doctor.id)
            .filter(Appointment.triage_session_id == session.id, Doctor.user_id == user.id)
            .first()
        )
        if linked:
            return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden triage access")


def ensure_patient_owns_session(session: SymptomSession, profile: PatientProfile) -> None:
    if session.patient_id != profile.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden triage access")


def session_detail_response(session: SymptomSession) -> dict:
    return session_to_result(session)


def book_from_triage(
    db: Session,
    profile: PatientProfile,
    session: SymptomSession,
    doctor_id: int,
    slot_id: int,
    patient_notes: str | None,
    confirm_manual_override: bool = False,
) -> Appointment:
    ensure_patient_owns_session(session, profile)
    slot = db.query(DoctorSlot).filter(DoctorSlot.id == slot_id).with_for_update().first()
    if slot is None or slot.doctor_id != doctor_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")
    if slot.status != SlotStatus.available:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slot is not available")

    doctor = db.get(Doctor, doctor_id)
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

    allowed_specialties = {session.recommended_specialty_id, session.secondary_specialty_id}
    if doctor.specialty_id not in allowed_specialties and not confirm_manual_override:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor does not match the recommended specialty. Confirm manual override to continue.",
        )

    slot.status = SlotStatus.booked
    symptoms = ", ".join((session.structured_symptoms or {}).get("main_symptoms", [])) or session.raw_input[:500]
    appointment = Appointment(
        patient_id=profile.id,
        doctor_id=doctor_id,
        slot_id=slot_id,
        symptoms=symptoms,
        patient_notes=patient_notes,
        status=AppointmentStatus.booked,
        triage_session_id=session.id,
        doctor_summary=session.doctor_summary,
    )
    db.add(appointment)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slot is already booked")
    return (
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
