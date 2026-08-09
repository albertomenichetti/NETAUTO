from __future__ import annotations

from collections.abc import Generator
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from netauto.api.app import create_app
from netauto.application.unit_of_work import ObjectTemplateUnitOfWork
from netauto.core.datatype import (
    DataType,
    DataTypeFactory,
    DataTypePersistenceError,
    DataTypeVersion,
    DataTypeVersioningService,
)
from netauto.core.objecttemplate import ObjectTemplate, ObjectTemplatePersistenceError
from netauto.persistence.memory.datatype_repository import InMemoryDataTypeRepository
from netauto.persistence.memory.objecttemplate_repository import InMemoryObjectTemplateRepository


class FakeUnitOfWork(ObjectTemplateUnitOfWork):
    def __init__(
        self,
        datatypes: InMemoryDataTypeRepository,
        object_templates: InMemoryObjectTemplateRepository,
        commit_counter: list[int],
    ) -> None:
        self._datatypes = datatypes
        self._object_templates = object_templates
        self._commit_counter = commit_counter

    @property
    def datatypes(self) -> InMemoryDataTypeRepository:
        return self._datatypes

    @property
    def object_templates(self) -> InMemoryObjectTemplateRepository:
        return self._object_templates

    def __enter__(self) -> FakeUnitOfWork:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    def commit(self) -> None:
        self._commit_counter[0] += 1


class BrokenDataTypeRepository(InMemoryDataTypeRepository):
    def list(self) -> tuple[DataType, ...]:
        raise DataTypePersistenceError("boom")


class BrokenObjectTemplateRepository(InMemoryObjectTemplateRepository):
    def list(self) -> tuple[ObjectTemplate, ...]:
        raise ObjectTemplatePersistenceError("boom")


class BrokenObjectTemplateUnitOfWork(FakeUnitOfWork):
    def __init__(self) -> None:
        super().__init__(BrokenDataTypeRepository(), BrokenObjectTemplateRepository(), [0])


@pytest.fixture
def client_context() -> (
    Generator[
        tuple[
            TestClient,
            InMemoryDataTypeRepository,
            InMemoryObjectTemplateRepository,
            list[int],
        ],
        None,
        None,
    ]
):
    datatypes = InMemoryDataTypeRepository()
    object_templates = InMemoryObjectTemplateRepository()
    commits = [0]

    def factory() -> FakeUnitOfWork:
        return FakeUnitOfWork(datatypes, object_templates, commits)

    with TestClient(create_app(factory)) as client:
        yield client, datatypes, object_templates, commits


def _store_datatype(
    repo: InMemoryDataTypeRepository,
    *,
    namespace: str = "network",
    name: str = "hostname",
    published_versions: int = 1,
) -> tuple[DataType, tuple[DataTypeVersion, ...]]:
    datatype, current = DataTypeFactory().create(
        namespace=namespace,
        name=name,
        description=f"{name} datatype",
        base_type="core.string",
    )
    repo.add(datatype)

    versioning = DataTypeVersioningService()
    stored_versions: list[DataTypeVersion] = []
    published = versioning.publish(current)
    repo.add_version(published)
    stored_versions.append(published)

    current = published
    for _ in range(1, published_versions):
        current = versioning.create_next_version(
            current,
            existing_versions=tuple(stored_versions),
        )
        current = versioning.publish(current)
        repo.add_version(current)
        stored_versions.append(current)

    return datatype, tuple(stored_versions)


def _deprecate_datatype_version(
    repo: InMemoryDataTypeRepository,
    version: DataTypeVersion,
) -> DataTypeVersion:
    deprecated = DataTypeVersioningService().deprecate(version)
    repo.replace_version(deprecated)
    return deprecated


def _create_published_parent_template(
    client: TestClient,
    *,
    datatype_id: UUID,
    name: str = "parent",
) -> dict[str, Any]:
    created = _create_object_template(
        client,
        datatype_id=datatype_id,
        name=name,
        properties=[{"name": "hostname", "datatype_id": str(datatype_id), "required": True}],
    )
    response = client.post(
        f"/api/v1/object-templates/{created['object_template']['id']}/versions/1/publish"
    )
    assert response.status_code == 200
    return created


