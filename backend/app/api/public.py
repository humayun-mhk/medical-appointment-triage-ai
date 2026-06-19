from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.ai.red_flag_engine import evaluate_red_flags
from app.ai.safety import validate_ai_response
from app.ai.specialty_router_agent import recommend_specialty
from app.ai.symptom_intake_agent import extract_symptoms
from app.db.database import get_db
from app.models import Doctor, DoctorSlot, SlotStatus, Specialty
from app.schemas import DoctorResponse, SlotResponse, SpecialtyResponse
from app.services import doctor_to_response
from app.services.simple_cache import cached_value

router = APIRouter(tags=["Public"])

PUBLIC_CACHE_TTL_SECONDS = 30


def _specialty_to_dict(specialty: Specialty) -> dict:
    return {
        "id": specialty.id,
        "name": specialty.name,
        "description": specialty.description,
        "created_at": specialty.created_at,
    }


def _doctor_to_cached_response(doctor: Doctor) -> dict:
    response = doctor_to_response(doctor)
    response["specialty"] = _specialty_to_dict(doctor.specialty)
    return response


@router.get("/specialties", response_model=list[SpecialtyResponse])
def get_specialties(db: Session = Depends(get_db)):
    return cached_value(
        "public:specialties",
        PUBLIC_CACHE_TTL_SECONDS,
        lambda: [_specialty_to_dict(specialty) for specialty in db.query(Specialty).order_by(Specialty.name.asc()).all()],
    )


@router.get("/doctors", response_model=list[DoctorResponse])
def get_doctors(
    specialty_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Doctor)
        .options(joinedload(Doctor.user), joinedload(Doctor.specialty))
        .filter(Doctor.is_available.is_(True))
    )
    if specialty_id is not None:
        query = query.filter(Doctor.specialty_id == specialty_id)
    return cached_value(
        f"public:doctors:{specialty_id or 'all'}",
        PUBLIC_CACHE_TTL_SECONDS,
        lambda: [_doctor_to_cached_response(doctor) for doctor in query.order_by(Doctor.id.desc()).all()],
    )


@router.get("/doctors/recommend")
def recommend_doctors_by_symptoms(
    symptoms: str = Query(..., min_length=2, max_length=1000),
    db: Session = Depends(get_db),
):
    structured = extract_symptoms(symptoms)
    red_flags = evaluate_red_flags(structured, symptoms)
    specialty_result = recommend_specialty(structured, red_flags, db)
    recommended = specialty_result["recommended_specialty"]
    secondary = specialty_result["secondary_specialty"]

    specialty_ids = [specialty.id for specialty in [recommended, secondary] if specialty is not None]
    query = (
        db.query(Doctor)
        .options(joinedload(Doctor.user), joinedload(Doctor.specialty))
        .filter(Doctor.is_available.is_(True))
    )
    if specialty_ids:
        query = query.filter(Doctor.specialty_id.in_(specialty_ids))
    doctors = query.order_by(Doctor.rating.desc(), Doctor.id.desc()).all()
    safe_reason = validate_ai_response(specialty_result["reason"])["corrected_text"]
    return {
        "recommended_specialty": {
            "id": recommended.id,
            "name": recommended.name,
        }
        if recommended
        else None,
        "secondary_specialty": {
            "id": secondary.id,
            "name": secondary.name,
        }
        if secondary
        else None,
        "urgency_level": red_flags["urgency_level"],
        "red_flag_status": red_flags["red_flag_status"],
        "reason": safe_reason,
        "safety_message": red_flags["safety_message"],
        "doctors": [doctor_to_response(doctor) for doctor in doctors],
    }


@router.get("/doctors/{doctor_id}", response_model=DoctorResponse)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = (
        db.query(Doctor)
        .options(joinedload(Doctor.user), joinedload(Doctor.specialty))
        .filter(Doctor.id == doctor_id)
        .first()
    )
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    return doctor_to_response(doctor)


@router.get("/doctors/{doctor_id}/slots", response_model=list[SlotResponse])
def get_doctor_slots(
    doctor_id: int,
    selected_date: date | None = Query(default=None, alias="date"),
    db: Session = Depends(get_db),
):
    query = db.query(DoctorSlot).filter(
        DoctorSlot.doctor_id == doctor_id,
        DoctorSlot.status == SlotStatus.available,
    )
    if selected_date is not None:
        query = query.filter(func.date(DoctorSlot.start_time) == selected_date)
    return query.order_by(DoctorSlot.start_time.asc()).all()
