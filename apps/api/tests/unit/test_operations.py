"""Safety gates of the P07 privileged offline tools."""

import base64
import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from cryptography.fernet import Fernet, InvalidToken

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))
from operations import (
    FIXTURE,
    SCHEMA_REVISION,
    activate,
    database_name,
    decrypt_backup,
    restore,
    settings,
)


@pytest.mark.parametrize(
    "name",
    [
        "petland",
        "petland_test",
        "production",
        "petland_demo;DROP DATABASE petland",
        "petland_recovery_x_demo",
    ],
)
def test_demo_tools_refuse_operational_or_injected_database_names(name):
    with pytest.raises(ValueError):
        database_name(name)


def test_demo_tools_refuse_production_even_with_staging_files(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    with pytest.raises(ValueError, match="production"):
        settings()


def archive(tmp_path):
    key, dump = Fernet.generate_key(), b"PGDMP-synthetic-fixture"
    payload = {
        "format": "petland-p07-backup-v1",
        "schema_revision": SCHEMA_REVISION,
        "source": "petland_demo",
        "fixture": {"fixture": FIXTURE},
        "dump": base64.b64encode(dump).decode(),
        "dump_sha256": hashlib.sha256(dump).hexdigest(),
    }
    path = tmp_path / "fixture.plbackup"
    path.write_bytes(Fernet(key).encrypt(json.dumps(payload).encode()))
    return path, key, payload


def test_authenticated_archive_roundtrip_and_wrong_key(tmp_path):
    path, key, payload = archive(tmp_path)
    assert decrypt_backup(path, key) == (payload, b"PGDMP-synthetic-fixture")
    with pytest.raises(InvalidToken):
        decrypt_backup(path, Fernet.generate_key())


def test_corrupted_archive_does_not_create_or_touch_a_database(tmp_path, monkeypatch):
    path, key, _ = archive(tmp_path)
    (tmp_path / "keys").mkdir()
    (tmp_path / "keys/backup.key").write_bytes(key)
    monkeypatch.setattr("operations.LOCAL", tmp_path)
    called = []
    monkeypatch.setattr("operations.create_database", lambda name: called.append(name))
    path.write_bytes(path.read_bytes()[:-16] + b"A" * 16)
    with pytest.raises(InvalidToken):
        restore(path)
    assert called == []


def test_authenticated_but_incompatible_schema_refused_before_restore(tmp_path):
    path, key, payload = archive(tmp_path)
    payload["schema_revision"] = "unknown"
    path.write_bytes(Fernet(key).encrypt(json.dumps(payload).encode()))
    with pytest.raises(ValueError, match="schema"):
        decrypt_backup(path, key)


def test_unreconciled_recovery_cannot_activate_or_stop_the_current_api(tmp_path, monkeypatch):
    monkeypatch.setattr("operations.LOCAL", tmp_path)
    calls = []
    monkeypatch.setattr("operations.compose", lambda *args, **kwargs: calls.append(args))
    with pytest.raises(ValueError, match="reconciliation"):
        activate("petland_recovery_" + "a" * 32 + "_demo")
    assert calls == []


def test_failed_activation_returns_to_the_original_database(tmp_path, monkeypatch):
    target = "petland_recovery_" + "a" * 32 + "_demo"
    (tmp_path / "active-db.txt").write_text("petland_demo")
    (tmp_path / "restores").mkdir()
    (tmp_path / "restores" / f"{target}.json").write_text('{"reconciled": true}')
    monkeypatch.setattr("operations.LOCAL", tmp_path)
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value.scalar.return_value = SCHEMA_REVISION
    monkeypatch.setattr("operations.engine_for", lambda name: engine)
    monkeypatch.setattr("operations.manifest", lambda engine: {"fixture": FIXTURE})
    attempts = []

    def fail_target(*args, **kwargs):
        if args[0] == "up":
            current = (tmp_path / "active-db.txt").read_text()
            attempts.append(current)
            if current == target:
                raise RuntimeError("Synthetic startup failure")

    monkeypatch.setattr("operations.compose", fail_target)
    with pytest.raises(RuntimeError, match="startup"):
        activate(target)
    assert attempts == [target, "petland_demo"]
    assert (tmp_path / "active-db.txt").read_text() == "petland_demo"
