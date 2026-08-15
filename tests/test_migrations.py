"""Real-PostgreSQL migration, schema structure, and drift verification."""

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text

from netauto.persistence.metadata import metadata
from tests.test_schema_metadata import EXPECTED_TABLES


def _include_netauto_names(
    name: str | None, type_: str, parent_names: dict[str, str | None]
) -> bool:
    """Exclude unrelated external tables from NETAUTO metadata comparison."""
    del parent_names
    return type_ != "table" or name in EXPECTED_TABLES


@pytest.mark.postgresql
@pytest.mark.migration
def test_initial_revision_structure_drift_and_owned_downgrade(
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

            assert inspector.get_pk_constraint("datatype_versions")[
                "constrained_columns"
            ] == ["datatype_id", "version"]
            assert inspector.get_pk_constraint("object_template_versions")[
                "constrained_columns"
            ] == ["template_id", "version"]
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

            config.attributes["connection"] = connection
            command.downgrade(config, "0001_m1_schema")
            restored = {
                constraint["name"]: constraint["column_names"]
                for constraint in inspect(connection).get_unique_constraints(
                    "relationship_resolutions"
                )
            }
            assert restored["uq_relationship_resolutions_semantic_child"] == [
                "relationship_definition_id",
                "from_template_id",
                "to_template_id",
                "name",
            ]
            command.upgrade(config, "head")
            upgraded = {
                constraint["name"]
                for constraint in inspect(connection).get_unique_constraints(
                    "relationship_resolutions"
                )
            }
            assert "uq_relationship_resolutions_semantic_child" not in upgraded

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
