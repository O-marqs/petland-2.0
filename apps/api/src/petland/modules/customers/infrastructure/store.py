from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, or_, select, text, update
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from petland.modules.customers.application.ports import CustomerStore
from petland.modules.customers.domain.models import Claim, Customer
from petland.modules.customers.infrastructure.models import ClaimRecord, CustomerRecord
from petland.modules.identity.public.audit import record
from petland.shared.domain.errors import BusinessError


def customer_value(row: CustomerRecord) -> Customer:
    return Customer(**{key: getattr(row, key) for key in Customer.__dataclass_fields__})


class PostgresCustomers:
    def __init__(self, session: Session) -> None:
        self.session = session

    def lock_owner(self, user_id: UUID) -> None:
        self.session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
            {"key": f"customer-owner:{user_id}"},
        )

    def own(self, user_id: UUID) -> Customer | None:
        row = self.session.scalar(select(CustomerRecord).where(CustomerRecord.user_id == user_id))
        return customer_value(row) if row else None

    def get(self, customer_id: UUID, lock: bool = False) -> Customer:
        query = select(CustomerRecord).where(CustomerRecord.id == customer_id)
        if lock:
            query = query.with_for_update()
        row = self.session.scalar(query.execution_options(populate_existing=True))
        if row is None:
            raise BusinessError("NOT_FOUND", 404)
        return customer_value(row)

    def search(self, query: str, offset: int, limit: int) -> tuple[list[Customer], int]:
        condition = or_(
            CustomerRecord.name.icontains(query, autoescape=True),
            CustomerRecord.email.icontains(query, autoescape=True),
            CustomerRecord.phone.contains(query, autoescape=True),
        )
        total = self.session.scalar(
            select(func.count()).select_from(CustomerRecord).where(condition)
        )
        rows = self.session.scalars(
            select(CustomerRecord)
            .where(condition)
            .order_by(CustomerRecord.name, CustomerRecord.id)
            .offset(offset)
            .limit(limit)
        )
        return [customer_value(row) for row in rows], total or 0

    def save(self, customer: Customer) -> None:
        self.session.merge(CustomerRecord(**asdict(customer)))
        self.session.flush()

    def claim(self, digest: str) -> Claim | None:
        row = self.session.scalar(
            select(ClaimRecord)
            .where(ClaimRecord.digest == digest)
            .execution_options(populate_existing=True)
        )
        return (
            Claim(**{key: getattr(row, key) for key in Claim.__dataclass_fields__}) if row else None
        )

    def save_claim(self, claim: Claim) -> None:
        self.session.add(ClaimRecord(**asdict(claim)))

    def invalidate_claims(self, customer_id: UUID) -> None:
        self.session.execute(
            update(ClaimRecord)
            .where(ClaimRecord.customer_id == customer_id, ClaimRecord.used_at.is_(None))
            .values(used_at=datetime.now(UTC))
        )

    def audit(self, actor: UUID, target: UUID, action: str, request_id: str) -> None:
        record(self.session, actor, target, action, request_id)


@contextmanager
def customer_store(engine: Engine) -> Iterator[CustomerStore]:
    with Session(engine) as session, session.begin():
        yield PostgresCustomers(session)
