from __future__ import annotations

from collections.abc import Collection
from uuid import UUID, uuid4

import pytest

from netauto.application.object import ObjectApplicationService
from netauto.application.unit_of_work import ObjectUnitOfWork
from netauto.core.object import ComponentMembership, ComponentOwnershipCycle, Object, ObjectNotFound
from netauto.core.objecttemplate import ObjectTemplate
from netauto.core.relationship import Relationship
from netauto.persistence.memory.datatype_repository import InMemoryDataTypeRepository
from netauto.persistence.memory.object_change_repository import (
    InMemoryObjectChangeRepository,
)
from netauto.persistence.memory.object_repository import InMemoryObjectRepository
from netauto.persistence.memory.objecttemplate_repository import (
    InMemoryObjectTemplateRepository,
)
from netauto.persistence.memory.relationship_repository import (
    InMemoryRelationshipDefinitionRepository,
    InMemoryRelationshipRepository,
)


class TrackingObjectTemplateRepository(InMemoryObjectTemplateRepository):
    def __init__(self) -> None:
        super().__init__()
        self.get_calls: list[UUID] = []
        self.get_version_calls: list[tuple[UUID, int]] = []

    def get(self, template_id: UUID) -> ObjectTemplate | None:
        self.get_calls.append(template_id)
        return super().get(template_id)

    def get_version(self, template_id: UUID, version: int):  # type: ignore[override]
        self.get_version_calls.append((template_id, version))
        return super().get_version(template_id, version)


class TrackingObjectRepository(InMemoryObjectRepository):
    def __init__(self) -> None:
        super().__init__()
        self.delete_calls: list[UUID] = []

    def delete(self, object_id: UUID) -> None:
        self.delete_calls.append(object_id)
        super().delete(object_id)


class RecordingObjectRepository(TrackingObjectRepository):
    def __init__(self) -> None:
        super().__init__()
        self.discovery_log: list[UUID] = []
        self.first_delete_at_discovery_count: int | None = None

    def list_components(
        self,
        parent_object_id: UUID,
        slot_name: str | None = None,
    ) -> tuple[ComponentMembership, ...]:
        self.discovery_log.append(parent_object_id)
        return super().list_components(parent_object_id, slot_name=slot_name)

    def delete(self, object_id: UUID) -> None:
        if self.first_delete_at_discovery_count is None:
            self.first_delete_at_discovery_count = len(self.discovery_log)
        super().delete(object_id)


class TrackingRelationshipRepository(InMemoryRelationshipRepository):
    def __init__(self) -> None:
        super().__init__()
        self.delete_calls: list[UUID] = []
        self.list_incident_calls: list[set[UUID]] = []

    def list_incident_to_objects(
        self,
        object_ids: Collection[UUID],
    ) -> tuple[Relationship, ...]:
        self.list_incident_calls.append(set(object_ids))
        return super().list_incident_to_objects(object_ids)

    def delete(self, relationship_id: UUID) -> None:
        self.delete_calls.append(relationship_id)
        super().delete(relationship_id)


class RecordingRelationshipRepository(TrackingRelationshipRepository):
    def __init__(self, object_repo: RecordingObjectRepository) -> None:
        super().__init__()
        self._object_repo = object_repo
        self.first_delete_at_discovery_count: int | None = None

    def delete(self, relationship_id: UUID) -> None:
        if self.first_delete_at_discovery_count is None:
            self.first_delete_at_discovery_count = len(self._object_repo.discovery_log)
        super().delete(relationship_id)


class CycleObjectRepository(InMemoryObjectRepository):
    def __init__(
        self,
        cycle_memberships_by_parent: dict[UUID, tuple[ComponentMembership, ...]],
    ) -> None:
        super().__init__()
        self._cycle_memberships_by_parent = cycle_memberships_by_parent
        self.delete_calls: list[UUID] = []

    def list_components(
        self,
        parent_object_id: UUID,
        slot_name: str | None = None,
    ) -> tuple[ComponentMembership, ...]:
        memberships = self._cycle_memberships_by_parent.get(parent_object_id, ())
        if slot_name is None:
            return memberships
        return tuple(
            membership for membership in memberships if membership.slot_name == slot_name
        )

    def delete(self, object_id: UUID) -> None:
        self.delete_calls.append(object_id)
        super().delete(object_id)


