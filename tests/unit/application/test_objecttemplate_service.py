from __future__ import annotations

import ast
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from netauto.application.objecttemplate import (
    ObjectTemplateApplicationService,
    ObjectTemplateComponentSpec,
    ObjectTemplatePropertySpec,
)
from netauto.application.unit_of_work import ObjectTemplateUnitOfWork
from netauto.core.datatype import (
    DataType,
    DataTypeFactory,
    DataTypeVersion,
    DataTypeVersioningService,
    DataTypeVersionStatus,
)
from netauto.core.objecttemplate import (
    InheritedObjectTemplateComponentConflict,
    InheritedObjectTemplatePropertyConflict,
    InvalidObjectTemplateVersionTransition,
    ObjectTemplate,
    ObjectTemplateComponent,
    ObjectTemplateComponentVersionNotFound,
    ObjectTemplateComponentVersionNotPublished,
    ObjectTemplateDataTypeVersionNotFound,
    ObjectTemplateDataTypeVersionNotPublished,
    ObjectTemplateNotFound,
    ObjectTemplateParentNotFound,
    ObjectTemplateParentNotPublished,
    ObjectTemplateProperty,
    ObjectTemplateVersion,
    ObjectTemplateVersionNotFound,
    ObjectTemplateVersionRef,
    ObjectTemplateVersionStatus,
)
from netauto.persistence.memory.datatype_repository import InMemoryDataTypeRepository
from netauto.persistence.memory.objecttemplate_repository import (
    InMemoryObjectTemplateRepository,
)


class TrackingObjectTemplateRepository(InMemoryObjectTemplateRepository):
    def __init__(self) -> None:
        super().__init__()
        self.get_version_calls: list[tuple[UUID, int]] = []
        self.list_versions_calls: list[UUID] = []

    def get_version(self, template_id: UUID, version: int) -> ObjectTemplateVersion | None:
        self.get_version_calls.append((template_id, version))
        return super().get_version(template_id, version)

    def list_versions(self, template_id: UUID) -> tuple[ObjectTemplateVersion, ...]:
        self.list_versions_calls.append(template_id)
        return super().list_versions(template_id)


class FakeUnitOfWork(ObjectTemplateUnitOfWork):
    def __init__(
        self,
        datatypes: InMemoryDataTypeRepository,
        object_templates: TrackingObjectTemplateRepository,
        commit_counter: list[int],
    ) -> None:
        self._datatypes = datatypes
        self._object_templates = object_templates
        self._commit_counter = commit_counter

    @property
    def datatypes(self) -> InMemoryDataTypeRepository:
        return self._datatypes

    @property
    def object_templates(self) -> TrackingObjectTemplateRepository:
        return self._object_templates

    def __enter__(self) -> FakeUnitOfWork:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    def commit(self) -> None:
        self._commit_counter[0] += 1


def _service() -> tuple[
    ObjectTemplateApplicationService,
    InMemoryDataTypeRepository,
    TrackingObjectTemplateRepository,
    list[int],
]:
    datatypes = InMemoryDataTypeRepository()
    object_templates = TrackingObjectTemplateRepository()
    commit_counter = [0]

    def factory() -> FakeUnitOfWork:
        return FakeUnitOfWork(datatypes, object_templates, commit_counter)

    return (
        ObjectTemplateApplicationService(factory),
        datatypes,
        object_templates,
        commit_counter,
    )


