"""validate jobs_status_check

Revision ID: 682e01d87be9
Revises: 15a05eeb0f79
Create Date: 2026-08-28 14:28:05.180881

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '682e01d87be9'
down_revision: Union[str, Sequence[str], None] = '15a05eeb0f79'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE jobs VALIDATE CONSTRAINT jobs_status_check;")


def downgrade() -> None:
    """Downgrade schema."""
    pass
