from __future__ import annotations

from collections.abc import Callable, Collection, Mapping
from datetime import UTC, datetime
from typing import cast
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
    DataTypeVersionStatus,
)
from netauto.core.object import (
    ComponentMembership,
    ComponentOwnershipCycle,
    MissingObjectMigrationPropertyValue,
    Object,
    ObjectChange,
    ObjectChangeKind,
    ObjectNotFound,
    ObjectTemplateVersionNotPublished,
    ObjectValidationFailed,
)
from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateComponent,
    ObjectTemplateProperty,
    ObjectTemplateVersion,
    ObjectTemplateVersionRef,
    ObjectTemplateVersionStatus,
)
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


class TrackingObjectRepository(InMemoryObjectRepository):
    def __init__(self) -> None:
        super().__init__()
        self.add_calls: list[Object] = []
        self.replace_calls: list[Object] = []
        self.delete_calls: list[UUID] = []

    def add(self, object_value: Object) -> None:
        self.add_calls.append(object_value)
        super().add(object_value)

    def replace(self, object_value: Object) -> None:
        self.replace_calls.append(object_value)
        super().replace(object_value)

    def delete(self, object_id: UUID) -> None:
        self.delete_calls.append(object_id)
        super().delete(object_id)


class TrackingObjectChangeRepository(InMemoryObjectChangeRepository):
    def __init__(self) -> None:
        super().__init__()
        self.add_calls: list[ObjectChange] = []

    def add(self, change: ObjectChange) -> None:
        self.add_calls.append(change)
        super().add(change)


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


class RecordingObjectRepository(TrackingObjectRepository):
    def __init__(self) -> None:
        super().__init__()
        self.discovery_log: list[UUID] = []
        self.first_delete_discovery_count: int | None = None

    def list_components(
        self,
        parent_object_id: UUID,
        slot_name: str | None = None,
    ) -> tuple[ComponentMembership, ...]:
        self.discovery_log.append(parent_object_id)
        return super().list_components(parent_object_id, slot_name=slot_name)

    def delete(self, object_id: UUID) -> None:
        if self.first_delete_discovery_count is None:
            self.first_delete_discovery_count = len(self.discovery_log)
        super().delete(object_id)


class RecordingObjectChangeRepository(TrackingObjectChangeRepository):
    def __init__(self, object_repo: RecordingObjectRepository) -> None:
        super().__init__()
        self._object_repo = object_repo
        self.first_add_discovery_count: int | None = None

    def add(self, change: ObjectChange) -> None:
        if self.first_add_discovery_count is None:
            self.first_add_discovery_count = len(self._object_repo.discovery_log)
        super().add(change)


class RecordingRelationshipRepository(TrackingRelationshipRepository):
    def __init__(self, object_repo: RecordingObjectRepository) -> None:
        super().__init__()
        self._object_repo = object_repo
        self.first_delete_discovery_count: int | None = None

    def delete(self, relationship_id: UUID) -> None:
        if self.first_delete_discovery_count is None:
            self.first_delete_discovery_count = len(self._object_repo.discovery_log)
        super().delete(relationship_id)


class CycleObjectRepository(TrackingObjectRepository):
    def __init__(
        self,
        memberships_by_parent: dict[UUID, tuple[ComponentMembership, ...]],
    ) -> None:
        super().__init__()
        self._memberships_by_parent = memberships_by_parent

    def list_components(
        self,
        parent_object_id: UUID,
        slot_name: str | None = None,
    ) -> tuple[ComponentMembership, ...]:
        memberships = self._memberships_by_parent.get(parent_object_id, ())
        if slot_name is None:
            return memberships
        return tuple(
            membership for membership in memberships if membership.slot_name == slot_name
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
        self._commits[0] += 1


def _service(
    *,
    clock: Callable[[], datetime] | None = None,
    datatypes: InMemoryDataTypeRepository | None = None,
    object_templates: InMemoryObjectTemplateRepository | None = None,
    objects: InMemoryObjectRepository | None = None,
    object_changes: InMemoryObjectChangeRepository | None = None,
    relationships: InMemoryRelationshipRepository | None = None,
) -> tuple[
    ObjectApplicationService,
    InMemoryDataTypeRepository,
    InMemoryObjectTemplateRepository,
    InMemoryObjectRepository,
    InMemoryObjectChangeRepository,
    InMemoryRelationshipRepository,
    list[int],
]:
    datatypes = datatypes or InMemoryDataTypeRepository()
    object_templates = object_templates or InMemoryObjectTemplateRepository()
    objects = objects or TrackingObjectRepository()
    object_changes = object_changes or TrackingObjectChangeRepository()
    relationships = relationships or TrackingRelationshipRepository()
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
        commits,
    )


