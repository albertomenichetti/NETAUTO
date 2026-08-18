"""Real-PostgreSQL migration, schema structure, and drift verification."""

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine.interfaces import ReflectedIndex

from netauto.persistence.metadata import metadata
from tests.test_schema_metadata import EXPECTED_TABLES

EXPECTED_COLUMNS = {
    "datatypes": ("id", "namespace", "name", "description", "default_version"),
    "datatype_versions": (
        "datatype_id",
        "version",
        "revision",
        "status",
        "base_type",
        "constraints",
    ),
    "object_templates": (
        "id",
        "namespace",
        "name",
        "description",
        "abstract",
        "default_version",
        "parent_template_id",
    ),
    "object_template_versions": (
        "template_id",
        "version",
        "revision",
        "status",
        "parent_template_id",
        "parent_version",
    ),
    "object_template_properties": (
        "template_id",
        "template_version",
        "name",
        "position",
        "datatype_id",
        "datatype_version",
        "value_mode",
        "required",
        "migration_default",
    ),
    "object_template_components": (
        "template_id",
        "template_version",
        "name",
        "position",
        "target_template_id",
    ),
    "relationship_definitions": ("id", "symmetric", "default_version"),
    "relationship_resolutions": (
        "id",
        "relationship_definition_id",
        "from_template_id",
        "to_template_id",
        "name",
    ),
    "relationship_definition_versions": (
        "relationship_definition_id",
        "version",
        "revision",
        "status",
    ),
    "relationship_definition_properties": (
        "relationship_definition_id",
        "relationship_definition_version",
        "name",
        "position",
        "datatype_id",
        "datatype_version",
        "value_mode",
    ),
    "objects": (
        "id",
        "canonical_name",
        "template_id",
        "template_version",
        "properties",
    ),
    "object_components": ("child_object_id", "parent_object_id", "slot_name"),
    "relationships": (
        "id",
        "relationship_definition_id",
        "relationship_definition_version",
        "properties",
    ),
    "runtime_relationship_resolutions": (
        "relationship_id",
        "relationship_definition_id",
        "resolution_id",
        "from_object_id",
        "to_object_id",
    ),
    "object_lifecycle_events": (
        "id",
        "occurred_at",
        "kind",
        "object_id",
        "canonical_name",
        "destination_object_id",
        "destination_canonical_name",
        "slot_declaring_template_id",
        "slot_name",
        "relationship_id",
        "relationship_definition_id",
        "relationship_name",
        "before_state",
        "after_state",
    ),
}

EXPECTED_EXPLICIT_INDEXES = {
    "ix_datatype_versions_status_datatype_version": (
        "datatype_versions",
        ("status", "datatype_id", "version"),
    ),
    "ix_object_template_properties_datatype_version": (
        "object_template_properties",
        ("datatype_id", "datatype_version"),
    ),
    "ix_object_template_properties_semantic_history": (
        "object_template_properties",
        ("template_id", "name", "template_version"),
    ),
    "ix_object_template_components_semantic_history": (
        "object_template_components",
        ("template_id", "name", "template_version"),
    ),
    "ix_object_template_versions_parent_version": (
        "object_template_versions",
        ("parent_template_id", "parent_version"),
    ),
    "ix_object_template_versions_status_template_version": (
        "object_template_versions",
        ("status", "template_id", "version"),
    ),
    "ix_object_templates_parent": ("object_templates", ("parent_template_id",)),
    "ix_object_template_components_target": (
        "object_template_components",
        ("target_template_id",),
    ),
    "ix_relationship_resolutions_from_template": (
        "relationship_resolutions",
        ("from_template_id",),
    ),
    "ix_relationship_resolutions_to_template": (
        "relationship_resolutions",
        ("to_template_id",),
    ),
    "ix_relationship_definition_versions_status_definition_version": (
        "relationship_definition_versions",
        ("status", "relationship_definition_id", "version"),
    ),
    "ix_relationship_definition_properties_datatype_version": (
        "relationship_definition_properties",
        ("datatype_id", "datatype_version"),
    ),
    "ix_relationship_definition_properties_semantic_history": (
        "relationship_definition_properties",
        (
            "relationship_definition_id",
            "name",
            "relationship_definition_version",
        ),
    ),
    "ix_relationship_resolutions_definition_id": (
        "relationship_resolutions",
        ("relationship_definition_id", "id"),
    ),
    "ix_relationship_resolutions_name_id": (
        "relationship_resolutions",
        ("name", "id"),
    ),
    "ix_objects_template_version": (
        "objects",
        ("template_id", "template_version"),
    ),
    "ix_objects_canonical_name_id": ("objects", ("canonical_name", "id")),
    "ix_object_components_parent_slot_child": (
        "object_components",
        ("parent_object_id", "slot_name", "child_object_id"),
    ),
    "ix_relationships_definition_version": (
        "relationships",
        ("relationship_definition_id", "relationship_definition_version"),
    ),
    "ix_runtime_resolutions_from_object_page": (
        "runtime_relationship_resolutions",
        ("from_object_id", "relationship_id", "to_object_id", "resolution_id"),
    ),
    "ix_runtime_resolutions_to_object_relationship": (
        "runtime_relationship_resolutions",
        ("to_object_id", "relationship_id"),
    ),
    "ix_runtime_resolutions_relationship": (
        "runtime_relationship_resolutions",
        ("relationship_id",),
    ),
    "ix_lifecycle_events_occurred": (
        "object_lifecycle_events",
        ("occurred_at", "id"),
    ),
    "ix_lifecycle_events_object": (
        "object_lifecycle_events",
        ("object_id", "occurred_at", "id"),
    ),
    "ix_lifecycle_events_destination": (
        "object_lifecycle_events",
        ("destination_object_id", "occurred_at", "id"),
    ),
    "ix_lifecycle_events_relationship": (
        "object_lifecycle_events",
        ("relationship_id", "occurred_at", "id"),
    ),
    "ix_lifecycle_events_definition": (
        "object_lifecycle_events",
        ("relationship_definition_id", "occurred_at", "id"),
    ),
    "ix_lifecycle_events_kind": (
        "object_lifecycle_events",
        ("kind", "occurred_at", "id"),
    ),
    "ix_lifecycle_events_relationship_name": (
        "object_lifecycle_events",
        ("relationship_name", "occurred_at", "id"),
    ),
}

