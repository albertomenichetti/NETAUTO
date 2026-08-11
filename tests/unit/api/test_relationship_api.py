from __future__ import annotations

from collections.abc import Generator
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from netauto.api.app import create_app
from netauto.application.unit_of_work import ObjectUnitOfWork
from netauto.core.object import Object
from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateVersion,
    ObjectTemplateVersionRef,
    ObjectTemplateVersionStatus,
)
from netauto.core.relationship import (
    Relationship,
    RelationshipDefinition,
    RelationshipDefinitionPersistenceError,
    RelationshipPersistenceError,
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
    def objects(self) -> InMemoryObjectRepository:
        return self._objects

    @property
    def object_changes(self) -> InMemoryObjectChangeRepository:
        return self._object_changes

    @property
    def relationships(self) -> InMemoryRelationshipRepository:
        return self._relationships

    @property
    def relationship_definitions(self) -> InMemoryRelationshipDefinitionRepository:
        return self._relationship_definitions

    def __enter__(self) -> FakeUnitOfWork:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    def commit(self) -> None:
        self._commit_counter[0] += 1


class BrokenRelationshipDefinitionRepository(InMemoryRelationshipDefinitionRepository):
    def list(self) -> tuple[RelationshipDefinition, ...]:
        raise RelationshipDefinitionPersistenceError("boom")


class BrokenRelationshipRepository(InMemoryRelationshipRepository):
    def list_by_definition(self, relationship_definition_id: UUID) -> tuple[Relationship, ...]:
        del relationship_definition_id
        raise RelationshipPersistenceError("boom")


class BrokenRuntimeRelationshipRepository(InMemoryRelationshipRepository):
    def list(self) -> tuple[Relationship, ...]:
        raise RelationshipPersistenceError("boom")


class BrokenRelationshipUnitOfWork(FakeUnitOfWork):
    def __init__(self) -> None:
        super().__init__(
            InMemoryDataTypeRepository(),
            InMemoryObjectTemplateRepository(),
            InMemoryObjectRepository(),
            InMemoryObjectChangeRepository(),
            InMemoryRelationshipRepository(),
            BrokenRelationshipDefinitionRepository(),
            [0],
        )


class BrokenLifecycleUnitOfWork(FakeUnitOfWork):
    definition_id = UUID("00000000-0000-0000-0000-000000000001")

    def __init__(self) -> None:
        source = ObjectTemplate(
            id=uuid4(),
            namespace="network",
            name="source",
            description="source template",
            abstract=False,
        )
        target = ObjectTemplate(
            id=uuid4(),
            namespace="network",
            name="target",
            description="target template",
            abstract=False,
        )
        object_templates = InMemoryObjectTemplateRepository()
        object_templates.add(source)
        object_templates.add(target)
        relationship_definitions = InMemoryRelationshipDefinitionRepository()
        relationship_definitions.add(
            RelationshipDefinition(
                id=self.definition_id,
                source_template_id=source.id,
                target_template_id=target.id,
                forward_name="uses",
                reverse_name="is_used_by",
            )
        )
        super().__init__(
            InMemoryDataTypeRepository(),
            object_templates,
            InMemoryObjectRepository(),
            InMemoryObjectChangeRepository(),
            BrokenRelationshipRepository(),
            relationship_definitions,
            [0],
        )


class BrokenRuntimeUnitOfWork(FakeUnitOfWork):
    def __init__(self) -> None:
        super().__init__(
            InMemoryDataTypeRepository(),
            InMemoryObjectTemplateRepository(),
            InMemoryObjectRepository(),
            InMemoryObjectChangeRepository(),
            BrokenRuntimeRelationshipRepository(),
            InMemoryRelationshipDefinitionRepository(),
            [0],
        )


@pytest.fixture
def client_context() -> (
    Generator[
        tuple[
            TestClient,
            InMemoryObjectTemplateRepository,
            InMemoryObjectRepository,
            InMemoryRelationshipDefinitionRepository,
            InMemoryRelationshipRepository,
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
        yield (
            client,
            object_templates,
            objects,
            relationship_definitions,
            relationships,
            commits,
        )


def _store_template(
    repo: InMemoryObjectTemplateRepository,
    *,
    name: str,
    abstract: bool = False,
    versions: tuple[ObjectTemplateVersion, ...],
) -> ObjectTemplate:
    template = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name=name,
        description=f"{name} template",
        abstract=abstract,
    )
    repo.add(template)
    for version in versions:
        repo.add_version(version)
    return template


def _store_published_template(
    repo: InMemoryObjectTemplateRepository,
    *,
    name: str,
) -> ObjectTemplate:
    template = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name=name,
        description=f"{name} template",
        abstract=False,
    )
    repo.add(template)
    repo.add_version(
        ObjectTemplateVersion(
            template_id=template.id,
            version=1,
            status=ObjectTemplateVersionStatus.PUBLISHED,
        )
    )
    return template


def _version(
    template_id: UUID,
    version: int,
    *,
    status: ObjectTemplateVersionStatus,
    parent: ObjectTemplateVersionRef | None = None,
) -> ObjectTemplateVersion:
    return ObjectTemplateVersion(
        template_id=template_id,
        version=version,
        status=status,
        parent=parent,
    )


def _definition(
    *,
    source_template_id: UUID,
    target_template_id: UUID,
    forward_name: str = "uses",
    reverse_name: str = "is_used_by",
    definition_id: UUID | None = None,
) -> RelationshipDefinition:
    return RelationshipDefinition(
        id=definition_id or uuid4(),
        source_template_id=source_template_id,
        target_template_id=target_template_id,
        forward_name=forward_name,
        reverse_name=reverse_name,
    )


def _relationship(
    *,
    relationship_definition_id: UUID,
    source_object_id: UUID,
    target_object_id: UUID,
    relationship_id: UUID | None = None,
) -> Relationship:
    return Relationship(
        id=relationship_id or uuid4(),
        relationship_definition_id=relationship_definition_id,
        source_object_id=source_object_id,
        target_object_id=target_object_id,
    )


def _store_object(
    repo: InMemoryObjectRepository,
    *,
    template_id: UUID,
    template_version: int = 1,
    object_id: UUID | None = None,
) -> Object:
    object_value = Object(
        id=object_id or uuid4(),
        template_id=template_id,
        template_version=template_version,
        properties={},
    )
    repo.add(object_value)
    return object_value


def test_create_list_show_and_delete_relationship_definition(
    client_context: tuple[
        TestClient,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        InMemoryRelationshipDefinitionRepository,
        InMemoryRelationshipRepository,
        list[int],
    ],
) -> None:
    client, object_templates, _objects, relationship_definitions, _relationships, commits = (
        client_context
    )
    source = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="source",
        description="source template",
        abstract=False,
    )
    target = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="target",
        description="target template",
        abstract=False,
    )
    object_templates.add(source)
    object_templates.add(target)
    object_templates.add_version(
        ObjectTemplateVersion(
            template_id=source.id,
            version=1,
            status=ObjectTemplateVersionStatus.PUBLISHED,
        )
    )
    object_templates.add_version(
        ObjectTemplateVersion(
            template_id=target.id,
            version=1,
            status=ObjectTemplateVersionStatus.PUBLISHED,
        )
    )

    created = client.post(
        "/api/v1/relationship-definitions",
        json={
            "source_template_id": str(source.id),
            "target_template_id": str(target.id),
            "forward_name": "uses",
            "reverse_name": "is_used_by",
        },
    )
    assert created.status_code == 201
    created_payload = created.json()
    definition_id = created_payload["id"]
    assert created_payload == {
        "id": definition_id,
        "source_template_id": str(source.id),
        "target_template_id": str(target.id),
        "forward_name": "uses",
        "reverse_name": "is_used_by",
    }
    assert commits[0] == 1

    listed = client.get("/api/v1/relationship-definitions")
    shown = client.get(f"/api/v1/relationship-definitions/{definition_id}")
    assert listed.status_code == 200
    assert listed.json() == [created_payload]
    assert shown.status_code == 200
    assert shown.json() == created_payload

    deleted = client.delete(f"/api/v1/relationship-definitions/{definition_id}")
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert commits[0] == 2
    assert relationship_definitions.get(UUID(definition_id)) is None

    missing = client.get(f"/api/v1/relationship-definitions/{definition_id}")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "relationship_definition_not_found"


