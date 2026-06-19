from sqlalchemy.orm import Session, joinedload

from app.models import KnowledgeCategory, KnowledgeChunk, KnowledgeDocument, SymptomSession
from app.rag.embedding_service import cosine_similarity, get_embedding
from app.rag.safety_rag_policy import clean_category


def _serialize_chunk(chunk: KnowledgeChunk, score: float) -> dict:
    return {
        "chunk_id": chunk.id,
        "document_id": chunk.document_id,
        "document_title": chunk.document.title,
        "category": chunk.document.category.value,
        "chunk_text": chunk.chunk_text,
        "score": score,
    }


def retrieve_relevant_chunks(query: str, category: str | None, db: Session, top_k: int = 5) -> dict:
    query_vector = get_embedding(query)
    normalized_category = clean_category(category)
    db_query = (
        db.query(KnowledgeChunk)
        .options(joinedload(KnowledgeChunk.document))
        .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
        .filter(KnowledgeDocument.is_active.is_(True))
    )
    if normalized_category:
        db_query = db_query.filter(KnowledgeDocument.category == KnowledgeCategory(normalized_category))

    scored = []
    for chunk in db_query.all():
        score = cosine_similarity(query_vector, list(chunk.embedding or []))
        scored.append((score, chunk))
    scored.sort(key=lambda item: item[0], reverse=True)
    return {"query": query, "chunks": [_serialize_chunk(chunk, score) for score, chunk in scored[:top_k]]}


def retrieve_for_triage(structured_symptoms: dict, urgency_level: str, recommended_specialty: str, db: Session) -> dict:
    symptoms = " ".join(structured_symptoms.get("main_symptoms") or [])
    query = f"{symptoms} {recommended_specialty} {urgency_level}".strip()
    if urgency_level == "emergency":
        return retrieve_relevant_chunks(query, "emergency_policy", db, top_k=5)
    if recommended_specialty:
        return retrieve_relevant_chunks(query, "specialty_description", db, top_k=5)
    return retrieve_relevant_chunks(query, "safety_guideline", db, top_k=5)


def retrieve_policy_context(query: str, db: Session) -> dict:
    lowered = (query or "").lower()
    if "cancel" in lowered or "reschedule" in lowered:
        return retrieve_relevant_chunks(query, "cancellation_policy", db, top_k=5)
    if "prepare" in lowered or "bring" in lowered or "before visit" in lowered:
        return retrieve_relevant_chunks(query, "patient_preparation", db, top_k=5)
    if "emergency" in lowered or "red flag" in lowered:
        return retrieve_relevant_chunks(query, "emergency_policy", db, top_k=5)
    return retrieve_relevant_chunks(query, None, db, top_k=5)


def retrieve_session_context(session: SymptomSession, db: Session) -> dict:
    specialty = session.recommended_specialty.name if session.recommended_specialty else ""
    return retrieve_for_triage(session.structured_symptoms or {}, session.urgency_level.value, specialty, db)