FORBIDDEN_INDEXES = {
    "ix_relationships_definition",
    "ix_runtime_resolutions_from_object",
    "ix_runtime_resolutions_to_object",
    "ix_relationships_default_version",
    "ix_relationships_properties_gin",
    "ix_lifecycle_events_state_gin",
    "ix_lifecycle_events_event_set",
}


def _include_netauto_names(
    name: str | None, type_: str, parent_names: dict[str, str | None]
) -> bool:
    """Exclude unrelated external tables from NETAUTO metadata comparison."""
    del parent_names
    return type_ != "table" or name in EXPECTED_TABLES


@pytest.mark.postgresql
@pytest.mark.migration
def test_durable_root_structure_drift_repeatability_and_owned_downgrade(
    test_database_url: str,
) -> None:
    engine = create_engine(test_database_url)
    config = Config("alembic.ini")
    sentinel = "s01_external_sentinel"
    try:
        with engine.connect() as connection:
            config.attributes["connection"] = connection
            command.downgrade(config, "base")
            connection.execute(text(f"DROP TABLE IF EXISTS {sentinel}"))
            connection.execute(
                text(f"CREATE TABLE {sentinel} (id integer PRIMARY KEY)")
            )
            connection.commit()
            command.upgrade(config, "head")

        with engine.connect() as connection:
            inspector = inspect(connection)
            tables = set(inspector.get_table_names())
            assert EXPECTED_TABLES <= tables
            assert set(EXPECTED_COLUMNS) == EXPECTED_TABLES
            for table_name, expected_columns in EXPECTED_COLUMNS.items():
                assert (
                    tuple(
                        column["name"] for column in inspector.get_columns(table_name)
                    )
                    == expected_columns
                )

            explicit_indexes: dict[str, tuple[str, tuple[str, ...]]] = {}
            index_details: dict[str, ReflectedIndex] = {}
            for table_name in EXPECTED_TABLES:
                for index in inspector.get_indexes(table_name):
                    if index.get("duplicates_constraint") is not None:
                        continue
                    index_name = str(index["name"])
                    explicit_indexes[index_name] = (
                        table_name,
                        tuple(str(column) for column in index["column_names"]),
                    )
                    index_details[index_name] = index
            assert explicit_indexes == EXPECTED_EXPLICIT_INDEXES
            assert FORBIDDEN_INDEXES.isdisjoint(explicit_indexes)
            assert index_details["ix_runtime_resolutions_from_object_page"].get(
                "include_columns"
            ) == ["relationship_definition_id"]
            assert index_details[
                "ix_relationship_definition_properties_semantic_history"
            ].get("column_sorting") == {"relationship_definition_version": ("desc",)}
            for selector in (
                "destination_object_id",
                "relationship_id",
                "relationship_definition_id",
                "relationship_name",
            ):
                index_name = {
                    "destination_object_id": "ix_lifecycle_events_destination",
                    "relationship_id": "ix_lifecycle_events_relationship",
                    "relationship_definition_id": "ix_lifecycle_events_definition",
                    "relationship_name": "ix_lifecycle_events_relationship_name",
                }[selector]
                dialect_options = index_details[index_name].get("dialect_options")
                assert dialect_options is not None
                predicate = dialect_options["postgresql_where"]
                assert str(predicate).strip("()") == f"{selector} IS NOT NULL"

            assert inspector.get_pk_constraint("datatype_versions")[
                "constrained_columns"
            ] == ["datatype_id", "version"]
            assert inspector.get_pk_constraint("object_template_versions")[
                "constrained_columns"
            ] == ["template_id", "version"]
            assert inspector.get_pk_constraint("relationship_definition_versions")[
                "constrained_columns"
            ] == ["relationship_definition_id", "version"]
            assert inspector.get_pk_constraint("runtime_relationship_resolutions")[
                "constrained_columns"
            ] == ["resolution_id", "from_object_id", "to_object_id"]

            resolution_unique_constraints = {
                constraint["name"]: constraint["column_names"]
                for constraint in inspector.get_unique_constraints(
                    "relationship_resolutions"
                )
            }
            assert resolution_unique_constraints == {
                "uq_relationship_resolutions_id_definition": [
                    "id",
                    "relationship_definition_id",
                ]
            }
            assert all(
                not index["unique"] or "name" not in index["column_names"]
                for index in inspector.get_indexes("relationship_resolutions")
            )

            datatype_fks = {
                foreign_key["name"]
                for foreign_key in inspector.get_foreign_keys("datatypes")
            }
            assert datatype_fks == {"fk_datatypes_default_version"}
            runtime_fks = {
                foreign_key["name"]
                for foreign_key in inspector.get_foreign_keys(
                    "runtime_relationship_resolutions"
                )
            }
            assert runtime_fks == {
                "fk_runtime_resolutions_from_object",
                "fk_runtime_resolutions_relationship_definition",
                "fk_runtime_resolutions_resolution_definition",
                "fk_runtime_resolutions_to_object",
            }

            lifecycle_indexes = {
                index["name"]
                for index in inspector.get_indexes("object_lifecycle_events")
            }
            assert {
                "ix_lifecycle_events_kind",
                "ix_lifecycle_events_relationship_name",
                "ix_lifecycle_events_occurred",
            } <= lifecycle_indexes
            lifecycle_checks = {
                check["name"]
                for check in inspector.get_check_constraints("object_lifecycle_events")
            }
            assert {
                "ck_lifecycle_events_kind",
                "ck_lifecycle_events_family_shape",
                "ck_lifecycle_events_state_shape",
            } <= lifecycle_checks

            differences = compare_metadata(
                MigrationContext.configure(
                    connection,
                    opts={
                        "compare_type": True,
                        "include_name": _include_netauto_names,
                    },
                ),
                metadata,
            )
            assert differences == []

            script = ScriptDirectory.from_config(config)
            assert script.get_heads() == ["0001_m2_kernel"]
            assert script.get_base() == "0001_m2_kernel"
            assert [item.revision for item in script.walk_revisions()] == [
                "0001_m2_kernel"
            ]

            config.attributes["connection"] = connection
            command.downgrade(config, "base")
            at_base = set(inspect(connection).get_table_names())
            assert EXPECTED_TABLES.isdisjoint(at_base)
            assert sentinel in at_base
            command.upgrade(config, "head")
            assert EXPECTED_TABLES <= set(inspect(connection).get_table_names())

        with engine.connect() as connection:
            config.attributes["connection"] = connection
            command.downgrade(config, "base")
            remaining = set(inspect(connection).get_table_names())
            assert EXPECTED_TABLES.isdisjoint(remaining)
            assert sentinel in remaining
            connection.execute(text(f"DROP TABLE {sentinel}"))
            connection.commit()
    finally:
        with engine.connect() as connection:
            config.attributes["connection"] = connection
            command.downgrade(config, "base")
            connection.execute(text(f"DROP TABLE IF EXISTS {sentinel}"))
            connection.commit()
        engine.dispose()


