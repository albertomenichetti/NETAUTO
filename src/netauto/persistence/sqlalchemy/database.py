"""SQLAlchemy engine and schema helpers."""

from sqlalchemy import Engine, event
from sqlalchemy.engine import create_engine

from netauto.persistence.sqlalchemy.base import Base


def create_sqlite_engine(database_url: str) -> Engine:
    """Create a SQLite engine with foreign key enforcement enabled."""

    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
    )

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

    return engine


def create_schema(engine: Engine) -> None:
    """Create the persistence schema explicitly."""

    Base.metadata.create_all(engine)
