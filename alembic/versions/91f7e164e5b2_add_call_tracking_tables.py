"""add call tracking tables

Revision ID: 91f7e164e5b2
Revises: d4f2e6c6346a
Create Date: 2026-06-04 17:41:04.941052

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '91f7e164e5b2'
down_revision: Union[str, Sequence[str], None] = 'd4f2e6c6346a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'call_conversations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('call_sid', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('speaker', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_call_conversations_id'), 'call_conversations', ['id'], unique=False)
    op.create_index(op.f('ix_call_conversations_call_sid'), 'call_conversations', ['call_sid'], unique=False)

    op.create_table(
        'call_logs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('call_sid', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('caller_number', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('call_status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_call_logs_id'), 'call_logs', ['id'], unique=False)
    op.create_index(op.f('ix_call_logs_call_sid'), 'call_logs', ['call_sid'], unique=True)

    op.create_table(
        'call_recordings',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('call_sid', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('recording_url', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_call_recordings_id'), 'call_recordings', ['id'], unique=False)
    op.create_index(op.f('ix_call_recordings_call_sid'), 'call_recordings', ['call_sid'], unique=False)

    op.create_table(
        'call_transcripts',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('call_sid', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('complete_transcript', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_call_transcripts_id'), 'call_transcripts', ['id'], unique=False)
    op.create_index(op.f('ix_call_transcripts_call_sid'), 'call_transcripts', ['call_sid'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_call_transcripts_call_sid'), table_name='call_transcripts')
    op.drop_index(op.f('ix_call_transcripts_id'), table_name='call_transcripts')
    op.drop_table('call_transcripts')
    op.drop_index(op.f('ix_call_recordings_call_sid'), table_name='call_recordings')
    op.drop_index(op.f('ix_call_recordings_id'), table_name='call_recordings')
    op.drop_table('call_recordings')
    op.drop_index(op.f('ix_call_logs_call_sid'), table_name='call_logs')
    op.drop_index(op.f('ix_call_logs_id'), table_name='call_logs')
    op.drop_table('call_logs')
    op.drop_index(op.f('ix_call_conversations_call_sid'), table_name='call_conversations')
    op.drop_index(op.f('ix_call_conversations_id'), table_name='call_conversations')
    op.drop_table('call_conversations')