@pytest.mark.postgresql
@pytest.mark.migration
def test_durable_root_failure_rolls_back_and_corrected_rerun_succeeds(
    test_database_url: str,
) -> None:
    engine = create_engine(test_database_url)
    config = Config("alembic.ini")
    injected = False

    def force_failure(
        _connection: object,
        _cursor: object,
        statement: str,
        _parameters: object,
        _context: object,
        _executemany: bool,
    ) -> None:
        nonlocal injected
        if not injected and "CREATE TABLE relationship_definitions" in statement:
            injected = True
            raise RuntimeError("forced durable-root DDL failure")

    try:
        with engine.connect() as connection:
            config.attributes["connection"] = connection
            command.downgrade(config, "base")
            event.listen(connection, "before_cursor_execute", force_failure)
            with pytest.raises(RuntimeError, match="forced durable-root DDL failure"):
                command.upgrade(config, "head")
            event.remove(connection, "before_cursor_execute", force_failure)
            connection.rollback()
            assert injected
            assert EXPECTED_TABLES.isdisjoint(inspect(connection).get_table_names())

            command.upgrade(config, "head")
            assert EXPECTED_TABLES <= set(inspect(connection).get_table_names())
            command.downgrade(config, "base")
            assert EXPECTED_TABLES.isdisjoint(inspect(connection).get_table_names())
    finally:
        with engine.connect() as connection:
            if event.contains(connection, "before_cursor_execute", force_failure):
                event.remove(connection, "before_cursor_execute", force_failure)
            config.attributes["connection"] = connection
            command.downgrade(config, "base")
        engine.dispose()
