from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import AppointmentResponse, DoctorResponse, SlotResponse, SpecialtyResponse


class PatientProfileCreate(BaseModel):
    date_of_birth: date | None = None
    gender: str | None = Field(default=None, max_length=50)
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = None
    blood_group: str | None = Field(default=None, max_length=10)
    allergies: str | None = None
    chronic_conditions: str | None = None
    emergency_contact: str | None = Field(default=None, max_length=120)


class PatientProfileResponse(PatientProfileCreate):
    id: int
    user_id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AppointmentBookRequest(BaseModel):
    doctor_id: int
    slot_id: int
    symptoms: str | None = Field(default=None, max_length=2000)
    patient_notes: str | None = Field(default=None, max_length=2000)


__all__ = [
    "AppointmentBookRequest",
    "AppointmentResponse",
    "DoctorResponse",
    "PatientProfileCreate",
    "PatientProfileResponse",
    "SlotResponse",
    "SpecialtyResponse",
]
