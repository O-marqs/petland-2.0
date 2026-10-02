import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

from petland.bootstrap.app import create_app
from petland.bootstrap.settings import Settings
from petland.modules.identity.application.service import IdentityService
from petland.modules.identity.domain.models import IdentityError, Role
from petland.modules.identity.infrastructure.security import ArgonPasswords, SecureTokens
from petland.modules.identity.infrastructure.store import PostgresUnitOfWork
from petland.shared.database import build_engine

pytestmark = pytest.mark.integration
PASSWORD = "Um passeio feliz pelo jardim 42!"
NEW_PASSWORD = "Outra tarde no parque com Luna 73!"


class Mailbox:
    def __init__(self):
        self.messages = []

    def send(self, email, purpose, token):
        self.messages.append((email, purpose, token))


@pytest.fixture(scope="module")
def identity_engine():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        if os.environ.get("REQUIRE_INTEGRATION") == "1":
            pytest.fail("TEST_DATABASE_URL required")
        pytest.skip("run python scripts/dev.py test")
    assert os.environ.get("APP_ENV") == "test" and make_url(url).database.endswith("_test")
    old = os.environ.get("MIGRATION_DATABASE_URL")
    os.environ["MIGRATION_DATABASE_URL"] = url
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    command.upgrade(config, "head")
    engine = build_engine(url, statement_timeout_ms=10000)
    yield engine
    engine.dispose()
    if old:
        os.environ["MIGRATION_DATABASE_URL"] = old
    else:
        os.environ.pop("MIGRATION_DATABASE_URL", None)


@pytest.fixture
def identity(identity_engine):
    with identity_engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE users, user_roles, sessions, account_tokens, audit_events, identity_rate_limits CASCADE"
            )
        )
    mailbox = Mailbox()
    now = [datetime.now(UTC)]
    service = IdentityService(
        lambda: PostgresUnitOfWork(identity_engine),
        ArgonPasswords(),
        SecureTokens(),
        mailbox,
        lambda: now[0],
    )
    settings = Settings(
        _env_file=None, app_env="test", database_url=os.environ["TEST_DATABASE_URL"]
    )
    with TestClient(
        create_app(settings, identity=service), headers={"Origin": "http://localhost:5173"}
    ) as client:
        yield service, mailbox, now, client


def mutate(client, method, path, body=None, **kwargs):
    csrf = client.get("/api/v1/auth/csrf").json()["csrf_token"]
    return client.request(
        method, "/api/v1" + path, json=body, headers={"X-CSRF-Token": csrf, **kwargs}
    )


def register(service, mailbox, email="cliente@example.com", roles=None):
    service.register(email, "Cliente de teste", PASSWORD, "test")
    service.consume_token(mailbox.messages[-1][2], "verify", None, "test")
    with service.uow() as work:
        user = work.store.user(email=email, lock=True)
        if roles:
            user.roles = frozenset(roles)
            work.store.save_user(user)
        return user


def login(client, email="cliente@example.com", password=PASSWORD):
    response = mutate(client, "POST", "/auth/login", {"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


def test_real_register_verify_login_logout_and_safe_storage(identity, identity_engine):
    service, mailbox, _, client = identity
    body = {"email": "Pessoa@EXAMPLE.COM", "display_name": "Pessoa", "password": PASSWORD}
    result = mutate(client, "POST", "/auth/register", body)
    assert result.status_code == 202
    assert mutate(client, "POST", "/auth/register", body).json() == result.json()
    assert len(mailbox.messages) == 1
    user = login(client, "pessoa@example.com")
    assert user["roles"] == ["CUSTOMER"] and not user["email_verified"]
    token = mailbox.messages[0][2]
    assert mutate(client, "POST", "/auth/email-verifications", {"token": token}).status_code == 200
    assert mutate(client, "POST", "/auth/email-verifications", {"token": token}).status_code == 400
    assert client.get("/api/v1/auth/me").json()["email_verified"]
    raw = client.cookies.get("petland_dev_session")
    with identity_engine.connect() as conn:
        hashed = conn.execute(text("SELECT password_hash FROM users")).scalar_one()
        digests = str(conn.execute(text("SELECT token_digest FROM sessions")).all())
        audit = str(conn.execute(text("SELECT * FROM audit_events")).all())
    assert hashed.startswith("$argon2id$") and service.passwords.verify(hashed, PASSWORD)
    assert raw not in digests and token not in audit and PASSWORD not in audit
    assert mutate(client, "POST", "/auth/logout").status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401
    with pytest.raises(IdentityError):
        service.authenticate(raw)


def test_csrf_origin_login_rotation_and_role_injection(identity):
    service, mailbox, _, client = identity
    register(service, mailbox)
    response = client.get("/api/v1/auth/csrf")
    old = client.cookies.get("petland_dev_session")
    csrf = response.json()["csrf_token"]
    body = {"email": "cliente@example.com", "password": PASSWORD}
    assert client.post("/api/v1/auth/login", json=body).status_code == 403
    assert (
        client.post(
            "/api/v1/auth/login",
            json=body,
            headers={"Origin": "https://evil.example", "X-CSRF-Token": csrf},
        ).status_code
        == 403
    )
    assert (
        client.post("/api/v1/auth/login", json=body, headers={"X-CSRF-Token": csrf}).status_code
        == 200
    )
    assert client.cookies.get("petland_dev_session") != old
    assert client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf}).status_code == 403
    injected = {**body, "display_name": "Pessoa", "roles": ["ADMIN"]}
    assert mutate(client, "POST", "/auth/register", injected).status_code == 422
    assert client.get("/api/v1/management/users").status_code == 403
    assert client.get("/api/v1/auth/logout").status_code == 405


