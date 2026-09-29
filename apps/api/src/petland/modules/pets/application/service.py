from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from petland.modules.identity.public import Actor
from petland.modules.pets.application.ports import PetStore
from petland.modules.pets.domain.models import Breed, Pet, Sex, Size, Species
from petland.shared.domain.errors import BusinessError


@dataclass
class PetData:
    name: str
    species_id: str
    breed_id: UUID | None
    size: Size
    sex: Sex
    birth_date: date | None
    birth_estimated: bool
    care_notes: str


class Pets:
    def __init__(self, store: Callable[[], AbstractContextManager[PetStore]]) -> None:
        self.store = store

    def species(self) -> list[Species]:
        with self.store() as store:
            return store.species()

    def breeds(self, species_id: str) -> list[Breed]:
        with self.store() as store:
            return store.breeds(species_id)

    def list(
        self, actor: Actor, customer_id: UUID | None, archived: bool, offset: int, limit: int
    ) -> tuple[list[Pet], int]:
        actor.require("customer:assist" if customer_id else "customer:own")
        with self.store() as store:
            owner = store.customer_for(actor.id, customer_id)
            return store.list(owner, archived, offset, limit)

    def get(self, actor: Actor, customer_id: UUID | None, pet_id: UUID) -> Pet:
        actor.require("customer:assist" if customer_id else "customer:own")
        with self.store() as store:
            return store.get(store.customer_for(actor.id, customer_id), pet_id)

    def save(
        self,
        actor: Actor,
        customer_id: UUID | None,
        data: PetData,
        request_id: str,
        pet_id: UUID | None = None,
        version: int | None = None,
    ) -> Pet:
        actor.require("customer:assist" if customer_id else "customer:own")
        now = datetime.now(UTC)
        with self.store() as store:
            owner = store.customer_for(actor.id, customer_id)
            previous = store.get(owner, pet_id, lock=True) if pet_id else None
            if previous and previous.version != version:
                raise BusinessError("STALE_VERSION", 409)
            if previous and previous.archived_at:
                raise BusinessError("PET_ARCHIVED", 409)
            if not store.valid_references(data.species_id, data.breed_id):
                raise BusinessError("INVALID_REFERENCE", 422)
            pet = Pet(
                owner,
                data.name,
                data.species_id,
                data.breed_id,
                data.size,
                data.sex,
                data.birth_date,
                data.birth_estimated,
                data.care_notes,
                now,
                now,
            )
            if previous:
                pet.id, pet.created_at, pet.version = (
                    previous.id,
                    previous.created_at,
                    previous.version + 1,
                )
            pet.validate(now.astimezone(ZoneInfo("America/Sao_Paulo")).date())
            store.save(pet)
            store.audit(actor.id, pet.id, "pet.updated" if previous else "pet.created", request_id)
            return pet

    def archive(
        self,
        actor: Actor,
        customer_id: UUID | None,
        pet_id: UUID,
        archived: bool,
        version: int,
        request_id: str,
    ) -> Pet:
        actor.require("customer:assist" if customer_id else "customer:own")
        with self.store() as store:
            owner = store.customer_for(actor.id, customer_id)
            pet = store.get(owner, pet_id, lock=True)
            if pet.version != version:
                raise BusinessError("STALE_VERSION", 409)
            pet.archived_at = datetime.now(UTC) if archived else None
            pet.updated_at, pet.version = datetime.now(UTC), pet.version + 1
            store.save(pet)
            store.audit(
                actor.id, pet.id, "pet.archived" if archived else "pet.restored", request_id
            )
            return pet
