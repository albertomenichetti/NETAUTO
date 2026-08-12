from __future__ import annotations

import os
from collections.abc import Callable, Generator
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from sqlalchemy import Engine, event, text
from sqlalchemy.engine import URL, Connection, make_url
from sqlalchemy.orm import Session, sessionmaker

import netauto.persistence.sqlalchemy.models  # noqa: F401
from netauto.composition import create_sqlalchemy_app
from netauto.persistence.sqlalchemy.base import Base
from netauto.persistence.sqlalchemy.database import create_database_engine
from support.http_server import serve_app_url


def _get_test_database_url() -> str:
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        raise pytest.UsageError(
            "TEST_DATABASE_URL is required for PostgreSQL integration tests"
        )
    return database_url


def _validated_postgresql_test_url() -> URL:
    database_url = _get_test_database_url()
    url = make_url(database_url)
    if url.get_backend_name() != "postgresql" or url.get_driver_name() != "psycopg":
        raise pytest.UsageError(
            "TEST_DATABASE_URL must use the postgresql+psycopg dialect"
        )
    return url


def _schema_name() -> str:
    return f"netauto_test_{uuid4().hex}"


def _migration_schema_name() -> str:
    return f"netauto_migration_test_{uuid4().hex}"


def _repository_schema_name() -> str:
    return f"netauto_repository_test_{uuid4().hex}"


@pytest.fixture(scope="session")
def postgresql_test_database_url() -> str:
    _validated_postgresql_test_url()
    return _get_test_database_url()


@pytest.fixture(scope="session")
def postgresql_engine(postgresql_test_database_url: str) -> Generator[Engine, None, None]:
    engine = create_database_engine(postgresql_test_database_url)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture(scope="session")
def postgresql_schema(postgresql_engine: Engine) -> Generator[str, None, None]:
    schema_name = _schema_name()
    yield from _managed_schema(postgresql_engine, schema_name)


@pytest.fixture(scope="session")
def postgresql_migration_schema(postgresql_engine: Engine) -> Generator[str, None, None]:
    schema_name = _migration_schema_name()
    yield from _managed_schema(postgresql_engine, schema_name)


@pytest.fixture(scope="session")
def postgresql_repository_schema(postgresql_engine: Engine) -> Generator[str, None, None]:
    schema_name = _repository_schema_name()
    before_public_tables = set(_inspector_table_names(postgresql_engine, schema="public"))
    with _managed_schema_context(postgresql_engine, schema_name):
        with postgresql_engine.connect().execution_options(
            isolation_level="AUTOCOMMIT"
        ) as connection:
            _set_search_path(connection, postgresql_engine, schema_name)
            command.upgrade(_alembic_config(connection, schema_name), "head")

        after_public_tables = set(_inspector_table_names(postgresql_engine, schema="public"))
        assert after_public_tables == before_public_tables
        yield schema_name


@pytest.fixture
def postgresql_connection(
    postgresql_engine: Engine,
    postgresql_schema: str,
) -> Generator[Connection, None, None]:
    connection = postgresql_engine.connect().execution_options(
        isolation_level="AUTOCOMMIT"
    )
    _set_search_path(connection, postgresql_engine, postgresql_schema)
    try:
        yield connection
    finally:
        connection.close()


@pytest.fixture(scope="session")
def postgresql_orm_schema(
    postgresql_engine: Engine,
    postgresql_schema: str,
) -> Generator[str, None, None]:
    before_public_tables = set(_inspector_table_names(postgresql_engine, schema="public"))
    with postgresql_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        _set_search_path(connection, postgresql_engine, postgresql_schema)
        Base.metadata.create_all(connection)

    after_public_tables = set(_inspector_table_names(postgresql_engine, schema="public"))
    assert after_public_tables == before_public_tables

    yield postgresql_schema


