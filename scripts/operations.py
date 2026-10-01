"""Isolated local staging, synthetic demo and authenticated backup/restore rehearsal."""

import argparse
import base64
import hashlib
import ipaddress
import json
import os
import re
import secrets
import ssl
import subprocess
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4
from zoneinfo import ZoneInfo

import httpx
from alembic import command
from alembic.config import Config
from cryptography import x509
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from demo_data import ACCOUNTS, FIXTURE, seed
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session

from petland.shared.database import SCHEMA_REVISION

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / ".local/staging"
ORIGIN = "https://localhost:8443"
MAX_BACKUP = 64 * 1024 * 1024


def write_private(path: Path, content: bytes, *, replace=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb" if replace else "xb") as file:
        file.write(content)
    path.chmod(0o600)


def initialize():
    if os.environ.get("APP_ENV") == "production":
        raise ValueError("Demo initialization refuses APP_ENV=production")
    config = LOCAL / "config.env"
    if config.exists():
        settings()
        print("Existing isolated staging credentials and certificates preserved.")
        return
    if LOCAL.exists() and any(LOCAL.iterdir()):
        raise ValueError("Partial staging initialization; inspect .local/staging before retrying")
    issue_certificates()
    write_private(LOCAL / "keys/backup.key", Fernet.generate_key())
    accounts = {
        key: {"email": data[0], "password": secrets.token_urlsafe(30)}
        for key, data in ACCOUNTS.items()
    }
    write_private(LOCAL / "accounts.json", json.dumps(accounts, indent=2).encode())
    values = {
        "STAGING_POSTGRES_PASSWORD": secrets.token_hex(24),
        "STAGING_APP_PASSWORD": secrets.token_hex(24),
        "LOCAL_UID": str(getattr(os, "getuid", lambda: 10001)()),
        "LOCAL_GID": str(getattr(os, "getgid", lambda: 10001)()),
    }
    write_private(config, ("\n".join(f"{k}={v}" for k, v in values.items()) + "\n").encode())
    (LOCAL / "active-db.txt").write_text("petland_demo")
    print("Isolated staging initialized; generated secrets are not printed or versioned.")


def issue_certificates(*, replace=False):
    def certificate_file(path, content):
        write_private(path, content, replace=replace)

    now = datetime.now(UTC)
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "PetLand local rehearsal CA")])
    ca = (
        x509.CertificateBuilder()
        .subject_name(ca_name)
        .issuer_name(ca_name)
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()), critical=False
        )
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), critical=False
        )
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .add_extension(
            x509.KeyUsage(True, False, False, False, False, True, True, False, False), critical=True
        )
        .sign(ca_key, hashes.SHA256())
    )
    private_format = serialization.PrivateFormat.PKCS8
    certificate_file(
        LOCAL / "keys/ca.key",
        ca_key.private_bytes(
            serialization.Encoding.PEM, private_format, serialization.NoEncryption()
        ),
    )
    certificate_file(LOCAL / "certs/ca.crt", ca.public_bytes(serialization.Encoding.PEM))
    (LOCAL / "certs/ca.crt").chmod(0o644)
    for name, hosts in [
        ("web", ["localhost"]),
        ("postgres", ["postgres", "localhost"]),
        ("mailpit", ["mailpit", "localhost"]),
    ]:
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, hosts[0])])
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(ca.subject)
            .add_extension(
                x509.SubjectKeyIdentifier.from_public_key(key.public_key()), critical=False
            )
            .add_extension(
                x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()),
                critical=False,
            )
            .add_extension(
                x509.KeyUsage(True, False, True, False, False, False, False, False, False),
                critical=True,
            )
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(days=1))
            .not_valid_after(now + timedelta(days=90))
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(
                x509.SubjectAlternativeName(
                    [x509.DNSName(host) for host in hosts]
                    + [x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]
                ),
                critical=False,
            )
            .add_extension(
                x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]), critical=False
            )
            .sign(ca_key, hashes.SHA256())
        )
        certificate_file(
            LOCAL / f"certs/{name}.key",
            key.private_bytes(
                serialization.Encoding.PEM, private_format, serialization.NoEncryption()
            ),
        )
        certificate_file(LOCAL / f"certs/{name}.crt", cert.public_bytes(serialization.Encoding.PEM))
        (LOCAL / f"certs/{name}.crt").chmod(0o644)


