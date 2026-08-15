"""Real-PostgreSQL coverage for the public ObjectTemplate vertical slice."""

from collections.abc import AsyncIterator
from typing import cast

import httpx
import pytest
from sqlalchemy import Engine

from netauto.entrypoints.http import build_app
from netauto.settings import Settings


@pytest.fixture
async def objecttemplate_client(
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


async def _published_datatype(client: httpx.AsyncClient, name: str) -> str:
    created = await client.post(
        "/api/v1/core/datatypes",
        json={
            "namespace": "public",
            "name": name,
            "base_type": "core.integer",
            "constraints": {"minimum": 1},
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


@pytest.mark.api
@pytest.mark.postgresql
async def test_objecttemplate_full_lifecycle_and_effective_schema(
    objecttemplate_client: httpx.AsyncClient,
) -> None:
    datatype_id = await _published_datatype(objecttemplate_client, "port_number")
    root_response = await objecttemplate_client.post(
        "/api/v1/core/object-templates",
        json={
            "namespace": "network",
            "name": "device",
            "abstract": True,
            "properties": [
                {
                    "name": "metric",
                    "position": 1,
                    "datatype_id": datatype_id,
                    "value_mode": "SCALAR",
                    "required": True,
                    "migration_default": 1,
                }
            ],
        },
    )
    assert root_response.status_code == 201, root_response.text
    root = root_response.json()
    root_id = root["object_template"]["id"]
    assert root_response.headers["location"].endswith(root_id)
    assert root["version"]["properties"][0]["datatype_version"] == 1

    published_root = await objecttemplate_client.post(
        f"/api/v1/core/object-templates/{root_id}/versions/1/publish",
        params={"expected_revision": 1},
    )
    assert published_root.status_code == 200, published_root.text

    child_response = await objecttemplate_client.post(
        "/api/v1/core/object-templates",
        json={
            "namespace": "network",
            "name": "router",
            "abstract": False,
            "parent_template_id": root_id,
            "components": [
                {
                    "name": "uplink",
                    "position": 1,
                    "target_template_id": root_id,
                }
            ],
        },
    )
    assert child_response.status_code == 201, child_response.text
    child = child_response.json()
    child_id = child["object_template"]["id"]
    assert child["version"]["parent_version"] == 1

    effective = await objecttemplate_client.get(
        f"/api/v1/core/object-templates/{child_id}/versions/1/effective-schema"
    )
    assert effective.status_code == 200, effective.text
    assert effective.json()["properties"][0]["declaring_template_id"] == root_id
    assert effective.json()["components"][0]["declaring_template_id"] == child_id

    revised = await objecttemplate_client.post(
        f"/api/v1/core/object-templates/{child_id}/versions/1/revise",
        params={"expected_revision": 1},
        json={"properties": [], "components": []},
    )
    assert revised.status_code == 200, revised.text
    assert revised.json()["revision"] == 2

    published_child = await objecttemplate_client.post(
        f"/api/v1/core/object-templates/{child_id}/versions/1/publish",
        params={"expected_revision": 2},
    )
    assert published_child.status_code == 200, published_child.text

    blocked = await objecttemplate_client.post(
        f"/api/v1/core/object-templates/{root_id}/clear-default"
    )
    assert blocked.status_code == 200
    active_child = await objecttemplate_client.post(
        f"/api/v1/core/object-templates/{root_id}/versions/1/deprecate"
    )
    assert active_child.status_code == 409
    assert active_child.json()["code"] == "active_dependency_conflict"

    versions = await objecttemplate_client.get(
        f"/api/v1/core/object-templates/{child_id}/versions"
    )
    assert versions.status_code == 200
    assert "properties" not in versions.json()["items"][0]
    capabilities = await objecttemplate_client.get(
        f"/api/v1/core/object-templates/{child_id}/versions/1/relationship-capabilities"
    )
    assert capabilities.status_code == 404


@pytest.mark.api
@pytest.mark.postgresql
async def test_objecttemplate_strict_shape_and_atomic_failure(
    objecttemplate_client: httpx.AsyncClient,
) -> None:
    datatype_id = await _published_datatype(objecttemplate_client, "vlan_id")
    invalid = await objecttemplate_client.post(
        "/api/v1/core/object-templates",
        json={
            "namespace": "network",
            "name": "switch",
            "abstract": False,
            "properties": [
                {
                    "name": "vlan",
                    "position": 1,
                    "datatype_id": datatype_id,
                    "datatype_version": None,
                    "value_mode": "SCALAR",
                    "required": False,
                }
            ],
        },
    )
    assert invalid.status_code == 400
    absent = await objecttemplate_client.get(
        "/api/v1/core/object-templates",
        params={"namespace": "network", "name": "switch"},
    )
    assert absent.status_code == 200
    assert absent.json()["items"] == []

    missing_default = await objecttemplate_client.post(
        "/api/v1/core/object-templates",
        json={
            "namespace": "network",
            "name": "bad_parent",
            "abstract": False,
            "parent_template_id": "00000000-0000-0000-0000-000000000001",
        },
    )
    assert missing_default.status_code == 422
    assert missing_default.json()["code"] == "referenced_resource_not_found"


@pytest.mark.api
@pytest.mark.postgresql
async def test_objecttemplate_binding_clone_and_publish_recertification(
    objecttemplate_client: httpx.AsyncClient,
) -> None:
    datatype_id = await _published_datatype(objecttemplate_client, "binding_value")
    created = await objecttemplate_client.post(
        "/api/v1/core/object-templates",
        json={
            "namespace": "binding",
            "name": "consumer",
            "abstract": False,
            "properties": [
                {
                    "name": "value",
                    "position": 1,
                    "datatype_id": datatype_id,
                    "value_mode": "SCALAR",
                    "required": False,
                }
            ],
        },
    )
    assert created.status_code == 201, created.text
    template_id = created.json()["object_template"]["id"]
    await objecttemplate_client.post(
        f"/api/v1/core/object-templates/{template_id}/versions/1/publish",
        params={"expected_revision": 1},
    )

    datatype_v2 = await objecttemplate_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/create-next",
        json={"source_version": 1},
    )
    assert datatype_v2.status_code == 201
    await objecttemplate_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/versions/2/publish",
        params={"expected_revision": 1},
    )
    await objecttemplate_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/set-default", json={"version": 2}
    )

    cloned = await objecttemplate_client.post(
        f"/api/v1/core/object-templates/{template_id}/create-next",
        json={"source_version": 1},
    )
    assert cloned.status_code == 201, cloned.text
    assert cloned.json()["properties"][0]["datatype_version"] == 1

    rebound = await objecttemplate_client.post(
        f"/api/v1/core/object-templates/{template_id}/versions/2/revise",
        params={"expected_revision": 1},
        json={
            "properties": [
                {
                    "name": "value",
                    "position": 1,
                    "datatype_id": datatype_id,
                    "value_mode": "SCALAR",
                    "required": False,
                }
            ],
            "components": [],
        },
    )
    assert rebound.status_code == 200, rebound.text
    assert rebound.json()["properties"][0]["datatype_version"] == 2

    preserved = await objecttemplate_client.post(
        f"/api/v1/core/object-templates/{template_id}/versions/2/revise",
        params={"expected_revision": 2},
        json={
            "properties": [
                {
                    "name": "value",
                    "position": 1,
                    "datatype_id": datatype_id,
                    "datatype_version": 1,
                    "value_mode": "SCALAR",
                    "required": False,
                }
            ],
            "components": [],
        },
    )
    assert preserved.status_code == 200, preserved.text
    await objecttemplate_client.post(
        f"/api/v1/core/object-templates/{template_id}/clear-default"
    )
    deprecated_consumer = await objecttemplate_client.post(
        f"/api/v1/core/object-templates/{template_id}/versions/1/deprecate"
    )
    assert deprecated_consumer.status_code == 200, deprecated_consumer.text
    deprecated_dependency = await objecttemplate_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/versions/1/deprecate"
    )
    assert deprecated_dependency.status_code == 200, deprecated_dependency.text

    not_publishable = await objecttemplate_client.post(
        f"/api/v1/core/object-templates/{template_id}/versions/2/publish",
        params={"expected_revision": 3},
    )
    assert not_publishable.status_code == 409
    assert not_publishable.json()["code"] == "dependency_not_admissible"


