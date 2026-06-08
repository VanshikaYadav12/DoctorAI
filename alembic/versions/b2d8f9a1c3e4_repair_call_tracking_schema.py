"""repair call tracking schema

Revision ID: b2d8f9a1c3e4
Revises: 91f7e164e5b2
Create Date: 2026-06-08 10:40:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b2d8f9a1c3e4"
down_revision: Union[str, Sequence[str], None] = "91f7e164e5b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        ALTER TABLE call_conversations
        ADD COLUMN IF NOT EXISTS timestamp TIMESTAMP WITHOUT TIME ZONE;
        """
    )
    op.execute(
        """
        UPDATE call_conversations
        SET timestamp = COALESCE(timestamp, created_at, NOW())
        WHERE timestamp IS NULL;
        """
    )
    op.execute(
        """
        ALTER TABLE call_conversations
        ALTER COLUMN timestamp SET NOT NULL;
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_call_conversations_call_sid
        ON call_conversations (call_sid);
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS call_transcripts (
            id UUID NOT NULL,
            call_sid VARCHAR NOT NULL,
            complete_transcript TEXT NOT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            PRIMARY KEY (id)
        );
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_call_transcripts_id
        ON call_transcripts (id);
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ix_call_transcripts_call_sid
        ON call_transcripts (call_sid);
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS ix_call_transcripts_call_sid;")
    op.execute("DROP INDEX IF EXISTS ix_call_transcripts_id;")
    op.execute("DROP TABLE IF EXISTS call_transcripts;")
