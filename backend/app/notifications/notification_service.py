from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Notification, NotificationChannel, NotificationLog, NotificationStatus, User, UserRole
from app.notifications.email_service import send_email
from app.notifications.sms_service import send_sms
from app.notifications.templates import (
    appointment_booked_doctor,
    appointment_booked_patient,
    appointment_booked_patient_html,
    appointment_cancelled,
    doctor_notes_added,
    emergency_warning,
    review_case_created,
)
from app.notifications.whatsapp_service import send_whatsapp
from app.security.pii_masking import mask_email, mask_phone


def create_in_app_notification(db: Session, user_id: int, title: str, message: str) -> Notification:
    notification = Notification(user_id=user_id, title=title, message=message)
    db.add(notification)
    db.add(
        NotificationLog(
            user_id=user_id,
            channel=NotificationChannel.in_app,
            event_type=title.lower().replace(" ", "_"),
            recipient=f"user:{user_id}",
            subject=title,
            message_preview=message[:500],
            status=NotificationStatus.sent,
            provider="in_app",
            sent_at=datetime.now(timezone.utc),
        )
    )
    db.flush()
    return notification


def send_notification(
    db: Session,
    *,
    user_id: int | None,
    appointment_id: int | None,
    channel: NotificationChannel,
    event_type: str,
    recipient: str,
    subject: str | None,
    message: str,
    html_message: str | None = None,
) -> NotificationLog:
    if channel == NotificationChannel.email:
        result = send_email(recipient, subject or "Healthcare notification", message, html_message)
        masked_recipient = mask_email(recipient)
    elif channel == NotificationChannel.sms:
        result = send_sms(recipient, message)
        masked_recipient = mask_phone(recipient)
    elif channel == NotificationChannel.whatsapp:
        result = send_whatsapp(recipient, message)
        masked_recipient = mask_phone(recipient)
    else:
        print(f"[in-app fallback] {recipient}: {subject} {message}")
        result = {"status": "sent", "provider": "console", "error": None}
        masked_recipient = recipient

    log = NotificationLog(
        user_id=user_id,
        appointment_id=appointment_id,
        channel=channel,
        event_type=event_type,
        recipient=masked_recipient,
        subject=subject,
        message_preview=message[:500],
        status=NotificationStatus(result["status"]),
        provider=result["provider"],
        error_message=result["error"],
        sent_at=datetime.now(timezone.utc) if result["status"] == "sent" else None,
    )
    db.add(log)
    db.flush()
    return log


def notify_appointment_booked(db: Session, appointment) -> None:
    patient_subject, patient_message = appointment_booked_patient(appointment)
    patient_html = appointment_booked_patient_html(appointment)
    doctor_subject, doctor_message = appointment_booked_doctor(appointment)
    create_in_app_notification(db, appointment.patient.user_id, patient_subject, patient_message)
    create_in_app_notification(db, appointment.doctor.user_id, doctor_subject, doctor_message)
    send_notification(
        db,
        user_id=appointment.patient.user_id,
        appointment_id=appointment.id,
        channel=NotificationChannel.email,
        event_type="appointment_booked_patient",
        recipient=appointment.patient.user.email,
        subject=patient_subject,
        message=patient_message,
        html_message=patient_html,
    )
    send_notification(
        db,
        user_id=appointment.doctor.user_id,
        appointment_id=appointment.id,
        channel=NotificationChannel.email,
        event_type="appointment_booked_doctor",
        recipient=appointment.doctor.user.email,
        subject=doctor_subject,
        message=doctor_message,
    )


def notify_appointment_cancelled(db: Session, appointment) -> None:
    subject, message = appointment_cancelled(appointment)
    create_in_app_notification(db, appointment.patient.user_id, subject, message)
    create_in_app_notification(db, appointment.doctor.user_id, subject, message)


def notify_emergency_warning(db: Session, user_id: int, message: str) -> None:
    subject, body = emergency_warning(message)
    create_in_app_notification(db, user_id, subject, body)


def notify_review_case_created(db: Session, case) -> None:
    subject, message = review_case_created(case)
    admins = db.query(User).filter(User.role == UserRole.admin, User.is_active.is_(True)).all()
    for admin in admins:
        create_in_app_notification(db, admin.id, subject, message)


def notify_doctor_notes_added(db: Session, appointment) -> None:
    subject, message = doctor_notes_added(appointment)
    create_in_app_notification(db, appointment.patient.user_id, subject, message)