def _published_datatype(
    *,
    namespace: str = "network",
    name: str = "hostname",
) -> tuple[DataType, DataTypeVersion]:
    datatype, draft = DataTypeFactory().create(
        namespace=namespace,
        name=name,
        description=f"{name} datatype",
        base_type="core.string",
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


def _spec(
    name: str,
    *,
    datatype_id: UUID,
    datatype_version: int | None = None,
    required: bool = False,
) -> ObjectTemplatePropertySpec:
    return ObjectTemplatePropertySpec(
        name=name,
        datatype_id=datatype_id,
        datatype_version=datatype_version,
        required=required,
    )


def _component_spec(
    name: str,
    *,
    template_id: UUID,
    template_version: int | None = None,
) -> ObjectTemplateComponentSpec:
    del template_version
    return ObjectTemplateComponentSpec(
        name=name,
        template_id=template_id,
    )


def _published_object_template_version(
    template_id: UUID,
    *,
    parent: ObjectTemplateVersionRef | None = None,
    properties: tuple[ObjectTemplateProperty, ...] = (),
    components: tuple[ObjectTemplateComponent, ...] = (),
) -> ObjectTemplateVersion:
    return ObjectTemplateVersion(
        template_id=template_id,
        version=1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        parent=parent,
        properties=properties,
        components=components,
    )


def _store_object_template_versions(
    repo: InMemoryObjectTemplateRepository,
    template: ObjectTemplate,
    versions: tuple[ObjectTemplateVersion, ...],
) -> None:
    repo.add(template)
    for version in versions:
        repo.add_version(version)


def test_objecttemplate_property_spec_accepts_none_and_positive_int() -> None:
    spec_none = ObjectTemplatePropertySpec(
        name="hostname",
        datatype_id=uuid4(),
        datatype_version=None,
    )
    spec_one = ObjectTemplatePropertySpec(
        name="hostname",
        datatype_id=uuid4(),
        datatype_version=1,
    )

    assert spec_none.datatype_version is None
    assert spec_one.datatype_version == 1


@pytest.mark.parametrize("value", [True, False, 0, -1, -5])
def test_objecttemplate_property_spec_rejects_invalid_runtime_datatype_version(
    value: object,
) -> None:
    with pytest.raises(
        ValueError,
        match="datatype_version must be a plain int >= 1 or None",
    ):
        ObjectTemplatePropertySpec(
            name="hostname",
            datatype_id=uuid4(),
            datatype_version=value,  # type: ignore[arg-type]
        )


def test_reads_do_not_commit() -> None:
    service, datatypes, object_templates, commits = _service()
    datatype, datatype_version = _published_datatype()
    _store_datatype_versions(datatypes, datatype, (datatype_version,))

    template = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="device",
        description="Device template",
        abstract=False,
    )
    version = ObjectTemplateVersion(
        template_id=template.id,
        version=1,
        status=ObjectTemplateVersionStatus.DRAFT,
        properties=(
            ObjectTemplateProperty(
                name="hostname",
                datatype_id=datatype.id,
                datatype_version=datatype_version.version,
            ),
        ),
    )
    object_templates.add(template)
    object_templates.add_version(version)

    assert service.list_object_templates() == (template,)
    assert service.get_object_template(template.id) == template
    assert service.get_object_template_by_name("network", "device") == template
    assert service.list_versions(template.id) == (version,)
    assert service.get_version(template.id, 1) == version
    assert commits[0] == 0


def test_missing_template_and_version_raise_focused_errors() -> None:
    service, _datatypes, object_templates, _commits = _service()
    template = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="device",
        description=None,
        abstract=False,
    )
    object_templates.add(template)

    with pytest.raises(ObjectTemplateNotFound):
        service.get_object_template(uuid4())
    with pytest.raises(ObjectTemplateNotFound):
        service.list_versions(uuid4())
    with pytest.raises(ObjectTemplateVersionNotFound):
        service.get_version(template.id, 1)


def test_create_object_template_creates_identity_and_v1_draft() -> None:
    service, datatypes, object_templates, commits = _service()
    datatype, datatype_version = _published_datatype()
    _store_datatype_versions(datatypes, datatype, (datatype_version,))
    parent = ObjectTemplateVersionRef(template_id=uuid4(), version=2)

    template, version = service.create_object_template(
        namespace="network",
        name="router",
        description="Router template",
        abstract=True,
        parent=parent,
        properties=(
            _spec("hostname", datatype_id=datatype.id, required=True),
            _spec("serial", datatype_id=datatype.id),
        ),
    )

    assert commits[0] == 1
    assert template.abstract is True
    assert version.status is ObjectTemplateVersionStatus.DRAFT
    assert version.parent == parent
    assert tuple(prop.name for prop in version.properties) == ("hostname", "serial")
    assert version.properties[0].required is True
    assert object_templates.get(template.id) == template
    assert object_templates.get_version(template.id, 1) == version


def test_create_object_template_stores_identity_only_components_and_properties_together() -> None:
    service, datatypes, object_templates, commits = _service()
    datatype, datatype_version = _published_datatype()
    _store_datatype_versions(datatypes, datatype, (datatype_version,))
    component_target = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="network_interface",
        description=None,
        abstract=True,
    )
    target_v1 = _published_object_template_version(component_target.id)
    target_v2 = ObjectTemplateVersion(
        template_id=component_target.id,
        version=2,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        properties=(),
        components=(),
    )
    _store_object_template_versions(object_templates, component_target, (target_v1, target_v2))

    template, version = service.create_object_template(
        namespace="network",
        name="device",
        description=None,
        abstract=False,
        parent=None,
        properties=(_spec("hostname", datatype_id=datatype.id, required=True),),
        components=(_component_spec("interfaces", template_id=component_target.id),),
    )

    assert commits[0] == 1
    assert version.properties[0].datatype_version == datatype_version.version
    assert version.components == (
        ObjectTemplateComponent(
            name="interfaces",
            template_id=component_target.id,
        ),
    )
    assert object_templates.get(template.id) == template
    assert object_templates.get_version(template.id, 1) == version
    assert component_target.abstract is True


def test_explicit_published_datatype_version_is_accepted() -> None:
    service, datatypes, _object_templates, _commits = _service()
    datatype, published = _published_datatype()
    _store_datatype_versions(datatypes, datatype, (published,))

    _, version = service.create_object_template(
        namespace="network",
        name="device",
        description=None,
        abstract=False,
        parent=None,
        properties=(
            _spec(
                "hostname",
                datatype_id=datatype.id,
                datatype_version=published.version,
            ),
        ),
    )

    assert version.properties[0].datatype_version == published.version


