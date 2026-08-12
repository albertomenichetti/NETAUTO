from __future__ import annotations

from collections.abc import Generator, Iterable
from contextlib import contextmanager
from uuid import uuid4

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import IntegrityError

import netauto.persistence.sqlalchemy.models  # noqa: F401
from netauto.persistence.sqlalchemy.base import Base

pytestmark = pytest.mark.postgresql

EXPECTED_TABLES = {
    "datatypes",
    "datatype_versions",
    "object_templates",
    "object_template_versions",
    "object_template_properties",
    "object_template_components",
    "relationship_definitions",
    "relationships",
    "objects",
    "object_changes",
    "object_components",
}

EXPECTED_PRIMARY_KEYS = {
    "datatypes": {"id"},
    "datatype_versions": {"datatype_id", "version"},
    "object_templates": {"id"},
    "object_template_versions": {"template_id", "version"},
    "object_template_properties": {"template_id", "template_version", "name"},
    "object_template_components": {"template_id", "template_version", "name"},
    "relationship_definitions": {"id"},
    "relationships": {"id"},
    "objects": {"id"},
    "object_changes": {"id"},
    "object_components": {"child_object_id"},
}

EXPECTED_UNIQUE_CONSTRAINTS = {
    "datatypes": {"uq_datatypes_name": ("namespace", "name")},
    "object_templates": {"uq_object_templates_name": ("namespace", "name")},
    "object_template_properties": {
        "uq_object_template_properties_owner_position": (
            "template_id",
            "template_version",
            "position",
        )
    },
    "object_template_components": {
        "uq_object_template_components_owner_position": (
            "template_id",
            "template_version",
            "position",
        )
    },
    "relationships": {
        "uq_relationships_definition_source_target": (
            "relationship_definition_id",
            "source_object_id",
            "target_object_id",
        )
    },
}

EXPECTED_CHECKS = {
    "object_template_versions": {"ck_object_template_versions_parent_pair"},
    "object_components": {
        "ck_object_components_distinct_objects",
        "ck_object_components_slot_name_not_empty",
    },
}

EXPECTED_INDEXES = {
    "object_template_versions": {
        "ix_object_template_versions_parent": ("parent_template_id", "parent_version"),
    },
    "object_template_properties": {
        "ix_object_template_properties_datatype_version": ("datatype_id", "datatype_version"),
    },
    "object_template_components": {
        "ix_object_template_components_target_template": ("target_template_id",),
    },
    "objects": {
        "ix_objects_template_version": ("template_id", "template_version"),
    },
    "object_changes": {
        "ix_object_changes_object_id_occurred_at": ("object_id", "occurred_at"),
    },
    "object_components": {
        "ix_object_components_parent_slot_child": (
            "parent_object_id",
            "slot_name",
            "child_object_id",
        ),
    },
}

@pytest.fixture(scope="session")
def postgresql_inspector(
    postgresql_engine: Engine,
    postgresql_orm_schema: str,
):
    del postgresql_orm_schema
    return inspect(postgresql_engine)


def test_postgresql_schema_contains_exact_current_orm_tables(
    postgresql_inspector,
    postgresql_orm_schema: str,
) -> None:
    reflected_tables = set(postgresql_inspector.get_table_names(schema=postgresql_orm_schema))
    metadata_tables = {table.name for table in Base.metadata.sorted_tables}

    assert metadata_tables == EXPECTED_TABLES
    assert reflected_tables == metadata_tables


def test_postgresql_primary_keys_match_current_metadata(
    postgresql_inspector,
    postgresql_orm_schema: str,
) -> None:
    for table_name, expected_columns in EXPECTED_PRIMARY_KEYS.items():
        reflected = postgresql_inspector.get_pk_constraint(table_name, schema=postgresql_orm_schema)
        assert set(reflected["constrained_columns"]) == expected_columns


def test_postgresql_foreign_keys_match_current_metadata(
    postgresql_inspector,
    postgresql_orm_schema: str,
) -> None:
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
            for item in postgresql_inspector.get_foreign_keys(
                table_name,
                schema=postgresql_orm_schema,
            )
        }
        for table_name in EXPECTED_TABLES
    }

    assert reflected_by_table == metadata_by_table


