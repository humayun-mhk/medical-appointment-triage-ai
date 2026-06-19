from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models import AppointmentStatus, SlotStatus


class MessageResponse(BaseModel):
    message: str


class SpecialtyResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserBrief(BaseModel):
    id: int
    full_name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class PatientBasicInfo(BaseModel):
    id: int
    user_id: int
    full_name: str
    email: str
    date_of_birth: str | None = None
    gender: str | None = None
    phone: str | None = None
    blood_group: str | None = None
    allergies: str | None = None
    chronic_conditions: str | None = None
    emergency_contact: str | None = None


class DoctorResponse(BaseModel):
    id: int
    user_id: int
    full_name: str
    email: str
    image_url: str | None = None
    specialty: SpecialtyResponse
    qualification: str
    experience_years: int
    bio: str | None = None
    consultation_fee: Decimal
    clinic_address: str
    rating: float = 4.5
    total_reviews: int = 0
    city: str | None = None
    is_available: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class SlotResponse(BaseModel):
    id: int
    doctor_id: int
    start_time: datetime
    end_time: datetime
    status: SlotStatus
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AppointmentResponse(BaseModel):
    id: int
    patient_id: int
    patient_name: str | None = None
    patient_email: str | None = None
    doctor_id: int
    slot_id: int
    status: AppointmentStatus
    symptoms: str | None = None
    patient_notes: str | None = None
    doctor_notes: str | None = None
    triage_session_id: int | None = None
    doctor_summary: str | None = None
    urgency_level: str | None = None
    red_flag_status: bool | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    doctor: DoctorResponse | None = None
    slot: SlotResponse | None = None

    model_config = ConfigDict(from_attributes=True)
