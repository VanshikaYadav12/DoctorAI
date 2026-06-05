from typing import Optional
from datetime import datetime
import uuid
from uuid import UUID

from sqlmodel import SQLModel, Field


class Appointment(SQLModel, table=True):
    __tablename__ = "appointments"

    id: UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True
    )

    patient_name: str

    patient_phone: str

    appointment_time: datetime

    status: str = "scheduled"

    notes: Optional[str] = None

    doctor_id: UUID = Field(
        foreign_key="doctors.id"
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow
    )