def _create_object_template(
    client: TestClient,
    *,
    datatype_id: UUID,
    datatype_version: int | None = None,
    parent: dict[str, object] | None = None,
    properties: list[dict[str, object]] | None = None,
    abstract: bool = False,
    namespace: str = "network",
    name: str = "device",
) -> dict[str, Any]:
    payload: dict[str, object] = {
        "namespace": namespace,
        "name": name,
        "description": "Device template",
        "abstract": abstract,
        "parent": parent,
        "properties": properties
        if properties is not None
        else [
            {
                "name": "hostname",
                "datatype_id": str(datatype_id),
                "datatype_version": datatype_version,
                "required": True,
            }
        ],
    }
    response = client.post("/api/v1/object-templates", json=payload)
    assert response.status_code == 201
    return response.json()


@pytest.mark.parametrize(
    ("payload", "path"),
    [
        (
            {
                "namespace": "network",
                "name": "device",
                "description": None,
                "abstract": False,
                "properties": [],
                "extra": "nope",
            },
            "/body/extra",
        ),
        (
            {
                "namespace": "network",
                "name": "device",
                "description": None,
                "abstract": 1,
                "properties": [],
            },
            "/body/abstract",
        ),
        (
            {
                "namespace": "network",
                "name": "device",
                "description": None,
                "abstract": "false",
                "properties": [],
            },
            "/body/abstract",
        ),
        (
            {
                "namespace": "network",
                "name": "device",
                "description": None,
                "abstract": False,
                "properties": [
                    {
                        "name": "hostname",
                        "datatype_id": str(uuid4()),
                        "required": 1,
                    }
                ],
            },
            "/body/properties/0/required",
        ),
        (
            {
                "namespace": "network",
                "name": "device",
                "description": None,
                "abstract": False,
                "properties": [
                    {
                        "name": "hostname",
                        "datatype_id": str(uuid4()),
                        "required": "true",
                    }
                ],
            },
            "/body/properties/0/required",
        ),
        (
            {
                "namespace": "network",
                "name": "device",
                "description": None,
                "abstract": False,
                "properties": [
                    {
                        "name": "hostname",
                        "datatype_id": str(uuid4()),
                        "datatype_version": True,
                    }
                ],
            },
            "/body/properties/0/datatype_version",
        ),
        (
            {
                "namespace": "network",
                "name": "device",
                "description": None,
                "abstract": False,
                "properties": [
                    {
                        "name": "hostname",
                        "datatype_id": str(uuid4()),
                        "datatype_version": 0,
                    }
                ],
            },
            "/body/properties/0/datatype_version",
        ),
        (
            {
                "namespace": "network",
                "name": "device",
                "description": None,
                "abstract": False,
                "properties": [
                    {
                        "name": "hostname",
                        "datatype_id": str(uuid4()),
                        "datatype_version": -1,
                    }
                ],
            },
            "/body/properties/0/datatype_version",
        ),
    ],
)
def test_create_schema_strictness(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
    payload: dict[str, object],
    path: str,
) -> None:
    client, _datatypes, _object_templates, _commits = client_context

    response = client.post("/api/v1/object-templates", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "request_validation_failed"
    assert any(detail["path"] == path for detail in response.json()["error"]["details"])
@pytest.mark.parametrize("value", [True, 0])
def test_create_next_source_version_validation(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
    value: object,
) -> None:
    client, datatypes, _object_templates, _commits = client_context
    datatype, _versions = _store_datatype(datatypes)
    created = _create_object_template(client, datatype_id=datatype.id)

    response = client.post(
        f"/api/v1/object-templates/{created['object_template']['id']}/versions",
        json={"source_version": value},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "request_validation_failed"


def test_revise_parent_field_is_required_but_nullable(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
) -> None:
    client, datatypes, _object_templates, _commits = client_context
    datatype, _versions = _store_datatype(datatypes)
    created = _create_object_template(client, datatype_id=datatype.id)

    missing_parent = client.put(
        f"/api/v1/object-templates/{created['object_template']['id']}/versions/1",
        json={"properties": []},
    )
    nullable_parent = client.put(
        f"/api/v1/object-templates/{created['object_template']['id']}/versions/1",
        json={"parent": None, "properties": []},
    )

    assert missing_parent.status_code == 422
    assert missing_parent.json()["error"]["code"] == "request_validation_failed"
    assert any(
        detail["path"] == "/body/parent"
        for detail in missing_parent.json()["error"]["details"]
    )
    assert nullable_parent.status_code == 200


def test_create_response_contains_abstract_parent_and_resolved_datatype_version(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
) -> None:
    client, datatypes, _object_templates, commits = client_context
    datatype, versions = _store_datatype(datatypes, published_versions=3)
    parent_id = uuid4()

    response = client.post(
        "/api/v1/object-templates",
        json={
            "namespace": "network",
            "name": "router",
            "description": "Router template",
            "abstract": True,
            "parent": {"template_id": str(parent_id), "version": 2},
            "properties": [{"name": "hostname", "datatype_id": str(datatype.id), "required": True}],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert commits[0] == 1
    assert payload["object_template"]["abstract"] is True
    assert payload["version"]["status"] == "draft"
    assert payload["version"]["parent"] == {"template_id": str(parent_id), "version": 2}
    assert payload["version"]["properties"][0]["datatype_version"] == versions[-1].version


def test_create_accepts_explicit_published_datatype_version(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
) -> None:
    client, datatypes, _object_templates, _commits = client_context
    datatype, versions = _store_datatype(datatypes, published_versions=2)

    payload = _create_object_template(
        client,
        datatype_id=datatype.id,
        datatype_version=versions[0].version,
        properties=[
            {
                "name": "hostname",
                "datatype_id": str(datatype.id),
                "datatype_version": versions[0].version,
                "required": True,
            }
        ],
    )

    assert payload["version"]["properties"][0]["datatype_version"] == versions[0].version


@pytest.mark.parametrize(
    ("missing_datatype", "datatype_version", "expected_status", "expected_code"),
    [
        (False, None, 409, "object_template_datatype_version_not_published"),
        (False, 1, 409, "object_template_datatype_version_not_published"),
        (True, 1, 404, "object_template_datatype_version_not_found"),
    ],
)
def test_create_invalid_or_non_published_datatype_reference_mapping(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
    missing_datatype: bool,
    datatype_version: int | None,
    expected_status: int,
    expected_code: str,
) -> None:
    client, datatypes, _object_templates, _commits = client_context
    datatype = uuid4()
    if not missing_datatype:
        datatype_model, stored = _store_datatype(
            datatypes,
            name=f"hostname_{expected_code}",
        )
        datatype = datatype_model.id
        deprecated = _deprecate_datatype_version(datatypes, stored[0])
        assert deprecated.status.value == "deprecated"

    response = client.post(
        "/api/v1/object-templates",
        json={
            "namespace": "network",
            "name": f"device_{expected_code}",
            "description": None,
            "abstract": False,
            "properties": [
                {
                    "name": "hostname",
                    "datatype_id": str(datatype),
                    "datatype_version": datatype_version,
                }
            ],
        },
    )

    assert response.status_code == expected_status
    assert response.json()["error"]["code"] == expected_code


def test_read_endpoints_and_not_found_mappings(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
) -> None:
    client, datatypes, _object_templates, _commits = client_context
    datatype, _versions = _store_datatype(datatypes)
    created = _create_object_template(client, datatype_id=datatype.id)
    template_id = created["object_template"]["id"]

    listed = client.get("/api/v1/object-templates")
    by_id = client.get(f"/api/v1/object-templates/{template_id}")
    by_name = client.get("/api/v1/object-templates/by-name/network/device")
    versions = client.get(f"/api/v1/object-templates/{template_id}/versions")
    exact_version = client.get(f"/api/v1/object-templates/{template_id}/versions/1")
    missing_template = client.get(f"/api/v1/object-templates/{uuid4()}")
    missing_version = client.get(f"/api/v1/object-templates/{template_id}/versions/99")

    assert listed.status_code == 200
    assert listed.json()[0]["qualified_name"] == "network.device"
    assert by_id.status_code == 200
    assert by_id.json()["id"] == template_id
    assert by_name.status_code == 200
    assert by_name.json()["id"] == template_id
    assert versions.status_code == 200
    assert versions.json()[0]["version"] == 1
    assert exact_version.status_code == 200
    assert exact_version.json()["status"] == "draft"
    assert missing_template.status_code == 404
    assert missing_template.json()["error"]["code"] == "object_template_not_found"
    assert missing_version.status_code == 404
    assert missing_version.json()["error"]["code"] == "object_template_version_not_found"


def test_revise_replaces_parent_and_properties_and_resolves_datatype_version(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
) -> None:
    client, datatypes, _object_templates, _commits = client_context
    datatype, versions = _store_datatype(datatypes, published_versions=2)
    parent_id = uuid4()
    created = _create_object_template(
        client,
        datatype_id=datatype.id,
        parent={"template_id": str(parent_id), "version": 1},
    )

    revised = client.put(
        f"/api/v1/object-templates/{created['object_template']['id']}/versions/1",
        json={
            "parent": None,
            "properties": [{"name": "serial", "datatype_id": str(datatype.id), "required": False}],
        },
    )

    assert revised.status_code == 200
    payload = revised.json()
    assert payload["parent"] is None
    assert [prop["name"] for prop in payload["properties"]] == ["serial"]
    assert payload["properties"][0]["datatype_version"] == versions[-1].version


def test_revise_invalid_transition_mapping(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
) -> None:
    client, datatypes, _object_templates, _commits = client_context
    datatype, _versions = _store_datatype(datatypes)
    created = _create_object_template(client, datatype_id=datatype.id)
    template_id = created["object_template"]["id"]
    publish_response = client.post(f"/api/v1/object-templates/{template_id}/versions/1/publish")
    assert publish_response.status_code == 200

    response = client.put(
        f"/api/v1/object-templates/{template_id}/versions/1",
        json={"parent": None, "properties": []},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "invalid_object_template_version_transition"


def test_create_next_returns_201_and_preserves_snapshot(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
) -> None:
    client, datatypes, _object_templates, _commits = client_context
    datatype, _versions = _store_datatype(datatypes)
    parent = _create_published_parent_template(client, datatype_id=datatype.id, name="base")
    created = _create_object_template(
        client,
        datatype_id=datatype.id,
        parent={"template_id": parent["object_template"]["id"], "version": 1},
        properties=[{"name": "serial", "datatype_id": str(datatype.id), "required": False}],
    )
    template_id = created["object_template"]["id"]
    publish_response = client.post(f"/api/v1/object-templates/{template_id}/versions/1/publish")
    assert publish_response.status_code == 200

    next_version = client.post(
        f"/api/v1/object-templates/{template_id}/versions",
        json={"source_version": 1},
    )

    assert next_version.status_code == 201
    payload = next_version.json()
    assert payload["version"] == 2
    assert payload["status"] == "draft"
    assert payload["parent"] == {
        "template_id": parent["object_template"]["id"],
        "version": 1,
    }
    assert [prop["name"] for prop in payload["properties"]] == ["serial"]


def test_publish_root_and_inherited_versions(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
) -> None:
    client, datatypes, _object_templates, _commits = client_context
    datatype, _versions = _store_datatype(datatypes)
    root = _create_object_template(
        client,
        datatype_id=datatype.id,
        name="device",
        properties=[{"name": "hostname", "datatype_id": str(datatype.id), "required": True}],
    )
    root_id = root["object_template"]["id"]
    root_publish = client.post(f"/api/v1/object-templates/{root_id}/versions/1/publish")

    child = _create_object_template(
        client,
        datatype_id=datatype.id,
        name="router",
        parent={"template_id": root_id, "version": 1},
        properties=[{"name": "serial", "datatype_id": str(datatype.id), "required": False}],
    )
    child_publish = client.post(
        f"/api/v1/object-templates/{child['object_template']['id']}/versions/1/publish"
    )

    assert root_publish.status_code == 200
    assert root_publish.json()["status"] == "published"
    assert child_publish.status_code == 200
    assert child_publish.json()["status"] == "published"


def test_publish_parent_not_published_mapping(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
) -> None:
    client, datatypes, _object_templates, _commits = client_context
    datatype, _versions = _store_datatype(datatypes)
    parent = _create_object_template(client, datatype_id=datatype.id, name="device")
    child = _create_object_template(
        client,
        datatype_id=datatype.id,
        name="router",
        parent={"template_id": parent["object_template"]["id"], "version": 1},
        properties=[{"name": "serial", "datatype_id": str(datatype.id), "required": False}],
    )

    response = client.post(
        f"/api/v1/object-templates/{child['object_template']['id']}/versions/1/publish"
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "object_template_parent_not_published"


def test_publish_datatype_not_published_mapping(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
) -> None:
    client, datatypes, _object_templates, _commits = client_context
    datatype, versions = _store_datatype(datatypes, name="publish_status")
    created = _create_object_template(
        client,
        datatype_id=datatype.id,
        datatype_version=versions[0].version,
        name="device",
        properties=[
            {
                "name": "hostname",
                "datatype_id": str(datatype.id),
                "datatype_version": versions[0].version,
                "required": True,
            }
        ],
    )
    _deprecate_datatype_version(datatypes, versions[0])

    response = client.post(
        f"/api/v1/object-templates/{created['object_template']['id']}/versions/1/publish"
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "object_template_datatype_version_not_published"


def test_publish_inheritance_conflict_mapping(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
) -> None:
    client, datatypes, _object_templates, _commits = client_context
    datatype, _versions = _store_datatype(datatypes)
    parent = _create_object_template(
        client,
        datatype_id=datatype.id,
        name="device",
        properties=[{"name": "hostname", "datatype_id": str(datatype.id), "required": True}],
    )
    assert (
        client.post(f"/api/v1/object-templates/{parent['object_template']['id']}/versions/1/publish")
        .status_code
        == 200
    )
    child = _create_object_template(
        client,
        datatype_id=datatype.id,
        name="router",
        parent={"template_id": parent["object_template"]["id"], "version": 1},
        properties=[{"name": "hostname", "datatype_id": str(datatype.id), "required": False}],
    )

    response = client.post(
        f"/api/v1/object-templates/{child['object_template']['id']}/versions/1/publish"
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "inherited_object_template_property_conflict"


def test_deprecate_success_and_invalid_transition_mapping(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
) -> None:
    client, datatypes, _object_templates, _commits = client_context
    datatype, _versions = _store_datatype(datatypes)
    created = _create_object_template(client, datatype_id=datatype.id)
    template_id = created["object_template"]["id"]
    publish_response = client.post(f"/api/v1/object-templates/{template_id}/versions/1/publish")
    assert publish_response.status_code == 200

    deprecated = client.post(f"/api/v1/object-templates/{template_id}/versions/1/deprecate")
    invalid = client.post(f"/api/v1/object-templates/{template_id}/versions/1/deprecate")

    assert deprecated.status_code == 200
    assert deprecated.json()["status"] == "deprecated"
    assert invalid.status_code == 409
    assert invalid.json()["error"]["code"] == "invalid_object_template_version_transition"


def test_persistence_errors_map_to_common_envelope() -> None:
    def factory() -> BrokenObjectTemplateUnitOfWork:
        return BrokenObjectTemplateUnitOfWork()

    with TestClient(create_app(factory)) as client:
        object_template_response = client.get("/api/v1/object-templates")
        datatype_response = client.get("/api/v1/datatypes")

    assert object_template_response.status_code == 500
    assert object_template_response.json()["error"]["code"] == "persistence_error"
    assert datatype_response.status_code == 500
    assert datatype_response.json()["error"]["code"] == "persistence_error"


def test_openapi_includes_object_template_and_datatype_endpoints_and_schemas(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
) -> None:
    client, _datatypes, _object_templates, _commits = client_context

    response = client.get("/openapi.json")

    assert response.status_code == 200
    payload = response.json()
    assert "/api/v1/object-templates" in payload["paths"]
    assert "/api/v1/object-templates/{template_id}/versions/{version}" in payload["paths"]
    assert "/api/v1/datatypes" in payload["paths"]
    assert "CreateObjectTemplateRequest" in payload["components"]["schemas"]
    assert "ObjectTemplateVersionResponse" in payload["components"]["schemas"]
