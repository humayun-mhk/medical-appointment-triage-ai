import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class AppointmentStatus(str, enum.Enum):
    booked = "booked"
    cancelled = "cancelled"
    completed = "completed"
    no_show = "no_show"


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True)
    slot_id = Column(Integer, ForeignKey("doctor_slots.id", ondelete="RESTRICT"), unique=True, nullable=False)
    status = Column(
        Enum(AppointmentStatus, name="appointment_status"),
        default=AppointmentStatus.booked,
        nullable=False,
        index=True,
    )
    patient_notes = Column(Text, nullable=True)
    symptoms = Column(Text, nullable=True)
    doctor_notes = Column(Text, nullable=True)
    triage_session_id = Column(Integer, ForeignKey("symptom_sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    doctor_summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    patient = relationship("PatientProfile", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
    slot = relationship("DoctorSlot", back_populates="appointment")
    triage_session = relationship("SymptomSession", back_populates="appointments")

    __table_args__ = (
        Index("ix_appointments_doctor_patient", "doctor_id", "patient_id"),
    )
