"""Cross-platform commands. Run from any directory; requires uv/pnpm/Docker."""

import argparse
import os
import secrets
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args: str, cwd: Path = ROOT, env: dict[str, str] | None = None) -> None:
    executable = shutil.which(args[0])
    if not executable:
        raise SystemExit(f"Missing tool: {args[0]}. See docs/runbooks/local.md")
    subprocess.run([executable, *args[1:]], cwd=cwd, env=env, check=True)


def environment() -> dict[str, str]:
    env = os.environ.copy()
    path = ROOT / ".env"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env.setdefault(key, value)
    # Never use an unrelated active virtualenv as the project environment.
    env.pop("VIRTUAL_ENV", None)
    return env


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=[
            "init",
            "install",
            "db",
            "migrate",
            "up",
            "down",
            "api",
            "web",
            "lint",
            "test",
            "check",
            "e2e",
        ],
    )
    command = parser.parse_args().command
    if command == "init":
        target = ROOT / ".env"
        if target.exists():
            print(".env already exists; preserved.")
            return
        text = (ROOT / ".env.example").read_text(encoding="utf-8")
        for key in ("MIGRATOR", "APP", "TEST"):
            text = text.replace(f"GENERATE_{key}_PASSWORD", secrets.token_hex(24))
        with target.open("x", encoding="utf-8", newline="\n") as file:
            file.write(text)
        print("Local .env created with random credentials (not printed).")
        return
    env = environment()
    compose = [
        "docker",
        "compose",
        "--env-file",
        str(ROOT / ".env"),
        "-f",
        str(ROOT / "infra/compose/compose.yaml"),
    ]
    api = ROOT / "apps/api"
    if command == "install":
        run("uv", "sync", "--frozen", cwd=api, env=env)
        run("pnpm", "install", "--frozen-lockfile", env=env)
    elif command == "db":
        run(*compose, "up", "-d", "--wait", "postgres", env=env)
    elif command == "up":
        run(*compose, "up", "-d", "--build", "--wait", "web", env=env)
    elif command == "down":
        run(*compose, "--profile", "quality", "down", env=env)
    elif command == "migrate":
        run("uv", "run", "--frozen", "alembic", "upgrade", "head", cwd=api, env=env)
    elif command == "api":
        run(
            "uv",
            "run",
            "--frozen",
            "uvicorn",
            "petland.bootstrap.app:create_app",
            "--factory",
            "--reload",
            "--host",
            "127.0.0.1",
            "--no-access-log",
            cwd=api,
            env=env,
        )
    elif command == "web":
        run("pnpm", "dev", env=env)
    elif command in {"lint", "test", "check"}:
        if command in {"lint", "check"}:
            run(
                "uv",
                "run",
                "--frozen",
                "ruff",
                "check",
                "--config",
                "pyproject.toml",
                ".",
                "../../scripts",
                cwd=api,
                env=env,
            )
            run(
                "uv",
                "run",
                "--frozen",
                "ruff",
                "format",
                "--check",
                "--config",
                "pyproject.toml",
                ".",
                "../../scripts",
                cwd=api,
                env=env,
            )
            run("uv", "run", "--frozen", "mypy", cwd=api, env=env)
            run(
                "uv",
                "run",
                "--frozen",
                "python",
                str(ROOT / "scripts/check_architecture.py"),
                cwd=api,
                env=env,
            )
            run(
                "uv",
                "run",
                "--frozen",
                "python",
                str(ROOT / "scripts/check_repository.py"),
                cwd=api,
                env=env,
            )
            for check in (
                "lint",
                "typecheck",
                "format:check",
                "contracts:check",
                "build",
            ):
                run("pnpm", check, env=env)
        if command in {"test", "check"}:
            run(
                *compose,
                "--profile",
                "quality",
                "up",
                "-d",
                "--wait",
                "test-postgres",
                env=env,
            )
            test_env = {**env, "APP_ENV": "test", "REQUIRE_INTEGRATION": "1"}
            run("uv", "run", "--frozen", "pytest", cwd=api, env=test_env)
            run("pnpm", "test", env=env)
    elif command == "e2e":
        run(
            "pnpm",
            "--filter",
            "@petland/web",
            "exec",
            "playwright",
            "install",
            "chromium",
            env=env,
        )
        run("pnpm", "test:e2e", env=env)


if __name__ == "__main__":
    main()
