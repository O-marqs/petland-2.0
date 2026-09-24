from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from petland.shared.database import SCHEMA_REVISION


class PostgresReadinessProbe:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def is_ready(self) -> bool:
        try:
            with self._engine.connect() as connection:
                revisions = connection.execute(text("SELECT version_num FROM alembic_version"))
                return set(revisions.scalars()) == {SCHEMA_REVISION}
        except SQLAlchemyError:
            # Connection, timeout, absent schema and permission errors fail closed.
            return False
