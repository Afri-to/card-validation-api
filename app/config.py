"""Settings read from environment variables (or a local .env file)."""

from decimal import Decimal
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/cards"

    # Secret used to fingerprint card numbers for duplicate detection.
    # The default is for local development only; set a real one in production.
    card_fingerprint_key: str = "dev-only-change-me"

    # Mock "credit limit": larger amounts are recorded as declined.
    max_approved_amount: Decimal = Decimal("10000.00")

    # Same card, amount and currency within this window is flagged as a duplicate.
    duplicate_window_seconds: int = 60

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, url: str) -> str:
        """Hosts like Neon and Render hand out postgres:// or postgresql:// URLs.

        SQLAlchemy needs the driver named explicitly (postgresql+psycopg://),
        so rewrite the scheme instead of making people edit the URL by hand.
        """
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url[len(prefix) :]
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
