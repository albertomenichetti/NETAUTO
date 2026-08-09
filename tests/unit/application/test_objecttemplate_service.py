from __future__ import annotations

import ast
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from netauto.application.objecttemplate import (
    ObjectTemplateApplicationService,
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
    InheritedObjectTemplatePropertyConflict,
    InvalidObjectTemplateVersionTransition,
    ObjectTemplate,
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

    def get_version(self, template_id: UUID, version: int) -> ObjectTemplateVersion | None:
        self.get_version_calls.append((template_id, version))
        return super().get_version(template_id, version)


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


def _published_object_template_version(
    template_id: UUID,
    *,
    parent: ObjectTemplateVersionRef | None = None,
    properties: tuple[ObjectTemplateProperty, ...] = (),
) -> ObjectTemplateVersion:
    return ObjectTemplateVersion(
        template_id=template_id,
        version=1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        parent=parent,
        properties=properties,
    )


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
