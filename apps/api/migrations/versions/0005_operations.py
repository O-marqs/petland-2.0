"""Operational attendance, immutable notes and extended occupancy.

Revision ID: 0005_operations
Revises: 0004_scheduling
"""

import sqlalchemy as sa
from alembic import op

revision = "0005_operations"
down_revision = "0004_scheduling"
branch_labels = None
depends_on = None


def exclusions(extended: bool) -> None:
    state = (
        "status IN ('BOOKED','ARRIVED','IN_PROGRESS','COMPLETED')"
        if extended
        else "status = 'BOOKED'"
    )
    pet_end = "COALESCE(reserved_until, ends_at)" if extended else "ends_at"
    op.execute(
        f"ALTER TABLE appointments ADD CONSTRAINT appointments_resource_overlap EXCLUDE USING gist (resource_id WITH =, tstzrange(occupied_start_at, occupied_end_at, '[)') WITH &&) WHERE ({state})"
    )
    op.execute(
        f"ALTER TABLE appointments ADD CONSTRAINT appointments_pet_overlap EXCLUDE USING gist (pet_id WITH =, tstzrange(starts_at, {pet_end}, '[)') WITH &&) WHERE ({state})"
    )


def upgrade() -> None:
    op.alter_column("booking_idempotency", "operation", type_=sa.String(40))
    op.add_column(
        "appointments",
        sa.Column("no_show_grace_minutes", sa.Integer(), nullable=False, server_default="0"),
    )
    for column in ("arrived_at", "started_at", "completed_at", "reserved_until"):
        op.add_column("appointments", sa.Column(column, sa.DateTime(timezone=True), nullable=True))
    op.drop_constraint("appointments_resource_overlap", "appointments")
    op.drop_constraint("appointments_pet_overlap", "appointments")
    op.drop_constraint(op.f("ck_appointments_status"), "appointments", type_="check")
    op.create_check_constraint(
        "status",
        "appointments",
        "status IN ('BOOKED','ARRIVED','IN_PROGRESS','COMPLETED','CANCELLED','NO_SHOW')",
    )
    op.create_check_constraint(
        "extension",
        "appointments",
        "reserved_until IS NULL OR (reserved_until >= ends_at AND reserved_until <= occupied_end_at)",
    )
    op.create_check_constraint(
        "actual_times",
        "appointments",
        "(started_at IS NULL OR (arrived_at IS NOT NULL AND started_at >= arrived_at)) AND (completed_at IS NULL OR (started_at IS NOT NULL AND completed_at >= started_at))",
    )
    exclusions(True)
    op.create_table(
        "appointment_notes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("appointment_id", sa.Uuid(), sa.ForeignKey("appointments.id"), nullable=False),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("body", sa.String(2000), nullable=False),
        sa.Column("visibility", sa.String(16), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "visibility IN ('INTERNAL','PUBLIC')", name=op.f("ck_appointment_notes_visibility")
        ),
    )
    op.create_index(
        op.f("ix_appointment_notes_appointment_id"), "appointment_notes", ["appointment_id"]
    )
    op.execute("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'petland_app') THEN
        GRANT SELECT, INSERT ON appointment_notes TO petland_app;
      END IF;
    END $$;""")


def downgrade() -> None:
    # Never silently discard a real attendance or its notes to fit P04's state machine.
    op.execute("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM appointments WHERE status NOT IN ('BOOKED','CANCELLED') OR arrived_at IS NOT NULL OR reserved_until IS NOT NULL)
         OR EXISTS (SELECT 1 FROM appointment_notes)
         OR EXISTS (SELECT 1 FROM booking_idempotency WHERE operation LIKE 'attendance.%') THEN
        RAISE EXCEPTION 'P05 attendance data exists; downgrade requires an explicit preservation plan';
      END IF;
    END $$;""")
    op.drop_table("appointment_notes")
    op.alter_column("booking_idempotency", "operation", type_=sa.String(20))
    op.drop_constraint("appointments_resource_overlap", "appointments")
    op.drop_constraint("appointments_pet_overlap", "appointments")
    for name in ("status", "extension", "actual_times"):
        op.drop_constraint(op.f("ck_appointments_" + name), "appointments", type_="check")
    op.create_check_constraint("status", "appointments", "status IN ('BOOKED','CANCELLED')")
    exclusions(False)
    for column in (
        "no_show_grace_minutes",
        "arrived_at",
        "started_at",
        "completed_at",
        "reserved_until",
    ):
        op.drop_column("appointments", column)