@pytest.mark.api
@pytest.mark.postgresql
async def test_objecttemplate_historical_property_and_component_evolution(
    objecttemplate_client: httpx.AsyncClient,
) -> None:
    datatype_id = await _published_datatype(objecttemplate_client, "history_value")
    root = await objecttemplate_client.post(
        "/api/v1/core/object-templates",
        json={"namespace": "targets", "name": "root", "abstract": True},
    )
    root_id = root.json()["object_template"]["id"]
    await objecttemplate_client.post(
        f"/api/v1/core/object-templates/{root_id}/versions/1/publish",
        params={"expected_revision": 1},
    )
    child = await objecttemplate_client.post(
        "/api/v1/core/object-templates",
        json={
            "namespace": "targets",
            "name": "child",
            "abstract": False,
            "parent_template_id": root_id,
        },
    )
    child_id = child.json()["object_template"]["id"]
    unrelated = await objecttemplate_client.post(
        "/api/v1/core/object-templates",
        json={"namespace": "targets", "name": "other", "abstract": False},
    )
    unrelated_id = unrelated.json()["object_template"]["id"]

    owner = await objecttemplate_client.post(
        "/api/v1/core/object-templates",
        json={
            "namespace": "history",
            "name": "owner",
            "abstract": False,
            "properties": [
                {
                    "name": "values",
                    "position": 1,
                    "datatype_id": datatype_id,
                    "value_mode": "SCALAR",
                    "required": False,
                }
            ],
            "components": [
                {
                    "name": "slot",
                    "position": 1,
                    "target_template_id": child_id,
                }
            ],
        },
    )
    owner_id = owner.json()["object_template"]["id"]
    await objecttemplate_client.post(
        f"/api/v1/core/object-templates/{owner_id}/versions/1/publish",
        params={"expected_revision": 1},
    )
    next_version = await objecttemplate_client.post(
        f"/api/v1/core/object-templates/{owner_id}/create-next",
        json={"source_version": 1},
    )
    assert next_version.status_code == 201
    widened = await objecttemplate_client.post(
        f"/api/v1/core/object-templates/{owner_id}/versions/2/revise",
        params={"expected_revision": 1},
        json={
            "properties": [
                {
                    "name": "values",
                    "position": 1,
                    "datatype_id": datatype_id,
                    "datatype_version": 1,
                    "value_mode": "LIST",
                    "required": False,
                }
            ],
            "components": [
                {"name": "slot", "position": 1, "target_template_id": root_id}
            ],
        },
    )
    assert widened.status_code == 200, widened.text
    published = await objecttemplate_client.post(
        f"/api/v1/core/object-templates/{owner_id}/versions/2/publish",
        params={"expected_revision": 2},
    )
    assert published.status_code == 200, published.text

    third = await objecttemplate_client.post(
        f"/api/v1/core/object-templates/{owner_id}/create-next",
        json={"source_version": 2},
    )
    assert third.status_code == 201
    invalid = await objecttemplate_client.post(
        f"/api/v1/core/object-templates/{owner_id}/versions/3/revise",
        params={"expected_revision": 1},
        json={
            "properties": [
                {
                    "name": "values",
                    "position": 1,
                    "datatype_id": datatype_id,
                    "datatype_version": 1,
                    "value_mode": "SCALAR",
                    "required": False,
                }
            ],
            "components": [
                {
                    "name": "slot",
                    "position": 1,
                    "target_template_id": unrelated_id,
                }
            ],
        },
    )
    assert invalid.status_code == 422
    assert invalid.json()["code"] == "semantic_validation_failed"
    unchanged = await objecttemplate_client.get(
        f"/api/v1/core/object-templates/{owner_id}/versions/3"
    )
    assert unchanged.json()["revision"] == 1
    assert unchanged.json()["properties"][0]["value_mode"] == "LIST"

    unrelated_component = await objecttemplate_client.post(
        f"/api/v1/core/object-templates/{owner_id}/versions/3/revise",
        params={"expected_revision": 1},
        json={
            "properties": [
                {
                    "name": "values",
                    "position": 1,
                    "datatype_id": datatype_id,
                    "datatype_version": 1,
                    "value_mode": "LIST",
                    "required": False,
                }
            ],
            "components": [
                {
                    "name": "slot",
                    "position": 1,
                    "target_template_id": unrelated_id,
                }
            ],
        },
    )
    assert unrelated_component.status_code == 422

    removed = await objecttemplate_client.post(
        f"/api/v1/core/object-templates/{owner_id}/versions/3/revise",
        params={"expected_revision": 1},
        json={"properties": [], "components": []},
    )
    assert removed.status_code == 200, removed.text
    removed_publish = await objecttemplate_client.post(
        f"/api/v1/core/object-templates/{owner_id}/versions/3/publish",
        params={"expected_revision": 2},
    )
    assert removed_publish.status_code == 200, removed_publish.text
    fourth = await objecttemplate_client.post(
        f"/api/v1/core/object-templates/{owner_id}/create-next",
        json={"source_version": 3},
    )
    assert fourth.status_code == 201
    invalid_readd = await objecttemplate_client.post(
        f"/api/v1/core/object-templates/{owner_id}/versions/4/revise",
        params={"expected_revision": 1},
        json={
            "properties": [
                {
                    "name": "values",
                    "position": 1,
                    "datatype_id": datatype_id,
                    "datatype_version": 1,
                    "value_mode": "SCALAR",
                    "required": False,
                }
            ],
            "components": [],
        },
    )
    assert invalid_readd.status_code == 422
    invalid_component_readd = await objecttemplate_client.post(
        f"/api/v1/core/object-templates/{owner_id}/versions/4/revise",
        params={"expected_revision": 1},
        json={
            "properties": [],
            "components": [
                {
                    "name": "slot",
                    "position": 1,
                    "target_template_id": child_id,
                }
            ],
        },
    )
    assert invalid_component_readd.status_code == 422


