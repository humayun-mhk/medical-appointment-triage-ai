from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models import Doctor, DoctorSlot, SlotStatus


def ensure_future_slot_times(start_time: datetime, end_time: datetime) -> None:
    if start_time >= end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_time must be before end_time",
        )
    now = datetime.now(timezone.utc)
    comparable_start = start_time if start_time.tzinfo else start_time.replace(tzinfo=timezone.utc)
    if comparable_start <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slot start_time must be in the future",
        )


def ensure_doctor_exists(db: Session, doctor_id: int) -> Doctor:
    doctor = db.get(Doctor, doctor_id)
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    return doctor


def has_overlapping_slot(
    db: Session,
    doctor_id: int,
    start_time: datetime,
    end_time: datetime,
) -> bool:
    return (
        db.query(DoctorSlot)
        .filter(
            DoctorSlot.doctor_id == doctor_id,
            DoctorSlot.status != SlotStatus.cancelled,
            and_(DoctorSlot.start_time < end_time, DoctorSlot.end_time > start_time),
        )
        .first()
        is not None
    )


def create_doctor_slot(
    db: Session,
    doctor_id: int,
    start_time: datetime,
    end_time: datetime,
) -> DoctorSlot:
    ensure_doctor_exists(db, doctor_id)
    ensure_future_slot_times(start_time, end_time)
    if has_overlapping_slot(db, doctor_id, start_time, end_time):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Slot overlaps an existing slot for this doctor",
        )
    slot = DoctorSlot(
        doctor_id=doctor_id,
        start_time=start_time,
        end_time=end_time,
        status=SlotStatus.available,
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot
