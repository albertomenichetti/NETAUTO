from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from netauto.application.object import ObjectApplicationService
from netauto.application.unit_of_work import ObjectUnitOfWork
from netauto.core.datatype import (
    DataType,
    DataTypeFactory,
    DataTypeVersion,
    DataTypeVersioningService,
)
from netauto.core.object import (
    ComponentMembership,
    MissingObjectMigrationPropertyValue,
    Object,
    ObjectChange,
    ObjectChangeKind,
    ObjectMigrationBlocked,
)
from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateComponent,
    ObjectTemplateInheritanceResolver,
    ObjectTemplateProperty,
    ObjectTemplateVersion,
    ObjectTemplateVersionRef,
    ObjectTemplateVersionStatus,
)
from netauto.core.relationship import (
    Relationship,
    RelationshipDefinition,
    relationship_definition_applies,
)
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


class TrackingObjectRepository(InMemoryObjectRepository):
    def __init__(self) -> None:
        super().__init__()
        self.replace_calls: list[Object] = []
        self.add_membership_calls: list[ComponentMembership] = []
        self.remove_membership_calls: list[UUID] = []

    def replace(self, object_value: Object) -> None:
        self.replace_calls.append(object_value)
        super().replace(object_value)

    def add_membership(self, membership: ComponentMembership) -> None:
        self.add_membership_calls.append(membership)
        super().add_membership(membership)

    def remove_membership(self, child_object_id: UUID) -> None:
        self.remove_membership_calls.append(child_object_id)
        super().remove_membership(child_object_id)


class TrackingObjectChangeRepository(InMemoryObjectChangeRepository):
    def __init__(self) -> None:
        super().__init__()
        self.add_calls: list[UUID] = []

    def add(self, change: ObjectChange) -> None:
        self.add_calls.append(change.object_id)
        super().add(change)


class TrackingRelationshipRepository(InMemoryRelationshipRepository):
    def __init__(self) -> None:
        super().__init__()
        self.add_calls: list[UUID] = []
        self.delete_calls: list[UUID] = []

    def add(self, relationship: Relationship) -> None:
        self.add_calls.append(relationship.id)
        super().add(relationship)

    def delete(self, relationship_id: UUID) -> None:
        self.delete_calls.append(relationship_id)
        super().delete(relationship_id)


class FakeUnitOfWork(ObjectUnitOfWork):
    def __init__(
        self,
        datatypes: InMemoryDataTypeRepository,
        object_templates: InMemoryObjectTemplateRepository,
        objects: TrackingObjectRepository,
        object_changes: TrackingObjectChangeRepository,
        relationships: TrackingRelationshipRepository,
        relationship_definitions: InMemoryRelationshipDefinitionRepository,
        commits: list[int],
    ) -> None:
        self._datatypes = datatypes
        self._object_templates = object_templates
        self._objects = objects
        self._object_changes = object_changes
        self._relationships = relationships
        self._relationship_definitions = relationship_definitions
        self._commits = commits

    @property
    def datatypes(self) -> InMemoryDataTypeRepository:
        return self._datatypes

    @property
    def object_templates(self) -> InMemoryObjectTemplateRepository:
        return self._object_templates

    @property
    def objects(self) -> TrackingObjectRepository:
        return self._objects

    @property
    def object_changes(self) -> TrackingObjectChangeRepository:
        return self._object_changes

    @property
    def relationships(self) -> TrackingRelationshipRepository:
        return self._relationships

    @property
    def relationship_definitions(self) -> InMemoryRelationshipDefinitionRepository:
        return self._relationship_definitions

    def __enter__(self) -> FakeUnitOfWork:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    def commit(self) -> None:
        self._commits[0] += 1


def _service(
    *,
    clock: Callable[[], datetime] | None = None,
) -> tuple[
    ObjectApplicationService,
    InMemoryDataTypeRepository,
    InMemoryObjectTemplateRepository,
    TrackingObjectRepository,
    TrackingObjectChangeRepository,
    TrackingRelationshipRepository,
    InMemoryRelationshipDefinitionRepository,
    list[int],
]:
    datatypes = InMemoryDataTypeRepository()
    object_templates = InMemoryObjectTemplateRepository()
    objects = TrackingObjectRepository()
    object_changes = TrackingObjectChangeRepository()
    relationships = TrackingRelationshipRepository()
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

    return (
        ObjectApplicationService(factory, clock=clock),
        datatypes,
        object_templates,
        objects,
        object_changes,
        relationships,
        relationship_definitions,
        commits,
    )


def _datatype(
    *,
    namespace: str = "network",
    name: str,
) -> tuple[DataType, DataTypeVersion]:
    datatype, draft = DataTypeFactory().create(
        namespace=namespace,
        name=name,
        description=f"{name} datatype",
        base_type="core.string",
        constraints=(),
    )
    return datatype, DataTypeVersioningService().publish(draft)


def _store_datatype_versions(
    repo: InMemoryDataTypeRepository,
    datatype: DataType,
    versions: tuple[DataTypeVersion, ...],
) -> None:
    repo.add(datatype)
    for version in versions:
        repo.add_version(version)


