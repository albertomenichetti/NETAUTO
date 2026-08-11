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
    DataTypeVersionStatus,
    PrimitiveTypeRegistry,
)
from netauto.core.object import (
    AbstractObjectTemplateInstantiation,
    InvalidObjectPatch,
    Object,
    ObjectChange,
    ObjectDataTypeVersionNotFound,
    ObjectNotFound,
    ObjectTemplateVersionNotPublished,
    ObjectValidationFailed,
)
from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateNotFound,
    ObjectTemplateParentNotFound,
    ObjectTemplateProperty,
    ObjectTemplateVersion,
    ObjectTemplateVersioningService,
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


class TrackingDataTypeRepository(InMemoryDataTypeRepository):
    def __init__(self) -> None:
        super().__init__()
        self.get_version_calls: list[tuple[UUID, int]] = []

    def get_version(self, datatype_id: UUID, version: int) -> DataTypeVersion | None:
        self.get_version_calls.append((datatype_id, version))
        return super().get_version(datatype_id, version)


class TrackingObjectTemplateRepository(InMemoryObjectTemplateRepository):
    def __init__(self) -> None:
        super().__init__()
        self.get_calls: list[UUID] = []
        self.get_version_calls: list[tuple[UUID, int]] = []

    def get(self, template_id: UUID) -> ObjectTemplate | None:
        self.get_calls.append(template_id)
        return super().get(template_id)

    def get_version(self, template_id: UUID, version: int) -> ObjectTemplateVersion | None:
        self.get_version_calls.append((template_id, version))
        return super().get_version(template_id, version)


class TrackingObjectRepository(InMemoryObjectRepository):
    def __init__(self) -> None:
        super().__init__()
        self.add_calls: list[Object] = []
        self.replace_calls: list[Object] = []

    def add(self, object_value: Object) -> None:
        self.add_calls.append(object_value)
        super().add(object_value)

    def replace(self, object_value: Object) -> None:
        self.replace_calls.append(object_value)
        super().replace(object_value)


class TrackingObjectChangeRepository(InMemoryObjectChangeRepository):
    def __init__(self) -> None:
        super().__init__()
        self.add_calls: list[ObjectChange] = []

    def add(self, change: ObjectChange) -> None:
        self.add_calls.append(change)
        super().add(change)


class FakeUnitOfWork(ObjectUnitOfWork):
    def __init__(
        self,
        datatypes: TrackingDataTypeRepository,
        object_templates: TrackingObjectTemplateRepository,
        objects: TrackingObjectRepository,
        object_changes: TrackingObjectChangeRepository,
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
    def datatypes(self) -> TrackingDataTypeRepository:
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
    def object_changes(self) -> TrackingObjectChangeRepository:
        return self._object_changes

    def __enter__(self) -> FakeUnitOfWork:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    def commit(self) -> None:
        self._commit_counter[0] += 1


def _service() -> tuple[
    ObjectApplicationService,
    TrackingDataTypeRepository,
    TrackingObjectTemplateRepository,
    TrackingObjectRepository,
    InMemoryRelationshipRepository,
    list[int],
]:
    datatypes = TrackingDataTypeRepository()
    object_templates = TrackingObjectTemplateRepository()
    objects = TrackingObjectRepository()
    object_changes = TrackingObjectChangeRepository()
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
    return DataTypeFactory().create(
        namespace=namespace,
        name=name,
        description=f"{name} datatype",
        base_type=base_type,
        constraints=constraints,
    )


def _store_datatype_versions(
    repo: InMemoryDataTypeRepository,
    datatype: DataType,
    versions: tuple[DataTypeVersion, ...],
) -> None:
    repo.add(datatype)
    for version in versions:
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
    version: int = 1,
    status: ObjectTemplateVersionStatus = ObjectTemplateVersionStatus.PUBLISHED,
    parent: ObjectTemplateVersionRef | None = None,
    properties: tuple[ObjectTemplateProperty, ...] = (),
) -> ObjectTemplateVersion:
    return ObjectTemplateVersion(
        template_id=template_id,
        version=version,
        status=status,
        parent=parent,
        properties=properties,
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
    object_id: UUID | None = None,
    template_id: UUID,
    template_version: int,
    properties: Mapping[str, object],
) -> Object:
    object_value = Object(
        id=object_id or uuid4(),
        template_id=template_id,
        template_version=template_version,
        properties=properties,
    )
    repo.add(object_value)
    return object_value


