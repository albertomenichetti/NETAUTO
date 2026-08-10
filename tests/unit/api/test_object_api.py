from __future__ import annotations

from collections.abc import Generator
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from netauto.api.app import create_app
from netauto.application.unit_of_work import ObjectUnitOfWork
from netauto.core.datatype import (
    Constraint,
    ConstraintName,
    DataType,
    DataTypeFactory,
    DataTypeVersion,
    DataTypeVersioningService,
)
from netauto.core.object import ComponentMembership, Object, ObjectPersistenceError
from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateProperty,
    ObjectTemplateVersion,
    ObjectTemplateVersionRef,
    ObjectTemplateVersionStatus,
)
from netauto.persistence.memory.datatype_repository import InMemoryDataTypeRepository
from netauto.persistence.memory.object_repository import InMemoryObjectRepository
from netauto.persistence.memory.objecttemplate_repository import InMemoryObjectTemplateRepository
from netauto.persistence.memory.relationship_repository import (
    InMemoryRelationshipDefinitionRepository,
)


class FakeUnitOfWork(ObjectUnitOfWork):
    def __init__(
        self,
        datatypes: InMemoryDataTypeRepository,
        object_templates: InMemoryObjectTemplateRepository,
        objects: InMemoryObjectRepository,
        relationship_definitions: InMemoryRelationshipDefinitionRepository,
        commit_counter: list[int],
    ) -> None:
        self._datatypes = datatypes
        self._object_templates = object_templates
        self._objects = objects
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
    def objects(self) -> InMemoryObjectRepository:
        return self._objects

    def __enter__(self) -> FakeUnitOfWork:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    def commit(self) -> None:
        self._commit_counter[0] += 1


class BrokenObjectRepository(InMemoryObjectRepository):
    def list(self) -> tuple[Object, ...]:
        raise ObjectPersistenceError("boom")


class BrokenObjectUnitOfWork(FakeUnitOfWork):
    def __init__(self) -> None:
        super().__init__(
            InMemoryDataTypeRepository(),
            InMemoryObjectTemplateRepository(),
            BrokenObjectRepository(),
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
            InMemoryObjectRepository,
            list[int],
        ],
        None,
        None,
    ]
):
    datatypes = InMemoryDataTypeRepository()
    object_templates = InMemoryObjectTemplateRepository()
    objects = InMemoryObjectRepository()
    relationship_definitions = InMemoryRelationshipDefinitionRepository()
    commits = [0]

    def factory() -> FakeUnitOfWork:
        return FakeUnitOfWork(
            datatypes,
            object_templates,
            objects,
            relationship_definitions,
            commits,
        )

    with TestClient(create_app(factory)) as client:
        yield client, datatypes, object_templates, objects, commits


def _store_datatype(
    repo: InMemoryDataTypeRepository,
    *,
    namespace: str = "network",
    name: str = "hostname",
    base_type: str = "core.string",
    constraints: tuple[Constraint, ...] = (),
) -> tuple[DataType, DataTypeVersion]:
    datatype, draft = DataTypeFactory().create(
        namespace=namespace,
        name=name,
        description=f"{name} datatype",
        base_type=base_type,
        constraints=constraints,
    )
    repo.add(datatype)
    published = DataTypeVersioningService().publish(draft)
    repo.add_version(published)
    return datatype, published


def _store_deprecated_datatype(
    repo: InMemoryDataTypeRepository,
    *,
    namespace: str = "network",
    name: str = "hostname",
    base_type: str = "core.string",
) -> tuple[DataType, DataTypeVersion]:
    datatype, published = _store_datatype(
        repo,
        namespace=namespace,
        name=name,
        base_type=base_type,
    )
    deprecated = DataTypeVersioningService().deprecate(published)
    repo.replace_version(deprecated)
    return datatype, deprecated


def _store_template(
    repo: InMemoryObjectTemplateRepository,
    *,
    namespace: str = "network",
    name: str = "device",
    abstract: bool = False,
    version_status: ObjectTemplateVersionStatus = ObjectTemplateVersionStatus.PUBLISHED,
    version_number: int = 1,
    parent: ObjectTemplateVersionRef | None = None,
    properties: tuple[ObjectTemplateProperty, ...] = (),
) -> tuple[ObjectTemplate, ObjectTemplateVersion]:
    template = ObjectTemplate(
        id=uuid4(),
        namespace=namespace,
        name=name,
        description=f"{name} template",
        abstract=abstract,
    )
    version = ObjectTemplateVersion(
        template_id=template.id,
        version=version_number,
        status=version_status,
        parent=parent,
        properties=properties,
    )
    repo.add(template)
    repo.add_version(version)
    return template, version


