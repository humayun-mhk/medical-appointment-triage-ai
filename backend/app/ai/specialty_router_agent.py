from sqlalchemy.orm import Session

from app.models import Specialty


SPECIALTY_KEYWORDS = {
    "General Physician": ["fever", "cough", "body pain", "fatigue"],
    "Cardiologist": ["chest pain", "palpitations", "heart disease", "heart problem"],
    "Dermatologist": ["skin rash", "itching", "acne", "rash", "skin disease", "skin problem"],
    "ENT Specialist": ["ear pain", "throat pain", "sore throat", "sinus"],
    "Dentist": ["tooth pain", "gum pain", "toothache"],
    "Pediatrician": ["child fever", "child cough", "infant", "baby"],
    "Gynecologist": ["pregnancy", "pregnancy pain", "pregnancy bleeding"],
    "Orthopedic": ["joint pain", "back pain", "fracture"],
    "Psychiatrist": ["anxiety", "panic", "sleep issue", "depression"],
    "Ophthalmologist": ["eye", "eye pain", "blurry vision", "redness in eye", "eye disease", "eye problem", "vision problem"],
    "Gastroenterologist": ["stomach pain", "abdominal pain", "vomiting", "diarrhea"],
    "Urologist": ["urine pain", "urinary pain", "kidney pain", "blood in urine"],
}


def _specialty_lookup(db: Session) -> dict[str, Specialty]:
    specialties = db.query(Specialty).all()
    return {specialty.name.lower(): specialty for specialty in specialties}


def _find_specialty(db: Session, name: str) -> Specialty | None:
    lookup = _specialty_lookup(db)
    return lookup.get(name.lower())


def _fallback_general(db: Session) -> Specialty | None:
    return _find_specialty(db, "General Physician") or db.query(Specialty).order_by(Specialty.id.asc()).first()


def recommend_specialty(structured_symptoms: dict, red_flag_result: dict, db: Session) -> dict:
    symptoms = set(structured_symptoms.get("main_symptoms", []))
    symptoms.update(structured_symptoms.get("body_parts", []))
    symptoms.update(structured_symptoms.get("associated_symptoms", []))
    text = " ".join(symptoms)
    if structured_symptoms.get("pregnancy_related"):
        text = f"{text} pregnancy"
    if structured_symptoms.get("patient_age_group") == "child":
        text = f"{text} child"

    if red_flag_result.get("urgency_level") == "emergency":
        selected = _find_specialty(db, "Emergency") or _fallback_general(db)
        secondary = _fallback_general(db)
        return {
            "recommended_specialty": selected,
            "secondary_specialty": secondary if secondary and selected and secondary.id != selected.id else None,
            "urgency_level": "emergency",
            "reason": "Emergency red flags were detected. Emergency care should be prioritized; a general physician is shown if emergency specialty is unavailable.",
            "confidence_score": 1.0,
        }

    scores: dict[str, int] = {}
    for specialty, keywords in SPECIALTY_KEYWORDS.items():
        scores[specialty] = sum(1 for keyword in keywords if keyword in text)

    best_name = max(scores, key=scores.get) if scores else "General Physician"
    if scores.get(best_name, 0) == 0:
        best_name = "General Physician"

    selected = _find_specialty(db, best_name) or _fallback_general(db)
    secondary = _fallback_general(db)
    if selected and selected.name == "General Physician":
        secondary = None

    confidence = min(0.95, 0.55 + (scores.get(best_name, 0) * 0.12))
    if best_name == "General Physician" and scores.get(best_name, 0) == 0:
        confidence = 0.55

    return {
        "recommended_specialty": selected,
        "secondary_specialty": secondary if secondary and selected and secondary.id != selected.id else None,
        "urgency_level": red_flag_result.get("urgency_level", "routine"),
        "reason": f"The symptoms are best routed to {selected.name if selected else 'General Physician'} based on symptom category.",
        "confidence_score": round(confidence, 2),
    }
