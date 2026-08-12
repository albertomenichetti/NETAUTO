from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID, uuid4

import pytest

from netauto.application.object import ObjectApplicationService
from netauto.application.unit_of_work import ObjectUnitOfWork
from netauto.core.object import (
    ComponentMembership,
    ComponentMembershipAlreadyExists,
    ComponentMembershipNotFound,
    ComponentOwnershipCycle,
    InvalidComponentMembership,
    Object,
    ObjectComponentSlotNotFound,
    ObjectComponentTemplateIncompatible,
    ObjectNotFound,
)
from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateComponent,
    ObjectTemplateInheritanceCycle,
    ObjectTemplateParentNotFound,
    ObjectTemplateProperty,
    ObjectTemplateSelfInheritance,
    ObjectTemplateVersion,
    ObjectTemplateVersionNotFound,
    ObjectTemplateVersionRef,
    ObjectTemplateVersionStatus,
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


class TrackingObjectTemplateRepository(InMemoryObjectTemplateRepository):
    def __init__(self) -> None:
        super().__init__()
        self.get_version_calls: list[tuple[UUID, int]] = []

    def get_version(self, template_id: UUID, version: int) -> ObjectTemplateVersion | None:
        self.get_version_calls.append((template_id, version))
        return super().get_version(template_id, version)


class TrackingObjectRepository(InMemoryObjectRepository):
    def __init__(self) -> None:
        super().__init__()
        self.add_calls: list[Object] = []
        self.add_membership_calls: list[ComponentMembership] = []
        self.remove_membership_calls: list[UUID] = []

    def add(self, object_value: Object) -> None:
        self.add_calls.append(object_value)
        super().add(object_value)

    def add_membership(self, membership: ComponentMembership) -> None:
        self.add_membership_calls.append(membership)
        super().add_membership(membership)

    def remove_membership(self, child_object_id: UUID) -> None:
        self.remove_membership_calls.append(child_object_id)
        super().remove_membership(child_object_id)