def test_published_component_target_identity_is_accepted() -> None:
    service, datatypes, object_templates, _commits = _service()
    datatype, datatype_version = _published_datatype()
    _store_datatype_versions(datatypes, datatype, (datatype_version,))
    component_target = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="network_interface",
        description=None,
        abstract=False,
    )
    published_target = _published_object_template_version(component_target.id)
    _store_object_template_versions(object_templates, component_target, (published_target,))

    _, version = service.create_object_template(
        namespace="network",
        name="device",
        description=None,
        abstract=False,
        parent=None,
        properties=(),
        components=(
            _component_spec(
                "interfaces",
                template_id=component_target.id,
            ),
        ),
    )

    assert version.components[0] == ObjectTemplateComponent(
        name="interfaces",
        template_id=component_target.id,
    )
    assert object_templates.list_versions_calls == [component_target.id]


@pytest.mark.parametrize("status", [DataTypeVersionStatus.DRAFT, DataTypeVersionStatus.DEPRECATED])
def test_explicit_non_published_datatype_version_rejected(status: DataTypeVersionStatus) -> None:
    service, datatypes, _object_templates, commits = _service()
    datatype, draft = DataTypeFactory().create(
        namespace="network",
        name=f"hostname_{status.value}",
        description=None,
        base_type="core.string",
    )
    version = DataTypeVersion(
        datatype_id=datatype.id,
        version=draft.version,
        status=status,
        base_type=draft.base_type,
        constraints=draft.constraints,
    )
    _store_datatype_versions(datatypes, datatype, (version,))

    with pytest.raises(ObjectTemplateDataTypeVersionNotPublished):
        service.create_object_template(
            namespace="network",
            name=f"device_{status.value}",
            description=None,
            abstract=False,
            parent=None,
            properties=(
                _spec(
                    "hostname",
                    datatype_id=datatype.id,
                    datatype_version=version.version,
                ),
            ),
        )

    assert commits[0] == 0


@pytest.mark.parametrize(
    "status",
    [ObjectTemplateVersionStatus.DRAFT, ObjectTemplateVersionStatus.DEPRECATED],
)
def test_explicit_non_published_component_target_version_rejected(
    status: ObjectTemplateVersionStatus,
) -> None:
    service, datatypes, object_templates, commits = _service()
    datatype, datatype_version = _published_datatype()
    _store_datatype_versions(datatypes, datatype, (datatype_version,))
    component_target = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name=f"network_interface_{status.value}",
        description=None,
        abstract=False,
    )
    target_version = ObjectTemplateVersion(
        template_id=component_target.id,
        version=1,
        status=status,
        properties=(),
        components=(),
    )
    _store_object_template_versions(object_templates, component_target, (target_version,))

    with pytest.raises(ObjectTemplateComponentVersionNotPublished):
        service.create_object_template(
            namespace="network",
            name=f"device_{status.value}",
            description=None,
            abstract=False,
            parent=None,
            properties=(),
            components=(
                _component_spec(
                    "interfaces",
                    template_id=component_target.id,
                ),
            ),
        )

    assert commits[0] == 0


def test_missing_component_target_identity_rejected_and_does_not_commit() -> None:
    service, datatypes, object_templates, commits = _service()
    datatype, datatype_version = _published_datatype()
    _store_datatype_versions(datatypes, datatype, (datatype_version,))
    missing_target_id = uuid4()

    with pytest.raises(ObjectTemplateComponentVersionNotFound):
        service.create_object_template(
            namespace="network",
            name="device",
            description=None,
            abstract=False,
            parent=None,
            properties=(),
            components=(
                _component_spec(
                    "interfaces",
                    template_id=missing_target_id,
                ),
            ),
        )

    assert commits[0] == 0


def test_explicit_missing_datatype_version_rejected() -> None:
    service, datatypes, _object_templates, commits = _service()
    datatype, published = _published_datatype()
    _store_datatype_versions(datatypes, datatype, (published,))

    with pytest.raises(ObjectTemplateDataTypeVersionNotFound):
        service.create_object_template(
            namespace="network",
            name="device",
            description=None,
            abstract=False,
            parent=None,
            properties=(
                _spec("hostname", datatype_id=datatype.id, datatype_version=99),
            ),
        )

    assert commits[0] == 0


def test_component_target_identity_does_not_resolve_or_store_a_specific_version(
) -> None:
    service, datatypes, object_templates, _commits = _service()
    datatype, datatype_version = _published_datatype()
    _store_datatype_versions(datatypes, datatype, (datatype_version,))
    component_target = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="network_interface",
        description=None,
        abstract=False,
    )
    v1_published = _published_object_template_version(component_target.id)
    v2_published = ObjectTemplateVersion(
        template_id=component_target.id,
        version=2,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        properties=(),
        components=(),
    )
    v3_draft = ObjectTemplateVersion(
        template_id=component_target.id,
        version=3,
        status=ObjectTemplateVersionStatus.DRAFT,
        properties=(),
        components=(),
    )
    v4_deprecated = ObjectTemplateVersion(
        template_id=component_target.id,
        version=4,
        status=ObjectTemplateVersionStatus.DEPRECATED,
        properties=(),
        components=(),
    )
    _store_object_template_versions(
        object_templates,
        component_target,
        (v1_published, v2_published, v3_draft, v4_deprecated),
    )

    _, version = service.create_object_template(
        namespace="network",
        name="device",
        description=None,
        abstract=False,
        parent=None,
        properties=(),
        components=(_component_spec("interfaces", template_id=component_target.id),),
    )

    assert version.components[0] == ObjectTemplateComponent(
        name="interfaces",
        template_id=component_target.id,
    )
    assert object_templates.list_versions_calls == [component_target.id]


