from __future__ import annotations

from collections.abc import Generator
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from netauto.api.app import create_app
from netauto.application.unit_of_work import ObjectUnitOfWork
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
        relationships: InMemoryRelationshipRepository,
        relationship_definitions: InMemoryRelationshipDefinitionRepository,
        commit_counter: list[int],
    ) -> None:
        self._datatypes = datatypes
        self._object_templates = object_templates
        self._objects = objects
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


class BrokenRelationshipUnitOfWork(FakeUnitOfWork):
    def __init__(self) -> None:
        super().__init__(
            InMemoryDataTypeRepository(),
            InMemoryObjectTemplateRepository(),
            InMemoryObjectRepository(),
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
            BrokenRelationshipRepository(),
            relationship_definitions,
            [0],
        )


@pytest.fixture
def client_context() -> (
    Generator[
        tuple[
            TestClient,
            InMemoryObjectTemplateRepository,
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
    relationships = InMemoryRelationshipRepository()
    relationship_definitions = InMemoryRelationshipDefinitionRepository()
    commits = [0]

    def factory() -> FakeUnitOfWork:
        return FakeUnitOfWork(
            datatypes,
            object_templates,
            objects,
            relationships,
            relationship_definitions,
            commits,
        )

    with TestClient(create_app(factory)) as client:
        yield client, object_templates, relationship_definitions, relationships, commits


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
) -> RelationshipDefinition:
    return RelationshipDefinition(
        id=uuid4(),
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
) -> Relationship:
    return Relationship(
        id=uuid4(),
        relationship_definition_id=relationship_definition_id,
        source_object_id=source_object_id,
        target_object_id=target_object_id,
    )


def test_create_list_show_and_delete_relationship_definition(
    client_context: tuple[
        TestClient,
        InMemoryObjectTemplateRepository,
        InMemoryRelationshipDefinitionRepository,
        InMemoryRelationshipRepository,
        list[int],
    ],
) -> None:
    client, object_templates, relationship_definitions, _relationships, commits = (
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
        InMemoryRelationshipDefinitionRepository,
        InMemoryRelationshipRepository,
        list[int],
    ],
) -> None:
    client, object_templates, _relationship_definitions, _relationships, _commits = (
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
        InMemoryRelationshipDefinitionRepository,
        InMemoryRelationshipRepository,
        list[int],
    ],
) -> None:
    client, object_templates, _relationship_definitions, _relationships, commits = (
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
        InMemoryRelationshipDefinitionRepository,
        InMemoryRelationshipRepository,
        list[int],
    ],
) -> None:
    client, object_templates, _relationship_definitions, _relationships, commits = (
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
        InMemoryRelationshipDefinitionRepository,
        InMemoryRelationshipRepository,
        list[int],
    ],
) -> None:
    client, object_templates, relationship_definitions, relationships, commits = client_context
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
    with TestClient(create_app(BrokenRelationshipUnitOfWork)) as client:
        response = client.get("/api/v1/relationship-definitions")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "persistence_error"


def test_relationship_definition_delete_relationship_persistence_error_maps_to_500() -> None:
    with TestClient(create_app(BrokenLifecycleUnitOfWork)) as client:
        response = client.delete(
            f"/api/v1/relationship-definitions/{BrokenLifecycleUnitOfWork.definition_id}"
        )

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "persistence_error"


def test_openapi_contains_relationship_definition_routes() -> None:
    with TestClient(create_app(BrokenRelationshipUnitOfWork)) as client:
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