def _issue_details(exc: ObjectValidationFailed) -> tuple[tuple[tuple[str | int, ...], str], ...]:
    return tuple((error.path, error.code) for error in exc.result.errors)


def test_create_object_persists_exact_template_pin_and_commits() -> None:
    service, datatypes, object_templates, objects, _relationships, commits = _service()
    datatype, draft = _datatype()
    published = DataTypeVersioningService().publish(draft)
    _store_datatype_versions(datatypes, datatype, (published,))

    template = _template()
    version = _version(
        template.id,
        properties=(
            _property(
                "hostname",
                datatype_id=datatype.id,
                datatype_version=published.version,
                required=True,
            ),
        ),
    )
    _store_template_versions(object_templates, template, (version,))

    created = service.create_object(
        template_id=template.id,
        template_version=1,
        properties={"hostname": "router-01"},
    )

    assert created.id is not None
    assert created.template_id == template.id
    assert created.template_version == 1
    assert dict(created.properties) == {"hostname": "router-01"}
    assert objects.get(created.id) == created
    assert objects.get_owner(created.id) is None
    assert objects.add_calls == [created]
    assert commits[0] == 1


def test_create_missing_template_identity_or_version_raises_focused_exceptions() -> None:
    service, datatypes, object_templates, _objects, _relationships, commits = _service()
    datatype, draft = _datatype()
    published = DataTypeVersioningService().publish(draft)
    _store_datatype_versions(datatypes, datatype, (published,))

    with pytest.raises(ObjectTemplateNotFound):
        service.create_object(
            template_id=uuid4(),
            template_version=1,
            properties={"hostname": "router-01"},
        )

    template = _template()
    _store_template_versions(object_templates, template, ())

    with pytest.raises(ObjectTemplateVersionNotFound):
        service.create_object(
            template_id=template.id,
            template_version=1,
            properties={"hostname": "router-01"},
        )

    assert commits[0] == 0


def test_create_omitted_version_uses_highest_published_template_version() -> None:
    service, datatypes, object_templates, objects, _relationships, commits = _service()
    datatype, draft = _datatype()
    published = DataTypeVersioningService().publish(draft)
    _store_datatype_versions(datatypes, datatype, (published,))

    template = _template()
    versions = (
        _version(
            template.id,
            version=1,
            status=ObjectTemplateVersionStatus.PUBLISHED,
            properties=(
                _property(
                    "hostname",
                    datatype_id=datatype.id,
                    datatype_version=published.version,
                    required=True,
                ),
            ),
        ),
        _version(
            template.id,
            version=2,
            status=ObjectTemplateVersionStatus.PUBLISHED,
            properties=(
                _property(
                    "hostname",
                    datatype_id=datatype.id,
                    datatype_version=published.version,
                    required=True,
                ),
            ),
        ),
        _version(
            template.id,
            version=3,
            status=ObjectTemplateVersionStatus.DRAFT,
            properties=(
                _property(
                    "hostname",
                    datatype_id=datatype.id,
                    datatype_version=published.version,
                    required=True,
                ),
            ),
        ),
    )
    _store_template_versions(object_templates, template, versions)

    created = service.create_object(
        template_id=template.id,
        template_version=None,
        properties={"hostname": "router-01"},
    )

    assert created.template_version == 2
    assert objects.get(created.id) == created
    assert commits[0] == 1


