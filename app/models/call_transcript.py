from datetime import datetime
import uuid
from uuid import UUID

from sqlmodel import SQLModel, Field

class CallConversation(SQLModel, table=True):
    __tablename__ = "call_conversations"

    id: UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True
    )

    call_sid: str

    speaker: str
    # USER or AI

    message: str

    created_at: datetime = Field(
        default_factory=datetime.utcnow
    )