def _template(
    *,
    name: str,
    namespace: str = "network",
    abstract: bool = False,
) -> ObjectTemplate:
    return ObjectTemplate(
        id=uuid4(),
        namespace=namespace,
        name=name,
        description=f"{name} template",
        abstract=abstract,
    )


def _version(
    template_id: UUID,
    *,
    version: int,
    status: ObjectTemplateVersionStatus = ObjectTemplateVersionStatus.PUBLISHED,
    parent: ObjectTemplateVersionRef | None = None,
    properties: tuple[ObjectTemplateProperty, ...] = (),
    components: tuple[ObjectTemplateComponent, ...] = (),
) -> ObjectTemplateVersion:
    return ObjectTemplateVersion(
        template_id=template_id,
        version=version,
        status=status,
        parent=parent,
        properties=properties,
        components=components,
    )


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


def _component(name: str, *, template_id: UUID) -> ObjectTemplateComponent:
    return ObjectTemplateComponent(name=name, template_id=template_id)


def _store_template_versions(
    repo: InMemoryObjectTemplateRepository,
    template: ObjectTemplate,
    versions: tuple[ObjectTemplateVersion, ...],
) -> None:
    repo.add(template)
    for version in versions:
        repo.add_version(version)


def _create_object(
    repo: TrackingObjectRepository,
    *,
    template_id: UUID,
    template_version: int,
    properties: Mapping[str, object] | None = None,
    object_id: UUID | None = None,
) -> Object:
    object_value = Object(
        id=object_id or uuid4(),
        template_id=template_id,
        template_version=template_version,
        properties=properties or {},
    )
    repo.add(object_value)
    return object_value


def _membership(
    parent_object_id: UUID,
    slot_name: str,
    child_object_id: UUID,
) -> ComponentMembership:
    return ComponentMembership(
        parent_object_id=parent_object_id,
        slot_name=slot_name,
        child_object_id=child_object_id,
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
    repo: TrackingRelationshipRepository,
    *,
    relationship_definition_id: UUID,
    source_object_id: UUID,
    target_object_id: UUID,
    relationship_id: UUID | None = None,
) -> Relationship:
    value = Relationship(
        id=relationship_id or uuid4(),
        relationship_definition_id=relationship_definition_id,
        source_object_id=source_object_id,
        target_object_id=target_object_id,
    )
    repo.add(value)
    return value


def _parent_lookup(
    repo: InMemoryObjectTemplateRepository,
    ref: ObjectTemplateVersionRef,
) -> ObjectTemplateVersion | None:
    return repo.get_version(ref.template_id, ref.version)


def _ancestry_identity_path(
    version: ObjectTemplateVersion,
    repo: InMemoryObjectTemplateRepository,
) -> tuple[UUID, ...]:
    path: list[UUID] = []
    current: ObjectTemplateVersion | None = version
    while current is not None:
        path.append(current.template_id)
        if current.parent is None:
            break
        current = repo.get_version(current.parent.template_id, current.parent.version)
    return tuple(path)


def _assert_single_migrated_change(
    object_changes: TrackingObjectChangeRepository,
    *,
    object_id: UUID,
    source_version: int,
    target_version: int,
    occurred_at: datetime,
) -> None:
    history = object_changes.list_by_object(object_id)
    assert len(history) == 1
    assert history[0].kind is ObjectChangeKind.MIGRATED
    assert history[0].occurred_at == occurred_at
    assert history[0].before is not None
    assert history[0].after is not None
    assert history[0].before.template_version == source_version
    assert history[0].after.template_version == target_version


def test_same_template_migration_preserves_component_child_membership_for_direct_parent() -> None:
    occurred_at = datetime(2026, 8, 11, 8, 30, tzinfo=UTC)
    (
        service,
        _datatypes,
        object_templates,
        objects,
        object_changes,
        relationships,
        _relationship_definitions,
        commits,
    ) = _service(clock=lambda: occurred_at)
    parent = _template(name="component_base")
    child = _template(name="child")
    container = _template(name="container")
    parent_v1 = _version(parent.id, version=1)
    parent_v2 = _version(parent.id, version=2)
    child_v1 = _version(
        child.id,
        version=1,
        parent=ObjectTemplateVersionRef(template_id=parent.id, version=1),
    )
    child_v2 = _version(
        child.id,
        version=2,
        parent=ObjectTemplateVersionRef(template_id=parent.id, version=2),
    )
    container_v1 = _version(
        container.id,
        version=1,
        components=(_component("children", template_id=parent.id),),
    )
    _store_template_versions(object_templates, parent, (parent_v1, parent_v2))
    _store_template_versions(object_templates, child, (child_v1, child_v2))
    _store_template_versions(object_templates, container, (container_v1,))

    owner = _create_object(objects, template_id=container.id, template_version=1)
    component = _create_object(objects, template_id=child.id, template_version=1)
    membership = _membership(owner.id, "children", component.id)
    objects.add_membership(membership)
    add_membership_calls_before = len(objects.add_membership_calls)
    remove_membership_calls_before = len(objects.remove_membership_calls)

    result = service.migrate_objects(
        template_id=child.id,
        source_version=1,
        target_version=2,
        property_values={},
    )

    migrated = objects.get(component.id)
    assert migrated is not None
    assert migrated.template_version == 2
    assert result.migrated_count == 1
    assert objects.get_owner(component.id) == membership
    assert objects.list_components(owner.id) == (membership,)
    assert ObjectTemplateInheritanceResolver().is_same_or_descendant_template(
        child_v2,
        required_template_id=parent.id,
        parent_lookup=lambda ref: _parent_lookup(object_templates, ref),
    )
    assert len(objects.add_membership_calls) == add_membership_calls_before
    assert len(objects.remove_membership_calls) == remove_membership_calls_before
    assert relationships.delete_calls == []
    assert commits[0] == 1
    _assert_single_migrated_change(
        object_changes,
        object_id=component.id,
        source_version=1,
        target_version=2,
        occurred_at=occurred_at,
    )


