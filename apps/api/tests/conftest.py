import pytest

from petland.bootstrap.settings import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,
        app_env="test",
        database_url="postgresql+psycopg://unused@127.0.0.1:1/petland_test",
    )
