"""Real-PostgreSQL integration coverage for the public DataType vertical slice."""

from collections.abc import AsyncIterator
from typing import TypedDict, cast
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import Engine
from sqlalchemy.ext.asyncio import create_async_engine

from netauto.entrypoints.http import build_app
from netauto.persistence.metadata import (
    object_template_properties,
    object_template_versions,
    object_templates,
)
from netauto.settings import Settings


class CreatedLineage(TypedDict):
    id: str


class CreatedVersion(TypedDict):
    constraints: dict[str, object]


class CreatedDataType(TypedDict):
    datatype: CreatedLineage
    version: CreatedVersion


@pytest.fixture
async def datatype_client(
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


async def _create_datatype(
    client: httpx.AsyncClient,
    namespace: str,
    name: str,
    *,
    base_type: str = "core.integer",
    constraints: dict[str, object] | None = None,
) -> CreatedDataType:
    body: dict[str, object] = {
        "namespace": namespace,
        "name": name,
        "base_type": base_type,
    }
    if constraints is not None:
        body["constraints"] = constraints
    response = await client.post("/api/v1/core/datatypes", json=body)
    assert response.status_code == 201, response.text
    return cast(CreatedDataType, response.json())


@pytest.mark.api
@pytest.mark.postgresql
async def test_datatype_full_public_lifecycle(
    datatype_client: httpx.AsyncClient,
) -> None:
    created_response = await datatype_client.post(
        "/api/v1/core/datatypes",
        json={
            "namespace": "network.routing",
            "name": "asn",
            "base_type": "core.integer",
            "description": "BGP ASN",
            "constraints": {"maximum": 4294967295, "minimum": 1},
        },
    )
    assert created_response.status_code == 201, created_response.text
    created = created_response.json()
    datatype_id = created["datatype"]["id"]
    assert created_response.headers["location"] == (
        f"/api/v1/core/datatypes/{datatype_id}"
    )
    assert created["version"] == {
        "datatype_id": datatype_id,
        "version": 1,
        "revision": 1,
        "status": "DRAFT",
        "base_type": "core.integer",
        "constraints": {"minimum": 1, "maximum": 4294967295},
    }

    revised_response = await datatype_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/versions/1/revise",
        params={"expected_revision": 1},
        json={"constraints": {"enum": [64512, 1], "minimum": 1}},
    )
    assert revised_response.status_code == 200, revised_response.text
    assert revised_response.json()["revision"] == 2
    assert revised_response.json()["constraints"]["enum"] == [1, 64512]

    stale_response = await datatype_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/versions/1/revise",
        params={"expected_revision": 1},
        json={"constraints": {}},
    )
    assert stale_response.status_code == 409
    assert stale_response.json()["code"] == "stale_revision"

    published_response = await datatype_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/versions/1/publish",
        params={"expected_revision": 2},
    )
    assert published_response.status_code == 200, published_response.text
    assert published_response.json()["status"] == "PUBLISHED"

    lineage_response = await datatype_client.get(
        f"/api/v1/core/datatypes/{datatype_id}"
    )
    assert lineage_response.json()["default_version"] == 1

    next_response = await datatype_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/create-next",
        json={"source_version": 1},
    )
    assert next_response.status_code == 201, next_response.text
    assert next_response.json()["version"] == 2
    assert next_response.headers["location"].endswith("/versions/2")

    second_publish = await datatype_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/versions/2/publish",
        params={"expected_revision": 1},
    )
    assert second_publish.status_code == 200, second_publish.text
    default_response = await datatype_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/set-default",
        json={"version": 2},
    )
    assert default_response.json()["default_version"] == 2

    deprecated_response = await datatype_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/versions/1/deprecate"
    )
    assert deprecated_response.status_code == 200, deprecated_response.text
    assert deprecated_response.json()["status"] == "DEPRECATED"

    third_response = await datatype_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/create-next",
        json={"source_version": 1},
    )
    assert third_response.status_code == 201
    deleted_draft = await datatype_client.delete(
        f"/api/v1/core/datatypes/{datatype_id}/versions/3",
        params={"expected_revision": 1},
    )
    assert deleted_draft.status_code == 204, deleted_draft.text

    description_response = await datatype_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/set-description",
        json={"description": None},
    )
    assert description_response.json()["description"] is None

    first_page = await datatype_client.get(
        f"/api/v1/core/datatypes/{datatype_id}/versions", params={"limit": 1}
    )
    assert first_page.status_code == 200
    assert len(first_page.json()["items"]) == 1
    assert "constraints" not in first_page.json()["items"][0]
    cursor = first_page.json()["next_cursor"]
    second_page = await datatype_client.get(
        f"/api/v1/core/datatypes/{datatype_id}/versions",
        params={"limit": 10, "cursor": cursor},
    )
    assert [item["version"] for item in second_page.json()["items"]] == [2]

    cleared_response = await datatype_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/clear-default"
    )
    assert cleared_response.json()["default_version"] is None
    deleted_lineage = await datatype_client.delete(
        f"/api/v1/core/datatypes/{datatype_id}"
    )
    assert deleted_lineage.status_code == 204, deleted_lineage.text
    absent = await datatype_client.get(f"/api/v1/core/datatypes/{datatype_id}")
    assert absent.status_code == 404
    assert absent.json()["code"] == "resource_not_found"


