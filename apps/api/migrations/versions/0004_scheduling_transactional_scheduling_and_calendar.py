"""transactional scheduling and calendar

Revision ID: 0004_scheduling
Revises: 0003_catalogs
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004_scheduling"
down_revision = "0003_catalogs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.create_table(
        "schedule_configuration",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.CheckConstraint("id = 1", name=op.f("ck_schedule_configuration_singleton")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_schedule_configuration")),
    )
    op.create_table(
        "booking_idempotency",
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("operation", sa.String(length=20), nullable=False),
        sa.Column("key", sa.Uuid(), nullable=False),
        sa.Column("signature", sa.String(length=64), nullable=False),
        sa.Column("response", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["actor_id"], ["users.id"], name=op.f("fk_booking_idempotency_actor_id_users")
        ),
        sa.PrimaryKeyConstraint(
            "actor_id", "operation", "key", name=op.f("pk_booking_idempotency")
        ),
    )
    op.create_table(
        "schedule_resources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("service_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("calendar", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_schedule_resources_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_schedule_resources")),
        sa.UniqueConstraint("user_id", name=op.f("uq_schedule_resources_user_id")),
    )
    op.create_table(
        "appointments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("pet_id", sa.Uuid(), nullable=False),
        sa.Column("service_id", sa.Uuid(), nullable=False),
        sa.Column("resource_id", sa.Uuid(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("occupied_start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("occupied_end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("offer", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("change_cutoff_minutes", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        postgresql.ExcludeConstraint(
            (sa.column("pet_id"), "="),
            (sa.text("tstzrange(starts_at, ends_at, '[)')"), "&&"),
            where=sa.text("status = 'BOOKED'"),
            using="gist",
            name="appointments_pet_overlap",
        ),
        postgresql.ExcludeConstraint(
            (sa.column("resource_id"), "="),
            (sa.text("tstzrange(occupied_start_at, occupied_end_at, '[)')"), "&&"),
            where=sa.text("status = 'BOOKED'"),
            using="gist",
            name="appointments_resource_overlap",
        ),
        sa.CheckConstraint("status IN ('BOOKED','CANCELLED')", name=op.f("ck_appointments_status")),
        sa.CheckConstraint(
            "occupied_start_at <= starts_at AND starts_at < ends_at AND ends_at <= occupied_end_at",
            name=op.f("ck_appointments_interval"),
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"], ["customers.id"], name=op.f("fk_appointments_customer_id_customers")
        ),
        sa.ForeignKeyConstraint(
            ["pet_id", "customer_id"],
            ["pets.id", "pets.customer_id"],
            name=op.f("fk_appointments_pet_id_pets"),
        ),
        sa.ForeignKeyConstraint(
            ["resource_id"],
            ["schedule_resources.id"],
            name=op.f("fk_appointments_resource_id_schedule_resources"),
        ),
        sa.ForeignKeyConstraint(
            ["service_id"], ["services.id"], name=op.f("fk_appointments_service_id_services")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_appointments")),
    )
    op.create_index(
        op.f("ix_appointments_customer_id"), "appointments", ["customer_id"], unique=False
    )
    op.create_index(op.f("ix_appointments_starts_at"), "appointments", ["starts_at"], unique=False)
    op.create_table(
        "appointment_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("appointment_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["actor_id"], ["users.id"], name=op.f("fk_appointment_events_actor_id_users")
        ),
        sa.ForeignKeyConstraint(
            ["appointment_id"],
            ["appointments.id"],
            name=op.f("fk_appointment_events_appointment_id_appointments"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_appointment_events")),
    )
    op.create_index(
        op.f("ix_appointment_events_appointment_id"),
        "appointment_events",
        ["appointment_id"],
        unique=False,
    )
    op.create_table(
        "appointment_outbox",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("appointment_id", sa.Uuid(), nullable=False),
        sa.Column("recipient", sa.String(length=254), nullable=False),
        sa.Column("subject", sa.String(length=120), nullable=False),
        sa.Column("body", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["appointment_id"],
            ["appointments.id"],
            name=op.f("fk_appointment_outbox_appointment_id_appointments"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_appointment_outbox")),
    )
    op.create_index(
        op.f("ix_appointment_outbox_appointment_id"),
        "appointment_outbox",
        ["appointment_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_appointment_outbox_available_at"),
        "appointment_outbox",
        ["available_at"],
        unique=False,
    )
    op.add_column(
        "service_options",
        sa.Column("buffer_before_minutes", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "service_options",
        sa.Column("buffer_after_minutes", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_check_constraint(
        "buffers",
        "service_options",
        "buffer_before_minutes BETWEEN 0 AND 240 AND buffer_after_minutes BETWEEN 0 AND 240",
    )
    # Disabled draft, no employees or commercial opening hours are seeded.
    op.execute("""INSERT INTO schedule_configuration (id, data) VALUES (1,
      '{"timezone": "America/Sao_Paulo","enabled": false,"lead_minutes": 0,"horizon_days": 1,"step_minutes": 15,"change_cutoff_minutes": 0,"calendar": {"weekly": [],"exceptions": []},"version": 1}'::jsonb)""")
    op.execute("""
      DO $$ BEGIN
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'petland_app') THEN
          GRANT SELECT, UPDATE ON schedule_configuration TO petland_app;
          GRANT SELECT, INSERT, UPDATE ON schedule_resources, appointments, appointment_outbox TO petland_app;
          GRANT SELECT, INSERT ON appointment_events, booking_idempotency TO petland_app;
        END IF;
      END $$;
    """)


def downgrade() -> None:
    op.drop_constraint(op.f("ck_service_options_buffers"), "service_options", type_="check")
    op.drop_column("service_options", "buffer_after_minutes")
    op.drop_column("service_options", "buffer_before_minutes")
    op.drop_index(op.f("ix_appointment_outbox_available_at"), table_name="appointment_outbox")
    op.drop_index(op.f("ix_appointment_outbox_appointment_id"), table_name="appointment_outbox")
    op.drop_table("appointment_outbox")
    op.drop_index(op.f("ix_appointment_events_appointment_id"), table_name="appointment_events")
    op.drop_table("appointment_events")
    op.drop_index(op.f("ix_appointments_starts_at"), table_name="appointments")
    op.drop_index(op.f("ix_appointments_customer_id"), table_name="appointments")
    op.drop_table("appointments")
    op.drop_table("schedule_resources")
    op.drop_table("booking_idempotency")
    op.drop_table("schedule_configuration")
