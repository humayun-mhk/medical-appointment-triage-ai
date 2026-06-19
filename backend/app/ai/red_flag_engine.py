import re

from app.ai.safety import emergency_message, medical_disclaimer


EMERGENCY_PATTERNS = {
    "difficulty breathing": [r"difficulty breathing", r"shortness of breath", r"trouble breathing", r"breathless"],
    "severe bleeding": [r"severe bleeding", r"heavy bleeding", r"bleeding won't stop"],
    "loss of consciousness": [r"loss of consciousness", r"passed out", r"fainted"],
    "confusion": [r"confusion", r"confused", r"disoriented"],
    "stroke symptoms": [r"stroke", r"slurred speech", r"facial droop", r"face drooping", r"one-sided weakness"],
    "severe allergic reaction": [r"severe allergic", r"anaphylaxis", r"swelling of face", r"swelling of throat"],
    "pregnancy bleeding": [r"pregnancy bleeding", r"bleeding during pregnancy"],
    "severe pregnancy abdominal pain": [r"pregnan.*severe.*(?:abdominal|stomach|belly).*pain"],
    "suicidal thoughts": [r"suicidal", r"kill myself", r"self harm"],
    "seizure": [r"seizure", r"convulsion"],
    "severe head injury": [r"severe head injury", r"head injury.*vomiting", r"head trauma"],
    "severe burn": [r"severe burn", r"large burn"],
    "blue lips": [r"blue lips"],
    "severe dehydration in child": [r"(child|infant|baby).*severe dehydration"],
    "high fever in infant": [r"(infant|baby).*high fever"],
}

URGENT_PATTERNS = {
    "fever for more than 3 days": [r"fever.*(?:4|5|6|7|8|9|10)\s*days", r"fever.*week"],
    "severe abdominal pain": [r"severe.*(?:abdominal|stomach|belly).*pain"],
    "persistent vomiting": [r"persistent vomiting", r"vomiting.*(?:all day|can't stop)"],
    "blood in vomit": [r"blood in vomit", r"vomiting blood"],
    "blood in stool": [r"blood in stool", r"bloody stool"],
    "severe eye pain": [r"severe eye pain"],
    "sudden blurry vision": [r"sudden blurry vision", r"sudden blurred vision"],
    "severe headache": [r"severe headache", r"worst headache"],
    "urinary pain with fever": [r"(urinary|urination|pee).*pain.*fever", r"fever.*(urinary|urination|pee).*pain"],
    "wound infection signs": [r"wound.*(?:pus|redness|swelling|infection)"],
}


def _matches(patterns: dict[str, list[str]], text: str) -> list[str]:
    matched = []
    for label, regexes in patterns.items():
        if any(re.search(regex, text, flags=re.IGNORECASE) for regex in regexes):
            matched.append(label)
    return matched


def _duration_days(duration: str | None) -> int | None:
    if not duration:
        return None
    match = re.search(r"(\d+)", duration)
    if not match:
        return None
    value = int(match.group(1))
    if "week" in duration.lower():
        return value * 7
    return value


def evaluate_red_flags(structured_symptoms: dict, raw_input: str) -> dict:
    text = f"{raw_input} {' '.join(structured_symptoms.get('main_symptoms', []))}".lower()
    matched_emergency = _matches(EMERGENCY_PATTERNS, text)

    if "chest pain" in text and any(
        phrase in text for phrase in ["shortness of breath", "difficulty breathing", "trouble breathing", "breathless"]
    ):
        matched_emergency.append("chest pain with shortness of breath")

    if matched_emergency:
        return {
            "red_flag_status": True,
            "urgency_level": "emergency",
            "matched_red_flags": sorted(set(matched_emergency)),
            "safety_message": emergency_message(),
            "reason": "Emergency red flag symptoms were found. This is routing support, not a diagnosis.",
        }

    matched_urgent = _matches(URGENT_PATTERNS, text)
    severity = structured_symptoms.get("severity")
    if isinstance(severity, int) and severity >= 8:
        matched_urgent.append("severity >= 8")
    if "fever" in structured_symptoms.get("main_symptoms", []) and (_duration_days(structured_symptoms.get("duration")) or 0) > 3:
        matched_urgent.append("fever for more than 3 days")

    if matched_urgent:
        return {
            "red_flag_status": False,
            "urgency_level": "urgent",
            "matched_red_flags": sorted(set(matched_urgent)),
            "safety_message": f"These symptoms may need prompt medical attention. {medical_disclaimer()}",
            "reason": "Urgent routing criteria were found.",
        }

    soon_symptoms = {"fever", "sore throat", "cough", "vomiting", "diarrhea", "urinary pain", "eye pain"}
    urgency = "soon" if soon_symptoms.intersection(set(structured_symptoms.get("main_symptoms", []))) else "routine"
    return {
        "red_flag_status": False,
        "urgency_level": urgency,
        "matched_red_flags": [],
        "safety_message": medical_disclaimer(),
        "reason": "No emergency red flags detected.",
    }
