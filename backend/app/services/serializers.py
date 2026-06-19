from urllib.parse import quote

from app.models import Appointment, Doctor, PatientProfile


def doctor_avatar_url(doctor: Doctor) -> str:
    seed = quote(f"doctor-{doctor.id}-{doctor.user.full_name}".lower())
    return (
        "https://api.dicebear.com/10.x/personas/svg"
        f"?seed={seed}&backgroundColor=d1fae5,dbeafe,fef3c7,fee2e2"
        "&radius=12"
    )


def doctor_to_response(doctor: Doctor) -> dict:
    return {
        "id": doctor.id,
        "user_id": doctor.user_id,
        "full_name": doctor.user.full_name,
        "email": doctor.user.email,
        "image_url": doctor_avatar_url(doctor),
        "specialty": doctor.specialty,
        "qualification": doctor.qualification,
        "experience_years": doctor.experience_years,
        "bio": doctor.bio,
        "consultation_fee": doctor.consultation_fee,
        "clinic_address": doctor.clinic_address,
        "rating": doctor.rating,
        "total_reviews": doctor.total_reviews,
        "city": doctor.city,
        "is_available": doctor.is_available,
        "created_at": doctor.created_at,
        "updated_at": doctor.updated_at,
    }


def patient_basic_info(patient: PatientProfile) -> dict:
    return {
        "id": patient.id,
        "user_id": patient.user_id,
        "full_name": patient.user.full_name,
        "email": patient.user.email,
        "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
        "gender": patient.gender,
        "phone": patient.phone,
        "blood_group": patient.blood_group,
        "allergies": patient.allergies,
        "chronic_conditions": patient.chronic_conditions,
        "emergency_contact": patient.emergency_contact,
    }


def doctor_appointment_to_response(appointment: Appointment) -> dict:
    triage = appointment.triage_session
    return {
        "appointment_id": appointment.id,
        "patient": patient_basic_info(appointment.patient),
        "symptoms": appointment.symptoms,
        "patient_notes": appointment.patient_notes,
        "doctor_notes": appointment.doctor_notes,
        "doctor_summary": appointment.doctor_summary,
        "triage_session_id": appointment.triage_session_id,
        "urgency_level": triage.urgency_level.value if triage else None,
        "red_flag_status": triage.red_flag_status if triage else None,
        "structured_symptoms": triage.structured_symptoms if triage else None,
        "recommended_specialty": triage.recommended_specialty.name if triage and triage.recommended_specialty else None,
        "ai_confidence": triage.ai_confidence if triage else None,
        "slot_start_time": appointment.slot.start_time,
        "slot_end_time": appointment.slot.end_time,
        "status": appointment.status,
    }


def admin_appointment_to_response(appointment: Appointment) -> dict:
    triage = appointment.triage_session
    return {
        "id": appointment.id,
        "patient_name": appointment.patient.user.full_name,
        "doctor_name": appointment.doctor.user.full_name,
        "specialty": appointment.doctor.specialty.name,
        "start_time": appointment.slot.start_time,
        "end_time": appointment.slot.end_time,
        "status": appointment.status,
        "symptoms": appointment.symptoms,
        "urgency_level": triage.urgency_level.value if triage else None,
        "red_flag_status": triage.red_flag_status if triage else None,
        "triage_session_id": appointment.triage_session_id,
    }
