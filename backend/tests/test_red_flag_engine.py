from app.ai.red_flag_engine import evaluate_red_flags


def test_chest_pain_shortness_of_breath_is_emergency():
    result = evaluate_red_flags({"main_symptoms": ["chest pain", "difficulty breathing"]}, "chest pain and shortness of breath")
    assert result["urgency_level"] == "emergency"
    assert result["red_flag_status"] is True


def test_difficulty_breathing_is_emergency():
    result = evaluate_red_flags({"main_symptoms": ["difficulty breathing"]}, "I have difficulty breathing")
    assert result["urgency_level"] == "emergency"
    assert result["red_flag_status"] is True


def test_severity_nine_is_urgent():
    result = evaluate_red_flags({"main_symptoms": ["headache"], "severity": 9}, "headache severity 9")
    assert result["urgency_level"] == "urgent"


def test_mild_cough_is_routine_or_soon():
    result = evaluate_red_flags({"main_symptoms": ["cough"], "severity": 3}, "mild cough")
    assert result["urgency_level"] in {"routine", "soon"}
    assert result["red_flag_status"] is False


def test_pregnancy_bleeding_is_emergency():
    result = evaluate_red_flags({"main_symptoms": ["pregnancy bleeding"], "pregnancy_related": True}, "pregnancy bleeding")
    assert result["urgency_level"] == "emergency"
    assert result["red_flag_status"] is True
