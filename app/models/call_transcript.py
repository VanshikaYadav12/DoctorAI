from datetime import datetime
import uuid
from uuid import UUID

from sqlalchemy import Column, Text
from sqlmodel import SQLModel, Field


class CallConversation(SQLModel, table=True):
    __tablename__ = "call_conversations"

    id: UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True
    )

    call_sid: str = Field(index=True)

    speaker: str
    # USER or AI

    message: str = Field(
        sa_column=Column(Text, nullable=False)
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow
    )


class CallTranscript(SQLModel, table=True):
    __tablename__ = "call_transcripts"

    id: UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True
    )

    call_sid: str = Field(
        index=True,
        unique=True
    )

    complete_transcript: str = Field(
        sa_column=Column(Text, nullable=False)
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow
    )