class FakeUnitOfWork(ObjectUnitOfWork):
    def __init__(
        self,
        datatypes: InMemoryDataTypeRepository,
        object_templates: TrackingObjectTemplateRepository,
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
    def object_templates(self) -> TrackingObjectTemplateRepository:
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


def _service_with_repo(
    objects: InMemoryObjectRepository,
) -> tuple[
    ObjectApplicationService,
    InMemoryDataTypeRepository,
    TrackingObjectTemplateRepository,
    InMemoryObjectRepository,
    TrackingRelationshipRepository,
    list[int],
]:
    datatypes = InMemoryDataTypeRepository()
    object_templates = TrackingObjectTemplateRepository()
    object_changes = InMemoryObjectChangeRepository()
    relationships = TrackingRelationshipRepository()
    relationship_definitions = InMemoryRelationshipDefinitionRepository()
    commit_counter = [0]

    def factory() -> FakeUnitOfWork:
        return FakeUnitOfWork(
            datatypes,
            object_templates,
            objects,
            object_changes,
            relationships,
            relationship_definitions,
            commit_counter,
        )

    return (
        ObjectApplicationService(factory, ownership_graph_uow_factory=factory),
        datatypes,
        object_templates,
        objects,
        relationships,
        commit_counter,
    )


def _service() -> tuple[
    ObjectApplicationService,
    InMemoryDataTypeRepository,
    TrackingObjectTemplateRepository,
    TrackingObjectRepository,
    TrackingRelationshipRepository,
    list[int],
]:
    objects = TrackingObjectRepository()
    service, datatypes, object_templates, _objects, relationships, commit_counter = (
        _service_with_repo(objects)
    )
    return service, datatypes, object_templates, objects, relationships, commit_counter


def _object(
    repo: InMemoryObjectRepository,
    *,
    object_id: UUID | None = None,
    template_id: UUID | None = None,
    template_version: int = 1,
) -> Object:
    object_value = Object(
        id=object_id or uuid4(),
        template_id=template_id or uuid4(),
        template_version=template_version,
        properties={},
    )
    repo.add(object_value)
    return object_value


def _membership(parent: UUID, slot_name: str, child: UUID) -> ComponentMembership:
    return ComponentMembership(
        parent_object_id=parent,
        slot_name=slot_name,
        child_object_id=child,
    )


def _relationship(
    repo: InMemoryRelationshipRepository,
    *,
    relationship_id: UUID | None = None,
    relationship_definition_id: UUID | None = None,
    source_object_id: UUID,
    target_object_id: UUID,
) -> Relationship:
    relationship = Relationship(
        id=relationship_id or uuid4(),
        relationship_definition_id=relationship_definition_id or uuid4(),
        source_object_id=source_object_id,
        target_object_id=target_object_id,
    )
    repo.add(relationship)
    return relationship


def test_delete_standalone_object_deletes_once_and_commits_once() -> None:
    service, datatypes, object_templates, objects, relationships, commits = _service()
    target = _object(objects)
    external = _object(objects)
    incoming = _relationship(
        relationships,
        source_object_id=external.id,
        target_object_id=target.id,
    )
    outgoing = _relationship(
        relationships,
        source_object_id=target.id,
        target_object_id=external.id,
    )

    service.delete_object(target.id)

    assert objects.get(target.id) is None
    assert objects.get(external.id) == external
    assert objects.delete_calls == [target.id]
    assert relationships.get(incoming.id) is None
    assert relationships.get(outgoing.id) is None
    assert relationships.delete_calls == sorted([incoming.id, outgoing.id], key=str)
    assert commits[0] == 1
    assert datatypes.list() == ()
    assert object_templates.get_calls == []
    assert object_templates.get_version_calls == []


def test_delete_missing_object_raises_and_does_not_commit() -> None:
    service, _datatypes, _object_templates, objects, relationships, commits = _service()

    with pytest.raises(ObjectNotFound):
        service.delete_object(uuid4())

    assert objects.delete_calls == []
    assert relationships.delete_calls == []
    assert commits[0] == 0


def test_delete_direct_child_cascades_to_child() -> None:
    service, _datatypes, _object_templates, objects, relationships, commits = _service()
    parent = _object(objects)
    child = _object(objects)
    external = _object(objects)
    objects.add_membership(_membership(parent.id, "children", child.id))
    parent_child_edge = _relationship(
        relationships,
        source_object_id=parent.id,
        target_object_id=child.id,
    )
    child_external_edge = _relationship(
        relationships,
        source_object_id=child.id,
        target_object_id=external.id,
    )
    survivor_edge = _relationship(
        relationships,
        source_object_id=external.id,
        target_object_id=external.id,
    )

    service.delete_object(parent.id)

    assert objects.get(parent.id) is None
    assert objects.get(child.id) is None
    assert objects.get(external.id) == external
    assert objects.get_owner(child.id) is None
    assert relationships.get(parent_child_edge.id) is None
    assert relationships.get(child_external_edge.id) is None
    assert relationships.get(survivor_edge.id) == survivor_edge
    assert objects.delete_calls == [child.id, parent.id]
    assert relationships.delete_calls == sorted(
        [parent_child_edge.id, child_external_edge.id],
        key=str,
    )
    assert commits[0] == 1


def test_delete_deep_subtree_uses_postorder() -> None:
    service, _datatypes, _object_templates, objects, _relationships, commits = _service()
    a = _object(objects)
    b = _object(objects)
    c = _object(objects)
    objects.add_membership(_membership(a.id, "children", b.id))
    objects.add_membership(_membership(b.id, "children", c.id))

    service.delete_object(a.id)

    assert objects.get(a.id) is None
    assert objects.get(b.id) is None
    assert objects.get(c.id) is None
    assert objects.delete_calls == [c.id, b.id, a.id]
    assert commits[0] == 1


def test_delete_branching_subtree_leaves_unrelated_objects() -> None:
    service, _datatypes, _object_templates, objects, relationships, commits = _service()
    a = _object(objects)
    b = _object(objects)
    c = _object(objects)
    d = _object(objects)
    x = _object(objects)
    y = _object(objects)
    objects.add_membership(_membership(a.id, "children", b.id))
    objects.add_membership(_membership(a.id, "children", c.id))
    objects.add_membership(_membership(b.id, "children", d.id))
    xy = _membership(x.id, "children", y.id)
    objects.add_membership(xy)
    external_to_parent = _relationship(
        relationships,
        source_object_id=x.id,
        target_object_id=a.id,
    )
    child_to_external = _relationship(
        relationships,
        source_object_id=b.id,
        target_object_id=x.id,
    )
    grandchild_to_external = _relationship(
        relationships,
        source_object_id=d.id,
        target_object_id=y.id,
    )
    internal_parent_child = _relationship(
        relationships,
        source_object_id=a.id,
        target_object_id=b.id,
    )
    internal_child_grandchild = _relationship(
        relationships,
        source_object_id=b.id,
        target_object_id=d.id,
    )
    unrelated_edge = _relationship(
        relationships,
        source_object_id=x.id,
        target_object_id=y.id,
    )

    service.delete_object(a.id)

    assert objects.get(a.id) is None
    assert objects.get(b.id) is None
    assert objects.get(c.id) is None
    assert objects.get(d.id) is None
    assert objects.get(x.id) == x
    assert objects.get(y.id) == y
    assert objects.get_owner(y.id) == xy
    assert relationships.get(external_to_parent.id) is None
    assert relationships.get(child_to_external.id) is None
    assert relationships.get(grandchild_to_external.id) is None
    assert relationships.get(internal_parent_child.id) is None
    assert relationships.get(internal_child_grandchild.id) is None
    assert relationships.get(unrelated_edge.id) == unrelated_edge
    assert commits[0] == 1


def test_delete_nested_component_directly_deletes_only_its_subtree() -> None:
    service, _datatypes, _object_templates, objects, relationships, commits = _service()
    a = _object(objects)
    b = _object(objects)
    c = _object(objects)
    external = _object(objects)
    objects.add_membership(_membership(a.id, "children", b.id))
    objects.add_membership(_membership(b.id, "children", c.id))
    owner_edge = _relationship(
        relationships,
        source_object_id=a.id,
        target_object_id=external.id,
    )
    child_edge = _relationship(
        relationships,
        source_object_id=b.id,
        target_object_id=external.id,
    )
    grandchild_edge = _relationship(
        relationships,
        source_object_id=c.id,
        target_object_id=external.id,
    )

    service.delete_object(b.id)

    assert objects.get(a.id) == a
    assert objects.get(b.id) is None
    assert objects.get(c.id) is None
    assert relationships.get(owner_edge.id) == owner_edge
    assert relationships.get(child_edge.id) is None
    assert relationships.get(grandchild_edge.id) is None
    assert objects.get_owner(b.id) is None
    assert objects.delete_calls == [c.id, b.id]
    assert commits[0] == 1


def test_delete_leaf_directly_preserves_owner() -> None:
    service, _datatypes, _object_templates, objects, relationships, commits = _service()
    a = _object(objects)
    b = _object(objects)
    external = _object(objects)
    objects.add_membership(_membership(a.id, "children", b.id))
    owner_edge = _relationship(
        relationships,
        source_object_id=a.id,
        target_object_id=external.id,
    )
    leaf_edge = _relationship(
        relationships,
        source_object_id=b.id,
        target_object_id=external.id,
    )

    service.delete_object(b.id)

    assert objects.get(a.id) == a
    assert objects.get(b.id) is None
    assert relationships.get(owner_edge.id) == owner_edge
    assert relationships.get(leaf_edge.id) is None
    assert objects.get_owner(b.id) is None
    assert objects.delete_calls == [b.id]
    assert commits[0] == 1


def test_detached_subtree_survives_former_owner_deletion() -> None:
    service, _datatypes, _object_templates, objects, relationships, commits = _service()
    a = _object(objects)
    b = _object(objects)
    c = _object(objects)
    bc = _membership(b.id, "children", c.id)
    objects.add_membership(_membership(a.id, "children", b.id))
    objects.add_membership(bc)
    owner_edge = _relationship(
        relationships,
        source_object_id=a.id,
        target_object_id=b.id,
    )
    detached_internal_edge = _relationship(
        relationships,
        source_object_id=b.id,
        target_object_id=c.id,
    )

    service.detach_component(b.id)
    commits[0] = 0
    objects.delete_calls.clear()
    relationships.delete_calls.clear()

    service.delete_object(a.id)

    assert objects.get(a.id) is None
    assert objects.get(b.id) == b
    assert objects.get(c.id) == c
    assert objects.get_owner(b.id) is None
    assert objects.get_owner(c.id) == bc
    assert relationships.get(owner_edge.id) is None
    assert relationships.get(detached_internal_edge.id) == detached_internal_edge
    assert objects.delete_calls == [a.id]
    assert relationships.delete_calls == [owner_edge.id]
    assert commits[0] == 1


def test_delete_unrelated_composition_survives() -> None:
    service, _datatypes, _object_templates, objects, relationships, commits = _service()
    a = _object(objects)
    b = _object(objects)
    x = _object(objects)
    y = _object(objects)
    objects.add_membership(_membership(a.id, "children", b.id))
    xy = _membership(x.id, "children", y.id)
    objects.add_membership(xy)
    unrelated_edge = _relationship(
        relationships,
        source_object_id=x.id,
        target_object_id=y.id,
    )

    service.delete_object(a.id)

    assert objects.get(a.id) is None
    assert objects.get(b.id) is None
    assert objects.get(x.id) == x
    assert objects.get(y.id) == y
    assert objects.get_owner(y.id) == xy
    assert relationships.get(unrelated_edge.id) == unrelated_edge
    assert commits[0] == 1


def test_delete_discovers_complete_subtree_before_first_mutation() -> None:
    repo = RecordingObjectRepository()
    relationship_repo = RecordingRelationshipRepository(repo)
    datatypes = InMemoryDataTypeRepository()
    object_templates = TrackingObjectTemplateRepository()
    object_changes = InMemoryObjectChangeRepository()
    relationship_definitions = InMemoryRelationshipDefinitionRepository()
    commits = [0]

    def factory() -> FakeUnitOfWork:
        return FakeUnitOfWork(
            datatypes,
            object_templates,
            repo,
            object_changes,
            relationship_repo,
            relationship_definitions,
            commits,
        )

    service = ObjectApplicationService(factory, ownership_graph_uow_factory=factory)
    a = _object(repo)
    b = _object(repo)
    c = _object(repo)
    repo.add_membership(_membership(a.id, "children", b.id))
    repo.add_membership(_membership(b.id, "children", c.id))
    internal = _relationship(
        relationship_repo,
        source_object_id=a.id,
        target_object_id=b.id,
    )

    service.delete_object(a.id)

    assert repo.discovery_log == [a.id, b.id, c.id]
    assert relationship_repo.list_incident_calls == [{a.id, b.id, c.id}]
    assert relationship_repo.first_delete_at_discovery_count == 3
    assert repo.first_delete_at_discovery_count == 3
    assert relationship_repo.delete_calls == [internal.id]
    assert repo.delete_calls == [c.id, b.id, a.id]
    assert commits[0] == 1


def test_delete_corrupt_cycle_raises_before_any_mutation_or_commit() -> None:
    a = Object(id=uuid4(), template_id=uuid4(), template_version=1, properties={})
    b = Object(id=uuid4(), template_id=uuid4(), template_version=1, properties={})
    c = Object(id=uuid4(), template_id=uuid4(), template_version=1, properties={})
    repo = CycleObjectRepository(
        {
            a.id: (_membership(a.id, "children", b.id),),
            b.id: (_membership(b.id, "children", c.id),),
            c.id: (_membership(c.id, "children", a.id),),
        }
    )
    repo.add(a)
    repo.add(b)
    repo.add(c)
    datatypes = InMemoryDataTypeRepository()
    object_templates = TrackingObjectTemplateRepository()
    object_changes = InMemoryObjectChangeRepository()
    relationships = TrackingRelationshipRepository()
    relationship_definitions = InMemoryRelationshipDefinitionRepository()
    commits = [0]

    def factory() -> FakeUnitOfWork:
        return FakeUnitOfWork(
            datatypes,
            object_templates,
            repo,
            object_changes,
            relationships,
            relationship_definitions,
            commits,
        )

    service = ObjectApplicationService(factory, ownership_graph_uow_factory=factory)

    with pytest.raises(ComponentOwnershipCycle):
        service.delete_object(a.id)

    assert repo.get(a.id) == a
    assert repo.get(b.id) == b
    assert repo.get(c.id) == c
    assert relationships.delete_calls == []
    assert repo.delete_calls == []
    assert commits[0] == 0
