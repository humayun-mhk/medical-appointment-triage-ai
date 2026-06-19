from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import NotificationChannel, NotificationStatus


class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    is_read: bool
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class NotificationLogResponse(BaseModel):
    id: int
    user_id: int | None = None
    appointment_id: int | None = None
    channel: NotificationChannel
    event_type: str
    recipient: str
    subject: str | None = None
    message_preview: str
    status: NotificationStatus
    provider: str
    error_message: str | None = None
    created_at: datetime | None = None
    sent_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class TestNotificationRequest(BaseModel):
    email: str | None = None
    phone: str | None = None
    channel: NotificationChannel
    message: str = Field(..., min_length=1, max_length=500)
