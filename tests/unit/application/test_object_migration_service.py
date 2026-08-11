from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID, uuid4

import pytest

from netauto.application.object import ObjectApplicationService
from netauto.application.unit_of_work import ObjectUnitOfWork
from netauto.core.datatype import (
    Constraint,
    ConstraintName,
    DataType,
    DataTypeFactory,
    DataTypeVersion,
    DataTypeVersioningService,
)
from netauto.core.object import (
    ComponentMembership,
    MissingObjectMigrationPropertyValue,
    Object,
    ObjectMigrationBlocked,
    ObjectMigrationTargetVersionNotNewer,
    ObjectMigrationTargetVersionNotPublished,
    ObjectTemplateMigrationBlockingChangeKind,
    ObjectValidationFailed,
    UnexpectedObjectMigrationPropertyValue,
)
from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateComponent,
    ObjectTemplateProperty,
    ObjectTemplateVersion,
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


class TrackingObjectRepository(InMemoryObjectRepository):
    def __init__(self) -> None:
        super().__init__()
        self.list_by_template_version_calls: list[tuple[UUID, int]] = []
        self.replace_calls: list[Object] = []

    def list_by_template_version(
        self,
        template_id: UUID,
        template_version: int,
    ) -> tuple[Object, ...]:
        self.list_by_template_version_calls.append((template_id, template_version))
        return super().list_by_template_version(template_id, template_version)

    def replace(self, object_value: Object) -> None:
        self.replace_calls.append(object_value)
        super().replace(object_value)


class FakeUnitOfWork(ObjectUnitOfWork):
    def __init__(
        self,
        datatypes: InMemoryDataTypeRepository,
        object_templates: InMemoryObjectTemplateRepository,
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
    def object_templates(self) -> InMemoryObjectTemplateRepository:
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
    InMemoryObjectTemplateRepository,
    TrackingObjectRepository,
    InMemoryRelationshipRepository,
    list[int],
]:
    datatypes = InMemoryDataTypeRepository()
    object_templates = InMemoryObjectTemplateRepository()
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
        ObjectApplicationService(factory),
        datatypes,
        object_templates,
        objects,
        relationships,
        commit_counter,
    )


