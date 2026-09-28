from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator

from petland.modules.identity.domain.models import Role, User


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class EmailInput(InputModel):
    email: EmailStr = Field(max_length=254)

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.casefold()


class LoginInput(EmailInput):
    password: SecretStr = Field(min_length=1, max_length=128)


class RegisterInput(LoginInput):
    display_name: str = Field(min_length=2, max_length=100, pattern=r".*\S.*")

    @field_validator("display_name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip()


class TokenInput(InputModel):
    token: SecretStr = Field(min_length=43, max_length=128)


class ResetInput(TokenInput):
    password: SecretStr = Field(min_length=15, max_length=128)


class InvitationInput(ResetInput):
    display_name: str = Field(min_length=2, max_length=100, pattern=r".*\S.*")


class ReauthenticationInput(InputModel):
    current_password: SecretStr = Field(min_length=1, max_length=128)


class ChangePasswordInput(ReauthenticationInput):
    password: SecretStr = Field(min_length=15, max_length=128)


class InviteEmployeeInput(EmailInput, ReauthenticationInput):
    pass


class RolesInput(ReauthenticationInput):
    roles: list[Role] = Field(min_length=1, max_length=3)
    expected_version: int = Field(ge=1)


class StatusInput(ReauthenticationInput):
    status: Literal["ACTIVE", "DISABLED"]
    expected_version: int = Field(ge=1)


class Message(BaseModel):
    message: str


class CsrfResponse(BaseModel):
    csrf_token: str


class AccountResponse(BaseModel):
    id: UUID
    email: str
    display_name: str
    roles: list[Role]
    permissions: list[str]
    email_verified: bool
    status: str
    version: int

    @classmethod
    def from_user(cls, user: User) -> "AccountResponse":
        return cls(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            roles=sorted(user.roles),
            permissions=user.permissions if user.verified_at else ["account:self"],
            email_verified=user.verified_at is not None,
            status=user.status,
            version=user.version,
        )


class SessionResponse(BaseModel):
    id: UUID
    created_at: datetime
    last_seen_at: datetime
    expires_at: datetime
    current: bool


class UsersResponse(BaseModel):
    items: list[AccountResponse]
    offset: int
    limit: int
    has_more: bool
