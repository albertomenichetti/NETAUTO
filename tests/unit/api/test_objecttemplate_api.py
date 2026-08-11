from __future__ import annotations

from collections.abc import Generator
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from netauto.api.app import create_app
from netauto.application.unit_of_work import ObjectUnitOfWork
from netauto.core.datatype import (
    DataType,
    DataTypeFactory,
    DataTypePersistenceError,
    DataTypeVersion,
    DataTypeVersioningService,
)
from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplatePersistenceError,
    ObjectTemplateVersion,
    ObjectTemplateVersionRef,
    ObjectTemplateVersionStatus,
)
from netauto.core.relationship import RelationshipDefinition
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


class FakeUnitOfWork(ObjectUnitOfWork):
    def __init__(
        self,
        datatypes: InMemoryDataTypeRepository,
        object_templates: InMemoryObjectTemplateRepository,
        objects: InMemoryObjectRepository,
        object_changes: InMemoryObjectChangeRepository,
        relationships: InMemoryRelationshipRepository,
        relationship_definitions: InMemoryRelationshipDefinitionRepository,
        commit_counter: list[int],
    ) -> None:
        self._datatypes = datatypes
        self._object_templates = object_templates
        self._objects = objects
        self._object_changes = object_changes
        self._relationships = relationships
        self._relationship_definitions = relationship_definitions
        self._commit_counter = commit_counter

    @property
    def datatypes(self) -> InMemoryDataTypeRepository:
        return self._datatypes

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


class BrokenDataTypeRepository(InMemoryDataTypeRepository):
    def list(self) -> tuple[DataType, ...]:
        raise DataTypePersistenceError("boom")


class BrokenObjectTemplateRepository(InMemoryObjectTemplateRepository):
    def list(self) -> tuple[ObjectTemplate, ...]:
        raise ObjectTemplatePersistenceError("boom")


class BrokenObjectTemplateUnitOfWork(FakeUnitOfWork):
    def __init__(self) -> None:
        super().__init__(
            BrokenDataTypeRepository(),
            BrokenObjectTemplateRepository(),
            InMemoryObjectRepository(),
            InMemoryObjectChangeRepository(),
            InMemoryRelationshipRepository(),
            InMemoryRelationshipDefinitionRepository(),
            [0],
        )


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
    objects = InMemoryObjectRepository()
    object_changes = InMemoryObjectChangeRepository()
    relationships = InMemoryRelationshipRepository()
    relationship_definitions = InMemoryRelationshipDefinitionRepository()
    commits = [0]

    def factory() -> FakeUnitOfWork:
        return FakeUnitOfWork(
            datatypes,
            object_templates,
            objects,
            object_changes,
            relationships,
            relationship_definitions,
            commits,
        )

    with TestClient(create_app(factory, model_write_uow_factory=factory)) as client:
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
    repo.add_version(current)
    published = versioning.publish(current)
    repo.replace_version(published)
    stored_versions.append(published)

    current = published
    for _ in range(1, published_versions):
        current = versioning.create_next_version(
            current,
            existing_versions=tuple(stored_versions),
        )
        repo.add_version(current)
        current = versioning.publish(current)
        repo.replace_version(current)
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


def _publish_object_template_version(
    client: TestClient,
    template_id: str,
    version: int = 1,
) -> dict[str, Any]:
    response = client.post(f"/api/v1/object-templates/{template_id}/versions/{version}/publish")
    assert response.status_code == 200
    return response.json()


def _deprecate_object_template_version(
    client: TestClient,
    template_id: str,
    version: int = 1,
) -> dict[str, Any]:
    response = client.post(f"/api/v1/object-templates/{template_id}/versions/{version}/deprecate")
    assert response.status_code == 200
    return response.json()


def _create_object_template(
    client: TestClient,
    *,
    datatype_id: UUID | None = None,
    datatype_version: int | None = None,
    parent: dict[str, object] | None = None,
    properties: list[dict[str, object]] | None = None,
    components: list[dict[str, object]] | None = None,
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
        else (
            []
            if datatype_id is None
            else [
                {
                    "name": "hostname",
                    "datatype_id": str(datatype_id),
                    "datatype_version": datatype_version,
                    "required": True,
                }
            ]
        ),
        "components": components if components is not None else [],
    }
    response = client.post("/api/v1/object-templates", json=payload)
    assert response.status_code == 201
    return response.json()


