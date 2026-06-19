import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class ReviewRiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ReviewStatus(str, enum.Enum):
    pending = "pending"
    in_review = "in_review"
    resolved = "resolved"
    dismissed = "dismissed"


class HumanReviewCase(Base):
    __tablename__ = "human_review_cases"

    id = Column(Integer, primary_key=True, index=True)
    triage_session_id = Column(Integer, ForeignKey("symptom_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_admin_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="SET NULL"), nullable=True, index=True)
    reason = Column(Text, nullable=False)
    risk_level = Column(Enum(ReviewRiskLevel, name="review_risk_level"), default=ReviewRiskLevel.medium, nullable=False, index=True)
    status = Column(Enum(ReviewStatus, name="review_status"), default=ReviewStatus.pending, nullable=False, index=True)
    review_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    triage_session = relationship("SymptomSession")
    patient = relationship("PatientProfile")
    assigned_admin = relationship("User", foreign_keys=[assigned_admin_id])
    assigned_doctor = relationship("Doctor", foreign_keys=[assigned_doctor_id])

    __table_args__ = (
        Index("ix_human_review_cases_session_status", "triage_session_id", "status"),
    )