def _property(
    name: str,
    *,
    datatype_id: UUID,
    datatype_version: int,
    required: bool = False,
) -> ObjectTemplateProperty:
    return ObjectTemplateProperty(
        name=name,
        datatype_id=datatype_id,
        datatype_version=datatype_version,
        required=required,
    )


def _create_object(
    client: TestClient,
    *,
    template_id: UUID,
    template_version: int,
    properties: dict[str, object] | None = None,
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/objects",
        json={
            "template_id": str(template_id),
            "template_version": template_version,
            "properties": properties or {},
        },
    )
    assert response.status_code == 201
    return response.json()


def test_create_request_validation_is_strict(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        list[int],
    ],
) -> None:
    client, _datatypes, _templates, _objects, _commits = client_context

    cases = [
        (
            {"template_id": str(uuid4()), "template_version": True, "properties": {}},
            "/body/template_version",
        ),
        (
            {"template_id": str(uuid4()), "template_version": "1", "properties": {}},
            "/body/template_version",
        ),
        (
            {"template_id": str(uuid4()), "template_version": 0, "properties": {}},
            "/body/template_version",
        ),
        (
            {"template_id": "not-a-uuid", "template_version": 1, "properties": {}},
            "/body/template_id",
        ),
        (
            {
                "template_id": str(uuid4()),
                "template_version": 1,
                "properties": [],
            },
            "/body/properties",
        ),
        (
            {
                "template_id": str(uuid4()),
                "template_version": 1,
                "properties": {},
                "extra": 1,
            },
            "/body/extra",
        ),
    ]

    for payload, path in cases:
        response = client.post("/api/v1/objects", json=payload)
        assert response.status_code == 422
        body = response.json()
        assert "detail" not in body
        assert body["error"]["code"] == "request_validation_failed"
        assert any(detail["path"] == path for detail in body["error"]["details"])


def test_create_object_and_list_and_get_round_trip(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        list[int],
    ],
) -> None:
    client, datatypes, templates, _objects, commits = client_context
    datatype, datatype_version = _store_datatype(datatypes)
    template, _version = _store_template(
        templates,
        properties=(
            _property(
                "hostname",
                datatype_id=datatype.id,
                datatype_version=datatype_version.version,
                required=True,
            ),
            _property(
                "serial",
                datatype_id=datatype.id,
                datatype_version=datatype_version.version,
            ),
        ),
    )

    empty = client.get("/api/v1/objects")
    created = _create_object(
        client,
        template_id=template.id,
        template_version=1,
        properties={"hostname": "router-01", "serial": "ABC"},
    )
    listed = client.get("/api/v1/objects")
    loaded = client.get(f"/api/v1/objects/{created['id']}")

    assert empty.status_code == 200
    assert empty.json() == []
    assert listed.status_code == 200
    assert loaded.status_code == 200
    assert created["template_id"] == str(template.id)
    assert created["template_version"] == 1
    assert created["properties"] == {"hostname": "router-01", "serial": "ABC"}
    assert "owner" not in created
    assert "components" not in created
    assert listed.json() == [created]
    assert loaded.json() == created
    assert commits[0] == 1


def test_list_preserves_repository_order_where_practical(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        list[int],
    ],
) -> None:
    client, datatypes, templates, objects, _commits = client_context
    datatype, datatype_version = _store_datatype(datatypes)
    template, _version = _store_template(
        templates,
        properties=(
            _property(
                "hostname",
                datatype_id=datatype.id,
                datatype_version=datatype_version.version,
            ),
        ),
    )
    first = Object(
        id=UUID("00000000-0000-0000-0000-000000000002"),
        template_id=template.id,
        template_version=1,
        properties={"hostname": "router-02"},
    )
    second = Object(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        template_id=template.id,
        template_version=1,
        properties={"hostname": "router-01"},
    )
    objects.add(first)
    objects.add(second)

    response = client.get("/api/v1/objects")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [str(second.id), str(first.id)]