def test_same_template_migration_preserves_recursive_ancestry_identity_space() -> None:
    occurred_at = datetime(2026, 8, 11, 8, 40, tzinfo=UTC)
    (
        service,
        _datatypes,
        object_templates,
        objects,
        object_changes,
        relationships,
        _relationship_definitions,
        commits,
    ) = _service(clock=lambda: occurred_at)
    entity = _template(name="entity")
    interface = _template(name="interface")
    ethernet = _template(name="ethernet_interface")
    container = _template(name="container")
    entity_v1 = _version(entity.id, version=1)
    entity_v3 = _version(entity.id, version=3)
    interface_v1 = _version(
        interface.id,
        version=1,
        parent=ObjectTemplateVersionRef(template_id=entity.id, version=1),
    )
    interface_v2 = _version(
        interface.id,
        version=2,
        parent=ObjectTemplateVersionRef(template_id=entity.id, version=3),
    )
    ethernet_v1 = _version(
        ethernet.id,
        version=1,
        parent=ObjectTemplateVersionRef(template_id=interface.id, version=1),
    )
    ethernet_v2 = _version(
        ethernet.id,
        version=2,
        parent=ObjectTemplateVersionRef(template_id=interface.id, version=2),
    )
    container_v1 = _version(
        container.id,
        version=1,
        components=(_component("interfaces", template_id=entity.id),),
    )
    _store_template_versions(object_templates, entity, (entity_v1, entity_v3))
    _store_template_versions(object_templates, interface, (interface_v1, interface_v2))
    _store_template_versions(object_templates, ethernet, (ethernet_v1, ethernet_v2))
    _store_template_versions(object_templates, container, (container_v1,))

    assert _ancestry_identity_path(ethernet_v1, object_templates) == (
        ethernet.id,
        interface.id,
        entity.id,
    )
    assert _ancestry_identity_path(ethernet_v2, object_templates) == (
        ethernet.id,
        interface.id,
        entity.id,
    )

    owner = _create_object(objects, template_id=container.id, template_version=1)
    child = _create_object(objects, template_id=ethernet.id, template_version=1)
    membership = _membership(owner.id, "interfaces", child.id)
    objects.add_membership(membership)
    add_membership_calls_before = len(objects.add_membership_calls)

    result = service.migrate_objects(
        template_id=ethernet.id,
        source_version=1,
        target_version=2,
        property_values={},
    )

    migrated = objects.get(child.id)
    assert migrated is not None
    assert migrated.template_version == 2
    assert result.migrated_count == 1
    assert objects.get_owner(child.id) == membership
    assert ObjectTemplateInheritanceResolver().is_same_or_descendant_template(
        ethernet_v2,
        required_template_id=entity.id,
        parent_lookup=lambda ref: _parent_lookup(object_templates, ref),
    )
    assert len(objects.add_membership_calls) == add_membership_calls_before
    assert objects.remove_membership_calls == []
    assert relationships.delete_calls == []
    assert commits[0] == 1
    _assert_single_migrated_change(
        object_changes,
        object_id=child.id,
        source_version=1,
        target_version=2,
        occurred_at=occurred_at,
    )