class FakeUnitOfWork(ObjectUnitOfWork):
    def __init__(
        self,
        datatypes: InMemoryDataTypeRepository,
        object_templates: TrackingObjectTemplateRepository,
        objects: TrackingObjectRepository,
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
    def objects(self) -> TrackingObjectRepository:
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


def _service() -> tuple[
    ObjectApplicationService,
    InMemoryDataTypeRepository,
    TrackingObjectTemplateRepository,
    TrackingObjectRepository,
    InMemoryRelationshipRepository,
    list[int],
]:
    datatypes = InMemoryDataTypeRepository()
    object_templates = TrackingObjectTemplateRepository()
    objects = TrackingObjectRepository()
    object_changes = InMemoryObjectChangeRepository()
    relationships = InMemoryRelationshipRepository()
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


def _template(
    *,
    namespace: str = "network",
    name: str,
    abstract: bool = False,
) -> ObjectTemplate:
    return ObjectTemplate(
        id=uuid4(),
        namespace=namespace,
        name=name,
        description=f"{name} template",
        abstract=abstract,
    )


def _component(
    name: str,
    *,
    template_id: UUID,
    template_version: int,
) -> ObjectTemplateComponent:
    del template_version
    return ObjectTemplateComponent(
        name=name,
        template_id=template_id,
    )


def _version(
    template_id: UUID,
    *,
    version: int = 1,
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


def _store_template_versions(
    repo: InMemoryObjectTemplateRepository,
    template: ObjectTemplate,
    versions: tuple[ObjectTemplateVersion, ...],
) -> None:
    repo.add(template)
    for version in versions:
        draft = ObjectTemplateVersion(
            template_id=version.template_id,
            version=version.version,
            status=ObjectTemplateVersionStatus.DRAFT,
            parent=version.parent,
            properties=version.properties,
            components=version.components,
        )
        repo.add_version(draft)
        if version.status is ObjectTemplateVersionStatus.PUBLISHED:
            repo.replace_version(version)
        elif version.status is ObjectTemplateVersionStatus.DEPRECATED:
            repo.replace_version(
                ObjectTemplateVersion(
                    template_id=draft.template_id,
                    version=draft.version,
                    status=ObjectTemplateVersionStatus.PUBLISHED,
                    parent=draft.parent,
                    properties=draft.properties,
                    components=draft.components,
                )
            )
            repo.replace_version(version)


def _create_object(
    repo: InMemoryObjectRepository,
    *,
    template_id: UUID,
    template_version: int,
    object_id: UUID | None = None,
    properties: Mapping[str, object] | None = None,
) -> Object:
    object_value = Object(
        id=object_id or uuid4(),
        template_id=template_id,
        template_version=template_version,
        properties=properties or {},
    )
    repo.add(object_value)
    return object_value


def _membership(parent: UUID, slot_name: str, child: UUID) -> ComponentMembership:
    return ComponentMembership(
        parent_object_id=parent,
        slot_name=slot_name,
        child_object_id=child,
    )


def test_attach_persists_membership_without_mutating_objects() -> None:
    service, _datatypes, object_templates, objects, _relationships, commits = _service()
    slot_target = _template(name="interface")
    _store_template_versions(object_templates, slot_target, (_version(slot_target.id),))

    parent_template = _template(name="device")
    parent_version = _version(
        parent_template.id,
        components=(
            _component("interfaces", template_id=slot_target.id, template_version=1),
        ),
    )
    _store_template_versions(object_templates, parent_template, (parent_version,))

    parent = _create_object(
        objects,
        template_id=parent_template.id,
        template_version=1,
        properties={"hostname": "router-01"},
    )
    child = _create_object(
        objects,
        template_id=slot_target.id,
        template_version=1,
        properties={"name": "xe-0/0/0"},
    )
    parent_before = objects.get(parent.id)
    child_before = objects.get(child.id)
    add_count_before = len(objects.add_calls)

    membership = service.attach_component(
        parent_object_id=parent.id,
        slot_name="interfaces",
        child_object_id=child.id,
    )

    assert membership == _membership(parent.id, "interfaces", child.id)
    assert objects.get_owner(child.id) == membership
    assert objects.add_membership_calls == [membership]
    assert len(objects.add_calls) == add_count_before
    assert objects.get(parent.id) == parent_before
    assert objects.get(child.id) == child_before
    assert commits[0] == 1


def test_attach_allows_same_template_parent_and_child_when_objects_are_distinct() -> None:
    service, _datatypes, object_templates, objects, _relationships, commits = _service()
    node_template = _template(name="node")
    node_version = _version(
        node_template.id,
        components=(
            _component("children", template_id=node_template.id, template_version=1),
        ),
    )
    _store_template_versions(object_templates, node_template, (node_version,))
    parent = _create_object(objects, template_id=node_template.id, template_version=1)
    child = _create_object(objects, template_id=node_template.id, template_version=1)

    membership = service.attach_component(
        parent_object_id=parent.id,
        slot_name="children",
        child_object_id=child.id,
    )

    assert membership == _membership(parent.id, "children", child.id)
    assert objects.get_owner(child.id) == membership
    assert commits[0] == 1


def test_attach_requires_existing_parent_and_child() -> None:
    service, _datatypes, object_templates, objects, _relationships, commits = _service()
    slot_target = _template(name="interface")
    _store_template_versions(object_templates, slot_target, (_version(slot_target.id),))
    parent_template = _template(name="device")
    _store_template_versions(
        object_templates,
        parent_template,
        (
            _version(
                parent_template.id,
                components=(
                    _component("interfaces", template_id=slot_target.id, template_version=1),
                ),
            ),
        ),
    )
    parent = _create_object(objects, template_id=parent_template.id, template_version=1)
    child = _create_object(objects, template_id=slot_target.id, template_version=1)

    with pytest.raises(ObjectNotFound, match="Parent object"):
        service.attach_component(
            parent_object_id=uuid4(),
            slot_name="interfaces",
            child_object_id=child.id,
        )

    with pytest.raises(ObjectNotFound, match="Child object"):
        service.attach_component(
            parent_object_id=parent.id,
            slot_name="interfaces",
            child_object_id=uuid4(),
        )

    assert commits[0] == 0


@pytest.mark.parametrize(
    ("slot_name", "child_object_id"),
    (
        ("", uuid4()),
        (1, uuid4()),
        ("interfaces", None),
    ),
)
def test_attach_preserves_componentmembership_local_invariants(
    slot_name: object,
    child_object_id: UUID | None,
) -> None:
    service, _datatypes, object_templates, objects, _relationships, commits = _service()
    slot_target = _template(name="interface")
    _store_template_versions(object_templates, slot_target, (_version(slot_target.id),))
    parent_template = _template(name="device")
    _store_template_versions(
        object_templates,
        parent_template,
        (
            _version(
                parent_template.id,
                components=(
                    _component("interfaces", template_id=slot_target.id, template_version=1),
                ),
            ),
        ),
    )
    parent = _create_object(objects, template_id=parent_template.id, template_version=1)
    child = _create_object(objects, template_id=slot_target.id, template_version=1)

    with pytest.raises(InvalidComponentMembership):
        service.attach_component(
            parent_object_id=parent.id,
            slot_name=slot_name,  # type: ignore[arg-type]
            child_object_id=child.id if child_object_id is not None else parent.id,
        )

    assert commits[0] == 0


def test_attach_child_must_be_unowned_and_is_never_implicitly_moved() -> None:
    service, _datatypes, object_templates, objects, _relationships, commits = _service()
    slot_target = _template(name="interface")
    _store_template_versions(object_templates, slot_target, (_version(slot_target.id),))
    parent_template = _template(name="device")
    _store_template_versions(
        object_templates,
        parent_template,
        (
            _version(
                parent_template.id,
                components=(
                    _component("interfaces", template_id=slot_target.id, template_version=1),
                ),
            ),
        ),
    )
    parent_a = _create_object(objects, template_id=parent_template.id, template_version=1)
    parent_b = _create_object(objects, template_id=parent_template.id, template_version=1)
    child = _create_object(objects, template_id=slot_target.id, template_version=1)

    first = service.attach_component(
        parent_object_id=parent_a.id,
        slot_name="interfaces",
        child_object_id=child.id,
    )

    with pytest.raises(ComponentMembershipAlreadyExists):
        service.attach_component(
            parent_object_id=parent_a.id,
            slot_name="interfaces",
            child_object_id=child.id,
        )

    with pytest.raises(ComponentMembershipAlreadyExists):
        service.attach_component(
            parent_object_id=parent_b.id,
            slot_name="interfaces",
            child_object_id=child.id,
        )

    assert objects.get_owner(child.id) == first
    assert commits[0] == 1


def test_attach_allows_multiple_children_on_same_slot_and_different_slots() -> None:
    service, _datatypes, object_templates, objects, _relationships, commits = _service()
    interface = _template(name="interface")
    module = _template(name="module")
    _store_template_versions(object_templates, interface, (_version(interface.id),))
    _store_template_versions(object_templates, module, (_version(module.id),))
    parent_template = _template(name="device")
    _store_template_versions(
        object_templates,
        parent_template,
        (
            _version(
                parent_template.id,
                components=(
                    _component("interfaces", template_id=interface.id, template_version=1),
                    _component("modules", template_id=module.id, template_version=1),
                ),
            ),
        ),
    )
    parent = _create_object(objects, template_id=parent_template.id, template_version=1)
    first_child = _create_object(objects, template_id=interface.id, template_version=1)
    second_child = _create_object(objects, template_id=interface.id, template_version=1)
    third_child = _create_object(objects, template_id=module.id, template_version=1)

    first = service.attach_component(
        parent_object_id=parent.id,
        slot_name="interfaces",
        child_object_id=first_child.id,
    )
    second = service.attach_component(
        parent_object_id=parent.id,
        slot_name="interfaces",
        child_object_id=second_child.id,
    )
    third = service.attach_component(
        parent_object_id=parent.id,
        slot_name="modules",
        child_object_id=third_child.id,
    )

    assert service.list_components(parent.id) == tuple(
        sorted(
            (first, second, third),
            key=lambda membership: (membership.slot_name, str(membership.child_object_id)),
        )
    )
    assert commits[0] == 3


def test_attach_uses_local_and_inherited_component_slots() -> None:
    service, _datatypes, object_templates, objects, _relationships, commits = _service()
    interface = _template(name="interface", abstract=True)
    _store_template_versions(object_templates, interface, (_version(interface.id),))

    parent_base = _template(name="device")
    parent_base_version = _version(
        parent_base.id,
        components=(
            _component("interfaces", template_id=interface.id, template_version=1),
        ),
    )
    _store_template_versions(object_templates, parent_base, (parent_base_version,))

    parent_child = _template(name="router")
    parent_child_version = _version(
        parent_child.id,
        parent=ObjectTemplateVersionRef(template_id=parent_base.id, version=1),
        components=(
            _component("linecards", template_id=interface.id, template_version=1),
        ),
    )
    _store_template_versions(object_templates, parent_child, (parent_child_version,))

    owner = _create_object(objects, template_id=parent_child.id, template_version=1)
    first_child = _create_object(objects, template_id=interface.id, template_version=1)
    second_child = _create_object(objects, template_id=interface.id, template_version=1)

    inherited_membership = service.attach_component(
        parent_object_id=owner.id,
        slot_name="interfaces",
        child_object_id=first_child.id,
    )
    local_membership = service.attach_component(
        parent_object_id=owner.id,
        slot_name="linecards",
        child_object_id=second_child.id,
    )

    assert inherited_membership.slot_name == "interfaces"
    assert local_membership.slot_name == "linecards"
    assert commits[0] == 2


def test_attach_unknown_slot_raises_focused_exception() -> None:
    service, _datatypes, object_templates, objects, _relationships, commits = _service()
    interface = _template(name="interface")
    _store_template_versions(object_templates, interface, (_version(interface.id),))
    parent_template = _template(name="device")
    _store_template_versions(
        object_templates,
        parent_template,
        (
            _version(
                parent_template.id,
                components=(
                    _component("interfaces", template_id=interface.id, template_version=1),
                ),
            ),
        ),
    )
    parent = _create_object(objects, template_id=parent_template.id, template_version=1)
    child = _create_object(objects, template_id=interface.id, template_version=1)

    with pytest.raises(ObjectComponentSlotNotFound):
        service.attach_component(
            parent_object_id=parent.id,
            slot_name="banana",
            child_object_id=child.id,
        )

    assert objects.get_owner(child.id) is None
    assert commits[0] == 0


def test_attach_accepts_same_identity_versions_and_descendant_templates() -> None:
    service, _datatypes, object_templates, objects, _relationships, commits = _service()
    required = _template(name="network_interface")
    required_v1 = _version(required.id, version=1)
    required_v2 = _version(required.id, version=2)
    _store_template_versions(object_templates, required, (required_v1, required_v2))

    direct_descendant = _template(name="physical_interface")
    direct_descendant_v3 = _version(
        direct_descendant.id,
        version=3,
        parent=ObjectTemplateVersionRef(template_id=required.id, version=1),
    )
    _store_template_versions(object_templates, direct_descendant, (direct_descendant_v3,))

    multi_level_descendant = _template(name="optical_interface")
    multi_level_descendant_v4 = _version(
        multi_level_descendant.id,
        version=4,
        parent=ObjectTemplateVersionRef(template_id=direct_descendant.id, version=3),
    )
    _store_template_versions(
        object_templates,
        multi_level_descendant,
        (multi_level_descendant_v4,),
    )

    unrelated = _template(name="module")
    _store_template_versions(object_templates, unrelated, (_version(unrelated.id),))

    parent_template = _template(name="device")
    _store_template_versions(
        object_templates,
        parent_template,
        (
            _version(
                parent_template.id,
                components=(
                    _component("interfaces", template_id=required.id, template_version=1),
                ),
            ),
        ),
    )
    parent = _create_object(objects, template_id=parent_template.id, template_version=1)

    v1_child = _create_object(objects, template_id=required.id, template_version=1)
    v2_child = _create_object(objects, template_id=required.id, template_version=2)
    direct_descendant_child = _create_object(
        objects,
        template_id=direct_descendant.id,
        template_version=3,
    )
    multi_level_descendant_child = _create_object(
        objects,
        template_id=multi_level_descendant.id,
        template_version=4,
    )
    unrelated_child = _create_object(objects, template_id=unrelated.id, template_version=1)

    assert service.attach_component(
        parent_object_id=parent.id,
        slot_name="interfaces",
        child_object_id=v1_child.id,
    ) == _membership(parent.id, "interfaces", v1_child.id)
    service.detach_component(v1_child.id)

    assert service.attach_component(
        parent_object_id=parent.id,
        slot_name="interfaces",
        child_object_id=v2_child.id,
    ) == _membership(parent.id, "interfaces", v2_child.id)
    service.detach_component(v2_child.id)

    assert service.attach_component(
        parent_object_id=parent.id,
        slot_name="interfaces",
        child_object_id=direct_descendant_child.id,
    ) == _membership(parent.id, "interfaces", direct_descendant_child.id)
    service.detach_component(direct_descendant_child.id)

    assert service.attach_component(
        parent_object_id=parent.id,
        slot_name="interfaces",
        child_object_id=multi_level_descendant_child.id,
    ) == _membership(parent.id, "interfaces", multi_level_descendant_child.id)
    service.detach_component(multi_level_descendant_child.id)

    with pytest.raises(ObjectComponentTemplateIncompatible):
        service.attach_component(
            parent_object_id=parent.id,
            slot_name="interfaces",
            child_object_id=unrelated_child.id,
        )

    assert object_templates.get_version_calls.count((parent_template.id, 1)) >= 1
    assert (required.id, 1) in object_templates.get_version_calls
    assert (direct_descendant.id, 3) in object_templates.get_version_calls
    assert commits[0] == 8


def test_attach_missing_exact_parent_or_child_template_version_raises() -> None:
    service, _datatypes, object_templates, objects, _relationships, commits = _service()
    required = _template(name="interface")
    _store_template_versions(object_templates, required, (_version(required.id),))

    parent_template = _template(name="device")
    _store_template_versions(
        object_templates,
        parent_template,
        (
            _version(
                parent_template.id,
                version=2,
                components=(
                    _component("interfaces", template_id=required.id, template_version=1),
                ),
            ),
        ),
    )
    parent = _create_object(objects, template_id=parent_template.id, template_version=1)
    child = _create_object(objects, template_id=required.id, template_version=99)

    with pytest.raises(ObjectTemplateVersionNotFound):
        service.attach_component(
            parent_object_id=parent.id,
            slot_name="interfaces",
            child_object_id=child.id,
        )

    valid_parent = _create_object(objects, template_id=parent_template.id, template_version=2)
    missing_child_version = _create_object(objects, template_id=required.id, template_version=99)

    with pytest.raises(ObjectTemplateVersionNotFound):
        service.attach_component(
            parent_object_id=valid_parent.id,
            slot_name="interfaces",
            child_object_id=missing_child_version.id,
        )

    assert commits[0] == 0


def test_attach_preserves_parent_and_child_ancestry_failures() -> None:
    service, _datatypes, object_templates, objects, _relationships, commits = _service()
    required = _template(name="interface")
    _store_template_versions(object_templates, required, (_version(required.id),))

    broken_parent_template = _template(name="device")
    broken_parent_version = _version(
        broken_parent_template.id,
        parent=ObjectTemplateVersionRef(template_id=uuid4(), version=1),
        components=(
            _component("interfaces", template_id=required.id, template_version=1),
        ),
    )
    _store_template_versions(object_templates, broken_parent_template, (broken_parent_version,))
    parent = _create_object(objects, template_id=broken_parent_template.id, template_version=1)
    child = _create_object(objects, template_id=required.id, template_version=1)

    with pytest.raises(ObjectTemplateParentNotFound):
        service.attach_component(
            parent_object_id=parent.id,
            slot_name="interfaces",
            child_object_id=child.id,
        )

    self_parent_template = _template(name="selfish_device")
    self_parent_v1 = _version(
        self_parent_template.id,
        version=1,
        parent=ObjectTemplateVersionRef(template_id=self_parent_template.id, version=1),
    )
    _store_template_versions(object_templates, self_parent_template, (self_parent_v1,))
    self_parent = _create_object(objects, template_id=self_parent_template.id, template_version=1)
    exact_child = _create_object(objects, template_id=required.id, template_version=1)

    with pytest.raises(ObjectTemplateSelfInheritance):
        service.attach_component(
            parent_object_id=self_parent.id,
            slot_name="interfaces",
            child_object_id=exact_child.id,
        )

    cycle_parent_a = _template(name="cycle_parent_a")
    cycle_parent_b = _template(name="cycle_parent_b")
    cycle_parent_a_v1 = _version(
        cycle_parent_a.id,
        version=1,
        parent=ObjectTemplateVersionRef(template_id=cycle_parent_b.id, version=1),
    )
    cycle_parent_b_v1 = _version(
        cycle_parent_b.id,
        version=1,
        parent=ObjectTemplateVersionRef(template_id=cycle_parent_a.id, version=1),
    )
    _store_template_versions(object_templates, cycle_parent_a, (cycle_parent_a_v1,))
    _store_template_versions(object_templates, cycle_parent_b, (cycle_parent_b_v1,))
    cycle_parent = _create_object(objects, template_id=cycle_parent_a.id, template_version=1)
    cycle_child = _create_object(objects, template_id=required.id, template_version=1)

    with pytest.raises(ObjectTemplateInheritanceCycle):
        service.attach_component(
            parent_object_id=cycle_parent.id,
            slot_name="interfaces",
            child_object_id=cycle_child.id,
        )

    valid_parent_template = _template(name="valid_device")
    valid_parent_version = _version(
        valid_parent_template.id,
        components=(
            _component("interfaces", template_id=required.id, template_version=1),
        ),
    )
    _store_template_versions(object_templates, valid_parent_template, (valid_parent_version,))
    valid_parent = _create_object(objects, template_id=valid_parent_template.id, template_version=1)

    broken_child_template = _template(name="broken_child")
    broken_child_version = _version(
        broken_child_template.id,
        version=1,
        parent=ObjectTemplateVersionRef(template_id=uuid4(), version=1),
    )
    _store_template_versions(object_templates, broken_child_template, (broken_child_version,))
    broken_child = _create_object(objects, template_id=broken_child_template.id, template_version=1)

    with pytest.raises(ObjectTemplateParentNotFound):
        service.attach_component(
            parent_object_id=valid_parent.id,
            slot_name="interfaces",
            child_object_id=broken_child.id,
        )

    self_child_template = _template(name="selfish_child")
    self_child_v1 = _version(
        self_child_template.id,
        version=1,
        parent=ObjectTemplateVersionRef(template_id=self_child_template.id, version=1),
    )
    _store_template_versions(object_templates, self_child_template, (self_child_v1,))
    self_child = _create_object(objects, template_id=self_child_template.id, template_version=1)

    with pytest.raises(ObjectTemplateSelfInheritance):
        service.attach_component(
            parent_object_id=valid_parent.id,
            slot_name="interfaces",
            child_object_id=self_child.id,
        )

    cycle_child_a = _template(name="cycle_child_a")
    cycle_child_b = _template(name="cycle_child_b")
    cycle_child_a_v1 = _version(
        cycle_child_a.id,
        version=1,
        parent=ObjectTemplateVersionRef(template_id=cycle_child_b.id, version=1),
    )
    cycle_child_b_v1 = _version(
        cycle_child_b.id,
        version=1,
        parent=ObjectTemplateVersionRef(template_id=cycle_child_a.id, version=1),
    )
    _store_template_versions(object_templates, cycle_child_a, (cycle_child_a_v1,))
    _store_template_versions(object_templates, cycle_child_b, (cycle_child_b_v1,))
    cycle_child_object = _create_object(
        objects,
        template_id=cycle_child_a.id,
        template_version=1,
    )

    with pytest.raises(ObjectTemplateInheritanceCycle):
        service.attach_component(
            parent_object_id=valid_parent.id,
            slot_name="interfaces",
            child_object_id=cycle_child_object.id,
        )

    assert commits[0] == 0


def test_attach_ignores_current_template_status_for_existing_objects() -> None:
    service, _datatypes, object_templates, objects, _relationships, commits = _service()
    target = _template(name="interface", abstract=True)
    target_deprecated = _version(
        target.id,
        version=1,
        status=ObjectTemplateVersionStatus.DEPRECATED,
    )
    _store_template_versions(object_templates, target, (target_deprecated,))

    parent_template = _template(name="device")
    parent_deprecated = _version(
        parent_template.id,
        version=1,
        status=ObjectTemplateVersionStatus.DEPRECATED,
        components=(
            _component("interfaces", template_id=target.id, template_version=1),
        ),
    )
    _store_template_versions(object_templates, parent_template, (parent_deprecated,))

    parent = _create_object(objects, template_id=parent_template.id, template_version=1)
    child = _create_object(objects, template_id=target.id, template_version=1)

    membership = service.attach_component(
        parent_object_id=parent.id,
        slot_name="interfaces",
        child_object_id=child.id,
    )

    assert membership == _membership(parent.id, "interfaces", child.id)
    assert commits[0] == 1


def test_attach_prevents_owner_chain_cycles_without_graph_abstraction() -> None:
    service, _datatypes, object_templates, objects, _relationships, commits = _service()
    node_template = _template(name="node")
    node_version = _version(
        node_template.id,
        components=(
            _component("children", template_id=node_template.id, template_version=1),
        ),
    )
    _store_template_versions(object_templates, node_template, (node_version,))
    a = _create_object(objects, template_id=node_template.id, template_version=1)
    b = _create_object(objects, template_id=node_template.id, template_version=1)
    c = _create_object(objects, template_id=node_template.id, template_version=1)
    d = _create_object(objects, template_id=node_template.id, template_version=1)

    service.attach_component(parent_object_id=a.id, slot_name="children", child_object_id=b.id)
    service.attach_component(parent_object_id=b.id, slot_name="children", child_object_id=c.id)

    service.attach_component(parent_object_id=a.id, slot_name="children", child_object_id=d.id)
    service.detach_component(d.id)

    with pytest.raises(ComponentOwnershipCycle):
        service.attach_component(parent_object_id=b.id, slot_name="children", child_object_id=a.id)
    with pytest.raises(ComponentOwnershipCycle):
        service.attach_component(parent_object_id=c.id, slot_name="children", child_object_id=a.id)

    assert objects.get_owner(a.id) is None
    assert commits[0] == 4


def test_attach_detects_preexisting_corrupt_owner_cycle() -> None:
    service, _datatypes, object_templates, objects, _relationships, commits = _service()
    node_template = _template(name="node")
    node_version = _version(
        node_template.id,
        components=(
            _component("children", template_id=node_template.id, template_version=1),
        ),
    )
    _store_template_versions(object_templates, node_template, (node_version,))
    a = _create_object(objects, template_id=node_template.id, template_version=1)
    b = _create_object(objects, template_id=node_template.id, template_version=1)
    c = _create_object(objects, template_id=node_template.id, template_version=1)
    d = _create_object(objects, template_id=node_template.id, template_version=1)

    objects.add_membership(_membership(a.id, "children", b.id))
    objects.add_membership(_membership(b.id, "children", c.id))
    objects.add_membership(_membership(c.id, "children", a.id))

    with pytest.raises(ComponentOwnershipCycle):
        service.attach_component(parent_object_id=a.id, slot_name="children", child_object_id=d.id)

    assert objects.get_owner(d.id) is None
    assert commits[0] == 0


def test_attach_preserves_existing_child_subtree() -> None:
    service, _datatypes, object_templates, objects, _relationships, commits = _service()
    node_template = _template(name="node")
    node_version = _version(
        node_template.id,
        components=(
            _component("children", template_id=node_template.id, template_version=1),
        ),
    )
    _store_template_versions(object_templates, node_template, (node_version,))
    a = _create_object(objects, template_id=node_template.id, template_version=1)
    b = _create_object(objects, template_id=node_template.id, template_version=1)
    c = _create_object(objects, template_id=node_template.id, template_version=1)

    existing = service.attach_component(
        parent_object_id=b.id,
        slot_name="children",
        child_object_id=c.id,
    )
    service.detach_component(c.id)
    objects.add_membership(existing)

    attached = service.attach_component(
        parent_object_id=a.id,
        slot_name="children",
        child_object_id=b.id,
    )

    assert attached == _membership(a.id, "children", b.id)
    assert objects.get_owner(b.id) == attached
    assert objects.get_owner(c.id) == existing
    assert commits[0] == 3


def test_detach_removes_only_incoming_membership_and_preserves_subtree() -> None:
    service, _datatypes, object_templates, objects, _relationships, commits = _service()
    node_template = _template(name="node")
    node_version = _version(
        node_template.id,
        components=(
            _component("children", template_id=node_template.id, template_version=1),
        ),
    )
    _store_template_versions(object_templates, node_template, (node_version,))
    a = _create_object(
        objects,
        template_id=node_template.id,
        template_version=1,
        properties={"name": "a"},
    )
    b = _create_object(
        objects,
        template_id=node_template.id,
        template_version=1,
        properties={"name": "b"},
    )
    c = _create_object(
        objects,
        template_id=node_template.id,
        template_version=1,
        properties={"name": "c"},
    )
    a_before = objects.get(a.id)
    b_before = objects.get(b.id)
    c_before = objects.get(c.id)

    ab = service.attach_component(parent_object_id=a.id, slot_name="children", child_object_id=b.id)
    bc = service.attach_component(parent_object_id=b.id, slot_name="children", child_object_id=c.id)
    detached = service.detach_component(b.id)

    assert detached == ab
    assert objects.get_owner(b.id) is None
    assert objects.get_owner(c.id) == bc
    assert objects.get(a.id) == a_before
    assert objects.get(b.id) == b_before
    assert objects.get(c.id) == c_before
    assert commits[0] == 3


def test_detach_requires_existing_owned_child_and_commits_once() -> None:
    service, _datatypes, object_templates, objects, _relationships, commits = _service()
    node_template = _template(name="node")
    node_version = _version(
        node_template.id,
        components=(
            _component("children", template_id=node_template.id, template_version=1),
        ),
    )
    _store_template_versions(object_templates, node_template, (node_version,))
    parent = _create_object(objects, template_id=node_template.id, template_version=1)
    child = _create_object(objects, template_id=node_template.id, template_version=1)
    detached_target = _create_object(objects, template_id=node_template.id, template_version=1)
    service.attach_component(
        parent_object_id=parent.id,
        slot_name="children",
        child_object_id=child.id,
    )
    commits[0] = 0

    with pytest.raises(ObjectNotFound):
        service.detach_component(uuid4())
    with pytest.raises(ComponentMembershipNotFound):
        service.detach_component(detached_target.id)

    detached = service.detach_component(child.id)
    assert detached == _membership(parent.id, "children", child.id)
    assert objects.remove_membership_calls == [child.id]
    assert commits[0] == 1


def test_get_owner_and_list_components_are_read_only_queries() -> None:
    service, _datatypes, object_templates, objects, _relationships, commits = _service()
    node_template = _template(name="node")
    node_version = _version(
        node_template.id,
        components=(
            _component("children", template_id=node_template.id, template_version=1),
            _component("modules", template_id=node_template.id, template_version=1),
        ),
    )
    _store_template_versions(object_templates, node_template, (node_version,))
    parent = _create_object(objects, template_id=node_template.id, template_version=1)
    child_a = _create_object(objects, template_id=node_template.id, template_version=1)
    child_b = _create_object(objects, template_id=node_template.id, template_version=1)
    grandchild = _create_object(objects, template_id=node_template.id, template_version=1)

    membership_a = service.attach_component(
        parent_object_id=parent.id,
        slot_name="children",
        child_object_id=child_a.id,
    )
    membership_b = service.attach_component(
        parent_object_id=parent.id,
        slot_name="modules",
        child_object_id=child_b.id,
    )
    service.attach_component(
        parent_object_id=child_a.id,
        slot_name="children",
        child_object_id=grandchild.id,
    )
    commits[0] = 0

    assert service.get_owner(child_a.id) == membership_a
    assert service.get_owner(parent.id) is None
    with pytest.raises(ObjectNotFound):
        service.get_owner(uuid4())

    assert service.list_components(parent.id) == (membership_a, membership_b)
    assert service.list_components(parent.id, slot_name="children") == (membership_a,)
    assert service.list_components(parent.id, slot_name="banana") == ()
    with pytest.raises(ObjectNotFound):
        service.list_components(uuid4())

    assert commits[0] == 0
