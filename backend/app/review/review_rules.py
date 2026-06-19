from datetime import date


def _age_from_profile(patient_profile: dict | None) -> int | None:
    if not patient_profile:
        return None
    dob = patient_profile.get("date_of_birth")
    if isinstance(dob, str):
        try:
            dob = date.fromisoformat(dob)
        except ValueError:
            return None
    if not dob:
        return None
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def should_flag_for_review(triage_result: dict, patient_profile: dict | None = None) -> dict:
    reasons: list[str] = []
    risk_level = "low"
    structured = triage_result.get("structured_symptoms") or {}
    confidence = triage_result.get("ai_confidence", triage_result.get("confidence_score"))
    urgency = triage_result.get("urgency_level")
    if hasattr(urgency, "value"):
        urgency = urgency.value

    if urgency == "emergency" or triage_result.get("red_flag_status") is True:
        reasons.append("Emergency or red-flag triage result")
        risk_level = "critical"
    if confidence is not None and confidence < 0.60:
        reasons.append("AI confidence below 0.60")
        risk_level = max(risk_level, "medium", key=["low", "medium", "high", "critical"].index)
    if structured.get("pregnancy_related"):
        reasons.append("Pregnancy-related symptoms")
        risk_level = max(risk_level, "high", key=["low", "medium", "high", "critical"].index)
    if structured.get("severity") and structured["severity"] >= 8:
        reasons.append("Severe pain or symptom severity")
        risk_level = max(risk_level, "high", key=["low", "medium", "high", "critical"].index)
    if len(structured.get("main_symptoms") or []) >= 5:
        reasons.append("Multiple complex symptoms")
        risk_level = max(risk_level, "medium", key=["low", "medium", "high", "critical"].index)
    age = _age_from_profile(patient_profile)
    if age is not None and age < 13:
        reasons.append("Child patient")
        risk_level = max(risk_level, "medium", key=["low", "medium", "high", "critical"].index)
    if age is not None and age >= 65 and structured.get("severity", 0) >= 7:
        reasons.append("Elderly patient with severe symptoms")
        risk_level = max(risk_level, "high", key=["low", "medium", "high", "critical"].index)
    safety_flags = triage_result.get("safety_flags") or []
    if safety_flags:
        reasons.append(f"Safety flags: {', '.join(map(str, safety_flags))}")
        risk_level = max(risk_level, "medium", key=["low", "medium", "high", "critical"].index)

    return {
        "flag_for_review": bool(reasons),
        "reason": "; ".join(reasons),
        "risk_level": risk_level,
        "route_to": "General Physician" if confidence is not None and confidence < 0.60 else None,
    }
