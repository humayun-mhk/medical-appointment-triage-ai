from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_admin
from app.db.database import get_db
from app.models import Notification, NotificationChannel, NotificationLog, NotificationStatus, User
from app.notifications.notification_service import send_notification
from app.schemas import NotificationLogResponse, NotificationResponse, TestNotificationRequest
from app.security.rate_limit import admin_rate_limit

router = APIRouter(tags=["Notifications"])


@router.get("/notifications/my", response_model=list[NotificationResponse])
def my_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )


@router.patch("/notifications/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == current_user.id)
        .first()
    )
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


@router.patch("/notifications/read-all")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(Notification).filter(Notification.user_id == current_user.id, Notification.is_read.is_(False)).update(
        {Notification.is_read: True},
        synchronize_session=False,
    )
    db.commit()
    return {"message": "Notifications marked as read"}


@router.get("/admin/notification-logs", response_model=list[NotificationLogResponse])
def admin_notification_logs(
    channel: NotificationChannel | None = Query(default=None),
    status_filter: NotificationStatus | None = Query(default=None, alias="status"),
    event_type: str | None = Query(default=None),
    selected_date: date | None = Query(default=None, alias="date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    _limit: None = Depends(admin_rate_limit),
):
    query = db.query(NotificationLog).order_by(NotificationLog.created_at.desc())
    if channel:
        query = query.filter(NotificationLog.channel == channel)
    if status_filter:
        query = query.filter(NotificationLog.status == status_filter)
    if event_type:
        query = query.filter(NotificationLog.event_type == event_type)
    if selected_date:
        query = query.filter(func.date(NotificationLog.created_at) == selected_date)
    return query.all()


@router.get("/admin/notification-logs/{log_id}", response_model=NotificationLogResponse)
def admin_notification_log_detail(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    _limit: None = Depends(admin_rate_limit),
):
    log = db.get(NotificationLog, log_id)
    if log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification log not found")
    return log


@router.post("/admin/notifications/test", response_model=NotificationLogResponse)
def send_test_notification(
    payload: TestNotificationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    _limit: None = Depends(admin_rate_limit),
):
    if payload.channel == NotificationChannel.email:
        recipient = payload.email
    elif payload.channel in {NotificationChannel.sms, NotificationChannel.whatsapp}:
        recipient = payload.phone
    else:
        recipient = f"user:{current_user.id}"
    if not recipient:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Recipient is required")
    log = send_notification(
        db,
        user_id=current_user.id,
        appointment_id=None,
        channel=payload.channel,
        event_type="test_notification",
        recipient=recipient,
        subject="Test notification",
        message=payload.message,
    )
    db.commit()
    db.refresh(log)
    return log
