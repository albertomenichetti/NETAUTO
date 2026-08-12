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
)


def _session_factory() -> Session:
    raise AssertionError("session factory should not be called in composition selection tests")


def test_create_sqlalchemy_app_selects_postgresql_uows() -> None:
    composition = create_sqlalchemy_app(_session_factory)

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


def test_create_runtime_application_rejects_sqlite_runtime_url() -> None:
    with pytest.raises(RuntimeError, match="DATABASE_URL must use postgresql\\+psycopg\\."):
        create_runtime_application("sqlite:///netauto.db")


@pytest.mark.parametrize(
    "database_url",
    [
        "mysql://user:secret@localhost/netauto",
        "postgresql+psycopg2://user:secret@localhost/netauto",
        "postgresql+asyncpg://user:secret@localhost/netauto",
    ],
)
def test_create_runtime_application_rejects_unsupported_runtime_urls(database_url: str) -> None:
    with pytest.raises(RuntimeError, match="DATABASE_URL must use postgresql\\+psycopg\\."):
        create_runtime_application(database_url)


def test_create_runtime_application_uses_postgresql_engine_without_schema_creation(
    monkeypatch,
) -> None:
    engine = Mock()
    create_database_engine = Mock(return_value=engine)
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
    create_sqlalchemy_app_mock.assert_called_once()
    assert create_sqlalchemy_app_mock.call_args.args
    session_factory = create_sqlalchemy_app_mock.call_args.args[0]
    assert callable(session_factory)
