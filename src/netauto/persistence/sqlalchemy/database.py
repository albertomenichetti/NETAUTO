"""SQLAlchemy engine and schema helpers."""

from sqlalchemy import Engine, event
from sqlalchemy.engine import create_engine, make_url

from netauto.persistence.sqlalchemy.base import Base


def _is_sqlite_url(database_url: str) -> bool:
    return make_url(database_url).get_backend_name() == "sqlite"


def _enable_sqlite_foreign_keys(engine: Engine) -> None:
    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection: object, _connection_record: object) -> None:
        cursor_factory = getattr(dbapi_connection, "cursor", None)
        if cursor_factory is None:
            return
        cursor = cursor_factory()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()


def create_database_engine(database_url: str) -> Engine:
    """Create a SQLAlchemy engine for the configured database URL."""

    if _is_sqlite_url(database_url):
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
        )
        _enable_sqlite_foreign_keys(engine)
        return engine

    return create_engine(database_url)


def create_sqlite_engine(database_url: str) -> Engine:
    """Create a SQLite engine with foreign key enforcement enabled."""

    return create_database_engine(database_url)


def create_schema(engine: Engine) -> None:
    """Create the persistence schema explicitly."""

    Base.metadata.create_all(engine)
