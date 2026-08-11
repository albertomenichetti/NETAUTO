from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from uuid import uuid4

import httpx2
import pytest

from netauto.api.app import create_app
from netauto.application.unit_of_work import ObjectUnitOfWork
from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateProperty,
    ObjectTemplateVersion,
    ObjectTemplateVersionStatus,
)
from netauto.persistence.memory.datatype_repository import InMemoryDataTypeRepository
from netauto.persistence.memory.object_change_repository import (
    InMemoryObjectChangeRepository,
)
from netauto.persistence.memory.object_repository import InMemoryObjectRepository
from netauto.persistence.memory.objecttemplate_repository import InMemoryObjectTemplateRepository
from netauto.persistence.memory.relationship_repository import (
    InMemoryRelationshipDefinitionRepository,
    InMemoryRelationshipRepository,
)
from support.http_server import serve_app


class FakeUnitOfWork(ObjectUnitOfWork):
    def __init__(
        self,
        repo: InMemoryDataTypeRepository,
        object_templates: InMemoryObjectTemplateRepository,
        objects: InMemoryObjectRepository,
        object_changes: InMemoryObjectChangeRepository,
        relationships: InMemoryRelationshipRepository,
        relationship_definitions: InMemoryRelationshipDefinitionRepository,
        commit_counter: list[int],
    ) -> None:
        self._repo = repo
        self._object_templates = object_templates
        self._objects = objects
        self._object_changes = object_changes
        self._relationships = relationships
        self._relationship_definitions = relationship_definitions
        self._commit_counter = commit_counter

    @property
    def datatypes(self) -> InMemoryDataTypeRepository:
        return self._repo

    @property
    def object_templates(self) -> InMemoryObjectTemplateRepository:
        return self._object_templates

    @property
    def relationship_definitions(self) -> InMemoryRelationshipDefinitionRepository:
        return self._relationship_definitions

    @property
    def relationships(self) -> InMemoryRelationshipRepository:
        return self._relationships

    @property
    def objects(self) -> InMemoryObjectRepository:
        return self._objects

    @property
    def object_changes(self) -> InMemoryObjectChangeRepository:
        return self._object_changes

    def __enter__(self) -> FakeUnitOfWork:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    def commit(self) -> None:
        self._commit_counter[0] += 1


@asynccontextmanager
async def _client() -> AsyncIterator[
    tuple[
        httpx2.AsyncClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ]
]:
    repo = InMemoryDataTypeRepository()
    object_templates = InMemoryObjectTemplateRepository()
    objects = InMemoryObjectRepository()
    object_changes = InMemoryObjectChangeRepository()
    relationships = InMemoryRelationshipRepository()
    relationship_definitions = InMemoryRelationshipDefinitionRepository()
    commits = [0]

    def factory() -> FakeUnitOfWork:
        return FakeUnitOfWork(
            repo,
            object_templates,
            objects,
            object_changes,
            relationships,
            relationship_definitions,
            commits,
        )

    async with serve_app(create_app(factory)) as client:
        yield client, repo, object_templates, commits


async def _create_hostname(client: httpx2.AsyncClient) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/datatypes",
        json={
            "namespace": "network",
            "name": "hostname",
            "description": "Network hostname",
            "base_type": "core.string",
            "constraints": [
                {"name": "min_length", "value": 1},
                {"name": "max_length", "value": 253},
            ],
        },
    )
    assert response.status_code == 201
    return response.json()


pytestmark = pytest.mark.anyio


async def test_create_list_get_and_by_name() -> None:
    async with _client() as (client, _repo, _object_templates, _commits):
        created = await _create_hostname(client)
        datatype_id = created["datatype"]["id"]

        listed = await client.get("/api/v1/datatypes")
        by_id = await client.get(f"/api/v1/datatypes/{datatype_id}")
        by_name = await client.get("/api/v1/datatypes/by-name/network/hostname")

    assert listed.status_code == 200
    assert by_id.status_code == 200
    assert by_name.status_code == 200
    assert listed.json()[0]["qualified_name"] == "network.hostname"
    assert by_id.json()["id"] == datatype_id
    assert by_name.json()["id"] == datatype_id


