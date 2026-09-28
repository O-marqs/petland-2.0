import hashlib
from datetime import datetime
from types import TracebackType
from typing import Self
from uuid import UUID, uuid4

from sqlalchemy import delete, func, select, text, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session as DatabaseSession

from petland.modules.identity.domain.models import AccountToken, Role, Session, User
from petland.modules.identity.infrastructure.models import (
    AuditRecord,
    LimitRecord,
    RoleRecord,
    SessionRecord,
    TokenRecord,
    UserRecord,
)


class PostgresIdentityStore:
    def __init__(self, session: DatabaseSession) -> None:
        self.db = session

    def _user(self, row: UserRecord) -> User:
        roles = self.db.scalars(select(RoleRecord.role).where(RoleRecord.user_id == row.id)).all()
        return User(
            row.email,
            row.display_name,
            row.password_hash,
            frozenset(Role(role) for role in roles),
            row.created_at,
            row.id,
            row.status,
            row.email_verified_at,
            row.version,
        )

    def user(
        self, *, user_id: UUID | None = None, email: str | None = None, lock: bool = False
    ) -> User | None:
        if user_id is None and email is None:
            return None
        if lock and email is not None:
            key = int.from_bytes(hashlib.sha256(email.encode()).digest()[:8], signed=True)
            self.db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})
        query = (
            select(UserRecord).where(UserRecord.id == user_id)
            if user_id
            else select(UserRecord).where(UserRecord.normalized_email == email)
        )
        row = self.db.scalar(query.with_for_update() if lock else query)
        return self._user(row) if row else None

    def save_user(self, user: User) -> None:
        self.db.merge(
            UserRecord(
                id=user.id,
                email=user.email,
                normalized_email=user.email.casefold(),
                display_name=user.display_name,
                password_hash=user.password_hash,
                status=user.status,
                email_verified_at=user.verified_at,
                created_at=user.created_at,
                version=user.version,
            )
        )
        self.db.flush()
        self.db.execute(delete(RoleRecord).where(RoleRecord.user_id == user.id))
        self.db.add_all(RoleRecord(user_id=user.id, role=role.value) for role in sorted(user.roles))
        self.db.flush()

    def users(self, offset: int, limit: int) -> list[User]:
        return [
            self._user(row)
            for row in self.db.scalars(
                select(UserRecord)
                .order_by(UserRecord.created_at, UserRecord.id)
                .offset(offset)
                .limit(limit)
            )
        ]

    def admin_count(self) -> int:
        return (
            self.db.scalar(
                select(func.count())
                .select_from(UserRecord)
                .join(RoleRecord)
                .where(
                    UserRecord.status == "ACTIVE",
                    RoleRecord.role == "ADMIN",
                    UserRecord.email_verified_at.is_not(None),
                )
            )
            or 0
        )

    def lock_administration(self) -> None:
        self.db.execute(text("SELECT pg_advisory_xact_lock(726381920341)"))

    @staticmethod
    def _session(row: SessionRecord) -> Session:
        return Session(
            row.token_digest,
            row.created_at,
            row.last_seen_at,
            row.expires_at,
            row.idle_expires_at,
            row.user_id,
            row.id,
            row.revoked_at,
        )

    def session(self, digest: str) -> Session | None:
        row = self.db.scalar(select(SessionRecord).where(SessionRecord.token_digest == digest))
        return self._session(row) if row else None

    def sessions(self, user_id: UUID) -> list[Session]:
        return [
            self._session(row)
            for row in self.db.scalars(
                select(SessionRecord)
                .where(SessionRecord.user_id == user_id)
                .order_by(SessionRecord.created_at.desc())
            )
        ]

    def save_session(self, session: Session) -> None:
        stmt = insert(SessionRecord).values(
            id=session.id,
            user_id=session.user_id,
            token_digest=session.token_digest,
            created_at=session.created_at,
            last_seen_at=session.last_seen_at,
            expires_at=session.expires_at,
            idle_expires_at=session.idle_expires_at,
            revoked_at=session.revoked_at,
        )
        # A request touching activity cannot resurrect a concurrently revoked session.
        self.db.execute(
            stmt.on_conflict_do_update(
                index_elements=[SessionRecord.id],
                set_={
                    "last_seen_at": func.greatest(SessionRecord.last_seen_at, session.last_seen_at),
                    "idle_expires_at": func.greatest(
                        SessionRecord.idle_expires_at, session.idle_expires_at
                    ),
                    "revoked_at": func.coalesce(SessionRecord.revoked_at, session.revoked_at),
                },
            )
        )

    def revoke_sessions(self, user_id: UUID, now: datetime) -> None:
        self.db.execute(
            update(SessionRecord)
            .where(SessionRecord.user_id == user_id, SessionRecord.revoked_at.is_(None))
            .values(revoked_at=now)
        )

    def token(self, digest: str) -> AccountToken | None:
        # Match user -> token ordering used by reissue/password change to avoid lock cycles.
        owner_id = self.db.scalar(
            select(TokenRecord.user_id).where(TokenRecord.token_digest == digest)
        )
        if owner_id is not None:
            self.db.scalar(select(UserRecord.id).where(UserRecord.id == owner_id).with_for_update())
        row = self.db.scalar(
            select(TokenRecord).where(TokenRecord.token_digest == digest).with_for_update()
        )
        return (
            AccountToken(
                row.purpose,
                row.token_digest,
                row.email,
                row.expires_at,
                row.created_at,
                row.user_id,
                row.id,
                row.used_at,
            )
            if row
            else None
        )

    def save_token(self, token: AccountToken) -> None:
        self.db.merge(
            TokenRecord(
                id=token.id,
                user_id=token.user_id,
                email=token.email,
                purpose=token.purpose,
                token_digest=token.token_digest,
                created_at=token.created_at,
                expires_at=token.expires_at,
                used_at=token.used_at,
            )
        )
        self.db.flush()

    def invalidate_tokens(self, user_id: UUID, purpose: str, now: datetime) -> None:
        self.db.execute(
            update(TokenRecord)
            .where(
                TokenRecord.user_id == user_id,
                TokenRecord.purpose == purpose,
                TokenRecord.used_at.is_(None),
            )
            .values(used_at=now)
        )

    def audit(
        self,
        action: str,
        actor: UUID | None,
        target: UUID | None,
        now: datetime,
        request_id: str,
        result: str = "success",
    ) -> None:
        self.db.add(
            AuditRecord(
                id=uuid4(),
                actor_user_id=actor,
                target_id=target,
                action=action,
                occurred_at=now,
                request_id=request_id,
                result=result,
            )
        )

    def hit_limit(self, key: str, window: int) -> int:
        stmt = insert(LimitRecord).values(key=key, window=window, count=1)
        return int(
            self.db.execute(
                stmt.on_conflict_do_update(
                    index_elements=[LimitRecord.key, LimitRecord.window],
                    set_={"count": LimitRecord.count + 1},
                ).returning(LimitRecord.count)
            ).scalar_one()
        )

    def prune(self, before: datetime) -> None:
        self.db.execute(delete(SessionRecord).where(SessionRecord.expires_at < before))
        self.db.execute(delete(TokenRecord).where(TokenRecord.expires_at < before))
        self.db.execute(
            delete(LimitRecord).where(LimitRecord.window < int(before.timestamp()) // 900)
        )


class PostgresUnitOfWork:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def __enter__(self) -> Self:
        self.db = DatabaseSession(self.engine, expire_on_commit=False)
        self.store = PostgresIdentityStore(self.db)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            if exc_type:
                self.db.rollback()
            else:
                self.db.commit()
        finally:
            self.db.close()
