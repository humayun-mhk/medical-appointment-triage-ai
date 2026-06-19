from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models import HumanReviewCase, PatientProfile, ReviewRiskLevel, ReviewStatus, SymptomSession
from app.notifications.notification_service import notify_review_case_created
from app.review.review_rules import should_flag_for_review


def _profile_payload(profile: PatientProfile | None) -> dict | None:
    if profile is None:
        return None
    return {
        "date_of_birth": profile.date_of_birth,
        "gender": profile.gender,
        "blood_group": profile.blood_group,
    }


def create_review_case_if_needed(triage_session_id: int, db: Session) -> HumanReviewCase | None:
    session = (
        db.query(SymptomSession)
        .options(joinedload(SymptomSession.patient))
        .filter(SymptomSession.id == triage_session_id)
        .first()
    )
    if session is None:
        return None
    existing = db.query(HumanReviewCase).filter(HumanReviewCase.triage_session_id == triage_session_id).first()
    if existing:
        return existing
    result = {
        "structured_symptoms": session.structured_symptoms or {},
        "urgency_level": session.urgency_level.value,
        "red_flag_status": session.red_flag_status,
        "ai_confidence": session.ai_confidence,
    }
    review = should_flag_for_review(result, _profile_payload(session.patient))
    if not review["flag_for_review"]:
        return None
    case = HumanReviewCase(
        triage_session_id=session.id,
        patient_id=session.patient_id,
        reason=review["reason"],
        risk_level=ReviewRiskLevel(review["risk_level"]),
        status=ReviewStatus.pending,
    )
    db.add(case)
    db.flush()
    notify_review_case_created(db, case)
    db.flush()
    return case


def list_review_cases(filters: dict, db: Session) -> list[HumanReviewCase]:
    query = (
        db.query(HumanReviewCase)
        .options(
            joinedload(HumanReviewCase.patient).joinedload(PatientProfile.user),
            joinedload(HumanReviewCase.triage_session).joinedload(SymptomSession.recommended_specialty),
        )
        .order_by(HumanReviewCase.created_at.desc())
    )
    if filters.get("status"):
        query = query.filter(HumanReviewCase.status == ReviewStatus(filters["status"]))
    if filters.get("risk_level"):
        query = query.filter(HumanReviewCase.risk_level == ReviewRiskLevel(filters["risk_level"]))
    return query.all()


def get_review_case(case_id: int, db: Session) -> HumanReviewCase:
    case = (
        db.query(HumanReviewCase)
        .options(
            joinedload(HumanReviewCase.patient).joinedload(PatientProfile.user),
            joinedload(HumanReviewCase.triage_session).joinedload(SymptomSession.recommended_specialty),
            joinedload(HumanReviewCase.assigned_admin),
            joinedload(HumanReviewCase.assigned_doctor),
        )
        .filter(HumanReviewCase.id == case_id)
        .first()
    )
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review case not found")
    return case


def assign_review_case(case_id: int, db: Session, admin_id: int | None = None, doctor_id: int | None = None) -> HumanReviewCase:
    case = get_review_case(case_id, db)
    case.assigned_admin_id = admin_id
    case.assigned_doctor_id = doctor_id
    case.status = ReviewStatus.in_review
    db.flush()
    return case


def update_review_status(case_id: int, status_value: str, notes: str | None, db: Session) -> HumanReviewCase:
    case = get_review_case(case_id, db)
    case.status = ReviewStatus(status_value)
    case.review_notes = notes
    if case.status in {ReviewStatus.resolved, ReviewStatus.dismissed}:
        case.resolved_at = datetime.now(timezone.utc)
    db.flush()
    return case
