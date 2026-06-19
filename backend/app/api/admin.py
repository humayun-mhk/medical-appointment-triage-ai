from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import require_admin
from app.core.security import hash_password
from app.db.database import get_db
from app.models import (
    Appointment,
    AppointmentStatus,
    Doctor,
    DoctorSlot,
    PatientProfile,
    SlotStatus,
    Specialty,
    SymptomSession,
    User,
    UserRole,
)
from app.schemas import (
    AdminAppointmentResponse,
    AdminDoctorResponse,
    AdminPatientResponse,
    AdminSlotCreateRequest,
    DashboardStatsResponse,
    DoctorCreateRequest,
    DoctorUpdateRequest,
    SlotResponse,
    SpecialtyCreateRequest,
    SpecialtyResponse,
)
from app.security.audit_logger import log_security_event
from app.security.rate_limit import admin_rate_limit
from app.services import admin_appointment_to_response, create_doctor_slot, doctor_to_response
from app.services.simple_cache import clear_cache_prefix

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(require_admin), Depends(admin_rate_limit)])


def _get_specialty(db: Session, specialty_id: int) -> Specialty:
    specialty = db.get(Specialty, specialty_id)
    if specialty is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specialty not found")
    return specialty


@router.post("/specialties", response_model=SpecialtyResponse, status_code=status.HTTP_201_CREATED)
def create_specialty(payload: SpecialtyCreateRequest, db: Session = Depends(get_db)):
    existing = db.query(Specialty).filter(func.lower(Specialty.name) == payload.name.lower()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Specialty already exists")
    specialty = Specialty(name=payload.name.strip(), description=payload.description)
    db.add(specialty)
    db.commit()
    db.refresh(specialty)
    clear_cache_prefix("public:specialties")
    return specialty


@router.get("/specialties", response_model=list[SpecialtyResponse])
def list_specialties(db: Session = Depends(get_db)):
    return db.query(Specialty).order_by(Specialty.name.asc()).all()


@router.post("/doctors", response_model=AdminDoctorResponse, status_code=status.HTTP_201_CREATED)
def create_doctor(payload: DoctorCreateRequest, db: Session = Depends(get_db)):
    _get_specialty(db, payload.specialty_id)
    email = payload.email.lower()
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    user = User(
        full_name=payload.full_name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        role=UserRole.doctor,
    )
    db.add(user)
    db.flush()
    doctor = Doctor(
        user_id=user.id,
        specialty_id=payload.specialty_id,
        qualification=payload.qualification,
        experience_years=payload.experience_years,
        bio=payload.bio,
        consultation_fee=payload.consultation_fee,
        clinic_address=payload.clinic_address,
        city=payload.city,
    )
    db.add(doctor)
    db.commit()
    doctor = (
        db.query(Doctor)
        .options(joinedload(Doctor.user), joinedload(Doctor.specialty))
        .filter(Doctor.id == doctor.id)
        .first()
    )
    clear_cache_prefix("public:doctors")
    return doctor_to_response(doctor)


@router.get("/doctors", response_model=list[AdminDoctorResponse])
def list_doctors(db: Session = Depends(get_db)):
    doctors = (
        db.query(Doctor)
        .options(joinedload(Doctor.user), joinedload(Doctor.specialty))
        .order_by(Doctor.id.desc())
        .all()
    )
    return [doctor_to_response(doctor) for doctor in doctors]


@router.patch("/doctors/{doctor_id}", response_model=AdminDoctorResponse)
def update_doctor(
    doctor_id: int,
    payload: DoctorUpdateRequest,
    db: Session = Depends(get_db),
):
    doctor = (
        db.query(Doctor)
        .options(joinedload(Doctor.user), joinedload(Doctor.specialty))
        .filter(Doctor.id == doctor_id)
        .first()
    )
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    values = payload.model_dump(exclude_unset=True)
    if "specialty_id" in values and values["specialty_id"] is not None:
        _get_specialty(db, values["specialty_id"])
    for key, value in values.items():
        setattr(doctor, key, value)
    db.commit()
    db.refresh(doctor)
    clear_cache_prefix("public:doctors")
    return doctor_to_response(doctor)


@router.post("/slots", response_model=SlotResponse, status_code=status.HTTP_201_CREATED)
def create_slot(payload: AdminSlotCreateRequest, db: Session = Depends(get_db)):
    return create_doctor_slot(db, payload.doctor_id, payload.start_time, payload.end_time)


@router.get("/appointments", response_model=list[AdminAppointmentResponse])
def list_appointments(
    status_filter: AppointmentStatus | None = Query(default=None, alias="status"),
    doctor_id: int | None = Query(default=None),
    patient_id: int | None = Query(default=None),
    selected_date: date | None = Query(default=None, alias="date"),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Appointment)
        .options(
            joinedload(Appointment.patient).joinedload(PatientProfile.user),
            joinedload(Appointment.doctor).joinedload(Doctor.user),
            joinedload(Appointment.doctor).joinedload(Doctor.specialty),
            joinedload(Appointment.slot),
            joinedload(Appointment.triage_session).joinedload(SymptomSession.recommended_specialty),
        )
        .join(DoctorSlot, Appointment.slot_id == DoctorSlot.id)
    )
    if status_filter is not None:
        query = query.filter(Appointment.status == status_filter)
    if doctor_id is not None:
        query = query.filter(Appointment.doctor_id == doctor_id)
    if patient_id is not None:
        query = query.filter(Appointment.patient_id == patient_id)
    if selected_date is not None:
        query = query.filter(func.date(DoctorSlot.start_time) == selected_date)
    appointments = query.order_by(DoctorSlot.start_time.desc()).all()
    return [admin_appointment_to_response(appointment) for appointment in appointments]


