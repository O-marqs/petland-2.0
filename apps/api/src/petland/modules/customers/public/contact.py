from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from petland.modules.customers.infrastructure.models import CustomerRecord
from petland.modules.customers.infrastructure.store import PostgresCustomers


def customer_email(session: Session, customer_id: UUID) -> str:
    return PostgresCustomers(session).get(customer_id).email


def customer_contact(session: Session, customer_id: UUID) -> tuple[str, str, str]:
    customer = PostgresCustomers(session).get(customer_id)
    return customer.name, customer.phone, customer.email


def customer_names(session: Session, ids: list[UUID]) -> dict[UUID, str]:
    return dict(
        session.execute(
            select(CustomerRecord.id, CustomerRecord.name).where(CustomerRecord.id.in_(ids))
        )
        .tuples()
        .all()
    )


def matching_customer_ids(term: str) -> Select[tuple[UUID]]:
    return select(CustomerRecord.id).where(CustomerRecord.name.icontains(term, autoescape=True))
