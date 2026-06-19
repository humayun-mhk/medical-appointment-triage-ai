from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.analytics.analytics_service import (
    ai_metrics,
    appointment_status_distribution,
    doctor_utilization,
    most_booked_specialties,
    most_common_symptoms,
    notification_metrics,
    overview,
    triage_urgency_distribution,
)
from app.core.dependencies import require_admin
from app.db.database import get_db
from app.security.rate_limit import admin_rate_limit

router = APIRouter(prefix="/admin/analytics", tags=["Analytics"], dependencies=[Depends(require_admin), Depends(admin_rate_limit)])


@router.get("/overview")
def analytics_overview(db: Session = Depends(get_db)):
    return overview(db)


@router.get("/symptoms")
def analytics_symptoms(db: Session = Depends(get_db)):
    return most_common_symptoms(db)


@router.get("/specialties")
def analytics_specialties(db: Session = Depends(get_db)):
    return most_booked_specialties(db)


@router.get("/doctors")
def analytics_doctors(db: Session = Depends(get_db)):
    return doctor_utilization(db)


@router.get("/ai")
def analytics_ai(db: Session = Depends(get_db)):
    return {
        **ai_metrics(db),
        "appointment_status_distribution": appointment_status_distribution(db),
        "triage_urgency_distribution": triage_urgency_distribution(db),
    }


@router.get("/notifications")
def analytics_notifications(db: Session = Depends(get_db)):
    return notification_metrics(db)