def test_create_omitted_version_ignores_deprecated_and_draft_versions() -> None:
    service, datatypes, object_templates, objects, _relationships, commits = _service()
    datatype, draft = _datatype()
    published = DataTypeVersioningService().publish(draft)
    _store_datatype_versions(datatypes, datatype, (published,))

    template = _template()
    versions = (
        _version(
            template.id,
            version=1,
            status=ObjectTemplateVersionStatus.PUBLISHED,
            properties=(
                _property(
                    "hostname",
                    datatype_id=datatype.id,
                    datatype_version=published.version,
                    required=True,
                ),
            ),
        ),
        _version(
            template.id,
            version=2,
            status=ObjectTemplateVersionStatus.DEPRECATED,
            properties=(
                _property(
                    "hostname",
                    datatype_id=datatype.id,
                    datatype_version=published.version,
                    required=True,
                ),
            ),
        ),
        _version(
            template.id,
            version=3,
            status=ObjectTemplateVersionStatus.DRAFT,
            properties=(
                _property(
                    "hostname",
                    datatype_id=datatype.id,
                    datatype_version=published.version,
                    required=True,
                ),
            ),
        ),
    )
    _store_template_versions(object_templates, template, versions)

    created = service.create_object(
        template_id=template.id,
        template_version=None,
        properties={"hostname": "router-01"},
    )

    assert created.template_version == 1
    assert objects.get(created.id) == created
    assert commits[0] == 1