def test_request_validation_and_identifier_errors(
    client_context: tuple[
        TestClient,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        InMemoryRelationshipDefinitionRepository,
        InMemoryRelationshipRepository,
        list[int],
    ],
) -> None:
    client, object_templates, _objects, _relationship_definitions, _relationships, _commits = (
        client_context
    )
    source = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="source",
        description="source template",
        abstract=False,
    )
    target = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="target",
        description="target template",
        abstract=False,
    )
    object_templates.add(source)
    object_templates.add(target)
    object_templates.add_version(
        ObjectTemplateVersion(
            template_id=source.id,
            version=1,
            status=ObjectTemplateVersionStatus.PUBLISHED,
        )
    )
    object_templates.add_version(
        ObjectTemplateVersion(
            template_id=target.id,
            version=1,
            status=ObjectTemplateVersionStatus.PUBLISHED,
        )
    )

    invalid_uuid = client.get("/api/v1/relationship-definitions/not-a-uuid")
    extra_field = client.post(
        "/api/v1/relationship-definitions",
        json={
            "source_template_id": str(source.id),
            "target_template_id": str(target.id),
            "forward_name": "uses",
            "reverse_name": "is_used_by",
            "extra": "nope",
        },
    )
    non_string_forward = client.post(
        "/api/v1/relationship-definitions",
        json={
            "source_template_id": str(source.id),
            "target_template_id": str(target.id),
            "forward_name": 1,
            "reverse_name": "is_used_by",
        },
    )
    non_string_reverse = client.post(
        "/api/v1/relationship-definitions",
        json={
            "source_template_id": str(source.id),
            "target_template_id": str(target.id),
            "forward_name": "uses",
            "reverse_name": 1,
        },
    )
    invalid_identifier = client.post(
        "/api/v1/relationship-definitions",
        json={
            "source_template_id": str(source.id),
            "target_template_id": str(target.id),
            "forward_name": "USES",
            "reverse_name": "is_used_by",
        },
    )

    assert invalid_uuid.status_code == 422
    assert invalid_uuid.json()["error"]["code"] == "request_validation_failed"
    assert extra_field.status_code == 422
    assert extra_field.json()["error"]["code"] == "request_validation_failed"
    assert non_string_forward.status_code == 422
    assert non_string_forward.json()["error"]["code"] == "request_validation_failed"
    assert non_string_reverse.status_code == 422
    assert non_string_reverse.json()["error"]["code"] == "request_validation_failed"
    assert invalid_identifier.status_code == 422
    assert invalid_identifier.json()["error"]["code"] == "invalid_relationship_identifier"


