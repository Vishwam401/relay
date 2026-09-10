"""add sink unique constraint and sink deliveries table

Revision ID: w4d4_sink_unique
Revises: w4d3_outbox
Create Date: 2026-09-09 14:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'w4d4_sink_unique'
down_revision: Union[str, Sequence[str], None] = 'w4d3_outbox'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    if 'sink_deliveries' not in tables:
        op.create_table(
            'sink_deliveries',
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column('idempotency_key', sa.Text(), nullable=False),
            sa.Column('job_id', sa.BigInteger(), server_default='0', nullable=False),
            sa.Column(
                'received_at',
                sa.DateTime(timezone=True),
                server_default=sa.text('now()'),
                nullable=False,
            ),
            sa.Column(
                'body',
                postgresql.JSONB(astext_type=sa.Text()),
                server_default=sa.text("'{}'::jsonb"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint(
                'idempotency_key', name='uq_sink_deliveries_idempotency_key'
            ),
        )
    else:
        constraints = [
            c['name'] for c in inspector.get_unique_constraints('sink_deliveries')
        ]
        if 'uq_sink_deliveries_idempotency_key' not in constraints:
            conn.execute(sa.text("""
                DELETE FROM sink_deliveries a
                USING sink_deliveries b
                WHERE a.id > b.id AND a.idempotency_key = b.idempotency_key
            """))
            op.create_unique_constraint(
                'uq_sink_deliveries_idempotency_key',
                'sink_deliveries',
                ['idempotency_key'],
            )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    if 'sink_deliveries' in tables:
        constraints = [
            c['name'] for c in inspector.get_unique_constraints('sink_deliveries')
        ]
        if 'uq_sink_deliveries_idempotency_key' in constraints:
            op.drop_constraint(
                'uq_sink_deliveries_idempotency_key',
                'sink_deliveries',
                type_='unique',
            )
