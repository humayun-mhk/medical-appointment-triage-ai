import re


DISCLAIMER = (
    "This is not a diagnosis or medical advice. This tool only helps route you "
    "to a suitable healthcare professional. Please consult a qualified doctor."
)

EMERGENCY_MESSAGE = (
    "Your symptoms may require emergency care. Please seek immediate medical "
    "attention or contact local emergency services."
)

DIAGNOSIS_PATTERNS = [
    r"\byou have\b",
    r"\byou are having\b",
    r"\bthis is (?:definitely |certainly )?(?:a|an)?\s*\w+\b",
    r"\bdiagnosed with\b",
    r"\bconfirmed (?:case|diagnosis)\b",
    r"\bspecific disease\b",
]

MEDICATION_PATTERNS = [
    r"\btake (?:an? )?(?:antibiotic|medicine|medication|painkiller)\b",
    r"\buse this medicine\b",
    r"\bstart (?:an? )?(?:antibiotic|medicine|medication)\b",
    r"\bprescribe\b",
    r"\b\d+\s?(?:mg|mcg|ml)\b",
    r"\bdosage\b",
]

FALSE_REASSURANCE_PATTERNS = [
    r"\bno need to see a doctor\b",
    r"\byou do not need a doctor\b",
    r"\bignore (?:the )?symptom\b",
    r"\bthis is definitely not serious\b",
    r"\bnothing to worry about\b",
    r"\bnot serious\b",
]

UNSAFE_PATTERNS = [
    *DIAGNOSIS_PATTERNS,
    *MEDICATION_PATTERNS,
    *FALSE_REASSURANCE_PATTERNS,
]


def medical_disclaimer() -> str:
    return DISCLAIMER


def emergency_message() -> str:
    return EMERGENCY_MESSAGE


def _matches(patterns: list[str], text: str) -> list[str]:
    if not text:
        return []
    return [pattern for pattern in patterns if re.search(pattern, text, flags=re.IGNORECASE)]


def detect_diagnosis_language(text: str) -> list[str]:
    return _matches(DIAGNOSIS_PATTERNS, text)


def detect_medication_advice(text: str) -> list[str]:
    return _matches(MEDICATION_PATTERNS, text)


def detect_false_reassurance(text: str) -> list[str]:
    return _matches(FALSE_REASSURANCE_PATTERNS, text)


def sanitize_ai_output(text: str) -> str:
    corrected = text or ""
    replacements = {
        **{pattern: "these symptoms should be reviewed by a qualified doctor" for pattern in DIAGNOSIS_PATTERNS},
        **{pattern: "medicine questions should be discussed with a qualified doctor" for pattern in MEDICATION_PATTERNS},
        **{pattern: "please consult a qualified doctor if symptoms persist or worsen" for pattern in FALSE_REASSURANCE_PATTERNS},
    }
    for pattern, replacement in replacements.items():
        corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)
    if corrected and DISCLAIMER.lower() not in corrected.lower():
        corrected = f"{corrected.strip()} {DISCLAIMER}"
    return corrected


def validate_ai_response(text: str) -> dict:
    if not text:
        return {
            "is_safe": True,
            "blocked_phrases": [],
            "safety_flags": [],
            "corrected_text": text,
            "corrected_output": text,
            "requires_review": False,
        }

    blocked = _matches(UNSAFE_PATTERNS, text)
    corrected = sanitize_ai_output(text) if blocked else text
    flags = []
    if detect_diagnosis_language(text):
        flags.append("diagnosis_language")
    if detect_medication_advice(text):
        flags.append("medication_advice")
    if detect_false_reassurance(text):
        flags.append("false_reassurance")

    return {
        "is_safe": not blocked,
        "blocked_phrases": blocked,
        "safety_flags": flags,
        "corrected_text": corrected,
        "corrected_output": corrected,
        "requires_review": bool(blocked),
    }


def safety_flags_for_text(text: str) -> dict:
    validation = validate_ai_response(text)
    return {
        "unsafe_output_detected": not validation["is_safe"],
        "blocked_phrases": validation["blocked_phrases"],
        "safety_flags": validation["safety_flags"],
    }


def enforce_emergency_rules(triage_result: dict) -> dict:
    result = dict(triage_result)
    urgency = result.get("urgency_level")
    if hasattr(urgency, "value"):
        urgency = urgency.value
    if result.get("red_flag_status") is True:
        result["urgency_level"] = "emergency"
        result["safety_message"] = emergency_message()
    structured = result.get("structured_symptoms") or {}
    if structured.get("pregnancy_related") and result.get("red_flag_status"):
        result["urgency_level"] = "emergency"
        result["safety_message"] = emergency_message()
    severity = structured.get("severity")
    if isinstance(severity, int) and severity >= 8 and urgency in {"routine", "soon"}:
        result["urgency_level"] = "urgent"
    return result


def validate_triage_safety(triage_result: dict) -> dict:
    checked = enforce_emergency_rules(triage_result)
    text_parts = [
        str(checked.get("ai_reason") or ""),
        str(checked.get("doctor_summary") or ""),
        str(checked.get("safety_message") or ""),
    ]
    output_validation = validate_ai_response(" ".join(text_parts))
    confidence = checked.get("ai_confidence")
    requires_review = output_validation["requires_review"]
    flags = list(output_validation["safety_flags"])
    if confidence is not None and confidence < 0.60:
        requires_review = True
        flags.append("low_confidence")
    if checked.get("urgency_level") == "emergency":
        requires_review = True
        flags.append("emergency_review")
    structured = checked.get("structured_symptoms") or {}
    if structured.get("pregnancy_related"):
        flags.append("pregnancy_related")
    return {
        "is_safe": output_validation["is_safe"],
        "blocked_phrases": output_validation["blocked_phrases"],
        "safety_flags": sorted(set(flags)),
        "corrected_output": output_validation["corrected_output"],
        "requires_review": requires_review,
        "triage_result": checked,
    }
