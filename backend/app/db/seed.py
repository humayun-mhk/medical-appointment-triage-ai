from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from app.core.security import hash_password
from app.db.database import SessionLocal
from app.models import Doctor, DoctorSlot, PatientProfile, SlotStatus, Specialty, User, UserRole
from app.rag.document_loader import chunk_document, load_documents_from_folder, save_chunks_to_db, save_document_to_db


SPECIALTIES = [
    ("General Physician", "Primary care, routine health checks, and common illnesses."),
    ("Cardiologist", "Heart and cardiovascular care."),
    ("Dermatologist", "Skin, hair, and nail conditions."),
    ("ENT Specialist", "Ear, nose, and throat care."),
    ("Dentist", "Dental health and oral care."),
    ("Pediatrician", "Healthcare for infants, children, and adolescents."),
    ("Gynecologist", "Women's reproductive health."),
    ("Orthopedic", "Bone, joint, and musculoskeletal care."),
    ("Psychiatrist", "Mental health diagnosis and treatment."),
    ("Ophthalmologist", "Eye health and vision care."),
    ("Gastroenterologist", "Digestive system and liver care."),
    ("Urologist", "Urinary tract and male reproductive health."),
]


def get_or_create_user(db, full_name: str, email: str, password: str, role: UserRole) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user
    user = User(
        full_name=full_name,
        email=email,
        password_hash=hash_password(password),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def run() -> None:
    db = SessionLocal()
    try:
        specialties_by_name: dict[str, Specialty] = {}
        for name, description in SPECIALTIES:
            specialty = db.query(Specialty).filter(Specialty.name == name).first()
            if specialty is None:
                specialty = Specialty(name=name, description=description)
                db.add(specialty)
                db.flush()
            specialties_by_name[name] = specialty

        get_or_create_user(db, "System Admin", "admin@healthcare.local", "Admin123!", UserRole.admin)

        patient_user = get_or_create_user(
            db,
            "Priya Patient",
            "patient@healthcare.local",
            "Patient123!",
            UserRole.patient,
        )
        if patient_user.patient_profile is None:
            db.add(
                PatientProfile(
                    user_id=patient_user.id,
                    date_of_birth=date(1992, 4, 12),
                    gender="Female",
                    phone="+1 555 0100",
                    address="120 Wellness Ave",
                    blood_group="O+",
                    allergies="None",
                    chronic_conditions="None",
                    emergency_contact="+1 555 0101",
                )
            )

        samples = [
            {
                "full_name": "Dr. Amir Khan",
                "email": "doctor@healthcare.local",
                "password": "Doctor123!",
                "specialty": "General Physician",
                "qualification": "MBBS, FCPS",
                "experience_years": 11,
                "bio": "Focused on preventive care, chronic disease management, and clear patient communication.",
                "consultation_fee": Decimal("75.00"),
                "clinic_address": "Care Clinic, 45 Main Street",
                "city": "New York",
                "rating": 4.7,
                "total_reviews": 128,
            },
            {
                "full_name": "Dr. Sara Mitchell",
                "email": "cardio@healthcare.local",
                "password": "Doctor123!",
                "specialty": "Cardiologist",
                "qualification": "MD Cardiology",
                "experience_years": 14,
                "bio": "Cardiac care specialist with an emphasis on hypertension and long-term heart health.",
                "consultation_fee": Decimal("125.00"),
                "clinic_address": "Heart Center, 200 North Plaza",
                "city": "New York",
                "rating": 4.8,
                "total_reviews": 94,
            },
            {
                "full_name": "Dr. Lina Patel",
                "email": "ent@healthcare.local",
                "password": "Doctor123!",
                "specialty": "ENT Specialist",
                "qualification": "MS ENT",
                "experience_years": 9,
                "bio": "ENT specialist for ear, throat, sinus, and upper respiratory concerns.",
                "consultation_fee": Decimal("95.00"),
                "clinic_address": "ENT Care, 12 Lake Road",
                "city": "New York",
                "rating": 4.6,
                "total_reviews": 81,
            },
            {
                "full_name": "Dr. Naomi Brooks",
                "email": "derm@healthcare.local",
                "password": "Doctor123!",
                "specialty": "Dermatologist",
                "qualification": "MD Dermatology",
                "experience_years": 8,
                "bio": "Dermatology care for rash, itching, acne, and skin irritation.",
                "consultation_fee": Decimal("105.00"),
                "clinic_address": "Skin Health Center, 88 Cedar Ave",
                "city": "Brooklyn",
                "rating": 4.5,
                "total_reviews": 63,
            },
            {
                "full_name": "Dr. Omar Reyes",
                "email": "gastro@healthcare.local",
                "password": "Doctor123!",
                "specialty": "Gastroenterologist",
                "qualification": "MD Gastroenterology",
                "experience_years": 12,
                "bio": "Digestive health specialist for abdominal pain, vomiting, and diarrhea routing.",
                "consultation_fee": Decimal("115.00"),
                "clinic_address": "Digestive Care Clinic, 300 Pine Street",
                "city": "Queens",
                "rating": 4.7,
                "total_reviews": 77,
            },
            {
                "full_name": "Dr. Elena Morris",
                "email": "eye@healthcare.local",
                "password": "Doctor123!",
                "specialty": "Ophthalmologist",
                "qualification": "MS Ophthalmology",
                "experience_years": 10,
                "bio": "Eye care specialist for eye pain, redness, and vision concerns.",
                "consultation_fee": Decimal("110.00"),
                "clinic_address": "Vision Clinic, 14 Market Lane",
                "city": "New York",
                "rating": 4.6,
                "total_reviews": 59,
            },
        ]

        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        for sample in samples:
            user = get_or_create_user(
                db,
                sample["full_name"],
                sample["email"],
                sample["password"],
                UserRole.doctor,
            )
            doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
            if doctor is None:
                doctor = Doctor(
                    user_id=user.id,
                    specialty_id=specialties_by_name[sample["specialty"]].id,
                    qualification=sample["qualification"],
                    experience_years=sample["experience_years"],
                    bio=sample["bio"],
                    consultation_fee=sample["consultation_fee"],
                    clinic_address=sample["clinic_address"],
                    city=sample["city"],
                    rating=sample["rating"],
                    total_reviews=sample["total_reviews"],
                    is_available=True,
                )
                db.add(doctor)
                db.flush()
            else:
                doctor.city = sample["city"]
                doctor.rating = sample["rating"]
                doctor.total_reviews = sample["total_reviews"]

            existing_slots = db.query(DoctorSlot).filter(DoctorSlot.doctor_id == doctor.id).count()
            if existing_slots == 0:
                for day in range(1, 6):
                    start = now + timedelta(days=day, hours=9)
                    db.add(
                        DoctorSlot(
                            doctor_id=doctor.id,
                            start_time=start,
                            end_time=start + timedelta(minutes=30),
                            status=SlotStatus.available,
                        )
                    )
                    db.add(
                        DoctorSlot(
                            doctor_id=doctor.id,
                            start_time=start + timedelta(hours=1),
                            end_time=start + timedelta(hours=1, minutes=30),
                            status=SlotStatus.available,
                        )
                    )

        db.commit()
        knowledge_folder = Path(__file__).resolve().parents[2] / "knowledge_base"
        if knowledge_folder.exists():
            for document_data in load_documents_from_folder(str(knowledge_folder)):
                document = save_document_to_db(
                    document_data["title"],
                    document_data["category"],
                    document_data["source"],
                    document_data["content"],
                    document_data["metadata"],
                    db,
                )
                save_chunks_to_db(document.id, chunk_document(document.content), db)
            db.commit()
        print("Seed data created successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