def settings():
    if os.environ.get("APP_ENV") == "production":
        raise ValueError("Demo operations refuse APP_ENV=production")
    config = LOCAL / "config.env"
    if not config.exists():
        raise ValueError("Run staging-init first")
    values = dict(line.split("=", 1) for line in config.read_text().splitlines() if "=" in line)
    for key in ["STAGING_POSTGRES_PASSWORD", "STAGING_APP_PASSWORD"]:
        if not re.fullmatch(r"[a-f0-9]{48}", values.get(key, "")):
            raise ValueError("Invalid isolated staging credential")
    if not all(
        (LOCAL / file).exists() for file in ["keys/backup.key", "certs/ca.crt", "accounts.json"]
    ):
        raise ValueError("Incomplete isolated staging initialization")
    return values


def database_name(value: str):
    if not re.fullmatch(r"petland_demo|petland_(?:reset|recovery)_[a-f0-9]{32}_demo", value):
        raise ValueError("Refusing a database outside the isolated P07 namespace")
    return value


def active_database():
    return database_name((LOCAL / "active-db.txt").read_text().strip())


def compose(*args: str, capture=False, data=None):
    env = {**os.environ, **settings(), "ACTIVE_DATABASE": active_database()}
    env.pop("VIRTUAL_ENV", None)
    revision = (
        subprocess.check_output(["git", "rev-parse", "--short=12", "HEAD"], cwd=ROOT)
        .decode()
        .strip()
    )
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT))
    env["RELEASE_ID"] = revision + ("-work" if dirty else "")
    return subprocess.run(
        [
            "docker",
            "compose",
            "--env-file",
            str(LOCAL / "config.env"),
            "-f",
            str(ROOT / "infra/compose/staging.yaml"),
            *args,
        ],
        cwd=ROOT,
        env=env,
        input=data,
        capture_output=capture,
        check=True,
    )


def engine_for(name=None):
    values = settings()
    return create_engine(
        URL.create(
            "postgresql+psycopg",
            username="petland_migrator",
            password=values["STAGING_POSTGRES_PASSWORD"],
            host="127.0.0.1",
            port=55434,
            database=database_name(name or active_database()),
            query={"sslmode": "verify-full", "sslrootcert": str(LOCAL / "certs/ca.crt")},
        ),
        hide_parameters=True,
    )


def manifest(engine):
    with engine.connect() as db:
        value = db.scalar(text("SELECT payload FROM petland_ops.demo_manifest WHERE id=1"))
        if not value or value["fixture"] != FIXTURE:
            raise ValueError("Database has no owned synthetic demo marker")
        return value


def fingerprints(engine):
    result = {}
    with engine.connect() as db:
        for schema, table in db.execute(
            text(
                "SELECT schemaname, tablename FROM pg_tables WHERE schemaname IN ('public', 'petland_ops') ORDER BY 1,2"
            )
        ):
            # Names originate in PostgreSQL, not user input; still constrain before quoting.
            if not re.fullmatch(r"[a-z_]+", schema) or not re.fullmatch(r"[a-z_]+", table):
                raise ValueError("Unexpected table identifier")
            digest, count = hashlib.sha256(), 0
            for row in db.scalars(
                text(
                    f'SELECT row_to_json(t)::text FROM "{schema}"."{table}" t ORDER BY row_to_json(t)::text'
                )
            ):
                digest.update(row.encode() + b"\n")
                count += 1
            result[f"{schema}.{table}"] = {"rows": count, "sha256": digest.hexdigest()}
    return result


def seed_demo(reference=None):
    credentials = json.loads((LOCAL / "accounts.json").read_text())
    engine = engine_for()
    try:
        with Session(engine) as session, session.begin():
            # Bootstrap is privileged and has no HTTP route; serialize concurrent seed commands.
            session.execute(text("SELECT pg_advisory_xact_lock(730007)"))
            result = seed(
                session,
                {k: v["password"] for k, v in credentials.items()},
                reference or datetime.now(ZoneInfo("America/Sao_Paulo")).date(),
            )
        print("Synthetic demo present; existing fixture preserved on repeated invocation.")
        return result
    finally:
        engine.dispose()


