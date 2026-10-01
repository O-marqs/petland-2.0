from uuid import UUID

from sqlalchemy.orm import Session

from petland.modules.customers.infrastructure.store import PostgresCustomers
from petland.shared.domain.errors import BusinessError


def customer_for(session: Session, actor_id: UUID, assisted_id: UUID | None) -> UUID:
    """Resolve an owner inside the pet transaction, never from a client-supplied user id."""
    return customer_booking_contact(session, actor_id, assisted_id)[0]


def customer_booking_contact(
    session: Session, actor_id: UUID, assisted_id: UUID | None
) -> tuple[UUID, str]:
    """Resolve the owner and notification recipient from the same database snapshot."""
    store = PostgresCustomers(session)
    customer = store.get(assisted_id) if assisted_id else store.own(actor_id)
    if not customer:
        raise BusinessError("NOT_FOUND", 404)
    return customer.id, customer.email
