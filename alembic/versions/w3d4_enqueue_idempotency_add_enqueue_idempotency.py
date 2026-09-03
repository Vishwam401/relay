"""add enqueue idempotency

Revision ID: w3d4_enqueue_idempotency
Revises: dbe13b69056d
Create Date: 2026-09-03 14:57:12.152291

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'w3d4_enqueue_idempotency'
down_revision: Union[str, Sequence[str], None] = 'dbe13b69056d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("jobs", sa.Column("idempotency_key", sa.Text(), nullable=True))
    op.add_column("jobs", sa.Column("request_fingerprint", sa.Text(), nullable=True))
    op.create_unique_constraint("uq_jobs_idempotency_key", "jobs", ["idempotency_key"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_jobs_idempotency_key", "jobs", type_="unique")
    op.drop_column("jobs", "request_fingerprint")
    op.drop_column("jobs", "idempotency_key")

