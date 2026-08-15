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


def test_persist_15_lifecycle_read_indices_match_frozen_shapes() -> None:
    table = metadata.tables["object_lifecycle_events"]
    indices = {str(index.name): index for index in table.indexes}
    expected = {
        "ix_lifecycle_events_occurred": ("occurred_at", "id"),
        "ix_lifecycle_events_object": ("object_id", "occurred_at", "id"),
        "ix_lifecycle_events_destination": (
            "destination_object_id",
            "occurred_at",
            "id",
        ),
        "ix_lifecycle_events_relationship": (
            "relationship_id",
            "occurred_at",
            "id",
        ),
        "ix_lifecycle_events_definition": (
            "relationship_definition_id",
            "occurred_at",
            "id",
        ),
        "ix_lifecycle_events_kind": ("kind", "occurred_at", "id"),
        "ix_lifecycle_events_relationship_name": (
            "relationship_name",
            "occurred_at",
            "id",
        ),
    }
    assert {
        name: tuple(index.columns.keys())
        for name, index in indices.items()
        if name in expected
    } == expected
    name_index = indices["ix_lifecycle_events_relationship_name"]
    assert str(name_index.dialect_options["postgresql"]["where"]) == (
        "object_lifecycle_events.relationship_name IS NOT NULL"
    )