@pytest.fixture
def postgresql_model_session(
    postgresql_engine: Engine,
    postgresql_repository_schema: str,
) -> Generator[Session, None, None]:
    _truncate_repository_tables(postgresql_engine, postgresql_repository_schema)
    connection = postgresql_engine.connect()
    transaction = connection.begin()
    _set_search_path(connection, postgresql_engine, postgresql_repository_schema)
    session = Session(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
        _truncate_repository_tables(postgresql_engine, postgresql_repository_schema)


@pytest.fixture(scope="session")
def postgresql_repository_session_factory(
    postgresql_engine: Engine,
    postgresql_repository_schema: str,
) -> Generator[Callable[[], Session], None, None]:
    quoted_schema = _quoted_identifier(postgresql_engine, postgresql_repository_schema)

    class RepositorySchemaSession(Session):
        pass

    factory = sessionmaker(
        bind=postgresql_engine,
        expire_on_commit=False,
        class_=RepositorySchemaSession,
    )

    @event.listens_for(RepositorySchemaSession, "after_begin")
    def _set_local_search_path(
        session: Session,
        transaction: object,
        connection: Connection,
    ) -> None:
        if transaction is not session.get_transaction():
            return
        connection.execute(text(f"SET LOCAL search_path TO {quoted_schema}"))

    try:
        yield factory
    finally:
        event.remove(RepositorySchemaSession, "after_begin", _set_local_search_path)


@pytest.fixture
def postgresql_clean_repository_session_factory(
    postgresql_engine: Engine,
    postgresql_repository_schema: str,
    postgresql_repository_session_factory: Callable[[], Session],
) -> Generator[Callable[[], Session], None, None]:
    _truncate_repository_tables(postgresql_engine, postgresql_repository_schema)
    try:
        yield postgresql_repository_session_factory
    finally:
        _truncate_repository_tables(postgresql_engine, postgresql_repository_schema)


@pytest.fixture
def postgresql_application_app(
    postgresql_clean_repository_session_factory: Callable[[], Session],
    postgresql_test_database_url: str,
) -> FastAPI:
    return create_sqlalchemy_app(
        postgresql_clean_repository_session_factory,
        database_url=postgresql_test_database_url,
    ).app


@pytest.fixture
def postgresql_application_base_url(
    postgresql_application_app: FastAPI,
) -> Generator[str, None, None]:
    with serve_app_url(postgresql_application_app) as base_url:
        yield base_url


def _quoted_identifier(engine: Engine, identifier: str) -> str:
    preparer = engine.dialect.identifier_preparer
    return preparer.quote_identifier(identifier)


def _set_search_path(connection: Connection, engine: Engine, schema: str) -> None:
    quoted_schema = _quoted_identifier(engine, schema)
    connection.execute(text(f"SET search_path TO {quoted_schema}"))


def _truncate_repository_tables(engine: Engine, schema: str) -> None:
    table_names = [
        table_name
        for table_name in _inspector_table_names(engine, schema=schema)
        if table_name != "alembic_version"
    ]
    if not table_names:
        return
    quoted_tables = ", ".join(
        f"{_quoted_identifier(engine, schema)}.{_quoted_identifier(engine, table_name)}"
        for table_name in table_names
    )
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        connection.execute(text(f"TRUNCATE TABLE {quoted_tables} RESTART IDENTITY CASCADE"))


def _inspector_table_names(engine: Engine, *, schema: str) -> list[str]:
    from sqlalchemy import inspect

    return inspect(engine).get_table_names(schema=schema)


def _managed_schema(engine: Engine, schema_name: str) -> Generator[str, None, None]:
    quoted_schema = _quoted_identifier(engine, schema_name)
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        connection.execute(text(f"CREATE SCHEMA {quoted_schema}"))
    try:
        yield schema_name
    finally:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            connection.execute(text(f"DROP SCHEMA {quoted_schema} CASCADE"))
            exists_after_drop = connection.execute(
                text("SELECT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = :schema_name)"),
                {"schema_name": schema_name},
            ).scalar_one()
        assert exists_after_drop is False


@contextmanager
def _managed_schema_context(engine: Engine, schema_name: str) -> Generator[str, None, None]:
    yield from _managed_schema(engine, schema_name)


def _alembic_config(connection: Connection, version_table_schema: str) -> Config:
    config = Config(str(Path("alembic.ini")))
    config.attributes["connection"] = connection
    config.attributes["version_table_schema"] = version_table_schema
    return config
