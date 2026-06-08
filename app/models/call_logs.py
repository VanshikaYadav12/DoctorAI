from datetime import datetime
import uuid
from uuid import UUID

from sqlmodel import SQLModel, Field


class CallLog(SQLModel, table=True):
    __tablename__ = "call_logs"

    id: UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True
    )

    call_sid: str = Field(
        index=True,
        unique=True
    )

    caller_number: str

    call_status: str = "in_progress"

    started_at: datetime = Field(
        default_factory=datetime.utcnow
    )

    ended_at: datetime | None = None

    duration_seconds: int | None = None

    created_at: datetime = Field(
        default_factory=datetime.utcnow
    )