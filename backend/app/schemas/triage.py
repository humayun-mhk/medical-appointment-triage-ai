from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models import TriageUrgency
from app.schemas.common import AppointmentResponse, SpecialtyResponse


class TriageStartRequest(BaseModel):
    raw_input: str = Field(..., min_length=1, max_length=3000)


class TriageStartResponse(BaseModel):
    session_id: int
    message: str


class TriageAnalyzeRequest(BaseModel):
    session_id: int | None = None
    raw_input: str | None = Field(default=None, min_length=1, max_length=3000)


class StructuredSymptoms(BaseModel):
    main_symptoms: list[str] = []
    duration: str | None = None
    severity: int | None = Field(default=None, ge=1, le=10)
    body_parts: list[str] = []
    associated_symptoms: list[str] = []
    medications_mentioned: list[str] = []
    patient_age_group: str | None = None
    pregnancy_related: bool = False
    extra_notes: str | None = None


class TriageResultResponse(BaseModel):
    session_id: int
    raw_input: str
    structured_symptoms: dict[str, Any]
    red_flag_status: bool
    urgency_level: TriageUrgency
    recommended_specialty: SpecialtyResponse | None = None
    secondary_specialty: SpecialtyResponse | None = None
    ai_confidence: float | None = None
    ai_reason: str | None = None
    doctor_summary: str | None = None
    safety_message: str | None = None
    created_at: datetime | None = None


class RecommendedSlotResponse(BaseModel):
    slot_id: int
    start_time: datetime
    end_time: datetime


class RecommendedDoctorResponse(BaseModel):
    doctor_id: int
    doctor_name: str
    image_url: str | None = None
    specialty: str
    score: int
    score_breakdown: dict[str, int]
    next_available_slot: RecommendedSlotResponse
    consultation_fee: Decimal
    rating: float
    total_reviews: int
    clinic_address: str
    city: str | None = None
    reason: str
    emergency_warning: str | None = None


class BookFromTriageRequest(BaseModel):
    session_id: int
    doctor_id: int
    slot_id: int
    patient_notes: str | None = Field(default=None, max_length=2000)
    confirm_manual_override: bool = False


class AIAuditLogResponse(BaseModel):
    id: int
    session_id: int
    agent_name: str
    input_payload: dict[str, Any]
    output_payload: dict[str, Any]
    safety_flags: dict[str, Any]
    model_name: str | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AdminTriageSessionListResponse(BaseModel):
    session_id: int
    patient_name: str
    raw_input_preview: str
    urgency_level: TriageUrgency
    red_flag_status: bool
    recommended_specialty: str | None = None
    ai_confidence: float | None = None
    created_at: datetime | None = None


class AdminTriageSessionDetailResponse(TriageResultResponse):
    patient_name: str
    audit_logs: list[AIAuditLogResponse] = []


__all__ = [
    "AIAuditLogResponse",
    "AdminTriageSessionDetailResponse",
    "AdminTriageSessionListResponse",
    "AppointmentResponse",
    "BookFromTriageRequest",
    "RecommendedDoctorResponse",
    "RecommendedSlotResponse",
    "StructuredSymptoms",
    "TriageAnalyzeRequest",
    "TriageResultResponse",
    "TriageStartRequest",
    "TriageStartResponse",
]
