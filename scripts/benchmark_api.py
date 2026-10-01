"""RNF02: isolated PostgreSQL, 100k synthetic visits, 20 concurrent HTTP sessions.

Run through `python scripts/dev.py benchmark`. Never accepts a production target.
Creates and drops only its randomly named database on TEST_DATABASE_URL's server.
"""

import argparse
import json
import math
import os
import platform
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Barrier, BrokenBarrierError
from uuid import uuid4

import httpx
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine, make_url

from petland.modules.catalog.infrastructure.models import (
    OptionRecord,
    ServiceRecord,
    ServiceSpeciesRecord,
)
from petland.modules.customers.infrastructure.models import CustomerRecord
from petland.modules.identity.infrastructure.models import (
    AuditRecord,
    RoleRecord,
    SessionRecord,
    UserRecord,
)
from petland.modules.identity.infrastructure.security import SecureTokens
from petland.modules.pets.infrastructure.models import PetRecord
from petland.modules.scheduling.domain.models import Calendar, Configuration, Day, Window
from petland.modules.scheduling.infrastructure.models import (
    AppointmentRecord,
    ConfigurationRecord,
    ResourceRecord,
)
from petland.modules.scheduling.infrastructure.values import document

ROOT = Path(__file__).resolve().parents[1]
CONCURRENCY = 20
COUNT = 100_000


def create_benchmark_app():
    from petland.bootstrap.app import create_app

    app = create_app()
    if os.environ.get("BENCH_SQL_PROFILE") == "1":

        @event.listens_for(Engine, "before_cursor_execute")
        def before(conn, cursor, statement, parameters, context, executemany):
            context.benchmark_started = time.perf_counter()

        @event.listens_for(Engine, "after_cursor_execute")
        def after(conn, cursor, statement, parameters, context, executemany):
            elapsed = (time.perf_counter() - context.benchmark_started) * 1000
            if elapsed >= 5:
                # SQL templates only. Never log bound values, tokens or connection URLs.
                print(
                    json.dumps(
                        dict(event="benchmark_sql", ms=round(elapsed, 2), statement=statement[:180])
                    ),
                    flush=True,
                )

        @event.listens_for(Engine, "handle_error")
        def failed(context):
            print(
                json.dumps(
                    dict(
                        event="benchmark_sql_error",
                        sqlstate=getattr(context.original_exception, "sqlstate", None),
                        statement=(context.statement or "")[:180],
                    )
                ),
                flush=True,
            )

    return app