def test_not_found_not_published_and_semantic_conflict_mappings(
    client_context: tuple[
        TestClient,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        InMemoryRelationshipDefinitionRepository,
        InMemoryRelationshipRepository,
        list[int],
    ],
) -> None:
    client, object_templates, _objects, _relationship_definitions, _relationships, commits = (
        client_context
    )
    missing_source = client.post(
        "/api/v1/relationship-definitions",
        json={
            "source_template_id": str(uuid4()),
            "target_template_id": str(uuid4()),
            "forward_name": "uses",
            "reverse_name": "is_used_by",
        },
    )
    assert missing_source.status_code == 404
    assert missing_source.json()["error"]["code"] == "relationship_definition_template_not_found"

    source = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="source",
        description="source template",
        abstract=False,
    )
    target = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="target",
        description="target template",
        abstract=False,
    )
    object_templates.add(source)
    object_templates.add(target)
    object_templates.add_version(
        ObjectTemplateVersion(
            template_id=source.id,
            version=1,
            status=ObjectTemplateVersionStatus.DRAFT,
        )
    )
    object_templates.add_version(
        ObjectTemplateVersion(
            template_id=target.id,
            version=1,
            status=ObjectTemplateVersionStatus.PUBLISHED,
        )
    )

    unpublished = client.post(
        "/api/v1/relationship-definitions",
        json={
            "source_template_id": str(source.id),
            "target_template_id": str(target.id),
            "forward_name": "uses",
            "reverse_name": "is_used_by",
        },
    )
    assert unpublished.status_code == 409
    assert unpublished.json()["error"]["code"] == (
        "relationship_definition_template_not_published"
    )
    assert commits[0] == 0

    object_templates.replace_version(
        ObjectTemplateVersion(
            template_id=source.id,
            version=1,
            status=ObjectTemplateVersionStatus.PUBLISHED,
        )
    )
    created = client.post(
        "/api/v1/relationship-definitions",
        json={
            "source_template_id": str(source.id),
            "target_template_id": str(target.id),
            "forward_name": "uses",
            "reverse_name": "is_used_by",
        },
    )
    assert created.status_code == 201

    exact_duplicate = client.post(
        "/api/v1/relationship-definitions",
        json={
            "source_template_id": str(source.id),
            "target_template_id": str(target.id),
            "forward_name": "uses",
            "reverse_name": "is_used_by",
        },
    )
    inverse_duplicate = client.post(
        "/api/v1/relationship-definitions",
        json={
            "source_template_id": str(target.id),
            "target_template_id": str(source.id),
            "forward_name": "is_used_by",
            "reverse_name": "uses",
        },
    )

    assert exact_duplicate.status_code == 409
    assert exact_duplicate.json()["error"]["code"] == (
        "relationship_definition_semantic_conflict"
    )
    assert inverse_duplicate.status_code == 409
    assert inverse_duplicate.json()["error"]["code"] == (
        "relationship_definition_semantic_conflict"
    )


def test_inheritance_overlap_conflict_and_delete_missing(
    client_context: tuple[
        TestClient,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        InMemoryRelationshipDefinitionRepository,
        InMemoryRelationshipRepository,
        list[int],
    ],
) -> None:
    client, object_templates, _objects, _relationship_definitions, _relationships, commits = (
        client_context
    )
    source = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="source",
        description="source template",
        abstract=False,
    )
    source_child = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="source_child",
        description="source child template",
        abstract=False,
    )
    target = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="target",
        description="target template",
        abstract=False,
    )
    object_templates.add(source)
    object_templates.add(source_child)
    object_templates.add(target)
    object_templates.add_version(
        ObjectTemplateVersion(
            template_id=source.id,
            version=1,
            status=ObjectTemplateVersionStatus.PUBLISHED,
        )
    )
    object_templates.add_version(
        ObjectTemplateVersion(
            template_id=source_child.id,
            version=1,
            status=ObjectTemplateVersionStatus.PUBLISHED,
            parent=ObjectTemplateVersionRef(template_id=source.id, version=1),
        )
    )
    object_templates.add_version(
        ObjectTemplateVersion(
            template_id=target.id,
            version=1,
            status=ObjectTemplateVersionStatus.PUBLISHED,
        )
    )

    first = client.post(
        "/api/v1/relationship-definitions",
        json={
            "source_template_id": str(source.id),
            "target_template_id": str(target.id),
            "forward_name": "uses",
            "reverse_name": "is_used_by",
        },
    )
    conflict = client.post(
        "/api/v1/relationship-definitions",
        json={
            "source_template_id": str(source_child.id),
            "target_template_id": str(target.id),
            "forward_name": "uses",
            "reverse_name": "is_used_by",
        },
    )
    missing_delete = client.delete(f"/api/v1/relationship-definitions/{uuid4()}")

    assert first.status_code == 201
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "relationship_definition_semantic_conflict"
    assert missing_delete.status_code == 404
    assert missing_delete.json()["error"]["code"] == "relationship_definition_not_found"
    assert commits[0] == 1


