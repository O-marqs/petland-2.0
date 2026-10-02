import os

from alembic import context

from petland.modules.catalog.infrastructure import models as catalog_models  # noqa: F401
from petland.modules.customers.infrastructure import models as customer_models  # noqa: F401
from petland.modules.identity.infrastructure import models  # noqa: F401
from petland.modules.pets.infrastructure import models as pet_models  # noqa: F401
from petland.modules.scheduling.infrastructure import models as schedule_models  # noqa: F401
from petland.shared.database import Base, build_engine

url = os.environ.get("MIGRATION_DATABASE_URL")
if not url:
    raise RuntimeError("MIGRATION_DATABASE_URL is required for migrations")

if context.is_offline_mode():
    context.configure(url=url, target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = build_engine(url)
    try:
        with engine.connect() as connection:
            context.configure(
                connection=connection, target_metadata=Base.metadata, compare_type=True
            )
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()
