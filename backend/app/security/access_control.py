from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Appointment, Doctor, PatientProfile, SymptomSession, User, UserRole


def assert_patient_owns_appointment(appointment: Appointment, user: User) -> None:
    if user.role != UserRole.patient or appointment.patient.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden appointment access")


def assert_doctor_owns_appointment(appointment: Appointment, doctor: Doctor) -> None:
    if appointment.doctor_id != doctor.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden appointment access")


def assert_admin(user: User) -> None:
    if user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden role access")


def assert_triage_visible(db: Session, session: SymptomSession, user: User) -> None:
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


def doctor_can_view_patient(db: Session, doctor: Doctor, patient: PatientProfile) -> bool:
    return (
        db.query(Appointment)
        .filter(Appointment.doctor_id == doctor.id, Appointment.patient_id == patient.id)
        .first()
        is not None
    )
