from __future__ import annotations

from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from sqlalchemy.orm import Session

from netauto.composition import (
    SqlAlchemyAppComposition,
    create_runtime_application,
    create_sqlalchemy_app,
)
from netauto.persistence.sqlalchemy.unit_of_work import (
    PostgresqlModelWriteUnitOfWork,
    PostgresqlOwnershipGraphWriteUnitOfWork,
    SqlAlchemyUnitOfWork,
    SqliteModelWriteUnitOfWork,
    SqliteOwnershipGraphWriteUnitOfWork,
)


def _session_factory() -> Session:
    raise AssertionError("session factory should not be called in composition selection tests")


def test_create_sqlalchemy_app_selects_sqlite_uows() -> None:
    composition = create_sqlalchemy_app(
        _session_factory,
        database_url="sqlite:///netauto.sqlite3",
    )

    assert isinstance(composition.app, FastAPI)
    assert isinstance(composition.uow_factory(), SqlAlchemyUnitOfWork)
    assert isinstance(composition.model_write_uow_factory(), SqliteModelWriteUnitOfWork)
    assert isinstance(
        composition.ownership_graph_uow_factory(),
        SqliteOwnershipGraphWriteUnitOfWork,
    )


def test_create_sqlalchemy_app_selects_postgresql_uows() -> None:
    composition = create_sqlalchemy_app(
        _session_factory,
        database_url="postgresql+psycopg://user:secret@localhost/netauto",
    )

    assert isinstance(composition.app, FastAPI)
    assert isinstance(composition.uow_factory(), SqlAlchemyUnitOfWork)
    assert isinstance(
        composition.model_write_uow_factory(),
        PostgresqlModelWriteUnitOfWork,
    )
    assert isinstance(
        composition.ownership_graph_uow_factory(),
        PostgresqlOwnershipGraphWriteUnitOfWork,
    )


@pytest.mark.parametrize(
    ("database_url", "match"),
    [
        ("mysql://user:secret@localhost/netauto", "sqlite or postgresql\\+psycopg"),
        (
            "postgresql+psycopg2://user:secret@localhost/netauto",
            "sqlite or postgresql\\+psycopg",
        ),
        (
            "postgresql+asyncpg://user:secret@localhost/netauto",
            "sqlite or postgresql\\+psycopg",
        ),
    ],
)
def test_create_sqlalchemy_app_rejects_unsupported_runtime_urls(
    database_url: str,
    match: str,
) -> None:
    with pytest.raises(RuntimeError, match=match):
        create_sqlalchemy_app(_session_factory, database_url=database_url)


def test_create_runtime_application_initializes_sqlite_schema(monkeypatch) -> None:
    engine = Mock()
    create_database_engine = Mock(return_value=engine)
    create_schema = Mock()
    composition = SqlAlchemyAppComposition(
        app=FastAPI(),
        uow_factory=Mock(),
        model_write_uow_factory=Mock(),
        ownership_graph_uow_factory=Mock(),
    )
    create_sqlalchemy_app_mock = Mock(return_value=composition)
    monkeypatch.setattr(
        "netauto.composition.create_database_engine",
        create_database_engine,
    )
    monkeypatch.setattr("netauto.composition.create_schema", create_schema)
    monkeypatch.setattr(
        "netauto.composition.create_sqlalchemy_app",
        create_sqlalchemy_app_mock,
    )

    runtime = create_runtime_application("sqlite:///netauto.sqlite3")

    assert runtime.engine is engine
    assert runtime.app is composition.app
    create_database_engine.assert_called_once_with("sqlite:///netauto.sqlite3")
    create_schema.assert_called_once_with(engine)
    create_sqlalchemy_app_mock.assert_called_once()
    assert create_sqlalchemy_app_mock.call_args.kwargs["database_url"] == "sqlite:///netauto.sqlite3"


def test_create_runtime_application_does_not_initialize_postgresql_schema(
    monkeypatch,
) -> None:
    engine = Mock()
    create_database_engine = Mock(return_value=engine)
    create_schema = Mock()
    composition = SqlAlchemyAppComposition(
        app=FastAPI(),
        uow_factory=Mock(),
        model_write_uow_factory=Mock(),
        ownership_graph_uow_factory=Mock(),
    )
    create_sqlalchemy_app_mock = Mock(return_value=composition)
    monkeypatch.setattr(
        "netauto.composition.create_database_engine",
        create_database_engine,
    )
    monkeypatch.setattr("netauto.composition.create_schema", create_schema)
    monkeypatch.setattr(
        "netauto.composition.create_sqlalchemy_app",
        create_sqlalchemy_app_mock,
    )

    runtime = create_runtime_application("postgresql+psycopg://user:secret@localhost/netauto")

    assert runtime.engine is engine
    assert runtime.app is composition.app
    create_database_engine.assert_called_once_with(
        "postgresql+psycopg://user:secret@localhost/netauto"
    )
    create_schema.assert_not_called()
    create_sqlalchemy_app_mock.assert_called_once()
    assert (
        create_sqlalchemy_app_mock.call_args.kwargs["database_url"]
        == "postgresql+psycopg://user:secret@localhost/netauto"
    )