def test_get_missing_object_maps_to_404(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        list[int],
    ],
) -> None:
    client, _datatypes, _templates, _objects, _commits = client_context

    response = client.get(f"/api/v1/objects/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "object_not_found"


def test_create_semantic_errors_and_structured_object_validation(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        list[int],
    ],
) -> None:
    client, datatypes, templates, _objects, _commits = client_context
    datatype, datatype_version = _store_datatype(
        datatypes,
        constraints=(Constraint(name=ConstraintName.MIN_LENGTH, value=3),),
    )

    missing_template = client.post(
        "/api/v1/objects",
        json={"template_id": str(uuid4()), "template_version": 1, "properties": {}},
    )
    assert missing_template.status_code == 404
    assert missing_template.json()["error"]["code"] == "object_template_not_found"

    template_no_version = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="missing_version_template",
        description=None,
        abstract=False,
    )
    templates.add(template_no_version)
    missing_version = client.post(
        "/api/v1/objects",
        json={
            "template_id": str(template_no_version.id),
            "template_version": 1,
            "properties": {},
        },
    )
    assert missing_version.status_code == 404
    assert missing_version.json()["error"]["code"] == "object_template_version_not_found"

    draft_template, _draft_version = _store_template(
        templates,
        name="draft_template",
        version_status=ObjectTemplateVersionStatus.DRAFT,
        properties=(
            _property(
                "hostname",
                datatype_id=datatype.id,
                datatype_version=datatype_version.version,
                required=True,
            ),
        ),
    )
    draft_response = client.post(
        "/api/v1/objects",
        json={
            "template_id": str(draft_template.id),
            "template_version": 1,
            "properties": {"hostname": "router-01"},
        },
    )
    assert draft_response.status_code == 409
    assert draft_response.json()["error"]["code"] == "object_template_version_not_published"

    deprecated_template, _deprecated_version = _store_template(
        templates,
        name="deprecated_template",
        version_status=ObjectTemplateVersionStatus.DEPRECATED,
        properties=(
            _property(
                "hostname",
                datatype_id=datatype.id,
                datatype_version=datatype_version.version,
                required=True,
            ),
        ),
    )
    deprecated_response = client.post(
        "/api/v1/objects",
        json={
            "template_id": str(deprecated_template.id),
            "template_version": 1,
            "properties": {"hostname": "router-01"},
        },
    )
    assert deprecated_response.status_code == 409
    assert deprecated_response.json()["error"]["code"] == "object_template_version_not_published"

    abstract_template, _abstract_version = _store_template(
        templates,
        name="abstract_template",
        abstract=True,
        properties=(
            _property(
                "hostname",
                datatype_id=datatype.id,
                datatype_version=datatype_version.version,
                required=True,
            ),
        ),
    )
    abstract_response = client.post(
        "/api/v1/objects",
        json={
            "template_id": str(abstract_template.id),
            "template_version": 1,
            "properties": {"hostname": "router-01"},
        },
    )
    assert abstract_response.status_code == 409
    assert abstract_response.json()["error"]["code"] == "abstract_object_template_instantiation"

    valid_template, _valid_version = _store_template(
        templates,
        name="router",
        properties=(
            _property(
                "hostname",
                datatype_id=datatype.id,
                datatype_version=datatype_version.version,
                required=True,
            ),
        ),
    )

    required_response = client.post(
        "/api/v1/objects",
        json={"template_id": str(valid_template.id), "template_version": 1, "properties": {}},
    )
    unknown_response = client.post(
        "/api/v1/objects",
        json={
            "template_id": str(valid_template.id),
            "template_version": 1,
            "properties": {"banana": "yellow"},
        },
    )
    invalid_response = client.post(
        "/api/v1/objects",
        json={
            "template_id": str(valid_template.id),
            "template_version": 1,
            "properties": {"hostname": "x"},
        },
    )

    assert required_response.status_code == 422
    assert required_response.json()["error"]["code"] == "object_validation_failed"
    assert required_response.json()["error"]["details"] == [
        {
            "path": "/properties/hostname",
            "code": "required",
            "message": "Required property is missing",
        }
    ]

    assert unknown_response.status_code == 422
    assert unknown_response.json()["error"]["code"] == "object_validation_failed"
    assert unknown_response.json()["error"]["details"] == [
        {
            "path": "/properties/banana",
            "code": "unknown_property",
            "message": "Property is not defined in template",
        },
        {
            "path": "/properties/hostname",
            "code": "required",
            "message": "Required property is missing",
        },
    ]

    assert invalid_response.status_code == 422
    assert invalid_response.json()["error"]["code"] == "object_validation_failed"
    assert invalid_response.json()["error"]["details"] == [
        {
            "path": "/properties/hostname",
            "code": "min_length",
            "message": "Value is shorter than the minimum allowed length",
        }
    ]


