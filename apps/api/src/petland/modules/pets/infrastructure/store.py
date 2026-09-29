from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from petland.modules.customers.public.access import customer_for
from petland.modules.identity.public.audit import record
from petland.modules.pets.application.ports import PetStore
from petland.modules.pets.domain.models import Breed, Pet, Species
from petland.modules.pets.infrastructure.models import BreedRecord, PetRecord, SpeciesRecord
from petland.shared.domain.errors import BusinessError


def pet_value(row: PetRecord) -> Pet:
    return Pet(**{key: getattr(row, key) for key in Pet.__dataclass_fields__})


class PostgresPets:
    def __init__(self, session: Session) -> None:
        self.session = session

    def customer_for(self, actor_id: UUID, assisted_id: UUID | None) -> UUID:
        return customer_for(self.session, actor_id, assisted_id)

    def species(self) -> list[Species]:
        return [
            Species(row.id, row.name)
            for row in self.session.scalars(select(SpeciesRecord).order_by(SpeciesRecord.name))
        ]

    def breeds(self, species_id: str) -> list[Breed]:
        return [
            Breed(row.id, row.species_id, row.name)
            for row in self.session.scalars(
                select(BreedRecord)
                .where(BreedRecord.species_id == species_id)
                .order_by(BreedRecord.name)
            )
        ]

    def valid_references(self, species_id: str, breed_id: UUID | None) -> bool:
        if not self.session.get(SpeciesRecord, species_id):
            return False
        breed = self.session.get(BreedRecord, breed_id) if breed_id else None
        return breed_id is None or (breed is not None and breed.species_id == species_id)

    def list(
        self, customer_id: UUID, archived: bool, offset: int, limit: int
    ) -> tuple[list[Pet], int]:
        conditions = [
            PetRecord.customer_id == customer_id,
            PetRecord.archived_at.is_not(None) if archived else PetRecord.archived_at.is_(None),
        ]
        total = self.session.scalar(select(func.count()).select_from(PetRecord).where(*conditions))
        rows = self.session.scalars(
            select(PetRecord)
            .where(*conditions)
            .order_by(PetRecord.name, PetRecord.id)
            .offset(offset)
            .limit(limit)
        )
        return [pet_value(row) for row in rows], total or 0

    def get(self, customer_id: UUID, pet_id: UUID, lock: bool = False) -> Pet:
        query = select(PetRecord).where(
            PetRecord.customer_id == customer_id, PetRecord.id == pet_id
        )
        row = self.session.scalar(query.with_for_update() if lock else query)
        if row is None:
            raise BusinessError("NOT_FOUND", 404)
        return pet_value(row)

    def save(self, pet: Pet) -> None:
        self.session.merge(PetRecord(**asdict(pet)))
        self.session.flush()

    def audit(self, actor: UUID, target: UUID, action: str, request_id: str) -> None:
        record(self.session, actor, target, action, request_id)


@contextmanager
def pet_store(engine: Engine) -> Iterator[PetStore]:
    with Session(engine) as session, session.begin():
        yield PostgresPets(session)
