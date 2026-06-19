from app.ai.safety import validate_ai_response


def generate_doctor_summary(
    raw_input: str,
    structured_symptoms: dict,
    red_flag_result: dict,
    specialty_result: dict,
) -> str:
    symptoms = structured_symptoms.get("main_symptoms") or []
    duration = structured_symptoms.get("duration") or "not specified"
    severity = structured_symptoms.get("severity")
    severity_text = f"{severity}/10" if severity else "not specified"
    matched_flags = red_flag_result.get("matched_red_flags") or []
    red_flag_text = ", ".join(matched_flags) if matched_flags else "No emergency red flags detected"
    specialty = specialty_result.get("recommended_specialty")
    specialty_name = specialty.name if specialty else "General Physician"

    summary = (
        f"Patient reports {', '.join(symptoms) if symptoms else 'symptoms described in free text'}. "
        f"Duration: {duration}. Severity: {severity_text}. "
        f"Red flag review: {red_flag_text}. "
        f"Urgency level: {red_flag_result.get('urgency_level', 'routine')}. "
        f"Recommended specialty for routing: {specialty_name}. "
        "Patient notes should be reviewed by the doctor during consultation."
    )
    return validate_ai_response(summary)["corrected_text"]
