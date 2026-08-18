"""Cheap S04 layer and hard-scope regressions."""

from dataclasses import fields
from pathlib import Path
from typing import cast

from netauto.domain.objects import Object
from netauto.entrypoints.api.errors import PUBLIC_STATUS_BY_CODE
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


def test_s08_closes_object_scope_with_only_object_delete() -> None:
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
    assert (
        "/api/v1/core/object-templates/{template_id}/relationship-capabilities" in paths
    )
    assert "/api/v1/core/objects/{object_id}/relationships" in paths
    object_methods = cast(dict[str, object], paths["/api/v1/core/objects/{object_id}"])
    assert set(object_methods) == {"get", "delete"}
    delete = _mapping(object_methods["delete"])
    assert "requestBody" not in delete
    assert set(_mapping(delete["responses"])) == {"204", "422"}


def test_lifecycle_response_schema_is_s07_discriminated_union() -> None:
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
            "RELATIONSHIP_CREATED": (
                "#/components/schemas/RelationshipCreatedLifecycleEventDto"
            ),
            "RELATIONSHIP_DATA_CHANGE": (
                "#/components/schemas/RelationshipChangedLifecycleEventDto"
            ),
            "RELATIONSHIP_SCHEMA_CHANGE": (
                "#/components/schemas/RelationshipChangedLifecycleEventDto"
            ),
            "RELATIONSHIP_DELETED": (
                "#/components/schemas/RelationshipDeletedLifecycleEventDto"
            ),
        },
    }
    assert event_union["oneOf"] == [
        {"$ref": "#/components/schemas/CreatedLifecycleEventDto"},
        {"$ref": "#/components/schemas/ChangedLifecycleEventDto"},
        {"$ref": "#/components/schemas/DeletedLifecycleEventDto"},
        {"$ref": "#/components/schemas/OwnershipLifecycleEventDto"},
        {"$ref": "#/components/schemas/RelationshipCreatedLifecycleEventDto"},
        {"$ref": "#/components/schemas/RelationshipChangedLifecycleEventDto"},
        {"$ref": "#/components/schemas/RelationshipDeletedLifecycleEventDto"},
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


def test_s08_public_route_and_error_catalog_closure() -> None:
    app = build_app(Settings(database_url="postgresql+psycopg://u:p@localhost/db"))
    paths = _mapping(_mapping(app.openapi())["paths"])
    actual_mutations = {
        (method.upper(), path)
        for path, raw_methods in paths.items()
        for method in _mapping(raw_methods)
        if method in {"post", "delete", "put", "patch"}
    }
    expected_mutations = {
        ("POST", "/api/v1/core/datatypes"),
        ("DELETE", "/api/v1/core/datatypes/{datatype_id}"),
        ("POST", "/api/v1/core/datatypes/{datatype_id}/clear-default"),
        ("POST", "/api/v1/core/datatypes/{datatype_id}/create-next"),
        ("POST", "/api/v1/core/datatypes/{datatype_id}/set-default"),
        ("POST", "/api/v1/core/datatypes/{datatype_id}/set-description"),
        ("DELETE", "/api/v1/core/datatypes/{datatype_id}/versions/{version}"),
        ("POST", "/api/v1/core/datatypes/{datatype_id}/versions/{version}/deprecate"),
        ("POST", "/api/v1/core/datatypes/{datatype_id}/versions/{version}/publish"),
        ("POST", "/api/v1/core/datatypes/{datatype_id}/versions/{version}/revise"),
        ("POST", "/api/v1/core/object-templates"),
        ("DELETE", "/api/v1/core/object-templates/{template_id}"),
        ("POST", "/api/v1/core/object-templates/{template_id}/clear-default"),
        ("POST", "/api/v1/core/object-templates/{template_id}/create-next"),
        ("POST", "/api/v1/core/object-templates/{template_id}/set-default"),
        ("POST", "/api/v1/core/object-templates/{template_id}/set-description"),
        ("DELETE", "/api/v1/core/object-templates/{template_id}/versions/{version}"),
        (
            "POST",
            "/api/v1/core/object-templates/{template_id}/versions/{version}/deprecate",
        ),
        (
            "POST",
            "/api/v1/core/object-templates/{template_id}/versions/{version}/publish",
        ),
        (
            "POST",
            "/api/v1/core/object-templates/{template_id}/versions/{version}/revise",
        ),
        ("POST", "/api/v1/core/objects"),
        ("DELETE", "/api/v1/core/objects/{object_id}"),
        ("POST", "/api/v1/core/objects/{object_id}/data-change"),
        ("POST", "/api/v1/core/objects/{object_id}/rename"),
        ("POST", "/api/v1/core/objects/{object_id}/schema-change"),
        ("POST", "/api/v1/core/objects/{parent_object_id}/attach"),
        ("POST", "/api/v1/core/objects/{parent_object_id}/detach"),
        ("POST", "/api/v1/core/relationship-definitions"),
        (
            "DELETE",
            "/api/v1/core/relationship-definitions/{relationship_definition_id}",
        ),
        (
            "POST",
            "/api/v1/core/relationship-definitions/{relationship_definition_id}/rename",
        ),
        (
            "POST",
            "/api/v1/core/relationship-definitions/{relationship_definition_id}/create-next",
        ),
        (
            "POST",
            "/api/v1/core/relationship-definitions/{relationship_definition_id}/set-default",
        ),
        (
            "POST",
            "/api/v1/core/relationship-definitions/{relationship_definition_id}/clear-default",
        ),
        (
            "POST",
            "/api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}/revise",
        ),
        (
            "POST",
            "/api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}/publish",
        ),
        (
            "POST",
            "/api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}/deprecate",
        ),
        (
            "DELETE",
            "/api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}",
        ),
        ("POST", "/api/v1/core/relationships"),
        ("DELETE", "/api/v1/core/relationships/{relationship_id}"),
    }
    assert len(expected_mutations) == 39
    assert actual_mutations == expected_mutations

    expected_reads = {
        ("GET", "/api/v1/core/datatypes"),
        ("GET", "/api/v1/core/datatypes/{datatype_id}"),
        ("GET", "/api/v1/core/datatypes/{datatype_id}/versions"),
        ("GET", "/api/v1/core/datatypes/{datatype_id}/versions/{version}"),
        ("GET", "/api/v1/core/lifecycle-events"),
        ("GET", "/api/v1/core/object-templates"),
        ("GET", "/api/v1/core/object-templates/{template_id}"),
        (
            "GET",
            "/api/v1/core/object-templates/{template_id}/relationship-capabilities",
        ),
        ("GET", "/api/v1/core/object-templates/{template_id}/versions"),
        ("GET", "/api/v1/core/object-templates/{template_id}/versions/{version}"),
        (
            "GET",
            "/api/v1/core/object-templates/{template_id}/versions/{version}/effective-schema",
        ),
        ("GET", "/api/v1/core/objects"),
        ("GET", "/api/v1/core/objects/{child_object_id}/owner"),
        ("GET", "/api/v1/core/objects/{object_id}"),
        ("GET", "/api/v1/core/objects/{object_id}/lifecycle-events"),
        ("GET", "/api/v1/core/objects/{object_id}/relationships"),
        ("GET", "/api/v1/core/objects/{parent_object_id}/components"),
        ("GET", "/api/v1/core/relationship-definitions"),
        (
            "GET",
            "/api/v1/core/relationship-definitions/{relationship_definition_id}",
        ),
        (
            "GET",
            "/api/v1/core/relationship-definitions/{relationship_definition_id}/versions",
        ),
        (
            "GET",
            "/api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}",
        ),
        ("GET", "/api/v1/core/relationships/{relationship_id}"),
    }
    actual_reads = {
        ("GET", path) for path, methods in paths.items() if "get" in _mapping(methods)
    }
    assert actual_reads == expected_reads
    assert all(
        method not in {"put", "patch"}
        for methods in paths.values()
        for method in _mapping(methods)
    )
    forbidden_fragments = {
        "/actions",
        "runtime-relationship-resolutions",
        "object-components",
        "json-schema",
    }
    assert all(
        fragment not in path for fragment in forbidden_fragments for path in paths
    )

    assert PUBLIC_STATUS_BY_CODE == {
        "invalid_request": 400,
        "invalid_cursor": 400,
        "resource_not_found": 404,
        "referenced_resource_not_found": 422,
        "semantic_validation_failed": 422,
        "stale_revision": 409,
        "lifecycle_state_conflict": 409,
        "version_source_conflict": 409,
        "default_version_unavailable": 409,
        "dependency_not_admissible": 409,
        "qualified_name_conflict": 409,
        "default_version_conflict": 409,
        "active_dependency_conflict": 409,
        "delete_blocked": 409,
        "ownership_slot_unavailable": 409,
        "ownership_conflict": 409,
        "ownership_mismatch": 409,
        "ownership_cycle": 409,
        "schema_change_blocked": 409,
        "relationship_definition_equivalent": 409,
        "relationship_definition_conflict": 409,
        "relationship_fact_conflict": 409,
        "internal_error": 500,
    }
