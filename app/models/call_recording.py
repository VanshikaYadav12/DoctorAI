from datetime import datetime
import uuid
from uuid import UUID

from sqlmodel import SQLModel, Field


class CallRecording(SQLModel, table=True):
    __tablename__ = "call_recordings"

    id: UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True
    )

    call_sid: str

    recording_url: str

    transcript: str | None = None

    created_at: datetime = Field(
        default_factory=datetime.utcnow
    )