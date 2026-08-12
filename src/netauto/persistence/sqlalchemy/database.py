"""SQLAlchemy engine construction for the supported PostgreSQL runtime."""

from sqlalchemy import Engine
from sqlalchemy.engine import create_engine, make_url


def create_database_engine(database_url: str) -> Engine:
    """Create a lazy SQLAlchemy engine for a supported PostgreSQL URL."""

    url = make_url(database_url)
    if url.get_backend_name() != "postgresql" or url.get_driver_name() != "psycopg":
        raise RuntimeError("DATABASE_URL must use postgresql+psycopg.")
    return create_engine(database_url)