def create_database(name):
    database_name(name)
    engine = engine_for("petland_demo")
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as db:
            if db.scalar(text("SELECT 1 FROM pg_database WHERE datname=:name"), {"name": name}):
                raise ValueError("Restore/reset target already exists; it will not be overwritten")
            db.execute(text(f'CREATE DATABASE "{name}" OWNER petland_migrator'))
        destination = engine_for(name)
        try:
            with destination.begin() as db:
                db.execute(text("REVOKE CREATE ON SCHEMA public FROM PUBLIC"))
                db.execute(text("GRANT USAGE ON SCHEMA public TO petland_app"))
                db.execute(
                    text(
                        "ALTER DEFAULT PRIVILEGES FOR ROLE petland_migrator IN SCHEMA public GRANT SELECT ON TABLES TO petland_app"
                    )
                )
        finally:
            destination.dispose()
    finally:
        engine.dispose()


def migrate_database(name):
    engine = engine_for(name)
    previous = os.environ.get("MIGRATION_DATABASE_URL")
    os.environ["MIGRATION_DATABASE_URL"] = engine.url.render_as_string(hide_password=False)
    try:
        command.upgrade(Config(str(ROOT / "apps/api/alembic.ini")), "head")
    finally:
        engine.dispose()
        if previous is None:
            os.environ.pop("MIGRATION_DATABASE_URL", None)
        else:
            os.environ["MIGRATION_DATABASE_URL"] = previous


def backup():
    compose("stop", "api", capture=True)
    engine = engine_for()
    try:
        source = active_database()
        marker, before = manifest(engine), fingerprints(engine)
        started = time.monotonic()
        dump = compose(
            "exec",
            "-T",
            "postgres",
            "pg_dump",
            "-U",
            "petland_migrator",
            "-d",
            source,
            "--format=custom",
            "--no-owner",
            capture=True,
        ).stdout
        if len(dump) > MAX_BACKUP or not dump.startswith(b"PGDMP"):
            raise ValueError("Backup exceeds the bounded demo archive limit or is invalid")
        if before != fingerprints(engine):
            raise ValueError("Data changed while writers were stopped; backup not accepted")
        payload = {
            "format": "petland-p07-backup-v1",
            "created_at": datetime.now(UTC).isoformat(),
            "schema_revision": SCHEMA_REVISION,
            "source": source,
            "fixture": marker,
            "tables": before,
            "dump_sha256": hashlib.sha256(dump).hexdigest(),
            "dump": base64.b64encode(dump).decode(),
        }
        cipher = Fernet((LOCAL / "keys/backup.key").read_bytes()).encrypt(
            json.dumps(payload).encode()
        )
        target = LOCAL / "backups" / f"{datetime.now(UTC):%Y%m%dT%H%M%S}-{uuid4().hex}.plbackup"
        write_private(target, cipher)
        info = {
            "file": target.name,
            "sha256": hashlib.sha256(cipher).hexdigest(),
            "bytes": len(cipher),
            "seconds": round(time.monotonic() - started, 3),
            "created_at": payload["created_at"],
            "source": source,
            "tables": before,
            "schema_revision": SCHEMA_REVISION,
        }
        target.with_suffix(".json").write_text(json.dumps(info, indent=2))
        print("Authenticated encrypted backup created; key and archive stored separately.")
        return target, info
    finally:
        engine.dispose()
        compose("start", "api", capture=True)


def decrypt_backup(path: Path, key: bytes):
    if path.stat().st_size > MAX_BACKUP * 2:
        raise ValueError("Archive exceeds the bounded demo limit")
    value = json.loads(Fernet(key).decrypt(path.read_bytes()))
    if (
        value.get("format") != "petland-p07-backup-v1"
        or value.get("schema_revision") != SCHEMA_REVISION
        or value.get("fixture", {}).get("fixture") != FIXTURE
    ):
        raise ValueError("Unsupported archive, schema revision or fixture")
    database_name(value["source"])
    dump = base64.b64decode(value["dump"], validate=True)
    if (
        not dump.startswith(b"PGDMP")
        or len(dump) > MAX_BACKUP
        or hashlib.sha256(dump).hexdigest() != value["dump_sha256"]
    ):
        raise ValueError("Archive content failed verification")
    return value, dump


