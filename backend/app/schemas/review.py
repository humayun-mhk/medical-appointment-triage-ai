from datetime import datetime

from pydantic import BaseModel, Field

from app.models import ReviewRiskLevel, ReviewStatus


class ReviewCaseAssignRequest(BaseModel):
    assigned_admin_id: int | None = None
    assigned_doctor_id: int | None = None


class ReviewCaseStatusRequest(BaseModel):
    status: ReviewStatus
    review_notes: str | None = Field(default=None, max_length=4000)


class ReviewCaseResponse(BaseModel):
    id: int
    triage_session_id: int
    patient_id: int
    patient_name: str
    raw_input: str
    structured_symptoms: dict
    urgency_level: str
    red_flag_status: bool
    ai_confidence: float | None = None
    recommended_specialty: str | None = None
    reason: str
    risk_level: ReviewRiskLevel
    status: ReviewStatus
    review_notes: str | None = None
    assigned_admin_id: int | None = None
    assigned_doctor_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    resolved_at: datetime | None = None
