from __future__ import annotations

from collections.abc import Generator
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from netauto.api.app import create_app
from netauto.application.unit_of_work import ObjectUnitOfWork
from netauto.core.object import ComponentMembership, Object, ObjectPersistenceError
from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateComponent,
    ObjectTemplateVersion,
    ObjectTemplateVersionRef,
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


class BrokenObjectRepository(InMemoryObjectRepository):
    def list_components(
        self,
        parent_object_id: UUID,
        slot_name: str | None = None,
    ) -> tuple[ComponentMembership, ...]:
        raise ObjectPersistenceError("boom")


class BrokenObjectUnitOfWork(FakeUnitOfWork):
    def __init__(self) -> None:
        objects = BrokenObjectRepository()
        objects.add(
            Object(
                id=UUID("00000000-0000-0000-0000-000000000001"),
                template_id=uuid4(),
                template_version=1,
                properties={},
            )
        )
        super().__init__(
            InMemoryDataTypeRepository(),
            InMemoryObjectTemplateRepository(),
            objects,
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

    with TestClient(create_app(factory)) as client:
        yield client, datatypes, object_templates, objects, commits


def _store_template(
    repo: InMemoryObjectTemplateRepository,
    *,
    name: str,
    abstract: bool = False,
    version: int = 1,
    status: ObjectTemplateVersionStatus = ObjectTemplateVersionStatus.PUBLISHED,
    parent: ObjectTemplateVersionRef | None = None,
    components: tuple[ObjectTemplateComponent, ...] = (),
) -> tuple[ObjectTemplate, ObjectTemplateVersion]:
    template = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name=name,
        description=f"{name} template",
        abstract=abstract,
    )
    template_version = ObjectTemplateVersion(
        template_id=template.id,
        version=version,
        status=status,
        parent=parent,
        components=components,
    )
    repo.add(template)
    repo.add_version(template_version)
    return template, template_version


def _component(
    name: str,
    *,
    template_id: UUID,
) -> ObjectTemplateComponent:
    return ObjectTemplateComponent(
        name=name,
        template_id=template_id,
    )


def _object(
    repo: InMemoryObjectRepository,
    *,
    template_id: UUID,
    template_version: int,
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


def _membership(parent_id: UUID, slot_name: str, child_id: UUID) -> dict[str, str]:
    return {
        "parent_object_id": str(parent_id),
        "slot_name": slot_name,
        "component_object_id": str(child_id),
    }


def test_attach_list_and_detach_component_successfully(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        list[int],
    ],
) -> None:
    client, _datatypes, templates, objects, commits = client_context
    interface, _interface_v1 = _store_template(templates, name="interface")
    device, _device_v1 = _store_template(
        templates,
        name="device",
        components=(_component("interfaces", template_id=interface.id),),
    )
    parent = _object(objects, template_id=device.id, template_version=1)
    child = _object(objects, template_id=interface.id, template_version=1)

    attached = client.post(
        f"/api/v1/objects/{parent.id}/components",
        json={"slot_name": "interfaces", "component_object_id": str(child.id)},
    )
    listed = client.get(f"/api/v1/objects/{parent.id}/components")
    detached = client.delete(f"/api/v1/objects/components/{child.id}")
    child_after = client.get(f"/api/v1/objects/{child.id}")
    listed_after = client.get(f"/api/v1/objects/{parent.id}/components")

    assert attached.status_code == 201
    assert attached.json() == _membership(parent.id, "interfaces", child.id)
    assert listed.status_code == 200
    assert listed.json() == [_membership(parent.id, "interfaces", child.id)]
    assert detached.status_code == 200
    assert detached.json() == _membership(parent.id, "interfaces", child.id)
    assert child_after.status_code == 200
    assert listed_after.status_code == 200
    assert listed_after.json() == []
    assert commits[0] == 2