async def test_versions_lifecycle_endpoints() -> None:
    async with _client() as (client, _repo, _object_templates, _commits):
        created = (
            await client.post(
                "/api/v1/datatypes",
                json={
                    "namespace": "network",
                    "name": "vlan_id",
                    "description": "VLAN identifier",
                    "base_type": "core.integer",
                    "constraints": [
                        {"name": "minimum", "value": 1},
                        {"name": "maximum", "value": 4094},
                    ],
                },
            )
        ).json()
        datatype_id = created["datatype"]["id"]

        version = await client.get(f"/api/v1/datatypes/{datatype_id}/versions/1")
        revised = await client.put(
            f"/api/v1/datatypes/{datatype_id}/versions/1",
            json={
                "constraints": [
                    {"name": "minimum", "value": 1},
                    {"name": "maximum", "value": 4094},
                ],
            },
        )
        published = await client.post(f"/api/v1/datatypes/{datatype_id}/versions/1/publish")
        next_version = await client.post(
            f"/api/v1/datatypes/{datatype_id}/versions",
            json={"source_version": 1},
        )
        published_v2 = await client.post(f"/api/v1/datatypes/{datatype_id}/versions/2/publish")
        deprecated = await client.post(f"/api/v1/datatypes/{datatype_id}/versions/1/deprecate")
        versions = await client.get(f"/api/v1/datatypes/{datatype_id}/versions")

    assert version.status_code == 200
    assert revised.status_code == 200
    assert published.status_code == 200
    assert next_version.status_code == 201
    assert published_v2.status_code == 200
    assert deprecated.status_code == 200
    assert versions.status_code == 200
    assert [item["status"] for item in versions.json()] == ["deprecated", "published"]


async def test_not_found_and_conflict_mappings() -> None:
    async with _client() as (client, _repo, _object_templates, _commits):
        missing = await client.get(f"/api/v1/datatypes/{uuid4()}")
        created = await _create_hostname(client)
        datatype_id = created["datatype"]["id"]
        missing_version = await client.get(f"/api/v1/datatypes/{datatype_id}/versions/99")
        await client.post(f"/api/v1/datatypes/{datatype_id}/versions/1/publish")
        revise_published = await client.put(
            f"/api/v1/datatypes/{datatype_id}/versions/1",
            json={"constraints": []},
        )

    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "datatype_not_found"
    assert missing_version.status_code == 404
    assert missing_version.json()["error"]["code"] == "datatype_version_not_found"
    assert revise_published.status_code == 409
    assert revise_published.json()["error"]["code"] == "invalid_datatype_version_transition"


async def test_create_next_accepts_deprecated_source() -> None:
    async with _client() as (client, _repo, _object_templates, _commits):
        created = await _create_hostname(client)
        datatype_id = created["datatype"]["id"]

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
    assert created_v3.json()["version"] == 3
    assert created_v3.json()["status"] == "draft"
    assert created_v3.json()["base_type"] == "core.string"
    assert created_v3.json()["constraints"] == created_v2.json()["constraints"]


