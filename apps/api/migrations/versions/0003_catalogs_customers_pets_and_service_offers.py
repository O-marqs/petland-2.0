"""customers pets and service offers

Revision ID: 0003_catalogs
Revises: 0002_identity
"""

import sqlalchemy as sa
from alembic import op

revision = "0003_catalogs"
down_revision = "0002_identity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "services",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=1500), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_services")),
    )
    op.create_index(op.f("ix_services_active"), "services", ["active"], unique=False)
    op.create_table(
        "species",
        sa.Column("id", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=60), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_species")),
        sa.UniqueConstraint("name", name=op.f("uq_species_name")),
    )
    op.create_table(
        "breeds",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("species_id", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.ForeignKeyConstraint(
            ["species_id"], ["species.id"], name=op.f("fk_breeds_species_id_species")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_breeds")),
        sa.UniqueConstraint("id", "species_id", name=op.f("uq_breeds_id")),
        sa.UniqueConstraint("species_id", "name", name=op.f("uq_breeds_species_id")),
    )
    op.create_table(
        "customers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("phone", sa.String(length=16), nullable=False),
        sa.Column("address", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_customers_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_customers")),
        sa.UniqueConstraint("user_id", name=op.f("uq_customers_user_id")),
    )
    op.create_index(op.f("ix_customers_email"), "customers", ["email"], unique=False)
    op.create_table(
        "service_options",
        sa.Column("service_id", sa.Uuid(), nullable=False),
        sa.Column("size", sa.String(length=16), nullable=False),
        sa.Column("price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "size IN ('SMALL','MEDIUM','LARGE')", name=op.f("ck_service_options_size")
        ),
        sa.CheckConstraint(
            "duration_minutes BETWEEN 1 AND 1440", name=op.f("ck_service_options_duration")
        ),
        sa.CheckConstraint(
            "price >= 0 AND price <= 9999999.99", name=op.f("ck_service_options_price")
        ),
        sa.ForeignKeyConstraint(
            ["service_id"], ["services.id"], name=op.f("fk_service_options_service_id_services")
        ),
        sa.PrimaryKeyConstraint("service_id", "size", name=op.f("pk_service_options")),
    )
    op.create_table(
        "service_species",
        sa.Column("service_id", sa.Uuid(), nullable=False),
        sa.Column("species_id", sa.String(length=16), nullable=False),
        sa.ForeignKeyConstraint(
            ["service_id"], ["services.id"], name=op.f("fk_service_species_service_id_services")
        ),
        sa.ForeignKeyConstraint(
            ["species_id"], ["species.id"], name=op.f("fk_service_species_species_id_species")
        ),
        sa.PrimaryKeyConstraint("service_id", "species_id", name=op.f("pk_service_species")),
    )
    op.create_table(
        "customer_claims",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("digest", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["customer_id"], ["customers.id"], name=op.f("fk_customer_claims_customer_id_customers")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_customer_claims")),
        sa.UniqueConstraint("digest", name=op.f("uq_customer_claims_digest")),
    )
    op.create_index(
        op.f("ix_customer_claims_customer_id"), "customer_claims", ["customer_id"], unique=False
    )
    op.create_table(
        "pets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("species_id", sa.String(length=16), nullable=False),
        sa.Column("breed_id", sa.Uuid(), nullable=True),
        sa.Column("size", sa.String(length=16), nullable=False),
        sa.Column("sex", sa.String(length=16), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("birth_estimated", sa.Boolean(), nullable=False),
        sa.Column("care_notes", sa.String(length=1000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint("sex IN ('UNKNOWN','FEMALE','MALE')", name=op.f("ck_pets_sex")),
        sa.CheckConstraint("size IN ('SMALL','MEDIUM','LARGE')", name=op.f("ck_pets_size")),
        sa.CheckConstraint(
            "NOT birth_estimated OR birth_date IS NOT NULL", name=op.f("ck_pets_estimated_date")
        ),
        sa.ForeignKeyConstraint(
            ["breed_id", "species_id"],
            ["breeds.id", "breeds.species_id"],
            name=op.f("fk_pets_breed_id_breeds"),
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"], ["customers.id"], name=op.f("fk_pets_customer_id_customers")
        ),
        sa.ForeignKeyConstraint(
            ["species_id"], ["species.id"], name=op.f("fk_pets_species_id_species")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pets")),
        sa.UniqueConstraint("id", "customer_id", name=op.f("uq_pets_id")),
    )
    op.create_index(op.f("ix_pets_customer_id"), "pets", ["customer_id"], unique=False)
    # Canonical reference data only. No customers, pets, prices or commercial offers are seeded.
    op.execute("INSERT INTO species (id, name) VALUES ('DOG', 'Cachorro'), ('CAT', 'Gato')")
    op.execute("""INSERT INTO breeds (id, species_id, name) VALUES
        ('a1f52a7f-17b6-456a-b039-1b4a75d20001', 'DOG', 'Sem raça definida'),
        ('a1f52a7f-17b6-456a-b039-1b4a75d20002', 'CAT', 'Sem raça definida'),
        ('a1f52a7f-17b6-456a-b039-1b4a75d20003', 'DOG', 'Poodle'),
        ('a1f52a7f-17b6-456a-b039-1b4a75d20004', 'DOG', 'Shih-tzu'),
        ('a1f52a7f-17b6-456a-b039-1b4a75d20005', 'CAT', 'Siamês'),
        ('a1f52a7f-17b6-456a-b039-1b4a75d20006', 'CAT', 'Persa')""")
    op.execute("""
        DO $$ BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'petland_app') THEN
            GRANT SELECT ON species, breeds TO petland_app;
            GRANT SELECT, INSERT, UPDATE ON customers, pets, services, customer_claims TO petland_app;
            GRANT SELECT, INSERT, UPDATE, DELETE ON service_options, service_species TO petland_app;
          END IF;
        END $$;
    """)


def downgrade() -> None:
    op.drop_index(op.f("ix_pets_customer_id"), table_name="pets")
    op.drop_table("pets")
    op.drop_index(op.f("ix_customer_claims_customer_id"), table_name="customer_claims")
    op.drop_table("customer_claims")
    op.drop_table("service_species")
    op.drop_table("service_options")
    op.drop_index(op.f("ix_customers_email"), table_name="customers")
    op.drop_table("customers")
    op.drop_table("breeds")
    op.drop_table("species")
    op.drop_index(op.f("ix_services_active"), table_name="services")
    op.drop_table("services")
