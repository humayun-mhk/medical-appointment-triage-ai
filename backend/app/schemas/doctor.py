from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models import AppointmentStatus
from app.schemas.common import PatientBasicInfo, SlotResponse


class DoctorAppointmentResponse(BaseModel):
    appointment_id: int
    patient: PatientBasicInfo
    symptoms: str | None = None
    patient_notes: str | None = None
    doctor_notes: str | None = None
    doctor_summary: str | None = None
    triage_session_id: int | None = None
    urgency_level: str | None = None
    red_flag_status: bool | None = None
    structured_symptoms: dict | None = None
    recommended_specialty: str | None = None
    ai_confidence: float | None = None
    slot_start_time: datetime
    slot_end_time: datetime
    status: AppointmentStatus


class DoctorNotesRequest(BaseModel):
    doctor_notes: str = Field(..., min_length=1, max_length=4000)


class DoctorStatusUpdateRequest(BaseModel):
    status: AppointmentStatus

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: AppointmentStatus) -> AppointmentStatus:
        allowed = {
            AppointmentStatus.completed,
            AppointmentStatus.no_show,
            AppointmentStatus.cancelled,
        }
        if value not in allowed:
            raise ValueError("Status must be completed, no_show, or cancelled")
        return value


class SlotCreateRequest(BaseModel):
    start_time: datetime
    end_time: datetime


class DoctorAvailabilityResponse(SlotResponse):
    pass