@pytest.mark.parametrize(
    ("payload", "expected_code"),
    [
        (
            {
                "namespace": "network",
                "name": "bad_integer_constraint",
                "description": None,
                "base_type": "core.string",
                "constraints": [{"name": "minimum", "value": 1}],
            },
            "unsupported_constraint",
        ),
        (
            {
                "namespace": "network",
                "name": "bad_value",
                "description": None,
                "base_type": "core.string",
                "constraints": [{"name": "min_length", "value": -1}],
            },
            "invalid_constraint_value",
        ),
        (
            {
                "namespace": "network",
                "name": "duplicate_constraint_name",
                "description": None,
                "base_type": "core.string",
                "constraints": [
                    {"name": "min_length", "value": 1},
                    {"name": "min_length", "value": 2},
                ],
            },
            "duplicate_constraint",
        ),
        (
            {
                "namespace": "network",
                "name": "conflicting_constraints",
                "description": None,
                "base_type": "core.string",
                "constraints": [
                    {"name": "min_length", "value": 10},
                    {"name": "max_length", "value": 5},
                ],
            },
            "conflicting_constraints",
        ),
        (
            {
                "namespace": "core",
                "name": "foo",
                "description": None,
                "base_type": "core.string",
                "constraints": [],
            },
            "reserved_datatype_namespace",
        ),
        (
            {
                "namespace": "Network",
                "name": "hostname",
                "description": None,
                "base_type": "core.string",
                "constraints": [],
            },
            "invalid_datatype_identifier",
        ),
        (
            {
                "namespace": "network",
                "name": "hostname",
                "description": None,
                "base_type": "network.hostname",
                "constraints": [],
            },
            "primitive_type_not_found",
        ),
    ],
)
async def test_domain_errors_map_to_422(payload: dict[str, object], expected_code: str) -> None:
    async with _client() as (client, _repo, _object_templates, _commits):
        response = await client.post("/api/v1/datatypes", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == expected_code


async def test_duplicate_logical_name_maps_to_409() -> None:
    async with _client() as (client, _repo, _object_templates, _commits):
        await _create_hostname(client)
        duplicate = await client.post(
            "/api/v1/datatypes",
            json={
                "namespace": "network",
                "name": "hostname",
                "description": None,
                "base_type": "core.string",
                "constraints": [],
            },
        )

    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "datatype_already_exists"


async def test_request_validation_envelope_and_no_default_detail_leak() -> None:
    async with _client() as (client, _repo, _object_templates, _commits):
        response = await client.post(
            "/api/v1/datatypes",
            json={
                "namespace": 123,
                "name": "hostname",
                "description": None,
                "base_type": "core.string",
                "constraints": [],
                "unexpected": "value",
            },
        )

    assert response.status_code == 422
    payload = response.json()
    assert "detail" not in payload
    assert payload["error"]["code"] == "request_validation_failed"
    assert payload["error"]["message"] == "Request validation failed"
    assert payload["error"]["details"][0]["path"].startswith("/body")


async def test_revise_request_rejects_removed_base_type_field() -> None:
    async with _client() as (client, _repo, _object_templates, _commits):
        created = await _create_hostname(client)
        datatype_id = created["datatype"]["id"]
        response = await client.put(
            f"/api/v1/datatypes/{datatype_id}/versions/1",
            json={"base_type": "core.integer", "constraints": []},
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "request_validation_failed"


async def test_delete_unreferenced_datatype_returns_204_and_empty_body() -> None:
    async with _client() as (client, _repo, _object_templates, _commits):
        created = await _create_hostname(client)
        datatype_id = created["datatype"]["id"]
        deleted = await client.delete(f"/api/v1/datatypes/{datatype_id}")
        missing = await client.get(f"/api/v1/datatypes/{datatype_id}")

    assert deleted.status_code == 204
    assert deleted.content == b""
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "datatype_not_found"


async def test_delete_referenced_datatype_returns_409_datatype_in_use() -> None:
    async with _client() as (client, repo, object_templates, _commits):
        created = await _create_hostname(client)
        datatype_id = created["datatype"]["id"]
        datatype = repo.get_by_name("network", "hostname")
        assert datatype is not None
        template = ObjectTemplate(id=uuid4(), namespace="network", name="device")
        template_version = ObjectTemplateVersion(
            template_id=template.id,
            version=1,
            status=ObjectTemplateVersionStatus.PUBLISHED,
            properties=(
                ObjectTemplateProperty(
                    name="hostname_property",
                    datatype_id=datatype.id,
                    datatype_version=1,
                    required=True,
                ),
            ),
        )
        object_templates.add(template)
        object_templates.add_version(template_version)
        response = await client.delete(f"/api/v1/datatypes/{datatype_id}")
        still_exists = await client.get(f"/api/v1/datatypes/{datatype_id}")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "datatype_in_use"
    assert still_exists.status_code == 200


async def test_delete_missing_datatype_returns_404() -> None:
    async with _client() as (client, _repo, _object_templates, _commits):
        response = await client.delete(f"/api/v1/datatypes/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "datatype_not_found"

async def test_no_string_to_int_coercion_and_bool_edge_cases() -> None:
    async with _client() as (client, _repo, _object_templates, _commits):
        created = (
            await client.post(
                "/api/v1/datatypes",
                json={
                    "namespace": "network",
                    "name": "vlan_id",
                    "description": None,
                    "base_type": "core.integer",
                    "constraints": [
                        {"name": "minimum", "value": 1},
                        {"name": "maximum", "value": 4094},
                    ],
                },
            )
        ).json()
        datatype_id = created["datatype"]["id"]

        source_version_string = await client.post(
            f"/api/v1/datatypes/{datatype_id}/versions",
            json={"source_version": "1"},
        )
        bool_constraint = await client.post(
            "/api/v1/datatypes",
            json={
                "namespace": "network",
                "name": "bad_bool_constraint",
                "description": None,
                "base_type": "core.integer",
                "constraints": [{"name": "minimum", "value": True}],
            },
        )

    assert source_version_string.status_code == 422
    assert source_version_string.json()["error"]["code"] == "request_validation_failed"
    assert bool_constraint.status_code == 422
    assert bool_constraint.json()["error"]["code"] in {
        "unsupported_constraint",
        "invalid_constraint_value",
    }


async def test_by_name_route_is_not_shadowed() -> None:
    async with _client() as (client, _repo, _object_templates, _commits):
        await _create_hostname(client)
        response = await client.get("/api/v1/datatypes/by-name/network/hostname")

    assert response.status_code == 200
    assert response.json()["qualified_name"] == "network.hostname"


async def test_openapi_documents_routes_and_schemas() -> None:
    async with _client() as (client, _repo, _object_templates, _commits):
        openapi = (await client.get("/openapi.json")).json()

    paths = openapi["paths"]
    schemas = openapi["components"]["schemas"]

    assert "/api/v1/datatypes" in paths
    assert "/api/v1/datatypes/by-name/{namespace}/{name}" in paths
    assert "/api/v1/datatypes/{datatype_id}" in paths
    assert "/api/v1/datatypes/{datatype_id}/versions" in paths
    assert "/api/v1/datatypes/{datatype_id}/versions/{version}" in paths
    assert "/api/v1/datatypes/{datatype_id}/versions/{version}/publish" in paths
    assert "/api/v1/datatypes/{datatype_id}/versions/{version}/deprecate" in paths
    assert (
        paths["/api/v1/datatypes/{datatype_id}"]["delete"]["responses"]["204"]["description"]
        == "Successful Response"
    )
    assert "delete" not in paths["/api/v1/datatypes/{datatype_id}/versions/{version}"]
    assert (
        paths["/api/v1/datatypes"]["post"]["responses"]["201"]["description"]
        == "Successful Response"
    )
    assert (
        paths["/api/v1/datatypes/{datatype_id}/versions"]["post"]["responses"]["201"]["description"]
        == "Successful Response"
    )
    assert schemas["ConstraintName"]["enum"] == [
        "min_length",
        "max_length",
        "pattern",
        "minimum",
        "maximum",
        "enum",
    ]
    assert schemas["DataTypeVersionStatus"]["enum"] == ["draft", "published", "deprecated"]
    post_422_ref = (
        paths["/api/v1/datatypes"]["post"]["responses"]["422"]["content"]["application/json"][
            "schema"
        ]["$ref"]
    )
    assert post_422_ref.endswith("/ErrorResponse")
    revise_schema = schemas["ReviseDataTypeVersionRequest"]
    assert set(revise_schema["properties"]) == {"constraints"}
