"""Bound the reads exercised by the 100k-appointment benchmark; preserve exclusions."""

import sqlalchemy as sa
from alembic import op

revision = "0006_hardening"
down_revision = "0005_operations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_appointments_occupied_end", "appointments", ["occupied_end_at"])
    op.create_index(
        "ix_appointments_open_start",
        "appointments",
        ["occupied_start_at"],
        postgresql_where=sa.text("status IN ('ARRIVED','IN_PROGRESS')"),
    )
    op.create_index(
        "ix_appointments_customer_time",
        "appointments",
        ["customer_id", sa.text("starts_at DESC"), "id"],
    )
    op.create_index("ix_audit_events_time", "audit_events", [sa.text("occurred_at DESC"), "id"])


def downgrade() -> None:
    op.drop_index("ix_audit_events_time", table_name="audit_events")
    for name in (
        "ix_appointments_customer_time",
        "ix_appointments_open_start",
        "ix_appointments_occupied_end",
    ):
        op.drop_index(name, table_name="appointments")
