from app.ai.safety import (
    detect_false_reassurance,
    detect_medication_advice,
    validate_ai_response,
    validate_triage_safety,
)
from app.rag.document_loader import chunk_document
from app.rag.safety_rag_policy import is_allowed_rag_query
from app.review.review_rules import should_flag_for_review
from app.security.pii_masking import mask_email, mask_phone, mask_pii_payload


def test_rag_chunking_creates_overlapping_chunks():
    content = "word " * 400
    chunks = chunk_document(content, chunk_size=120, overlap=20)
    assert len(chunks) > 1
    assert all(len(chunk) <= 120 for chunk in chunks)


def test_rag_blocks_diagnosis_requests():
    allowed, blocked = is_allowed_rag_query("What disease do I have and what medicine should I take?")
    assert allowed is False
    assert "what disease" in blocked
    assert "medicine" in blocked


def test_strong_safety_blocks_false_reassurance_and_medicine():
    response = validate_ai_response("No need to see a doctor. Take antibiotic 500mg.")
    assert response["is_safe"] is False
    assert detect_false_reassurance("this is definitely not serious")
    assert detect_medication_advice("take antibiotic")
    assert "This is not a diagnosis" in response["corrected_text"]


def test_emergency_triage_requires_review():
    result = validate_triage_safety(
        {
            "red_flag_status": True,
            "urgency_level": "routine",
            "structured_symptoms": {"main_symptoms": ["chest pain"], "severity": 7},
            "ai_confidence": 0.9,
        }
    )
    assert result["triage_result"]["urgency_level"] == "emergency"
    assert result["requires_review"] is True


def test_low_confidence_review_rule():
    review = should_flag_for_review(
        {"urgency_level": "routine", "red_flag_status": False, "ai_confidence": 0.4, "structured_symptoms": {}},
        None,
    )
    assert review["flag_for_review"] is True
    assert review["route_to"] == "General Physician"


def test_pii_masking():
    assert mask_email("patient@example.com").startswith("p*****t@")
    assert mask_phone("+1 555 123 4567").endswith("4567")
    payload = mask_pii_payload({"email": "patient@example.com", "phone": "+1 555 123 4567"})
    assert payload["email"] != "patient@example.com"
    assert payload["phone"] != "+1 555 123 4567"