@pytest.mark.api
@pytest.mark.postgresql
async def test_datatype_transport_and_semantic_failures_are_canonical(
    datatype_client: httpx.AsyncClient,
) -> None:
    malformed = await datatype_client.post(
        "/api/v1/core/datatypes",
        json={
            "namespace": "public",
            "name": "metric",
            "base_type": "core.number",
            "constraints": None,
        },
    )
    assert malformed.status_code == 400
    assert malformed.json() == {
        "code": "invalid_request",
        "message": "The request path, query, or body is malformed.",
        "details": {},
    }

    reserved = await datatype_client.post(
        "/api/v1/core/datatypes",
        json={"namespace": "core.user", "name": "metric", "base_type": "core.number"},
    )
    assert reserved.status_code == 422
    assert reserved.json()["code"] == "semantic_validation_failed"

    created = await datatype_client.post(
        "/api/v1/core/datatypes",
        json={"namespace": "public", "name": "metric", "base_type": "core.number"},
    )
    assert created.status_code == 201, created.text
    datatype_id = created.json()["datatype"]["id"]

    duplicate = await datatype_client.post(
        "/api/v1/core/datatypes",
        json={"namespace": "public", "name": "metric", "base_type": "core.number"},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "qualified_name_conflict"

    body_on_no_body_route = await datatype_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/clear-default", json={}
    )
    assert body_on_no_body_route.status_code == 400

    malformed_revision = await datatype_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/versions/1/publish",
        params={"expected_revision": "1.0"},
    )
    assert malformed_revision.status_code == 400

    unknown_query = await datatype_client.get(
        f"/api/v1/core/datatypes/{datatype_id}", params={"expand": "versions"}
    )
    assert unknown_query.status_code == 400

    invalid_cursor = await datatype_client.get(
        "/api/v1/core/datatypes", params={"cursor": "not-a-cursor"}
    )
    assert invalid_cursor.status_code == 400
    assert invalid_cursor.json()["code"] == "invalid_cursor"