def test_delete_in_use_relationship_definition_returns_conflict(
    client_context: tuple[
        TestClient,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        InMemoryRelationshipDefinitionRepository,
        InMemoryRelationshipRepository,
        list[int],
    ],
) -> None:
    client, object_templates, _objects, relationship_definitions, relationships, commits = (
        client_context
    )
    source = _store_template(
        object_templates,
        name="source",
        versions=(),
    )
    target = _store_template(
        object_templates,
        name="target",
        versions=(),
    )
    definition = _definition(source_template_id=source.id, target_template_id=target.id)
    relationship_definitions.add(definition)
    relationships.add(
        _relationship(
            relationship_definition_id=definition.id,
            source_object_id=uuid4(),
            target_object_id=uuid4(),
        )
    )

    deleted = client.delete(f"/api/v1/relationship-definitions/{definition.id}")

    assert deleted.status_code == 409
    assert deleted.json()["error"]["code"] == "relationship_definition_in_use"
    assert relationship_definitions.get(definition.id) == definition
    assert commits[0] == 0


def test_relationship_definition_persistence_error_mapping() -> None:
    with TestClient(
        create_app(
            BrokenRelationshipUnitOfWork,
            model_write_uow_factory=BrokenRelationshipUnitOfWork,
        )
    ) as client:
        response = client.get("/api/v1/relationship-definitions")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "persistence_error"


def test_relationship_definition_delete_relationship_persistence_error_maps_to_500() -> None:
    with TestClient(
        create_app(
            BrokenLifecycleUnitOfWork,
            model_write_uow_factory=BrokenLifecycleUnitOfWork,
        )
    ) as client:
        response = client.delete(
            f"/api/v1/relationship-definitions/{BrokenLifecycleUnitOfWork.definition_id}"
        )

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "persistence_error"


def test_openapi_contains_relationship_definition_routes() -> None:
    with TestClient(
        create_app(
            BrokenRelationshipUnitOfWork,
            model_write_uow_factory=BrokenRelationshipUnitOfWork,
        )
    ) as client:
        openapi = client.get("/openapi.json")

    assert openapi.status_code == 200
    paths = openapi.json()["paths"]
    assert "/api/v1/relationship-definitions" in paths
    assert "/api/v1/relationship-definitions/{definition_id}" in paths
    assert "post" in paths["/api/v1/relationship-definitions"]
    assert "get" in paths["/api/v1/relationship-definitions"]
    assert "get" in paths["/api/v1/relationship-definitions/{definition_id}"]
    assert "delete" in paths["/api/v1/relationship-definitions/{definition_id}"]
    assert "put" not in paths["/api/v1/relationship-definitions/{definition_id}"]
    assert "patch" not in paths["/api/v1/relationship-definitions/{definition_id}"]
    assert "/api/v1/relationships" in paths
    assert "/api/v1/relationships/{relationship_id}" in paths
    assert "get" in paths["/api/v1/relationships"]
    assert "post" in paths["/api/v1/relationships"]
    assert "get" in paths["/api/v1/relationships/{relationship_id}"]
    assert "delete" in paths["/api/v1/relationships/{relationship_id}"]
    assert "put" not in paths["/api/v1/relationships/{relationship_id}"]
    assert "patch" not in paths["/api/v1/relationships/{relationship_id}"]
    assert "/api/v1/objects/{object_id}/relationship-definitions/effective" in paths
    assert "get" in paths["/api/v1/objects/{object_id}/relationship-definitions/effective"]
    assert "post" not in paths["/api/v1/objects/{object_id}/relationship-definitions/effective"]
    assert "put" not in paths["/api/v1/objects/{object_id}/relationship-definitions/effective"]
    assert "patch" not in paths["/api/v1/objects/{object_id}/relationship-definitions/effective"]
    assert (
        "delete"
        not in paths["/api/v1/objects/{object_id}/relationship-definitions/effective"]
    )
    assert "/api/v1/objects/{object_id}/relationships/outgoing" in paths
    assert "/api/v1/objects/{object_id}/relationships/incoming" in paths
    assert "/api/v1/objects/{object_id}/relationships/neighbors" in paths
    for path in (
        "/api/v1/objects/{object_id}/relationships/outgoing",
        "/api/v1/objects/{object_id}/relationships/incoming",
        "/api/v1/objects/{object_id}/relationships/neighbors",
    ):
        assert "get" in paths[path]
        assert "post" not in paths[path]
        assert "put" not in paths[path]
        assert "patch" not in paths[path]
        assert "delete" not in paths[path]


