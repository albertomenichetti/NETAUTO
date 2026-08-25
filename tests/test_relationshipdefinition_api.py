"""Real-PostgreSQL API coverage for the S06 Relationship model plane."""

from collections.abc import AsyncIterator
from typing import cast
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import Engine

from netauto.entrypoints.http import build_app
from netauto.persistence.metadata import (
    datatype_versions,
    object_template_versions,
    relationship_definition_versions,
    relationship_definitions,
    relationships,
)
from netauto.settings import Settings


@pytest.fixture
async def relationshipdefinition_client(
    migrated_database_engine: Engine, test_database_url: str
) -> AsyncIterator[httpx.AsyncClient]:
    del migrated_database_engine
    app = build_app(Settings(database_url=test_database_url))
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            yield client


async def _template(
    client: httpx.AsyncClient,
    name: str,
    *,
    abstract: bool = False,
    parent_template_id: str | None = None,
) -> str:
    body: dict[str, object] = {
        "namespace": "relationship_test",
        "name": name,
        "abstract": abstract,
    }
    if parent_template_id is not None:
        body["parent_template_id"] = parent_template_id
    response = await client.post("/api/v1/core/object-templates", json=body)
    assert response.status_code == 201, response.text
    return cast(str, response.json()["object_template"]["id"])


async def _non_symmetric(
    client: httpx.AsyncClient,
    first_template_id: str,
    second_template_id: str,
    first_name: str,
    second_name: str,
) -> httpx.Response:
    return await client.post(
        "/api/v1/core/relationship-definitions",
        json={
            "symmetric": False,
            "perspectives": [
                {"template_id": first_template_id, "name": first_name},
                {"template_id": second_template_id, "name": second_name},
            ],
        },
    )


def _created_definition(response: httpx.Response) -> dict[str, object]:
    payload = cast(dict[str, object], response.json())
    return cast(dict[str, object], payload["relationship_definition"])


async def _publish_v1(client: httpx.AsyncClient, definition_id: object) -> None:
    published = await client.post(
        f"/api/v1/core/relationship-definitions/{definition_id}/versions/1/publish",
        params={"expected_revision": 1},
    )
    assert published.status_code == 200, published.text


async def _published_integer_datatype(client: httpx.AsyncClient, name: str) -> str:
    created = await client.post(
        "/api/v1/core/datatypes",
        json={
            "namespace": "relationship_test",
            "name": name,
            "base_type": "core.integer",
        },
    )
    assert created.status_code == 201, created.text
    datatype_id = cast(str, created.json()["datatype"]["id"])
    published = await client.post(
        f"/api/v1/core/datatypes/{datatype_id}/versions/1/publish",
        params={"expected_revision": 1},
    )
    assert published.status_code == 200, published.text
    return datatype_id


async def _publish_template(client: httpx.AsyncClient, template_id: str) -> None:
    response = await client.post(
        f"/api/v1/core/object-templates/{template_id}/versions/1/publish",
        params={"expected_revision": 1},
    )
    assert response.status_code == 200, response.text


async def _object(
    client: httpx.AsyncClient, template_id: str, canonical_name: str
) -> str:
    response = await client.post(
        "/api/v1/core/objects",
        json={
            "template_id": template_id,
            "template_version": 1,
            "canonical_name": canonical_name,
            "properties": {},
        },
    )
    assert response.status_code == 201, response.text
    return cast(str, response.json()["id"])


