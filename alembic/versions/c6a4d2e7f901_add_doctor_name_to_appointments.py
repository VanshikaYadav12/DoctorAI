"""add doctor name to appointments

Revision ID: c6a4d2e7f901
Revises: b2d8f9a1c3e4
Create Date: 2026-06-08 10:41:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c6a4d2e7f901"
down_revision: Union[str, Sequence[str], None] = "b2d8f9a1c3e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        ALTER TABLE appointments
        ADD COLUMN IF NOT EXISTS doctor_name VARCHAR;
        """
    )
    op.execute(
        """
        UPDATE appointments
        SET doctor_name = doctors.name
        FROM doctors
        WHERE appointments.doctor_id = doctors.id
        AND appointments.doctor_name IS NULL;
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        """
        ALTER TABLE appointments
        DROP COLUMN IF EXISTS doctor_name;
        """
    )
