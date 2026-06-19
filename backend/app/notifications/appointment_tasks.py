from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from app.db.database import SessionLocal
from app.models import Appointment, Doctor, PatientProfile
from app.notifications.notification_service import notify_appointment_booked
from app.notifications.reminder_scheduler import schedule_appointment_reminder


def send_appointment_booked_notifications(appointment_id: int) -> None:
    db = SessionLocal()
    try:
        appointment = (
            db.query(Appointment)
            .options(
                joinedload(Appointment.patient).joinedload(PatientProfile.user),
                joinedload(Appointment.doctor).joinedload(Doctor.user),
                joinedload(Appointment.doctor).joinedload(Doctor.specialty),
                joinedload(Appointment.slot),
                joinedload(Appointment.triage_session),
            )
            .filter(Appointment.id == appointment_id)
            .first()
        )
        if appointment is None:
            return

        notify_appointment_booked(db, appointment)
        schedule_appointment_reminder(appointment.id, db)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        print(f"[notification background task failed] appointment_id={appointment_id} error={exc}")
    finally:
        db.close()
