from app.ai.safety import medical_disclaimer

ALLOWED_CATEGORIES = {
    "specialty_description",
    "clinic_policy",
    "emergency_policy",
    "doctor_service",
    "faq",
    "cancellation_policy",
    "patient_preparation",
    "safety_guideline",
}

BLOCKED_QUERY_TERMS = {
    "diagnose",
    "diagnosis",
    "what disease",
    "which disease",
    "do i have",
    "medicine",
    "medication",
    "antibiotic",
    "dosage",
    "treatment plan",
    "lab test",
    "prescribe",
    "cure",
}


def is_allowed_rag_query(question: str) -> tuple[bool, list[str]]:
    lowered = (question or "").lower()
    blocked = [term for term in BLOCKED_QUERY_TERMS if term in lowered]
    return not blocked, blocked


def blocked_rag_answer(blocked_terms: list[str]) -> dict:
    return {
        "answer": (
            "I cannot provide diagnosis, medicine, dosage, or treatment instructions. "
            "I can help explain appointment policy, emergency routing policy, visit preparation, "
            "or which doctor specialty may be suitable. "
            f"{medical_disclaimer()}"
        ),
        "sources": [],
        "safety_flags": [{"type": "blocked_rag_query", "terms": blocked_terms}],
        "disclaimer": medical_disclaimer(),
    }


def clean_category(category: str | None) -> str | None:
    if not category:
        return None
    return category if category in ALLOWED_CATEGORIES else None