@pytest.mark.api
@pytest.mark.postgresql
async def test_relationship_definition_complete_crud_and_capability_projection(
    relationshipdefinition_client: httpx.AsyncClient,
) -> None:
    client = relationshipdefinition_client
    first_template_id = await _template(client, "endpoint_a", abstract=True)
    second_template_id = await _template(client, "endpoint_b")

    created = await _non_symmetric(
        client,
        first_template_id,
        second_template_id,
        "hosts",
        "hosted_by",
    )
    assert created.status_code == 201, created.text
    payload = created.json()
    value = _created_definition(created)
    definition_id = cast(str, value["id"])
    resolutions = cast(list[dict[str, object]], value["resolutions"])
    assert payload["version"] == {
        "relationship_definition_id": definition_id,
        "version": 1,
        "revision": 1,
        "status": "DRAFT",
        "properties": [],
    }
    assert created.headers["location"].endswith(definition_id)
    assert value["symmetric"] is False
    assert len(resolutions) == 2
    assert all("relationship_definition_id" not in item for item in resolutions)
    assert all("forward" not in item and "reverse" not in item for item in value)

    exact = await client.get(f"/api/v1/core/relationship-definitions/{definition_id}")
    assert exact.status_code == 200
    assert exact.json() == value

    rename_body = {
        "resolutions": [
            {
                "resolution_id": item["resolution_id"],
                "name": "owns" if item["name"] == "hosts" else "owned_by",
            }
            for item in reversed(resolutions)
        ]
    }
    renamed = await client.post(
        f"/api/v1/core/relationship-definitions/{definition_id}/rename",
        json=rename_body,
    )
    assert renamed.status_code == 200, renamed.text
    assert {item["name"] for item in renamed.json()["resolutions"]} == {
        "owns",
        "owned_by",
    }

    listed = await client.get("/api/v1/core/relationship-definitions")
    assert listed.status_code == 200
    assert listed.json() == {"items": [renamed.json()], "next_cursor": None}

    await _publish_v1(client, definition_id)

    capabilities = await client.get(
        f"/api/v1/core/object-templates/{first_template_id}/relationship-capabilities"
    )
    assert capabilities.status_code == 200, capabilities.text
    assert len(capabilities.json()["items"]) == 1
    capability = capabilities.json()["items"][0]
    assert set(capability) == {
        "resolution_id",
        "relationship_definition_id",
        "name",
        "from_template_id",
        "to_template_id",
        "default_version",
    }
    assert capability["relationship_definition_id"] == definition_id
    assert capability["default_version"] == 1

    deleted = await client.delete(
        f"/api/v1/core/relationship-definitions/{definition_id}"
    )
    assert deleted.status_code == 204
    missing = await client.get(f"/api/v1/core/relationship-definitions/{definition_id}")
    assert missing.status_code == 404
    assert missing.json()["code"] == "resource_not_found"


@pytest.mark.api
@pytest.mark.postgresql
async def test_relationship_definition_strict_shapes_and_finite_failures(
    relationshipdefinition_client: httpx.AsyncClient,
) -> None:
    client = relationshipdefinition_client
    first_template_id = await _template(client, "strict_a")
    second_template_id = await _template(client, "strict_b")

    coerced = await client.post(
        "/api/v1/core/relationship-definitions",
        json={
            "symmetric": 0,
            "perspectives": [
                {"template_id": first_template_id, "name": "left"},
                {"template_id": second_template_id, "name": "right"},
            ],
        },
    )
    assert coerced.status_code == 400
    malformed = await client.post(
        "/api/v1/core/relationship-definitions",
        json={
            "symmetric": True,
            "endpoint_template_ids": [first_template_id],
            "name": "peer",
        },
    )
    assert malformed.status_code == 400
    semantic = await _non_symmetric(
        client, first_template_id, second_template_id, "duplicate", "duplicate"
    )
    assert semantic.status_code == 422
    assert semantic.json()["code"] == "semantic_validation_failed"
    missing = await client.post(
        "/api/v1/core/relationship-definitions",
        json={
            "symmetric": True,
            "endpoint_template_ids": [first_template_id, str(uuid4())],
            "name": "missing_endpoint",
        },
    )
    assert missing.status_code == 422
    assert missing.json()["code"] == "referenced_resource_not_found"

    created = await _non_symmetric(
        client, first_template_id, second_template_id, "hosts", "hosted_by"
    )
    assert created.status_code == 201
    definition = _created_definition(created)
    equivalent = await _non_symmetric(
        client, second_template_id, first_template_id, "hosted_by", "hosts"
    )
    assert equivalent.status_code == 409
    assert equivalent.json()["code"] == "relationship_definition_equivalent"
    conflict = await client.post(
        "/api/v1/core/relationship-definitions",
        json={
            "symmetric": True,
            "endpoint_template_ids": [first_template_id, second_template_id],
            "name": "hosts",
        },
    )
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "relationship_definition_conflict"

    wrong_shape = await client.post(
        f"/api/v1/core/relationship-definitions/{definition['id']}/rename",
        json={"name": "renamed"},
    )
    assert wrong_shape.status_code == 422
    definition_resolutions = cast(list[dict[str, object]], definition["resolutions"])
    duplicate_id = definition_resolutions[0]["resolution_id"]
    duplicate_rename = await client.post(
        f"/api/v1/core/relationship-definitions/{definition['id']}/rename",
        json={
            "resolutions": [
                {"resolution_id": duplicate_id, "name": "one"},
                {"resolution_id": duplicate_id, "name": "two"},
            ]
        },
    )
    assert duplicate_rename.status_code == 400
    wrong_membership = await client.post(
        f"/api/v1/core/relationship-definitions/{definition['id']}/rename",
        json={
            "resolutions": [
                {
                    "resolution_id": definition_resolutions[0]["resolution_id"],
                    "name": "one",
                },
                {"resolution_id": str(uuid4()), "name": "two"},
            ]
        },
    )
    assert wrong_membership.status_code == 422
    assert wrong_membership.json()["code"] == "semantic_validation_failed"
    body_delete = await client.request(
        "DELETE",
        f"/api/v1/core/relationship-definitions/{definition['id']}",
        json={"force": True},
    )
    assert body_delete.status_code == 400