def test_detach_preserves_detached_component_subtree(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        list[int],
    ],
) -> None:
    client, _datatypes, templates, objects, commits = client_context
    node, _node_v1 = _store_template(
        templates,
        name="node",
        components=(_component("children", template_id=uuid4()),),
    )
    templates.replace_version(
        ObjectTemplateVersion(
            template_id=node.id,
            version=1,
            status=ObjectTemplateVersionStatus.PUBLISHED,
            components=(_component("children", template_id=node.id),),
        )
    )
    parent = _object(objects, template_id=node.id, template_version=1)
    child = _object(objects, template_id=node.id, template_version=1)
    grandchild = _object(objects, template_id=node.id, template_version=1)

    attach_child = client.post(
        f"/api/v1/objects/{parent.id}/components",
        json={"slot_name": "children", "component_object_id": str(child.id)},
    )
    attach_grandchild = client.post(
        f"/api/v1/objects/{child.id}/components",
        json={"slot_name": "children", "component_object_id": str(grandchild.id)},
    )
    commits[0] = 0
    detached = client.delete(f"/api/v1/objects/components/{child.id}")
    child_after = client.get(f"/api/v1/objects/{child.id}")
    grandchild_after = client.get(f"/api/v1/objects/{grandchild.id}")
    child_components = client.get(f"/api/v1/objects/{child.id}/components")

    assert attach_child.status_code == 201
    assert attach_grandchild.status_code == 201
    assert detached.status_code == 200
    assert detached.json() == _membership(parent.id, "children", child.id)
    assert child_after.status_code == 200
    assert grandchild_after.status_code == 200
    assert child_components.status_code == 200
    assert child_components.json() == [_membership(child.id, "children", grandchild.id)]
    assert commits[0] == 1


def test_list_direct_components_only_and_reads_do_not_commit(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        list[int],
    ],
) -> None:
    client, _datatypes, templates, objects, commits = client_context
    node, _node_v1 = _store_template(templates, name="node")
    parent = _object(objects, template_id=node.id, template_version=1)
    child = _object(objects, template_id=node.id, template_version=1)
    grandchild = _object(objects, template_id=node.id, template_version=1)
    objects.add_membership(ComponentMembership(parent.id, "children", child.id))
    objects.add_membership(ComponentMembership(child.id, "children", grandchild.id))

    response = client.get(f"/api/v1/objects/{parent.id}/components")

    assert response.status_code == 200
    assert response.json() == [_membership(parent.id, "children", child.id)]
    assert commits[0] == 0


def test_attach_missing_parent_child_and_slot_errors_flow_through_mapping(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        list[int],
    ],
) -> None:
    client, _datatypes, templates, objects, commits = client_context
    interface, _interface_v1 = _store_template(templates, name="interface")
    device, _device_v1 = _store_template(
        templates,
        name="device",
        components=(_component("interfaces", template_id=interface.id),),
    )
    parent = _object(objects, template_id=device.id, template_version=1)
    child = _object(objects, template_id=interface.id, template_version=1)

    missing_parent = client.post(
        f"/api/v1/objects/{uuid4()}/components",
        json={"slot_name": "interfaces", "component_object_id": str(child.id)},
    )
    missing_child = client.post(
        f"/api/v1/objects/{parent.id}/components",
        json={"slot_name": "interfaces", "component_object_id": str(uuid4())},
    )
    missing_slot = client.post(
        f"/api/v1/objects/{parent.id}/components",
        json={"slot_name": "modules", "component_object_id": str(child.id)},
    )

    assert missing_parent.status_code == 404
    assert missing_parent.json()["error"]["code"] == "object_not_found"
    assert missing_child.status_code == 404
    assert missing_child.json()["error"]["code"] == "object_not_found"
    assert missing_slot.status_code == 404
    assert missing_slot.json()["error"]["code"] == "object_component_slot_not_found"
    assert commits[0] == 0


