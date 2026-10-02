"""Prepare/stop a separate synthetic documentation demo; preserve personal staging."""

import argparse
import json
import os
import subprocess
from datetime import date
from pathlib import Path

from demo_data import seed
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / ".local/docs-capture"
REFERENCE = "25495230b75e"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--down", action="store_true")
    parser.add_argument(
        "--build",
        action="store_true",
        help="Build reference images from matching functional source",
    )
    args = parser.parse_args()
    path = LOCAL / "compose.json"
    if args.down:
        config = json.loads(path.read_text())
        if (
            config["name"] != "petlanddocs"
            or config["volumes"]["staging_data"]["name"] != "petlanddocs_staging_data"
        ):
            raise SystemExit("Refusing a project outside the documentation namespace")
        subprocess.run(["docker", "compose", "-f", str(path), "down"], check=True)
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
        raise SystemExit(
            "Functional source differs; review reference and provenance before capture"
        )
    private = ROOT / ".local/staging"
    # Require normal staging-init/up first. Never print resolved Compose credentials.
    values = dict(
        line.split("=", 1)
        for line in (private / "config.env").read_text().splitlines()
        if "=" in line
    )
    original = (private / "active-db.txt").read_text()
    env = {**os.environ, **values, "RELEASE_ID": REFERENCE, "ACTIVE_DATABASE": "petland_demo"}
    resolved = subprocess.check_output(
        [
            "docker",
            "compose",
            "--env-file",
            str(private / "config.env"),
            "-f",
            str(ROOT / "infra/compose/staging.yaml"),
            "config",
            "--format",
            "json",
        ],
        env=env,
    )
    config = json.loads(resolved)
    config["name"] = "petlanddocs"
    config["networks"]["default"]["name"] = "petlanddocs_default"
    config["volumes"]["staging_data"]["name"] = "petlanddocs_staging_data"
    for name, port in [("postgres", "55435"), ("mailpit", "8027"), ("web", "8444")]:
        config["services"][name]["ports"][0]["published"] = port
    config["services"]["api"]["environment"]["PUBLIC_ORIGIN"] = "https://localhost:8444"
    LOCAL.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config), encoding="utf-8")
    path.chmod(0o600)
    if args.build:
        subprocess.run(["docker", "compose", "-f", str(path), "build"], check=True)
    # Existing reference images are reused; no personal environment is restarted.
    subprocess.run(
        ["docker", "compose", "-f", str(path), "up", "-d", "--no-build", "--wait"], check=True
    )
    engine = create_engine(
        URL.create(
            "postgresql+psycopg",
            username="petland_migrator",
            password=values["STAGING_POSTGRES_PASSWORD"],
            host="127.0.0.1",
            port=55435,
            database="petland_demo",
            query={"sslmode": "verify-full", "sslrootcert": str(private / "certs/ca.crt")},
        ),
        hide_parameters=True,
    )
    accounts = json.loads((private / "accounts.json").read_text())
    try:
        with Session(engine) as session, session.begin():
            fixture = seed(
                session, {key: value["password"] for key, value in accounts.items()}, date.today()
            )
    finally:
        engine.dispose()
    (LOCAL / "fixture.json").write_text(json.dumps(fixture), encoding="utf-8")
    if (private / "active-db.txt").read_text() != original:
        raise SystemExit("Personal staging pointer unexpectedly changed")
    print("Independent synthetic documentation demo ready; personal staging pointer preserved.")


if __name__ == "__main__":
    main()