def test_wrong_password_unknown_account_and_reset_requests_are_generic(identity):
    service, mailbox, _, client = identity
    register(service, mailbox)
    responses = [
        mutate(client, "POST", "/auth/login", {"email": email, "password": "wrong"})
        for email in ["cliente@example.com", "unknown@example.com"]
    ]
    assert [response.status_code for response in responses] == [401, 401]
    assert responses[0].json()["detail"] == responses[1].json()["detail"]
    requests = [
        mutate(client, "POST", "/auth/password-reset-requests", {"email": email})
        for email in ["cliente@example.com", "unknown@example.com"]
    ]
    assert requests[0].json() == requests[1].json() and requests[0].status_code == 202
    assert mailbox.messages[-1][1] == "reset"


def test_reset_token_atomic_and_revokes_all_sessions_without_auto_login(identity):
    service, mailbox, _, client = identity
    register(service, mailbox)
    login(client)
    raw = client.cookies.get("petland_dev_session")
    service.request_token("cliente@example.com", "reset", "test")
    token = mailbox.messages[-1][2]

    def consume():
        try:
            service.consume_token(token, "reset", NEW_PASSWORD, "test")
            return 200
        except IdentityError as exc:
            return exc.status

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(lambda _: consume(), range(2))) == [200, 400]
    assert client.get("/api/v1/auth/me").status_code == 401
    with pytest.raises(IdentityError):
        service.authenticate(raw)
    assert (
        mutate(
            client, "POST", "/auth/login", {"email": "cliente@example.com", "password": PASSWORD}
        ).status_code
        == 401
    )
    login(client, password=NEW_PASSWORD)


def test_expiration_and_purpose_mismatch(identity):
    service, mailbox, now, client = identity
    register(service, mailbox)
    login(client)
    service.request_token("cliente@example.com", "reset", "test")
    token = mailbox.messages[-1][2]
    with pytest.raises(IdentityError):
        service.consume_token(token, "verify", None, "test")
    now[0] += timedelta(minutes=31)
    assert client.get("/api/v1/auth/me").status_code == 401
    with pytest.raises(IdentityError):
        service.consume_token(token, "reset", NEW_PASSWORD, "test")


def test_sessions_are_owned_and_revocation_cannot_be_undone_by_stale_touch(identity):
    service, mailbox, _, client = identity
    a = register(service, mailbox)
    b = register(service, mailbox, "b@example.com")
    login(client)
    _, token_b = service.login(b.email, PASSWORD, None, "test")
    _, session_b = service.authenticate(token_b)
    assert mutate(client, "DELETE", f"/auth/sessions/{session_b.id}").status_code == 404
    items = client.get("/api/v1/auth/sessions").json()
    assert len(items) == 1 and items[0]["current"]
    raw = client.cookies.get("petland_dev_session")
    _, stale_session = service.authenticate(raw)
    service.revoke_session(a.id, stale_session.id, "test")
    with service.uow() as work:
        work.store.save_session(stale_session)
    with pytest.raises(IdentityError):
        service.authenticate(raw)


