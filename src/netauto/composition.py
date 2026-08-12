"""Runtime SQLAlchemy application composition."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from fastapi import FastAPI
from sqlalchemy import Engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import Session, sessionmaker

from netauto.api.app import create_app
from netauto.application.unit_of_work import ObjectUnitOfWorkFactory
from netauto.persistence.sqlalchemy.database import create_database_engine, create_schema
from netauto.persistence.sqlalchemy.unit_of_work import (
    PostgresqlModelWriteUnitOfWork,
    PostgresqlOwnershipGraphWriteUnitOfWork,
    SqlAlchemyUnitOfWork,
    SqliteModelWriteUnitOfWork,
    SqliteOwnershipGraphWriteUnitOfWork,
)


def _validated_runtime_database_url(database_url: str) -> URL:
    url = make_url(database_url)
    backend_name = url.get_backend_name()
    driver_name = url.get_driver_name()

    if backend_name == "sqlite":
        return url
    if backend_name == "postgresql" and driver_name == "psycopg":
        return url
    raise RuntimeError("DATABASE_URL must use sqlite or postgresql+psycopg.")


@dataclass(frozen=True)
class SqlAlchemyAppComposition:
    """Concrete FastAPI composition over a SQLAlchemy session factory."""

    app: FastAPI
    uow_factory: ObjectUnitOfWorkFactory
    model_write_uow_factory: ObjectUnitOfWorkFactory
    ownership_graph_uow_factory: ObjectUnitOfWorkFactory


@dataclass(frozen=True)
class RuntimeApplication:
    """Concrete runtime application and its process-lifetime engine."""

    engine: Engine
    app: FastAPI


def create_sqlalchemy_app(
    session_factory: Callable[[], Session],
    *,
    database_url: str,
) -> SqlAlchemyAppComposition:
    url = _validated_runtime_database_url(database_url)

    def uow_factory() -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(session_factory)

    if url.get_backend_name() == "sqlite":
        def sqlite_model_write_uow_factory() -> SqliteModelWriteUnitOfWork:
            return SqliteModelWriteUnitOfWork(session_factory)

        def sqlite_ownership_graph_uow_factory() -> SqliteOwnershipGraphWriteUnitOfWork:
            return SqliteOwnershipGraphWriteUnitOfWork(session_factory)

        model_write_uow_factory = sqlite_model_write_uow_factory
        ownership_graph_uow_factory = sqlite_ownership_graph_uow_factory
    else:
        def postgresql_model_write_uow_factory() -> PostgresqlModelWriteUnitOfWork:
            return PostgresqlModelWriteUnitOfWork(session_factory)

        def postgresql_ownership_graph_uow_factory() -> PostgresqlOwnershipGraphWriteUnitOfWork:
            return PostgresqlOwnershipGraphWriteUnitOfWork(session_factory)

        model_write_uow_factory = postgresql_model_write_uow_factory
        ownership_graph_uow_factory = postgresql_ownership_graph_uow_factory

    app = create_app(
        uow_factory,
        model_write_uow_factory=model_write_uow_factory,
        ownership_graph_uow_factory=ownership_graph_uow_factory,
    )
    return SqlAlchemyAppComposition(
        app=app,
        uow_factory=uow_factory,
        model_write_uow_factory=model_write_uow_factory,
        ownership_graph_uow_factory=ownership_graph_uow_factory,
    )


def create_runtime_application(database_url: str) -> RuntimeApplication:
    url = _validated_runtime_database_url(database_url)
    engine = create_database_engine(database_url)
    if url.get_backend_name() == "sqlite":
        create_schema(engine)

    session_factory = sessionmaker(
        engine,
        expire_on_commit=False,
    )
    composition = create_sqlalchemy_app(session_factory, database_url=database_url)
    return RuntimeApplication(engine=engine, app=composition.app)
