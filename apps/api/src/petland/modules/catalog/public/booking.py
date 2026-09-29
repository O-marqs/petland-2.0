from uuid import UUID

from sqlalchemy.orm import Session

from petland.modules.catalog.domain.models import Service
from petland.modules.catalog.infrastructure.store import PostgresCatalog


def booking_service(session: Session, service_id: UUID) -> Service:
    return PostgresCatalog(session).get(service_id)