def _datatype(
    *,
    namespace: str = "network",
    name: str = "hostname",
    base_type: str = "core.string",
    constraints: tuple[Constraint, ...] = (),
    publish: bool = True,
) -> tuple[DataType, DataTypeVersion]:
    datatype, version = DataTypeFactory().create(
        namespace=namespace,
        name=name,
        description=f"{name} datatype",
        base_type=base_type,
        constraints=constraints,
    )
    if publish:
        version = DataTypeVersioningService().publish(version)
    return datatype, version


def _store_datatypes(
    repo: InMemoryDataTypeRepository,
    datatype_versions: tuple[tuple[DataType, DataTypeVersion], ...],
) -> None:
    for datatype, version in datatype_versions:
        repo.add(datatype)
        draft = DataTypeVersion(
            datatype_id=version.datatype_id,
            version=version.version,
            status=DataTypeVersionStatus.DRAFT,
            base_type=version.base_type,
            constraints=version.constraints,
        )
        repo.add_version(draft)
        if version.status is DataTypeVersionStatus.PUBLISHED:
            repo.replace_version(version)
        elif version.status is DataTypeVersionStatus.DEPRECATED:
            repo.replace_version(DataTypeVersioningService().publish(draft))
            repo.replace_version(version)


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


def _template(*, name: str = "device", abstract: bool = False) -> ObjectTemplate:
    return ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name=name,
        description=f"{name} template",
        abstract=abstract,
    )


