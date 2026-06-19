from decimal import Decimal

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    specialty_id = Column(Integer, ForeignKey("specialties.id"), nullable=False, index=True)
    qualification = Column(String(255), nullable=False)
    experience_years = Column(Integer, nullable=False, default=0)
    bio = Column(Text, nullable=True)
    consultation_fee = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    clinic_address = Column(Text, nullable=False)
    rating = Column(Float, default=4.5, nullable=False)
    total_reviews = Column(Integer, default=0, nullable=False)
    city = Column(String(120), nullable=True)
    is_available = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="doctor_profile")
    specialty = relationship("Specialty", back_populates="doctors")
    slots = relationship("DoctorSlot", back_populates="doctor", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="doctor")
