from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.db.database import SessionLocal
from app.models import Appointment, AppointmentStatus, Doctor, DoctorSlot, PatientProfile, ScheduledJob, ScheduledJobStatus
from app.notifications.notification_service import create_in_app_notification
from app.notifications.templates import appointment_reminder


def schedule_appointment_reminder(appointment_id: int, db: Session) -> None:
    appointment = db.query(Appointment).options(joinedload(Appointment.slot)).filter(Appointment.id == appointment_id).first()
    if appointment is None:
        return
    now = datetime.now(timezone.utc)
    reminder_times = [appointment.slot.start_time - timedelta(hours=24), appointment.slot.start_time - timedelta(hours=2)]
    for run_at in reminder_times:
        if run_at <= now:
            continue
        exists = (
            db.query(ScheduledJob)
            .filter(
                ScheduledJob.appointment_id == appointment_id,
                ScheduledJob.job_type == "appointment_reminder",
                ScheduledJob.run_at == run_at,
            )
            .first()
        )
        if not exists:
            db.add(ScheduledJob(job_type="appointment_reminder", appointment_id=appointment_id, run_at=run_at))
    db.flush()


def cancel_pending_reminders(appointment_id: int, db: Session) -> None:
    (
        db.query(ScheduledJob)
        .filter(
            ScheduledJob.appointment_id == appointment_id,
            ScheduledJob.job_type == "appointment_reminder",
            ScheduledJob.status == ScheduledJobStatus.pending,
        )
        .update({ScheduledJob.status: ScheduledJobStatus.cancelled}, synchronize_session=False)
    )
    db.flush()


def mark_job_completed(job_id: int, db: Session) -> None:
    job = db.get(ScheduledJob, job_id)
    if job:
        job.status = ScheduledJobStatus.completed
        db.flush()


def mark_job_failed(job_id: int, error: str, db: Session) -> None:
    job = db.get(ScheduledJob, job_id)
    if job:
        job.status = ScheduledJobStatus.failed
        job.attempts += 1
        job.last_error = error
        db.flush()


def send_due_reminders(db: Session) -> int:
    now = datetime.now(timezone.utc)
    jobs = (
        db.query(ScheduledJob)
        .options(
            joinedload(ScheduledJob.appointment).joinedload(Appointment.patient).joinedload(PatientProfile.user),
            joinedload(ScheduledJob.appointment).joinedload(Appointment.doctor).joinedload(Doctor.user),
            joinedload(ScheduledJob.appointment).joinedload(Appointment.slot),
        )
        .filter(ScheduledJob.status == ScheduledJobStatus.pending, ScheduledJob.run_at <= now)
        .all()
    )
    sent = 0
    for job in jobs:
        try:
            appointment = job.appointment
            if appointment is None or appointment.status != AppointmentStatus.booked:
                job.status = ScheduledJobStatus.cancelled
                continue
            subject, message = appointment_reminder(appointment)
            create_in_app_notification(db, appointment.patient.user_id, subject, message)
            create_in_app_notification(db, appointment.doctor.user_id, subject, message)
            job.status = ScheduledJobStatus.completed
            sent += 1
        except Exception as exc:
            job.status = ScheduledJobStatus.failed
            job.attempts += 1
            job.last_error = str(exc)
    db.flush()
    return sent


def start_scheduler() -> None:
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except Exception:
        return

    scheduler = BackgroundScheduler(timezone="UTC")

    def run_due_jobs():
        db = SessionLocal()
        try:
            send_due_reminders(db)
            db.commit()
        except SQLAlchemyError:
            db.rollback()
        finally:
            db.close()

    scheduler.add_job(run_due_jobs, "interval", minutes=5, id="appointment_reminders", replace_existing=True)
    scheduler.start()
