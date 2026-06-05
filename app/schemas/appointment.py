from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlmodel import SQLModel


# CREATE APPOINTMENT
class AppointmentCreate(SQLModel):
    patient_name: str
    patient_phone: str
    appointment_time: datetime
    doctor_id: UUID
    notes: Optional[str] = None


# RESPONSE MODEL
class AppointmentRead(SQLModel):
    id: UUID
    patient_name: str
    patient_phone: str
    appointment_time: datetime
    status: str
    doctor_id: UUID
    notes: Optional[str]
    created_at: datetime


# UPDATE APPOINTMENT
class AppointmentUpdate(SQLModel):
    patient_name: Optional[str] = None
    patient_phone: Optional[str] = None
    appointment_time: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None

