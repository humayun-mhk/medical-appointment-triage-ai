from sqlalchemy.orm import Session, joinedload

from app.ai.safety import medical_disclaimer, validate_ai_response
from app.models import RAGQuery, SymptomSession
from app.rag.retriever import retrieve_policy_context, retrieve_session_context
from app.rag.safety_rag_policy import blocked_rag_answer, is_allowed_rag_query


def _sources(chunks: list[dict]) -> list[dict]:
    seen = set()
    sources = []
    for chunk in chunks:
        key = (chunk["document_title"], chunk["category"])
        if key in seen:
            continue
        seen.add(key)
        sources.append({"title": chunk["document_title"], "category": chunk["category"]})
    return sources


def _save_query(user_id: int | None, triage_session_id: int | None, question: str, answer: dict, db: Session) -> None:
    db.add(
        RAGQuery(
            user_id=user_id,
            triage_session_id=triage_session_id,
            query_text=question,
            retrieved_chunks=answer.get("retrieved_chunks", []),
            response_text=answer["answer"],
            safety_flags={"flags": answer.get("safety_flags", [])},
        )
    )
    db.flush()


def answer_policy_question(user_id: int, question: str, db: Session) -> dict:
    allowed, blocked_terms = is_allowed_rag_query(question)
    if not allowed:
        answer = blocked_rag_answer(blocked_terms)
        _save_query(user_id, None, question, {**answer, "retrieved_chunks": []}, db)
        db.commit()
        return answer

    retrieved = retrieve_policy_context(question, db)
    chunks = retrieved["chunks"]
    if chunks:
        context = " ".join(chunk["chunk_text"] for chunk in chunks[:2])
        answer_text = (
            f"{context} This information is for appointment routing and clinic policy support only. "
            f"{medical_disclaimer()}"
        )
    else:
        answer_text = (
            "I can help with appointment policy, preparation, cancellation rules, emergency routing policy, "
            f"and doctor specialty routing. {medical_disclaimer()}"
        )
    validation = validate_ai_response(answer_text)
    answer = {
        "answer": validation["corrected_text"],
        "sources": _sources(chunks),
        "safety_flags": validation["safety_flags"],
        "disclaimer": medical_disclaimer(),
        "retrieved_chunks": chunks,
    }
    _save_query(user_id, None, question, answer, db)
    db.commit()
    return {key: value for key, value in answer.items() if key != "retrieved_chunks"}


def generate_safe_routing_context(triage_session_id: int, db: Session) -> dict:
    session = (
        db.query(SymptomSession)
        .options(joinedload(SymptomSession.recommended_specialty))
        .filter(SymptomSession.id == triage_session_id)
        .first()
    )
    if session is None:
        raise ValueError("Triage session not found")
    retrieved = retrieve_session_context(session, db)
    specialty_name = session.recommended_specialty.name if session.recommended_specialty else "General Physician"
    if session.urgency_level.value == "emergency":
        answer_text = (
            "Emergency red flags require immediate medical attention before routine appointment booking. "
            f"A {specialty_name} may be used for routing only when emergency care is not required. "
            f"{medical_disclaimer()}"
        )
    else:
        answer_text = (
            f"Based on routing policy, a {specialty_name} may be suitable for reviewing these symptoms. "
            "This is only specialty routing support and should be confirmed by a qualified clinician. "
            f"{medical_disclaimer()}"
        )
    validation = validate_ai_response(answer_text)
    answer = {
        "answer": validation["corrected_text"],
        "sources": _sources(retrieved["chunks"]),
        "safety_flags": validation["safety_flags"],
        "disclaimer": medical_disclaimer(),
        "retrieved_chunks": retrieved["chunks"],
    }
    _save_query(session.patient.user_id if session.patient else None, session.id, retrieved["query"], answer, db)
    db.commit()
    return {key: value for key, value in answer.items() if key != "retrieved_chunks"}


def enrich_triage_reason_with_rag(triage_result: dict, db: Session) -> dict:
    session_id = triage_result.get("session_id")
    if not session_id:
        return triage_result
    try:
        context = generate_safe_routing_context(session_id, db)
    except ValueError:
        return triage_result
    enriched = dict(triage_result)
    enriched["rag_context"] = context
    enriched["ai_reason"] = f"{triage_result.get('ai_reason') or ''} {context['answer']}".strip()
    return enriched
