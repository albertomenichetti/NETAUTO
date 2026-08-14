"""Static assertions for the frozen M1 SQLAlchemy metadata authority."""

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