def test_same_template_migration_preserves_relationship_source_compatibility() -> None:
    occurred_at = datetime(2026, 8, 11, 8, 50, tzinfo=UTC)
    (
        service,
        _datatypes,
        object_templates,
        objects,
        object_changes,
        relationships,
        relationship_definitions,
        commits,
    ) = _service(clock=lambda: occurred_at)
    parent = _template(name="device")
    child = _template(name="router")
    network = _template(name="network")
    parent_v1 = _version(parent.id, version=1)
    parent_v2 = _version(parent.id, version=2)
    child_v1 = _version(
        child.id,
        version=1,
        parent=ObjectTemplateVersionRef(template_id=parent.id, version=1),
    )
    child_v2 = _version(
        child.id,
        version=2,
        parent=ObjectTemplateVersionRef(template_id=parent.id, version=2),
    )
    network_v1 = _version(network.id, version=1)
    _store_template_versions(object_templates, parent, (parent_v1, parent_v2))
    _store_template_versions(object_templates, child, (child_v1, child_v2))
    _store_template_versions(object_templates, network, (network_v1,))
    definition = _definition(source_template_id=parent.id, target_template_id=network.id)
    relationship_definitions.add(definition)

    source = _create_object(objects, template_id=child.id, template_version=1)
    target = _create_object(objects, template_id=network.id, template_version=1)
    relationship = _relationship(
        relationships,
        relationship_definition_id=definition.id,
        source_object_id=source.id,
        target_object_id=target.id,
    )
    add_calls_before = len(relationships.add_calls)
    delete_calls_before = len(relationships.delete_calls)

    result = service.migrate_objects(
        template_id=child.id,
        source_version=1,
        target_version=2,
        property_values={},
    )

    assert result.migrated_count == 1
    assert relationships.get(relationship.id) == relationship
    assert relationship_definition_applies(
        definition,
        source_version=child_v2,
        target_version=network_v1,
        parent_lookup=lambda ref: _parent_lookup(object_templates, ref),
    )
    assert len(relationships.add_calls) == add_calls_before
    assert len(relationships.delete_calls) == delete_calls_before
    assert commits[0] == 1
    _assert_single_migrated_change(
        object_changes,
        object_id=source.id,
        source_version=1,
        target_version=2,
        occurred_at=occurred_at,
    )


def test_same_template_migration_preserves_relationship_target_compatibility() -> None:
    occurred_at = datetime(2026, 8, 11, 9, 0, tzinfo=UTC)
    (
        service,
        _datatypes,
        object_templates,
        objects,
        object_changes,
        relationships,
        relationship_definitions,
        commits,
    ) = _service(clock=lambda: occurred_at)
    parent = _template(name="device")
    child = _template(name="router")
    network = _template(name="network")
    parent_v1 = _version(parent.id, version=1)
    parent_v2 = _version(parent.id, version=2)
    child_v1 = _version(
        child.id,
        version=1,
        parent=ObjectTemplateVersionRef(template_id=parent.id, version=1),
    )
    child_v2 = _version(
        child.id,
        version=2,
        parent=ObjectTemplateVersionRef(template_id=parent.id, version=2),
    )
    network_v1 = _version(network.id, version=1)
    _store_template_versions(object_templates, parent, (parent_v1, parent_v2))
    _store_template_versions(object_templates, child, (child_v1, child_v2))
    _store_template_versions(object_templates, network, (network_v1,))
    definition = _definition(source_template_id=network.id, target_template_id=parent.id)
    relationship_definitions.add(definition)

    source = _create_object(objects, template_id=network.id, template_version=1)
    target = _create_object(objects, template_id=child.id, template_version=1)
    relationship = _relationship(
        relationships,
        relationship_definition_id=definition.id,
        source_object_id=source.id,
        target_object_id=target.id,
    )
    add_calls_before = len(relationships.add_calls)

    result = service.migrate_objects(
        template_id=child.id,
        source_version=1,
        target_version=2,
        property_values={},
    )

    assert result.migrated_count == 1
    assert relationships.get(relationship.id) == relationship
    assert relationship_definition_applies(
        definition,
        source_version=network_v1,
        target_version=child_v2,
        parent_lookup=lambda ref: _parent_lookup(object_templates, ref),
    )
    assert len(relationships.add_calls) == add_calls_before
    assert relationships.delete_calls == []
    assert commits[0] == 1
    _assert_single_migrated_change(
        object_changes,
        object_id=target.id,
        source_version=1,
        target_version=2,
        occurred_at=occurred_at,
    )


def test_same_template_bulk_migration_preserves_relationship_when_both_endpoints_move() -> None:
    occurred_at = datetime(2026, 8, 11, 9, 10, tzinfo=UTC)
    (
        service,
        _datatypes,
        object_templates,
        objects,
        object_changes,
        relationships,
        relationship_definitions,
        commits,
    ) = _service(clock=lambda: occurred_at)
    parent = _template(name="device")
    child = _template(name="router")
    parent_v1 = _version(parent.id, version=1)
    parent_v2 = _version(parent.id, version=2)
    child_v1 = _version(
        child.id,
        version=1,
        parent=ObjectTemplateVersionRef(template_id=parent.id, version=1),
    )
    child_v2 = _version(
        child.id,
        version=2,
        parent=ObjectTemplateVersionRef(template_id=parent.id, version=2),
    )
    _store_template_versions(object_templates, parent, (parent_v1, parent_v2))
    _store_template_versions(object_templates, child, (child_v1, child_v2))
    definition = _definition(source_template_id=parent.id, target_template_id=parent.id)
    relationship_definitions.add(definition)

    left = _create_object(objects, template_id=child.id, template_version=1)
    right = _create_object(objects, template_id=child.id, template_version=1)
    relationship = _relationship(
        relationships,
        relationship_definition_id=definition.id,
        source_object_id=left.id,
        target_object_id=right.id,
    )
    add_calls_before = len(relationships.add_calls)

    result = service.migrate_objects(
        template_id=child.id,
        source_version=1,
        target_version=2,
        property_values={},
    )

    assert result.migrated_count == 2
    assert objects.get(left.id) == Object(
        id=left.id,
        template_id=child.id,
        template_version=2,
        properties={},
    )
    assert objects.get(right.id) == Object(
        id=right.id,
        template_id=child.id,
        template_version=2,
        properties={},
    )
    assert relationships.get(relationship.id) == relationship
    assert relationship_definition_applies(
        definition,
        source_version=child_v2,
        target_version=child_v2,
        parent_lookup=lambda ref: _parent_lookup(object_templates, ref),
    )
    assert len(relationships.add_calls) == add_calls_before
    assert relationships.delete_calls == []
    assert commits[0] == 1
    _assert_single_migrated_change(
        object_changes,
        object_id=left.id,
        source_version=1,
        target_version=2,
        occurred_at=occurred_at,
    )
    _assert_single_migrated_change(
        object_changes,
        object_id=right.id,
        source_version=1,
        target_version=2,
        occurred_at=occurred_at,
    )


