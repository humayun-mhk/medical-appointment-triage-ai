from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.db.database import get_db
from app.models import HumanReviewCase, User
from app.review.review_service import assign_review_case, get_review_case, list_review_cases, update_review_status
from app.schemas import ReviewCaseAssignRequest, ReviewCaseResponse, ReviewCaseStatusRequest
from app.security.rate_limit import admin_rate_limit

router = APIRouter(prefix="/admin/review-cases", tags=["Human Review"], dependencies=[Depends(require_admin), Depends(admin_rate_limit)])


def _case_response(case: HumanReviewCase) -> dict:
    session = case.triage_session
    return {
        "id": case.id,
        "triage_session_id": case.triage_session_id,
        "patient_id": case.patient_id,
        "patient_name": case.patient.user.full_name,
        "raw_input": session.raw_input,
        "structured_symptoms": session.structured_symptoms or {},
        "urgency_level": session.urgency_level.value,
        "red_flag_status": session.red_flag_status,
        "ai_confidence": session.ai_confidence,
        "recommended_specialty": session.recommended_specialty.name if session.recommended_specialty else None,
        "reason": case.reason,
        "risk_level": case.risk_level,
        "status": case.status,
        "review_notes": case.review_notes,
        "assigned_admin_id": case.assigned_admin_id,
        "assigned_doctor_id": case.assigned_doctor_id,
        "created_at": case.created_at,
        "updated_at": case.updated_at,
        "resolved_at": case.resolved_at,
    }


@router.get("", response_model=list[ReviewCaseResponse])
def review_cases(
    status: str | None = Query(default=None),
    risk_level: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    cases = list_review_cases({"status": status, "risk_level": risk_level}, db)
    return [_case_response(case) for case in cases]


@router.get("/{case_id}", response_model=ReviewCaseResponse)
def review_case_detail(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return _case_response(get_review_case(case_id, db))


@router.patch("/{case_id}/assign", response_model=ReviewCaseResponse)
def assign_case(
    case_id: int,
    payload: ReviewCaseAssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    case = assign_review_case(case_id, db, payload.assigned_admin_id or current_user.id, payload.assigned_doctor_id)
    db.commit()
    return _case_response(get_review_case(case.id, db))


@router.patch("/{case_id}/status", response_model=ReviewCaseResponse)
def update_case_status(
    case_id: int,
    payload: ReviewCaseStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    case = update_review_status(case_id, payload.status.value, payload.review_notes, db)
    db.commit()
    return _case_response(get_review_case(case.id, db))