def test_postgresql_unique_constraints_match_current_metadata(
    postgresql_inspector,
    postgresql_orm_schema: str,
) -> None:
    for table_name, expected in EXPECTED_UNIQUE_CONSTRAINTS.items():
        reflected = {
            item["name"]: tuple(item["column_names"])
            for item in postgresql_inspector.get_unique_constraints(
                table_name,
                schema=postgresql_orm_schema,
            )
        }
        assert reflected == expected


def test_postgresql_check_constraints_match_current_metadata(
    postgresql_inspector,
    postgresql_orm_schema: str,
) -> None:
    for table_name, expected_names in EXPECTED_CHECKS.items():
        reflected_names = {
            item["name"]
            for item in postgresql_inspector.get_check_constraints(
                table_name,
                schema=postgresql_orm_schema,
            )
        }
        assert reflected_names == expected_names


def test_postgresql_explicit_indexes_match_current_metadata(
    postgresql_inspector,
    postgresql_orm_schema: str,
) -> None:
    for table_name, expected_indexes in EXPECTED_INDEXES.items():
        reflected = {
            item["name"]: tuple(item["column_names"])
            for item in postgresql_inspector.get_indexes(
                table_name,
                schema=postgresql_orm_schema,
            )
            if not item.get("unique", False)
        }
        assert reflected == expected_indexes


def test_postgresql_enforces_primary_key_uniqueness(
    postgresql_engine: Engine,
    postgresql_schema: str,
    postgresql_orm_schema: str,
) -> None:
    del postgresql_orm_schema
    datatype_id = _uuid()
    with pytest.raises(IntegrityError):
        _autocommit_block(
            postgresql_engine,
            postgresql_schema,
            [
                (
                    "INSERT INTO datatypes (id, namespace, name, description) "
                    "VALUES (:id, :namespace, :name, :description)",
                    {
                        "id": datatype_id,
                        "namespace": _name("pk_namespace"),
                        "name": _name("pk_name"),
                        "description": None,
                    },
                ),
                (
                    "INSERT INTO datatypes (id, namespace, name, description) "
                    "VALUES (:id, :namespace, :name, :description)",
                    {
                        "id": datatype_id,
                        "namespace": _name("pk_namespace_second"),
                        "name": _name("pk_name_second"),
                        "description": None,
                    },
                ),
            ],
        )


def test_postgresql_enforces_unique_datatype_name_pair(
    postgresql_engine: Engine,
    postgresql_schema: str,
    postgresql_orm_schema: str,
) -> None:
    del postgresql_orm_schema
    namespace = _name("unique_ns")
    name = _name("unique_name")
    with pytest.raises(IntegrityError):
        _autocommit_block(
            postgresql_engine,
            postgresql_schema,
            [
                (
                    "INSERT INTO datatypes (id, namespace, name, description) "
                    "VALUES (:id, :namespace, :name, :description)",
                    {
                        "id": _uuid(),
                        "namespace": namespace,
                        "name": name,
                        "description": None,
                    },
                ),
                (
                    "INSERT INTO datatypes (id, namespace, name, description) "
                    "VALUES (:id, :namespace, :name, :description)",
                    {
                        "id": _uuid(),
                        "namespace": namespace,
                        "name": name,
                        "description": None,
                    },
                ),
            ],
        )


def test_postgresql_enforces_simple_foreign_key(
    postgresql_engine: Engine,
    postgresql_schema: str,
    postgresql_orm_schema: str,
) -> None:
    del postgresql_orm_schema
    with pytest.raises(IntegrityError):
        _execute(
            postgresql_engine,
            postgresql_schema,
            "INSERT INTO datatype_versions "
            "(datatype_id, version, status, base_type, constraints_json) "
            "VALUES (:datatype_id, 1, 'draft', 'core.string', '[]')",
            {"datatype_id": _uuid()},
        )