@pytest.mark.api
@pytest.mark.postgresql
async def test_objecttemplate_defaults_collisions_and_parent_admission(
    objecttemplate_client: httpx.AsyncClient,
) -> None:
    datatype = await objecttemplate_client.post(
        "/api/v1/core/datatypes",
        json={
            "namespace": "public",
            "name": "ratio",
            "base_type": "core.number",
            "constraints": {"minimum": "0"},
        },
    )
    datatype_id = datatype.json()["datatype"]["id"]
    await objecttemplate_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/versions/1/publish",
        params={"expected_revision": 1},
    )
    canonical = await objecttemplate_client.post(
        "/api/v1/core/object-templates",
        json={
            "namespace": "validation",
            "name": "canonical",
            "abstract": False,
            "properties": [
                {
                    "name": "required_values",
                    "position": 1,
                    "datatype_id": datatype_id,
                    "value_mode": "LIST",
                    "required": True,
                    "migration_default": ["1.0", "1.00"],
                },
                {
                    "name": "optional_value",
                    "position": 2,
                    "datatype_id": datatype_id,
                    "value_mode": "SCALAR",
                    "required": False,
                },
            ],
        },
    )
    assert canonical.status_code == 201, canonical.text
    properties = canonical.json()["version"]["properties"]
    assert properties[0]["migration_default"] == ["1", "1"]
    assert "migration_default" not in properties[1]

    draft_parent = await objecttemplate_client.post(
        "/api/v1/core/object-templates",
        json={"namespace": "validation", "name": "draft_parent", "abstract": True},
    )
    parent_id = draft_parent.json()["object_template"]["id"]
    unavailable = await objecttemplate_client.post(
        "/api/v1/core/object-templates",
        json={
            "namespace": "validation",
            "name": "implicit_child",
            "abstract": False,
            "parent_template_id": parent_id,
        },
    )
    assert unavailable.status_code == 409
    assert unavailable.json()["code"] == "default_version_unavailable"
    inadmissible = await objecttemplate_client.post(
        "/api/v1/core/object-templates",
        json={
            "namespace": "validation",
            "name": "explicit_child",
            "abstract": False,
            "parent_template_id": parent_id,
            "parent_version": 1,
        },
    )
    assert inadmissible.status_code == 409
    assert inadmissible.json()["code"] == "dependency_not_admissible"

    duplicate_position = await objecttemplate_client.post(
        "/api/v1/core/object-templates",
        json={
            "namespace": "validation",
            "name": "duplicate_position",
            "abstract": False,
            "properties": [
                {
                    "name": "first",
                    "position": 1,
                    "datatype_id": datatype_id,
                    "value_mode": "SCALAR",
                    "required": False,
                },
                {
                    "name": "second",
                    "position": 1,
                    "datatype_id": datatype_id,
                    "value_mode": "SCALAR",
                    "required": False,
                },
            ],
        },
    )
    assert duplicate_position.status_code == 422
    absent = await objecttemplate_client.get(
        "/api/v1/core/object-templates",
        params={"namespace": "validation", "name": "duplicate_position"},
    )
    assert absent.json()["items"] == []
