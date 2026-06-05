from typing import Optional
from uuid import UUID

from sqlmodel import SQLModel


# CREATE DOCTOR REQUEST
class DoctorCreate(SQLModel):
    name: str
    specialization: str
    department: str


# RESPONSE SCHEMA
class DoctorRead(SQLModel):
    id: UUID
    name: str
    specialization: str
    department: str


# UPDATE SCHEMA
class DoctorUpdate(SQLModel):
    name: Optional[str] = None
    specialization: Optional[str] = None
    department: Optional[str] = None