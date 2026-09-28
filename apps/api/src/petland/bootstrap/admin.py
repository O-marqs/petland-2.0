"""Operator-only first-admin provisioning and cleanup; no default credential or public bootstrap."""

import argparse
from datetime import UTC, datetime, timedelta

from email_validator import validate_email

from petland.bootstrap.identity import build_identity
from petland.bootstrap.settings import Settings
from petland.modules.identity.domain.models import IdentityError
from petland.modules.identity.infrastructure.store import PostgresUnitOfWork
from petland.shared.database import build_engine


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["bootstrap", "prune"])
    parser.add_argument("--email")
    args = parser.parse_args()
    settings = Settings()
    engine = build_engine(settings.database_url.get_secret_value())
    try:
        if args.command == "bootstrap":
            if not args.email:
                parser.error("bootstrap requires --email")
            email = validate_email(
                args.email,
                check_deliverability=False,
                test_environment=settings.app_env in {"development", "test"},
            ).normalized.casefold()
            build_identity(engine, settings).bootstrap(email)
            print(
                "Bootstrap requested. Check the configured mailbox and delivery logs; expires in 30 minutes."
            )
        else:
            with PostgresUnitOfWork(engine) as work:
                work.store.prune(datetime.now(UTC) - timedelta(days=1))
            print("Expired identity sessions, tokens and counters pruned; audit retained.")
    except IdentityError as exc:
        raise SystemExit(exc.code) from None
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
