import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class TriageUrgency(str, enum.Enum):
    routine = "routine"
    soon = "soon"
    urgent = "urgent"
    emergency = "emergency"


class SymptomSession(Base):
    __tablename__ = "symptom_sessions"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    raw_input = Column(Text, nullable=False)
    structured_symptoms = Column(JSONB, nullable=False, default=dict)
    red_flag_status = Column(Boolean, default=False, nullable=False)
    urgency_level = Column(
        Enum(TriageUrgency, name="triage_urgency"),
        default=TriageUrgency.routine,
        nullable=False,
        index=True,
    )
    recommended_specialty_id = Column(Integer, ForeignKey("specialties.id"), nullable=True, index=True)
    secondary_specialty_id = Column(Integer, ForeignKey("specialties.id"), nullable=True)
    ai_confidence = Column(Float, nullable=True)
    ai_reason = Column(Text, nullable=True)
    doctor_summary = Column(Text, nullable=True)
    safety_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    patient = relationship("PatientProfile", back_populates="symptom_sessions")
    recommended_specialty = relationship("Specialty", foreign_keys=[recommended_specialty_id])
    secondary_specialty = relationship("Specialty", foreign_keys=[secondary_specialty_id])
    audit_logs = relationship("AIAuditLog", back_populates="session", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="triage_session")


class AIAuditLog(Base):
    __tablename__ = "ai_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("symptom_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_name = Column(String(120), nullable=False, index=True)
    input_payload = Column(JSONB, nullable=False, default=dict)
    output_payload = Column(JSONB, nullable=False, default=dict)
    safety_flags = Column(JSONB, nullable=False, default=dict)
    model_name = Column(String(120), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("SymptomSession", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_ai_audit_logs_session_agent", "session_id", "agent_name"),
    )
