from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

pytestmark = pytest.mark.postgresql


def test_postgresql_harness_smoke(
    postgresql_engine: Engine,
    postgresql_schema: str,
    postgresql_connection: Connection,
) -> None:
    assert postgresql_engine.dialect.name == "postgresql"
    assert postgresql_engine.dialect.driver == "psycopg"

    scalar_one = postgresql_connection.execute(text("SELECT 1")).scalar_one()
    assert scalar_one == 1

    version_text = postgresql_connection.execute(text("SELECT version()")).scalar_one()
    assert "PostgreSQL" in version_text

    current_database = postgresql_connection.execute(text("SELECT current_database()")).scalar_one()
    assert isinstance(current_database, str)
    assert current_database != ""

    current_schema = postgresql_connection.execute(text("SELECT current_schema()")).scalar_one()
    assert current_schema == postgresql_schema

    schema_exists = postgresql_connection.execute(
        text("SELECT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = :schema_name)"),
        {"schema_name": postgresql_schema},
    ).scalar_one()
    assert schema_exists is True

    probe_name = "harness_probe_smoke"
    postgresql_connection.execute(text(f"CREATE TABLE {probe_name} (value integer NOT NULL)"))
    try:
        postgresql_connection.execute(text(f"INSERT INTO {probe_name} (value) VALUES (1)"))
        stored_value = postgresql_connection.execute(
            text(f"SELECT value FROM {probe_name}")
        ).scalar_one()
        assert stored_value == 1
    finally:
        postgresql_connection.execute(text(f"DROP TABLE {probe_name}"))
