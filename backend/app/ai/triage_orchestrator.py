from sqlalchemy.orm import Session, joinedload

from app.ai.doctor_summary_agent import generate_doctor_summary
from app.ai.red_flag_engine import evaluate_red_flags
from app.ai.safety import medical_disclaimer, safety_flags_for_text, validate_ai_response
from app.ai.specialty_router_agent import recommend_specialty
from app.ai.symptom_intake_agent import extract_symptoms
from app.core.config import settings
from app.models import AIAuditLog, SymptomSession, TriageUrgency


def _log_audit(
    db: Session,
    session_id: int,
    agent_name: str,
    input_payload: dict,
    output_payload: dict,
    safety_flags: dict | None = None,
    model_name: str | None = None,
) -> None:
    db.add(
        AIAuditLog(
            session_id=session_id,
            agent_name=agent_name,
            input_payload=input_payload,
            output_payload=output_payload,
            safety_flags=safety_flags or {},
            model_name=model_name or ("rule-based" if not settings.OPENAI_API_KEY else settings.AI_MODEL),
        )
    )
    db.flush()


def _validate_raw_input(raw_input: str) -> str:
    cleaned = (raw_input or "").strip()
    if not cleaned:
        raise ValueError("raw_input must not be empty")
    if len(cleaned) > 3000:
        raise ValueError("raw_input must be 3000 characters or fewer")
    return cleaned


def session_to_result(session: SymptomSession) -> dict:
    return {
        "session_id": session.id,
        "raw_input": session.raw_input,
        "structured_symptoms": session.structured_symptoms or {},
        "red_flag_status": session.red_flag_status,
        "urgency_level": session.urgency_level,
        "recommended_specialty": session.recommended_specialty,
        "secondary_specialty": session.secondary_specialty,
        "ai_confidence": session.ai_confidence,
        "ai_reason": session.ai_reason,
        "doctor_summary": session.doctor_summary,
        "safety_message": session.safety_message or medical_disclaimer(),
        "created_at": session.created_at,
    }


def run_triage_for_session(session: SymptomSession, db: Session) -> dict:
    raw_input = _validate_raw_input(session.raw_input)

    structured = extract_symptoms(raw_input)
    session.structured_symptoms = structured
    _log_audit(
        db,
        session.id,
        "Symptom Intake Agent",
        {"raw_input": raw_input},
        structured,
        {"fallback_used": not bool(settings.OPENAI_API_KEY)},
    )

    red_flags = evaluate_red_flags(structured, raw_input)
    session.red_flag_status = red_flags["red_flag_status"]
    session.urgency_level = TriageUrgency(red_flags["urgency_level"])
    session.safety_message = red_flags["safety_message"]
    _log_audit(
        db,
        session.id,
        "Red Flag Rule Engine",
        {"raw_input": raw_input, "structured_symptoms": structured},
        red_flags,
        {"emergency": red_flags["urgency_level"] == "emergency"},
        "rule-based",
    )

    specialty = recommend_specialty(structured, red_flags, db)
    recommended = specialty["recommended_specialty"]
    secondary = specialty["secondary_specialty"]
    session.recommended_specialty_id = recommended.id if recommended else None
    session.secondary_specialty_id = secondary.id if secondary else None
    session.ai_confidence = specialty["confidence_score"]
    safe_reason = validate_ai_response(specialty["reason"])
    session.ai_reason = safe_reason["corrected_text"]
    _log_audit(
        db,
        session.id,
        "Specialty Router Agent",
        {"structured_symptoms": structured, "red_flag_result": red_flags},
        {
            "recommended_specialty": recommended.name if recommended else None,
            "secondary_specialty": secondary.name if secondary else None,
            "reason": session.ai_reason,
            "confidence_score": session.ai_confidence,
        },
        {"unsafe_output_detected": not safe_reason["is_safe"], "blocked_phrases": safe_reason["blocked_phrases"]},
        "rule-based",
    )

    summary = generate_doctor_summary(raw_input, structured, red_flags, specialty)
    summary_validation = validate_ai_response(summary)
    session.doctor_summary = summary_validation["corrected_text"]
    _log_audit(
        db,
        session.id,
        "Doctor Summary Agent",
        {"raw_input": raw_input, "structured_symptoms": structured},
        {"doctor_summary": session.doctor_summary},
        safety_flags_for_text(session.doctor_summary),
        "rule-based",
    )

    db.commit()
    session = (
        db.query(SymptomSession)
        .options(
            joinedload(SymptomSession.recommended_specialty),
            joinedload(SymptomSession.secondary_specialty),
        )
        .filter(SymptomSession.id == session.id)
        .first()
    )
    return session_to_result(session)


def run_triage(patient_id: int, raw_input: str, db: Session) -> dict:
    cleaned = _validate_raw_input(raw_input)
    session = SymptomSession(
        patient_id=patient_id,
        raw_input=cleaned,
        structured_symptoms={},
        urgency_level=TriageUrgency.routine,
        safety_message=medical_disclaimer(),
    )
    db.add(session)
    db.flush()
    try:
        return run_triage_for_session(session, db)
    except Exception:
        db.rollback()
        raise
