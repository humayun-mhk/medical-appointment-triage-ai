from sqlalchemy.orm import Session

from app.analytics.analytics_service import (
    ai_metrics,
    appointment_status_distribution,
    bookings_from_triage_vs_manual,
    doctor_utilization,
    most_booked_specialties,
    most_common_symptoms,
    notification_metrics,
    overview,
    triage_urgency_distribution,
)


def full_dashboard(db: Session) -> dict:
    return {
        "overview": overview(db),
        "appointment_status_distribution": appointment_status_distribution(db),
        "triage_urgency_distribution": triage_urgency_distribution(db),
        "most_common_symptoms": most_common_symptoms(db),
        "most_booked_specialties": most_booked_specialties(db),
        "doctor_utilization": doctor_utilization(db),
        "ai": ai_metrics(db),
        "notifications": notification_metrics(db),
        "bookings_source": bookings_from_triage_vs_manual(db),
    }