def test_runtime_relationship_list_create_show_and_delete(
    client_context: tuple[
        TestClient,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        InMemoryRelationshipDefinitionRepository,
        InMemoryRelationshipRepository,
        list[int],
    ],
) -> None:
    client, object_templates, objects, relationship_definitions, _relationships, commits = (
        client_context
    )
    source = _store_published_template(object_templates, name="network_device")
    target = _store_published_template(object_templates, name="credential")
    definition = _definition(source_template_id=source.id, target_template_id=target.id)
    relationship_definitions.add(definition)
    source_object = _store_object(objects, template_id=source.id)
    target_object = _store_object(objects, template_id=target.id)

    empty = client.get("/api/v1/relationships")
    created = client.post(
        "/api/v1/relationships",
        json={
            "relationship_definition_id": str(definition.id),
            "source_object_id": str(source_object.id),
            "target_object_id": str(target_object.id),
        },
    )

    assert empty.status_code == 200
    assert empty.json() == []
    assert created.status_code == 201
    created_payload = created.json()
    relationship_id = created_payload["id"]
    assert created_payload == {
        "id": relationship_id,
        "relationship_definition_id": str(definition.id),
        "source_object_id": str(source_object.id),
        "target_object_id": str(target_object.id),
    }

    listed = client.get("/api/v1/relationships")
    shown = client.get(f"/api/v1/relationships/{relationship_id}")
    deleted = client.delete(f"/api/v1/relationships/{relationship_id}")
    missing = client.get(f"/api/v1/relationships/{relationship_id}")

    assert listed.status_code == 200
    assert listed.json() == [created_payload]
    assert shown.status_code == 200
    assert shown.json() == created_payload
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "relationship_not_found"
    assert commits[0] == 2


def test_runtime_relationship_request_validation_and_error_mappings(
    client_context: tuple[
        TestClient,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        InMemoryRelationshipDefinitionRepository,
        InMemoryRelationshipRepository,
        list[int],
    ],
) -> None:
    client, object_templates, objects, relationship_definitions, _relationships, commits = (
        client_context
    )
    source = _store_published_template(object_templates, name="network_device")
    target = _store_published_template(object_templates, name="credential")
    definition = _definition(source_template_id=source.id, target_template_id=target.id)
    relationship_definitions.add(definition)
    source_object = _store_object(objects, template_id=source.id)
    target_object = _store_object(objects, template_id=target.id)

    invalid_path = client.get("/api/v1/relationships/not-a-uuid")
    extra_field = client.post(
        "/api/v1/relationships",
        json={
            "relationship_definition_id": str(definition.id),
            "source_object_id": str(source_object.id),
            "target_object_id": str(target_object.id),
            "extra": "nope",
        },
    )
    malformed_definition = client.post(
        "/api/v1/relationships",
        json={
            "relationship_definition_id": "not-a-uuid",
            "source_object_id": str(source_object.id),
            "target_object_id": str(target_object.id),
        },
    )
    malformed_source = client.post(
        "/api/v1/relationships",
        json={
            "relationship_definition_id": str(definition.id),
            "source_object_id": "not-a-uuid",
            "target_object_id": str(target_object.id),
        },
    )
    malformed_target = client.post(
        "/api/v1/relationships",
        json={
            "relationship_definition_id": str(definition.id),
            "source_object_id": str(source_object.id),
            "target_object_id": "not-a-uuid",
        },
    )
    missing_target = client.post(
        "/api/v1/relationships",
        json={
            "relationship_definition_id": str(definition.id),
            "source_object_id": str(source_object.id),
        },
    )
    missing_definition = client.post(
        "/api/v1/relationships",
        json={
            "relationship_definition_id": str(uuid4()),
            "source_object_id": str(source_object.id),
            "target_object_id": str(target_object.id),
        },
    )
    missing_object = client.post(
        "/api/v1/relationships",
        json={
            "relationship_definition_id": str(definition.id),
            "source_object_id": str(uuid4()),
            "target_object_id": str(target_object.id),
        },
    )
    created = client.post(
        "/api/v1/relationships",
        json={
            "relationship_definition_id": str(definition.id),
            "source_object_id": str(source_object.id),
            "target_object_id": str(target_object.id),
        },
    )
    duplicate = client.post(
        "/api/v1/relationships",
        json={
            "relationship_definition_id": str(definition.id),
            "source_object_id": str(source_object.id),
            "target_object_id": str(target_object.id),
        },
    )
    incompatible = client.post(
        "/api/v1/relationships",
        json={
            "relationship_definition_id": str(definition.id),
            "source_object_id": str(target_object.id),
            "target_object_id": str(source_object.id),
        },
    )

    assert invalid_path.status_code == 422
    assert invalid_path.json()["error"]["code"] == "request_validation_failed"
    assert extra_field.status_code == 422
    assert extra_field.json()["error"]["code"] == "request_validation_failed"
    assert malformed_definition.status_code == 422
    assert malformed_definition.json()["error"]["code"] == "request_validation_failed"
    assert malformed_source.status_code == 422
    assert malformed_source.json()["error"]["code"] == "request_validation_failed"
    assert malformed_target.status_code == 422
    assert malformed_target.json()["error"]["code"] == "request_validation_failed"
    assert missing_target.status_code == 422
    assert missing_target.json()["error"]["code"] == "request_validation_failed"
    assert missing_definition.status_code == 404
    assert missing_definition.json()["error"]["code"] == "relationship_definition_not_found"
    assert missing_object.status_code == 404
    assert missing_object.json()["error"]["code"] == "relationship_object_not_found"
    assert created.status_code == 201
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "relationship_already_exists"
    assert incompatible.status_code == 409
    assert incompatible.json()["error"]["code"] == "relationship_endpoint_incompatible"
    assert commits[0] == 1


