from __future__ import annotations

import os
from collections.abc import Generator
from uuid import uuid4

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.engine import URL, Connection, make_url

import netauto.persistence.sqlalchemy.models  # noqa: F401
from netauto.persistence.sqlalchemy.base import Base
from netauto.persistence.sqlalchemy.database import create_database_engine


def _get_test_database_url() -> str:
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is required for PostgreSQL integration tests")
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


def _quoted_identifier(engine: Engine, identifier: str) -> str:
    preparer = engine.dialect.identifier_preparer
    return preparer.quote_identifier(identifier)


def _set_search_path(connection: Connection, engine: Engine, schema: str) -> None:
    quoted_schema = _quoted_identifier(engine, schema)
    connection.execute(text(f"SET search_path TO {quoted_schema}"))


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