def _create_component_target(
    client: TestClient,
    *,
    name: str,
    abstract: bool = False,
) -> dict[str, Any]:
    return _create_object_template(
        client,
        datatype_id=None,
        properties=[],
        components=[],
        abstract=abstract,
        name=name,
    )


def _create_published_component_target_versions(
    client: TestClient,
    *,
    name: str,
    published_versions: int = 1,
    abstract: bool = False,
) -> dict[str, Any]:
    created = _create_component_target(client, name=name, abstract=abstract)
    template_id = created["object_template"]["id"]
    _publish_object_template_version(client, template_id, 1)

    current_version = 1
    for _ in range(1, published_versions):
        next_response = client.post(
            f"/api/v1/object-templates/{template_id}/versions",
            json={"source_version": current_version},
        )
        assert next_response.status_code == 201
        current_version = next_response.json()["version"]
        _publish_object_template_version(client, template_id, current_version)

    return created


def _create_component_target_with_draft_and_deprecated_versions(
    client: TestClient,
    *,
    name: str,
) -> dict[str, Any]:
    created = _create_published_component_target_versions(client, name=name, published_versions=2)
    template_id = created["object_template"]["id"]

    draft_response = client.post(
        f"/api/v1/object-templates/{template_id}/versions",
        json={"source_version": 2},
    )
    assert draft_response.status_code == 201

    deprecated_response = client.post(
        f"/api/v1/object-templates/{template_id}/versions",
        json={"source_version": 2},
    )
    assert deprecated_response.status_code == 201
    _publish_object_template_version(client, template_id, 4)
    _deprecate_object_template_version(client, template_id, 4)

    return created


def _component_request(
    template_id: str,
    *,
    name: str = "interfaces",
) -> dict[str, object]:
    return {
        "name": name,
        "template_id": template_id,
    }


def _relationship_definition(
    *,
    source_template_id: UUID,
    target_template_id: UUID,
    forward_name: str = "uses",
    reverse_name: str = "is_used_by",
) -> RelationshipDefinition:
    return RelationshipDefinition(
        id=uuid4(),
        source_template_id=source_template_id,
        target_template_id=target_template_id,
        forward_name=forward_name,
        reverse_name=reverse_name,
    )


