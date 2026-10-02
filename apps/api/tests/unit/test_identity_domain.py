from datetime import UTC, datetime, timedelta

import pytest

from petland.modules.identity.domain.models import AccountToken, IdentityError, Role, Session, User
from petland.modules.identity.infrastructure.security import ArgonPasswords, SecureTokens

NOW = datetime(2026, 9, 24, tzinfo=UTC)


def test_permissions_deny_by_default_and_never_publish_internal_notes():
    customer = User(
        "customer@example.com", "Cliente", "hash", frozenset({Role.CUSTOMER}), NOW, verified_at=NOW
    )
    assert "notes:internal" not in customer.permissions
    with pytest.raises(IdentityError, match="FORBIDDEN"):
        customer.require("identity:manage")
    employee = User(
        "employee@example.com", "Equipe", "hash", frozenset({Role.EMPLOYEE}), NOW, verified_at=NOW
    )
    employee.require("customer:assist")
    employee.require("booking:assist")
    assert not any("cancel" in permission for permission in employee.permissions)
    with pytest.raises(IdentityError):
        employee.require("identity:manage")


def test_unverified_or_disabled_identity_cannot_use_privileged_permissions():
    admin = User("admin@example.com", "Admin", "hash", frozenset({Role.ADMIN}), NOW)
    with pytest.raises(IdentityError, match="EMAIL_NOT_VERIFIED"):
        admin.require("identity:manage")
    admin.verified_at = NOW
    admin.status = "DISABLED"
    with pytest.raises(IdentityError, match="AUTH_REQUIRED"):
        admin.require("identity:manage")


def test_expiration_boundaries_and_revocation():
    session = Session("digest", NOW, NOW, NOW + timedelta(hours=8), NOW + timedelta(minutes=30))
    assert session.valid(NOW + timedelta(minutes=29))
    assert not session.valid(NOW + timedelta(minutes=30))
    session.idle_expires_at = NOW + timedelta(hours=9)
    assert not session.valid(NOW + timedelta(hours=8))
    session.revoked_at = NOW
    assert not session.valid(NOW)
    token = AccountToken("reset", "digest", "a@example.com", NOW, NOW)
    with pytest.raises(IdentityError, match="INVALID_TOKEN"):
        token.consume("reset", NOW)


def test_tokens_are_random_and_csrf_bound_to_cookie_secret():
    tokens = SecureTokens()
    a, b = tokens.new(), tokens.new()
    assert len(a) >= 43 and a != b
    assert tokens.csrf(a) != tokens.csrf(b) and tokens.csrf(a) != a
    assert len(tokens.digest(a)) == 64


def test_password_policy_spaces_long_passwords_and_local_blocklist():
    passwords = ArgonPasswords()
    accepted = "  Uma frase longa e particular para testes 2026  "
    passwords.validate(accepted, "a@example.com")
    hashed = passwords.hash(accepted)
    assert passwords.verify(hashed, accepted)
    assert not passwords.verify(hashed, accepted.strip())
    for invalid in ["short", "x" * 128, "passwordpassword", "x" * 129]:
        with pytest.raises(IdentityError, match="WEAK_PASSWORD"):
            passwords.validate(invalid, "a@example.com")


def test_smtp_failure_is_observable_without_leaking_recipient_or_token(monkeypatch, caplog):
    import logging
    import smtplib

    from petland.modules.identity.infrastructure.mail import SmtpMailer

    def failed(*args, **kwargs):
        raise OSError("SENSITIVE_TOKEN")

    monkeypatch.setattr(smtplib, "SMTP", failed)
    logger = logging.getLogger("petland")
    logger.addHandler(caplog.handler)
    try:
        SmtpMailer("127.0.0.1", 1025, "demo@example.com", "http://localhost:5173").send(
            "private@example.com", "reset", "SENSITIVE_TOKEN"
        )
    finally:
        logger.removeHandler(caplog.handler)
    assert "identity_mail_delivery_failed" in caplog.text
    assert "SENSITIVE_TOKEN" not in caplog.text and "private@example.com" not in caplog.text