def test_postgresql_enforces_composite_exact_version_foreign_key(
    postgresql_engine: Engine,
    postgresql_schema: str,
    postgresql_orm_schema: str,
) -> None:
    del postgresql_orm_schema
    template_id = _uuid()
    _execute(
        postgresql_engine,
        postgresql_schema,
        "INSERT INTO object_templates (id, namespace, name, description, abstract) "
        "VALUES (:id, :namespace, :name, :description, FALSE)",
        {
            "id": template_id,
            "namespace": _name("template_ns"),
            "name": _name("template_name"),
            "description": None,
        },
    )
    with pytest.raises(IntegrityError):
        _execute(
            postgresql_engine,
            postgresql_schema,
            "INSERT INTO objects (id, template_id, template_version, properties_json) "
            "VALUES (:id, :template_id, 99, '{}')",
            {
                "id": _uuid(),
                "template_id": template_id,
            },
        )


def test_postgresql_enforces_parent_pair_check(
    postgresql_engine: Engine,
    postgresql_schema: str,
    postgresql_orm_schema: str,
) -> None:
    del postgresql_orm_schema
    template_id = _uuid()
    _execute(
        postgresql_engine,
        postgresql_schema,
        "INSERT INTO object_templates (id, namespace, name, description, abstract) "
        "VALUES (:id, :namespace, :name, :description, FALSE)",
        {
            "id": template_id,
            "namespace": _name("pair_ns"),
            "name": _name("pair_name"),
            "description": None,
        },
    )
    with pytest.raises(IntegrityError):
        _execute(
            postgresql_engine,
            postgresql_schema,
            "INSERT INTO object_template_versions "
            "(template_id, version, status, parent_template_id, parent_version) "
            "VALUES (:template_id, 1, 'draft', :parent_template_id, NULL)",
            {
                "template_id": template_id,
                "parent_template_id": _uuid(),
            },
        )


def test_postgresql_enforces_object_component_checks(
    postgresql_engine: Engine,
    postgresql_schema: str,
    postgresql_orm_schema: str,
) -> None:
    del postgresql_orm_schema
    template_id = _insert_minimal_template_lineage(postgresql_engine, postgresql_schema)
    object_id = _uuid()
    _execute(
        postgresql_engine,
        postgresql_schema,
        "INSERT INTO objects (id, template_id, template_version, properties_json) "
        "VALUES (:id, :template_id, 1, '{}')",
        {
            "id": object_id,
            "template_id": template_id,
        },
    )
    with pytest.raises(IntegrityError):
        _execute(
            postgresql_engine,
            postgresql_schema,
            "INSERT INTO object_components (parent_object_id, slot_name, child_object_id) "
            "VALUES (:parent_object_id, 'children', :child_object_id)",
            {
                "parent_object_id": object_id,
                "child_object_id": object_id,
            },
        )
    with pytest.raises(IntegrityError):
        _execute(
            postgresql_engine,
            postgresql_schema,
            "INSERT INTO object_components (parent_object_id, slot_name, child_object_id) "
            "VALUES (:parent_object_id, '', :child_object_id)",
            {
                "parent_object_id": object_id,
                "child_object_id": _uuid(),
            },
        )


def test_postgresql_enforces_cascade_delete_for_template_properties(
    postgresql_engine: Engine,
    postgresql_schema: str,
    postgresql_orm_schema: str,
) -> None:
    del postgresql_orm_schema
    datatype_id = _insert_minimal_datatype_lineage(postgresql_engine, postgresql_schema)
    template_id = _insert_minimal_template_lineage(postgresql_engine, postgresql_schema)
    _execute(
        postgresql_engine,
        postgresql_schema,
        "INSERT INTO object_template_properties "
        "(template_id, template_version, position, name, datatype_id, datatype_version, required) "
        "VALUES (:template_id, 1, 0, :name, :datatype_id, 1, FALSE)",
        {
            "template_id": template_id,
            "name": _name("cascade_property"),
            "datatype_id": datatype_id,
        },
    )

    before_count = _scalar_count(
        postgresql_engine,
        postgresql_schema,
        "SELECT COUNT(*) FROM object_template_properties WHERE template_id = :template_id",
        {"template_id": template_id},
    )
    assert before_count == 1

    _execute(
        postgresql_engine,
        postgresql_schema,
        "DELETE FROM object_template_versions WHERE template_id = :template_id AND version = 1",
        {"template_id": template_id},
    )

    after_count = _scalar_count(
        postgresql_engine,
        postgresql_schema,
        "SELECT COUNT(*) FROM object_template_properties WHERE template_id = :template_id",
        {"template_id": template_id},
    )
    assert after_count == 0