def test_attach_incompatible_duplicate_and_cycle_errors_flow_through_mapping(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        list[int],
    ],
) -> None:
    client, _datatypes, templates, objects, commits = client_context
    interface, _interface_v1 = _store_template(templates, name="interface")
    unrelated, _unrelated_v1 = _store_template(templates, name="module")
    device, _device_v1 = _store_template(
        templates,
        name="device",
        components=(_component("interfaces", template_id=interface.id),),
    )
    node, _node_v1 = _store_template(
        templates,
        name="node",
        components=(),
    )
    templates.replace_version(
        ObjectTemplateVersion(
            template_id=node.id,
            version=1,
            status=ObjectTemplateVersionStatus.PUBLISHED,
            components=(_component("children", template_id=node.id),),
        )
    )
    parent = _object(objects, template_id=device.id, template_version=1)
    incompatible_child = _object(objects, template_id=unrelated.id, template_version=1)
    child = _object(objects, template_id=interface.id, template_version=1)
    other_parent = _object(objects, template_id=device.id, template_version=1)

    incompatible = client.post(
        f"/api/v1/objects/{parent.id}/components",
        json={"slot_name": "interfaces", "component_object_id": str(incompatible_child.id)},
    )
    attached = client.post(
        f"/api/v1/objects/{parent.id}/components",
        json={"slot_name": "interfaces", "component_object_id": str(child.id)},
    )
    duplicate = client.post(
        f"/api/v1/objects/{other_parent.id}/components",
        json={"slot_name": "interfaces", "component_object_id": str(child.id)},
    )

    cycle_root = _object(objects, template_id=node.id, template_version=1)
    cycle_child = _object(objects, template_id=node.id, template_version=1)
    cycle_grandchild = _object(objects, template_id=node.id, template_version=1)
    cycle_attach_a = client.post(
        f"/api/v1/objects/{cycle_root.id}/components",
        json={"slot_name": "children", "component_object_id": str(cycle_child.id)},
    )
    cycle_attach_b = client.post(
        f"/api/v1/objects/{cycle_child.id}/components",
        json={"slot_name": "children", "component_object_id": str(cycle_grandchild.id)},
    )
    cycle = client.post(
        f"/api/v1/objects/{cycle_grandchild.id}/components",
        json={"slot_name": "children", "component_object_id": str(cycle_root.id)},
    )

    assert incompatible.status_code == 409
    assert incompatible.json()["error"]["code"] == "object_component_template_incompatible"
    assert attached.status_code == 201
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "component_membership_already_exists"
    assert cycle_attach_a.status_code == 201
    assert cycle_attach_b.status_code == 201
    assert cycle.status_code == 409
    assert cycle.json()["error"]["code"] == "component_ownership_cycle"
    assert commits[0] == 3


def test_detach_missing_membership_uses_existing_mapping(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        list[int],
    ],
) -> None:
    client, _datatypes, templates, objects, commits = client_context
    node, _node_v1 = _store_template(templates, name="node")
    _parent = _object(objects, template_id=node.id, template_version=1)
    child = _object(objects, template_id=node.id, template_version=1)

    missing_membership = client.delete(f"/api/v1/objects/components/{uuid4()}")
    missing_child = client.delete(f"/api/v1/objects/components/{child.id}")

    assert missing_membership.status_code == 404
    assert missing_membership.json()["error"]["code"] == "object_not_found"
    assert missing_child.status_code == 404
    assert missing_child.json()["error"]["code"] == "component_membership_not_found"
    assert commits[0] == 0


def test_request_validation_remains_separate_for_composition_endpoints(
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
            "post",
            f"/api/v1/objects/{uuid4()}/components",
            {"slot_name": 1, "component_object_id": str(uuid4())},
            "/body/slot_name",
        ),
        (
            "post",
            f"/api/v1/objects/{uuid4()}/components",
            {"slot_name": "interfaces", "component_object_id": "not-a-uuid"},
            "/body/component_object_id",
        ),
        (
            "post",
            f"/api/v1/objects/{uuid4()}/components",
            {"slot_name": "interfaces", "component_object_id": str(uuid4()), "extra": 1},
            "/body/extra",
        ),
        (
            "get",
            "/api/v1/objects/not-a-uuid/components",
            None,
            "/path/object_id",
        ),
        (
            "delete",
            "/api/v1/objects/components/not-a-uuid",
            None,
            "/path/component_object_id",
        ),
    ]

    for method, url, payload, path in cases:
        if method == "post":
            response = client.post(url, json=payload)
        elif method == "get":
            response = client.get(url)
        else:
            response = client.delete(url)
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "request_validation_failed"
        assert any(detail["path"] == path for detail in response.json()["error"]["details"])


def test_component_membership_persistence_error_maps_to_500() -> None:
    def factory() -> BrokenObjectUnitOfWork:
        return BrokenObjectUnitOfWork()

    with TestClient(create_app(factory)) as client:
        response = client.get(
            "/api/v1/objects/00000000-0000-0000-0000-000000000001/components"
        )

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "persistence_error"


def test_openapi_contains_object_composition_routes_and_schemas(
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
    assert "/api/v1/objects/{object_id}/components" in payload["paths"]
    assert "/api/v1/objects/components/{component_object_id}" in payload["paths"]
    assert "AttachObjectComponentRequest" in payload["components"]["schemas"]
    assert "ComponentMembershipResponse" in payload["components"]["schemas"]