def _datatype(
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
    return datatype, DataTypeVersioningService().publish(draft)


def _store_datatype_versions(
    repo: InMemoryDataTypeRepository,
    datatype: DataType,
    versions: tuple[DataTypeVersion, ...],
) -> None:
    repo.add(datatype)
    for version in versions:
        repo.add_version(version)


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


def _template(
    *,
    namespace: str = "network",
    name: str = "device",
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


def _store_template_versions(
    repo: InMemoryObjectTemplateRepository,
    template: ObjectTemplate,
    versions: tuple[ObjectTemplateVersion, ...],
) -> None:
    repo.add(template)
    for version in versions:
        repo.add_version(version)


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


def test_analyze_optional_property_addition_is_automatic() -> None:
    service, datatypes, object_templates, _objects, _relationships, commits = _service()
    hostname, hostname_v1 = _datatype(name="hostname")
    serial, serial_v1 = _datatype(name="serial")
    _store_datatype_versions(datatypes, hostname, (hostname_v1,))
    _store_datatype_versions(datatypes, serial, (serial_v1,))

    template = _template(name="device")
    v1 = _version(
        template.id,
        version=1,
        properties=(
            _property("hostname", datatype_id=hostname.id, datatype_version=1, required=True),
        ),
    )
    v2 = _version(
        template.id,
        version=2,
        properties=(
            _property("hostname", datatype_id=hostname.id, datatype_version=1, required=True),
            _property("serialnumber", datatype_id=serial.id, datatype_version=1, required=False),
        ),
    )
    _store_template_versions(object_templates, template, (v1, v2))

    analysis = service.analyze_object_migration(
        template_id=template.id,
        source_version=1,
        target_version=2,
    )

    assert analysis.automatic is True
    assert [
        (property_value.name, property_value.required)
        for property_value in analysis.added_properties
    ] == [("serialnumber", False)]
    assert analysis.added_components == ()
    assert analysis.blocking_changes == ()
    assert commits[0] == 0


def test_analyze_detects_effective_inherited_addition() -> None:
    service, datatypes, object_templates, _objects, _relationships, _commits = _service()
    hostname, hostname_v1 = _datatype(name="hostname")
    serial, serial_v1 = _datatype(name="serial")
    _store_datatype_versions(datatypes, hostname, (hostname_v1,))
    _store_datatype_versions(datatypes, serial, (serial_v1,))

    base = _template(name="base_device")
    base_v1 = _version(
        base.id,
        version=1,
        properties=(
            _property("hostname", datatype_id=hostname.id, datatype_version=1, required=True),
        ),
    )
    base_v2 = _version(
        base.id,
        version=2,
        properties=(
            _property("hostname", datatype_id=hostname.id, datatype_version=1, required=True),
            _property("serialnumber", datatype_id=serial.id, datatype_version=1, required=True),
        ),
    )
    _store_template_versions(object_templates, base, (base_v1, base_v2))

    child = _template(name="network_device")
    child_v1 = _version(
        child.id,
        version=1,
        parent=ObjectTemplateVersionRef(template_id=base.id, version=1),
    )
    child_v2 = _version(
        child.id,
        version=2,
        parent=ObjectTemplateVersionRef(template_id=base.id, version=2),
    )
    _store_template_versions(object_templates, child, (child_v1, child_v2))

    analysis = service.analyze_object_migration(
        template_id=child.id,
        source_version=1,
        target_version=2,
    )

    assert analysis.automatic is True
    assert [property_value.name for property_value in analysis.added_properties] == [
        "serialnumber"
    ]
    assert analysis.added_properties[0].required is True


def test_analyze_added_component_is_automatic() -> None:
    service, _datatypes, object_templates, _objects, _relationships, _commits = _service()
    interface = _template(name="interface")
    power_supply = _template(name="power_supply")
    _store_template_versions(object_templates, interface, (_version(interface.id, version=1),))
    _store_template_versions(
        object_templates,
        power_supply,
        (_version(power_supply.id, version=1),),
    )

    template = _template(name="device")
    v1 = _version(
        template.id,
        version=1,
        components=(_component("interfaces", template_id=interface.id),),
    )
    v2 = _version(
        template.id,
        version=2,
        components=(
            _component("interfaces", template_id=interface.id),
            _component("power_supplies", template_id=power_supply.id),
        ),
    )
    _store_template_versions(object_templates, template, (v1, v2))

    analysis = service.analyze_object_migration(
        template_id=template.id,
        source_version=1,
        target_version=2,
    )

    assert analysis.automatic is True
    assert [component.name for component in analysis.added_components] == ["power_supplies"]
    assert analysis.added_components[0].template_id == power_supply.id


@pytest.mark.parametrize(
    ("builder", "expected_kind"),
    [
        ("property_removed", ObjectTemplateMigrationBlockingChangeKind.PROPERTY_REMOVED),
        ("property_changed", ObjectTemplateMigrationBlockingChangeKind.PROPERTY_CHANGED),
        ("component_removed", ObjectTemplateMigrationBlockingChangeKind.COMPONENT_REMOVED),
        ("component_changed", ObjectTemplateMigrationBlockingChangeKind.COMPONENT_CHANGED),
    ],
)
def test_analyze_detects_blocking_changes(
    builder: str,
    expected_kind: ObjectTemplateMigrationBlockingChangeKind,
) -> None:
    service, datatypes, object_templates, _objects, _relationships, _commits = _service()
    hostname, hostname_v1 = _datatype(name="hostname")
    serial, serial_v1 = _datatype(name="serial")
    interface = _template(name="interface")
    module = _template(name="module")
    _store_datatype_versions(datatypes, hostname, (hostname_v1,))
    _store_datatype_versions(datatypes, serial, (serial_v1,))
    _store_template_versions(object_templates, interface, (_version(interface.id, version=1),))
    _store_template_versions(object_templates, module, (_version(module.id, version=1),))

    template = _template(name="device")
    v1 = _version(
        template.id,
        version=1,
        properties=(
            _property("hostname", datatype_id=hostname.id, datatype_version=1, required=True),
        ),
        components=(_component("interfaces", template_id=interface.id),),
    )
    if builder == "property_removed":
        v2 = _version(template.id, version=2, properties=(), components=v1.components)
    elif builder == "property_changed":
        v2 = _version(
            template.id,
            version=2,
            properties=(
                _property("hostname", datatype_id=serial.id, datatype_version=1, required=True),
            ),
            components=v1.components,
        )
    elif builder == "component_removed":
        v2 = _version(template.id, version=2, properties=v1.properties, components=())
    else:
        v2 = _version(
            template.id,
            version=2,
            properties=v1.properties,
            components=(_component("interfaces", template_id=module.id),),
        )
    _store_template_versions(object_templates, template, (v1, v2))

    analysis = service.analyze_object_migration(
        template_id=template.id,
        source_version=1,
        target_version=2,
    )

    assert analysis.automatic is False
    assert analysis.blocking_changes[0].kind is expected_kind


def test_migrate_required_property_addition_applies_same_value_to_all_candidates() -> None:
    service, datatypes, object_templates, objects, _relationships, commits = _service()
    hostname, hostname_v1 = _datatype(name="hostname")
    serial, serial_v1 = _datatype(name="serial")
    _store_datatype_versions(datatypes, hostname, (hostname_v1,))
    _store_datatype_versions(datatypes, serial, (serial_v1,))

    template = _template(name="device")
    v1 = _version(
        template.id,
        version=1,
        properties=(
            _property("hostname", datatype_id=hostname.id, datatype_version=1, required=True),
        ),
    )
    v2 = _version(
        template.id,
        version=2,
        properties=(
            _property("hostname", datatype_id=hostname.id, datatype_version=1, required=True),
            _property("serialnumber", datatype_id=serial.id, datatype_version=1, required=True),
        ),
    )
    _store_template_versions(object_templates, template, (v1, v2))

    first = _create_object(
        objects,
        template_id=template.id,
        template_version=1,
        properties={"hostname": "a"},
    )
    second = _create_object(
        objects,
        template_id=template.id,
        template_version=1,
        properties={"hostname": "b"},
    )
    other = _create_object(
        objects,
        template_id=template.id,
        template_version=2,
        properties={"hostname": "c"},
    )

    result = service.migrate_objects(
        template_id=template.id,
        source_version=1,
        target_version=2,
        property_values={"serialnumber": "UNKNOWN"},
    )

    assert result.migrated_count == 2
    assert objects.get(first.id) == Object(
        id=first.id,
        template_id=template.id,
        template_version=2,
        properties={"hostname": "a", "serialnumber": "UNKNOWN"},
    )
    assert objects.get(second.id) == Object(
        id=second.id,
        template_id=template.id,
        template_version=2,
        properties={"hostname": "b", "serialnumber": "UNKNOWN"},
    )
    assert objects.get(other.id) == other
    assert commits[0] == 1
    assert len(objects.replace_calls) == 2
    assert objects.list_by_template_version_calls == [(template.id, 1)]


def test_migrate_optional_addition_and_added_component_preserve_memberships() -> None:
    service, datatypes, object_templates, objects, _relationships, commits = _service()
    hostname, hostname_v1 = _datatype(name="hostname")
    serial, serial_v1 = _datatype(name="serial")
    child_template = _template(name="bundle")
    power_supply = _template(name="power_supply")
    _store_datatype_versions(datatypes, hostname, (hostname_v1,))
    _store_datatype_versions(datatypes, serial, (serial_v1,))
    _store_template_versions(
        object_templates,
        child_template,
        (_version(child_template.id, version=1), _version(child_template.id, version=2)),
    )
    _store_template_versions(
        object_templates,
        power_supply,
        (_version(power_supply.id, version=1),),
    )

    template = _template(name="device")
    v1 = _version(
        template.id,
        version=1,
        properties=(
            _property("hostname", datatype_id=hostname.id, datatype_version=1, required=True),
        ),
        components=(_component("interfaces", template_id=child_template.id),),
    )
    v2 = _version(
        template.id,
        version=2,
        properties=(
            _property("hostname", datatype_id=hostname.id, datatype_version=1, required=True),
            _property("serialnumber", datatype_id=serial.id, datatype_version=1, required=False),
        ),
        components=(
            _component("interfaces", template_id=child_template.id),
            _component("power_supplies", template_id=power_supply.id),
        ),
    )
    _store_template_versions(object_templates, template, (v1, v2))

    parent = _create_object(
        objects,
        template_id=template.id,
        template_version=1,
        properties={"hostname": "router-01"},
    )
    child_v1 = _create_object(objects, template_id=child_template.id, template_version=1)
    child_v2 = _create_object(objects, template_id=child_template.id, template_version=2)
    objects.add_membership(
        ComponentMembership(
            parent_object_id=parent.id,
            slot_name="interfaces",
            child_object_id=child_v1.id,
        )
    )
    objects.add_membership(
        ComponentMembership(
            parent_object_id=parent.id,
            slot_name="interfaces",
            child_object_id=child_v2.id,
        )
    )

    result = service.migrate_objects(
        template_id=template.id,
        source_version=1,
        target_version=2,
        property_values={},
    )

    migrated = objects.get(parent.id)
    assert migrated is not None
    assert migrated.template_version == 2
    assert migrated.properties == {"hostname": "router-01"}
    assert objects.get_owner(child_v1.id) is not None
    assert objects.get_owner(child_v2.id) is not None
    assert result.migrated_count == 1
    assert commits[0] == 1


def test_required_property_addition_without_value_fails_before_mutation() -> None:
    service, datatypes, object_templates, objects, _relationships, commits = _service()
    hostname, hostname_v1 = _datatype(name="hostname")
    serial, serial_v1 = _datatype(name="serial")
    _store_datatype_versions(datatypes, hostname, (hostname_v1,))
    _store_datatype_versions(datatypes, serial, (serial_v1,))

    template = _template(name="device")
    v1 = _version(
        template.id,
        version=1,
        properties=(
            _property("hostname", datatype_id=hostname.id, datatype_version=1, required=True),
        ),
    )
    v2 = _version(
        template.id,
        version=2,
        properties=(
            _property("hostname", datatype_id=hostname.id, datatype_version=1, required=True),
            _property("serialnumber", datatype_id=serial.id, datatype_version=1, required=True),
        ),
    )
    _store_template_versions(object_templates, template, (v1, v2))
    source = _create_object(
        objects,
        template_id=template.id,
        template_version=1,
        properties={"hostname": "r1"},
    )

    with pytest.raises(MissingObjectMigrationPropertyValue):
        service.migrate_objects(
            template_id=template.id,
            source_version=1,
            target_version=2,
            property_values={},
        )

    assert objects.get(source.id) == source
    assert objects.replace_calls == []
    assert commits[0] == 0


def test_unexpected_migration_property_value_fails_before_mutation() -> None:
    service, datatypes, object_templates, objects, _relationships, commits = _service()
    hostname, hostname_v1 = _datatype(name="hostname")
    serial, serial_v1 = _datatype(name="serial")
    _store_datatype_versions(datatypes, hostname, (hostname_v1,))
    _store_datatype_versions(datatypes, serial, (serial_v1,))

    template = _template(name="device")
    v1 = _version(
        template.id,
        version=1,
        properties=(
            _property("hostname", datatype_id=hostname.id, datatype_version=1, required=True),
        ),
    )
    v2 = _version(
        template.id,
        version=2,
        properties=(
            _property("hostname", datatype_id=hostname.id, datatype_version=1, required=True),
            _property("serialnumber", datatype_id=serial.id, datatype_version=1, required=False),
        ),
    )
    _store_template_versions(object_templates, template, (v1, v2))
    source = _create_object(
        objects,
        template_id=template.id,
        template_version=1,
        properties={"hostname": "r1"},
    )

    with pytest.raises(UnexpectedObjectMigrationPropertyValue):
        service.migrate_objects(
            template_id=template.id,
            source_version=1,
            target_version=2,
            property_values={"hostname": "new"},
        )

    assert objects.get(source.id) == source
    assert objects.replace_calls == []
    assert commits[0] == 0


def test_invalid_supplied_value_fails_atomically_before_replace() -> None:
    service, datatypes, object_templates, objects, _relationships, commits = _service()
    hostname, hostname_v1 = _datatype(name="hostname")
    vlan, vlan_v1 = _datatype(
        name="vlan",
        base_type="core.integer",
        constraints=(Constraint(name=ConstraintName.MINIMUM, value=1),),
    )
    _store_datatype_versions(datatypes, hostname, (hostname_v1,))
    _store_datatype_versions(datatypes, vlan, (vlan_v1,))

    template = _template(name="device")
    v1 = _version(
        template.id,
        version=1,
        properties=(
            _property("hostname", datatype_id=hostname.id, datatype_version=1, required=True),
        ),
    )
    v2 = _version(
        template.id,
        version=2,
        properties=(
            _property("hostname", datatype_id=hostname.id, datatype_version=1, required=True),
            _property("vlan", datatype_id=vlan.id, datatype_version=1, required=True),
        ),
    )
    _store_template_versions(object_templates, template, (v1, v2))
    first = _create_object(
        objects,
        template_id=template.id,
        template_version=1,
        properties={"hostname": "a"},
    )
    second = _create_object(
        objects,
        template_id=template.id,
        template_version=1,
        properties={"hostname": "b"},
    )

    with pytest.raises(ObjectValidationFailed):
        service.migrate_objects(
            template_id=template.id,
            source_version=1,
            target_version=2,
            property_values={"vlan": "not-an-integer"},
        )

    assert objects.get(first.id) == first
    assert objects.get(second.id) == second
    assert objects.replace_calls == []
    assert commits[0] == 0


def test_blocked_migration_raises_and_does_not_mutate() -> None:
    service, datatypes, object_templates, objects, _relationships, commits = _service()
    hostname, hostname_v1 = _datatype(name="hostname")
    serial, serial_v1 = _datatype(name="serial")
    _store_datatype_versions(datatypes, hostname, (hostname_v1,))
    _store_datatype_versions(datatypes, serial, (serial_v1,))

    template = _template(name="device")
    v1 = _version(
        template.id,
        version=1,
        properties=(
            _property("hostname", datatype_id=hostname.id, datatype_version=1, required=True),
        ),
    )
    v2 = _version(
        template.id,
        version=2,
        properties=(
            _property("hostname", datatype_id=serial.id, datatype_version=1, required=True),
        ),
    )
    _store_template_versions(object_templates, template, (v1, v2))
    source = _create_object(
        objects,
        template_id=template.id,
        template_version=1,
        properties={"hostname": "r1"},
    )

    with pytest.raises(ObjectMigrationBlocked):
        service.migrate_objects(
            template_id=template.id,
            source_version=1,
            target_version=2,
            property_values={},
        )

    assert objects.get(source.id) == source
    assert objects.replace_calls == []
    assert commits[0] == 0


def test_target_version_must_be_published_for_analysis_and_execution() -> None:
    service, datatypes, object_templates, objects, _relationships, commits = _service()
    hostname, hostname_v1 = _datatype(name="hostname")
    _store_datatype_versions(datatypes, hostname, (hostname_v1,))

    template = _template(name="device")
    v1 = _version(
        template.id,
        version=1,
        properties=(
            _property("hostname", datatype_id=hostname.id, datatype_version=1, required=True),
        ),
    )
    v2_draft = _version(
        template.id,
        version=2,
        status=ObjectTemplateVersionStatus.DRAFT,
        properties=v1.properties,
    )
    _store_template_versions(object_templates, template, (v1, v2_draft))
    _create_object(
        objects,
        template_id=template.id,
        template_version=1,
        properties={"hostname": "r1"},
    )

    with pytest.raises(ObjectMigrationTargetVersionNotPublished):
        service.analyze_object_migration(
            template_id=template.id,
            source_version=1,
            target_version=2,
        )
    with pytest.raises(ObjectMigrationTargetVersionNotPublished):
        service.migrate_objects(
            template_id=template.id,
            source_version=1,
            target_version=2,
            property_values={},
        )

    assert commits[0] == 0


@pytest.mark.parametrize("target_version", [2, 1])
def test_forward_only_migration_rejects_non_newer_target_versions(
    target_version: int,
) -> None:
    service, datatypes, object_templates, objects, _relationships, commits = _service()
    hostname, hostname_v1 = _datatype(name="hostname")
    serial, serial_v1 = _datatype(name="serial")
    _store_datatype_versions(datatypes, hostname, (hostname_v1,))
    _store_datatype_versions(datatypes, serial, (serial_v1,))

    template = _template(name="device")
    v1 = _version(
        template.id,
        version=1,
        properties=(
            _property("hostname", datatype_id=hostname.id, datatype_version=1, required=True),
        ),
    )
    v2 = _version(
        template.id,
        version=2,
        properties=(
            _property("hostname", datatype_id=hostname.id, datatype_version=1, required=True),
            _property("serialnumber", datatype_id=serial.id, datatype_version=1, required=False),
        ),
    )
    _store_template_versions(object_templates, template, (v1, v2))
    _create_object(
        objects,
        template_id=template.id,
        template_version=1,
        properties={"hostname": "done"},
    )

    with pytest.raises(ObjectMigrationTargetVersionNotNewer):
        service.analyze_object_migration(
            template_id=template.id,
            source_version=2,
            target_version=target_version,
        )
    with pytest.raises(ObjectMigrationTargetVersionNotNewer):
        service.migrate_objects(
            template_id=template.id,
            source_version=2,
            target_version=target_version,
            property_values={},
        )

    assert objects.replace_calls == []
    assert commits[0] == 0


def test_zero_candidate_migration_with_required_added_property_is_noop_without_commit() -> None:
    service, datatypes, object_templates, objects, _relationships, commits = _service()
    hostname, hostname_v1 = _datatype(name="hostname")
    serial, serial_v1 = _datatype(name="serial")
    _store_datatype_versions(datatypes, hostname, (hostname_v1,))
    _store_datatype_versions(datatypes, serial, (serial_v1,))

    template = _template(name="device")
    v1 = _version(
        template.id,
        version=1,
        properties=(
            _property("hostname", datatype_id=hostname.id, datatype_version=1, required=True),
        ),
    )
    v2 = _version(
        template.id,
        version=2,
        properties=(
            _property("hostname", datatype_id=hostname.id, datatype_version=1, required=True),
            _property("serialnumber", datatype_id=serial.id, datatype_version=1, required=True),
        ),
    )
    _store_template_versions(object_templates, template, (v1, v2))
    _create_object(
        objects,
        template_id=template.id,
        template_version=2,
        properties={"hostname": "done"},
    )

    result = service.migrate_objects(
        template_id=template.id,
        source_version=1,
        target_version=2,
        property_values={},
    )

    assert result.migrated_count == 0
    assert objects.replace_calls == []
    assert commits[0] == 0


def test_zero_candidate_migration_still_rejects_unexpected_property_values() -> None:
    service, datatypes, object_templates, objects, _relationships, commits = _service()
    hostname, hostname_v1 = _datatype(name="hostname")
    serial, serial_v1 = _datatype(name="serial")
    _store_datatype_versions(datatypes, hostname, (hostname_v1,))
    _store_datatype_versions(datatypes, serial, (serial_v1,))

    template = _template(name="device")
    v1 = _version(
        template.id,
        version=1,
        properties=(
            _property("hostname", datatype_id=hostname.id, datatype_version=1, required=True),
        ),
    )
    v2 = _version(
        template.id,
        version=2,
        properties=(
            _property("hostname", datatype_id=hostname.id, datatype_version=1, required=True),
            _property("serialnumber", datatype_id=serial.id, datatype_version=1, required=True),
        ),
    )
    _store_template_versions(object_templates, template, (v1, v2))

    with pytest.raises(UnexpectedObjectMigrationPropertyValue):
        service.migrate_objects(
            template_id=template.id,
            source_version=1,
            target_version=2,
            property_values={"hostname": "new"},
        )

    assert objects.replace_calls == []
    assert commits[0] == 0
