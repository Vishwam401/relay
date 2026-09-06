"""add claim_generation to jobs and job_executions

Revision ID: w4d1_claim_generation
Revises: w3d4_enqueue_idempotency
Create Date: 2026-09-06 13:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'w4d1_claim_generation'
down_revision: Union[str, Sequence[str], None] = 'w3d4_enqueue_idempotency'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column(
            "claim_generation",
            sa.BigInteger(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "job_executions",
        sa.Column(
            "claim_generation",
            sa.BigInteger(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("job_executions", "claim_generation")
    op.drop_column("jobs", "claim_generation")
