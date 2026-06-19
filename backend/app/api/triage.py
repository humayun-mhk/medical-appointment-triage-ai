from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.ai.doctor_matching_engine import match_doctors
from app.ai.safety import validate_triage_safety
from app.ai.triage_orchestrator import run_triage, run_triage_for_session
from app.core.dependencies import get_current_user, require_patient
from app.db.database import get_db
from app.models import AIAuditLog, Appointment, Doctor, PatientProfile, SymptomSession, TriageUrgency, User
from app.notifications.notification_service import notify_emergency_warning
from app.notifications.appointment_tasks import send_appointment_booked_notifications
from app.review.review_service import create_review_case_if_needed
from app.schemas import (
    AIAuditLogResponse,
    AppointmentResponse,
    BookFromTriageRequest,
    RecommendedDoctorResponse,
    TriageAnalyzeRequest,
    TriageResultResponse,
    TriageStartRequest,
    TriageStartResponse,
)
from app.services import (
    book_from_triage,
    create_symptom_session,
    doctor_to_response,
    ensure_patient_owns_session,
    ensure_session_visible_to_user,
    get_patient_profile_or_404,
    get_session_with_details,
)
from app.security.audit_logger import log_security_event
from app.security.rate_limit import check_rate_limit

router = APIRouter(tags=["AI Triage"])


def _appointment_response(appointment: Appointment) -> dict:
    triage = appointment.triage_session
    return {
        "id": appointment.id,
        "patient_id": appointment.patient_id,
        "doctor_id": appointment.doctor_id,
        "slot_id": appointment.slot_id,
        "status": appointment.status,
        "symptoms": appointment.symptoms,
        "patient_notes": appointment.patient_notes,
        "doctor_notes": appointment.doctor_notes,
        "triage_session_id": appointment.triage_session_id,
        "doctor_summary": appointment.doctor_summary,
        "urgency_level": triage.urgency_level.value if triage else None,
        "red_flag_status": triage.red_flag_status if triage else None,
        "created_at": appointment.created_at,
        "updated_at": appointment.updated_at,
        "doctor": doctor_to_response(appointment.doctor),
        "slot": appointment.slot,
    }


@router.post("/triage/start", response_model=TriageStartResponse, status_code=status.HTTP_201_CREATED)
def start_triage(
    payload: TriageStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient),
):
    profile = get_patient_profile_or_404(db, current_user)
    session = create_symptom_session(db, profile.id, payload.raw_input)
    return {"session_id": session.id, "message": "Triage session started."}


@router.post("/triage/analyze", response_model=TriageResultResponse)
def analyze_triage(
    payload: TriageAnalyzeRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient),
):
    check_rate_limit(request, f"user:{current_user.id}", 10, 60)
    profile = get_patient_profile_or_404(db, current_user)
    try:
        if payload.session_id:
            session = get_session_with_details(db, payload.session_id)
            ensure_patient_owns_session(session, profile)
            result = run_triage_for_session(session, db)
            safety = validate_triage_safety(result)
            create_review_case_if_needed(result["session_id"], db)
            if safety["triage_result"].get("urgency_level") == "emergency" or result.get("red_flag_status"):
                notify_emergency_warning(db, current_user.id, result.get("safety_message") or "Emergency care may be required.")
            log_security_event(
                db,
                action="triage_analyzed",
                resource_type="triage_session",
                resource_id=result["session_id"],
                request=request,
                user_id=current_user.id,
                metadata={"urgency_level": str(result.get("urgency_level")), "red_flag_status": result.get("red_flag_status")},
            )
            db.commit()
            return result
        if payload.raw_input:
            result = run_triage(profile.id, payload.raw_input, db)
            safety = validate_triage_safety(result)
            create_review_case_if_needed(result["session_id"], db)
            if safety["triage_result"].get("urgency_level") == "emergency" or result.get("red_flag_status"):
                notify_emergency_warning(db, current_user.id, result.get("safety_message") or "Emergency care may be required.")
            log_security_event(
                db,
                action="triage_analyzed",
                resource_type="triage_session",
                resource_id=result["session_id"],
                request=request,
                user_id=current_user.id,
                metadata={"urgency_level": str(result.get("urgency_level")), "red_flag_status": result.get("red_flag_status")},
            )
            db.commit()
            return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="session_id or raw_input is required")