def test_runtime_relationship_persistence_error_maps_to_500() -> None:
    with TestClient(
        create_app(
            BrokenRuntimeUnitOfWork,
            model_write_uow_factory=BrokenRuntimeUnitOfWork,
        )
    ) as client:
        response = client.get("/api/v1/relationships")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "persistence_error"


def test_effective_relationship_definitions_rest_semantics(
    client_context: tuple[
        TestClient,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        InMemoryRelationshipDefinitionRepository,
        InMemoryRelationshipRepository,
        list[int],
    ],
) -> None:
    client, object_templates, objects, relationship_definitions, _relationships, commits = (
        client_context
    )
    network_device = _store_published_template(object_templates, name="network_device")
    router = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="router",
        description="router template",
        abstract=False,
    )
    object_templates.add(router)
    object_templates.add_version(
        ObjectTemplateVersion(
            template_id=router.id,
            version=1,
            status=ObjectTemplateVersionStatus.PUBLISHED,
        )
    )
    object_templates.add_version(
        ObjectTemplateVersion(
            template_id=router.id,
            version=2,
            status=ObjectTemplateVersionStatus.PUBLISHED,
            parent=ObjectTemplateVersionRef(template_id=network_device.id, version=1),
        )
    )
    credential = _store_published_template(object_templates, name="credential")
    device = _store_published_template(object_templates, name="device")
    object_templates.add_version(
        ObjectTemplateVersion(
            template_id=device.id,
            version=2,
            status=ObjectTemplateVersionStatus.DEPRECATED,
        )
    )
    outgoing_definition = _definition(
        source_template_id=network_device.id,
        target_template_id=credential.id,
        definition_id=UUID(int=3),
    )
    incoming_definition = _definition(
        source_template_id=credential.id,
        target_template_id=device.id,
        forward_name="used_by",
        reverse_name="uses_for",
        definition_id=UUID(int=2),
    )
    both_definition = _definition(
        source_template_id=device.id,
        target_template_id=device.id,
        forward_name="connects_to",
        reverse_name="connected_from",
        definition_id=UUID(int=1),
    )
    relationship_definitions.add(outgoing_definition)
    relationship_definitions.add(incoming_definition)
    relationship_definitions.add(both_definition)
    router_v1_object = _store_object(objects, template_id=router.id, template_version=1)
    router_v2_object = _store_object(objects, template_id=router.id, template_version=2)
    deprecated_device_object = _store_object(
        objects,
        template_id=device.id,
        template_version=2,
    )

    router_v1_response = client.get(
        f"/api/v1/objects/{router_v1_object.id}/relationship-definitions/effective"
    )
    router_v2_response = client.get(
        f"/api/v1/objects/{router_v2_object.id}/relationship-definitions/effective"
    )
    deprecated_response = client.get(
        f"/api/v1/objects/{deprecated_device_object.id}/relationship-definitions/effective"
    )
    missing = client.get(f"/api/v1/objects/{uuid4()}/relationship-definitions/effective")
    malformed = client.get("/api/v1/objects/not-a-uuid/relationship-definitions/effective")

    assert router_v1_response.status_code == 200
    assert router_v1_response.json() == []
    assert router_v2_response.status_code == 200
    assert router_v2_response.json() == [
        {
            "relationship_definition_id": str(outgoing_definition.id),
            "direction": "outgoing",
            "name": "uses",
            "related_template_id": str(credential.id),
        }
    ]
    assert deprecated_response.status_code == 200
    assert deprecated_response.json() == [
        {
            "relationship_definition_id": str(both_definition.id),
            "direction": "outgoing",
            "name": "connects_to",
            "related_template_id": str(device.id),
        },
        {
            "relationship_definition_id": str(both_definition.id),
            "direction": "incoming",
            "name": "connected_from",
            "related_template_id": str(device.id),
        },
        {
            "relationship_definition_id": str(incoming_definition.id),
            "direction": "incoming",
            "name": "uses_for",
            "related_template_id": str(credential.id),
        },
    ]
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "object_not_found"
    assert malformed.status_code == 422
    assert malformed.json()["error"]["code"] == "request_validation_failed"
    assert commits[0] == 0