def test_omitted_version_chooses_highest_published_ignoring_newer_draft_and_deprecated() -> None:
    service, datatypes, _object_templates, _commits = _service()
    datatype, draft = DataTypeFactory().create(
        namespace="network",
        name="status",
        description=None,
        base_type="core.string",
    )
    versioning = DataTypeVersioningService()
    v1_published = versioning.publish(draft)
    v2_published = DataTypeVersion(
        datatype_id=datatype.id,
        version=2,
        status=DataTypeVersionStatus.PUBLISHED,
        base_type=draft.base_type,
        constraints=draft.constraints,
    )
    v3_draft = DataTypeVersion(
        datatype_id=datatype.id,
        version=3,
        status=DataTypeVersionStatus.DRAFT,
        base_type=draft.base_type,
        constraints=draft.constraints,
    )
    v4_deprecated = DataTypeVersion(
        datatype_id=datatype.id,
        version=4,
        status=DataTypeVersionStatus.DEPRECATED,
        base_type=draft.base_type,
        constraints=draft.constraints,
    )
    _store_datatype_versions(
        datatypes,
        datatype,
        (v1_published, v2_published, v3_draft, v4_deprecated),
    )

    _, version = service.create_object_template(
        namespace="network",
        name="device",
        description=None,
        abstract=False,
        parent=None,
        properties=(_spec("hostname", datatype_id=datatype.id),),
    )

    assert version.properties[0].datatype_version == 2


def test_omitted_component_version_with_identity_but_no_published_version_rejected() -> None:
    service, datatypes, object_templates, commits = _service()
    datatype, datatype_version = _published_datatype()
    _store_datatype_versions(datatypes, datatype, (datatype_version,))
    component_target = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="network_interface",
        description=None,
        abstract=False,
    )
    draft = ObjectTemplateVersion(
        template_id=component_target.id,
        version=1,
        status=ObjectTemplateVersionStatus.DRAFT,
        properties=(),
        components=(),
    )
    deprecated = ObjectTemplateVersion(
        template_id=component_target.id,
        version=2,
        status=ObjectTemplateVersionStatus.DEPRECATED,
        properties=(),
        components=(),
    )
    _store_object_template_versions(object_templates, component_target, (draft, deprecated))

    with pytest.raises(ObjectTemplateComponentVersionNotPublished):
        service.create_object_template(
            namespace="network",
            name="device",
            description=None,
            abstract=False,
            parent=None,
            properties=(),
            components=(_component_spec("interfaces", template_id=component_target.id),),
        )

    assert commits[0] == 0
    assert object_templates.list_versions_calls == [component_target.id]


def test_omitted_version_with_identity_but_no_published_version_rejected() -> None:
    service, datatypes, _object_templates, commits = _service()
    datatype, draft = DataTypeFactory().create(
        namespace="network",
        name="status",
        description=None,
        base_type="core.string",
    )
    deprecated = DataTypeVersion(
        datatype_id=datatype.id,
        version=2,
        status=DataTypeVersionStatus.DEPRECATED,
        base_type=draft.base_type,
        constraints=draft.constraints,
    )
    _store_datatype_versions(datatypes, datatype, (draft, deprecated))

    with pytest.raises(ObjectTemplateDataTypeVersionNotPublished):
        service.create_object_template(
            namespace="network",
            name="device",
            description=None,
            abstract=False,
            parent=None,
            properties=(_spec("hostname", datatype_id=datatype.id),),
        )

    assert commits[0] == 0


def test_omitted_component_version_with_missing_template_rejected() -> None:
    service, datatypes, _object_templates, commits = _service()
    datatype, datatype_version = _published_datatype()
    _store_datatype_versions(datatypes, datatype, (datatype_version,))

    with pytest.raises(ObjectTemplateComponentVersionNotFound):
        service.create_object_template(
            namespace="network",
            name="device",
            description=None,
            abstract=False,
            parent=None,
            properties=(),
            components=(_component_spec("interfaces", template_id=uuid4()),),
        )

    assert commits[0] == 0


def test_omitted_version_with_missing_datatype_rejected() -> None:
    service, _datatypes, _object_templates, commits = _service()

    with pytest.raises(ObjectTemplateDataTypeVersionNotFound):
        service.create_object_template(
            namespace="network",
            name="device",
            description=None,
            abstract=False,
            parent=None,
            properties=(_spec("hostname", datatype_id=uuid4()),),
        )

    assert commits[0] == 0


