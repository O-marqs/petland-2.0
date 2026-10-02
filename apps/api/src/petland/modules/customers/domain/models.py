from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from petland.shared.domain.errors import BusinessError


@dataclass
class Customer:
    name: str
    email: str
    phone: str
    address: str
    created_at: datetime
    updated_at: datetime
    user_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)
    version: int = 1

    def edit(
        self, name: str, email: str, phone: str, address: str, version: int, now: datetime
    ) -> None:
        if version != self.version:
            raise BusinessError("STALE_VERSION", 409)
        if self.user_id and email != self.email:
            raise BusinessError("LINKED_EMAIL", 409)
        self.name, self.email, self.phone, self.address = name, email, phone, address
        self.updated_at, self.version = now, self.version + 1


@dataclass
class Claim:
    customer_id: UUID
    email: str
    digest: str
    expires_at: datetime
    id: UUID = field(default_factory=uuid4)
    used_at: datetime | None = None