def seed(engine):
    now = datetime.now(UTC)
    today = now.replace(hour=12, minute=0, second=0, microsecond=0)
    users = [uuid4() for _ in range(60)]
    customers = [uuid4() for _ in range(2000)]
    pets = [uuid4() for _ in customers]
    resources = [uuid4() for _ in range(5)]
    service_id = uuid4()
    tokens = SecureTokens()
    sessions = [tokens.new() for _ in users]
    with engine.begin() as db:
        db.execute(
            UserRecord.__table__.insert(),
            [
                dict(
                    id=id,
                    email=f"synthetic-{i}@example.com",
                    normalized_email=f"synthetic-{i}@example.com",
                    display_name=f"Pessoa sintética {i}",
                    password_hash="!benchmark-login-disabled",
                    status="ACTIVE",
                    email_verified_at=now,
                    created_at=now,
                    version=1,
                )
                for i, id in enumerate(users)
            ],
        )
        db.execute(
            RoleRecord.__table__.insert(),
            [
                dict(user_id=id, role=("CUSTOMER" if i < 20 else "EMPLOYEE" if i < 40 else "ADMIN"))
                for i, id in enumerate(users)
            ],
        )
        db.execute(
            SessionRecord.__table__.insert(),
            [
                dict(
                    id=uuid4(),
                    user_id=id,
                    token_digest=tokens.digest(sessions[i]),
                    created_at=now,
                    last_seen_at=now,
                    expires_at=now + timedelta(hours=2),
                    idle_expires_at=now + timedelta(hours=2),
                    revoked_at=None,
                )
                for i, id in enumerate(users)
            ],
        )
        db.execute(
            CustomerRecord.__table__.insert(),
            [
                dict(
                    id=id,
                    user_id=users[i] if i < 20 else None,
                    name=f"Cliente sintético {i}",
                    email=f"synthetic-{i}@example.com",
                    phone="",
                    address="",
                    created_at=now,
                    updated_at=now,
                    version=1,
                )
                for i, id in enumerate(customers)
            ],
        )
        db.execute(
            PetRecord.__table__.insert(),
            [
                dict(
                    id=id,
                    customer_id=customers[i],
                    name=f"Pet sintético {i}",
                    species_id="DOG",
                    breed_id=None,
                    size="SMALL",
                    sex="UNKNOWN",
                    birth_date=None,
                    birth_estimated=False,
                    care_notes="",
                    created_at=now,
                    updated_at=now,
                    archived_at=None,
                    version=1,
                )
                for i, id in enumerate(pets)
            ],
        )
        db.execute(
            ServiceRecord.__table__.insert(),
            dict(
                id=service_id,
                name="Banho sintético",
                description="Oferta exclusiva do benchmark",
                active=True,
                created_at=now,
                updated_at=now,
                version=1,
            ),
        )
        db.execute(
            ServiceSpeciesRecord.__table__.insert(), dict(service_id=service_id, species_id="DOG")
        )
        db.execute(
            OptionRecord.__table__.insert(),
            dict(
                service_id=service_id,
                size="SMALL",
                price="80.00",
                duration_minutes=30,
                buffer_before_minutes=0,
                buffer_after_minutes=0,
            ),
        )
        db.execute(
            ResourceRecord.__table__.insert(),
            [
                dict(
                    id=id,
                    user_id=users[20 + i],
                    name=f"Equipe sintética {i}",
                    active=True,
                    service_ids=[str(service_id)],
                    calendar=None,
                    version=1,
                )
                for i, id in enumerate(resources)
            ],
        )
        config = Configuration(
            enabled=True,
            horizon_days=30,
            calendar=Calendar([Day(d, [Window(540, 1140)]) for d in range(7)]),
        )
        db.execute(
            ConfigurationRecord.__table__.update()
            .where(ConfigurationRecord.id == 1)
            .values(data=document(config))
        )
        for batch in range(0, COUNT, 1000):
            appointments, audits = [], []
            for i in range(batch, batch + 1000):
                at = (
                    today - timedelta(days=1000 - i // 100) + timedelta(minutes=(i % 100 // 5) * 30)
                )
                end = at + timedelta(minutes=30)
                id = uuid4()
                status = "CANCELLED" if i % 10 == 0 else "NO_SHOW" if i % 10 == 1 else "COMPLETED"
                appointments.append(
                    dict(
                        id=id,
                        customer_id=customers[i % 2000],
                        pet_id=pets[i % 2000],
                        service_id=service_id,
                        resource_id=resources[i % 5],
                        starts_at=at,
                        ends_at=end,
                        occupied_start_at=at,
                        occupied_end_at=end,
                        offer=dict(
                            service_id=str(service_id),
                            service_name="Banho sintético",
                            pet_name=f"Pet sintético {i % 2000}",
                            size="SMALL",
                            price="80.00",
                            duration_minutes=30,
                            buffer_before_minutes=0,
                            buffer_after_minutes=0,
                            version=1,
                        ),
                        timezone="America/Sao_Paulo",
                        change_cutoff_minutes=0,
                        status=status,
                        version=1,
                        created_at=at,
                        updated_at=end,
                        no_show_grace_minutes=0,
                        arrived_at=at if status == "COMPLETED" else None,
                        started_at=at if status == "COMPLETED" else None,
                        completed_at=end if status == "COMPLETED" else None,
                        reserved_until=None,
                    )
                )
                audits.append(
                    dict(
                        id=uuid4(),
                        actor_user_id=users[20 + i % 5],
                        target_id=id,
                        action="appointment.complete",
                        occurred_at=end,
                        request_id="synthetic-benchmark",
                        result="success",
                    )
                )
            db.execute(AppointmentRecord.__table__.insert().values(appointments))
            db.execute(AuditRecord.__table__.insert().values(audits))
            if (batch + 1000) % 25000 == 0:
                print(f"Seeded {batch + 1000} / {COUNT}", flush=True)
        db.execute(text("ANALYZE"))
    return sessions, pets[:20], service_id, today


def measure(base, tokens, path, iterations, booking=None):
    barrier = Barrier(CONCURRENCY)

    def worker(i):
        with httpx.Client(
            base_url=base,
            timeout=60,
            headers={"Origin": "http://localhost:5173"},
            cookies={"petland_dev_session": tokens[i]},
        ) as client:
            try:
                csrf = client.get("/api/v1/auth/csrf")
                csrf.raise_for_status()
                headers = {"X-CSRF-Token": csrf.json()["csrf_token"]}
                # Warm caches; measured requests still use real sessions and SQL.
                client.get("/api/v1/auth/me").raise_for_status()
                warmups = []
                if not booking:
                    for _ in range(3):
                        warmups.append(client.get(path).status_code)
            except Exception:
                barrier.abort()
                raise
            barrier.wait(timeout=60)
            results = []
            for n in range(iterations):
                body = booking(i, n) if booking else None
                start = time.perf_counter()
                response = client.request(
                    "POST" if booking else "GET",
                    path,
                    json=body,
                    headers={**headers, "Idempotency-Key": str(uuid4())} if booking else None,
                )
                results.append(
                    (
                        (time.perf_counter() - start) * 1000,
                        response.status_code,
                        response.json().get("code", "") if response.is_error else "",
                    )
                )
            return results, warmups

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        futures = [pool.submit(worker, i) for i in range(CONCURRENCY)]
        batches, failures = [], []
        for future in futures:
            try:
                batches.append(future.result())
            except Exception as exc:
                failures.append(exc)
        if failures:
            cause = next(
                (e for e in failures if not isinstance(e, BrokenBarrierError)), failures[0]
            )
            status = cause.response.status_code if isinstance(cause, httpx.HTTPStatusError) else ""
            raise RuntimeError(f"Scenario aborted: {type(cause).__name__} {status}") from None
    samples = [sample for batch, _ in batches for sample in batch]
    warmups = [status for _, batch in batches for status in batch]
    times = sorted(t for t, _, _ in samples)
    expected = 201 if booking else 200
    return dict(
        samples=len(samples),
        concurrency=CONCURRENCY,
        p50_ms=round(times[math.ceil(len(times) * 0.5) - 1], 2),
        p95_ms=round(times[math.ceil(len(times) * 0.95) - 1], 2),
        max_ms=round(times[-1], 2),
        statuses={
            str(code): sum(s == code for _, s, _ in samples)
            for code in sorted({s for _, s, _ in samples})
        },
        errors={
            code: sum(c == code for _, _, c in samples) for code in {c for _, _, c in samples if c}
        },
        target_ms=800 if booking else 400,
        warmup_errors=sum(status != 200 for status in warmups),
        passed=all(s == expected for _, s, _ in samples)
        and all(status == 200 for status in warmups)
        and times[math.ceil(len(times) * 0.95) - 1] <= (800 if booking else 400),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".local-p06-api-benchmark.json")
    parser.add_argument("--iterations", type=int, default=10)
    parser.add_argument("--workers", type=int, choices=[1, 2, 3, 4], default=2)
    parser.add_argument("--profile", action="store_true")
    args = parser.parse_args()
    if not 5 <= args.iterations <= 50:
        parser.error("iterations must be between 5 and 50")
    source = make_url(os.environ["TEST_DATABASE_URL"])
    if (
        os.environ.get("APP_ENV") != "test"
        or not (source.database or "").endswith("_test")
        or source.host not in {"127.0.0.1", "localhost", "test-postgres"}
    ):
        raise SystemExit(
            "Requires APP_ENV=test and a local disposable TEST_DATABASE_URL ending _test"
        )
    name = f"petland_bench_{uuid4().hex}_test"
    url = source.set(database=name).render_as_string(hide_password=False)
    admin = create_engine(source, isolation_level="AUTOCOMMIT", hide_parameters=True)
    engine, process = None, None
    report = {"started_at": datetime.now(UTC).isoformat(), "passed": False, "results": {}}

    def write_report():
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    write_report()
    try:
        with admin.connect() as db:
            db.execute(text(f'CREATE DATABASE "{name}"'))
        os.environ["MIGRATION_DATABASE_URL"] = url
        command.upgrade(Config(str(ROOT / "apps/api/alembic.ini")), "head")
        engine = create_engine(url, hide_parameters=True)
        print(
            "Seeding 100000 appointments and audit records in an isolated test database.",
            flush=True,
        )
        sessions, pets, service_id, today = seed(engine)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        env = {
            **os.environ,
            "APP_ENV": "test",
            "DATABASE_URL": url,
            "PUBLIC_ORIGIN": "http://localhost:5173",
            "LOG_LEVEL": "WARNING",
            "BENCH_SQL_PROFILE": "1" if args.profile else "0",
        }
        log_path = args.output.with_suffix(".api.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("w", encoding="utf-8") as log:
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "benchmark_api:create_benchmark_app",
                    "--app-dir",
                    str(ROOT / "scripts"),
                    "--factory",
                    "--workers",
                    str(args.workers),
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                    "--no-access-log",
                    "--no-proxy-headers",
                ],
                cwd=ROOT / "apps/api",
                env=env,
                stdout=log,
                stderr=log,
            )
            base = f"http://127.0.0.1:{port}"
            for _ in range(100):
                try:
                    if httpx.get(base + "/api/v1/health/live", timeout=1).is_success:
                        break
                except httpx.TransportError:
                    pass
                if process.poll() is not None:
                    raise RuntimeError(
                        "Benchmark API stopped; inspect .local-p06-benchmark-api.log"
                    )
                time.sleep(0.1)
            else:
                raise RuntimeError("Benchmark API did not become healthy")
            last, first = today.date() - timedelta(days=1), today.date() - timedelta(days=30)
            period = f"date_from={first}&date_to={last}"
            scenarios = [
                ("catalog", sessions[:20], "/api/v1/catalog/services"),
                ("customer_history", sessions[:20], "/api/v1/me/appointments?period=history"),
                (
                    "staff_agenda",
                    sessions[20:40],
                    f"/api/v1/operations/agenda?date_from={last}&date_to={last}",
                ),
                ("admin_metrics_month", sessions[40:], f"/api/v1/management/metrics?{period}"),
                (
                    "admin_audit_month",
                    sessions[40:],
                    f"/api/v1/management/audit?start={first}T00:00:00Z&end={today.date()}T00:00:00Z",
                ),
            ]
            results = {}
            report["results"] = results
            for label, tokens, path in scenarios:
                results[label] = measure(base, tokens, path, args.iterations)
                write_report()
                print(label, json.dumps(results[label]), flush=True)

            def booking(i, n):
                index = n * 20 + i
                at = today + timedelta(days=1 + index // 100, minutes=(index % 100 // 5) * 30)
                return dict(
                    pet_id=str(pets[i]),
                    service_id=str(service_id),
                    starts_at=at.isoformat(),
                    offer_version=1,
                    configuration_version=1,
                )

            results["booking"] = measure(
                base, sessions[:20], "/api/v1/me/appointments", args.iterations, booking
            )
            print("booking", json.dumps(results["booking"]), flush=True)
            report = dict(
                measured_at=datetime.now(UTC).isoformat(),
                platform=platform.platform(),
                processor=platform.processor(),
                logical_cpus=os.cpu_count(),
                python=platform.python_version(),
                api_workers=args.workers,
                sql_profile=args.profile,
                dataset=dict(
                    appointments=COUNT,
                    customers=2000,
                    pets=2000,
                    employees=5,
                    historical_days=1000,
                    audit_records=COUNT,
                    completed_percent=80,
                    cancelled_percent=10,
                    no_show_percent=10,
                ),
                method="Local uvicorn workers as reported, default DB pool 5+5 per worker, HTTP keep-alive, 20 distinct sessions per scenario; closed-loop, 3 read warmups, nearest-rank percentiles; login/CSRF setup and SMTP delivery excluded; booking commits include outbox.",
                results=results,
                passed=all(r["passed"] for r in results.values()),
            )
            write_report()
            if not report["passed"]:
                raise SystemExit("RNF02 target not met; report saved.")
    except Exception as exc:
        report["aborted"] = type(exc).__name__
        write_report()
        raise
    finally:
        if process is not None and process.poll() is None:
            if os.name == "nt":
                # Only the API process tree created by this benchmark, including workers.
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                )
            else:
                process.terminate()
            process.wait(timeout=15)
        if engine is not None:
            engine.dispose()
        with admin.connect() as db:
            db.execute(text(f'DROP DATABASE IF EXISTS "{name}"'))
        admin.dispose()


if __name__ == "__main__":
    main()