def test_revise_draft_replaces_snapshot_and_preserves_identity_abstract() -> None:
    service, datatypes, object_templates, commits = _service()
    datatype, published = _published_datatype()
    _store_datatype_versions(datatypes, datatype, (published,))
    template = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="device",
        description=None,
        abstract=True,
    )
    draft = ObjectTemplateVersion(
        template_id=template.id,
        version=1,
        status=ObjectTemplateVersionStatus.DRAFT,
        properties=(),
    )
    object_templates.add(template)
    object_templates.add_version(draft)

    revised = service.revise_version(
        template_id=template.id,
        version=1,
        parent=None,
        properties=(_spec("hostname", datatype_id=datatype.id),),
    )

    assert commits[0] == 1
    assert revised.status is ObjectTemplateVersionStatus.DRAFT
    assert revised.properties[0].datatype_version == published.version
    assert object_templates.get_version(template.id, 1) == revised
    assert object_templates.get(template.id) == template
    assert template.abstract is True


def test_revise_replaces_components_with_newly_resolved_snapshot_and_can_clear() -> None:
    service, datatypes, object_templates, commits = _service()
    datatype, published = _published_datatype()
    _store_datatype_versions(datatypes, datatype, (published,))
    abstract_target = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="network_interface",
        description=None,
        abstract=True,
    )
    target_v1 = _published_object_template_version(abstract_target.id)
    target_v2 = ObjectTemplateVersion(
        template_id=abstract_target.id,
        version=2,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        properties=(),
        components=(),
    )
    _store_object_template_versions(object_templates, abstract_target, (target_v1, target_v2))
    template = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="device",
        description=None,
        abstract=False,
    )
    draft = ObjectTemplateVersion(
        template_id=template.id,
        version=1,
        status=ObjectTemplateVersionStatus.DRAFT,
        properties=(),
        components=(
            ObjectTemplateComponent(
                name="old_components",
                template_id=abstract_target.id,
            ),
        ),
    )
    object_templates.add(template)
    object_templates.add_version(draft)

    revised = service.revise_version(
        template_id=template.id,
        version=1,
        parent=None,
        properties=(_spec("hostname", datatype_id=datatype.id),),
        components=(_component_spec("interfaces", template_id=abstract_target.id),),
    )

    assert commits[0] == 1
    assert revised.properties[0].datatype_version == published.version
    assert revised.components == (
        ObjectTemplateComponent(
            name="interfaces",
            template_id=abstract_target.id,
        ),
    )
    assert object_templates.get(template.id) == template
    assert abstract_target.abstract is True

    cleared = service.revise_version(
        template_id=template.id,
        version=1,
        parent=None,
        properties=(),
        components=(),
    )

    assert commits[0] == 2
    assert cleared.components == ()


def test_revise_invalid_transition_does_not_commit() -> None:
    service, datatypes, object_templates, commits = _service()
    datatype, published_datatype = _published_datatype()
    _store_datatype_versions(datatypes, datatype, (published_datatype,))
    template = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="device",
        description=None,
        abstract=False,
    )
    published = ObjectTemplateVersion(
        template_id=template.id,
        version=1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        properties=(),
    )
    object_templates.add(template)
    object_templates.add_version(published)

    with pytest.raises(InvalidObjectTemplateVersionTransition):
        service.revise_version(
            template_id=template.id,
            version=1,
            parent=None,
            properties=(_spec("hostname", datatype_id=datatype.id),),
        )

    assert commits[0] == 0
    assert object_templates.get_version(template.id, 1) == published


def test_create_next_version_clones_exact_pinned_snapshot_without_reresolving() -> None:
    service, datatypes, object_templates, commits = _service()
    datatype, published_datatype = _published_datatype()
    _store_datatype_versions(datatypes, datatype, (published_datatype,))
    deprecated_datatype = DataTypeVersion(
        datatype_id=datatype.id,
        version=published_datatype.version,
        status=DataTypeVersionStatus.DEPRECATED,
        base_type=published_datatype.base_type,
        constraints=published_datatype.constraints,
    )

    template = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="device",
        description=None,
        abstract=False,
    )
    parent = ObjectTemplateVersionRef(template_id=uuid4(), version=2)
    source = ObjectTemplateVersion(
        template_id=template.id,
        version=1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        parent=parent,
        properties=(
            ObjectTemplateProperty(
                name="hostname",
                datatype_id=datatype.id,
                datatype_version=published_datatype.version,
            ),
        ),
    )
    object_templates.add(template)
    object_templates.add_version(source)
    datatypes.replace_version(deprecated_datatype)

    next_version = service.create_next_version(template_id=template.id, source_version=1)

    assert commits[0] == 1
    assert next_version.version == 2
    assert next_version.status is ObjectTemplateVersionStatus.DRAFT
    assert next_version.parent == source.parent
    assert next_version.properties == source.properties


