"""Database engine, session factory and the FastAPI dependency that hands out sessions."""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


# create_engine does not connect yet; the first query does.
engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """One session per request, always closed afterwards."""
    with SessionLocal() as session:
        yield session


def init_db() -> None:
    """Create tables that don't exist yet."""
    from app import models  # noqa: F401  (registers the tables on Base)

    Base.metadata.create_all(engine)
