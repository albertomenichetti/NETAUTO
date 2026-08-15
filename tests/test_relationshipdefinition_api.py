"""Real-PostgreSQL API coverage for the S06 Relationship model plane."""

from collections.abc import AsyncIterator
from typing import cast
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import Engine

from netauto.entrypoints.http import build_app
from netauto.persistence.metadata import relationship_definitions, relationships
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
    value = created.json()
    definition_id = value["id"]
    assert created.headers["location"].endswith(definition_id)
    assert value["symmetric"] is False
    assert len(value["resolutions"]) == 2
    assert all(
        "relationship_definition_id" not in item for item in value["resolutions"]
    )
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
            for item in reversed(value["resolutions"])
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
    }
    assert capability["relationship_definition_id"] == definition_id

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
    definition = created.json()
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
    duplicate_id = definition["resolutions"][0]["resolution_id"]
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
                    "resolution_id": definition["resolutions"][0]["resolution_id"],
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
    definition_id = UUID(created.json()["id"])

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
                },
                {
                    "id": uuid4(),
                    "relationship_definition_id": definition_id,
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
        (first.json()["id"], second.json()["id"])
    )
