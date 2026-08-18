"""Cheap S06 layer and public-surface regressions."""

from dataclasses import fields
from pathlib import Path
from typing import cast

from netauto.domain.relationships import (
    RelationshipDefinition,
    RelationshipResolution,
)
from netauto.entrypoints.http import build_app
from netauto.persistence.gates import AdvisoryGate
from netauto.settings import Settings

ROOT = Path(__file__).parents[1]


def test_relationship_aggregate_has_only_frozen_model_plane_fields() -> None:
    assert [field.name for field in fields(RelationshipDefinition)] == [
        "id",
        "symmetric",
        "resolutions",
        "default_version",
    ]
    assert [field.name for field in fields(RelationshipResolution)] == [
        "id",
        "relationship_definition_id",
        "from_template_id",
        "to_template_id",
        "name",
    ]


def test_relationship_domain_and_application_preserve_layer_boundaries() -> None:
    for relative in (
        "src/netauto/domain/relationships.py",
        "src/netauto/application/relationshipdefinitions.py",
    ):
        source = (ROOT / relative).read_text()
        assert "sqlalchemy" not in source
        assert "fastapi" not in source
        assert "pydantic" not in source
        assert "Session" not in source
        assert "source_template" not in source
        assert "target_template" not in source
        assert "forward_name" not in source
        assert "reverse_name" not in source


def test_s07_registers_runtime_routes_without_resolution_crud() -> None:
    app = build_app(Settings(database_url="postgresql+psycopg://u:p@localhost/db"))
    schema = cast(dict[str, object], app.openapi())
    paths = cast(dict[str, object], schema["paths"])
    assert {
        "/api/v1/core/relationship-definitions",
        "/api/v1/core/relationship-definitions/{relationship_definition_id}",
        "/api/v1/core/relationship-definitions/{relationship_definition_id}/rename",
        "/api/v1/core/object-templates/{template_id}/relationship-capabilities",
    } <= set(paths)
    assert {
        "/api/v1/core/relationships",
        "/api/v1/core/relationships/{relationship_id}",
        "/api/v1/core/objects/{object_id}/relationships",
    } <= set(paths)
    forbidden = {
        "/api/v1/core/relationship-resolutions",
        "/api/v1/core/relationship-resolutions/{resolution_id}",
    }
    assert forbidden.isdisjoint(paths)


def test_m2_s01_keeps_three_gates_and_installs_one_durable_root() -> None:
    assert list(AdvisoryGate) == [
        AdvisoryGate.OWNERSHIP_GRAPH_WRITE_GATE,
        AdvisoryGate.RELATIONSHIP_DEFINITION_CONFLICT_GATE,
        AdvisoryGate.MODEL_ROOT_DELETE_GATE,
    ]
    migrations = sorted((ROOT / "src/netauto/migrations/versions").glob("*.py"))
    assert [item.name for item in migrations] == [
        "0001_m2_durable_kernel.py",
        "__init__.py",
    ]