def restore(path: Path):
    # Authenticate before creating any target. No --clean, overwrite or production DSN.
    value, dump = decrypt_backup(path, (LOCAL / "keys/backup.key").read_bytes())
    name = f"petland_recovery_{uuid4().hex}_demo"
    started = time.monotonic()
    create_database(name)
    compose(
        "exec",
        "-T",
        "postgres",
        "pg_restore",
        "-U",
        "petland_migrator",
        "-d",
        name,
        "--no-owner",
        "--exit-on-error",
        "--single-transaction",
        capture=True,
        data=dump,
    )
    engine = engine_for(name)
    try:
        if fingerprints(engine) != value["tables"] or manifest(engine) != value["fixture"]:
            raise ValueError(
                "Restore reconciliation failed; source preserved and target not activated"
            )
        # Preserve restricted grants and both GiST exclusion constraints.
        with engine.connect() as db:
            protected = db.scalar(
                text("SELECT has_table_privilege('petland_app','appointments','INSERT')")
            )
            protected = protected and not db.scalar(
                text("SELECT has_table_privilege('petland_app','appointment_notes','DELETE')")
            )
            protected = protected and not db.scalar(
                text("SELECT has_table_privilege('petland_app','audit_events','UPDATE')")
            )
            exclusions = db.scalar(
                text(
                    "SELECT count(*) FROM pg_constraint WHERE conrelid='appointments'::regclass AND contype='x'"
                )
            )
            if not protected or exclusions != 2:
                raise ValueError("Restored permissions or concurrency exclusions are incompatible")
        result = {
            "target": name,
            "seconds": round(time.monotonic() - started, 3),
            "tables": value["tables"],
            "reconciled": True,
            "backup_age_seconds": round(
                (datetime.now(UTC) - datetime.fromisoformat(value["created_at"])).total_seconds(), 3
            ),
        }
        record = LOCAL / "restores" / f"{name}.json"
        record.parent.mkdir(parents=True, exist_ok=True)
        record.write_text(json.dumps(result, indent=2))
        return result
    finally:
        engine.dispose()


def activate(name):
    database_name(name)
    if name.startswith("petland_recovery_"):
        proof = LOCAL / "restores" / f"{name}.json"
        if not proof.exists() or not json.loads(proof.read_text()).get("reconciled"):
            raise ValueError("Recovery target has not passed reconciliation")
    engine = engine_for(name)
    try:
        manifest(engine)
        with engine.connect() as db:
            if db.scalar(text("SELECT version_num FROM alembic_version")) != SCHEMA_REVISION:
                raise ValueError("Target schema is incompatible; active database preserved")
    finally:
        engine.dispose()
    previous = active_database()
    compose("stop", "api", capture=True)
    (LOCAL / "active-db.txt").write_text(database_name(name))
    try:
        # This job alone migrates; workers never perform DDL at startup.
        compose("up", "-d", "--force-recreate", "--wait", "web")
    except Exception:
        # Restore the pointer even if restarting the original also fails.
        (LOCAL / "active-db.txt").write_text(previous)
        compose("up", "-d", "--force-recreate", "--wait", "web")
        raise


def browser_smoke(phase):
    subprocess.run(
        ["node", str(ROOT / "apps/web/scripts/smoke-staging.mjs"), phase], cwd=ROOT, check=True
    )
    return json.loads((LOCAL / f"browser/{phase}/report.json").read_text())


def image_evidence():
    result = {}
    for service in ["api", "web"]:
        container = compose("ps", "-q", service, capture=True).stdout.decode().strip()
        image_id = (
            subprocess.check_output(["docker", "inspect", "--format", "{{.Image}}", container])
            .decode()
            .strip()
        )
        revision = (
            subprocess.check_output(
                [
                    "docker",
                    "image",
                    "inspect",
                    "--format",
                    '{{index .Config.Labels "org.opencontainers.image.revision"}}',
                    image_id,
                ]
            )
            .decode()
            .strip()
        )
        result[service] = {"image_id": image_id, "revision": revision}
    return result