def test_invite_existing_customer_preserves_role_requires_password_and_rotates_access(identity):
    service, mailbox, _, client = identity
    admin = register(service, mailbox, "admin@example.com", {Role.ADMIN})
    customer = register(service, mailbox)
    _, old_session = service.login(customer.email, PASSWORD, None, "test")
    service.invite(admin.id, customer.email, PASSWORD, "test")
    token = mailbox.messages[-1][2]
    with pytest.raises(IdentityError):
        service.accept_invitation(token, "Pessoa", NEW_PASSWORD, "test")
    service.accept_invitation(token, "Pessoa", PASSWORD, "test")
    with pytest.raises(IdentityError):
        service.authenticate(old_session)
    account = login(client)
    assert account["roles"] == ["CUSTOMER", "EMPLOYEE"]
    assert (
        "customer:assist" in account["permissions"]
        and "identity:manage" not in account["permissions"]
    )
    assert client.get("/api/v1/management/users").status_code == 403
    with pytest.raises(IdentityError):
        service.accept_invitation(token, "Pessoa", PASSWORD, "test")


def test_new_employee_and_bootstrap_are_email_controlled_and_one_time(identity):
    service, mailbox, _, client = identity
    service.bootstrap("first@example.com")
    token = mailbox.messages[-1][2]
    assert (
        mutate(
            client,
            "POST",
            "/auth/invitations/accept",
            {"token": token, "display_name": "Admin teste", "password": PASSWORD},
        ).status_code
        == 200
    )
    admin = login(client, "first@example.com")
    assert admin["roles"] == ["ADMIN"] and admin["email_verified"]
    with pytest.raises(IdentityError, match="BOOTSTRAP_CLOSED"):
        service.bootstrap("second@example.com")
    assert (
        mutate(
            client,
            "POST",
            "/management/employee-invitations",
            {"email": "staff@example.com", "current_password": PASSWORD},
        ).status_code
        == 202
    )
    assert mailbox.messages[-1][0:2] == ("staff@example.com", "invite")
    service.accept_invitation(mailbox.messages[-1][2], "Funcionária", PASSWORD, "test")
    staff = login(client, "staff@example.com")
    assert staff["roles"] == ["EMPLOYEE"]
    assert (
        mutate(
            client,
            "POST",
            "/management/employee-invitations",
            {"email": "other@example.com", "current_password": PASSWORD},
        ).status_code
        == 403
    )


def test_admin_role_and_status_changes_reauthenticate_version_and_revoke(identity):
    service, mailbox, _, client = identity
    admin = register(service, mailbox, "admin@example.com", {Role.ADMIN})
    target = register(service, mailbox)
    _, old = service.login(target.email, PASSWORD, None, "test")
    login(client, admin.email)
    body = {
        "roles": ["CUSTOMER", "EMPLOYEE"],
        "expected_version": target.version,
        "current_password": "wrong",
    }
    assert mutate(client, "PUT", f"/management/users/{target.id}/roles", body).status_code == 403
    body["current_password"] = PASSWORD
    assert mutate(client, "PUT", f"/management/users/{target.id}/roles", body).status_code == 204
    assert mutate(client, "PUT", f"/management/users/{target.id}/roles", body).status_code == 409
    with pytest.raises(IdentityError):
        service.authenticate(old)
    listing = client.get("/api/v1/management/users?limit=1").json()
    assert len(listing["items"]) == 1 and listing["has_more"]
    body = {
        "status": "DISABLED",
        "expected_version": target.version + 1,
        "current_password": PASSWORD,
    }
    assert mutate(client, "PATCH", f"/management/users/{target.id}/status", body).status_code == 204
    assert (
        mutate(
            client, "POST", "/auth/login", {"email": target.email, "password": PASSWORD}
        ).status_code
        == 401
    )


def test_last_admin_survives_concurrent_demotion_and_self_disable(identity):
    service, mailbox, _, _ = identity
    a = register(service, mailbox, "a@example.com", {Role.ADMIN})
    b = register(service, mailbox, "b@example.com", {Role.ADMIN})

    def demote(pair):
        actor, target = pair
        try:
            service.manage_user(
                actor.id,
                target.id,
                PASSWORD,
                target.version,
                frozenset({Role.CUSTOMER}),
                None,
                "test",
            )
            return 204
        except IdentityError as exc:
            return exc.status

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(demote, [(a, b), (b, a)])) == [204, 403]
    with service.uow() as work:
        admins = [user for user in work.store.users(0, 10) if Role.ADMIN in user.roles]
        assert work.store.admin_count() == len(admins) == 1
    last = admins[0]
    for roles, status in [(frozenset({Role.CUSTOMER}), None), (None, "DISABLED")]:
        with pytest.raises(IdentityError, match="LAST_ADMIN"):
            service.manage_user(last.id, last.id, PASSWORD, last.version, roles, status, "test")