@pytest.mark.api
@pytest.mark.postgresql
async def test_capability_inheritance_filter_pagination_and_cursor_identity(
    relationshipdefinition_client: httpx.AsyncClient,
) -> None:
    client = relationshipdefinition_client
    root_id = await _template(client, "capability_root", abstract=True)
    published = await client.post(
        f"/api/v1/core/object-templates/{root_id}/versions/1/publish",
        params={"expected_revision": 1},
    )
    assert published.status_code == 200
    child_id = await _template(client, "capability_child", parent_template_id=root_id)
    created = await _non_symmetric(client, root_id, root_id, "parents", "children")
    assert created.status_code == 201, created.text
    await _publish_v1(client, _created_definition(created)["id"])
    overlap_conflict = await client.post(
        "/api/v1/core/relationship-definitions",
        json={
            "symmetric": True,
            "endpoint_template_ids": [child_id, child_id],
            "name": "parents",
        },
    )
    assert overlap_conflict.status_code == 409
    assert overlap_conflict.json()["code"] == "relationship_definition_conflict"

    first_page = await client.get(
        f"/api/v1/core/object-templates/{child_id}/relationship-capabilities",
        params={"limit": 1},
    )
    assert first_page.status_code == 200, first_page.text
    first_payload = first_page.json()
    assert len(first_payload["items"]) == 1
    assert first_payload["next_cursor"] is not None
    second_page = await client.get(
        f"/api/v1/core/object-templates/{child_id}/relationship-capabilities",
        params={"limit": 500, "cursor": first_payload["next_cursor"]},
    )
    assert second_page.status_code == 200
    all_items = first_payload["items"] + second_page.json()["items"]
    assert len(all_items) == 2
    assert len({item["resolution_id"] for item in all_items}) == 2
    assert all(item["from_template_id"] == root_id for item in all_items)

    filtered = await client.get(
        f"/api/v1/core/object-templates/{child_id}/relationship-capabilities",
        params={"name": "parents"},
    )
    assert filtered.status_code == 200
    assert [item["name"] for item in filtered.json()["items"]] == ["parents"]
    invalid_cursor = await client.get(
        f"/api/v1/core/object-templates/{child_id}/relationship-capabilities",
        params={"name": "parents", "cursor": first_payload["next_cursor"]},
    )
    assert invalid_cursor.status_code == 400
    assert invalid_cursor.json()["code"] == "invalid_cursor"

    missing = await client.get(
        f"/api/v1/core/object-templates/{uuid4()}/relationship-capabilities"
    )
    assert missing.status_code == 404


@pytest.mark.api
@pytest.mark.postgresql
async def test_definition_references_block_lineage_and_factual_rows_block_delete(
    relationshipdefinition_client: httpx.AsyncClient,
    migrated_database_engine: Engine,
) -> None:
    client = relationshipdefinition_client
    template_id = await _template(client, "reference_endpoint", abstract=True)
    created = await client.post(
        "/api/v1/core/relationship-definitions",
        json={
            "symmetric": True,
            "endpoint_template_ids": [template_id, template_id],
            "name": "self_link",
        },
    )
    assert created.status_code == 201, created.text
    definition_id = UUID(cast(str, _created_definition(created)["id"]))
    await _publish_v1(client, definition_id)

    blocked_lineage = await client.delete(
        f"/api/v1/core/object-templates/{template_id}"
    )
    assert blocked_lineage.status_code == 409
    assert blocked_lineage.json()["code"] == "delete_blocked"

    with migrated_database_engine.begin() as connection:
        connection.execute(
            relationships.insert(),
            [
                {
                    "id": uuid4(),
                    "relationship_definition_id": definition_id,
                    "relationship_definition_version": 1,
                    "properties": {},
                },
                {
                    "id": uuid4(),
                    "relationship_definition_id": definition_id,
                    "relationship_definition_version": 1,
                    "properties": {},
                },
            ],
        )
    blocked_definition = await client.delete(
        f"/api/v1/core/relationship-definitions/{definition_id}"
    )
    assert blocked_definition.status_code == 409
    assert blocked_definition.json() == {
        "code": "delete_blocked",
        "message": "Current Relationships prevent RelationshipDefinition deletion.",
        "details": {
            "resource_type": "relationship_definition",
            "id": str(definition_id),
            "blockers": [{"type": "relationship", "count": 2}],
        },
    }