def test_same_template_migration_preserves_self_link_relationship() -> None:
    occurred_at = datetime(2026, 8, 11, 9, 20, tzinfo=UTC)
    (
        service,
        _datatypes,
        object_templates,
        objects,
        object_changes,
        relationships,
        relationship_definitions,
        commits,
    ) = _service(clock=lambda: occurred_at)
    parent = _template(name="device")
    child = _template(name="router")
    parent_v1 = _version(parent.id, version=1)
    parent_v2 = _version(parent.id, version=2)
    child_v1 = _version(
        child.id,
        version=1,
        parent=ObjectTemplateVersionRef(template_id=parent.id, version=1),
    )
    child_v2 = _version(
        child.id,
        version=2,
        parent=ObjectTemplateVersionRef(template_id=parent.id, version=2),
    )
    _store_template_versions(object_templates, parent, (parent_v1, parent_v2))
    _store_template_versions(object_templates, child, (child_v1, child_v2))
    definition = _definition(
        source_template_id=parent.id,
        target_template_id=parent.id,
        forward_name="connects_to",
        reverse_name="connected_from",
    )
    relationship_definitions.add(definition)

    object_value = _create_object(objects, template_id=child.id, template_version=1)
    relationship = _relationship(
        relationships,
        relationship_definition_id=definition.id,
        source_object_id=object_value.id,
        target_object_id=object_value.id,
    )

    result = service.migrate_objects(
        template_id=child.id,
        source_version=1,
        target_version=2,
        property_values={},
    )

    assert result.migrated_count == 1
    assert relationships.get(relationship.id) == relationship
    assert relationship_definition_applies(
        definition,
        source_version=child_v2,
        target_version=child_v2,
        parent_lookup=lambda ref: _parent_lookup(object_templates, ref),
    )
    assert relationships.delete_calls == []
    assert commits[0] == 1
    _assert_single_migrated_change(
        object_changes,
        object_id=object_value.id,
        source_version=1,
        target_version=2,
        occurred_at=occurred_at,
    )


def test_same_template_migration_from_deprecated_source_preserves_membership_and_relationship(
) -> None:
    occurred_at = datetime(2026, 8, 11, 9, 30, tzinfo=UTC)
    (
        service,
        _datatypes,
        object_templates,
        objects,
        object_changes,
        relationships,
        relationship_definitions,
        commits,
    ) = _service(clock=lambda: occurred_at)
    parent = _template(name="device")
    child = _template(name="router")
    container = _template(name="container")
    network = _template(name="network")
    parent_v1 = _version(parent.id, version=1)
    parent_v2 = _version(parent.id, version=2)
    child_v1 = _version(
        child.id,
        version=1,
        status=ObjectTemplateVersionStatus.DEPRECATED,
        parent=ObjectTemplateVersionRef(template_id=parent.id, version=1),
    )
    child_v2 = _version(
        child.id,
        version=2,
        parent=ObjectTemplateVersionRef(template_id=parent.id, version=2),
    )
    container_v1 = _version(
        container.id,
        version=1,
        components=(_component("children", template_id=parent.id),),
    )
    network_v1 = _version(network.id, version=1)
    _store_template_versions(object_templates, parent, (parent_v1, parent_v2))
    _store_template_versions(object_templates, child, (child_v1, child_v2))
    _store_template_versions(object_templates, container, (container_v1,))
    _store_template_versions(object_templates, network, (network_v1,))
    definition = _definition(source_template_id=parent.id, target_template_id=network.id)
    relationship_definitions.add(definition)

    owner = _create_object(objects, template_id=container.id, template_version=1)
    source = _create_object(objects, template_id=child.id, template_version=1)
    target = _create_object(objects, template_id=network.id, template_version=1)
    membership = _membership(owner.id, "children", source.id)
    objects.add_membership(membership)
    relationship = _relationship(
        relationships,
        relationship_definition_id=definition.id,
        source_object_id=source.id,
        target_object_id=target.id,
    )
    add_membership_calls_before = len(objects.add_membership_calls)
    add_relationship_calls_before = len(relationships.add_calls)

    result = service.migrate_objects(
        template_id=child.id,
        source_version=1,
        target_version=2,
        property_values={},
    )

    assert result.migrated_count == 1
    assert objects.get_owner(source.id) == membership
    assert relationships.get(relationship.id) == relationship
    assert relationship_definition_applies(
        definition,
        source_version=child_v2,
        target_version=network_v1,
        parent_lookup=lambda ref: _parent_lookup(object_templates, ref),
    )
    assert len(objects.add_membership_calls) == add_membership_calls_before
    assert len(relationships.add_calls) == add_relationship_calls_before
    assert objects.remove_membership_calls == []
    assert relationships.delete_calls == []
    assert commits[0] == 1
    _assert_single_migrated_change(
        object_changes,
        object_id=source.id,
        source_version=1,
        target_version=2,
        occurred_at=occurred_at,
    )


