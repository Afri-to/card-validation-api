import pytest

from app.config import Settings

NEON_STYLE = "user:pw@ep-cool-name.us-east-2.aws.neon.tech/cards?sslmode=require"


@pytest.mark.parametrize("scheme", ["postgres://", "postgresql://"])
def test_hosted_database_urls_get_the_psycopg_driver(scheme):
    settings = Settings(database_url=scheme + NEON_STYLE)
    assert settings.database_url == "postgresql+psycopg://" + NEON_STYLE


def test_url_that_already_names_the_driver_is_unchanged():
    url = "postgresql+psycopg://postgres:postgres@localhost:5432/cards"
    assert Settings(database_url=url).database_url == url


def test_query_string_such_as_sslmode_is_kept():
    settings = Settings(database_url="postgresql://" + NEON_STYLE)
    assert settings.database_url.endswith("?sslmode=require")
