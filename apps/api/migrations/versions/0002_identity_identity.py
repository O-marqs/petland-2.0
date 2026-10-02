"""identity

Revision ID: 0002_identity
Revises: 0001_foundation
"""

import sqlalchemy as sa
from alembic import op

revision = "0002_identity"
down_revision = "0001_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Reviewed: identity only; no business tables or customer data migration.
    op.create_table(
        "identity_rate_limits",
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("window", sa.Integer(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("key", "window", name=op.f("pk_identity_rate_limits")),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("normalized_email", sa.String(length=254), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=256), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint("status IN ('ACTIVE','DISABLED')", name=op.f("ck_users_status")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("normalized_email", name=op.f("uq_users_normalized_email")),
    )
    op.create_table(
        "account_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("purpose", sa.String(length=16), nullable=False),
        sa.Column("token_digest", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "purpose IN ('verify','reset','invite','bootstrap')",
            name=op.f("ck_account_tokens_purpose"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_account_tokens_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_account_tokens")),
        sa.UniqueConstraint("token_digest", name=op.f("uq_account_tokens_token_digest")),
    )
    op.create_index(
        op.f("ix_account_tokens_expires_at"), "account_tokens", ["expires_at"], unique=False
    )
    op.create_index(op.f("ix_account_tokens_user_id"), "account_tokens", ["user_id"], unique=False)
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("target_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("result", sa.String(length=16), nullable=False),
        sa.ForeignKeyConstraint(
            ["actor_user_id"], ["users.id"], name=op.f("fk_audit_events_actor_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_events")),
    )
    op.create_index(
        op.f("ix_audit_events_actor_user_id"), "audit_events", ["actor_user_id"], unique=False
    )
    op.create_index(
        "ix_audit_events_target_time", "audit_events", ["target_id", "occurred_at"], unique=False
    )
    op.create_table(
        "sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("token_digest", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("idle_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_sessions_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sessions")),
        sa.UniqueConstraint("token_digest", name=op.f("uq_sessions_token_digest")),
    )
    op.create_index(op.f("ix_sessions_expires_at"), "sessions", ["expires_at"], unique=False)
    op.create_index(op.f("ix_sessions_user_id"), "sessions", ["user_id"], unique=False)
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.CheckConstraint(
            "role IN ('CUSTOMER','EMPLOYEE','ADMIN')", name=op.f("ck_user_roles_role")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_user_roles_user_id_users")
        ),
        sa.PrimaryKeyConstraint("user_id", "role", name=op.f("pk_user_roles")),
    )
    # Upgrade existing P01 volumes as well as clean installations. CI uses its own owner.
    op.execute("""
        DO $$ BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'petland_app') THEN
            GRANT SELECT, INSERT, UPDATE ON users, account_tokens, sessions TO petland_app;
            GRANT SELECT, INSERT, UPDATE, DELETE ON user_roles, identity_rate_limits TO petland_app;
            GRANT DELETE ON account_tokens, sessions TO petland_app;
            GRANT SELECT, INSERT ON audit_events TO petland_app;
          END IF;
        END $$;
    """)


def downgrade() -> None:
    # Destructive rollback is for disposable test environments; back up real identity data first.
    op.drop_table("user_roles")
    op.drop_index(op.f("ix_sessions_user_id"), table_name="sessions")
    op.drop_index(op.f("ix_sessions_expires_at"), table_name="sessions")
    op.drop_table("sessions")
    op.drop_index("ix_audit_events_target_time", table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_actor_user_id"), table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index(op.f("ix_account_tokens_user_id"), table_name="account_tokens")
    op.drop_index(op.f("ix_account_tokens_expires_at"), table_name="account_tokens")
    op.drop_table("account_tokens")
    op.drop_table("users")
    op.drop_table("identity_rate_limits")