def test_parent_exact_version_advance_with_inherited_optional_property_remains_safe() -> None:
    occurred_at = datetime(2026, 8, 11, 9, 40, tzinfo=UTC)
    (
        service,
        datatypes,
        object_templates,
        objects,
        object_changes,
        relationships,
        relationship_definitions,
        commits,
    ) = _service(clock=lambda: occurred_at)
    hostname, hostname_v1 = _datatype(name="hostname")
    description, description_v1 = _datatype(name="description")
    _store_datatype_versions(datatypes, hostname, (hostname_v1,))
    _store_datatype_versions(datatypes, description, (description_v1,))
    parent = _template(name="device")
    child = _template(name="router")
    container = _template(name="container")
    network = _template(name="network")
    parent_v1 = _version(
        parent.id,
        version=1,
        properties=(
            _property("hostname", datatype_id=hostname.id, datatype_version=1, required=True),
        ),
    )
    parent_v2 = _version(
        parent.id,
        version=2,
        properties=(
            _property("hostname", datatype_id=hostname.id, datatype_version=1, required=True),
            _property(
                "description",
                datatype_id=description.id,
                datatype_version=1,
                required=False,
            ),
        ),
    )
    child_v1 = _version(
        child.id,
        version=1,
        parent=ObjectTemplateVersionRef(template_id=parent.id, version=1),
    )
    child_v2 = _version(
        child.id,
        version=2,
        parent=ObjectTemplateVersionRef(template_id=parent.id, version=2),
    )
    container_v1 = _version(
        container.id,
        version=1,
        components=(_component("children", template_id=parent.id),),
    )
    network_v1 = _version(network.id, version=1)
    _store_template_versions(object_templates, parent, (parent_v1, parent_v2))
    _store_template_versions(object_templates, child, (child_v1, child_v2))
    _store_template_versions(object_templates, container, (container_v1,))
    _store_template_versions(object_templates, network, (network_v1,))
    definition = _definition(source_template_id=parent.id, target_template_id=network.id)
    relationship_definitions.add(definition)

    owner = _create_object(objects, template_id=container.id, template_version=1)
    source = _create_object(
        objects,
        template_id=child.id,
        template_version=1,
        properties={"hostname": "router-01"},
    )
    target = _create_object(objects, template_id=network.id, template_version=1)
    membership = _membership(owner.id, "children", source.id)
    objects.add_membership(membership)
    relationship = _relationship(
        relationships,
        relationship_definition_id=definition.id,
        source_object_id=source.id,
        target_object_id=target.id,
    )

    analysis = service.analyze_object_migration(
        template_id=child.id,
        source_version=1,
        target_version=2,
    )
    result = service.migrate_objects(
        template_id=child.id,
        source_version=1,
        target_version=2,
        property_values={},
    )

    migrated = objects.get(source.id)
    assert analysis.automatic is True
    assert [(item.name, item.required) for item in analysis.added_properties] == [
        ("description", False)
    ]
    assert migrated is not None
    assert migrated.template_version == 2
    assert migrated.properties == {"hostname": "router-01"}
    assert result.migrated_count == 1
    assert objects.get_owner(source.id) == membership
    assert relationships.get(relationship.id) == relationship
    assert relationship_definition_applies(
        definition,
        source_version=child_v2,
        target_version=network_v1,
        parent_lookup=lambda ref: _parent_lookup(object_templates, ref),
    )
    assert objects.remove_membership_calls == []
    assert relationships.delete_calls == []
    assert commits[0] == 1
    _assert_single_migrated_change(
        object_changes,
        object_id=source.id,
        source_version=1,
        target_version=2,
        occurred_at=occurred_at,
    )