def smoke():
    engine = engine_for()
    try:
        fixture = manifest(engine)
    finally:
        engine.dispose()
    context = ssl.create_default_context(cafile=str(LOCAL / "certs/ca.crt"))
    with httpx.Client(
        base_url=ORIGIN,
        verify=context,
        timeout=httpx.Timeout(10, connect=3),
        headers={"Origin": ORIGIN},
    ) as client:
        for _ in range(30):
            try:
                if client.get("/api/v1/health/ready").status_code == 200:
                    break
            except httpx.TransportError as exc:
                if "CERTIFICATE_VERIFY_FAILED" in str(exc):
                    raise ValueError(
                        "Local TLS certificate verification failed; renew certificates"
                    ) from None
            time.sleep(1)
        else:
            raise ValueError("Staging readiness failed")
        for path in [
            "/",
            "/entrar",
            "/servicos",
            "/app/pets",
            "/operacao/agenda",
            "/gestao/auditoria",
        ]:
            response = client.get(path)
            assert response.status_code == 200 and '<div id="root">' in response.text
            assert response.headers["x-content-type-options"] == "nosniff"
            assert "unsafe-eval" not in response.headers["content-security-policy"]
        catalog = client.get("/api/v1/catalog/services")
        assert catalog.status_code == 200 and catalog.json()["total"] == 2
        assert "no-store" in catalog.headers["cache-control"]
        csrf = client.get("/api/v1/auth/csrf")
        assert "Secure" in csrf.headers["set-cookie"] and "HttpOnly" in csrf.headers["set-cookie"]
        accounts = json.loads((LOCAL / "accounts.json").read_text())
        for key, path in [
            ("customer_a", "/api/v1/me/pets"),
            ("employee", "/api/v1/operations/agenda"),
            ("admin", "/api/v1/management/users"),
        ]:
            token = client.get("/api/v1/auth/csrf").json()["csrf_token"]
            response = client.post(
                "/api/v1/auth/login", json=accounts[key], headers={"X-CSRF-Token": token}
            )
            assert response.status_code == 200
            assert "Secure" in response.headers["set-cookie"]
            assert client.get(path).status_code == 200
            if key != "admin":
                assert client.get("/api/v1/management/users").status_code == 403
            if key == "customer_a":
                replay_file = LOCAL / "replay.json"
                replay = json.loads(replay_file.read_text()) if replay_file.exists() else None
                check_engine = engine_for()
                try:
                    with check_engine.connect() as db:
                        replay_exists = replay and db.scalar(
                            text(
                                "SELECT 1 FROM booking_idempotency WHERE actor_id=:actor AND operation='book' AND key=:key"
                            ),
                            {"actor": fixture["accounts"]["customer_a"], "key": replay["key"]},
                        )
                finally:
                    check_engine.dispose()
                if not replay_exists:
                    free_day = date.fromisoformat(fixture["reference_date"]) + timedelta(days=2)
                    free = client.get(
                        "/api/v1/me/availability",
                        params={
                            "pet_id": fixture["pets"]["Luna demo"],
                            "service_id": fixture["services"]["bath"],
                            "date": str(free_day),
                        },
                    ).json()
                    if not free.get("slots"):
                        raise ValueError(
                            "Demo dates are stale or full; reset-demo with a fresh reference"
                        )
                    replay = {
                        "key": str(uuid4()),
                        "body": {
                            "pet_id": fixture["pets"]["Luna demo"],
                            "service_id": fixture["services"]["bath"],
                            "starts_at": free["slots"][0]["starts_at"],
                            "offer_version": free["offer"]["version"],
                            "configuration_version": free["configuration_version"],
                        },
                    }
                token = client.get("/api/v1/auth/csrf").json()["csrf_token"]
                headers = {"X-CSRF-Token": token, "Idempotency-Key": replay["key"]}
                booked = client.post(
                    "/api/v1/me/appointments", json=replay["body"], headers=headers
                )
                assert booked.status_code == 201
                if replay_exists:
                    assert booked.json()["id"] == replay["appointment_id"]
                    assert (
                        client.get(f"/api/v1/me/appointments/{replay['appointment_id']}").json()[
                            "appointment"
                        ]["status"]
                        == "CANCELLED"
                    )
                else:
                    replay["appointment_id"] = booked.json()["id"]
                    duplicate = client.post(
                        "/api/v1/me/appointments", json=replay["body"], headers=headers
                    )
                    assert duplicate.status_code == 201 and duplicate.json() == booked.json()
                    cancelled = client.post(
                        f"/api/v1/me/appointments/{replay['appointment_id']}/cancel",
                        json={"version": 1, "reason": "Ensaio sintético P07"},
                        headers={"X-CSRF-Token": token, "Idempotency-Key": str(uuid4())},
                    )
                    assert cancelled.status_code == 200
                    replay_file.write_text(json.dumps(replay))
                assert (
                    client.get(f"/api/v1/me/pets/{fixture['pets']['Mimi demo']}").status_code == 404
                )
                history = client.get(
                    f"/api/v1/me/appointments/{fixture['appointments']['completed']}"
                )
                assert history.status_code == 200
                assert "Nota interna fictícia P07" not in history.text
                assert "Atendimento de demonstração concluído." in history.text
                assert (
                    client.get(
                        f"/api/v1/catalog/services/{fixture['services']['inactive']}"
                    ).status_code
                    == 404
                )
                first_day = date.fromisoformat(fixture["reference_date"]) + timedelta(days=1)
                availability = client.get(
                    "/api/v1/me/availability",
                    params={
                        "pet_id": fixture["pets"]["Thor demo"],
                        "service_id": fixture["services"]["bath"],
                        "date": str(first_day),
                    },
                )
                assert availability.status_code == 200
                occupied = datetime.combine(
                    first_day, datetime.min.time(), ZoneInfo("America/Sao_Paulo")
                ) + timedelta(hours=9)
                token = client.get("/api/v1/auth/csrf").json()["csrf_token"]
                rejected = client.post(
                    "/api/v1/me/appointments",
                    json={
                        "pet_id": fixture["pets"]["Thor demo"],
                        "service_id": fixture["services"]["bath"],
                        "starts_at": occupied.isoformat(),
                        "offer_version": 1,
                        "configuration_version": availability.json()["configuration_version"],
                    },
                    headers={"X-CSRF-Token": token, "Idempotency-Key": str(uuid4())},
                )
                assert rejected.status_code == 409 and rejected.json()["code"] == "SLOT_UNAVAILABLE"
            if key == "employee":
                care = client.get(
                    f"/api/v1/operations/attendances/{fixture['appointments']['completed']}"
                )
                assert care.status_code == 200 and "Nota interna fictícia P07" in care.text
            token = client.get("/api/v1/auth/csrf").json()["csrf_token"]
            assert client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": token}).is_success
        assert client.get("/api/v1/auth/me").status_code == 401
        # Actual STARTTLS SMTP and one-use verification, independent of fixture provision.
        email, password = f"p07-smoke-{uuid4().hex}@example.com", secrets.token_urlsafe(30)
        token = client.get("/api/v1/auth/csrf").json()["csrf_token"]
        assert (
            client.post(
                "/api/v1/auth/register",
                json={"email": email, "display_name": "SMTP sintético P07", "password": password},
                headers={"X-CSRF-Token": token},
            ).status_code
            == 202
        )
        message_id = None
        for _ in range(15):
            messages = httpx.get(
                "http://127.0.0.1:8026/api/v1/search", params={"query": f"to:{email}"}, timeout=5
            ).json()
            message_id = next(
                (m["ID"] for m in messages.get("messages", []) if "Confirme" in m["Subject"]), None
            )
            if message_id:
                break
            time.sleep(1)
        if not message_id:
            raise ValueError("Actual STARTTLS mail delivery not observed in isolated Mailpit")
        message = httpx.get(f"http://127.0.0.1:8026/api/v1/message/{message_id}", timeout=5).json()
        link = re.search(r"https://localhost:8443/verificar-email#token=([^\s]+)", message["Text"])
        assert link
        verification = parse_qs(urlsplit(link[0]).fragment)["token"][0]
        token = client.get("/api/v1/auth/csrf").json()["csrf_token"]
        headers = {"X-CSRF-Token": token}
        assert (
            client.post(
                "/api/v1/auth/email-verifications", json={"token": verification}, headers=headers
            ).status_code
            == 200
        )
        assert (
            client.post(
                "/api/v1/auth/email-verifications", json={"token": verification}, headers=headers
            ).status_code
            == 400
        )
    print("TLS, static deep links, API, secure cookies and three demo profiles passed.")
    return {
        "passed": True,
        "tls_verified": True,
        "smtp_starttls_verified": True,
        "profiles": 3,
        "static_deep_links": 6,
        "ownership_private_notes_and_capacity": True,
        "persistent_booking_idempotency": True,
    }


