"""Cheap S04 layer and hard-scope regressions."""

from dataclasses import fields
from pathlib import Path
from typing import cast

from netauto.domain.objects import Object
from netauto.entrypoints.http import build_app
from netauto.settings import Settings

ROOT = Path(__file__).parents[1]


def _mapping(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    raw = cast(dict[object, object], value)
    assert all(isinstance(key, str) for key in raw)
    return cast(dict[str, object], raw)


def test_object_intrinsic_snapshot_has_only_frozen_fields() -> None:
    assert [field.name for field in fields(Object)] == [
        "id",
        "canonical_name",
        "template_id",
        "template_version",
        "properties",
    ]


def test_object_domain_and_application_preserve_layer_boundaries() -> None:
    for relative in (
        "src/netauto/domain/objects.py",
        "src/netauto/application/objects.py",
    ):
        source = (ROOT / relative).read_text()
        assert "sqlalchemy" not in source
        assert "fastapi" not in source
        assert "pydantic" not in source
        assert "Session" not in source
        assert "state_revision" not in source
        assert "JSON Schema" not in source


def test_s05_registers_only_ownership_and_schema_change_capabilities() -> None:
    app = build_app(Settings(database_url="postgresql+psycopg://u:p@localhost/db"))
    schema = cast(dict[str, object], app.openapi())
    paths = cast(dict[str, object], schema["paths"])
    expected = {
        "/api/v1/core/objects",
        "/api/v1/core/objects/{object_id}",
        "/api/v1/core/objects/{object_id}/rename",
        "/api/v1/core/objects/{object_id}/data-change",
        "/api/v1/core/lifecycle-events",
        "/api/v1/core/objects/{object_id}/lifecycle-events",
        "/api/v1/core/objects/{object_id}/schema-change",
        "/api/v1/core/objects/{parent_object_id}/attach",
        "/api/v1/core/objects/{parent_object_id}/detach",
        "/api/v1/core/objects/{parent_object_id}/components",
        "/api/v1/core/objects/{child_object_id}/owner",
    }
    assert expected <= set(paths)
    for suffix in (
        "/relationships",
        "/relationship-capabilities",
    ):
        assert not any(path.endswith(suffix) for path in paths)
    object_methods = cast(dict[str, object], paths["/api/v1/core/objects/{object_id}"])
    assert "delete" not in object_methods


def test_lifecycle_response_schema_is_s05_discriminated_union() -> None:
    app = build_app(Settings(database_url="postgresql+psycopg://u:p@localhost/db"))
    schema = _mapping(app.openapi())
    paths = _mapping(schema["paths"])
    lifecycle_path = _mapping(paths["/api/v1/core/lifecycle-events"])
    operation = _mapping(lifecycle_path["get"])
    responses = _mapping(operation["responses"])
    success = _mapping(responses["200"])
    content = _mapping(success["content"])
    media_type = _mapping(content["application/json"])
    assert _mapping(media_type["schema"]) == {
        "$ref": "#/components/schemas/LifecyclePageDto"
    }

    components = _mapping(schema["components"])
    schemas = _mapping(components["schemas"])
    page = _mapping(schemas["LifecyclePageDto"])
    properties = _mapping(page["properties"])
    items = _mapping(properties["items"])
    assert _mapping(items["items"]) == {
        "$ref": "#/components/schemas/LifecycleEventDto"
    }
    event_union = _mapping(schemas["LifecycleEventDto"])
    assert event_union["discriminator"] == {
        "propertyName": "kind",
        "mapping": {
            "CREATED": "#/components/schemas/CreatedLifecycleEventDto",
            "DATA_CHANGE": "#/components/schemas/ChangedLifecycleEventDto",
            "DELETED": "#/components/schemas/DeletedLifecycleEventDto",
            "RENAME": "#/components/schemas/ChangedLifecycleEventDto",
            "SCHEMA_CHANGE": "#/components/schemas/ChangedLifecycleEventDto",
            "ATTACH_TO": "#/components/schemas/OwnershipLifecycleEventDto",
            "DETACH_FROM": "#/components/schemas/OwnershipLifecycleEventDto",
        },
    }
    assert event_union["oneOf"] == [
        {"$ref": "#/components/schemas/CreatedLifecycleEventDto"},
        {"$ref": "#/components/schemas/ChangedLifecycleEventDto"},
        {"$ref": "#/components/schemas/DeletedLifecycleEventDto"},
        {"$ref": "#/components/schemas/OwnershipLifecycleEventDto"},
    ]

    intrinsic_schema_text = repr(
        {
            name: schemas[name]
            for name in (
                "CreatedLifecycleEventDto",
                "ChangedLifecycleEventDto",
                "DeletedLifecycleEventDto",
                "OwnershipLifecycleEventDto",
            )
        }
    )
    for intrinsic_kind in (
        "CREATED",
        "RENAME",
        "DATA_CHANGE",
        "SCHEMA_CHANGE",
        "DELETED",
        "ATTACH_TO",
        "DETACH_FROM",
    ):
        assert intrinsic_kind in intrinsic_schema_text
    for excluded_kind in (
        "RELATIONSHIP_CREATED",
        "RELATIONSHIP_DELETED",
    ):
        assert excluded_kind not in intrinsic_schema_text
