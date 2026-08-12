from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx2
import pytest
from fastapi import FastAPI

from support.http_server import serve_app

pytestmark = [pytest.mark.postgresql, pytest.mark.anyio]


@asynccontextmanager
async def _client(app: FastAPI) -> AsyncIterator[httpx2.AsyncClient]:
    async with serve_app(app) as client:
        yield client


async def test_full_lifecycle_workflow_over_http_and_postgresql(
    postgresql_application_app: FastAPI,
) -> None:
    async with _client(postgresql_application_app) as client:
        created = await client.post(
            "/api/v1/datatypes",
            json={
                "namespace": "network",
                "name": "vlan_id",
                "description": "IEEE 802.1Q VLAN identifier",
                "base_type": "core.integer",
                "constraints": [
                    {"name": "minimum", "value": 1},
                    {"name": "maximum", "value": 4094},
                ],
            },
        )
        assert created.status_code == 201
        payload = created.json()
        datatype_id = payload["datatype"]["id"]
        assert payload["version"]["version"] == 1
        assert payload["version"]["status"] == "draft"

        by_id = await client.get(f"/api/v1/datatypes/{datatype_id}")
        assert by_id.status_code == 200

        by_name = await client.get("/api/v1/datatypes/by-name/network/vlan_id")
        assert by_name.status_code == 200
        assert by_name.json()["id"] == datatype_id

        revised = await client.put(
            f"/api/v1/datatypes/{datatype_id}/versions/1",
            json={
                "constraints": [
                    {"name": "minimum", "value": 1},
                    {"name": "maximum", "value": 4094},
                ],
            },
        )
        assert revised.status_code == 200
        assert revised.json()["status"] == "draft"

        published_v1 = await client.post(f"/api/v1/datatypes/{datatype_id}/versions/1/publish")
        assert published_v1.status_code == 200
        assert published_v1.json()["status"] == "published"

        next_version = await client.post(
            f"/api/v1/datatypes/{datatype_id}/versions",
            json={"source_version": 1},
        )
        assert next_version.status_code == 201
        assert next_version.json()["version"] == 2
        assert next_version.json()["status"] == "draft"

        published_v2 = await client.post(f"/api/v1/datatypes/{datatype_id}/versions/2/publish")
        assert published_v2.status_code == 200
        assert published_v2.json()["status"] == "published"

        versions = await client.get(f"/api/v1/datatypes/{datatype_id}/versions")
        assert versions.status_code == 200
        assert [(item["version"], item["status"]) for item in versions.json()] == [
            (1, "published"),
            (2, "published"),
        ]

        deprecated_v1 = await client.post(f"/api/v1/datatypes/{datatype_id}/versions/1/deprecate")
        assert deprecated_v1.status_code == 200
        assert deprecated_v1.json()["status"] == "deprecated"

        versions_after = await client.get(f"/api/v1/datatypes/{datatype_id}/versions")
        assert [(item["version"], item["status"]) for item in versions_after.json()] == [
            (1, "deprecated"),
            (2, "published"),
        ]


async def test_large_integer_constraint_round_trip_over_http(
    postgresql_application_app: FastAPI,
) -> None:
    large_integer = 10**1000

    async with _client(postgresql_application_app) as client:
        created = await client.post(
            "/api/v1/datatypes",
            json={
                "namespace": "network",
                "name": "huge_minimum",
                "description": None,
                "base_type": "core.number",
                "constraints": [{"name": "minimum", "value": large_integer}],
            },
        )
        assert created.status_code == 201
        datatype_id = created.json()["datatype"]["id"]

        loaded = await client.get(f"/api/v1/datatypes/{datatype_id}/versions/1")
        assert loaded.status_code == 200
        assert loaded.json()["constraints"][0]["value"] == large_integer
        assert isinstance(loaded.json()["constraints"][0]["value"], int)


async def test_create_next_accepts_deprecated_source_over_http_and_postgresql(
    postgresql_application_app: FastAPI,
) -> None:
    async with _client(postgresql_application_app) as client:
        created = await client.post(
            "/api/v1/datatypes",
            json={
                "namespace": "common",
                "name": "email",
                "description": "Email address",
                "base_type": "core.string",
                "constraints": [{"name": "pattern", "value": "^[^@]+@[^@]+[.][^@]+$"}],
            },
        )
        assert created.status_code == 201
        datatype_id = created.json()["datatype"]["id"]

        published_v1 = await client.post(f"/api/v1/datatypes/{datatype_id}/versions/1/publish")
        assert published_v1.status_code == 200

        created_v2 = await client.post(
            f"/api/v1/datatypes/{datatype_id}/versions",
            json={"source_version": 1},
        )
        assert created_v2.status_code == 201

        published_v2 = await client.post(f"/api/v1/datatypes/{datatype_id}/versions/2/publish")
        assert published_v2.status_code == 200

        deprecated_v1 = await client.post(f"/api/v1/datatypes/{datatype_id}/versions/1/deprecate")
        assert deprecated_v1.status_code == 200
        deprecated_v2 = await client.post(f"/api/v1/datatypes/{datatype_id}/versions/2/deprecate")
        assert deprecated_v2.status_code == 200

        created_v3 = await client.post(
            f"/api/v1/datatypes/{datatype_id}/versions",
            json={"source_version": 2},
        )
        assert created_v3.status_code == 201
        created_v3_payload = created_v3.json()
        assert created_v3_payload["version"] == 3
        assert created_v3_payload["status"] == "draft"
        assert created_v3_payload["base_type"] == "core.string"
        assert created_v3_payload["constraints"] == published_v2.json()["constraints"]

        versions = await client.get(f"/api/v1/datatypes/{datatype_id}/versions")
        assert versions.status_code == 200
        assert [(item["version"], item["status"]) for item in versions.json()] == [
            (1, "deprecated"),
            (2, "deprecated"),
            (3, "draft"),
        ]


async def test_failed_http_mutation_does_not_leave_partial_state(
    postgresql_application_app: FastAPI,
) -> None:
    async with _client(postgresql_application_app) as client:
        first = await client.post(
            "/api/v1/datatypes",
            json={
                "namespace": "network",
                "name": "hostname",
                "description": "Network hostname",
                "base_type": "core.string",
                "constraints": [],
            },
        )
        duplicate = await client.post(
            "/api/v1/datatypes",
            json={
                "namespace": "network",
                "name": "hostname",
                "description": "Duplicate hostname",
                "base_type": "core.string",
                "constraints": [],
            },
        )
        listed = await client.get("/api/v1/datatypes")

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "datatype_already_exists"
    assert len(listed.json()) == 1
    assert listed.json()[0]["qualified_name"] == "network.hostname"
