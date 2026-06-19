from app.ai.safety import validate_ai_response


def test_diagnosis_statement_is_blocked():
    result = validate_ai_response("You have pneumonia.")
    assert result["is_safe"] is False
    assert "you have pneumonia" not in result["corrected_text"].lower()


def test_medicine_advice_is_blocked():
    result = validate_ai_response("Take antibiotic now.")
    assert result["is_safe"] is False
    assert "take antibiotic" not in result["corrected_text"].lower()
