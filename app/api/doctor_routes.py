from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from uuid import UUID

from app.database.session import get_session

from app.models.doctor import Doctor

from app.schemas.doctor import (
    DoctorCreate,
    DoctorRead,
    DoctorUpdate
)

router = APIRouter(
    prefix="/doctors",
    tags=["Doctors"]
)


# CREATE DOCTOR
@router.post("/", response_model=DoctorRead)
def create_doctor(
    doctor: DoctorCreate,
    session: Session = Depends(get_session)
):
    db_doctor = Doctor(
        name=doctor.name,
        specialization=doctor.specialization,
        department=doctor.department
    )

    session.add(db_doctor)
    session.commit()
    session.refresh(db_doctor)

    return db_doctor


# GET ALL DOCTORS
@router.get("/", response_model=list[DoctorRead])
def get_doctors(
    session: Session = Depends(get_session)
):
    doctors = session.exec(
        select(Doctor)
    ).all()

    return doctors


# GET SINGLE DOCTOR
@router.get("/{doctor_id}", response_model=DoctorRead)
def get_doctor(
    doctor_id: UUID,
    session: Session = Depends(get_session)
):
    doctor = session.get(
        Doctor,
        doctor_id
    )

    if not doctor:
        raise HTTPException(
            status_code=404,
            detail="Doctor not found"
        )

    return doctor


# UPDATE DOCTOR
@router.patch("/{doctor_id}", response_model=DoctorRead)
def update_doctor(
    doctor_id: int,
    doctor_update: DoctorUpdate,
    session: Session = Depends(get_session)
):
    doctor = session.get(
        Doctor,
        doctor_id
    )

    if not doctor:
        raise HTTPException(
            status_code=404,
            detail="Doctor not found"
        )

    update_data = doctor_update.model_dump(
        exclude_unset=True
    )

    for key, value in update_data.items():
        setattr(doctor, key, value)

    session.add(doctor)
    session.commit()
    session.refresh(doctor)

    return doctor


# DELETE DOCTOR
@router.delete("/{doctor_id}")
def delete_doctor(
    doctor_id: int,
    session: Session = Depends(get_session)
):
    doctor = session.get(
        Doctor,
        doctor_id
    )

    if not doctor:
        raise HTTPException(
            status_code=404,
            detail="Doctor not found"
        )

    session.delete(doctor)
    session.commit()

    return {
        "message": "Doctor deleted successfully"
    }