@pytest.mark.parametrize(
    ("component", "path"),
    [
        (
            {
                "name": "interfaces",
                "template_id": "not-a-uuid",
            },
            "/body/components/0/template_id",
        ),
        (
            {
                "name": "interfaces",
                "template_id": str(uuid4()),
                "unexpected": "nope",
            },
            "/body/components/0/unexpected",
        ),
    ],
)
def test_create_component_schema_strictness(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
    component: dict[str, object],
    path: str,
) -> None:
    client, _datatypes, _object_templates, _commits = client_context

    response = client.post(
        "/api/v1/object-templates",
        json={
            "namespace": "network",
            "name": "device",
            "description": None,
            "abstract": False,
            "properties": [],
            "components": [component],
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "request_validation_failed"
    assert any(detail["path"] == path for detail in response.json()["error"]["details"])


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


def test_revise_endpoint_rejects_datatype_version_downgrade_and_preserves_snapshot(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
) -> None:
    client, datatypes, object_templates, commits = client_context
    datatype, _versions = _store_datatype(
        datatypes,
        namespace="common",
        name="email",
        published_versions=3,
    )
    created = _create_object_template(
        client,
        datatype_id=datatype.id,
        datatype_version=3,
        properties=[
            {
                "name": "e_mail",
                "datatype_id": str(datatype.id),
                "datatype_version": 3,
                "required": False,
            }
        ],
        name="contact",
    )
    template_id = created["object_template"]["id"]
    before = commits[0]

    response = client.put(
        f"/api/v1/object-templates/{template_id}/versions/1",
        json={
            "parent": None,
            "properties": [
                {
                    "name": "e_mail",
                    "datatype_id": str(datatype.id),
                    "datatype_version": 2,
                    "required": False,
                }
            ],
            "components": [],
        },
    )
    loaded = client.get(f"/api/v1/object-templates/{template_id}/versions/1")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "object_template_datatype_version_downgrade"
    assert commits[0] == before
    assert loaded.status_code == 200
    assert loaded.json()["properties"][0]["datatype_version"] == 3
    stored = object_templates.get_version(UUID(template_id), 1)
    assert stored is not None
    assert stored.properties[0].datatype_version == 3


def test_revise_endpoint_allows_datatype_version_upgrade(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
) -> None:
    client, datatypes, _object_templates, commits = client_context
    datatype, _versions = _store_datatype(
        datatypes,
        namespace="common",
        name="email_upgrade",
        published_versions=4,
    )
    created = _create_object_template(
        client,
        datatype_id=datatype.id,
        datatype_version=3,
        properties=[
            {
                "name": "e_mail",
                "datatype_id": str(datatype.id),
                "datatype_version": 3,
                "required": False,
            }
        ],
        name="contact_upgrade",
    )
    template_id = created["object_template"]["id"]
    before = commits[0]

    response = client.put(
        f"/api/v1/object-templates/{template_id}/versions/1",
        json={
            "parent": None,
            "properties": [
                {
                    "name": "e_mail",
                    "datatype_id": str(datatype.id),
                    "datatype_version": 4,
                    "required": True,
                }
            ],
            "components": [],
        },
    )

    assert response.status_code == 200
    assert commits[0] == before + 1
    assert response.json()["properties"][0]["datatype_version"] == 4
    assert response.json()["properties"][0]["required"] is True


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
    parent_template = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="parent_device",
        description=None,
        abstract=False,
    )
    _object_templates.add(parent_template)
    _object_templates.add_version(
        ObjectTemplateVersion(
            template_id=parent_template.id,
            version=2,
            status=ObjectTemplateVersionStatus.DRAFT,
            properties=(),
        )
    )

    response = client.post(
        "/api/v1/object-templates",
        json={
            "namespace": "network",
            "name": "router",
            "description": "Router template",
            "abstract": True,
            "parent": {"template_id": str(parent_template.id), "version": 2},
            "properties": [{"name": "hostname", "datatype_id": str(datatype.id), "required": True}],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert commits[0] == 1
    assert payload["object_template"]["abstract"] is True
    assert payload["version"]["status"] == "draft"
    assert payload["version"]["parent"] == {
        "template_id": str(parent_template.id),
        "version": 2,
    }
    assert payload["version"]["properties"][0]["datatype_version"] == versions[-1].version
    assert payload["version"]["components"] == []


def test_create_without_components_returns_empty_component_list(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
) -> None:
    client, datatypes, _object_templates, commits = client_context
    datatype, _versions = _store_datatype(datatypes)

    response = client.post(
        "/api/v1/object-templates",
        json={
            "namespace": "network",
            "name": "switch",
            "description": "Switch template",
            "abstract": False,
            "parent": None,
            "properties": [{"name": "hostname", "datatype_id": str(datatype.id), "required": True}],
        },
    )

    assert response.status_code == 201
    assert commits[0] == 1
    assert response.json()["version"]["components"] == []


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


def test_create_accepts_explicit_published_component_target_version(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
) -> None:
    client, _datatypes, _object_templates, _commits = client_context
    target = _create_published_component_target_versions(
        client,
        name="network_interface",
        published_versions=2,
    )

    payload = _create_object_template(
        client,
        properties=[],
        components=[_component_request(target["object_template"]["id"])],
        name="network_device",
    )

    assert payload["version"]["components"] == [
        {
            "name": "interfaces",
            "template_id": target["object_template"]["id"],
        }
    ]


def test_create_component_target_identity_is_not_rewritten_by_newer_versions(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
) -> None:
    client, _datatypes, _object_templates, _commits = client_context
    target = _create_component_target_with_draft_and_deprecated_versions(
        client,
        name="network_interface",
    )

    payload = _create_object_template(
        client,
        properties=[],
        components=[_component_request(target["object_template"]["id"])],
        abstract=True,
        name="network_device",
    )

    assert payload["version"]["components"] == [
        {
            "name": "interfaces",
            "template_id": target["object_template"]["id"],
        }
    ]


def test_create_accepts_abstract_component_target_and_coexists_with_properties(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
) -> None:
    client, datatypes, _object_templates, _commits = client_context
    datatype, versions = _store_datatype(datatypes)
    target = _create_published_component_target_versions(
        client,
        name="network_interface",
        abstract=True,
    )

    payload = _create_object_template(
        client,
        datatype_id=datatype.id,
        properties=[{"name": "hostname", "datatype_id": str(datatype.id), "required": True}],
        components=[_component_request(target["object_template"]["id"])],
        abstract=True,
        name="network_device",
    )

    assert payload["version"]["properties"][0]["datatype_version"] == versions[0].version
    assert payload["version"]["components"][0] == {
        "name": "interfaces",
        "template_id": target["object_template"]["id"],
    }


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


@pytest.mark.parametrize(
    ("setup", "component", "expected_status", "expected_code"),
    [
        (
            "missing",
            _component_request(str(uuid4())),
            404,
            "object_template_component_version_not_found",
        ),
        ("unpublished_identity", None, 409, "object_template_component_version_not_published"),
    ],
)
def test_create_component_reference_error_mapping(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
    setup: str,
    component: dict[str, object] | None,
    expected_status: int,
    expected_code: str,
) -> None:
    client, _datatypes, _object_templates, commits = client_context

    if setup == "unpublished_identity":
        target = _create_component_target(client, name="network_interface")
        component = _component_request(target["object_template"]["id"])

    before = commits[0]
    response = client.post(
        "/api/v1/object-templates",
        json={
            "namespace": "network",
            "name": f"device_{setup}",
            "description": None,
            "abstract": False,
            "properties": [],
            "components": [component],
        },
    )

    assert response.status_code == expected_status
    assert response.json()["error"]["code"] == expected_code
    assert commits[0] == before


def test_publish_endpoint_maps_relationship_definition_semantic_conflict_and_keeps_draft() -> None:
    datatypes = InMemoryDataTypeRepository()
    object_templates = InMemoryObjectTemplateRepository()
    objects = InMemoryObjectRepository()
    object_changes = InMemoryObjectChangeRepository()
    relationships = InMemoryRelationshipRepository()
    relationship_definitions = InMemoryRelationshipDefinitionRepository()
    commits = [0]

    def factory() -> FakeUnitOfWork:
        return FakeUnitOfWork(
            datatypes,
            object_templates,
            objects,
            object_changes,
            relationships,
            relationship_definitions,
            commits,
        )

    network_device = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="network_device",
        description="network_device template",
        abstract=False,
    )
    router = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="router",
        description="router template",
        abstract=False,
    )
    credential = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="credential",
        description="credential template",
        abstract=False,
    )
    object_templates.add(network_device)
    object_templates.add(router)
    object_templates.add(credential)
    object_templates.add_version(
        ObjectTemplateVersion(
            template_id=network_device.id,
            version=1,
            status=ObjectTemplateVersionStatus.DRAFT,
        )
    )
    object_templates.replace_version(
        ObjectTemplateVersion(
            template_id=network_device.id,
            version=1,
            status=ObjectTemplateVersionStatus.PUBLISHED,
        )
    )
    object_templates.add_version(
        ObjectTemplateVersion(
            template_id=router.id,
            version=1,
            status=ObjectTemplateVersionStatus.DRAFT,
            parent=ObjectTemplateVersionRef(template_id=network_device.id, version=1),
        )
    )
    object_templates.replace_version(
        ObjectTemplateVersion(
            template_id=router.id,
            version=1,
            status=ObjectTemplateVersionStatus.PUBLISHED,
            parent=ObjectTemplateVersionRef(template_id=network_device.id, version=1),
        )
    )
    object_templates.add_version(
        ObjectTemplateVersion(
            template_id=router.id,
            version=2,
            status=ObjectTemplateVersionStatus.DRAFT,
            parent=ObjectTemplateVersionRef(template_id=network_device.id, version=1),
        )
    )
    object_templates.add_version(
        ObjectTemplateVersion(
            template_id=credential.id,
            version=1,
            status=ObjectTemplateVersionStatus.DRAFT,
        )
    )
    object_templates.replace_version(
        ObjectTemplateVersion(
            template_id=credential.id,
            version=1,
            status=ObjectTemplateVersionStatus.PUBLISHED,
        )
    )
    relationship_definitions.add(
        _relationship_definition(
            source_template_id=network_device.id,
            target_template_id=credential.id,
        )
    )
    relationship_definitions.add(
        _relationship_definition(
            source_template_id=router.id,
            target_template_id=credential.id,
        )
    )

    with TestClient(create_app(factory, model_write_uow_factory=factory)) as client:
        response = client.post(f"/api/v1/object-templates/{router.id}/versions/2/publish")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "relationship_definition_semantic_conflict"
    assert commits[0] == 0
    assert object_templates.get_version(router.id, 2) == ObjectTemplateVersion(
        template_id=router.id,
        version=2,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=ObjectTemplateVersionRef(template_id=network_device.id, version=1),
    )