@router.get("/triage/result/{session_id}", response_model=TriageResultResponse)
def triage_result(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = get_session_with_details(db, session_id)
    ensure_session_visible_to_user(db, session, current_user)
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
        "safety_message": session.safety_message,
        "created_at": session.created_at,
    }


@router.get("/doctors/recommended/{session_id}", response_model=list[RecommendedDoctorResponse])
def recommended_doctors(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = get_session_with_details(db, session_id)
    ensure_session_visible_to_user(db, session, current_user)
    return match_doctors(session_id, db)


@router.post("/appointments/book-from-triage", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def book_appointment_from_triage(
    payload: BookFromTriageRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient),
):
    profile = get_patient_profile_or_404(db, current_user)
    session = get_session_with_details(db, payload.session_id)
    appointment = book_from_triage(
        db,
        profile,
        session,
        payload.doctor_id,
        payload.slot_id,
        payload.patient_notes,
        payload.confirm_manual_override,
    )
    response_payload = _appointment_response(appointment)
    background_tasks.add_task(send_appointment_booked_notifications, appointment.id)
    return response_payload


@router.get("/admin/triage/sessions")
def admin_triage_sessions(
    urgency_level: TriageUrgency | None = Query(default=None),
    recommended_specialty_id: int | None = Query(default=None),
    red_flag_status: bool | None = Query(default=None),
    selected_date: date | None = Query(default=None, alias="date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.value != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden role access")
    query = (
        db.query(SymptomSession)
        .options(
            joinedload(SymptomSession.patient).joinedload(PatientProfile.user),
            joinedload(SymptomSession.recommended_specialty),
        )
        .order_by(SymptomSession.created_at.desc())
    )
    if urgency_level:
        query = query.filter(SymptomSession.urgency_level == urgency_level)
    if recommended_specialty_id:
        query = query.filter(SymptomSession.recommended_specialty_id == recommended_specialty_id)
    if red_flag_status is not None:
        query = query.filter(SymptomSession.red_flag_status == red_flag_status)
    if selected_date:
        query = query.filter(func.date(SymptomSession.created_at) == selected_date)
    sessions = query.all()
    return [
        {
            "session_id": session.id,
            "patient_name": session.patient.user.full_name,
            "raw_input_preview": session.raw_input[:140],
            "urgency_level": session.urgency_level,
            "red_flag_status": session.red_flag_status,
            "recommended_specialty": session.recommended_specialty.name if session.recommended_specialty else None,
            "ai_confidence": session.ai_confidence,
            "created_at": session.created_at,
        }
        for session in sessions
    ]


@router.get("/admin/triage/sessions/{session_id}")
def admin_triage_session_detail(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.value != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden role access")
    session = get_session_with_details(db, session_id)
    return {
        "session_id": session.id,
        "patient_name": session.patient.user.full_name,
        "raw_input": session.raw_input,
        "structured_symptoms": session.structured_symptoms or {},
        "red_flag_status": session.red_flag_status,
        "urgency_level": session.urgency_level,
        "recommended_specialty": session.recommended_specialty,
        "secondary_specialty": session.secondary_specialty,
        "ai_confidence": session.ai_confidence,
        "ai_reason": session.ai_reason,
        "doctor_summary": session.doctor_summary,
        "safety_message": session.safety_message,
        "created_at": session.created_at,
        "audit_logs": session.audit_logs,
    }


@router.get("/admin/ai-audit-logs", response_model=list[AIAuditLogResponse])
def admin_ai_audit_logs(
    agent_name: str | None = Query(default=None),
    session_id: int | None = Query(default=None),
    model_name: str | None = Query(default=None),
    selected_date: date | None = Query(default=None, alias="date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.value != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden role access")
    query = db.query(AIAuditLog).order_by(AIAuditLog.created_at.desc())
    if agent_name:
        query = query.filter(AIAuditLog.agent_name == agent_name)
    if session_id:
        query = query.filter(AIAuditLog.session_id == session_id)
    if model_name:
        query = query.filter(AIAuditLog.model_name == model_name)
    if selected_date:
        query = query.filter(func.date(AIAuditLog.created_at) == selected_date)
    return query.all()
