from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database.session import get_session

from app.models.appointments import Appointment
from app.models.doctor import Doctor

from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentRead,
    AppointmentUpdate
)

router = APIRouter(
    prefix="/appointments",
    tags=["Appointments"]
)


# CREATE APPOINTMENT
@router.post("/", response_model=AppointmentRead)
def create_appointment(
    appointment: AppointmentCreate,
    session: Session = Depends(get_session)
):

    # CHECK DOCTOR EXISTS
    doctor = session.get(
        Doctor,
        appointment.doctor_id
    )

    if not doctor:
        raise HTTPException(
            status_code=404,
            detail="Doctor not found"
        )

    db_appointment = Appointment(
        patient_name=appointment.patient_name,
        patient_phone=appointment.patient_phone,
        appointment_time=appointment.appointment_time,
        doctor_id=appointment.doctor_id,
        doctor_name=doctor.name,
        notes=appointment.notes
    )

    session.add(db_appointment)
    session.commit()
    session.refresh(db_appointment)

    return db_appointment


# GET ALL APPOINTMENTS
@router.get("/", response_model=list[AppointmentRead])
def get_appointments(
    session: Session = Depends(get_session)
):
    appointments = session.exec(
        select(Appointment)
    ).all()

    return appointments


# GET SINGLE APPOINTMENT
@router.get("/{appointment_id}", response_model=AppointmentRead)
def get_appointment(
    appointment_id: int,
    session: Session = Depends(get_session)
):
    appointment = session.get(
        Appointment,
        appointment_id
    )

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )

    return appointment


# UPDATE APPOINTMENT
@router.patch("/{appointment_id}", response_model=AppointmentRead)
def update_appointment(
    appointment_id: int,
    appointment_update: AppointmentUpdate,
    session: Session = Depends(get_session)
):
    appointment = session.get(
        Appointment,
        appointment_id
    )

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )

    update_data = appointment_update.model_dump(
        exclude_unset=True
    )

    for key, value in update_data.items():
        setattr(appointment, key, value)

    session.add(appointment)
    session.commit()
    session.refresh(appointment)

    return appointment


# DELETE APPOINTMENT
@router.delete("/{appointment_id}")
def delete_appointment(
    appointment_id: int,
    session: Session = Depends(get_session)
):
    appointment = session.get(
        Appointment,
        appointment_id
    )

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )

    session.delete(appointment)
    session.commit()

    return {
        "message": "Appointment deleted successfully"
    }

