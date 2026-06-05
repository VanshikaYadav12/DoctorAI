from typing import Optional
import uuid
from uuid import UUID

from sqlmodel import SQLModel, Field

class Doctor(SQLModel, table=True):
    __tablename__ = "doctors"

    id: UUID = Field(
        default_factory=uuid.uuid4, 
        primary_key=True,
        index=True
    )

    name: str
    specialization: str
    department: str