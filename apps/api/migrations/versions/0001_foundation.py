"""Schema compatibility marker; business tables start in P02.

Alembic creates/updates alembic_version transactionally. There are deliberately
no speculative users, pets, capacity or commercial policy tables in P01.
"""

revision = "0001_foundation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
