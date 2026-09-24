import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import make_url

from petland.bootstrap.app import create_app
from petland.bootstrap.settings import Settings
from petland.modules.system.infrastructure.readiness import PostgresReadinessProbe
from petland.shared.database import SCHEMA_REVISION, build_engine

pytestmark = pytest.mark.integration


def test_empty_database_upgrade_downgrade_and_readiness(monkeypatch):
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        if os.environ.get("REQUIRE_INTEGRATION") == "1":
            pytest.fail("TEST_DATABASE_URL required; integration cannot be skipped in CI")
        pytest.skip("TEST_DATABASE_URL absent; run python scripts/dev.py test")
    if os.environ.get("APP_ENV") != "test" or not make_url(url).database.endswith("_test"):
        pytest.fail("Refusing migration test: requires APP_ENV=test and database name ending _test")
    monkeypatch.setenv("MIGRATION_DATABASE_URL", url)
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    assert ScriptDirectory.from_config(config).get_heads() == [SCHEMA_REVISION]
    engine = build_engine(url)
    try:
        command.downgrade(config, "base")
        assert not PostgresReadinessProbe(engine).is_ready()
        command.upgrade(config, "head")
        command.upgrade(config, "head")  # Repeated startup command must be safe.
        command.check(config)
        assert PostgresReadinessProbe(engine).is_ready()
        with TestClient(
            create_app(Settings(_env_file=None, app_env="test", database_url=url))
        ) as client:
            assert client.get("/api/v1/health/ready").json() == {"status": "ready"}
            with engine.begin() as conn:
                conn.execute(text("UPDATE alembic_version SET version_num = 'incompatible'"))
            assert client.get("/api/v1/health/ready").status_code == 503
            with engine.begin() as conn:
                conn.execute(
                    text("UPDATE alembic_version SET version_num = :revision"),
                    {"revision": SCHEMA_REVISION},
                )
        command.downgrade(config, "base")
        assert not PostgresReadinessProbe(engine).is_ready()
        command.upgrade(config, "head")
        assert PostgresReadinessProbe(engine).is_ready()
    finally:
        engine.dispose()
