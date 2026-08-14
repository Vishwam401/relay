"""create_jobs_table

Revision ID: 81b6e20c9ea7
Revises: 
Create Date: 2026-08-14 17:12:49.986323

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '81b6e20c9ea7'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the jobs table — Relay's only table in Month 1."""
    op.create_table(
        'jobs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('type', sa.Text(), nullable=False),
        sa.Column(
            'payload',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column('status', sa.Text(), server_default='pending', nullable=False),
        sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'running', 'succeeded', 'failed')",
            name='jobs_status_check',
        ),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    """Drop the jobs table."""
    op.drop_table('jobs')
