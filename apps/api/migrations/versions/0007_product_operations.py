"""Care alerts, structured assignment history and scheduled communication; preserve data."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0007_product_operations"
down_revision = "0006_hardening"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for name in ("allergies", "handling_notes"):
        op.add_column("pets", sa.Column(name, sa.String(1000), nullable=False, server_default=""))
    for name in ("previous_resource_id", "resource_id"):
        op.add_column("appointment_events", sa.Column(name, postgresql.UUID(), nullable=True))
        op.create_foreign_key(
            f"fk_appointment_events_{name}_schedule_resources",
            "appointment_events",
            "schedule_resources",
            [name],
            ["id"],
        )
    op.add_column(
        "appointment_outbox",
        sa.Column("kind", sa.String(20), nullable=False, server_default="legacy"),
    )
    for name in ("scheduled_start_at", "suppressed_at"):
        op.add_column(
            "appointment_outbox", sa.Column(name, sa.DateTime(timezone=True), nullable=True)
        )


def downgrade() -> None:
    db = op.get_bind()
    if db.scalar(
        sa.text(
            "SELECT EXISTS(SELECT 1 FROM pets WHERE allergies <> '' OR handling_notes <> '') OR EXISTS(SELECT 1 FROM appointment_events WHERE resource_id IS NOT NULL OR previous_resource_id IS NOT NULL) OR EXISTS(SELECT 1 FROM appointment_outbox WHERE kind <> 'legacy') OR EXISTS(SELECT 1 FROM schedule_configuration WHERE jsonb_array_length(COALESCE(data->'staff_days', '[]'::jsonb)) > 0 OR jsonb_array_length(COALESCE(data->'capacity_pools', '[]'::jsonb)) > 0 OR COALESCE((data->>'reminder_minutes')::int, 0) <> 0)"
        )
    ):
        raise RuntimeError(
            "Preserve operational alerts, assignment history and communication before downgrade"
        )
    db.execute(
        sa.text(
            "UPDATE schedule_configuration SET data = data - 'staff_days' - 'capacity_pools' - 'reminder_minutes'"
        )
    )
    for name in ("suppressed_at", "scheduled_start_at", "kind"):
        op.drop_column("appointment_outbox", name)
    for name in ("resource_id", "previous_resource_id"):
        op.drop_constraint(
            f"fk_appointment_events_{name}_schedule_resources",
            "appointment_events",
            type_="foreignkey",
        )
        op.drop_column("appointment_events", name)
    for name in ("handling_notes", "allergies"):
        op.drop_column("pets", name)
