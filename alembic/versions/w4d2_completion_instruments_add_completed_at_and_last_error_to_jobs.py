"""add completed_at and last_error to jobs

Revision ID: w4d2_completion_instruments
Revises: w4d1_claim_generation
Create Date: 2026-09-07 14:02:02.171587

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'w4d2_completion_instruments'
down_revision: Union[str, Sequence[str], None] = 'w4d1_claim_generation'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "jobs",
        sa.Column("last_error", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("jobs", "last_error")
    op.drop_column("jobs", "completed_at")
