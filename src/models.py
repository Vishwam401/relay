"""
SQLAlchemy models for Relay.

Jobs table — the only table in Month 1.
Schema decisions and their rejected alternatives: docs/DECISIONS.md (D-03 .. D-08).
"""

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Integer,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime


class Base(DeclarativeBase):
    """Base class for all models. Alembic will use this to detect schema changes."""
    pass


class Job(Base):
    """
    A single unit of work submitted to Relay.

    Column decisions (see docs/DECISIONS.md D-03..D-08 for full reasoning,
    including which alternative was rejected and when it would be correct):

    id:         bigint IDENTITY — DB-generated sequential id.
                Idempotency is a separate concern (Week 3, separate column).
                Sequential = append-only B-tree inserts, no page splits.

    type:       text NOT NULL — no DB constraint, validation at app/worker layer.
                DB cannot check if a Python handler exists for this type.
                Wrong type → job fails → DLQ. Bounded cost, not silent loss.

    payload:    jsonb NOT NULL DEFAULT '{}' — binary parsed JSON.
                Read-fast (no reparse), future-queryable, normalized for hashing.
                NOT NULL + default '{}' so handlers always get a dict, never None.

    status:     text NOT NULL DEFAULT 'pending' + CHECK constraint.
                CHECK (not ENUM) because DROP VALUE doesn't exist in Postgres.
                Transitions enforced via compare-and-set (WHERE status = ...), not DB.

    attempts:   integer NOT NULL DEFAULT 0 — retry counter.
                NULL + 1 = NULL → infinite retry loop → Contract #3 broken.
                Added now (table empty) to avoid Week 2 backfill headache.

    created_at: timestamptz NOT NULL DEFAULT now() — DB clock, not app clock.
                timestamptz (not timestamp) because API/Worker/Reaper may run
                in different timezones. now() = transaction start time (correct
                for atomic inserts). One clock = one truth.
    """

    __tablename__ = "jobs"

    # --- Columns ---

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        # BigInteger + autoincrement=True uses bigserial under the hood,
        # which is functionally identical to IDENTITY (both use sequences).
        autoincrement=True,
    )

    type: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # NOTE on server_default: a plain Python string gets *quoted* by SQLAlchemy,
    # so server_default="'pending'" would render as DEFAULT '''pending''' — a
    # literal string including the quote characters. Anything that is a SQL
    # expression (or a quoted literal) must be wrapped in text().
    payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )

    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'pending'"),
    )

    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # --- Table-level constraints ---

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'running', 'succeeded', 'failed')",
            name="jobs_status_check",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Job(id={self.id}, type={self.type!r}, "
            f"status={self.status!r}, attempts={self.attempts})>"
        )