def test_create_next_version_clones_component_identity_without_reresolving() -> None:
    service, datatypes, object_templates, commits = _service()
    datatype, published_datatype = _published_datatype()
    _store_datatype_versions(datatypes, datatype, (published_datatype,))
    component_target = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="network_interface",
        description=None,
        abstract=False,
    )
    pinned_published = _published_object_template_version(component_target.id)
    newer_published = ObjectTemplateVersion(
        template_id=component_target.id,
        version=2,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        properties=(),
        components=(),
    )
    _store_object_template_versions(
        object_templates,
        component_target,
        (pinned_published, newer_published),
    )

    template = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="device",
        description=None,
        abstract=False,
    )
    source = ObjectTemplateVersion(
        template_id=template.id,
        version=1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        properties=(),
        components=(
            ObjectTemplateComponent(
                name="interfaces",
                template_id=component_target.id,
            ),
        ),
    )
    object_templates.add(template)
    object_templates.add_version(source)
    deprecated_target = ObjectTemplateVersion(
        template_id=component_target.id,
        version=1,
        status=ObjectTemplateVersionStatus.DEPRECATED,
        properties=(),
        components=(),
    )
    object_templates.replace_version(deprecated_target)
    object_templates.get_version_calls.clear()
    object_templates.list_versions_calls.clear()

    next_version = service.create_next_version(template_id=template.id, source_version=1)

    assert commits[0] == 1
    assert next_version.version == 2
    assert next_version.status is ObjectTemplateVersionStatus.DRAFT
    assert next_version.components == source.components
    assert object_templates.list_versions_calls == [template.id]
    assert (component_target.id, 1) not in object_templates.get_version_calls
    assert component_target.id not in object_templates.list_versions_calls


def test_publish_root_template_succeeds_and_commits() -> None:
    service, datatypes, object_templates, commits = _service()
    datatype, published_datatype = _published_datatype()
    _store_datatype_versions(datatypes, datatype, (published_datatype,))
    template = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="device",
        description=None,
        abstract=False,
    )
    draft = ObjectTemplateVersion(
        template_id=template.id,
        version=1,
        status=ObjectTemplateVersionStatus.DRAFT,
        properties=(
            ObjectTemplateProperty(
                name="hostname",
                datatype_id=datatype.id,
                datatype_version=published_datatype.version,
            ),
        ),
    )
    object_templates.add(template)
    object_templates.add_version(draft)

    published = service.publish_version(template_id=template.id, version=1)

    assert commits[0] == 1
    assert published.status is ObjectTemplateVersionStatus.PUBLISHED
    assert object_templates.get_version(template.id, 1) == published


def test_publish_missing_or_non_published_component_target_blocks_publication() -> None:
    service, datatypes, object_templates, commits = _service()
    datatype, published_datatype = _published_datatype()
    _store_datatype_versions(datatypes, datatype, (published_datatype,))
    component_target = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="network_interface",
        description=None,
        abstract=False,
    )
    draft_target = ObjectTemplateVersion(
        template_id=component_target.id,
        version=1,
        status=ObjectTemplateVersionStatus.DRAFT,
        properties=(),
        components=(),
    )
    _store_object_template_versions(object_templates, component_target, (draft_target,))
    template = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="device",
        description=None,
        abstract=False,
    )
    draft = ObjectTemplateVersion(
        template_id=template.id,
        version=1,
        status=ObjectTemplateVersionStatus.DRAFT,
        properties=(
            ObjectTemplateProperty(
                name="hostname",
                datatype_id=datatype.id,
                datatype_version=published_datatype.version,
            ),
        ),
        components=(
            ObjectTemplateComponent(
                name="interfaces",
                template_id=component_target.id,
            ),
        ),
    )
    object_templates.add(template)
    object_templates.add_version(draft)

    with pytest.raises(ObjectTemplateComponentVersionNotPublished):
        service.publish_version(template_id=template.id, version=1)

    object_templates.replace_version(
        ObjectTemplateVersion(
            template_id=component_target.id,
            version=1,
            status=ObjectTemplateVersionStatus.DEPRECATED,
            properties=(),
            components=(),
        )
    )

    with pytest.raises(ObjectTemplateComponentVersionNotPublished):
        service.publish_version(template_id=template.id, version=1)

    missing_target_draft = ObjectTemplateVersion(
        template_id=template.id,
        version=2,
        status=ObjectTemplateVersionStatus.DRAFT,
        properties=(
            ObjectTemplateProperty(
                name="hostname",
                datatype_id=datatype.id,
                datatype_version=published_datatype.version,
            ),
        ),
        components=(
            ObjectTemplateComponent(
                name="interfaces",
                template_id=uuid4(),
            ),
        ),
    )
    object_templates.add_version(missing_target_draft)

    with pytest.raises(ObjectTemplateComponentVersionNotFound):
        service.publish_version(template_id=template.id, version=2)

    assert commits[0] == 0
    assert object_templates.get_version(template.id, 1) == draft
    assert object_templates.get_version(template.id, 2) == missing_target_draft


