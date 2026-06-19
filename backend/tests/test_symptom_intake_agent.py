from app.ai.symptom_intake_agent import fallback_extract_symptoms


def test_fallback_extracts_common_symptoms_and_duration():
    result = fallback_extract_symptoms("I have fever, sore throat and cough for 3 days.")
    assert "fever" in result["main_symptoms"]
    assert "sore throat" in result["main_symptoms"]
    assert "cough" in result["main_symptoms"]
    assert result["duration"] == "3 days"
