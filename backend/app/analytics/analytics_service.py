from collections import Counter
from datetime import datetime, time, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models import (
    Appointment,
    AppointmentStatus,
    Doctor,
    DoctorSlot,
    HumanReviewCase,
    NotificationLog,
    NotificationStatus,
    ReviewStatus,
    SlotStatus,
    Specialty,
    SymptomSession,
    TriageUrgency,
)


def _period_bounds():
    now = datetime.now(timezone.utc)
    today_start = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)
    today_end = today_start + timedelta(days=1)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)
    return now, today_start, today_end, week_start, month_start


def overview(db: Session) -> dict:
    _, today_start, today_end, week_start, month_start = _period_bounds()
    confidences = [value for (value,) in db.query(SymptomSession.ai_confidence).filter(SymptomSession.ai_confidence.isnot(None)).all()]
    return {
        "total_appointments": db.query(Appointment).count(),
        "appointments_today": db.query(Appointment).join(DoctorSlot).filter(DoctorSlot.start_time >= today_start, DoctorSlot.start_time < today_end).count(),
        "appointments_this_week": db.query(Appointment).join(DoctorSlot).filter(DoctorSlot.start_time >= week_start).count(),
        "appointments_this_month": db.query(Appointment).join(DoctorSlot).filter(DoctorSlot.start_time >= month_start).count(),
        "completed_appointments": db.query(Appointment).filter(Appointment.status == AppointmentStatus.completed).count(),
        "cancelled_appointments": db.query(Appointment).filter(Appointment.status == AppointmentStatus.cancelled).count(),
        "no_show_appointments": db.query(Appointment).filter(Appointment.status == AppointmentStatus.no_show).count(),
        "urgent_cases": db.query(SymptomSession).filter(SymptomSession.urgency_level == TriageUrgency.urgent).count(),
        "red_flag_cases": db.query(SymptomSession).filter(SymptomSession.red_flag_status.is_(True)).count(),
        "average_ai_confidence": round(sum(confidences) / len(confidences), 3) if confidences else 0,
        "pending_review_cases": db.query(HumanReviewCase).filter(HumanReviewCase.status == ReviewStatus.pending).count(),
    }


def appointment_status_distribution(db: Session) -> list[dict]:
    rows = db.query(Appointment.status, func.count(Appointment.id)).group_by(Appointment.status).all()
    counts = {status.value if hasattr(status, "value") else status: count for status, count in rows}
    return [{"status": status.value, "count": counts.get(status.value, 0)} for status in AppointmentStatus]


def triage_urgency_distribution(db: Session) -> list[dict]:
    rows = db.query(SymptomSession.urgency_level, func.count(SymptomSession.id)).group_by(SymptomSession.urgency_level).all()
    counts = {level.value if hasattr(level, "value") else level: count for level, count in rows}
    return [{"urgency": urgency.value, "count": counts.get(urgency.value, 0)} for urgency in TriageUrgency]


def most_common_symptoms(db: Session, limit: int = 10) -> list[dict]:
    counter: Counter[str] = Counter()
    sessions = db.query(SymptomSession.structured_symptoms).all()
    for (structured,) in sessions:
        for symptom in (structured or {}).get("main_symptoms", []):
            counter[str(symptom).lower()] += 1
    return [{"symptom": symptom, "count": count} for symptom, count in counter.most_common(limit)]


def most_booked_specialties(db: Session, limit: int = 10) -> list[dict]:
    rows = (
        db.query(Specialty.name, func.count(Appointment.id))
        .join(Doctor, Doctor.specialty_id == Specialty.id)
        .join(Appointment, Appointment.doctor_id == Doctor.id)
        .group_by(Specialty.name)
        .order_by(func.count(Appointment.id).desc())
        .limit(limit)
        .all()
    )
    return [{"specialty": name, "count": count} for name, count in rows]


def doctor_utilization(db: Session) -> list[dict]:
    doctors = db.query(Doctor).options(joinedload(Doctor.user)).all()
    rows = []
    for doctor in doctors:
        total_slots = db.query(DoctorSlot).filter(DoctorSlot.doctor_id == doctor.id).count()
        booked_slots = db.query(DoctorSlot).filter(DoctorSlot.doctor_id == doctor.id, DoctorSlot.status == SlotStatus.booked).count()
        rows.append(
            {
                "doctor_id": doctor.id,
                "doctor_name": doctor.user.full_name,
                "total_slots": total_slots,
                "booked_slots": booked_slots,
                "utilization_rate": round((booked_slots / total_slots) * 100, 1) if total_slots else 0,
            }
        )
    return rows


def ai_metrics(db: Session) -> dict:
    confidences = [value for (value,) in db.query(SymptomSession.ai_confidence).filter(SymptomSession.ai_confidence.isnot(None)).all()]
    return {
        "average_confidence": round(sum(confidences) / len(confidences), 3) if confidences else 0,
        "low_confidence_cases": db.query(SymptomSession).filter(SymptomSession.ai_confidence < 0.60).count(),
        "red_flag_cases": db.query(SymptomSession).filter(SymptomSession.red_flag_status.is_(True)).count(),
        "review_cases": db.query(HumanReviewCase).count(),
        "urgency_distribution": triage_urgency_distribution(db),
    }


def notification_metrics(db: Session) -> dict:
    rows = db.query(NotificationLog.status, func.count(NotificationLog.id)).group_by(NotificationLog.status).all()
    counts = {status.value if hasattr(status, "value") else status: count for status, count in rows}
    total = sum(counts.values())
    return {
        "sent": counts.get(NotificationStatus.sent.value, 0),
        "failed": counts.get(NotificationStatus.failed.value, 0),
        "pending": counts.get(NotificationStatus.pending.value, 0),
        "total": total,
        "success_rate": round((counts.get(NotificationStatus.sent.value, 0) / total) * 100, 1) if total else 0,
    }


def bookings_from_triage_vs_manual(db: Session) -> dict:
    triage = db.query(Appointment).filter(Appointment.triage_session_id.isnot(None)).count()
    manual = db.query(Appointment).filter(Appointment.triage_session_id.is_(None)).count()
    return {"triage": triage, "manual": manual}