@router.get("/patients", response_model=list[AdminPatientResponse])
def list_patients(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    patients = (
        db.query(PatientProfile)
        .options(joinedload(PatientProfile.user))
        .order_by(PatientProfile.id.desc())
        .all()
    )
    log_security_event(
        db,
        action="admin_viewed_patient_data",
        resource_type="patient_profile",
        request=request,
        user_id=current_user.id,
        metadata={"count": len(patients)},
    )
    db.commit()
    return [
        {
            "id": patient.id,
            "user_id": patient.user_id,
            "full_name": patient.user.full_name,
            "email": patient.user.email,
            "phone": patient.phone,
            "gender": patient.gender,
            "blood_group": patient.blood_group,
            "date_of_birth": patient.date_of_birth,
        }
        for patient in patients
    ]


@router.get("/dashboard", response_model=DashboardStatsResponse)
def dashboard(db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    today_start = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)
    today_end = today_start + timedelta(days=1)

    total_patients = db.query(PatientProfile).count()
    total_doctors = db.query(Doctor).count()
    total_appointments = db.query(Appointment).count()
    todays_appointments = (
        db.query(Appointment)
        .join(DoctorSlot, Appointment.slot_id == DoctorSlot.id)
        .filter(DoctorSlot.start_time >= today_start, DoctorSlot.start_time < today_end)
        .count()
    )
    completed_appointments = (
        db.query(Appointment).filter(Appointment.status == AppointmentStatus.completed).count()
    )
    cancelled_appointments = (
        db.query(Appointment).filter(Appointment.status == AppointmentStatus.cancelled).count()
    )
    available_slots = db.query(DoctorSlot).filter(DoctorSlot.status == SlotStatus.available).count()
    return {
        "total_patients": total_patients,
        "total_doctors": total_doctors,
        "total_appointments": total_appointments,
        "todays_appointments": todays_appointments,
        "completed_appointments": completed_appointments,
        "cancelled_appointments": cancelled_appointments,
        "available_slots": available_slots,
    }
