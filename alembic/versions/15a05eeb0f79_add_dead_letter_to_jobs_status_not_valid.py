"""add dead_letter to jobs status not valid

Revision ID: 15a05eeb0f79
Revises: 9e4822cbf157
Create Date: 2026-08-28 14:27:56.967541

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '15a05eeb0f79'
down_revision: Union[str, Sequence[str], None] = '9e4822cbf157'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint('jobs_status_check', 'jobs', type_='check')
    op.create_check_constraint(
        'jobs_status_check',
        'jobs',
        "status IN ('pending', 'running', 'succeeded', 'failed', 'dead_letter')",
        postgresql_not_valid=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('jobs_status_check', 'jobs', type_='check')
    op.create_check_constraint(
        'jobs_status_check',
        'jobs',
        "status IN ('pending', 'running', 'succeeded', 'failed')",
    )
