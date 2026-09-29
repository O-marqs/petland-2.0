from uuid import UUID

from sqlalchemy.orm import Session

from petland.modules.customers.infrastructure.store import PostgresCustomers


def customer_email(session: Session, customer_id: UUID) -> str:
    return PostgresCustomers(session).get(customer_id).email
