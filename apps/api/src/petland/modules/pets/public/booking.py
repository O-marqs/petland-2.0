from uuid import UUID

from sqlalchemy.orm import Session

from petland.modules.pets.domain.models import Pet
from petland.modules.pets.infrastructure.store import PostgresPets
from petland.shared.domain.errors import BusinessError


def booking_pet(session: Session, customer_id: UUID, pet_id: UUID) -> Pet:
    pet = PostgresPets(session).get(customer_id, pet_id)
    if pet.archived_at is not None:
        raise BusinessError("PET_ARCHIVED", 409)
    return pet


def care_context(session: Session, customer_id: UUID, pet_id: UUID) -> tuple[str, str, str]:
    pet = PostgresPets(session).get(customer_id, pet_id)
    return pet.name, pet.species_id, pet.care_notes
