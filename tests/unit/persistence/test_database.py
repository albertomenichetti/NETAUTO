from pathlib import Path
from unittest.mock import Mock

from sqlalchemy import text

from netauto.persistence.sqlalchemy.database import (
    create_database_engine,
    create_sqlite_engine,
)


def test_create_database_engine_preserves_sqlite_behavior(tmp_path: Path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'engine.sqlite3'}")
    try:
        with engine.connect() as connection:
            foreign_keys = connection.execute(text("PRAGMA foreign_keys")).scalar_one()

        assert foreign_keys == 1
        assert engine.dialect.name == "sqlite"
    finally:
        engine.dispose()


def test_create_sqlite_engine_remains_compatible_wrapper(tmp_path: Path) -> None:
    engine = create_sqlite_engine(f"sqlite:///{tmp_path / 'compat.sqlite3'}")
    try:
        assert engine.dialect.name == "sqlite"
    finally:
        engine.dispose()


def test_create_database_engine_builds_lazy_psycopg_postgresql_engine() -> None:
    engine = create_database_engine("postgresql+psycopg://user:password@localhost/netauto")
    try:
        assert engine.dialect.name == "postgresql"
        assert engine.dialect.driver == "psycopg"
    finally:
        engine.dispose()


def test_postgresql_engine_does_not_apply_sqlite_connect_args(monkeypatch) -> None:
    create_engine_mock = Mock()
    engine = Mock()
    create_engine_mock.return_value = engine
    monkeypatch.setattr("netauto.persistence.sqlalchemy.database.create_engine", create_engine_mock)

    create_database_engine("postgresql+psycopg://user:password@localhost/netauto")

    create_engine_mock.assert_called_once_with(
        "postgresql+psycopg://user:password@localhost/netauto"
    )


def test_sqlite_engine_applies_sqlite_connect_args_and_listener(monkeypatch) -> None:
    create_engine_mock = Mock()
    engine = Mock()
    create_engine_mock.return_value = engine
    listens_for_mock = Mock(side_effect=lambda *_args, **_kwargs: (lambda fn: fn))
    monkeypatch.setattr("netauto.persistence.sqlalchemy.database.create_engine", create_engine_mock)
    monkeypatch.setattr(
        "netauto.persistence.sqlalchemy.database.event.listens_for",
        listens_for_mock,
    )

    result = create_database_engine("sqlite:///netauto.sqlite3")

    assert result is engine
    create_engine_mock.assert_called_once_with(
        "sqlite:///netauto.sqlite3",
        connect_args={"check_same_thread": False},
    )
    listens_for_mock.assert_called_once_with(engine, "connect")


def test_postgresql_engine_does_not_install_sqlite_pragma_listener(monkeypatch) -> None:
    create_engine_mock = Mock()
    engine = Mock()
    create_engine_mock.return_value = engine
    listens_for_mock = Mock(side_effect=lambda *_args, **_kwargs: (lambda fn: fn))
    monkeypatch.setattr("netauto.persistence.sqlalchemy.database.create_engine", create_engine_mock)
    monkeypatch.setattr(
        "netauto.persistence.sqlalchemy.database.event.listens_for",
        listens_for_mock,
    )

    result = create_database_engine("postgresql+psycopg://user:password@localhost/netauto")

    assert result is engine
    listens_for_mock.assert_not_called()