def test_dynamic_property_values_are_not_coerced(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        list[int],
    ],
) -> None:
    client, datatypes, templates, _objects, _commits = client_context
    datatype, datatype_version = _store_datatype(
        datatypes,
        name="vlan",
        base_type="core.integer",
        constraints=(
            Constraint(name=ConstraintName.MINIMUM, value=1),
            Constraint(name=ConstraintName.MAXIMUM, value=4094),
        ),
    )
    template, _version = _store_template(
        templates,
        name="vlan_object",
        properties=(
            _property(
                "vlan",
                datatype_id=datatype.id,
                datatype_version=datatype_version.version,
                required=True,
            ),
        ),
    )

    string_value = client.post(
        "/api/v1/objects",
        json={
            "template_id": str(template.id),
            "template_version": 1,
            "properties": {"vlan": "100"},
        },
    )
    bool_value = client.post(
        "/api/v1/objects",
        json={
            "template_id": str(template.id),
            "template_version": 1,
            "properties": {"vlan": True},
        },
    )

    assert string_value.status_code == 422
    assert string_value.json()["error"]["code"] == "object_validation_failed"
    assert string_value.json()["error"]["details"] == [
        {
            "path": "/properties/vlan",
            "code": "type",
            "message": "Value is not of the expected type",
        }
    ]
    assert bool_value.status_code == 422
    assert bool_value.json()["error"]["code"] == "object_validation_failed"
    assert bool_value.json()["error"]["details"] == [
        {
            "path": "/properties/vlan",
            "code": "type",
            "message": "Value is not of the expected type",
        }
    ]


def test_patch_request_validation_and_semantic_translation(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        list[int],
    ],
) -> None:
    client, datatypes, templates, _objects, commits = client_context
    datatype, datatype_version = _store_datatype(datatypes)
    template, _version = _store_template(
        templates,
        properties=(
            _property(
                "hostname",
                datatype_id=datatype.id,
                datatype_version=datatype_version.version,
                required=True,
            ),
            _property(
                "serial",
                datatype_id=datatype.id,
                datatype_version=datatype_version.version,
            ),
        ),
    )
    created = _create_object(
        client,
        template_id=template.id,
        template_version=1,
        properties={"hostname": "router-01", "serial": "ABC"},
    )
    commits[0] = 0

    request_validation_cases = [
        ({"remove_properties": [1]}, "/body/remove_properties/0"),
        ({"extra": 1}, "/body/extra"),
        ({"template_id": str(uuid4())}, "/body/template_id"),
        ({"template_version": 2}, "/body/template_version"),
    ]
    for payload, path in request_validation_cases:
        response = client.patch(f"/api/v1/objects/{created['id']}", json=payload)
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "request_validation_failed"
        assert any(detail["path"] == path for detail in response.json()["error"]["details"])

    patched = client.patch(
        f"/api/v1/objects/{created['id']}",
        json={"properties": {"hostname": "router-02"}},
    )
    assert patched.status_code == 200
    assert patched.json()["properties"] == {"hostname": "router-02", "serial": "ABC"}
    assert patched.json()["template_id"] == created["template_id"]
    assert patched.json()["template_version"] == created["template_version"]

    removed = client.patch(
        f"/api/v1/objects/{created['id']}",
        json={"remove_properties": ["serial"]},
    )
    assert removed.status_code == 200
    assert removed.json()["properties"] == {"hostname": "router-02"}

    overlap = client.patch(
        f"/api/v1/objects/{created['id']}",
        json={"properties": {"serial": "NEW"}, "remove_properties": ["serial"]},
    )
    assert overlap.status_code == 422
    assert overlap.json()["error"]["code"] == "invalid_object_patch"

    unknown_removal = client.patch(
        f"/api/v1/objects/{created['id']}",
        json={"remove_properties": ["banana"]},
    )
    assert unknown_removal.status_code == 422
    assert unknown_removal.json()["error"]["code"] == "invalid_object_patch"

    required_removal = client.patch(
        f"/api/v1/objects/{created['id']}",
        json={"remove_properties": ["hostname"]},
    )
    assert required_removal.status_code == 422
    assert required_removal.json()["error"]["code"] == "object_validation_failed"
    assert required_removal.json()["error"]["details"] == [
        {
            "path": "/properties/hostname",
            "code": "required",
            "message": "Required property is missing",
        }
    ]

    unknown_set = client.patch(
        f"/api/v1/objects/{created['id']}",
        json={"properties": {"banana": "yellow"}},
    )
    assert unknown_set.status_code == 422
    assert unknown_set.json()["error"]["code"] == "object_validation_failed"
    assert unknown_set.json()["error"]["details"] == [
        {
            "path": "/properties/banana",
            "code": "unknown_property",
            "message": "Property is not defined in template",
        }
    ]

    none_value = client.patch(
        f"/api/v1/objects/{created['id']}",
        json={"properties": {"hostname": None}},
    )
    assert none_value.status_code == 422
    assert none_value.json()["error"]["code"] == "object_validation_failed"
    assert none_value.json()["error"]["details"] == [
        {
            "path": "/properties/hostname",
            "code": "type",
            "message": "Value is not of the expected type",
        }
    ]

    assert commits[0] == 2