def test_password_change_revokes_session_and_pending_reset(identity):
    service, mailbox, _, client = identity
    register(service, mailbox)
    login(client)
    service.request_token("cliente@example.com", "reset", "test")
    token = mailbox.messages[-1][2]
    assert (
        mutate(
            client,
            "POST",
            "/me/password-changes",
            {"current_password": PASSWORD, "password": NEW_PASSWORD},
        ).status_code
        == 200
    )
    assert client.get("/api/v1/auth/me").status_code == 401
    with pytest.raises(IdentityError):
        service.consume_token(token, "reset", PASSWORD, "test")


def test_rate_limits_shared_between_service_instances(identity):
    service, _, _, client = identity
    for _ in range(10):
        service.limit("login", "ip-a", "someone@example.com")
    other = IdentityService(
        service.uow, service.passwords, service.tokens, service.mailer, service.clock
    )
    with pytest.raises(IdentityError, match="RATE_LIMITED"):
        other.limit("login", "ip-b", "someone@example.com")
    response = mutate(
        client, "POST", "/auth/login", {"email": "someone@example.com", "password": PASSWORD}
    )
    assert response.status_code == 429 and response.headers["Retry-After"] == "900"


def test_audit_failure_rolls_back_account(identity, identity_engine):
    service, _, _, _ = identity
    with identity_engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE audit_events ADD CONSTRAINT test_reject_audit CHECK (action <> 'account.registered')"
            )
        )
    try:
        with pytest.raises(IntegrityError):
            service.register("rollback@example.com", "Pessoa", PASSWORD, "test")
        with service.uow() as work:
            assert work.store.user(email="rollback@example.com") is None
    finally:
        with identity_engine.begin() as conn:
            conn.execute(text("ALTER TABLE audit_events DROP CONSTRAINT test_reject_audit"))


def test_unverified_admin_can_be_demoted_or_disabled_without_blocking_last_admin(identity):
    service, mailbox, _, _ = identity
    service.bootstrap("admin@example.com")
    service.accept_invitation(mailbox.messages[-1][2], "Admin", PASSWORD, "test")
    service.register("unverified@example.com", "Pendente", PASSWORD, "test")
    with service.uow() as work:
        admin = work.store.user(email="admin@example.com")
        target = work.store.user(email="unverified@example.com")
    service.manage_user(
        admin.id, target.id, PASSWORD, target.version, frozenset({Role.ADMIN}), None, "test"
    )
    service.manage_user(
        admin.id, target.id, PASSWORD, target.version + 1, frozenset({Role.CUSTOMER}), None, "test"
    )
    service.manage_user(
        admin.id, target.id, PASSWORD, target.version + 2, frozenset({Role.ADMIN}), None, "test"
    )
    service.manage_user(admin.id, target.id, PASSWORD, target.version + 3, None, "DISABLED", "test")
    with service.uow() as work:
        assert work.store.admin_count() == 1
        assert work.store.user(user_id=target.id).status == "DISABLED"


def test_https_cookie_and_chunked_body_limit(identity):
    service, _, _, _ = identity
    settings = Settings(
        _env_file=None,
        app_env="production",
        public_origin="https://petland.example",
        smtp_starttls=True,
        database_url="postgresql+psycopg://app:synthetic_long_credential_123456789@db/petland?sslmode=verify-full",
    )
    with TestClient(
        create_app(settings, identity=service), base_url="https://petland.example"
    ) as client:
        response = client.get("/api/v1/auth/csrf")
        cookie = response.headers["set-cookie"]
        assert "__Host-petland_session=" in cookie
        for attribute in ["HttpOnly", "Secure", "SameSite=lax", "Path=/"]:
            assert attribute in cookie
        assert "Domain=" not in cookie
        csrf = response.json()["csrf_token"]
        response = client.post(
            "/api/v1/auth/login",
            content=iter([b"x" * 10000, b"y" * 10000]),
            headers={
                "Origin": "https://petland.example",
                "X-CSRF-Token": csrf,
                "Content-Type": "application/json",
            },
        )
        assert response.status_code == 413 and response.json()["code"] == "BODY_TOO_LARGE"
        assert client.get("/api/docs").status_code == 404
