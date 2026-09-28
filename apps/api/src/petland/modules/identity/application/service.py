from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID

from petland.modules.identity.application.ports import Mailer, Passwords, Tokens, UnitOfWork
from petland.modules.identity.domain.models import AccountToken, IdentityError, Role, Session, User


class IdentityService:
    """Identity use cases; transactions and adapters are supplied by the composition root."""

    def __init__(
        self,
        uow: Callable[[], UnitOfWork],
        passwords: Passwords,
        tokens: Tokens,
        mailer: Mailer,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.uow = uow
        self.passwords = passwords
        self.tokens = tokens
        self.mailer = mailer
        self.clock = clock

    def limit(self, operation: str, ip: str, identifier: str = "", maximum: int = 10) -> None:
        window = int(self.clock().timestamp()) // 900
        with self.uow() as work:
            counts = [work.store.hit_limit(self.tokens.digest(f"{operation}:ip:{ip}"), window)]
            if identifier:
                counts.append(
                    work.store.hit_limit(
                        self.tokens.digest(f"{operation}:id:{identifier.casefold()}"), window
                    )
                )
        if counts[0] > maximum * 5 or (len(counts) > 1 and counts[1] > maximum):
            raise IdentityError("RATE_LIMITED", 429)

    def _session(self, user_id: UUID | None = None) -> tuple[str, Session]:
        now = self.clock()
        raw = self.tokens.new()
        return raw, Session(
            self.tokens.digest(raw),
            now,
            now,
            now + timedelta(hours=8 if user_id else 1),
            now + timedelta(minutes=30),
            user_id,
        )

    def csrf(self, raw: str | None) -> tuple[str, str]:
        with self.uow() as work:
            session = work.store.session(self.tokens.digest(raw)) if raw else None
            if not session or not session.valid(self.clock()):
                raw, session = self._session()
                work.store.save_session(session)
        assert raw is not None
        return raw, self.tokens.csrf(raw)

    def verify_csrf(self, raw: str | None, csrf: str) -> None:
        if not raw or not self.tokens.equal(self.tokens.csrf(raw), csrf):
            raise IdentityError("CSRF_REJECTED", 403)
        with self.uow() as work:
            session = work.store.session(self.tokens.digest(raw))
            if not session or not session.valid(self.clock()):
                raise IdentityError("CSRF_REJECTED", 403)

    def authenticate(self, raw: str | None) -> tuple[User, Session]:
        now = self.clock()
        with self.uow() as work:
            session = work.store.session(self.tokens.digest(raw)) if raw else None
            if not session or not session.valid(now) or session.user_id is None:
                raise IdentityError("AUTH_REQUIRED", 401)
            user = work.store.user(user_id=session.user_id)
            if not user or user.status != "ACTIVE":
                raise IdentityError("AUTH_REQUIRED", 401)
            session.last_seen_at = now
            session.idle_expires_at = min(session.expires_at, now + timedelta(minutes=30))
            work.store.save_session(session)
        return user, session

    def register(self, email: str, display_name: str, password: str, request_id: str) -> None:
        self.passwords.validate(password, email)
        hashed = self.passwords.hash(password)
        raw = self.tokens.new()
        now = self.clock()
        with self.uow() as work:
            # Serializes only the normalized address, including concurrent signups/invitations.
            existing = work.store.user(email=email, lock=True)
            if existing:
                return
            user = User(email, display_name, hashed, frozenset({Role.CUSTOMER}), now)
            work.store.save_user(user)
            work.store.save_token(
                AccountToken(
                    "verify",
                    self.tokens.digest(raw),
                    email,
                    now + timedelta(hours=24),
                    now,
                    user.id,
                )
            )
            work.store.audit("account.registered", user.id, user.id, now, request_id)
        self.mailer.send(email, "verify", raw)

    def login(
        self, email: str, password: str, previous: str | None, request_id: str
    ) -> tuple[User, str]:
        now = self.clock()
        with self.uow() as work:
            user = work.store.user(email=email, lock=True)
            if user is None:
                self.passwords.dummy_verify(password)
                raise IdentityError("INVALID_CREDENTIALS", 401)
            if not self.passwords.verify(user.password_hash, password) or user.status != "ACTIVE":
                raise IdentityError("INVALID_CREDENTIALS", 401)
            if self.passwords.needs_rehash(user.password_hash):
                user.password_hash = self.passwords.hash(password)
                work.store.save_user(user)
            old = work.store.session(self.tokens.digest(previous)) if previous else None
            if old:
                old.revoked_at = now
                work.store.save_session(old)
            raw, session = self._session(user.id)
            work.store.save_session(session)
            work.store.audit("session.started", user.id, session.id, now, request_id)
        return user, raw

    def logout(self, raw: str | None, request_id: str) -> None:
        with self.uow() as work:
            session = work.store.session(self.tokens.digest(raw)) if raw else None
            if session:
                session.revoked_at = self.clock()
                work.store.save_session(session)
                work.store.audit(
                    "session.revoked", session.user_id, session.id, self.clock(), request_id
                )

    def request_token(self, email: str, purpose: str, request_id: str) -> None:
        raw = self.tokens.new()
        now = self.clock()
        with self.uow() as work:
            user = work.store.user(email=email, lock=True)
            if (
                not user
                or user.status != "ACTIVE"
                or (purpose == "verify" and user.verified_at is not None)
            ):
                return
            work.store.invalidate_tokens(user.id, purpose, now)
            ttl = timedelta(minutes=30) if purpose == "reset" else timedelta(hours=24)
            work.store.save_token(
                AccountToken(purpose, self.tokens.digest(raw), email, now + ttl, now, user.id)
            )
            work.store.audit(f"account.{purpose}_requested", None, user.id, now, request_id)
        self.mailer.send(email, purpose, raw)

    def consume_token(self, raw: str, purpose: str, password: str | None, request_id: str) -> None:
        now = self.clock()
        with self.uow() as work:
            token = work.store.token(self.tokens.digest(raw))
            if token is None:
                raise IdentityError("INVALID_TOKEN")
            token.consume(purpose, now)
            user = work.store.user(user_id=token.user_id, lock=True)
            if user is None or user.status != "ACTIVE":
                raise IdentityError("INVALID_TOKEN")
            if purpose == "reset":
                assert password is not None
                self.passwords.validate(password, user.email)
                user.password_hash = self.passwords.hash(password)
                work.store.revoke_sessions(user.id, now)
                work.store.invalidate_tokens(user.id, "reset", now)
            else:
                user.verified_at = now
            user.version += 1
            work.store.save_user(user)
            work.store.save_token(token)
            work.store.audit(f"account.{purpose}_completed", user.id, user.id, now, request_id)

    def list_sessions(self, user_id: UUID) -> list[Session]:
        with self.uow() as work:
            return [
                session for session in work.store.sessions(user_id) if session.valid(self.clock())
            ]

    def revoke_session(self, user_id: UUID, session_id: UUID, request_id: str) -> None:
        with self.uow() as work:
            session = next(
                (item for item in work.store.sessions(user_id) if item.id == session_id), None
            )
            if not session:
                raise IdentityError("NOT_FOUND", 404)
            session.revoked_at = self.clock()
            work.store.save_session(session)
            work.store.audit("session.revoked", user_id, session_id, self.clock(), request_id)

    def change_password(self, user_id: UUID, current: str, password: str, request_id: str) -> None:
        now = self.clock()
        with self.uow() as work:
            user = self._active_user(work, user_id)
            self._reauthenticate(user, current)
            self.passwords.validate(password, user.email)
            user.password_hash = self.passwords.hash(password)
            user.version += 1
            work.store.save_user(user)
            work.store.revoke_sessions(user.id, now)
            work.store.invalidate_tokens(user.id, "reset", now)
            work.store.audit("account.password_changed", user.id, user.id, now, request_id)

    def _active_user(self, work: UnitOfWork, user_id: UUID) -> User:
        user = work.store.user(user_id=user_id, lock=True)
        if not user or user.status != "ACTIVE":
            raise IdentityError("AUTH_REQUIRED", 401)
        return user

    def _reauthenticate(self, user: User, password: str) -> None:
        if not self.passwords.verify(user.password_hash, password):
            raise IdentityError("REAUTHENTICATION_FAILED", 403)

    def invite(self, actor_id: UUID, email: str, password: str, request_id: str) -> None:
        now = self.clock()
        raw = self.tokens.new()
        with self.uow() as work:
            work.store.lock_administration()
            actor = self._active_user(work, actor_id)
            actor.require("identity:manage")
            self._reauthenticate(actor, password)
            work.store.save_token(
                AccountToken(
                    "invite", self.tokens.digest(raw), email, now + timedelta(hours=24), now
                )
            )
            work.store.audit("employee.invited", actor_id, None, now, request_id)
        self.mailer.send(email, "invite", raw)

    def accept_invitation(
        self, raw: str, display_name: str, password: str, request_id: str
    ) -> None:
        now = self.clock()
        with self.uow() as work:
            work.store.lock_administration()
            token = work.store.token(self.tokens.digest(raw))
            if not token or token.purpose not in {"invite", "bootstrap"}:
                raise IdentityError("INVALID_TOKEN")
            token.consume(token.purpose, now)
            if token.purpose == "bootstrap" and work.store.admin_count() > 0:
                raise IdentityError("BOOTSTRAP_CLOSED", 409)
            role = Role.ADMIN if token.purpose == "bootstrap" else Role.EMPLOYEE
            user = work.store.user(email=token.email, lock=True)
            if user:
                self._reauthenticate(user, password)
                if user.status != "ACTIVE":
                    raise IdentityError("INVALID_TOKEN")
                user.roles = user.roles | {role}
                user.version += 1
            else:
                self.passwords.validate(password, token.email)
                user = User(
                    token.email, display_name, self.passwords.hash(password), frozenset({role}), now
                )
            user.verified_at = now
            work.store.save_user(user)
            work.store.revoke_sessions(user.id, now)
            work.store.save_token(token)
            work.store.audit("invitation.accepted", user.id, user.id, now, request_id)

    def list_users(self, actor_id: UUID, offset: int, limit: int) -> list[User]:
        with self.uow() as work:
            actor = self._active_user(work, actor_id)
            actor.require("identity:manage")
            return work.store.users(offset, limit)

    def manage_user(
        self,
        actor_id: UUID,
        target_id: UUID,
        password: str,
        version: int,
        roles: frozenset[Role] | None,
        status: str | None,
        request_id: str,
    ) -> None:
        now = self.clock()
        with self.uow() as work:
            # A shared transaction lock serializes the invariant across administrators/instances.
            work.store.lock_administration()
            actor = self._active_user(work, actor_id)
            actor.require("identity:manage")
            self._reauthenticate(actor, password)
            target = work.store.user(user_id=target_id, lock=True)
            if not target:
                raise IdentityError("NOT_FOUND", 404)
            if target.version != version:
                raise IdentityError("STALE_VERSION", 409)
            if roles is not None:
                target.change_roles(roles, work.store.admin_count())
            if status is not None:
                if (
                    status == "DISABLED"
                    and target.status == "ACTIVE"
                    and Role.ADMIN in target.roles
                    and target.verified_at is not None
                    and work.store.admin_count() <= 1
                ):
                    raise IdentityError("LAST_ADMIN", 409)
                target.status = status
                target.version += 1
            work.store.save_user(target)
            work.store.revoke_sessions(target.id, now)
            work.store.audit(
                "identity.roles_changed" if roles is not None else "identity.status_changed",
                actor_id,
                target.id,
                now,
                request_id,
            )

    def bootstrap(self, email: str) -> None:
        now = self.clock()
        raw = self.tokens.new()
        with self.uow() as work:
            work.store.lock_administration()
            if work.store.admin_count() > 0:
                raise IdentityError("BOOTSTRAP_CLOSED", 409)
            work.store.save_token(
                AccountToken(
                    "bootstrap", self.tokens.digest(raw), email, now + timedelta(minutes=30), now
                )
            )
            work.store.audit("admin.bootstrap_requested", None, None, now, "operator-cli")
        self.mailer.send(email, "bootstrap", raw)