@pytest.mark.api
@pytest.mark.postgresql
async def test_corrupted_definition_aggregate_maps_to_internal_error(
    relationshipdefinition_client: httpx.AsyncClient,
    migrated_database_engine: Engine,
) -> None:
    definition_id = uuid4()
    with migrated_database_engine.begin() as connection:
        connection.execute(
            relationship_definitions.insert().values(id=definition_id, symmetric=False)
        )
    response = await relationshipdefinition_client.get(
        f"/api/v1/core/relationship-definitions/{definition_id}"
    )
    assert response.status_code == 500
    assert response.json() == {
        "code": "internal_error",
        "message": "A persisted RelationshipDefinition aggregate is invalid.",
        "details": {},
    }
    template_id = await _template(
        relationshipdefinition_client, "corrupt_certified_set_operand"
    )
    certification = await relationshipdefinition_client.post(
        "/api/v1/core/relationship-definitions",
        json={
            "symmetric": True,
            "endpoint_template_ids": [template_id, template_id],
            "name": "cannot_certify",
        },
    )
    assert certification.status_code == 500
    assert certification.json()["code"] == "internal_error"


@pytest.mark.api
@pytest.mark.postgresql
async def test_definition_list_uses_id_keyset_cursor_and_complete_items(
    relationshipdefinition_client: httpx.AsyncClient,
) -> None:
    client = relationshipdefinition_client
    first_template_id = await _template(client, "list_first")
    second_template_id = await _template(client, "list_second")
    first = await client.post(
        "/api/v1/core/relationship-definitions",
        json={
            "symmetric": True,
            "endpoint_template_ids": [first_template_id, first_template_id],
            "name": "first_capability",
        },
    )
    second = await client.post(
        "/api/v1/core/relationship-definitions",
        json={
            "symmetric": True,
            "endpoint_template_ids": [second_template_id, second_template_id],
            "name": "second_capability",
        },
    )
    assert first.status_code == second.status_code == 201

    first_page = await client.get(
        "/api/v1/core/relationship-definitions", params={"limit": 1}
    )
    assert first_page.status_code == 200
    first_payload = first_page.json()
    assert len(first_payload["items"]) == 1
    assert len(first_payload["items"][0]["resolutions"]) == 1
    assert first_payload["next_cursor"] is not None
    second_page = await client.get(
        "/api/v1/core/relationship-definitions",
        params={"cursor": first_payload["next_cursor"], "limit": 500},
    )
    assert second_page.status_code == 200
    combined = first_payload["items"] + second_page.json()["items"]
    assert [item["id"] for item in combined] == sorted(
        (
            cast(str, _created_definition(first)["id"]),
            cast(str, _created_definition(second)["id"]),
        )
    )


