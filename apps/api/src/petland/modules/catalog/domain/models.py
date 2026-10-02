from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from petland.modules.pets.public import Size
from petland.shared.domain.errors import BusinessError


@dataclass
class Option:
    size: Size
    price: Decimal
    duration_minutes: int
    buffer_before_minutes: int = 0
    buffer_after_minutes: int = 0


@dataclass
class Service:
    name: str
    description: str
    species_ids: list[str]
    options: list[Option]
    active: bool
    created_at: datetime
    updated_at: datetime
    id: UUID = field(default_factory=uuid4)
    version: int = 1

    def validate(self) -> None:
        if (
            not 2 <= len(self.name.strip()) <= 100
            or len(self.description) > 1500
            or not self.species_ids
            or len(set(self.species_ids)) != len(self.species_ids)
            or not self.options
            or len({o.size for o in self.options}) != len(self.options)
        ):
            raise BusinessError("INVALID_SERVICE", 422)
        for option in self.options:
            if (
                not option.price.is_finite()
                or option.price < 0
                or option.price > Decimal("9999999.99")
                or option.price != option.price.quantize(Decimal("0.01"))
                or not 1 <= option.duration_minutes <= 1440
                or not 0 <= option.buffer_before_minutes <= 240
                or not 0 <= option.buffer_after_minutes <= 240
            ):
                raise BusinessError("INVALID_SERVICE", 422)
