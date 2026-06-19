import json
import re
import urllib.error
import urllib.request

from app.ai.prompts import SYMPTOM_INTAKE_PROMPT
from app.core.config import settings


SYMPTOM_KEYWORDS = {
    "fever": ["fever", "temperature", "high temp"],
    "cough": ["cough", "coughing"],
    "sore throat": ["sore throat", "throat pain", "painful throat"],
    "chest pain": ["chest pain", "chest tightness"],
    "difficulty breathing": ["difficulty breathing", "shortness of breath", "breathless", "trouble breathing"],
    "skin rash": ["rash", "skin rash"],
    "itching": ["itching", "itchy"],
    "acne": ["acne", "pimples"],
    "ear pain": ["ear pain", "earache"],
    "sinus": ["sinus", "blocked nose", "nasal congestion"],
    "tooth pain": ["tooth pain", "toothache", "gum pain"],
    "pregnancy bleeding": ["pregnancy bleeding", "bleeding during pregnancy"],
    "abdominal pain": ["abdominal pain", "stomach pain", "belly pain"],
    "vomiting": ["vomiting", "throwing up"],
    "diarrhea": ["diarrhea", "loose motion"],
    "joint pain": ["joint pain", "knee pain", "shoulder pain"],
    "back pain": ["back pain"],
    "eye pain": ["eye pain", "eye disease", "eye problem", "eye issue", "red eye", "redness in eye"],
    "blurry vision": ["blurry vision", "blurred vision", "vision problem", "vision issue", "poor vision"],
    "urinary pain": ["urinary pain", "burning urination", "pain while urinating"],
    "anxiety": ["anxiety", "panic"],
    "depression": ["depression", "depressed"],
    "headache": ["headache", "head pain"],
}

BODY_PARTS = {
    "throat": ["throat"],
    "chest": ["chest", "breath"],
    "skin": ["skin", "rash", "itch"],
    "ear": ["ear"],
    "mouth": ["tooth", "gum", "dental"],
    "abdomen": ["stomach", "abdomen", "belly"],
    "eye": ["eye", "vision"],
    "back": ["back"],
    "joint": ["joint", "knee", "shoulder"],
}


def _default_output() -> dict:
    return {
        "main_symptoms": [],
        "duration": None,
        "severity": None,
        "body_parts": [],
        "associated_symptoms": [],
        "medications_mentioned": [],
        "patient_age_group": None,
        "pregnancy_related": False,
        "extra_notes": None,
    }


def _extract_duration(text: str) -> str | None:
    match = re.search(
        r"\b(?:for|since)\s+(\d+\s*(?:hour|hours|day|days|week|weeks|month|months))\b",
        text,
        flags=re.IGNORECASE,
    )
    if match:
        return match.group(1)
    match = re.search(r"\b(\d+\s*(?:hour|hours|day|days|week|weeks|month|months))\b", text, flags=re.IGNORECASE)
    return match.group(1) if match else None


def _extract_severity(text: str) -> int | None:
    match = re.search(r"\b(?:severity|pain|rate|level)[^\d]*(10|[1-9])(?:\s*/\s*10)?\b", text, flags=re.IGNORECASE)
    if match:
        return int(match.group(1))
    if re.search(r"\b(severe|very bad|worst)\b", text, flags=re.IGNORECASE):
        return 8
    if re.search(r"\b(moderate|medium)\b", text, flags=re.IGNORECASE):
        return 5
    if re.search(r"\b(mild|slight)\b", text, flags=re.IGNORECASE):
        return 3
    return None


def fallback_extract_symptoms(raw_input: str) -> dict:
    text = raw_input.lower()
    output = _default_output()
    for symptom, keywords in SYMPTOM_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            output["main_symptoms"].append(symptom)

    for body_part, keywords in BODY_PARTS.items():
        if any(keyword in text for keyword in keywords):
            output["body_parts"].append(body_part)

    medications = re.findall(r"\b(?:taking|took|using|used)\s+([a-zA-Z][a-zA-Z0-9 -]{2,30})", raw_input)
    output["medications_mentioned"] = [item.strip(" .") for item in medications]
    output["duration"] = _extract_duration(raw_input)
    output["severity"] = _extract_severity(raw_input)
    output["pregnancy_related"] = "pregnan" in text
    output["patient_age_group"] = "child" if re.search(r"\b(child|kid|infant|baby)\b", text) else None
    output["extra_notes"] = "No emergency symptom mentioned"
    return validate_symptom_output(output)


def validate_symptom_output(data: dict) -> dict:
    output = _default_output()
    output.update(data or {})
    for list_key in ["main_symptoms", "body_parts", "associated_symptoms", "medications_mentioned"]:
        value = output.get(list_key)
        output[list_key] = value if isinstance(value, list) else []
        output[list_key] = [str(item).strip().lower() for item in output[list_key] if str(item).strip()]

    severity = output.get("severity")
    if severity is not None:
        try:
            severity = int(severity)
            output["severity"] = severity if 1 <= severity <= 10 else None
        except (TypeError, ValueError):
            output["severity"] = None

    output["pregnancy_related"] = bool(output.get("pregnancy_related"))
    return output


def _llm_extract_symptoms(raw_input: str) -> dict | None:
    if not settings.OPENAI_API_KEY or not settings.TRIAGE_USE_LLM:
        return None

    payload = {
        "model": settings.AI_MODEL,
        "messages": [
            {"role": "system", "content": SYMPTOM_INTAKE_PROMPT},
            {"role": "user", "content": raw_input},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
        content = result["choices"][0]["message"]["content"]
        return validate_symptom_output(json.loads(content))
    except (urllib.error.URLError, KeyError, ValueError, TimeoutError, json.JSONDecodeError):
        return None


def extract_symptoms(raw_input: str) -> dict:
    llm_result = _llm_extract_symptoms(raw_input)
    if llm_result:
        return llm_result
    return fallback_extract_symptoms(raw_input)