def test_create_omitted_version_fails_when_no_published_version_exists() -> None:
    service, datatypes, object_templates, objects, _relationships, commits = _service()
    datatype, draft = _datatype()
    published = DataTypeVersioningService().publish(draft)
    _store_datatype_versions(datatypes, datatype, (published,))

    template = _template()
    _store_template_versions(
        object_templates,
        template,
        (
            _version(
                template.id,
                version=1,
                status=ObjectTemplateVersionStatus.DEPRECATED,
                properties=(
                    _property(
                        "hostname",
                        datatype_id=datatype.id,
                        datatype_version=published.version,
                        required=True,
                    ),
                ),
            ),
            _version(
                template.id,
                version=2,
                status=ObjectTemplateVersionStatus.DRAFT,
                properties=(
                    _property(
                        "hostname",
                        datatype_id=datatype.id,
                        datatype_version=published.version,
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

    assert objects.list() == ()
    assert commits[0] == 0


def test_create_explicit_older_published_version_is_used_exactly() -> None:
    service, datatypes, object_templates, objects, _relationships, commits = _service()
    datatype, draft = _datatype()
    published = DataTypeVersioningService().publish(draft)
    _store_datatype_versions(datatypes, datatype, (published,))

    template = _template()
    _store_template_versions(
        object_templates,
        template,
        (
            _version(
                template.id,
                version=1,
                status=ObjectTemplateVersionStatus.PUBLISHED,
                properties=(
                    _property(
                        "hostname",
                        datatype_id=datatype.id,
                        datatype_version=published.version,
                        required=True,
                    ),
                ),
            ),
            _version(
                template.id,
                version=2,
                status=ObjectTemplateVersionStatus.PUBLISHED,
                properties=(
                    _property(
                        "hostname",
                        datatype_id=datatype.id,
                        datatype_version=published.version,
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

    assert created.template_version == 1
    assert objects.get(created.id) == created
    assert commits[0] == 1


@pytest.mark.parametrize(
    "status",
    (
        ObjectTemplateVersionStatus.DRAFT,
        ObjectTemplateVersionStatus.DEPRECATED,
    ),
)
def test_create_rejects_non_published_template_versions(
    status: ObjectTemplateVersionStatus,
) -> None:
    service, datatypes, object_templates, objects, _relationships, commits = _service()
    datatype, draft = _datatype()
    published = DataTypeVersioningService().publish(draft)
    _store_datatype_versions(datatypes, datatype, (published,))

    template = _template()
    version = _version(
        template.id,
        status=status,
        properties=(
            _property(
                "hostname",
                datatype_id=datatype.id,
                datatype_version=published.version,
                required=True,
            ),
        ),
    )
    _store_template_versions(object_templates, template, (version,))

    with pytest.raises(ObjectTemplateVersionNotPublished):
        service.create_object(
            template_id=template.id,
            template_version=1,
            properties={"hostname": "router-01"},
        )

    assert objects.list() == ()
    assert commits[0] == 0


def test_create_rejects_abstract_template_instantiation() -> None:
    service, datatypes, object_templates, objects, _relationships, commits = _service()
    datatype, draft = _datatype()
    published = DataTypeVersioningService().publish(draft)
    _store_datatype_versions(datatypes, datatype, (published,))

    template = _template(name="abstract_device", abstract=True)
    version = _version(
        template.id,
        properties=(
            _property(
                "hostname",
                datatype_id=datatype.id,
                datatype_version=published.version,
                required=True,
            ),
        ),
    )
    _store_template_versions(object_templates, template, (version,))

    with pytest.raises(AbstractObjectTemplateInstantiation):
        service.create_object(
            template_id=template.id,
            template_version=1,
            properties={"hostname": "router-01"},
        )

    assert objects.list() == ()
    assert commits[0] == 0


def test_create_validation_failure_preserves_structured_result() -> None:
    service, datatypes, object_templates, objects, _relationships, commits = _service()
    datatype, draft = _datatype(
        constraints=(Constraint(name=ConstraintName.MIN_LENGTH, value=3),),
    )
    published = DataTypeVersioningService().publish(draft)
    _store_datatype_versions(datatypes, datatype, (published,))

    template = _template()
    version = _version(
        template.id,
        properties=(
            _property(
                "hostname",
                datatype_id=datatype.id,
                datatype_version=published.version,
                required=True,
            ),
        ),
    )
    _store_template_versions(object_templates, template, (version,))

    with pytest.raises(ObjectValidationFailed) as exc_info:
        service.create_object(
            template_id=template.id,
            template_version=1,
            properties={"banana": "x"},
        )

    assert _issue_details(exc_info.value) == (
        (("properties", "banana"), "unknown_property"),
        (("properties", "hostname"), "required"),
    )
    assert objects.list() == ()
    assert commits[0] == 0


def test_create_uses_effective_inherited_properties_for_required_and_datatype_validation() -> None:
    service, datatypes, object_templates, objects, _relationships, commits = _service()
    hostname_datatype, hostname_draft = _datatype(
        name="hostname",
        constraints=(Constraint(name=ConstraintName.MIN_LENGTH, value=3),),
    )
    hostname_published = DataTypeVersioningService().publish(hostname_draft)
    serial_datatype, serial_draft = _datatype(name="serial", base_type="core.integer")
    serial_published = DataTypeVersioningService().publish(serial_draft)
    _store_datatype_versions(datatypes, hostname_datatype, (hostname_published,))
    _store_datatype_versions(datatypes, serial_datatype, (serial_published,))

    parent = _template(name="device")
    parent_version = _version(
        parent.id,
        properties=(
            _property(
                "hostname",
                datatype_id=hostname_datatype.id,
                datatype_version=hostname_published.version,
                required=True,
            ),
        ),
    )
    child = _template(name="router")
    child_version = _version(
        child.id,
        parent=ObjectTemplateVersionRef(template_id=parent.id, version=1),
        properties=(
            _property(
                "serial",
                datatype_id=serial_datatype.id,
                datatype_version=serial_published.version,
            ),
        ),
    )
    _store_template_versions(object_templates, parent, (parent_version,))
    _store_template_versions(object_templates, child, (child_version,))

    with pytest.raises(ObjectValidationFailed) as exc_info:
        service.create_object(
            template_id=child.id,
            template_version=1,
            properties={"serial": "bad"},
        )

    assert _issue_details(exc_info.value) == (
        (("properties", "hostname"), "required"),
        (("properties", "serial"), "type"),
    )
    assert objects.list() == ()
    assert commits[0] == 0


def test_create_preserves_missing_parent_inheritance_error() -> None:
    service, datatypes, object_templates, objects, _relationships, commits = _service()
    datatype, draft = _datatype()
    published = DataTypeVersioningService().publish(draft)
    _store_datatype_versions(datatypes, datatype, (published,))

    template = _template(name="router")
    version = _version(
        template.id,
        parent=ObjectTemplateVersionRef(template_id=uuid4(), version=1),
        properties=(
            _property(
                "hostname",
                datatype_id=datatype.id,
                datatype_version=published.version,
                required=True,
            ),
        ),
    )
    _store_template_versions(object_templates, template, (version,))

    with pytest.raises(ObjectTemplateParentNotFound):
        service.create_object(
            template_id=template.id,
            template_version=1,
            properties={"hostname": "router-01"},
        )

    assert objects.list() == ()
    assert commits[0] == 0


def test_create_requires_exact_pinned_datatype_version_without_fallback() -> None:
    service, datatypes, object_templates, objects, _relationships, commits = _service()
    datatype, v1_draft = _datatype()
    v1_published = DataTypeVersioningService().publish(v1_draft)
    v2_published = DataTypeVersion(
        datatype_id=datatype.id,
        version=2,
        status=DataTypeVersionStatus.PUBLISHED,
        base_type=v1_published.base_type,
        constraints=v1_published.constraints,
    )
    _store_datatype_versions(datatypes, datatype, (v2_published,))

    template = _template()
    version = _version(
        template.id,
        properties=(
            _property(
                "hostname",
                datatype_id=datatype.id,
                datatype_version=v1_published.version,
                required=True,
            ),
        ),
    )
    _store_template_versions(object_templates, template, (version,))

    with pytest.raises(ObjectDataTypeVersionNotFound):
        service.create_object(
            template_id=template.id,
            template_version=1,
            properties={"hostname": "router-01"},
        )

    assert datatypes.get_version_calls == [(datatype.id, 1)]
    assert objects.list() == ()
    assert commits[0] == 0


def test_create_accepts_deprecated_exact_pinned_datatype_version() -> None:
    service, datatypes, object_templates, objects, _relationships, commits = _service()
    datatype, draft = _datatype()
    published = DataTypeVersioningService().publish(draft)
    deprecated = DataTypeVersioningService().deprecate(published)
    _store_datatype_versions(datatypes, datatype, (deprecated,))

    template = _template()
    version = _version(
        template.id,
        properties=(
            _property(
                "hostname",
                datatype_id=datatype.id,
                datatype_version=deprecated.version,
                required=True,
            ),
        ),
    )
    _store_template_versions(object_templates, template, (version,))

    created = service.create_object(
        template_id=template.id,
        template_version=1,
        properties={"hostname": "router-01"},
    )

    assert dict(created.properties) == {"hostname": "router-01"}
    assert objects.get(created.id) == created
    assert commits[0] == 1


def test_list_and_get_are_read_only_and_do_not_revalidate_templates() -> None:
    service, datatypes, object_templates, objects, _relationships, commits = _service()
    first_template = _template(name="first")
    second_template = _template(name="second")
    first = _create_object(
        objects,
        object_id=UUID("00000000-0000-0000-0000-000000000002"),
        template_id=first_template.id,
        template_version=3,
        properties={"hostname": "router-02"},
    )
    second = _create_object(
        objects,
        object_id=UUID("00000000-0000-0000-0000-000000000001"),
        template_id=second_template.id,
        template_version=1,
        properties={},
    )

    assert service.list_objects() == (second, first)
    assert service.get_object(first.id) == first
    with pytest.raises(ObjectNotFound):
        service.get_object(uuid4())

    assert object_templates.get_calls == []
    assert object_templates.get_version_calls == []
    assert datatypes.get_version_calls == []
    assert commits[0] == 0


def test_update_sets_and_preserves_properties_then_replaces_and_commits() -> None:
    service, datatypes, object_templates, objects, _relationships, commits = _service()
    hostname_datatype, hostname_draft = _datatype(name="hostname")
    hostname_published = DataTypeVersioningService().publish(hostname_draft)
    serial_datatype, serial_draft = _datatype(name="serial")
    serial_published = DataTypeVersioningService().publish(serial_draft)
    _store_datatype_versions(datatypes, hostname_datatype, (hostname_published,))
    _store_datatype_versions(datatypes, serial_datatype, (serial_published,))

    template = _template()
    version = _version(
        template.id,
        properties=(
            _property(
                "hostname",
                datatype_id=hostname_datatype.id,
                datatype_version=hostname_published.version,
                required=True,
            ),
            _property(
                "serial",
                datatype_id=serial_datatype.id,
                datatype_version=serial_published.version,
            ),
        ),
    )
    _store_template_versions(object_templates, template, (version,))
    current = _create_object(
        objects,
        template_id=template.id,
        template_version=1,
        properties={"hostname": "router-01"},
    )

    updated = service.update_object(
        object_id=current.id,
        properties={"serial": "ABC123", "hostname": "router-02"},
    )

    assert updated.id == current.id
    assert updated.template_id == current.template_id
    assert updated.template_version == current.template_version
    assert dict(updated.properties) == {"hostname": "router-02", "serial": "ABC123"}
    assert objects.get(current.id) == updated
    assert objects.replace_calls == [updated]
    assert commits[0] == 1


def test_update_remove_optional_property_and_absent_optional_removal_are_allowed() -> None:
    service, datatypes, object_templates, objects, _relationships, commits = _service()
    hostname_datatype, hostname_draft = _datatype(name="hostname")
    hostname_published = DataTypeVersioningService().publish(hostname_draft)
    serial_datatype, serial_draft = _datatype(name="serial")
    serial_published = DataTypeVersioningService().publish(serial_draft)
    _store_datatype_versions(datatypes, hostname_datatype, (hostname_published,))
    _store_datatype_versions(datatypes, serial_datatype, (serial_published,))

    template = _template()
    version = _version(
        template.id,
        properties=(
            _property(
                "hostname",
                datatype_id=hostname_datatype.id,
                datatype_version=hostname_published.version,
                required=True,
            ),
            _property(
                "serial",
                datatype_id=serial_datatype.id,
                datatype_version=serial_published.version,
            ),
        ),
    )
    _store_template_versions(object_templates, template, (version,))

    with_optional = _create_object(
        objects,
        template_id=template.id,
        template_version=1,
        properties={"hostname": "router-01", "serial": "ABC123"},
    )
    removed = service.update_object(
        object_id=with_optional.id,
        remove_properties=("serial",),
    )
    assert dict(removed.properties) == {"hostname": "router-01"}

    absent_optional = _create_object(
        objects,
        template_id=template.id,
        template_version=1,
        properties={"hostname": "router-02"},
    )
    unchanged = service.update_object(
        object_id=absent_optional.id,
        remove_properties=("serial",),
    )
    assert dict(unchanged.properties) == {"hostname": "router-02"}
    assert commits[0] == 1


def test_update_treats_none_as_value_not_removal() -> None:
    service, datatypes, object_templates, objects, _relationships, commits = _service()
    datatype, draft = _datatype(name="hostname")
    published = DataTypeVersioningService().publish(draft)
    _store_datatype_versions(datatypes, datatype, (published,))

    template = _template()
    version = _version(
        template.id,
        properties=(
            _property(
                "hostname",
                datatype_id=datatype.id,
                datatype_version=published.version,
                required=True,
            ),
        ),
    )
    _store_template_versions(object_templates, template, (version,))
    current = _create_object(
        objects,
        template_id=template.id,
        template_version=1,
        properties={"hostname": "router-01"},
    )

    with pytest.raises(ObjectValidationFailed) as exc_info:
        service.update_object(
            object_id=current.id,
            properties={"hostname": None},
        )

    assert _issue_details(exc_info.value) == (((("properties", "hostname"), "type")),)
    assert objects.get(current.id) == current
    assert objects.replace_calls == []
    assert commits[0] == 0


@pytest.mark.parametrize(
    ("properties", "remove_properties", "message"),
    (
        ({"serial": "123"}, ("serial",), "set and removed"),
        ({}, (1,), "must be strings"),
        ({}, ("unknown",), "not declared"),
    ),
)
def test_update_rejects_invalid_patch_shape(
    properties: Mapping[str, object],
    remove_properties: tuple[object, ...],
    message: str,
) -> None:
    service, datatypes, object_templates, objects, _relationships, commits = _service()
    datatype, draft = _datatype(name="hostname")
    published = DataTypeVersioningService().publish(draft)
    _store_datatype_versions(datatypes, datatype, (published,))

    template = _template()
    version = _version(
        template.id,
        properties=(
            _property(
                "hostname",
                datatype_id=datatype.id,
                datatype_version=published.version,
                required=True,
            ),
            _property(
                "serial",
                datatype_id=datatype.id,
                datatype_version=published.version,
            ),
        ),
    )
    _store_template_versions(object_templates, template, (version,))
    current = _create_object(
        objects,
        template_id=template.id,
        template_version=1,
        properties={"hostname": "router-01"},
    )

    with pytest.raises(InvalidObjectPatch, match=message):
        service.update_object(
            object_id=current.id,
            properties=properties,
            remove_properties=remove_properties,  # type: ignore[arg-type]
        )

    assert objects.get(current.id) == current
    assert objects.replace_calls == []
    assert commits[0] == 0


def test_update_validates_complete_candidate_snapshot() -> None:
    service, datatypes, object_templates, objects, _relationships, commits = _service()
    hostname_datatype, hostname_draft = _datatype(name="hostname")
    hostname_published = DataTypeVersioningService().publish(hostname_draft)
    serial_datatype, serial_draft = _datatype(name="serial", base_type="core.integer")
    serial_published = DataTypeVersioningService().publish(serial_draft)
    _store_datatype_versions(datatypes, hostname_datatype, (hostname_published,))
    _store_datatype_versions(datatypes, serial_datatype, (serial_published,))

    template = _template()
    version = _version(
        template.id,
        properties=(
            _property(
                "hostname",
                datatype_id=hostname_datatype.id,
                datatype_version=hostname_published.version,
                required=True,
            ),
            _property(
                "serial",
                datatype_id=serial_datatype.id,
                datatype_version=serial_published.version,
            ),
        ),
    )
    _store_template_versions(object_templates, template, (version,))

    invalid_current = _create_object(
        objects,
        template_id=template.id,
        template_version=1,
        properties={"hostname": "router-01", "serial": "bad"},
    )

    with pytest.raises(ObjectValidationFailed) as exc_info:
        service.update_object(
            object_id=invalid_current.id,
            properties={"hostname": "router-02"},
        )

    assert _issue_details(exc_info.value) == (((("properties", "serial"), "type")),)
    assert objects.get(invalid_current.id) == invalid_current
    assert objects.replace_calls == []
    assert commits[0] == 0


def test_update_rejects_required_removal_unknown_property_and_invalid_datatype() -> None:
    service, datatypes, object_templates, objects, _relationships, commits = _service()
    hostname_datatype, hostname_draft = _datatype(name="hostname")
    hostname_published = DataTypeVersioningService().publish(hostname_draft)
    serial_datatype, serial_draft = _datatype(name="serial", base_type="core.integer")
    serial_published = DataTypeVersioningService().publish(serial_draft)
    _store_datatype_versions(datatypes, hostname_datatype, (hostname_published,))
    _store_datatype_versions(datatypes, serial_datatype, (serial_published,))

    template = _template()
    version = _version(
        template.id,
        properties=(
            _property(
                "hostname",
                datatype_id=hostname_datatype.id,
                datatype_version=hostname_published.version,
                required=True,
            ),
            _property(
                "serial",
                datatype_id=serial_datatype.id,
                datatype_version=serial_published.version,
            ),
        ),
    )
    _store_template_versions(object_templates, template, (version,))
    current = _create_object(
        objects,
        template_id=template.id,
        template_version=1,
        properties={"hostname": "router-01"},
    )

    with pytest.raises(ObjectValidationFailed) as remove_exc:
        service.update_object(
            object_id=current.id,
            remove_properties=("hostname",),
        )
    assert _issue_details(remove_exc.value) == (((("properties", "hostname"), "required")),)

    with pytest.raises(ObjectValidationFailed) as unknown_exc:
        service.update_object(
            object_id=current.id,
            properties={"banana": "yellow"},
        )
    assert _issue_details(unknown_exc.value) == (((("properties", "banana"), "unknown_property")),)

    with pytest.raises(ObjectValidationFailed) as datatype_exc:
        service.update_object(
            object_id=current.id,
            properties={"serial": "bad"},
        )
    assert _issue_details(datatype_exc.value) == (((("properties", "serial"), "type")),)

    assert objects.get(current.id) == current
    assert objects.replace_calls == []
    assert commits[0] == 0


def test_empty_patch_returns_current_without_replace_or_commit() -> None:
    service, _datatypes, _object_templates, objects, _relationships, commits = _service()
    current = _create_object(
        objects,
        template_id=uuid4(),
        template_version=2,
        properties={"hostname": "router-01"},
    )

    returned = service.update_object(
        object_id=current.id,
        properties=None,
        remove_properties=(),
    )

    assert returned == current
    assert objects.replace_calls == []
    assert commits[0] == 0


def test_update_uses_exact_pinned_template_version_and_allows_deprecated_pins() -> None:
    service, datatypes, object_templates, objects, _relationships, commits = _service()
    datatype, v1_draft = _datatype(name="hostname")
    v1_published = DataTypeVersioningService().publish(v1_draft)
    v2_string = DataTypeVersion(
        datatype_id=datatype.id,
        version=2,
        status=DataTypeVersionStatus.PUBLISHED,
        base_type=PrimitiveTypeRegistry().get("core.string"),
        constraints=(Constraint(name=ConstraintName.MIN_LENGTH, value=10),),
    )
    _store_datatype_versions(datatypes, datatype, (v1_published, v2_string))

    template = _template()
    v1_deprecated = _version(
        template.id,
        version=1,
        status=ObjectTemplateVersionStatus.DEPRECATED,
        properties=(
            _property(
                "hostname",
                datatype_id=datatype.id,
                datatype_version=v1_published.version,
                required=True,
            ),
        ),
    )
    v2_published = _version(
        template.id,
        version=2,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        properties=(
            _property(
                "hostname",
                datatype_id=datatype.id,
                datatype_version=v2_string.version,
                required=True,
            ),
        ),
    )
    _store_template_versions(object_templates, template, (v1_deprecated, v2_published))
    current = _create_object(
        objects,
        template_id=template.id,
        template_version=1,
        properties={"hostname": "router-01"},
    )

    updated = service.update_object(
        object_id=current.id,
        properties={"hostname": "router-02"},
    )

    assert updated.id == current.id
    assert updated.template_id == current.template_id
    assert updated.template_version == 1
    assert dict(updated.properties) == {"hostname": "router-02"}
    assert object_templates.get_version_calls == [(template.id, 1)]
    assert datatypes.get_version_calls == [(datatype.id, 1)]
    assert commits[0] == 1
