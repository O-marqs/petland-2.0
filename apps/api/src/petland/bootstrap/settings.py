from typing import Literal, Self
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)
    app_env: Literal["development", "test", "staging", "production"] = "development"
    database_url: SecretStr
    public_origin: str = "http://localhost:5173"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    smtp_host: str = "127.0.0.1"
    smtp_port: int = Field(default=1025, ge=1, le=65535)
    smtp_sender: str = "PetLand <acesso@petland.local>"
    smtp_starttls: bool = False
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    db_connect_timeout: int = Field(default=3, ge=1, le=10)
    db_statement_timeout_ms: int = Field(default=2000, ge=100, le=10000)

    @model_validator(mode="after")
    def validate_configuration(self) -> Self:
        origin = urlsplit(self.public_origin)
        if (
            origin.scheme not in {"http", "https"}
            or not origin.hostname
            or origin.username
            or origin.password
            or origin.path
            or origin.query
            or origin.fragment
        ):
            raise ValueError("PUBLIC_ORIGIN must be an exact HTTP(S) origin without a path")
        try:
            url = make_url(self.database_url.get_secret_value())
        except Exception:
            raise ValueError("DATABASE_URL must be a valid PostgreSQL URL") from None
        if url.drivername != "postgresql+psycopg" or not url.host or not url.database:
            raise ValueError("DATABASE_URL must use postgresql+psycopg with host and database")
        if self.app_env in {"staging", "production"}:
            if not self.smtp_starttls:
                raise ValueError("SMTP requires STARTTLS outside local development")
            if not self.public_origin.startswith("https://"):
                raise ValueError("HTTPS is required outside local development")
            if url.query.get("sslmode") != "verify-full":
                raise ValueError("DATABASE_URL requires sslmode=verify-full outside development")
            if not url.password or len(url.password) < 24:
                raise ValueError("A strong externally managed database credential is required")
        return self