def rehearse():
    source = active_database()
    compose("stop", "api", capture=True)
    try:
        seed_demo()
        engine = engine_for()
        try:
            before = fingerprints(engine)
            seed_demo()
            assert before == fingerprints(engine)
        finally:
            engine.dispose()
    finally:
        compose("start", "api", capture=True)
    first_smoke = smoke()
    source_browser = browser_smoke("source")
    path, backup_info = backup()
    restored = restore(path)
    started = time.monotonic()
    try:
        activate(restored["target"])
        second_smoke = smoke()
        restored_browser = browser_smoke("recovery")
        restored["activation_and_smoke_seconds"] = round(time.monotonic() - started, 3)
    finally:
        activate(source)
    final_smoke = smoke()
    return_browser = browser_smoke("return")
    result = {
        "executed_at": datetime.now(UTC).isoformat(),
        "fixture": FIXTURE,
        "seed_idempotent": True,
        "backup": backup_info,
        "restore": restored,
        "source_smoke": first_smoke,
        "restored_smoke": second_smoke,
        "return_to_source_smoke": final_smoke,
        "browser": {
            "source": source_browser,
            "recovery": restored_browser,
            "return": return_browser,
        },
        "source_preserved": True,
        "images": image_evidence(),
        "external_publish": False,
        "off_host_backup": False,
        "rpo_rto": "Observed rehearsal durations only; no production SLA or off-host recovery guarantee.",
    }
    (LOCAL / "rehearsal.json").write_text(json.dumps(result, indent=2) + "\n")
    print("Backup/restore, reconciliation, activation and return to the preserved source passed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=[
            "init",
            "up",
            "down",
            "seed-demo",
            "reset-demo",
            "backup",
            "restore",
            "smoke",
            "rehearse",
            "renew-certs",
            "activate",
        ],
    )
    parser.add_argument("--reference-date", type=date.fromisoformat)
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--confirm")
    parser.add_argument("--target", help="Existing reconciled P07 demo database")
    args = parser.parse_args()
    if args.command == "init":
        initialize()
        return
    settings()
    if args.command == "renew-certs":
        issue_certificates(replace=True)
        compose("restart", "postgres", "mailpit", "api", "web")
        print("Local demo certificates renewed; generated credentials preserved.")
    elif args.command == "up":
        compose("up", "-d", "--build", "--wait", "web")
    elif args.command == "activate":
        if not args.target:
            parser.error("activate requires --target from a reconciled restore")
        activate(database_name(args.target))
    elif args.command == "down":
        compose("down")
    elif args.command == "seed-demo":
        seed_demo(args.reference_date)
    elif args.command == "reset-demo":
        if args.confirm != active_database():
            parser.error("reset-demo requires --confirm with the exact active demo database name")
        name = f"petland_reset_{uuid4().hex}_demo"
        create_database(name)
        migrate_database(name)
        previous = active_database()
        (LOCAL / "active-db.txt").write_text(name)
        try:
            seed_demo(args.reference_date)
        finally:
            (LOCAL / "active-db.txt").write_text(previous)
        activate(name)
        print("New synthetic demo activated; previous database preserved.")
    elif args.command == "backup":
        path, _ = backup()
        print(path)
    elif args.command == "restore":
        if not args.backup:
            parser.error("restore requires --backup; target is always a new isolated database")
        print(json.dumps(restore(args.backup.resolve()), indent=2))
    elif args.command == "smoke":
        smoke()
    elif args.command == "rehearse":
        rehearse()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # No DSN, SQL values, SMTP bodies, archive plaintext or credentials in CLI errors.
        raise SystemExit(
            f"Operation failed: {type(exc).__name__}; inspect isolated staging and runbook."
        ) from None