@pytest.mark.api
@pytest.mark.postgresql
async def test_m2_s01_rdv_properties_versions_defaults_and_factual_pin(
    relationshipdefinition_client: httpx.AsyncClient,
) -> None:
    client = relationshipdefinition_client
    datatype_id = await _published_integer_datatype(client, "rdv_value")
    first_template_id = await _template(client, "rdv_endpoint_a")
    second_template_id = await _template(client, "rdv_endpoint_b")
    await _publish_template(client, first_template_id)
    await _publish_template(client, second_template_id)

    property_body = {
        "name": "measurements",
        "position": 1,
        "datatype_id": datatype_id,
        "value_mode": "SCALAR",
    }
    created = await client.post(
        "/api/v1/core/relationship-definitions",
        json={
            "symmetric": False,
            "perspectives": [
                {"template_id": first_template_id, "name": "measures"},
                {"template_id": second_template_id, "name": "measured_by"},
            ],
            "properties": [property_body],
        },
    )
    assert created.status_code == 201, created.text
    payload = created.json()
    definition = payload["relationship_definition"]
    definition_id = definition["id"]
    assert definition["default_version"] is None
    assert payload["version"] == {
        "relationship_definition_id": definition_id,
        "version": 1,
        "revision": 1,
        "status": "DRAFT",
        "properties": [
            {
                **property_body,
                "datatype_version": 1,
            }
        ],
    }

    capabilities = await client.get(
        f"/api/v1/core/object-templates/{first_template_id}/relationship-capabilities"
    )
    assert capabilities.status_code == 200
    assert capabilities.json()["items"] == []

    null_pin = await client.post(
        f"/api/v1/core/relationship-definitions/{definition_id}/versions/1/revise",
        params={"expected_revision": 1},
        json={"properties": [{**property_body, "datatype_version": None}]},
    )
    assert null_pin.status_code == 400
    assert null_pin.json()["code"] == "invalid_request"

    revised = await client.post(
        f"/api/v1/core/relationship-definitions/{definition_id}/versions/1/revise",
        params={"expected_revision": 1},
        json={"properties": [property_body]},
    )
    assert revised.status_code == 200, revised.text
    assert revised.json()["revision"] == 2
    stale = await client.post(
        f"/api/v1/core/relationship-definitions/{definition_id}/versions/1/publish",
        params={"expected_revision": 1},
    )
    assert stale.status_code == 409
    assert stale.json()["code"] == "stale_revision"
    published = await client.post(
        f"/api/v1/core/relationship-definitions/{definition_id}/versions/1/publish",
        params={"expected_revision": 2},
    )
    assert published.status_code == 200, published.text
    assert published.json()["status"] == "PUBLISHED"

    next_version = await client.post(
        f"/api/v1/core/relationship-definitions/{definition_id}/create-next",
        json={"source_version": 1},
    )
    assert next_version.status_code == 201, next_version.text
    assert next_version.headers["location"].endswith("/versions/2")
    assert next_version.json()["properties"] == published.json()["properties"]
    list_mode = {**property_body, "value_mode": "LIST"}
    second_revision = await client.post(
        f"/api/v1/core/relationship-definitions/{definition_id}/versions/2/revise",
        params={"expected_revision": 1},
        json={"properties": [list_mode]},
    )
    assert second_revision.status_code == 200, second_revision.text
    second_publish = await client.post(
        f"/api/v1/core/relationship-definitions/{definition_id}/versions/2/publish",
        params={"expected_revision": 2},
    )
    assert second_publish.status_code == 200, second_publish.text

    version_page = await client.get(
        f"/api/v1/core/relationship-definitions/{definition_id}/versions",
        params={"limit": 1},
    )
    assert version_page.status_code == 200
    assert [item["version"] for item in version_page.json()["items"]] == [1]
    assert version_page.json()["next_cursor"] is not None
    published_page = await client.get(
        f"/api/v1/core/relationship-definitions/{definition_id}/versions",
        params={"status": "PUBLISHED", "limit": 100},
    )
    assert [item["version"] for item in published_page.json()["items"]] == [1, 2]

    selected_default = await client.post(
        f"/api/v1/core/relationship-definitions/{definition_id}/set-default",
        json={"version": 2},
    )
    assert selected_default.status_code == 200
    assert selected_default.json()["default_version"] == 2
    blocked_deprecation = await client.post(
        f"/api/v1/core/relationship-definitions/{definition_id}/versions/2/deprecate"
    )
    assert blocked_deprecation.status_code == 409
    assert blocked_deprecation.json()["code"] == "default_version_conflict"
    deprecated = await client.post(
        f"/api/v1/core/relationship-definitions/{definition_id}/versions/1/deprecate"
    )
    assert deprecated.status_code == 200
    assert deprecated.json()["status"] == "DEPRECATED"

    third = await client.post(
        f"/api/v1/core/relationship-definitions/{definition_id}/create-next",
        json={"source_version": 1},
    )
    assert third.status_code == 201, third.text
    deleted_draft = await client.delete(
        f"/api/v1/core/relationship-definitions/{definition_id}/versions/3",
        params={"expected_revision": 1},
    )
    assert deleted_draft.status_code == 204
    missing_draft = await client.delete(
        f"/api/v1/core/relationship-definitions/{definition_id}/versions/3",
        params={"expected_revision": 1},
    )
    assert missing_draft.status_code == 404

    first_object_id = await _object(client, first_template_id, "rdv-fact-a")
    second_object_id = await _object(client, second_template_id, "rdv-fact-b")
    resolution = next(
        item
        for item in definition["resolutions"]
        if item["from_template_id"] == first_template_id
    )
    fact = await client.post(
        "/api/v1/core/relationships",
        json={
            "resolution_id": resolution["resolution_id"],
            "from_object_id": first_object_id,
            "to_object_id": second_object_id,
            "properties": {"measurements": [3, 1, 3]},
        },
    )
    assert fact.status_code == 201, fact.text
    fact_value = fact.json()
    assert fact_value["relationship_definition_version"] == 2
    assert fact_value["properties"] == {"measurements": [3, 1, 3]}
    exact_fact = await client.get(f"/api/v1/core/relationships/{fact_value['id']}")
    assert exact_fact.json() == fact_value
    object_relative = await client.get(
        f"/api/v1/core/objects/{first_object_id}/relationships"
    )
    assert object_relative.status_code == 200, object_relative.text
    relative_items = object_relative.json()["items"]
    assert len(relative_items) == 1
    assert relative_items[0]["relationship_definition_version"] == 2
    assert relative_items[0]["properties"] == {"measurements": [3, 1, 3]}

    created_events = await client.get(
        "/api/v1/core/lifecycle-events",
        params={
            "relationship_id": fact_value["id"],
            "kind": "RELATIONSHIP_CREATED",
        },
    )
    assert len(created_events.json()["items"]) == 2
    factual_snapshot = {
        "relationship_definition_version": 2,
        "properties": {"measurements": [3, 1, 3]},
    }
    assert all(
        item["before"] is None and item["after"] == factual_snapshot
        for item in created_events.json()["items"]
    )
    deleted_fact = await client.delete(f"/api/v1/core/relationships/{fact_value['id']}")
    assert deleted_fact.status_code == 204
    deleted_events = await client.get(
        "/api/v1/core/lifecycle-events",
        params={
            "relationship_id": fact_value["id"],
            "kind": "RELATIONSHIP_DELETED",
        },
    )
    assert len(deleted_events.json()["items"]) == 2
    assert all(
        item["before"] == factual_snapshot and item["after"] is None
        for item in deleted_events.json()["items"]
    )