def test_publish_inherited_template_uses_exact_parent_lookup_and_validates_effective_datatypes(
) -> None:
    service, datatypes, object_templates, commits = _service()
    datatype, published_datatype = _published_datatype()
    _store_datatype_versions(datatypes, datatype, (published_datatype,))

    parent_template = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="base_device",
        description=None,
        abstract=False,
    )
    parent_version = _published_object_template_version(
        parent_template.id,
        properties=(
            ObjectTemplateProperty(
                name="hostname",
                datatype_id=datatype.id,
                datatype_version=published_datatype.version,
            ),
        ),
    )
    child_template = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="router",
        description=None,
        abstract=False,
    )
    child_draft = ObjectTemplateVersion(
        template_id=child_template.id,
        version=1,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=ObjectTemplateVersionRef(template_id=parent_template.id, version=1),
        properties=(
            ObjectTemplateProperty(
                name="serial",
                datatype_id=datatype.id,
                datatype_version=published_datatype.version,
            ),
        ),
    )
    object_templates.add(parent_template)
    object_templates.add_version(parent_version)
    object_templates.add(child_template)
    object_templates.add_version(child_draft)

    published = service.publish_version(template_id=child_template.id, version=1)

    assert commits[0] == 1
    assert published.status is ObjectTemplateVersionStatus.PUBLISHED
    assert (parent_template.id, 1) in object_templates.get_version_calls


def test_publish_inherited_component_target_validation_and_conflict_propagate() -> None:
    service, datatypes, object_templates, commits = _service()
    datatype, published_datatype = _published_datatype()
    _store_datatype_versions(datatypes, datatype, (published_datatype,))
    inherited_target = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="network_interface",
        description=None,
        abstract=True,
    )
    inherited_target_published = _published_object_template_version(inherited_target.id)
    _store_object_template_versions(
        object_templates,
        inherited_target,
        (inherited_target_published,),
    )

    parent_template = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="base_device",
        description=None,
        abstract=False,
    )
    parent_version = _published_object_template_version(
        parent_template.id,
        properties=(
            ObjectTemplateProperty(
                name="hostname",
                datatype_id=datatype.id,
                datatype_version=published_datatype.version,
            ),
        ),
        components=(
            ObjectTemplateComponent(
                name="interfaces",
                template_id=inherited_target.id,
            ),
        ),
    )
    child_template = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="router",
        description=None,
        abstract=False,
    )
    valid_child = ObjectTemplateVersion(
        template_id=child_template.id,
        version=1,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=ObjectTemplateVersionRef(template_id=parent_template.id, version=1),
        properties=(
            ObjectTemplateProperty(
                name="serial",
                datatype_id=datatype.id,
                datatype_version=published_datatype.version,
            ),
        ),
        components=(),
    )
    object_templates.add(parent_template)
    object_templates.add_version(parent_version)
    object_templates.add(child_template)
    object_templates.add_version(valid_child)

    object_templates.replace_version(
        ObjectTemplateVersion(
            template_id=inherited_target.id,
            version=1,
            status=ObjectTemplateVersionStatus.DEPRECATED,
            properties=(),
            components=(),
        )
    )

    with pytest.raises(ObjectTemplateComponentVersionNotPublished):
        service.publish_version(template_id=child_template.id, version=1)

    object_templates.replace_version(
        ObjectTemplateVersion(
            template_id=parent_template.id,
            version=1,
            status=ObjectTemplateVersionStatus.PUBLISHED,
            properties=parent_version.properties,
            components=(
                ObjectTemplateComponent(
                    name="interfaces",
                    template_id=uuid4(),
                ),
            ),
        )
    )

    with pytest.raises(ObjectTemplateComponentVersionNotFound):
        service.publish_version(template_id=child_template.id, version=1)

    object_templates.replace_version(parent_version)
    object_templates.replace_version(
        ObjectTemplateVersion(
            template_id=inherited_target.id,
            version=1,
            status=ObjectTemplateVersionStatus.PUBLISHED,
            properties=(),
            components=(),
        )
    )
    conflicting_child = ObjectTemplateVersion(
        template_id=child_template.id,
        version=2,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=ObjectTemplateVersionRef(template_id=parent_template.id, version=1),
        properties=(),
        components=(
            ObjectTemplateComponent(
                name="interfaces",
                template_id=inherited_target.id,
            ),
        ),
    )
    object_templates.add_version(conflicting_child)

    with pytest.raises(InheritedObjectTemplateComponentConflict):
        service.publish_version(template_id=child_template.id, version=2)

    assert commits[0] == 0


def test_publish_missing_or_non_published_datatype_blocks_publication() -> None:
    service, datatypes, object_templates, commits = _service()
    datatype, draft_datatype = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description=None,
        base_type="core.string",
    )
    _store_datatype_versions(datatypes, datatype, (draft_datatype,))
    template = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="device",
        description=None,
        abstract=False,
    )
    draft = ObjectTemplateVersion(
        template_id=template.id,
        version=1,
        status=ObjectTemplateVersionStatus.DRAFT,
        properties=(
            ObjectTemplateProperty(
                name="hostname",
                datatype_id=datatype.id,
                datatype_version=draft_datatype.version,
            ),
        ),
    )
    object_templates.add(template)
    object_templates.add_version(draft)

    with pytest.raises(ObjectTemplateDataTypeVersionNotPublished):
        service.publish_version(template_id=template.id, version=1)

    assert commits[0] == 0
    assert object_templates.get_version(template.id, 1) == draft


