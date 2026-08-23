"""S08 bounded cross-domain whole-aggregate delete diagnostics."""

from collections.abc import AsyncIterator
from typing import cast
from uuid import UUID

import httpx
import pytest
from sqlalchemy import Engine

from netauto.entrypoints.http import build_app
from netauto.persistence.datatypes import DataTypeReferenceCounts, DataTypeStore
from netauto.settings import Settings


@pytest.fixture
async def s08_client(
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
    parent_template_id: str | None = None,
    properties: list[dict[str, object]] | None = None,
    components: list[dict[str, object]] | None = None,
    publish: bool = False,
) -> str:
    body: dict[str, object] = {
        "namespace": "s08_delete",
        "name": name,
        "abstract": False,
        "properties": properties or [],
        "components": components or [],
    }
    if parent_template_id is not None:
        body["parent_template_id"] = parent_template_id
    created = await client.post("/api/v1/core/object-templates", json=body)
    assert created.status_code == 201, created.text
    template_id = cast(str, created.json()["object_template"]["id"])
    if publish:
        published = await client.post(
            f"/api/v1/core/object-templates/{template_id}/versions/1/publish",
            params={"expected_revision": 1},
        )
        assert published.status_code == 200, published.text
    return template_id


async def _published_datatype(client: httpx.AsyncClient, name: str) -> str:
    created = await client.post(
        "/api/v1/core/datatypes",
        json={
            "namespace": "s08_delete",
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


async def _bypass_datatype_delete_precheck(
    store: DataTypeStore, datatype_id: UUID
) -> DataTypeReferenceCounts:
    del store, datatype_id
    return DataTypeReferenceCounts(0, 0)


@pytest.mark.api
@pytest.mark.postgresql
async def test_cross_domain_delete_blocker_matrix_and_aggregate_integrity(
    s08_client: httpx.AsyncClient,
) -> None:
    client = s08_client
    datatype = await client.post(
        "/api/v1/core/datatypes",
        json={
            "namespace": "s08_delete",
            "name": "referenced_value",
            "base_type": "core.integer",
        },
    )
    assert datatype.status_code == 201, datatype.text
    datatype_id = cast(str, datatype.json()["datatype"]["id"])
    published_datatype = await client.post(
        f"/api/v1/core/datatypes/{datatype_id}/versions/1/publish",
        params={"expected_revision": 1},
    )
    assert published_datatype.status_code == 200, published_datatype.text
    property_consumer = await _template(
        client,
        "property_consumer",
        properties=[
            {
                "name": "value",
                "position": 1,
                "datatype_id": datatype_id,
                "datatype_version": 1,
                "value_mode": "SCALAR",
                "required": False,
            }
        ],
    )
    blocked_datatype = await client.delete(f"/api/v1/core/datatypes/{datatype_id}")
    assert blocked_datatype.status_code == 409
    assert blocked_datatype.json()["details"]["blockers"] == [
        {"type": "object_template_property", "count": 1}
    ]
    assert (
        await client.get(f"/api/v1/core/datatypes/{datatype_id}")
    ).status_code == 200
    versions = await client.get(f"/api/v1/core/datatypes/{datatype_id}/versions")
    assert [item["version"] for item in versions.json()["items"]] == [1]

    target_id = await _template(client, "target", publish=True)
    child_id = await _template(client, "child", parent_template_id=target_id)
    component_consumer_id = await _template(
        client,
        "component_consumer",
        components=[
            {
                "name": "target",
                "position": 1,
                "target_template_id": target_id,
            }
        ],
    )
    current_object = await client.post(
        "/api/v1/core/objects",
        json={"template_id": target_id, "canonical_name": "target-object"},
    )
    assert current_object.status_code == 201, current_object.text
    object_id = cast(str, current_object.json()["id"])
    peer_id = await _template(client, "peer", publish=True)
    definition = await client.post(
        "/api/v1/core/relationship-definitions",
        json={
            "symmetric": False,
            "perspectives": [
                {"template_id": target_id, "name": "targets"},
                {"template_id": peer_id, "name": "targeted_by"},
            ],
        },
    )
    assert definition.status_code == 201, definition.text
    definition_id = cast(str, definition.json()["relationship_definition"]["id"])

    blocked_template = await client.delete(f"/api/v1/core/object-templates/{target_id}")
    assert blocked_template.status_code == 409
    assert blocked_template.json()["details"]["blockers"] == [
        {"type": "child_object_template", "count": 1},
        {"type": "object", "count": 1},
        {"type": "object_template_component", "count": 1},
        {"type": "relationship_resolution", "count": 2},
    ]
    assert (
        await client.get(f"/api/v1/core/object-templates/{target_id}")
    ).status_code == 200
    target_versions = await client.get(
        f"/api/v1/core/object-templates/{target_id}/versions"
    )
    assert [item["version"] for item in target_versions.json()["items"]] == [1]

    # Removing only current blockers through their semantic root operations admits
    # the formerly blocked aggregate deletes; no cross-domain cleanup is implicit.
    for path in (
        f"/api/v1/core/object-templates/{child_id}",
        f"/api/v1/core/object-templates/{component_consumer_id}",
        f"/api/v1/core/objects/{object_id}",
        f"/api/v1/core/relationship-definitions/{definition_id}",
    ):
        response = await client.delete(path)
        assert response.status_code == 204, response.text
    assert (
        await client.delete(f"/api/v1/core/object-templates/{target_id}")
    ).status_code == 204

    assert (
        await client.delete(f"/api/v1/core/object-templates/{property_consumer}")
    ).status_code == 204
    assert (
        await client.delete(f"/api/v1/core/datatypes/{datatype_id}")
    ).status_code == 204


@pytest.mark.api
@pytest.mark.postgresql
async def test_datatype_delete_reports_rdv_only_and_mixed_property_blockers(
    s08_client: httpx.AsyncClient,
) -> None:
    client = s08_client
    datatype_id = await _published_datatype(client, "rdv_referenced_value")
    first_template_id = await _template(client, "rdv_first")
    second_template_id = await _template(client, "rdv_second")
    definition = await client.post(
        "/api/v1/core/relationship-definitions",
        json={
            "symmetric": False,
            "perspectives": [
                {"template_id": first_template_id, "name": "links_to"},
                {"template_id": second_template_id, "name": "linked_from"},
            ],
            "properties": [
                {
                    "name": "first_value",
                    "position": 1,
                    "datatype_id": datatype_id,
                    "datatype_version": 1,
                    "value_mode": "SCALAR",
                },
                {
                    "name": "second_value",
                    "position": 2,
                    "datatype_id": datatype_id,
                    "datatype_version": 1,
                    "value_mode": "LIST",
                },
            ],
        },
    )
    assert definition.status_code == 201, definition.text

    rdv_only = await client.delete(f"/api/v1/core/datatypes/{datatype_id}")
    assert rdv_only.status_code == 409
    assert rdv_only.json()["details"]["blockers"] == [
        {"type": "relationship_definition_property", "count": 2}
    ]

    await _template(
        client,
        "mixed_property_consumer",
        properties=[
            {
                "name": "value",
                "position": 1,
                "datatype_id": datatype_id,
                "datatype_version": 1,
                "value_mode": "SCALAR",
                "required": False,
            }
        ],
    )
    mixed = await client.delete(f"/api/v1/core/datatypes/{datatype_id}")
    assert mixed.status_code == 409
    assert mixed.json()["details"]["blockers"] == [
        {"type": "object_template_property", "count": 1},
        {"type": "relationship_definition_property", "count": 2},
    ]


@pytest.mark.api
@pytest.mark.postgresql
async def test_datatype_delete_final_ot_property_fk_is_bounded(
    s08_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = s08_client
    datatype_id = await _published_datatype(client, "ot_final_fk_value")
    await _template(
        client,
        "ot_final_fk_consumer",
        properties=[
            {
                "name": "value",
                "position": 1,
                "datatype_id": datatype_id,
                "datatype_version": 1,
                "value_mode": "SCALAR",
                "required": False,
            }
        ],
    )
    monkeypatch.setattr(
        DataTypeStore,
        "external_reference_counts",
        _bypass_datatype_delete_precheck,
    )

    blocked = await client.delete(f"/api/v1/core/datatypes/{datatype_id}")
    assert blocked.status_code == 409
    assert blocked.json()["details"]["blockers"] == [
        {"type": "object_template_property", "count": 1}
    ]
    assert "fk_object_template_properties_datatype_version" not in blocked.text
    current = await client.get(f"/api/v1/core/datatypes/{datatype_id}")
    assert current.status_code == 200
    assert current.json()["default_version"] == 1


@pytest.mark.api
@pytest.mark.postgresql
async def test_datatype_delete_final_rdv_property_fk_is_bounded(
    s08_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = s08_client
    datatype_id = await _published_datatype(client, "rdv_final_fk_value")
    first_template_id = await _template(client, "rdv_final_fk_first")
    second_template_id = await _template(client, "rdv_final_fk_second")
    definition = await client.post(
        "/api/v1/core/relationship-definitions",
        json={
            "symmetric": False,
            "perspectives": [
                {"template_id": first_template_id, "name": "depends_on"},
                {"template_id": second_template_id, "name": "supports"},
            ],
            "properties": [
                {
                    "name": "value",
                    "position": 1,
                    "datatype_id": datatype_id,
                    "datatype_version": 1,
                    "value_mode": "SCALAR",
                }
            ],
        },
    )
    assert definition.status_code == 201, definition.text
    monkeypatch.setattr(
        DataTypeStore,
        "external_reference_counts",
        _bypass_datatype_delete_precheck,
    )

    blocked = await client.delete(f"/api/v1/core/datatypes/{datatype_id}")
    assert blocked.status_code == 409
    assert blocked.json()["details"]["blockers"] == [
        {"type": "relationship_definition_property", "count": 1}
    ]
    assert "fk_relationship_definition_properties_datatype_version" not in blocked.text
    current = await client.get(f"/api/v1/core/datatypes/{datatype_id}")
    assert current.status_code == 200
    assert current.json()["default_version"] == 1
