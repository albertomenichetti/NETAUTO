"""Static assertions for the frozen M1 SQLAlchemy metadata authority."""

from sqlalchemy import UniqueConstraint

from netauto.persistence.metadata import metadata

EXPECTED_TABLES = {
    "datatypes",
    "datatype_versions",
    "object_templates",
    "object_template_versions",
    "object_template_properties",
    "object_template_components",
    "relationship_definitions",
    "relationship_resolutions",
    "objects",
    "object_components",
    "relationships",
    "runtime_relationship_resolutions",
    "object_lifecycle_events",
}


def test_metadata_contains_exactly_the_frozen_thirteen_tables() -> None:
    assert set(metadata.tables) == EXPECTED_TABLES


def test_relationship_resolution_name_is_not_part_of_a_unique_key() -> None:
    table = metadata.tables["relationship_resolutions"]
    unique_column_sets = {
        tuple(column.name for column in constraint.columns)
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert ("id", "relationship_definition_id") in unique_column_sets
    assert all("name" not in columns for columns in unique_column_sets)
    assert all(
        not index.unique or "name" not in index.columns.keys()
        for index in table.indexes
    )
