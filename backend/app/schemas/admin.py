from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models import AppointmentStatus
from app.schemas.common import DoctorResponse, SpecialtyResponse
from app.utils.email_validation import validate_common_email_domain


class SpecialtyCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    description: str | None = None


class DoctorCreateRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    specialty_id: int
    qualification: str = Field(..., min_length=2, max_length=255)
    experience_years: int = Field(..., ge=0, le=80)
    bio: str | None = None
    consultation_fee: Decimal = Field(..., ge=0)
    clinic_address: str = Field(..., min_length=2)
    city: str | None = Field(default=None, max_length=120)

    @field_validator("email")
    @classmethod
    def validate_email_domain(cls, value: EmailStr) -> str:
        return validate_common_email_domain(str(value))


class DoctorUpdateRequest(BaseModel):
    specialty_id: int | None = None
    qualification: str | None = Field(default=None, max_length=255)
    experience_years: int | None = Field(default=None, ge=0, le=80)
    bio: str | None = None
    consultation_fee: Decimal | None = Field(default=None, ge=0)
    clinic_address: str | None = None
    city: str | None = Field(default=None, max_length=120)
    rating: float | None = Field(default=None, ge=0, le=5)
    total_reviews: int | None = Field(default=None, ge=0)
    is_available: bool | None = None


class AdminSlotCreateRequest(BaseModel):
    doctor_id: int
    start_time: datetime
    end_time: datetime


class AdminPatientResponse(BaseModel):
    id: int
    user_id: int
    full_name: str
    email: str
    phone: str | None = None
    gender: str | None = None
    blood_group: str | None = None
    date_of_birth: date | None = None


class AdminAppointmentResponse(BaseModel):
    id: int
    patient_name: str
    doctor_name: str
    specialty: str
    start_time: datetime
    end_time: datetime
    status: AppointmentStatus
    symptoms: str | None = None
    urgency_level: str | None = None
    red_flag_status: bool | None = None
    triage_session_id: int | None = None


class DashboardStatsResponse(BaseModel):
    total_patients: int
    total_doctors: int
    total_appointments: int
    todays_appointments: int
    completed_appointments: int
    cancelled_appointments: int
    available_slots: int


class AdminDoctorResponse(DoctorResponse):
    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "AdminAppointmentResponse",
    "AdminDoctorResponse",
    "AdminPatientResponse",
    "AdminSlotCreateRequest",
    "DashboardStatsResponse",
    "DoctorCreateRequest",
    "DoctorUpdateRequest",
    "SpecialtyCreateRequest",
    "SpecialtyResponse",
]
