import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class NotificationChannel(str, enum.Enum):
    email = "email"
    sms = "sms"
    whatsapp = "whatsapp"
    in_app = "in_app"


class NotificationStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True, index=True)
    channel = Column(Enum(NotificationChannel, name="notification_channel"), nullable=False, index=True)
    event_type = Column(String(120), nullable=False, index=True)
    recipient = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=True)
    message_preview = Column(Text, nullable=False)
    status = Column(Enum(NotificationStatus, name="notification_status"), default=NotificationStatus.pending, nullable=False, index=True)
    provider = Column(String(80), nullable=False, default="console")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User")
    appointment = relationship("Appointment")

    __table_args__ = (
        Index("ix_notification_logs_channel_status", "channel", "status"),
        Index("ix_notification_logs_event_created", "event_type", "created_at"),
    )
