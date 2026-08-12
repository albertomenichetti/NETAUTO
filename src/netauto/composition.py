"""Runtime SQLAlchemy application composition."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from fastapi import FastAPI
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from netauto.api.app import create_app
from netauto.application.unit_of_work import ObjectUnitOfWorkFactory
from netauto.persistence.sqlalchemy.database import create_database_engine
from netauto.persistence.sqlalchemy.unit_of_work import (
    PostgresqlModelWriteUnitOfWork,
    PostgresqlOwnershipGraphWriteUnitOfWork,
    SqlAlchemyUnitOfWork,
)


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
) -> SqlAlchemyAppComposition:
    def uow_factory() -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(session_factory)

    def postgresql_model_write_uow_factory() -> PostgresqlModelWriteUnitOfWork:
        return PostgresqlModelWriteUnitOfWork(session_factory)

    def postgresql_ownership_graph_uow_factory() -> PostgresqlOwnershipGraphWriteUnitOfWork:
        return PostgresqlOwnershipGraphWriteUnitOfWork(session_factory)

    app = create_app(
        uow_factory,
        model_write_uow_factory=postgresql_model_write_uow_factory,
        ownership_graph_uow_factory=postgresql_ownership_graph_uow_factory,
    )
    return SqlAlchemyAppComposition(
        app=app,
        uow_factory=uow_factory,
        model_write_uow_factory=postgresql_model_write_uow_factory,
        ownership_graph_uow_factory=postgresql_ownership_graph_uow_factory,
    )


def create_runtime_application(database_url: str) -> RuntimeApplication:
    engine = create_database_engine(database_url)
    session_factory = sessionmaker(
        engine,
        expire_on_commit=False,
    )
    composition = create_sqlalchemy_app(session_factory)
    return RuntimeApplication(engine=engine, app=composition.app)