@pytest.mark.api
@pytest.mark.postgresql
async def test_m3_default_pointer_read_boundary_is_resource_family_specific(
    relationshipdefinition_client: httpx.AsyncClient,
    migrated_database_engine: Engine,
) -> None:
    client = relationshipdefinition_client
    datatype_id = await _published_integer_datatype(client, "corrupt_default_dt")
    template_id = await _template(client, "corrupt_default_ot")
    await _publish_template(client, template_id)
    created_definition = await client.post(
        "/api/v1/core/relationship-definitions",
        json={
            "symmetric": True,
            "endpoint_template_ids": [template_id, template_id],
            "name": "corrupt_default_rd",
        },
    )
    assert created_definition.status_code == 201
    definition_id = cast(
        str, created_definition.json()["relationship_definition"]["id"]
    )
    await _publish_v1(client, definition_id)

    with migrated_database_engine.begin() as connection:
        connection.execute(
            datatype_versions.update()
            .where(
                datatype_versions.c.datatype_id == UUID(datatype_id),
                datatype_versions.c.version == 1,
            )
            .values(status="DEPRECATED")
        )
        connection.execute(
            object_template_versions.update()
            .where(
                object_template_versions.c.template_id == UUID(template_id),
                object_template_versions.c.version == 1,
            )
            .values(status="DEPRECATED")
        )
        connection.execute(
            relationship_definition_versions.update()
            .where(
                relationship_definition_versions.c.relationship_definition_id
                == UUID(definition_id),
                relationship_definition_versions.c.version == 1,
            )
            .values(status="DEPRECATED")
        )

    datatype_requests = (
        f"/api/v1/core/datatypes/{datatype_id}",
        "/api/v1/core/datatypes",
    )
    for path in datatype_requests:
        response = await client.get(path)
        assert response.status_code == 200, (path, response.text)
        if path.endswith("/datatypes"):
            assert response.json()["items"][0]["default_version"] == 1
        else:
            assert response.json()["default_version"] == 1

    later_slice_requests = (
        f"/api/v1/core/object-templates/{template_id}",
        "/api/v1/core/object-templates",
        f"/api/v1/core/relationship-definitions/{definition_id}",
        "/api/v1/core/relationship-definitions",
    )
    for path in later_slice_requests:
        response = await client.get(path)
        assert response.status_code == 500, (path, response.text)
        assert response.json()["code"] == "internal_error"
