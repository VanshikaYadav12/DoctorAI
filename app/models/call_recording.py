from datetime import datetime
import uuid
from uuid import UUID

from sqlmodel import SQLModel, Field


class CallRecording(SQLModel, table=True):
    __tablename__ = "call_recordings"

    id: UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True
    )

    call_sid: str = Field(index=True)

    recording_url: str

    created_at: datetime = Field(
        default_factory=datetime.utcnow
    )