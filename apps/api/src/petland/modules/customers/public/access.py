from uuid import UUID

from sqlalchemy.orm import Session

from petland.modules.customers.infrastructure.store import PostgresCustomers
from petland.shared.domain.errors import BusinessError


def customer_for(session: Session, actor_id: UUID, assisted_id: UUID | None) -> UUID:
    """Resolve an owner inside the pet transaction, never from a client-supplied user id."""
    store = PostgresCustomers(session)
    if assisted_id:
        return store.get(assisted_id).id
    customer = store.own(actor_id)
    if not customer:
        raise BusinessError("NOT_FOUND", 404)
    return customer.id