def _template_version(
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
        repo.add_version(version)


def _object(
    *,
    template_id: UUID,
    template_version: int = 1,
    object_id: UUID | None = None,
    properties: Mapping[str, object] | None = None,
) -> Object:
    return Object(
        id=object_id or uuid4(),
        template_id=template_id,
        template_version=template_version,
        properties=properties or {},
    )


def _store_object(repo: InMemoryObjectRepository, object_value: Object) -> Object:
    repo.add(object_value)
    return object_value


def _membership(parent: UUID, child: UUID, *, slot_name: str = "children") -> ComponentMembership:
    return ComponentMembership(
        parent_object_id=parent,
        slot_name=slot_name,
        child_object_id=child,
    )


def _relationship(
    repo: InMemoryRelationshipRepository,
    *,
    source_object_id: UUID,
    target_object_id: UUID,
) -> Relationship:
    relationship = Relationship(
        id=uuid4(),
        relationship_definition_id=uuid4(),
        source_object_id=source_object_id,
        target_object_id=target_object_id,
    )
    repo.add(relationship)
    return relationship


def test_create_appends_created_history_and_commits_once() -> None:
    occurred_at = datetime(2026, 8, 11, 12, 0, tzinfo=UTC)
    (
        service,
        datatypes,
        object_templates,
        objects,
        object_changes,
        _relationships,
        commits,
    ) = _service(clock=lambda: occurred_at)
    hostname = _datatype(name="hostname")
    _store_datatypes(datatypes, (hostname,))
    template = _template()
    _store_template_versions(
        object_templates,
        template,
        (
            _template_version(
                template.id,
                properties=(
                    _property(
                        "hostname",
                        datatype_id=hostname[0].id,
                        datatype_version=hostname[1].version,
                        required=True,
                    ),
                ),
            ),
        ),
    )

    created = service.create_object(
        template_id=template.id,
        template_version=1,
        properties={"hostname": "router-01"},
    )

    history = object_changes.list_by_object(created.id)
    assert commits[0] == 1
    assert objects.get(created.id) == created
    assert len(history) == 1
    assert history[0].kind is ObjectChangeKind.CREATED
    assert history[0].before is None
    assert history[0].after is not None
    assert history[0].occurred_at == occurred_at
    assert history[0].after.template_id == created.template_id
    assert history[0].after.template_version == created.template_version
    assert history[0].after.properties == created.properties


def test_create_without_template_version_uses_highest_published_in_object_and_history() -> None:
    occurred_at = datetime(2026, 8, 11, 12, 5, tzinfo=UTC)
    (
        service,
        datatypes,
        object_templates,
        objects,
        object_changes,
        _relationships,
        commits,
    ) = _service(clock=lambda: occurred_at)
    hostname = _datatype(name="hostname")
    _store_datatypes(datatypes, (hostname,))
    template = _template()
    _store_template_versions(
        object_templates,
        template,
        (
            _template_version(
                template.id,
                version=1,
                status=ObjectTemplateVersionStatus.PUBLISHED,
                properties=(
                    _property(
                        "hostname",
                        datatype_id=hostname[0].id,
                        datatype_version=hostname[1].version,
                        required=True,
                    ),
                ),
            ),
            _template_version(
                template.id,
                version=2,
                status=ObjectTemplateVersionStatus.PUBLISHED,
                properties=(
                    _property(
                        "hostname",
                        datatype_id=hostname[0].id,
                        datatype_version=hostname[1].version,
                        required=True,
                    ),
                ),
            ),
            _template_version(
                template.id,
                version=3,
                status=ObjectTemplateVersionStatus.DRAFT,
                properties=(
                    _property(
                        "hostname",
                        datatype_id=hostname[0].id,
                        datatype_version=hostname[1].version,
                        required=True,
                    ),
                ),
            ),
        ),
    )

    created = service.create_object(
        template_id=template.id,
        template_version=None,
        properties={"hostname": "router-01"},
    )

    history = object_changes.list_by_object(created.id)
    assert commits[0] == 1
    assert created.template_version == 2
    assert objects.get(created.id) == created
    assert len(history) == 1
    assert history[0].kind is ObjectChangeKind.CREATED
    assert history[0].after is not None
    assert history[0].after.template_version == 2


def test_create_without_template_version_without_published_fails_without_history() -> None:
    (
        service,
        datatypes,
        object_templates,
        objects,
        object_changes,
        _relationships,
        commits,
    ) = _service()
    hostname = _datatype(name="hostname")
    _store_datatypes(datatypes, (hostname,))
    template = _template()
    _store_template_versions(
        object_templates,
        template,
        (
            _template_version(
                template.id,
                version=1,
                status=ObjectTemplateVersionStatus.DEPRECATED,
                properties=(
                    _property(
                        "hostname",
                        datatype_id=hostname[0].id,
                        datatype_version=hostname[1].version,
                        required=True,
                    ),
                ),
            ),
            _template_version(
                template.id,
                version=2,
                status=ObjectTemplateVersionStatus.DRAFT,
                properties=(
                    _property(
                        "hostname",
                        datatype_id=hostname[0].id,
                        datatype_version=hostname[1].version,
                        required=True,
                    ),
                ),
            ),
        ),
    )

    with pytest.raises(ObjectTemplateVersionNotPublished):
        service.create_object(
            template_id=template.id,
            template_version=None,
            properties={"hostname": "router-01"},
        )

    tracked_changes = cast(TrackingObjectChangeRepository, object_changes)
    assert objects.list() == ()
    assert tracked_changes.add_calls == []
    assert commits[0] == 0


def test_create_validation_failure_produces_no_history_and_no_commit() -> None:
    (
        service,
        datatypes,
        object_templates,
        _objects,
        object_changes,
        _relationships,
        commits,
    ) = _service()
    hostname = _datatype(name="hostname")
    _store_datatypes(datatypes, (hostname,))
    template = _template()
    _store_template_versions(
        object_templates,
        template,
        (
            _template_version(
                template.id,
                properties=(
                    _property(
                        "hostname",
                        datatype_id=hostname[0].id,
                        datatype_version=hostname[1].version,
                        required=True,
                    ),
                ),
            ),
        ),
    )

    with pytest.raises(ObjectValidationFailed):
        service.create_object(template_id=template.id, template_version=1, properties={})

    tracked_changes = cast(TrackingObjectChangeRepository, object_changes)
    assert tracked_changes.add_calls == []
    assert commits[0] == 0


def test_update_property_change_appends_updated_history() -> None:
    occurred_at = datetime(2026, 8, 11, 13, 0, tzinfo=UTC)
    (
        service,
        datatypes,
        object_templates,
        objects,
        object_changes,
        _relationships,
        commits,
    ) = _service(clock=lambda: occurred_at)
    hostname = _datatype(name="hostname")
    _store_datatypes(datatypes, (hostname,))
    template = _template()
    _store_template_versions(
        object_templates,
        template,
        (
            _template_version(
                template.id,
                properties=(
                    _property(
                        "hostname",
                        datatype_id=hostname[0].id,
                        datatype_version=hostname[1].version,
                        required=True,
                    ),
                ),
            ),
        ),
    )
    current = _store_object(
        objects,
        _object(template_id=template.id, properties={"hostname": "router-01"}),
    )

    updated = service.update_object(
        object_id=current.id,
        properties={"hostname": "router-02"},
        remove_properties=(),
    )

    history = object_changes.list_by_object(current.id)
    assert commits[0] == 1
    assert updated.properties["hostname"] == "router-02"
    assert len(history) == 1
    assert history[0].kind is ObjectChangeKind.UPDATED
    assert history[0].occurred_at == occurred_at
    assert history[0].before is not None
    assert history[0].after is not None
    assert history[0].before.properties == {"hostname": "router-01"}
    assert history[0].after.properties == {"hostname": "router-02"}


def test_update_remove_property_appends_correct_before_after() -> None:
    occurred_at = datetime(2026, 8, 11, 13, 30, tzinfo=UTC)
    (
        service,
        datatypes,
        object_templates,
        objects,
        object_changes,
        _relationships,
        commits,
    ) = _service(clock=lambda: occurred_at)
    hostname = _datatype(name="hostname")
    serial = _datatype(name="serial")
    _store_datatypes(datatypes, (hostname, serial))
    template = _template()
    _store_template_versions(
        object_templates,
        template,
        (
            _template_version(
                template.id,
                properties=(
                    _property(
                        "hostname",
                        datatype_id=hostname[0].id,
                        datatype_version=hostname[1].version,
                        required=True,
                    ),
                    _property(
                        "serial",
                        datatype_id=serial[0].id,
                        datatype_version=serial[1].version,
                        required=False,
                    ),
                ),
            ),
        ),
    )
    current = _store_object(
        objects,
        _object(
            template_id=template.id,
            properties={"hostname": "router-01", "serial": "ABC123"},
        ),
    )

    updated = service.update_object(
        object_id=current.id,
        properties={},
        remove_properties=("serial",),
    )

    history = object_changes.list_by_object(current.id)
    assert commits[0] == 1
    assert updated.properties == {"hostname": "router-01"}
    assert history[0].before is not None
    assert history[0].after is not None
    assert history[0].before.properties == {"hostname": "router-01", "serial": "ABC123"}
    assert history[0].after.properties == {"hostname": "router-01"}


@pytest.mark.parametrize(
    ("set_properties", "remove_properties"),
    [
        ({}, ()),
        ({"hostname": "router-01"}, ()),
        ({}, ("serial",)),
    ],
)
def test_update_semantic_noop_produces_no_history_and_no_commit(
    set_properties: dict[str, object],
    remove_properties: tuple[str, ...],
) -> None:
    (
        service,
        datatypes,
        object_templates,
        objects,
        object_changes,
        _relationships,
        commits,
    ) = _service()
    hostname = _datatype(name="hostname")
    serial = _datatype(name="serial")
    _store_datatypes(datatypes, (hostname, serial))
    template = _template()
    _store_template_versions(
        object_templates,
        template,
        (
            _template_version(
                template.id,
                properties=(
                    _property(
                        "hostname",
                        datatype_id=hostname[0].id,
                        datatype_version=hostname[1].version,
                        required=True,
                    ),
                    _property(
                        "serial",
                        datatype_id=serial[0].id,
                        datatype_version=serial[1].version,
                        required=False,
                    ),
                ),
            ),
        ),
    )
    current = _store_object(
        objects,
        _object(template_id=template.id, properties={"hostname": "router-01"}),
    )

    result = service.update_object(
        object_id=current.id,
        properties=set_properties,
        remove_properties=remove_properties,
    )

    tracked_objects = cast(TrackingObjectRepository, objects)
    assert result == current
    assert object_changes.list_by_object(current.id) == ()
    assert commits[0] == 0
    assert tracked_objects.replace_calls == []


def test_invalid_update_produces_no_history_and_no_commit() -> None:
    (
        service,
        datatypes,
        object_templates,
        objects,
        object_changes,
        _relationships,
        commits,
    ) = _service()
    hostname = _datatype(name="hostname")
    _store_datatypes(datatypes, (hostname,))
    template = _template()
    _store_template_versions(
        object_templates,
        template,
        (
            _template_version(
                template.id,
                properties=(
                    _property(
                        "hostname",
                        datatype_id=hostname[0].id,
                        datatype_version=hostname[1].version,
                        required=True,
                    ),
                ),
            ),
        ),
    )
    current = _store_object(
        objects,
        _object(template_id=template.id, properties={"hostname": "router-01"}),
    )

    with pytest.raises(ObjectValidationFailed):
        service.update_object(
            object_id=current.id,
            properties={},
            remove_properties=("hostname",),
        )

    tracked_objects = cast(TrackingObjectRepository, objects)
    assert object_changes.list_by_object(current.id) == ()
    assert commits[0] == 0
    assert tracked_objects.get(current.id) == current


def test_list_object_history_returns_empty_tuple_for_pre_audit_object() -> None:
    service, _datatypes, _templates, objects, _changes, _relationships, _commits = _service()
    current = _store_object(objects, _object(template_id=uuid4()))

    assert service.list_object_history(current.id) == ()


def test_list_object_history_raises_when_object_and_history_are_both_missing() -> None:
    service, _datatypes, _templates, _objects, _changes, _relationships, _commits = _service()

    with pytest.raises(ObjectNotFound):
        service.list_object_history(uuid4())


def test_migration_appends_one_event_per_object_with_shared_timestamp() -> None:
    occurred_at = datetime(2026, 8, 11, 14, 0, tzinfo=UTC)
    (
        service,
        datatypes,
        object_templates,
        objects,
        object_changes,
        _relationships,
        commits,
    ) = _service(clock=lambda: occurred_at)
    hostname = _datatype(name="hostname")
    serial = _datatype(name="serial")
    _store_datatypes(datatypes, (hostname, serial))
    template = _template()
    _store_template_versions(
        object_templates,
        template,
        (
            _template_version(
                template.id,
                version=1,
                properties=(
                    _property(
                        "hostname",
                        datatype_id=hostname[0].id,
                        datatype_version=hostname[1].version,
                        required=True,
                    ),
                ),
            ),
            _template_version(
                template.id,
                version=2,
                properties=(
                    _property(
                        "hostname",
                        datatype_id=hostname[0].id,
                        datatype_version=hostname[1].version,
                        required=True,
                    ),
                    _property(
                        "serial",
                        datatype_id=serial[0].id,
                        datatype_version=serial[1].version,
                        required=False,
                    ),
                ),
            ),
        ),
    )
    first = _store_object(
        objects,
        _object(template_id=template.id, template_version=1, properties={"hostname": "r1"}),
    )
    second = _store_object(
        objects,
        _object(template_id=template.id, template_version=1, properties={"hostname": "r2"}),
    )

    result = service.migrate_objects(
        template_id=template.id,
        source_version=1,
        target_version=2,
        property_values={},
    )

    first_history = object_changes.list_by_object(first.id)
    second_history = object_changes.list_by_object(second.id)
    assert result.migrated_count == 2
    assert commits[0] == 1
    assert len(first_history) == 1
    assert len(second_history) == 1
    assert first_history[0].kind is ObjectChangeKind.MIGRATED
    assert second_history[0].kind is ObjectChangeKind.MIGRATED
    assert first_history[0].occurred_at == occurred_at
    assert second_history[0].occurred_at == occurred_at
    assert first_history[0].before is not None
    assert first_history[0].after is not None
    assert first_history[0].before.template_version == 1
    assert first_history[0].after.template_version == 2
    assert second_history[0].before is not None
    assert second_history[0].after is not None
    assert second_history[0].before.template_version == 1
    assert second_history[0].after.template_version == 2


def test_migration_candidate_failure_produces_zero_history_zero_mutation_and_zero_commit() -> None:
    (
        service,
        datatypes,
        object_templates,
        objects,
        object_changes,
        _relationships,
        commits,
    ) = _service()
    hostname = _datatype(name="hostname")
    serial = _datatype(
        name="serial",
        constraints=(Constraint(name=ConstraintName.MIN_LENGTH, value=1),),
    )
    _store_datatypes(datatypes, (hostname, serial))
    template = _template()
    _store_template_versions(
        object_templates,
        template,
        (
            _template_version(
                template.id,
                version=1,
                properties=(
                    _property(
                        "hostname",
                        datatype_id=hostname[0].id,
                        datatype_version=hostname[1].version,
                        required=True,
                    ),
                ),
            ),
            _template_version(
                template.id,
                version=2,
                properties=(
                    _property(
                        "hostname",
                        datatype_id=hostname[0].id,
                        datatype_version=hostname[1].version,
                        required=True,
                    ),
                    _property(
                        "serial",
                        datatype_id=serial[0].id,
                        datatype_version=serial[1].version,
                        required=True,
                    ),
                ),
            ),
        ),
    )
    current = _store_object(
        objects,
        _object(template_id=template.id, template_version=1, properties={"hostname": "r1"}),
    )

    with pytest.raises(MissingObjectMigrationPropertyValue):
        service.migrate_objects(
            template_id=template.id,
            source_version=1,
            target_version=2,
            property_values={},
        )

    tracked_objects = cast(TrackingObjectRepository, objects)
    assert object_changes.list_by_object(current.id) == ()
    assert tracked_objects.replace_calls == []
    assert commits[0] == 0
    assert tracked_objects.get(current.id) == current


def test_migration_zero_candidates_is_noop_with_zero_history_and_zero_commit() -> None:
    (
        service,
        datatypes,
        object_templates,
        _objects,
        object_changes,
        _relationships,
        commits,
    ) = _service()
    hostname = _datatype(name="hostname")
    _store_datatypes(datatypes, (hostname,))
    template = _template()
    _store_template_versions(
        object_templates,
        template,
        (
            _template_version(
                template.id,
                version=1,
                properties=(
                    _property(
                        "hostname",
                        datatype_id=hostname[0].id,
                        datatype_version=hostname[1].version,
                        required=True,
                    ),
                ),
            ),
            _template_version(
                template.id,
                version=2,
                properties=(
                    _property(
                        "hostname",
                        datatype_id=hostname[0].id,
                        datatype_version=hostname[1].version,
                        required=True,
                    ),
                ),
            ),
        ),
    )

    result = service.migrate_objects(
        template_id=template.id,
        source_version=1,
        target_version=2,
        property_values={},
    )

    tracked_changes = cast(TrackingObjectChangeRepository, object_changes)
    assert result.migrated_count == 0
    assert tracked_changes.add_calls == []
    assert commits[0] == 0


def test_delete_single_object_appends_deleted_history_that_survives_object_deletion() -> None:
    occurred_at = datetime(2026, 8, 11, 15, 0, tzinfo=UTC)
    (
        service,
        _datatypes,
        _templates,
        objects,
        object_changes,
        relationships,
        commits,
    ) = _service(clock=lambda: occurred_at)
    target = _store_object(
        objects,
        _object(template_id=uuid4(), properties={"hostname": "router-01"}),
    )
    external = _store_object(objects, _object(template_id=uuid4()))
    _relationship(
        relationships,
        source_object_id=external.id,
        target_object_id=target.id,
    )

    service.delete_object(target.id)

    history = service.list_object_history(target.id)
    assert commits[0] == 1
    assert objects.get(target.id) is None
    assert len(history) == 1
    assert history[0].kind is ObjectChangeKind.DELETED
    assert history[0].occurred_at == occurred_at
    assert history[0].before is not None
    assert history[0].before.properties == {"hostname": "router-01"}
    assert history[0].after is None


def test_delete_subtree_appends_deleted_history_for_parent_and_descendants() -> None:
    occurred_at = datetime(2026, 8, 11, 15, 30, tzinfo=UTC)
    objects = TrackingObjectRepository()
    object_changes = TrackingObjectChangeRepository()
    relationships = TrackingRelationshipRepository()
    (
        service,
        _datatypes,
        _templates,
        objects,
        object_changes,
        relationships,
        commits,
    ) = _service(
        clock=lambda: occurred_at,
        objects=objects,
        object_changes=object_changes,
        relationships=relationships,
    )
    parent = _store_object(
        objects,
        _object(template_id=uuid4(), properties={"name": "parent"}),
    )
    child = _store_object(
        objects,
        _object(template_id=uuid4(), properties={"name": "child"}),
    )
    grandchild = _store_object(
        objects,
        _object(template_id=uuid4(), properties={"name": "grandchild"}),
    )
    objects.add_membership(_membership(parent.id, child.id))
    objects.add_membership(_membership(child.id, grandchild.id))

    service.delete_object(parent.id)

    parent_history = object_changes.list_by_object(parent.id)
    child_history = object_changes.list_by_object(child.id)
    grandchild_history = object_changes.list_by_object(grandchild.id)
    assert parent_history[0].before is not None
    assert child_history[0].before is not None
    assert grandchild_history[0].before is not None
    parent_before = parent_history[0].before
    child_before = child_history[0].before
    grandchild_before = grandchild_history[0].before
    assert commits[0] == 1
    assert {
        parent_before.properties["name"],
        child_before.properties["name"],
        grandchild_before.properties["name"],
    } == {
        "parent",
        "child",
        "grandchild",
    }
    assert all(
        history[0].kind is ObjectChangeKind.DELETED
        for history in (parent_history, child_history, grandchild_history)
    )
    assert all(
        history[0].occurred_at == occurred_at
        for history in (parent_history, child_history, grandchild_history)
    )


def test_delete_discovery_finishes_before_first_history_or_object_mutation() -> None:
    occurred_at = datetime(2026, 8, 11, 16, 0, tzinfo=UTC)
    objects = RecordingObjectRepository()
    relationships = RecordingRelationshipRepository(objects)
    object_changes = RecordingObjectChangeRepository(objects)
    (
        service,
        _datatypes,
        _templates,
        objects,
        object_changes,
        relationships,
        commits,
    ) = _service(
        clock=lambda: occurred_at,
        objects=objects,
        object_changes=object_changes,
        relationships=relationships,
    )
    parent = _store_object(objects, _object(template_id=uuid4()))
    child = _store_object(objects, _object(template_id=uuid4()))
    grandchild = _store_object(objects, _object(template_id=uuid4()))
    external = _store_object(objects, _object(template_id=uuid4()))
    objects.add_membership(_membership(parent.id, child.id))
    objects.add_membership(_membership(child.id, grandchild.id))
    _relationship(
        relationships,
        source_object_id=external.id,
        target_object_id=parent.id,
    )

    service.delete_object(parent.id)

    recording_objects = cast(RecordingObjectRepository, objects)
    recording_changes = cast(RecordingObjectChangeRepository, object_changes)
    recording_relationships = cast(RecordingRelationshipRepository, relationships)
    assert commits[0] == 1
    assert recording_objects.discovery_log == [parent.id, child.id, grandchild.id]
    assert recording_relationships.list_incident_calls == [
        {parent.id, child.id, grandchild.id}
    ]
    assert recording_relationships.first_delete_discovery_count == 3
    assert recording_changes.first_add_discovery_count == 3
    assert recording_objects.first_delete_discovery_count == 3


def test_delete_cycle_failure_produces_zero_history_zero_deletion_and_zero_commit() -> None:
    first = _object(template_id=uuid4())
    second = _object(template_id=uuid4())
    cycle_repo = CycleObjectRepository(
        {
            first.id: (_membership(first.id, second.id),),
            second.id: (_membership(second.id, first.id),),
        }
    )
    _store_object(cycle_repo, first)
    _store_object(cycle_repo, second)
    object_changes = TrackingObjectChangeRepository()
    (
        service,
        _datatypes,
        _templates,
        objects,
        object_changes,
        relationships,
        commits,
    ) = _service(
        objects=cycle_repo,
        object_changes=object_changes,
        relationships=TrackingRelationshipRepository(),
    )

    with pytest.raises(ComponentOwnershipCycle):
        service.delete_object(first.id)

    tracked_changes = cast(TrackingObjectChangeRepository, object_changes)
    tracked_objects = cast(CycleObjectRepository, objects)
    tracked_relationships = cast(TrackingRelationshipRepository, relationships)
    assert tracked_changes.add_calls == []
    assert tracked_objects.delete_calls == []
    assert tracked_relationships.delete_calls == []
    assert commits[0] == 0