def test_patch_works_against_deprecated_pinned_template_version(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        list[int],
    ],
) -> None:
    client, datatypes, templates, _objects, _commits = client_context
    datatype, datatype_version = _store_deprecated_datatype(datatypes)
    template, version = _store_template(
        templates,
        properties=(
            _property(
                "hostname",
                datatype_id=datatype.id,
                datatype_version=datatype_version.version,
                required=True,
            ),
        ),
    )
    created = _create_object(
        client,
        template_id=template.id,
        template_version=1,
        properties={"hostname": "router-01"},
    )

    deprecated_version = ObjectTemplateVersion(
        template_id=version.template_id,
        version=version.version,
        status=ObjectTemplateVersionStatus.DEPRECATED,
        parent=version.parent,
        properties=version.properties,
        components=version.components,
    )
    templates.replace_version(deprecated_version)

    patched = client.patch(
        f"/api/v1/objects/{created['id']}",
        json={"properties": {"hostname": "router-02"}},
    )

    assert patched.status_code == 200
    assert patched.json()["template_id"] == str(template.id)
    assert patched.json()["template_version"] == 1
    assert patched.json()["properties"] == {"hostname": "router-02"}


def test_delete_returns_204_and_delegates_subtree_cascade(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        list[int],
    ],
) -> None:
    client, _datatypes, _templates, objects, commits = client_context
    a = Object(id=uuid4(), template_id=uuid4(), template_version=1, properties={})
    b = Object(id=uuid4(), template_id=uuid4(), template_version=1, properties={})
    c = Object(id=uuid4(), template_id=uuid4(), template_version=1, properties={})
    objects.add(a)
    objects.add(b)
    objects.add(c)
    objects.add_membership(
        ComponentMembership(parent_object_id=a.id, slot_name="children", child_object_id=b.id)
    )
    objects.add_membership(
        ComponentMembership(parent_object_id=b.id, slot_name="children", child_object_id=c.id)
    )

    response = client.delete(f"/api/v1/objects/{a.id}")
    missing_a = client.get(f"/api/v1/objects/{a.id}")
    missing_b = client.get(f"/api/v1/objects/{b.id}")
    missing_c = client.get(f"/api/v1/objects/{c.id}")

    assert response.status_code == 204
    assert response.content == b""
    assert missing_a.status_code == 404
    assert missing_b.status_code == 404
    assert missing_c.status_code == 404
    assert commits[0] == 1


def test_delete_missing_object_maps_to_404(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        list[int],
    ],
) -> None:
    client, _datatypes, _templates, _objects, _commits = client_context

    response = client.delete(f"/api/v1/objects/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "object_not_found"


def test_object_persistence_error_maps_to_500() -> None:
    def factory() -> BrokenObjectUnitOfWork:
        return BrokenObjectUnitOfWork()

    with TestClient(create_app(factory)) as client:
        response = client.get("/api/v1/objects")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "persistence_error"


def test_openapi_documents_object_routes_and_schemas(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        list[int],
    ],
) -> None:
    client, _datatypes, _templates, _objects, _commits = client_context

    response = client.get("/openapi.json")

    assert response.status_code == 200
    payload = response.json()
    assert "/api/v1/objects" in payload["paths"]
    assert "/api/v1/objects/{object_id}" in payload["paths"]
    assert "CreateObjectRequest" in payload["components"]["schemas"]
    assert "UpdateObjectRequest" in payload["components"]["schemas"]
    assert "ObjectResponse" in payload["components"]["schemas"]
    assert payload["components"]["schemas"]["CreateObjectRequest"]["properties"][
        "template_version"
    ] == {"minimum": 1, "title": "Template Version", "type": "integer"}