def test_inherited_required_property_migration_keeps_edges_safe(
) -> None:
    occurred_at = datetime(2026, 8, 11, 9, 50, tzinfo=UTC)
    (
        service,
        datatypes,
        object_templates,
        objects,
        object_changes,
        relationships,
        relationship_definitions,
        commits,
    ) = _service(clock=lambda: occurred_at)
    hostname, hostname_v1 = _datatype(name="hostname")
    description, description_v1 = _datatype(name="description")
    _store_datatype_versions(datatypes, hostname, (hostname_v1,))
    _store_datatype_versions(datatypes, description, (description_v1,))
    parent = _template(name="device")
    child = _template(name="router")
    container = _template(name="container")
    network = _template(name="network")
    parent_v1 = _version(
        parent.id,
        version=1,
        properties=(
            _property("hostname", datatype_id=hostname.id, datatype_version=1, required=True),
        ),
    )
    parent_v2 = _version(
        parent.id,
        version=2,
        properties=(
            _property("hostname", datatype_id=hostname.id, datatype_version=1, required=True),
            _property(
                "description",
                datatype_id=description.id,
                datatype_version=1,
                required=True,
            ),
        ),
    )
    child_v1 = _version(
        child.id,
        version=1,
        parent=ObjectTemplateVersionRef(template_id=parent.id, version=1),
    )
    child_v2 = _version(
        child.id,
        version=2,
        parent=ObjectTemplateVersionRef(template_id=parent.id, version=2),
    )
    container_v1 = _version(
        container.id,
        version=1,
        components=(_component("children", template_id=parent.id),),
    )
    network_v1 = _version(network.id, version=1)
    _store_template_versions(object_templates, parent, (parent_v1, parent_v2))
    _store_template_versions(object_templates, child, (child_v1, child_v2))
    _store_template_versions(object_templates, container, (container_v1,))
    _store_template_versions(object_templates, network, (network_v1,))
    definition = _definition(source_template_id=parent.id, target_template_id=network.id)
    relationship_definitions.add(definition)

    owner = _create_object(objects, template_id=container.id, template_version=1)
    source = _create_object(
        objects,
        template_id=child.id,
        template_version=1,
        properties={"hostname": "router-01"},
    )
    target = _create_object(objects, template_id=network.id, template_version=1)
    membership = _membership(owner.id, "children", source.id)
    objects.add_membership(membership)
    relationship = _relationship(
        relationships,
        relationship_definition_id=definition.id,
        source_object_id=source.id,
        target_object_id=target.id,
    )
    analysis = service.analyze_object_migration(
        template_id=child.id,
        source_version=1,
        target_version=2,
    )

    with pytest.raises(MissingObjectMigrationPropertyValue):
        service.migrate_objects(
            template_id=child.id,
            source_version=1,
            target_version=2,
            property_values={},
        )

    assert analysis.automatic is True
    assert [(item.name, item.required) for item in analysis.added_properties] == [
        ("description", True)
    ]
    assert objects.get(source.id) == source
    assert objects.get_owner(source.id) == membership
    assert relationships.get(relationship.id) == relationship
    assert object_changes.list_by_object(source.id) == ()
    assert objects.replace_calls == []
    assert relationships.delete_calls == []
    assert objects.remove_membership_calls == []
    assert commits[0] == 0

    result = service.migrate_objects(
        template_id=child.id,
        source_version=1,
        target_version=2,
        property_values={"description": "edge-safe"},
    )

    migrated = objects.get(source.id)
    assert migrated is not None
    assert migrated.template_version == 2
    assert migrated.properties == {
        "hostname": "router-01",
        "description": "edge-safe",
    }
    assert result.migrated_count == 1
    assert objects.get_owner(source.id) == membership
    assert relationships.get(relationship.id) == relationship
    assert relationship_definition_applies(
        definition,
        source_version=child_v2,
        target_version=network_v1,
        parent_lookup=lambda ref: _parent_lookup(object_templates, ref),
    )
    assert relationships.delete_calls == []
    assert objects.remove_membership_calls == []
    assert commits[0] == 1
    _assert_single_migrated_change(
        object_changes,
        object_id=source.id,
        source_version=1,
        target_version=2,
        occurred_at=occurred_at,
    )


@pytest.mark.parametrize("with_added_slot", [False, True])
def test_owner_side_component_slot_regression_preserves_existing_memberships_when_allowed(
    with_added_slot: bool,
) -> None:
    occurred_at = datetime(2026, 8, 11, 10, 0, tzinfo=UTC)
    (
        service,
        _datatypes,
        object_templates,
        objects,
        object_changes,
        _relationships,
        _relationship_definitions,
        commits,
    ) = _service(clock=lambda: occurred_at)
    child_template = _template(name="child")
    owner = _template(name="owner")
    extra = _template(name="extra")
    _store_template_versions(
        object_templates,
        child_template,
        (_version(child_template.id, version=1),),
    )
    _store_template_versions(object_templates, extra, (_version(extra.id, version=1),))
    owner_v1 = _version(
        owner.id,
        version=1,
        components=(_component("children", template_id=child_template.id),),
    )
    owner_v2_components = (_component("children", template_id=child_template.id),)
    if with_added_slot:
        owner_v2_components += (_component("extras", template_id=extra.id),)
    owner_v2 = _version(owner.id, version=2, components=owner_v2_components)
    _store_template_versions(object_templates, owner, (owner_v1, owner_v2))

    parent_object = _create_object(objects, template_id=owner.id, template_version=1)
    first_child = _create_object(objects, template_id=child_template.id, template_version=1)
    second_child = _create_object(objects, template_id=child_template.id, template_version=1)
    first_membership = _membership(parent_object.id, "children", first_child.id)
    second_membership = _membership(parent_object.id, "children", second_child.id)
    objects.add_membership(first_membership)
    objects.add_membership(second_membership)
    add_membership_calls_before = len(objects.add_membership_calls)

    result = service.migrate_objects(
        template_id=owner.id,
        source_version=1,
        target_version=2,
        property_values={},
    )

    migrated = objects.get(parent_object.id)
    assert migrated is not None
    assert migrated.template_version == 2
    assert result.migrated_count == 1
    assert objects.list_components(parent_object.id) == tuple(
        sorted(
            (first_membership, second_membership),
            key=lambda item: (item.slot_name, str(item.child_object_id)),
        )
    )
    assert len(objects.add_membership_calls) == add_membership_calls_before
    assert objects.remove_membership_calls == []
    assert commits[0] == 1
    _assert_single_migrated_change(
        object_changes,
        object_id=parent_object.id,
        source_version=1,
        target_version=2,
        occurred_at=occurred_at,
    )