@pytest.mark.api
@pytest.mark.postgresql
async def test_datatype_version_failure_families_and_canonical_round_trip(
    datatype_client: httpx.AsyncClient,
) -> None:
    created = await _create_datatype(
        datatype_client,
        "contract",
        "measurement",
        base_type="core.number",
        constraints={
            "maximum": "10.000",
            "minimum": "-0.00",
            "enum": ["10.0", "0.000"],
        },
    )
    datatype_id = str(created["datatype"]["id"])
    canonical = {"minimum": "0", "maximum": "10", "enum": ["0", "10"]}
    assert created["version"]["constraints"] == canonical

    exact = await datatype_client.get(
        f"/api/v1/core/datatypes/{datatype_id}/versions/1"
    )
    assert exact.status_code == 200
    assert exact.json()["constraints"] == canonical

    missing_source = await datatype_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/create-next",
        json={"source_version": 99},
    )
    assert missing_source.status_code == 422
    assert missing_source.json()["code"] == "referenced_resource_not_found"

    draft_source = await datatype_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/create-next",
        json={"source_version": 1},
    )
    assert draft_source.status_code == 409
    assert draft_source.json()["code"] == "version_source_conflict"

    missing_default_target = await datatype_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/set-default", json={"version": 99}
    )
    assert missing_default_target.status_code == 422
    assert missing_default_target.json()["code"] == "referenced_resource_not_found"

    draft_default_target = await datatype_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/set-default", json={"version": 1}
    )
    assert draft_default_target.status_code == 409
    assert draft_default_target.json()["code"] == "dependency_not_admissible"

    missing_revision = await datatype_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/versions/1/publish"
    )
    assert missing_revision.status_code == 400
    repeated_revision = await datatype_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/versions/1/publish"
        "?expected_revision=1&expected_revision=1"
    )
    assert repeated_revision.status_code == 400
    unknown_body = await datatype_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/versions/1/revise",
        params={"expected_revision": 1},
        json={"constraints": {}, "description": "forbidden"},
    )
    assert unknown_body.status_code == 400

    published = await datatype_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/versions/1/publish",
        params={"expected_revision": 1},
    )
    assert published.status_code == 200
    assert published.json()["status"] == "PUBLISHED"
    assert (await datatype_client.get(f"/api/v1/core/datatypes/{datatype_id}")).json()[
        "default_version"
    ] == 1

    revise_published = await datatype_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/versions/1/revise",
        params={"expected_revision": 1},
        json={"constraints": {}},
    )
    assert revise_published.status_code == 409
    assert revise_published.json()["code"] == "lifecycle_state_conflict"
    delete_published = await datatype_client.delete(
        f"/api/v1/core/datatypes/{datatype_id}/versions/1",
        params={"expected_revision": 1},
    )
    assert delete_published.status_code == 409
    assert delete_published.json()["code"] == "lifecycle_state_conflict"

    second = await datatype_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/create-next",
        json={"source_version": 1},
    )
    assert second.status_code == 201
    await datatype_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/versions/2/publish",
        params={"expected_revision": 1},
    )
    lineage = await datatype_client.get(f"/api/v1/core/datatypes/{datatype_id}")
    assert lineage.json()["default_version"] == 1

    default_blocker = await datatype_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/versions/1/deprecate"
    )
    assert default_blocker.status_code == 409
    assert default_blocker.json()["code"] == "default_version_conflict"

    third = await datatype_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/create-next",
        json={"source_version": 1},
    )
    assert third.json()["version"] == 3
    revised_third = await datatype_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/versions/3/revise",
        params={"expected_revision": 1},
        json={"constraints": {"minimum": "1"}},
    )
    assert revised_third.json()["revision"] == 2
    stale_publish = await datatype_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/versions/3/publish",
        params={"expected_revision": 1},
    )
    assert stale_publish.status_code == 409
    assert stale_publish.json()["code"] == "stale_revision"
    stale_delete = await datatype_client.delete(
        f"/api/v1/core/datatypes/{datatype_id}/versions/3",
        params={"expected_revision": 1},
    )
    assert stale_delete.status_code == 409
    assert stale_delete.json()["code"] == "stale_revision"
    deleted = await datatype_client.delete(
        f"/api/v1/core/datatypes/{datatype_id}/versions/3",
        params={"expected_revision": 2},
    )
    assert deleted.status_code == 204
    reused = await datatype_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/create-next",
        json={"source_version": 1},
    )
    assert reused.json()["version"] == 3


@pytest.mark.api
@pytest.mark.postgresql
async def test_datatype_list_order_filters_keysets_and_cursor_identity(
    datatype_client: httpx.AsyncClient,
) -> None:
    for namespace, name in [
        ("zeta", "last"),
        ("alpha", "second"),
        ("alpha", "first"),
    ]:
        await _create_datatype(datatype_client, namespace, name)

    first_page = await datatype_client.get(
        "/api/v1/core/datatypes", params={"limit": 2}
    )
    assert first_page.status_code == 200
    assert [
        (item["namespace"], item["name"]) for item in first_page.json()["items"]
    ] == [("alpha", "first"), ("alpha", "second")]
    cursor = first_page.json()["next_cursor"]
    next_page = await datatype_client.get(
        "/api/v1/core/datatypes", params={"cursor": cursor, "limit": 1}
    )
    assert [
        (item["namespace"], item["name"]) for item in next_page.json()["items"]
    ] == [("zeta", "last")]

    filtered = await datatype_client.get(
        "/api/v1/core/datatypes", params={"namespace": "alpha"}
    )
    assert [item["name"] for item in filtered.json()["items"]] == [
        "first",
        "second",
    ]
    mismatched = await datatype_client.get(
        "/api/v1/core/datatypes",
        params={"cursor": cursor, "namespace": "alpha"},
    )
    assert mismatched.status_code == 400
    assert mismatched.json()["code"] == "invalid_cursor"

    datatype_id = filtered.json()["items"][0]["id"]
    await datatype_client.post(
        f"/api/v1/core/datatypes/{datatype_id}/versions/1/publish",
        params={"expected_revision": 1},
    )
    published_only = await datatype_client.get(
        f"/api/v1/core/datatypes/{datatype_id}/versions",
        params={"status": "PUBLISHED"},
    )
    assert [item["status"] for item in published_only.json()["items"]] == ["PUBLISHED"]
    assert "constraints" not in published_only.json()["items"][0]


