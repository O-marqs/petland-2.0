from fastapi import FastAPI
from sqlalchemy.engine import Engine

from petland.bootstrap.settings import Settings
from petland.modules.catalog.application.service import Catalog
from petland.modules.catalog.infrastructure.store import catalog_store
from petland.modules.catalog.presentation.http import catalog_router
from petland.modules.customers.application.service import Customers
from petland.modules.customers.infrastructure.store import customer_store
from petland.modules.customers.presentation.http import customer_router
from petland.modules.identity.infrastructure.mail import SmtpMailer
from petland.modules.identity.infrastructure.security import SecureTokens
from petland.modules.identity.public.http import HttpIdentity
from petland.modules.pets.application.service import Pets
from petland.modules.pets.infrastructure.store import pet_store
from petland.modules.pets.presentation.http import pet_router


def include_catalogs(
    app: FastAPI,
    engine: Engine,
    settings: Settings,
    auth: HttpIdentity,
    customers: Customers | None = None,
) -> None:
    mailer = SmtpMailer(
        settings.smtp_host,
        settings.smtp_port,
        settings.smtp_sender,
        settings.public_origin,
        settings.smtp_starttls,
        settings.smtp_username,
        settings.smtp_password.get_secret_value() if settings.smtp_password else None,
    )
    app.include_router(
        customer_router(
            customers or Customers(lambda: customer_store(engine), SecureTokens(), mailer), auth
        )
    )
    app.include_router(pet_router(Pets(lambda: pet_store(engine)), auth))
    app.include_router(catalog_router(Catalog(lambda: catalog_store(engine)), auth))
