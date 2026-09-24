import pytest
from pydantic import ValidationError

from petland.bootstrap.settings import Settings


@pytest.mark.parametrize(
    "url",
    ["sqlite:///test.db", "mysql://root@localhost/legacy", "postgresql+psycopg:///missing-host"],
)
def test_only_explicit_postgres_supported(url):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, database_url=url)


def test_production_rejects_local_configuration():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            app_env="production",
            database_url="postgresql+psycopg://local:weak@db/petland",
        )


def test_secret_not_in_settings_representation():
    config = Settings(
        _env_file=None, database_url="postgresql+psycopg://local:secret_value@db/petland"
    )
    assert "secret_value" not in repr(config)


def test_production_docs_disabled():
    from petland.bootstrap.app import create_app

    config = Settings(
        _env_file=None,
        app_env="production",
        public_origin="https://petland.example",
        database_url="postgresql+psycopg://app:long_test_credential_123456789@db/petland?sslmode=verify-full",
    )
    app = create_app(config)
    assert app.docs_url is None and app.openapi_url is None