@pytest.mark.parametrize(
    "target_components",
    [
        (),
        (_component("children", template_id=uuid4()),),
    ],
)
def test_owner_side_component_slot_blocking_changes_preserve_existing_memberships(
    target_components: tuple[ObjectTemplateComponent, ...],
) -> None:
    (
        service,
        _datatypes,
        object_templates,
        objects,
        object_changes,
        _relationships,
        _relationship_definitions,
        commits,
    ) = _service()
    child_template = _template(name="child")
    owner = _template(name="owner")
    _store_template_versions(
        object_templates,
        child_template,
        (_version(child_template.id, version=1),),
    )
    owner_v1 = _version(
        owner.id,
        version=1,
        components=(_component("children", template_id=child_template.id),),
    )
    owner_v2 = _version(owner.id, version=2, components=target_components)
    _store_template_versions(object_templates, owner, (owner_v1, owner_v2))

    parent_object = _create_object(objects, template_id=owner.id, template_version=1)
    child_object = _create_object(objects, template_id=child_template.id, template_version=1)
    membership = _membership(parent_object.id, "children", child_object.id)
    objects.add_membership(membership)

    with pytest.raises(ObjectMigrationBlocked):
        service.migrate_objects(
            template_id=owner.id,
            source_version=1,
            target_version=2,
            property_values={},
        )

    assert objects.get(parent_object.id) == parent_object
    assert objects.get_owner(child_object.id) == membership
    assert objects.replace_calls == []
    assert object_changes.list_by_object(parent_object.id) == ()
    assert objects.remove_membership_calls == []
    assert commits[0] == 0


def test_forbidden_pre_s0_parent_identity_drift_would_invalidate_membership_and_relationship_spaces(
) -> None:
    object_templates = InMemoryObjectTemplateRepository()
    parent_p = _template(name="parent_p")
    parent_q = _template(name="parent_q")
    child = _template(name="child")
    container = _template(name="container")
    network = _template(name="network")
    parent_p_v1 = _version(parent_p.id, version=1)
    parent_q_v1 = _version(parent_q.id, version=1)
    child_v1 = _version(
        child.id,
        version=1,
        parent=ObjectTemplateVersionRef(template_id=parent_p.id, version=1),
    )
    child_v2 = _version(
        child.id,
        version=2,
        parent=ObjectTemplateVersionRef(template_id=parent_q.id, version=1),
    )
    container_v1 = _version(
        container.id,
        version=1,
        components=(_component("children", template_id=parent_p.id),),
    )
    network_v1 = _version(network.id, version=1)
    _store_template_versions(object_templates, parent_p, (parent_p_v1,))
    _store_template_versions(object_templates, parent_q, (parent_q_v1,))
    _store_template_versions(object_templates, child, (child_v1, child_v2))
    _store_template_versions(object_templates, container, (container_v1,))
    _store_template_versions(object_templates, network, (network_v1,))
    definition = _definition(source_template_id=parent_p.id, target_template_id=network.id)

    assert _ancestry_identity_path(child_v1, object_templates) == (child.id, parent_p.id)
    assert _ancestry_identity_path(child_v2, object_templates) == (child.id, parent_q.id)
    assert ObjectTemplateInheritanceResolver().is_same_or_descendant_template(
        child_v1,
        required_template_id=parent_p.id,
        parent_lookup=lambda ref: _parent_lookup(object_templates, ref),
    )
    assert not ObjectTemplateInheritanceResolver().is_same_or_descendant_template(
        child_v2,
        required_template_id=parent_p.id,
        parent_lookup=lambda ref: _parent_lookup(object_templates, ref),
    )
    assert relationship_definition_applies(
        definition,
        source_version=child_v1,
        target_version=network_v1,
        parent_lookup=lambda ref: _parent_lookup(object_templates, ref),
    )
    assert not relationship_definition_applies(
        definition,
        source_version=child_v2,
        target_version=network_v1,
        parent_lookup=lambda ref: _parent_lookup(object_templates, ref),
    )
