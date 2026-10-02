from sqlalchemy.engine import Engine

from petland.bootstrap.settings import Settings
from petland.modules.identity.application.service import IdentityService
from petland.modules.identity.infrastructure.mail import SmtpMailer
from petland.modules.identity.infrastructure.security import ArgonPasswords, SecureTokens
from petland.modules.identity.infrastructure.store import PostgresUnitOfWork


def build_identity(engine: Engine, settings: Settings) -> IdentityService:
    return IdentityService(
        lambda: PostgresUnitOfWork(engine),
        ArgonPasswords(),
        SecureTokens(),
        SmtpMailer(
            settings.smtp_host,
            settings.smtp_port,
            settings.smtp_sender,
            settings.public_origin,
            settings.smtp_starttls,
            settings.smtp_username,
            settings.smtp_password.get_secret_value() if settings.smtp_password else None,
        ),
    )