def test_effective_relationship_definitions_rest_propagates_ancestry_error(
    client_context: tuple[
        TestClient,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        InMemoryRelationshipDefinitionRepository,
        InMemoryRelationshipRepository,
        list[int],
    ],
) -> None:
    client, object_templates, objects, relationship_definitions, _relationships, commits = (
        client_context
    )
    network_device = _store_published_template(object_templates, name="network_device")
    credential = _store_published_template(object_templates, name="credential")
    router = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="router",
        description="router template",
        abstract=False,
    )
    object_templates.add(router)
    object_templates.add_version(
        ObjectTemplateVersion(
            template_id=router.id,
            version=1,
            status=ObjectTemplateVersionStatus.PUBLISHED,
            parent=ObjectTemplateVersionRef(template_id=network_device.id, version=9),
        )
    )
    relationship_definitions.add(
        _definition(
            source_template_id=network_device.id,
            target_template_id=credential.id,
        )
    )
    router_object = _store_object(objects, template_id=router.id, template_version=1)

    response = client.get(
        f"/api/v1/objects/{router_object.id}/relationship-definitions/effective"
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "object_template_parent_not_found"
    assert commits[0] == 0


def test_runtime_relationship_navigation_rest_semantics_and_self_link(
    client_context: tuple[
        TestClient,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        InMemoryRelationshipDefinitionRepository,
        InMemoryRelationshipRepository,
        list[int],
    ],
) -> None:
    client, object_templates, objects, relationship_definitions, relationships, commits = (
        client_context
    )
    network_device = _store_published_template(object_templates, name="network_device")
    credential = _store_published_template(object_templates, name="credential")
    device = _store_published_template(object_templates, name="device")
    uses_definition = _definition(
        source_template_id=network_device.id,
        target_template_id=credential.id,
    )
    managed_definition = _definition(
        source_template_id=network_device.id,
        target_template_id=credential.id,
        forward_name="manages",
        reverse_name="managed_by",
    )
    self_definition = _definition(
        source_template_id=device.id,
        target_template_id=device.id,
        forward_name="connects_to",
        reverse_name="connected_from",
    )
    relationship_definitions.add(uses_definition)
    relationship_definitions.add(managed_definition)
    relationship_definitions.add(self_definition)
    source_object = _store_object(objects, template_id=network_device.id, object_id=UUID(int=1))
    target_object = _store_object(objects, template_id=credential.id, object_id=UUID(int=2))
    other_source = _store_object(objects, template_id=network_device.id, object_id=UUID(int=3))
    device_object = _store_object(objects, template_id=device.id, object_id=UUID(int=4))
    uses_relationship = _relationship(
        relationship_definition_id=uses_definition.id,
        source_object_id=source_object.id,
        target_object_id=target_object.id,
        relationship_id=UUID(int=10),
    )
    manages_relationship = _relationship(
        relationship_definition_id=managed_definition.id,
        source_object_id=source_object.id,
        target_object_id=target_object.id,
        relationship_id=UUID(int=11),
    )
    incoming_relationship = _relationship(
        relationship_definition_id=uses_definition.id,
        source_object_id=other_source.id,
        target_object_id=source_object.id,
        relationship_id=UUID(int=12),
    )
    self_relationship = _relationship(
        relationship_definition_id=self_definition.id,
        source_object_id=device_object.id,
        target_object_id=device_object.id,
        relationship_id=UUID(int=13),
    )
    relationships.add(uses_relationship)
    relationships.add(manages_relationship)
    relationships.add(incoming_relationship)
    relationships.add(self_relationship)

    outgoing = client.get(f"/api/v1/objects/{source_object.id}/relationships/outgoing")
    incoming = client.get(f"/api/v1/objects/{target_object.id}/relationships/incoming")
    neighbors = client.get(f"/api/v1/objects/{source_object.id}/relationships/neighbors")
    self_neighbors = client.get(f"/api/v1/objects/{device_object.id}/relationships/neighbors")

    assert outgoing.status_code == 200
    assert outgoing.json() == [
        {
            "relationship_id": str(uses_relationship.id),
            "relationship_definition_id": str(uses_definition.id),
            "source_object_id": str(source_object.id),
            "target_object_id": str(target_object.id),
            "direction": "outgoing",
            "name": "uses",
            "related_object_id": str(target_object.id),
        },
        {
            "relationship_id": str(manages_relationship.id),
            "relationship_definition_id": str(managed_definition.id),
            "source_object_id": str(source_object.id),
            "target_object_id": str(target_object.id),
            "direction": "outgoing",
            "name": "manages",
            "related_object_id": str(target_object.id),
        },
    ]
    assert incoming.status_code == 200
    assert incoming.json() == [
        {
            "relationship_id": str(uses_relationship.id),
            "relationship_definition_id": str(uses_definition.id),
            "source_object_id": str(source_object.id),
            "target_object_id": str(target_object.id),
            "direction": "incoming",
            "name": "is_used_by",
            "related_object_id": str(source_object.id),
        },
        {
            "relationship_id": str(manages_relationship.id),
            "relationship_definition_id": str(managed_definition.id),
            "source_object_id": str(source_object.id),
            "target_object_id": str(target_object.id),
            "direction": "incoming",
            "name": "managed_by",
            "related_object_id": str(source_object.id),
        },
    ]
    assert outgoing.json()[0]["relationship_id"] == incoming.json()[0]["relationship_id"]
    assert neighbors.status_code == 200
    assert neighbors.json() == [
        {
            "relationship_id": str(uses_relationship.id),
            "relationship_definition_id": str(uses_definition.id),
            "source_object_id": str(source_object.id),
            "target_object_id": str(target_object.id),
            "direction": "outgoing",
            "name": "uses",
            "related_object_id": str(target_object.id),
        },
        {
            "relationship_id": str(manages_relationship.id),
            "relationship_definition_id": str(managed_definition.id),
            "source_object_id": str(source_object.id),
            "target_object_id": str(target_object.id),
            "direction": "outgoing",
            "name": "manages",
            "related_object_id": str(target_object.id),
        },
        {
            "relationship_id": str(incoming_relationship.id),
            "relationship_definition_id": str(uses_definition.id),
            "source_object_id": str(other_source.id),
            "target_object_id": str(source_object.id),
            "direction": "incoming",
            "name": "is_used_by",
            "related_object_id": str(other_source.id),
        },
    ]
    assert self_neighbors.status_code == 200
    assert self_neighbors.json() == [
        {
            "relationship_id": str(self_relationship.id),
            "relationship_definition_id": str(self_definition.id),
            "source_object_id": str(device_object.id),
            "target_object_id": str(device_object.id),
            "direction": "outgoing",
            "name": "connects_to",
            "related_object_id": str(device_object.id),
        },
        {
            "relationship_id": str(self_relationship.id),
            "relationship_definition_id": str(self_definition.id),
            "source_object_id": str(device_object.id),
            "target_object_id": str(device_object.id),
            "direction": "incoming",
            "name": "connected_from",
            "related_object_id": str(device_object.id),
        },
    ]
    assert commits[0] == 0


def test_runtime_relationship_navigation_rest_missing_object_and_corruption(
    client_context: tuple[
        TestClient,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        InMemoryRelationshipDefinitionRepository,
        InMemoryRelationshipRepository,
        list[int],
    ],
) -> None:
    client, object_templates, objects, _relationship_definitions, relationships, commits = (
        client_context
    )
    device = _store_published_template(object_templates, name="device")
    object_value = _store_object(objects, template_id=device.id)
    corrupted = _relationship(
        relationship_definition_id=uuid4(),
        source_object_id=object_value.id,
        target_object_id=object_value.id,
    )
    relationships.add(corrupted)

    missing_outgoing = client.get(f"/api/v1/objects/{uuid4()}/relationships/outgoing")
    missing_incoming = client.get(f"/api/v1/objects/{uuid4()}/relationships/incoming")
    missing_neighbors = client.get(f"/api/v1/objects/{uuid4()}/relationships/neighbors")
    corrupted_neighbors = client.get(f"/api/v1/objects/{object_value.id}/relationships/neighbors")

    assert missing_outgoing.status_code == 404
    assert missing_outgoing.json()["error"]["code"] == "object_not_found"
    assert missing_incoming.status_code == 404
    assert missing_incoming.json()["error"]["code"] == "object_not_found"
    assert missing_neighbors.status_code == 404
    assert missing_neighbors.json()["error"]["code"] == "object_not_found"
    assert corrupted_neighbors.status_code == 404
    assert corrupted_neighbors.json()["error"]["code"] == "relationship_definition_not_found"
    assert commits[0] == 0


def test_runtime_relationship_navigation_rest_reports_persisted_incompatible_edge(
    client_context: tuple[
        TestClient,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        InMemoryRelationshipDefinitionRepository,
        InMemoryRelationshipRepository,
        list[int],
    ],
) -> None:
    client, object_templates, objects, relationship_definitions, relationships, commits = (
        client_context
    )
    network_device = _store_published_template(object_templates, name="network_device")
    router = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="router",
        description="router template",
        abstract=False,
    )
    object_templates.add(router)
    object_templates.add_version(
        ObjectTemplateVersion(
            template_id=router.id,
            version=1,
            status=ObjectTemplateVersionStatus.PUBLISHED,
        )
    )
    object_templates.add_version(
        ObjectTemplateVersion(
            template_id=router.id,
            version=2,
            status=ObjectTemplateVersionStatus.PUBLISHED,
            parent=ObjectTemplateVersionRef(template_id=network_device.id, version=1),
        )
    )
    credential = _store_published_template(object_templates, name="credential")
    definition = _definition(
        source_template_id=network_device.id,
        target_template_id=credential.id,
    )
    relationship_definitions.add(definition)
    router_object = _store_object(objects, template_id=router.id, template_version=1)
    credential_object = _store_object(objects, template_id=credential.id, template_version=1)
    incompatible_but_persisted = _relationship(
        relationship_definition_id=definition.id,
        source_object_id=router_object.id,
        target_object_id=credential_object.id,
    )
    relationships.add(incompatible_but_persisted)

    response = client.get(f"/api/v1/objects/{router_object.id}/relationships/outgoing")

    assert response.status_code == 200
    assert response.json() == [
        {
            "relationship_id": str(incompatible_but_persisted.id),
            "relationship_definition_id": str(definition.id),
            "source_object_id": str(router_object.id),
            "target_object_id": str(credential_object.id),
            "direction": "outgoing",
            "name": "uses",
            "related_object_id": str(credential_object.id),
        }
    ]
    assert commits[0] == 0