@pytest.mark.parametrize("route", ["create", "revise"])
def test_duplicate_local_component_names_map_to_422(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
    route: str,
) -> None:
    client, datatypes, _object_templates, commits = client_context
    datatype, _versions = _store_datatype(datatypes)
    target = _create_published_component_target_versions(client, name="network_interface")
    components = [
        _component_request(target["object_template"]["id"], name="interfaces"),
        _component_request(target["object_template"]["id"], name="interfaces"),
    ]

    if route == "create":
        before = commits[0]
        response = client.post(
            "/api/v1/object-templates",
            json={
                "namespace": "network",
                "name": "device_with_duplicate_components",
                "description": None,
                "abstract": False,
                "properties": [],
                "components": components,
            },
        )
        assert commits[0] == before
    else:
        created = _create_object_template(
            client,
            datatype_id=datatype.id,
            properties=[{"name": "hostname", "datatype_id": str(datatype.id), "required": True}],
        )
        before = commits[0]
        response = client.put(
            f"/api/v1/object-templates/{created['object_template']['id']}/versions/1",
            json={"parent": None, "properties": [], "components": components},
        )
        assert commits[0] == before

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "duplicate_object_template_component"


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


def test_read_version_responses_return_local_components_only(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
) -> None:
    client, _datatypes, _object_templates, _commits = client_context
    parent_target = _create_published_component_target_versions(client, name="network_interface")
    child_target = _create_published_component_target_versions(client, name="routing_engine")

    parent = _create_object_template(
        client,
        properties=[],
        components=[_component_request(parent_target["object_template"]["id"], name="interfaces")],
        name="network_device",
    )
    _publish_object_template_version(client, parent["object_template"]["id"])

    child = _create_object_template(
        client,
        properties=[],
        parent={"template_id": parent["object_template"]["id"], "version": 1},
        components=[
            _component_request(
                child_target["object_template"]["id"],
                name="routing_engines",
            )
        ],
        name="router",
    )

    listed = client.get(f"/api/v1/object-templates/{child['object_template']['id']}/versions")
    exact = client.get(f"/api/v1/object-templates/{child['object_template']['id']}/versions/1")

    expected = [
        {
            "name": "routing_engines",
            "template_id": child_target["object_template"]["id"],
        }
    ]
    assert listed.status_code == 200
    assert listed.json()[0]["components"] == expected
    assert exact.status_code == 200
    assert exact.json()["components"] == expected


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
    parent_template = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="base_device",
        description=None,
        abstract=False,
    )
    _object_templates.add(parent_template)
    _object_templates.add_version(
        ObjectTemplateVersion(
            template_id=parent_template.id,
            version=1,
            status=ObjectTemplateVersionStatus.DRAFT,
            properties=(),
        )
    )
    _object_templates.replace_version(
        ObjectTemplateVersion(
            template_id=parent_template.id,
            version=1,
            status=ObjectTemplateVersionStatus.PUBLISHED,
            properties=(),
        )
    )
    created = _create_object_template(
        client,
        datatype_id=datatype.id,
        parent={"template_id": str(parent_template.id), "version": 1},
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


def test_revise_components_add_replace_and_clear_local_snapshot(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
) -> None:
    client, _datatypes, _object_templates, _commits = client_context
    first_target = _create_published_component_target_versions(
        client,
        name="network_interface",
        published_versions=2,
    )
    second_target = _create_published_component_target_versions(client, name="module")
    created = _create_object_template(client, properties=[], name="device")
    template_id = created["object_template"]["id"]

    added = client.put(
        f"/api/v1/object-templates/{template_id}/versions/1",
        json={
            "parent": None,
            "properties": [],
            "components": [_component_request(first_target["object_template"]["id"])],
        },
    )
    replaced = client.put(
        f"/api/v1/object-templates/{template_id}/versions/1",
        json={
            "parent": None,
            "properties": [],
            "components": [
                _component_request(
                    second_target["object_template"]["id"],
                    name="modules",
                )
            ],
        },
    )
    cleared = client.put(
        f"/api/v1/object-templates/{template_id}/versions/1",
        json={"parent": None, "properties": [], "components": []},
    )

    assert added.status_code == 200
    assert added.json()["components"] == [
        {
            "name": "interfaces",
            "template_id": first_target["object_template"]["id"],
        }
    ]
    assert replaced.status_code == 200
    assert replaced.json()["components"] == [
        {
            "name": "modules",
            "template_id": second_target["object_template"]["id"],
        }
    ]
    assert cleared.status_code == 200
    assert cleared.json()["components"] == []


def test_revise_omitted_components_means_empty_local_component_snapshot(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
) -> None:
    client, _datatypes, _object_templates, _commits = client_context
    target = _create_published_component_target_versions(client, name="network_interface")
    created = _create_object_template(
        client,
        properties=[],
        components=[_component_request(target["object_template"]["id"])],
        name="device",
    )

    response = client.put(
        f"/api/v1/object-templates/{created['object_template']['id']}/versions/1",
        json={"parent": None, "properties": []},
    )

    assert response.status_code == 200
    assert response.json()["components"] == []


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
    assert payload["components"] == []


def test_create_next_accepts_deprecated_source(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
) -> None:
    client, datatypes, _object_templates, _commits = client_context
    datatype, _versions = _store_datatype(datatypes)
    parent = _create_published_parent_template(
        client,
        datatype_id=datatype.id,
        name="base_deprecated",
    )
    created = _create_object_template(
        client,
        datatype_id=datatype.id,
        parent={"template_id": parent["object_template"]["id"], "version": 1},
        properties=[{"name": "serial", "datatype_id": str(datatype.id), "required": False}],
        name="device_deprecated_source",
    )
    template_id = created["object_template"]["id"]

    assert (
        client.post(f"/api/v1/object-templates/{template_id}/versions/1/publish").status_code
        == 200
    )
    created_v2 = client.post(
        f"/api/v1/object-templates/{template_id}/versions",
        json={"source_version": 1},
    )
    assert created_v2.status_code == 201
    assert (
        client.post(f"/api/v1/object-templates/{template_id}/versions/2/publish").status_code
        == 200
    )
    assert (
        client.post(
            f"/api/v1/object-templates/{template_id}/versions/1/deprecate"
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/v1/object-templates/{template_id}/versions/2/deprecate"
        ).status_code
        == 200
    )

    next_version = client.post(
        f"/api/v1/object-templates/{template_id}/versions",
        json={"source_version": 2},
    )
    versions = client.get(f"/api/v1/object-templates/{template_id}/versions")

    assert next_version.status_code == 201
    payload = next_version.json()
    assert payload["version"] == 3
    assert payload["status"] == "draft"
    assert payload["parent"] == {
        "template_id": parent["object_template"]["id"],
        "version": 1,
    }
    assert payload["properties"] == [
        {
            "name": "serial",
            "datatype_id": str(datatype.id),
            "datatype_version": 1,
            "required": False,
        }
    ]
    assert payload["components"] == []
    assert [(item["version"], item["status"]) for item in versions.json()] == [
        (1, "deprecated"),
        (2, "deprecated"),
        (3, "draft"),
    ]


def test_create_next_does_not_upgrade_component_pins(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
) -> None:
    client, _datatypes, _object_templates, _commits = client_context
    target = _create_published_component_target_versions(client, name="network_interface")
    created = _create_object_template(
        client,
        properties=[],
        components=[_component_request(target["object_template"]["id"])],
        name="network_device",
    )
    _publish_object_template_version(client, created["object_template"]["id"])

    newer_target = client.post(
        f"/api/v1/object-templates/{target['object_template']['id']}/versions",
        json={"source_version": 1},
    )
    assert newer_target.status_code == 201
    _publish_object_template_version(client, target["object_template"]["id"], 2)

    next_version = client.post(
        f"/api/v1/object-templates/{created['object_template']['id']}/versions",
        json={"source_version": 1},
    )

    assert next_version.status_code == 201
    assert next_version.json()["components"] == [
        {
            "name": "interfaces",
            "template_id": target["object_template"]["id"],
        }
    ]


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


def test_revise_parent_identity_change_maps_to_conflict(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
) -> None:
    client, datatypes, _object_templates, _commits = client_context
    datatype, _versions = _store_datatype(datatypes)
    parent_p = _create_object_template(client, datatype_id=datatype.id, name="device")
    parent_q = _create_object_template(client, datatype_id=datatype.id, name="service")
    _publish_object_template_version(client, parent_p["object_template"]["id"])
    _publish_object_template_version(client, parent_q["object_template"]["id"])
    child = _create_object_template(
        client,
        datatype_id=datatype.id,
        name="router",
        parent={"template_id": parent_p["object_template"]["id"], "version": 1},
        properties=[
            {
                "name": "serial",
                "datatype_id": str(datatype.id),
                "required": False,
            }
        ],
    )
    child_id = child["object_template"]["id"]
    _publish_object_template_version(client, child_id)
    assert client.post(
        f"/api/v1/object-templates/{child_id}/versions",
        json={"source_version": 1},
    ).status_code == 201

    response = client.put(
        f"/api/v1/object-templates/{child_id}/versions/2",
        json={
            "parent": {"template_id": parent_q["object_template"]["id"], "version": 1},
            "properties": child["version"]["properties"],
            "components": [],
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "object_template_parent_identity_changed"


def test_revise_parent_version_downgrade_maps_to_conflict(
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
    parent_id = parent["object_template"]["id"]
    _publish_object_template_version(client, parent_id)
    assert client.post(
        f"/api/v1/object-templates/{parent_id}/versions",
        json={"source_version": 1},
    ).status_code == 201
    _publish_object_template_version(client, parent_id, 2)
    assert client.post(
        f"/api/v1/object-templates/{parent_id}/versions",
        json={"source_version": 2},
    ).status_code == 201
    _publish_object_template_version(client, parent_id, 3)

    child = _create_object_template(
        client,
        datatype_id=datatype.id,
        name="router",
        parent={"template_id": parent_id, "version": 3},
        properties=[
            {
                "name": "serial",
                "datatype_id": str(datatype.id),
                "required": False,
            }
        ],
    )
    child_id = child["object_template"]["id"]
    _publish_object_template_version(client, child_id)
    assert client.post(
        f"/api/v1/object-templates/{child_id}/versions",
        json={"source_version": 1},
    ).status_code == 201

    response = client.put(
        f"/api/v1/object-templates/{child_id}/versions/2",
        json={
            "parent": {"template_id": parent_id, "version": 1},
            "properties": child["version"]["properties"],
            "components": [],
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "object_template_parent_version_downgrade"


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


def test_publish_component_not_published_mapping(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
) -> None:
    client, _datatypes, _object_templates, _commits = client_context
    target = _create_published_component_target_versions(client, name="network_interface")
    created = _create_object_template(
        client,
        properties=[],
        components=[_component_request(target["object_template"]["id"])],
        name="network_device",
    )
    _deprecate_object_template_version(client, target["object_template"]["id"], 1)

    response = client.post(
        f"/api/v1/object-templates/{created['object_template']['id']}/versions/1/publish"
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "object_template_component_version_not_published"


def test_publish_component_target_identity_with_another_published_version_still_succeeds(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
) -> None:
    client, _datatypes, _object_templates, _commits = client_context
    target = _create_published_component_target_versions(
        client,
        name="network_interface",
        published_versions=2,
    )
    created = _create_object_template(
        client,
        properties=[],
        components=[_component_request(target["object_template"]["id"])],
        name="network_device",
    )
    _deprecate_object_template_version(client, target["object_template"]["id"], 1)

    response = client.post(
        f"/api/v1/object-templates/{created['object_template']['id']}/versions/1/publish"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "published"


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


def test_publish_inherited_component_conflict_mapping(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
) -> None:
    client, _datatypes, _object_templates, _commits = client_context
    parent_target = _create_published_component_target_versions(client, name="network_interface")
    child_target = _create_published_component_target_versions(client, name="physical_interface")
    parent = _create_object_template(
        client,
        properties=[],
        components=[_component_request(parent_target["object_template"]["id"], name="interfaces")],
        name="network_device",
    )
    _publish_object_template_version(client, parent["object_template"]["id"])
    child = _create_object_template(
        client,
        properties=[],
        parent={"template_id": parent["object_template"]["id"], "version": 1},
        components=[_component_request(child_target["object_template"]["id"], name="interfaces")],
        name="router",
    )

    response = client.post(
        f"/api/v1/object-templates/{child['object_template']['id']}/versions/1/publish"
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "inherited_object_template_component_conflict"


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

    with TestClient(create_app(factory, model_write_uow_factory=factory)) as client:
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
    assert "delete" in payload["paths"]["/api/v1/object-templates/{template_id}"]
    assert "/api/v1/object-templates/{template_id}/versions/{version}" in payload["paths"]
    assert "/api/v1/datatypes" in payload["paths"]
    assert "CreateObjectTemplateRequest" in payload["components"]["schemas"]
    assert "ObjectTemplateVersionResponse" in payload["components"]["schemas"]
    component_request = payload["components"]["schemas"]["ObjectTemplateComponentRequest"]
    component_response = payload["components"]["schemas"]["ObjectTemplateComponentResponse"]
    assert set(component_request["properties"]) == {"name", "template_id"}
    assert set(component_response["properties"]) == {"name", "template_id"}


def test_delete_object_template_returns_204_and_commits_once(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
) -> None:
    client, _datatypes, _object_templates, commits = client_context
    created = _create_object_template(
        client,
        datatype_id=None,
        properties=[],
        name="standalone",
    )
    template_id = created["object_template"]["id"]
    before = commits[0]

    response = client.delete(f"/api/v1/object-templates/{template_id}")

    assert response.status_code == 204
    assert response.content == b""
    assert commits[0] == before + 1
    assert client.get(f"/api/v1/object-templates/{template_id}").status_code == 404


def test_delete_object_template_missing_returns_404(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
) -> None:
    client, _datatypes, _object_templates, commits = client_context
    before = commits[0]

    response = client.delete(f"/api/v1/object-templates/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "object_template_not_found"
    assert commits[0] == before


def test_delete_object_template_in_use_returns_409(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
) -> None:
    client, _datatypes, _object_templates, commits = client_context
    parent = _create_object_template(
        client,
        datatype_id=None,
        properties=[],
        name="device",
    )
    _create_object_template(
        client,
        datatype_id=None,
        properties=[],
        name="router",
        parent={"template_id": parent["object_template"]["id"], "version": 1},
    )
    before = commits[0]

    response = client.delete(
        f"/api/v1/object-templates/{parent['object_template']['id']}"
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "object_template_in_use"
    assert commits[0] == before


def test_delete_object_template_malformed_uuid_returns_422(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        list[int],
    ],
) -> None:
    client, _datatypes, _object_templates, _commits = client_context

    response = client.delete("/api/v1/object-templates/not-a-uuid")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "request_validation_failed"
