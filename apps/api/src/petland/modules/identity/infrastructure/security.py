import hashlib
import hmac
import secrets
from pathlib import Path

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from petland.modules.identity.domain.models import IdentityError


class ArgonPasswords:
    def __init__(self) -> None:
        self.hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=1)
        self.dummy = self.hasher.hash(secrets.token_urlsafe(32))
        self.common = frozenset(
            Path(__file__)
            .with_name("common_passwords.txt")
            .read_text(encoding="utf-8")
            .splitlines()
        )

    def validate(self, password: str, email: str) -> None:
        lowered = password.casefold()
        if (
            not 15 <= len(password) <= 128
            or len(set(password)) < 5
            or lowered in self.common
            or lowered == email.casefold()
            or lowered in {"passwordpassword", "senhasenhasenha123", "minhasenhamuitosegura"}
        ):
            raise IdentityError("WEAK_PASSWORD", 422)

    def hash(self, password: str) -> str:
        return self.hasher.hash(password)

    def verify(self, hashed: str, password: str) -> bool:
        try:
            return self.hasher.verify(hashed, password)
        except (VerificationError, InvalidHashError):
            return False

    def needs_rehash(self, hashed: str) -> bool:
        return self.hasher.check_needs_rehash(hashed)

    def dummy_verify(self, password: str) -> None:
        self.verify(self.dummy, password)


class SecureTokens:
    def new(self) -> str:
        return secrets.token_urlsafe(32)

    def digest(self, value: str) -> str:
        return hashlib.sha256(value.encode()).hexdigest()

    def csrf(self, session_token: str) -> str:
        return hmac.new(session_token.encode(), b"petland.csrf.v1", hashlib.sha256).hexdigest()

    def equal(self, left: str, right: str) -> bool:
        return hmac.compare_digest(left.encode(), right.encode())
