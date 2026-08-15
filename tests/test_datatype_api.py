"""Real-PostgreSQL integration coverage for the public DataType vertical slice."""

from collections.abc import AsyncIterator

import httpx
import pytest
from sqlalchemy import Engine

from netauto.entrypoints.http import build_app
from netauto.settings import Settings


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