async def _seed_raw_consumer(
    database_url: str,
    datatype_id: UUID,
    datatype_version: int,
    consumer_status: str,
    suffix: str,
) -> None:
    engine = create_async_engine(database_url, isolation_level="READ COMMITTED")
    template_id = uuid4()
    try:
        async with engine.begin() as connection:
            await connection.execute(
                object_templates.insert().values(
                    id=template_id,
                    namespace="raw_consumer",
                    name=f"consumer_{suffix}",
                    description=None,
                    abstract=False,
                    default_version=None,
                    parent_template_id=None,
                )
            )
            await connection.execute(
                object_template_versions.insert().values(
                    template_id=template_id,
                    version=1,
                    revision=1,
                    status=consumer_status,
                    parent_template_id=None,
                    parent_version=None,
                )
            )
            await connection.execute(
                object_template_properties.insert().values(
                    template_id=template_id,
                    template_version=1,
                    name="value",
                    position=1,
                    datatype_id=datatype_id,
                    datatype_version=datatype_version,
                    value_mode="SCALAR",
                    required=False,
                )
            )
    finally:
        await engine.dispose()


@pytest.mark.api
@pytest.mark.postgresql
async def test_datatype_active_consumers_and_lineage_delete_authority(
    datatype_client: httpx.AsyncClient,
    test_database_url: str,
) -> None:
    active = await _create_datatype(datatype_client, "consumers", "active")
    active_id = str(active["datatype"]["id"])
    await datatype_client.post(
        f"/api/v1/core/datatypes/{active_id}/versions/1/publish",
        params={"expected_revision": 1},
    )
    await datatype_client.post(f"/api/v1/core/datatypes/{active_id}/clear-default")
    await _seed_raw_consumer(
        test_database_url, UUID(active_id), 1, "PUBLISHED", "active"
    )
    blocked_deprecate = await datatype_client.post(
        f"/api/v1/core/datatypes/{active_id}/versions/1/deprecate"
    )
    assert blocked_deprecate.status_code == 409
    assert blocked_deprecate.json()["code"] == "active_dependency_conflict"
    blocked_delete = await datatype_client.delete(f"/api/v1/core/datatypes/{active_id}")
    assert blocked_delete.status_code == 409
    assert blocked_delete.json()["code"] == "delete_blocked"
    assert "fk_" not in blocked_delete.text.lower()
    assert "object_template_properties" not in blocked_delete.text.lower()

    for status in ("DRAFT", "DEPRECATED"):
        candidate = await _create_datatype(
            datatype_client, "consumers", f"inactive_{status.lower()}"
        )
        datatype_id = str(candidate["datatype"]["id"])
        await datatype_client.post(
            f"/api/v1/core/datatypes/{datatype_id}/versions/1/publish",
            params={"expected_revision": 1},
        )
        await datatype_client.post(
            f"/api/v1/core/datatypes/{datatype_id}/clear-default"
        )
        await _seed_raw_consumer(
            test_database_url, UUID(datatype_id), 1, status, status.lower()
        )
        deprecated = await datatype_client.post(
            f"/api/v1/core/datatypes/{datatype_id}/versions/1/deprecate"
        )
        assert deprecated.status_code == 200, deprecated.text
        assert deprecated.json()["status"] == "DEPRECATED"

    internal_only = await _create_datatype(
        datatype_client, "consumers", "internal_default_only"
    )
    internal_id = str(internal_only["datatype"]["id"])
    await datatype_client.post(
        f"/api/v1/core/datatypes/{internal_id}/versions/1/publish",
        params={"expected_revision": 1},
    )
    deleted = await datatype_client.delete(f"/api/v1/core/datatypes/{internal_id}")
    assert deleted.status_code == 204, deleted.text
