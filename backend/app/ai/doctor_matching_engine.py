from datetime import datetime, timezone

from sqlalchemy.orm import Session, joinedload

from app.ai.safety import emergency_message
from app.models import Doctor, DoctorSlot, SlotStatus, SymptomSession
from app.services.serializers import doctor_avatar_url


def _availability_points(hours_until_slot: float) -> int:
    if hours_until_slot <= 24:
        return 25
    if hours_until_slot <= 72:
        return 18
    if hours_until_slot <= 168:
        return 12
    return 8


def _urgency_points(urgency: str, hours_until_slot: float) -> int:
    if urgency in {"emergency", "urgent"}:
        if hours_until_slot <= 24:
            return 20
        if hours_until_slot <= 72:
            return 12
        return 6
    if urgency == "soon":
        return 18 if hours_until_slot <= 72 else 12
    return 15


def match_doctors(session_id: int, db: Session, patient_preferences: dict | None = None) -> list[dict]:
    patient_preferences = patient_preferences or {}
    session = (
        db.query(SymptomSession)
        .options(
            joinedload(SymptomSession.recommended_specialty),
            joinedload(SymptomSession.secondary_specialty),
        )
        .filter(SymptomSession.id == session_id)
        .first()
    )
    if session is None or session.recommended_specialty_id is None:
        return []

    specialty_ids = [session.recommended_specialty_id]
    include_secondary = session.secondary_specialty_id is not None
    if include_secondary:
        specialty_ids.append(session.secondary_specialty_id)

    now = datetime.now(timezone.utc)
    slots = (
        db.query(DoctorSlot)
        .options(
            joinedload(DoctorSlot.doctor).joinedload(Doctor.user),
            joinedload(DoctorSlot.doctor).joinedload(Doctor.specialty),
        )
        .join(Doctor, DoctorSlot.doctor_id == Doctor.id)
        .filter(
            Doctor.specialty_id.in_(specialty_ids),
            Doctor.is_available.is_(True),
            DoctorSlot.status == SlotStatus.available,
            DoctorSlot.start_time > now,
        )
        .order_by(DoctorSlot.start_time.asc())
        .all()
    )

    earliest_by_doctor: dict[int, DoctorSlot] = {}
    for slot in slots:
        if slot.doctor_id not in earliest_by_doctor:
            earliest_by_doctor[slot.doctor_id] = slot

    recommendations = []
    for slot in earliest_by_doctor.values():
        doctor = slot.doctor
        hours_until = max((slot.start_time - now).total_seconds() / 3600, 0)
        specialty_match = 40 if doctor.specialty_id == session.recommended_specialty_id else 30
        available_soon = _availability_points(hours_until)
        urgency_fit = _urgency_points(session.urgency_level.value, hours_until)
        rating_points = min(10, round((doctor.rating or 0) / 5 * 10))
        location_points = 0
        if patient_preferences.get("city") and doctor.city:
            location_points = 5 if patient_preferences["city"].lower() == doctor.city.lower() else 1
        elif doctor.city:
            location_points = 2

        breakdown = {
            "specialty_match": specialty_match,
            "available_soon": available_soon,
            "urgency_fit": urgency_fit,
            "rating": rating_points,
            "location": location_points,
        }
        score = sum(breakdown.values())
        recommendations.append(
            {
                "doctor_id": doctor.id,
                "doctor_name": doctor.user.full_name,
                "image_url": doctor_avatar_url(doctor),
                "specialty": doctor.specialty.name,
                "score": score,
                "score_breakdown": breakdown,
                "next_available_slot": {
                    "slot_id": slot.id,
                    "start_time": slot.start_time,
                    "end_time": slot.end_time,
                },
                "consultation_fee": doctor.consultation_fee,
                "rating": doctor.rating,
                "total_reviews": doctor.total_reviews,
                "clinic_address": doctor.clinic_address,
                "city": doctor.city,
                "reason": (
                    f"Best match because this doctor belongs to {doctor.specialty.name} "
                    "and has an available upcoming slot."
                ),
                "emergency_warning": emergency_message() if session.urgency_level.value == "emergency" else None,
            }
        )

    if session.urgency_level.value == "emergency":
        recommendations.sort(key=lambda item: item["next_available_slot"]["start_time"])
    else:
        recommendations.sort(key=lambda item: (-item["score"], item["consultation_fee"]))
    return recommendations