def test_publish_missing_parent_or_non_published_parent_blocks_publication() -> None:
    service, datatypes, object_templates, commits = _service()
    datatype, published_datatype = _published_datatype()
    _store_datatype_versions(datatypes, datatype, (published_datatype,))
    template = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="router",
        description=None,
        abstract=False,
    )
    missing_parent_draft = ObjectTemplateVersion(
        template_id=template.id,
        version=1,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=ObjectTemplateVersionRef(template_id=uuid4(), version=1),
        properties=(
            ObjectTemplateProperty(
                name="hostname",
                datatype_id=datatype.id,
                datatype_version=published_datatype.version,
            ),
        ),
    )
    object_templates.add(template)
    object_templates.add_version(missing_parent_draft)

    with pytest.raises(ObjectTemplateParentNotFound):
        service.publish_version(template_id=template.id, version=1)

    non_published_parent = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="base_device",
        description=None,
        abstract=False,
    )
    non_published_parent_version = ObjectTemplateVersion(
        template_id=non_published_parent.id,
        version=1,
        status=ObjectTemplateVersionStatus.DEPRECATED,
        properties=(),
    )
    blocked_child = ObjectTemplateVersion(
        template_id=template.id,
        version=2,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=ObjectTemplateVersionRef(template_id=non_published_parent.id, version=1),
        properties=(
            ObjectTemplateProperty(
                name="hostname",
                datatype_id=datatype.id,
                datatype_version=published_datatype.version,
            ),
        ),
    )
    object_templates.add(non_published_parent)
    object_templates.add_version(non_published_parent_version)
    object_templates.add_version(blocked_child)

    with pytest.raises(ObjectTemplateParentNotPublished):
        service.publish_version(template_id=template.id, version=2)

    assert commits[0] == 0


def test_publish_inheritance_resolver_failures_propagate_and_do_not_commit() -> None:
    service, datatypes, object_templates, commits = _service()
    datatype, published_datatype = _published_datatype()
    _store_datatype_versions(datatypes, datatype, (published_datatype,))

    parent_template = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="base_device",
        description=None,
        abstract=False,
    )
    parent_version = _published_object_template_version(
        parent_template.id,
        properties=(
            ObjectTemplateProperty(
                name="hostname",
                datatype_id=datatype.id,
                datatype_version=published_datatype.version,
            ),
        ),
    )
    child_template = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="router",
        description=None,
        abstract=False,
    )
    conflicting_draft = ObjectTemplateVersion(
        template_id=child_template.id,
        version=1,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=ObjectTemplateVersionRef(template_id=parent_template.id, version=1),
        properties=(
            ObjectTemplateProperty(
                name="hostname",
                datatype_id=datatype.id,
                datatype_version=published_datatype.version,
            ),
        ),
    )
    object_templates.add(parent_template)
    object_templates.add_version(parent_version)
    object_templates.add(child_template)
    object_templates.add_version(conflicting_draft)

    with pytest.raises(InheritedObjectTemplatePropertyConflict):
        service.publish_version(template_id=child_template.id, version=1)

    assert commits[0] == 0
    assert object_templates.get_version(child_template.id, 1) == conflicting_draft


def test_deprecate_replaces_snapshot_and_commits_once() -> None:
    service, _datatypes, object_templates, commits = _service()
    template = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="device",
        description=None,
        abstract=False,
    )
    published = ObjectTemplateVersion(
        template_id=template.id,
        version=1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        properties=(),
    )
    object_templates.add(template)
    object_templates.add_version(published)

    deprecated = service.deprecate_version(template_id=template.id, version=1)

    assert commits[0] == 1
    assert deprecated.status is ObjectTemplateVersionStatus.DEPRECATED
    assert object_templates.get_version(template.id, 1) == deprecated


def test_invalid_deprecate_transition_does_not_commit() -> None:
    service, _datatypes, object_templates, commits = _service()
    template = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="device",
        description=None,
        abstract=False,
    )
    draft = ObjectTemplateVersion(
        template_id=template.id,
        version=1,
        status=ObjectTemplateVersionStatus.DRAFT,
        properties=(),
    )
    object_templates.add(template)
    object_templates.add_version(draft)

    with pytest.raises(InvalidObjectTemplateVersionTransition):
        service.deprecate_version(template_id=template.id, version=1)

    assert commits[0] == 0


def test_objecttemplate_application_module_has_no_sqlalchemy_or_concrete_persistence_imports(
) -> None:
    path = Path("src/netauto/application/objecttemplate.py")
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    forbidden = (
        "sqlalchemy",
        "netauto.persistence",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith(forbidden), alias.name
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            assert not module.startswith(forbidden), module
