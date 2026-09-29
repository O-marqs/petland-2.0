from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from petland.shared.domain.errors import BusinessError


class Role(StrEnum):
    CUSTOMER = "CUSTOMER"
    EMPLOYEE = "EMPLOYEE"
    ADMIN = "ADMIN"


ROLE_PERMISSIONS: dict[Role, frozenset[str]] = {
    Role.CUSTOMER: frozenset({"account:self", "customer:own"}),
    Role.EMPLOYEE: frozenset(
        {
            "account:self",
            "operation:read",
            "attendance:execute",
            "customer:assist",
            "booking:assist",
            "notes:internal",
            "catalog:manage",
            "establishment:manage",
        }
    ),
    Role.ADMIN: frozenset(
        {
            "account:self",
            "operation:read",
            "attendance:execute",
            "customer:assist",
            "booking:assist",
            "notes:internal",
            "identity:manage",
            "catalog:manage",
            "establishment:manage",
        }
    ),
}


class IdentityError(BusinessError):
    pass


@dataclass
class User:
    email: str
    display_name: str
    password_hash: str
    roles: frozenset[Role]
    created_at: datetime
    id: UUID = field(default_factory=uuid4)
    status: str = "ACTIVE"
    verified_at: datetime | None = None
    version: int = 1

    @property
    def permissions(self) -> list[str]:
        return sorted({permission for role in self.roles for permission in ROLE_PERMISSIONS[role]})

    def require(self, permission: str) -> None:
        if self.status != "ACTIVE":
            raise IdentityError("AUTH_REQUIRED", 401)
        if self.verified_at is None:
            raise IdentityError("EMAIL_NOT_VERIFIED", 403)
        if permission not in self.permissions:
            raise IdentityError("FORBIDDEN", 403)

    def change_roles(self, roles: frozenset[Role], active_admins: int) -> None:
        if not roles:
            raise IdentityError("ROLES_REQUIRED", 422)
        if (
            Role.ADMIN in self.roles
            and Role.ADMIN not in roles
            and self.status == "ACTIVE"
            and self.verified_at is not None
            and active_admins <= 1
        ):
            raise IdentityError("LAST_ADMIN", 409)
        self.roles = roles
        self.version += 1


@dataclass
class Session:
    token_digest: str
    created_at: datetime
    last_seen_at: datetime
    expires_at: datetime
    idle_expires_at: datetime
    user_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)
    revoked_at: datetime | None = None

    def valid(self, now: datetime) -> bool:
        return self.revoked_at is None and now < min(self.expires_at, self.idle_expires_at)


@dataclass
class AccountToken:
    purpose: str
    token_digest: str
    email: str
    expires_at: datetime
    created_at: datetime
    user_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)
    used_at: datetime | None = None

    def consume(self, purpose: str, now: datetime) -> None:
        if self.purpose != purpose or self.used_at is not None or now >= self.expires_at:
            raise IdentityError("INVALID_TOKEN", 400)
        self.used_at = now
