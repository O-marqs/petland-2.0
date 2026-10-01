import os
import sys
from datetime import date
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))
from demo_data import ACCOUNTS, seed
from operations import fingerprints

pytestmark = pytest.mark.integration


@pytest.fixture
def demo_engine():
    source = os.environ.get("TEST_DATABASE_URL")
    assert (
        os.environ.get("APP_ENV") == "test"
        and source
        and make_url(source).database.endswith("_test")
    )
    name = f"petland_reset_{uuid4().hex}_demo"
    admin = create_engine(source, isolation_level="AUTOCOMMIT", hide_parameters=True)
    with admin.connect() as db:
        db.execute(text(f'CREATE DATABASE "{name}"'))
    url = make_url(source).set(database=name).render_as_string(hide_password=False)
    engine = create_engine(url, hide_parameters=True)
    previous = os.environ.get("MIGRATION_DATABASE_URL")
    os.environ["MIGRATION_DATABASE_URL"] = url
    try:
        command.upgrade(Config(str(Path(__file__).resolve().parents[2] / "alembic.ini")), "head")
        yield engine
    finally:
        engine.dispose()
        if previous:
            os.environ["MIGRATION_DATABASE_URL"] = previous
        else:
            os.environ.pop("MIGRATION_DATABASE_URL", None)
        # Only the random database created by this fixture in the ephemeral test server.
        with admin.connect() as db:
            db.execute(text(f'DROP DATABASE "{name}"'))
        admin.dispose()


def test_synthetic_seed_is_idempotent_with_capacity_history_and_private_notes(demo_engine):
    passwords = dict.fromkeys(ACCOUNTS, "Senha apenas sintética de teste 2026!")
    with Session(demo_engine) as db, db.begin():
        first = seed(db, passwords, date(2026, 10, 1))
    before = fingerprints(demo_engine)
    with Session(demo_engine) as db, db.begin():
        assert seed(db, passwords, date(2026, 10, 2)) == first
    assert fingerprints(demo_engine) == before
    with demo_engine.connect() as db:
        assert db.scalar(text("SELECT count(*) FROM users")) == 4
        assert db.scalar(text("SELECT count(*) FROM appointments")) == 6
        assert (
            db.scalar(text("SELECT count(*) FROM appointment_notes WHERE visibility='INTERNAL'"))
            == 1
        )
        assert (
            db.scalar(
                text(
                    "SELECT count(*) FROM appointments WHERE status='COMPLETED' AND version=4 AND completed_at IS NOT NULL"
                )
            )
            == 1
        )
        assert db.scalar(text("SELECT count(*) FROM appointment_events WHERE kind='complete'")) == 1
        assert db.scalar(text("SELECT count(*) FROM pets WHERE archived_at IS NOT NULL")) == 1


def test_seed_failure_rolls_back_all_business_rows(demo_engine, monkeypatch):
    calls = []

    def fail_second(self, password):
        calls.append(password)
        if len(calls) == 2:
            raise RuntimeError("Synthetic failure")
        return "non-authenticating-test-hash"

    monkeypatch.setattr("demo_data.ArgonPasswords.hash", fail_second)
    with pytest.raises(RuntimeError), Session(demo_engine) as db, db.begin():
        seed(db, dict.fromkeys(ACCOUNTS, "Synthetic password"), date(2026, 10, 1))
    with demo_engine.connect() as db:
        assert db.scalar(text("SELECT count(*) FROM users")) == 0
        assert db.scalar(text("SELECT to_regclass('petland_ops.demo_manifest')")) is None
