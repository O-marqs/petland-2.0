"""Own synthetic presentation environment on 8445/55436/8028; preserve personal staging."""

import argparse
import json
import os
import ssl
import subprocess
import urllib.request
from pathlib import Path
from uuid import uuid4

import operations as ops
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / ".local/final-case"
PRIVATE = LOCAL / "staging"
PROJECT = "petlandfinalcase"
ORIGIN = "https://localhost:8445"
REFERENCE = "f3d70a2cce07d587351eadaa66864b7c1ae4444a"
COMPOSE = LOCAL / "compose.json"


def configuration():
    env = {**os.environ, **ops.settings(), "RELEASE_ID": REFERENCE[:12]}
    env["COMPOSE_PROJECT_NAME"] = PROJECT
    env["ACTIVE_DATABASE"] = ops.active_database()
    value = json.loads(
        subprocess.check_output(
            [
                "docker",
                "compose",
                "--env-file",
                str(PRIVATE / "config.env"),
                "-f",
                str(ROOT / "infra/compose/staging.yaml"),
                "config",
                "--format",
                "json",
            ],
            env=env,
            cwd=ROOT,
        )
    )
    value["name"] = PROJECT
    value["networks"]["default"]["name"] = PROJECT + "_default"
    value["volumes"]["staging_data"]["name"] = PROJECT + "_staging_data"
    for service, port in [("web", "8445"), ("postgres", "55436"), ("mailpit", "8028")]:
        value["services"][service]["ports"][0]["published"] = port
    value["services"]["api"]["environment"]["PUBLIC_ORIGIN"] = ORIGIN
    for name, service in value["services"].items():
        if name in {"api", "migrate", "web"}:
            kind = "web" if name == "web" else "api"
            service["image"] = f"petland-final-case-{kind}:{REFERENCE[:12]}"
        for volume in service.get("volumes", []):
            if volume["type"] == "bind":
                source = Path(volume["source"])
                if source.is_relative_to(ROOT / ".local/staging"):
                    volume["source"] = str(PRIVATE / source.relative_to(ROOT / ".local/staging"))
    COMPOSE.write_text(json.dumps(value), encoding="utf-8")
    COMPOSE.chmod(0o600)


def compose(*args, capture=False, data=None):
    configuration()
    config = json.loads(COMPOSE.read_text())
    if (
        config["name"] != PROJECT
        or config["volumes"]["staging_data"]["name"] != PROJECT + "_staging_data"
    ):
        raise ValueError("Presentation namespace mismatch")
    return subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE), *args],
        cwd=ROOT,
        env={**os.environ, "COMPOSE_PROJECT_NAME": PROJECT},
        check=True,
        input=data,
        capture_output=capture,
    )


def engine_for(name=None):
    values = ops.settings()
    database = name or ops.active_database()
    if database != "postgres":
        ops.database_name(database)
    return create_engine(
        URL.create(
            "postgresql+psycopg",
            username="petland_migrator",
            password=values["STAGING_POSTGRES_PASSWORD"],
            host="127.0.0.1",
            port=55436,
            database=database,
            query={
                "sslmode": "verify-full",
                "sslrootcert": str(PRIVATE / "certs/ca.crt"),
            },
        ),
        hide_parameters=True,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["up", "fresh", "down"])
    args = parser.parse_args()
    if os.environ.get("APP_ENV") == "production":
        raise SystemExit("Production refused")
    if os.environ.get("COMPOSE_PROJECT_NAME") not in {None, PROJECT}:
        raise SystemExit("Unrelated inherited Compose project refused")
    ops.LOCAL, ops.ORIGIN = PRIVATE, ORIGIN
    ops.engine_for, ops.compose = engine_for, compose
    if args.command == "down":
        compose("down")
        print("Presentation containers stopped; own volume/credentials preserved.")
        return
    if subprocess.check_output(
        [
            "git",
            "diff",
            REFERENCE,
            "--",
            "apps/api/src",
            "apps/api/migrations",
            "apps/web/src",
            "packages/api-contract",
            "infra",
        ],
        cwd=ROOT,
    ):
        raise SystemExit("Functional source differs from the declared capture commit")
    ops.initialize()
    if args.command == "up":
        compose("up", "-d", "--build", "--wait")
    else:
        target = "petland_reset_" + uuid4().hex + "_demo"
        ops.create_database(target)
        ops.migrate_database(target)
        (PRIVATE / "active-db.txt").write_text(target)
        compose("up", "-d", "--no-build", "--wait")
    fixture = ops.seed_demo()
    context = ssl.create_default_context(cafile=str(PRIVATE / "certs/ca.crt"))
    with urllib.request.urlopen(
        ORIGIN + "/api/v1/health/ready", context=context, timeout=10
    ) as response:
        if response.status != 200:
            raise ValueError("Strict TLS readiness failed")
    with urllib.request.urlopen("http://127.0.0.1:8028/api/v1/info", timeout=10) as response:
        if response.status != 200:
            raise ValueError("Own Mailpit unavailable")
    (LOCAL / "fixture.json").write_text(
        json.dumps(
            {
                "database": ops.active_database(),
                "manifest": fixture,
                "project": PROJECT,
                "origin": ORIGIN,
                "application_commit": REFERENCE,
                "tls_verified": True,
                "source_equality_checked": True,
            }
        ),
        encoding="utf-8",
    )
    print("Own final-case demo ready; TLS/source verified, personal staging untouched.")


if __name__ == "__main__":
    main()
