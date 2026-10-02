from sqlalchemy import select
from sqlalchemy.orm import Session

from petland.modules.pets.domain.models import Size as Size
from petland.modules.pets.infrastructure.models import SpeciesRecord


def species_exist(session: Session, species_ids: list[str]) -> bool:
    found = session.scalars(select(SpeciesRecord.id).where(SpeciesRecord.id.in_(species_ids))).all()
    return len(found) == len(species_ids)
