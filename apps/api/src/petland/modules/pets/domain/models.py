from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from petland.shared.domain.errors import BusinessError


class Size(StrEnum):
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"


class Sex(StrEnum):
    UNKNOWN = "UNKNOWN"
    FEMALE = "FEMALE"
    MALE = "MALE"


@dataclass
class Species:
    id: str
    name: str


@dataclass
class Breed:
    id: UUID
    species_id: str
    name: str


@dataclass
class Pet:
    customer_id: UUID
    name: str
    species_id: str
    breed_id: UUID | None
    size: Size
    sex: Sex
    birth_date: date | None
    birth_estimated: bool
    care_notes: str
    created_at: datetime
    updated_at: datetime
    id: UUID = field(default_factory=uuid4)
    archived_at: datetime | None = None
    version: int = 1

    def validate(self, today: date) -> None:
        if (
            not 1 <= len(self.name.strip()) <= 80
            or len(self.care_notes) > 1000
            or (self.birth_date is not None and self.birth_date > today)
            or (self.birth_estimated and self.birth_date is None)
        ):
            raise BusinessError("INVALID_PET", 422)