def test_postgresql_enforces_restrict_delete_for_bound_template_version(
    postgresql_engine: Engine,
    postgresql_schema: str,
    postgresql_orm_schema: str,
) -> None:
    del postgresql_orm_schema
    template_id = _insert_minimal_template_lineage(postgresql_engine, postgresql_schema)
    _execute(
        postgresql_engine,
        postgresql_schema,
        "INSERT INTO objects (id, template_id, template_version, properties_json) "
        "VALUES (:id, :template_id, 1, '{}')",
        {
            "id": _uuid(),
            "template_id": template_id,
        },
    )
    with pytest.raises(IntegrityError):
        _execute(
            postgresql_engine,
            postgresql_schema,
            "DELETE FROM object_template_versions WHERE template_id = :template_id AND version = 1",
            {"template_id": template_id},
        )


def _insert_minimal_datatype_lineage(engine: Engine, schema: str) -> str:
    datatype_id = _uuid()
    _execute(
        engine,
        schema,
        "INSERT INTO datatypes (id, namespace, name, description) "
        "VALUES (:id, :namespace, :name, :description)",
        {
            "id": datatype_id,
            "namespace": _name("datatype_ns"),
            "name": _name("datatype_name"),
            "description": None,
        },
    )
    _execute(
        engine,
        schema,
        "INSERT INTO datatype_versions "
        "(datatype_id, version, status, base_type, constraints_json) "
        "VALUES (:datatype_id, 1, 'published', 'core.string', '[]')",
        {"datatype_id": datatype_id},
    )
    return datatype_id


def _insert_minimal_template_lineage(engine: Engine, schema: str) -> str:
    template_id = _uuid()
    _execute(
        engine,
        schema,
        "INSERT INTO object_templates (id, namespace, name, description, abstract) "
        "VALUES (:id, :namespace, :name, :description, FALSE)",
        {
            "id": template_id,
            "namespace": _name("template_ns"),
            "name": _name("template_name"),
            "description": None,
        },
    )
    _execute(
        engine,
        schema,
        "INSERT INTO object_template_versions "
        "(template_id, version, status, parent_template_id, parent_version) "
        "VALUES (:template_id, 1, 'published', NULL, NULL)",
        {"template_id": template_id},
    )
    return template_id


def _execute(engine: Engine, schema: str, statement: str, parameters: dict[str, object]) -> None:
    with _schema_connection(engine, schema) as connection:
        connection.execute(text(statement), parameters)


def _autocommit_block(
    engine: Engine,
    schema: str,
    statements: Iterable[tuple[str, dict[str, object]]],
) -> None:
    with _schema_connection(engine, schema) as connection:
        for statement, parameters in statements:
            connection.execute(text(statement), parameters)


def _scalar_count(
    engine: Engine,
    schema: str,
    statement: str,
    parameters: dict[str, object],
) -> int:
    with _schema_connection(engine, schema) as connection:
        return int(connection.execute(text(statement), parameters).scalar_one())


@contextmanager
def _schema_connection(engine: Engine, schema: str) -> Generator[Connection, None, None]:
    quoted_schema = engine.dialect.identifier_preparer.quote_identifier(schema)
    connection = engine.connect().execution_options(isolation_level="AUTOCOMMIT")
    try:
        connection.execute(text(f"SET search_path TO {quoted_schema}"))
        yield connection
    finally:
        connection.close()


def _uuid() -> str:
    return str(uuid4())


def _name(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"
