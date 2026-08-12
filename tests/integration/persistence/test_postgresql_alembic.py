from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection, Engine
from tests.integration.persistence.test_postgresql_orm_schema import (
    EXPECTED_CHECKS,
    EXPECTED_INDEXES,
    EXPECTED_PRIMARY_KEYS,
    EXPECTED_TABLES,
    EXPECTED_UNIQUE_CONSTRAINTS,
)

pytestmark = pytest.mark.postgresql


def test_alembic_upgrade_head_creates_current_schema_in_isolated_postgresql_namespace(
    postgresql_engine: Engine,
    postgresql_migration_schema: str,
) -> None:
    before_public_tables = set(_table_names(postgresql_engine, "public"))
    assert _table_names(postgresql_engine, postgresql_migration_schema) == []

    with postgresql_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        _set_search_path(connection, postgresql_engine, postgresql_migration_schema)
        config = _alembic_config(connection, postgresql_migration_schema)
        command.upgrade(config, "head")
        current_revision = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()

    head_revision = _head_revision()
    assert current_revision == head_revision

    reflected_tables = set(_table_names(postgresql_engine, postgresql_migration_schema))
    assert reflected_tables == EXPECTED_TABLES | {"alembic_version"}
    assert set(_table_names(postgresql_engine, "public")) == before_public_tables

    inspector = inspect(postgresql_engine)
    _assert_primary_keys(inspector, postgresql_migration_schema)
    _assert_foreign_keys(inspector, postgresql_migration_schema)
    _assert_unique_constraints(inspector, postgresql_migration_schema)
    _assert_check_constraints(inspector, postgresql_migration_schema)
    _assert_indexes(inspector, postgresql_migration_schema)


def _alembic_config(connection: Connection, version_table_schema: str) -> Config:
    config = Config(str(Path("alembic.ini")))
    config.attributes["connection"] = connection
    config.attributes["version_table_schema"] = version_table_schema
    return config


def _head_revision() -> str:
    config = Config(str(Path("alembic.ini")))
    script = __import__("alembic.script").script.ScriptDirectory.from_config(config)
    heads = script.get_heads()
    assert len(heads) == 1
    return heads[0]


def _table_names(engine: Engine, schema: str) -> list[str]:
    return inspect(engine).get_table_names(schema=schema)


def _set_search_path(connection: Connection, engine: Engine, schema: str) -> None:
    quoted_schema = engine.dialect.identifier_preparer.quote_identifier(schema)
    connection.execute(text(f"SET search_path TO {quoted_schema}"))


def _assert_primary_keys(inspector, schema: str) -> None:
    for table_name, expected_columns in EXPECTED_PRIMARY_KEYS.items():
        reflected = inspector.get_pk_constraint(table_name, schema=schema)
        assert set(reflected["constrained_columns"]) == expected_columns


def _assert_foreign_keys(inspector, schema: str) -> None:
    import netauto.persistence.sqlalchemy.models  # noqa: F401
    from netauto.persistence.sqlalchemy.base import Base

    metadata_by_table = {
        table.name: {
            (
                tuple(element.parent.name for element in constraint.elements),
                constraint.referred_table.name,
                tuple(element.column.name for element in constraint.elements),
                (constraint.ondelete or "").upper(),
            )
            for constraint in table.foreign_key_constraints
        }
        for table in Base.metadata.sorted_tables
    }
    reflected_by_table = {
        table_name: {
            (
                tuple(item["constrained_columns"]),
                item["referred_table"],
                tuple(item["referred_columns"]),
                ((item.get("options") or {}).get("ondelete") or "").upper(),
            )
            for item in inspector.get_foreign_keys(table_name, schema=schema)
        }
        for table_name in EXPECTED_TABLES
    }
    assert reflected_by_table == metadata_by_table


def _assert_unique_constraints(inspector, schema: str) -> None:
    for table_name, expected in EXPECTED_UNIQUE_CONSTRAINTS.items():
        reflected = {
            item["name"]: tuple(item["column_names"])
            for item in inspector.get_unique_constraints(table_name, schema=schema)
        }
        assert reflected == expected


def _assert_check_constraints(inspector, schema: str) -> None:
    for table_name, expected_names in EXPECTED_CHECKS.items():
        reflected_names = {
            item["name"] for item in inspector.get_check_constraints(table_name, schema=schema)
        }
        assert reflected_names == expected_names


def _assert_indexes(inspector, schema: str) -> None:
    for table_name, expected_indexes in EXPECTED_INDEXES.items():
        reflected = {
            item["name"]: tuple(item["column_names"])
            for item in inspector.get_indexes(table_name, schema=schema)
            if not item.get("unique", False)
        }
        assert reflected == expected_indexes
