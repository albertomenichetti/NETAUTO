from __future__ import annotations

from uuid import uuid4

import pytest

from netauto.application.datatype import DataTypeApplicationService
from netauto.application.unit_of_work import DataTypeUnitOfWork
from netauto.core.datatype import (
    Constraint,
    ConstraintName,
    DataTypeFactory,
    DataTypeInUse,
    DataTypeNotFound,
    DataTypeVersioningService,
    DataTypeVersionNotFound,
    DataTypeVersionStatus,
    InvalidDataTypeVersionTransition,
)
from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateProperty,
    ObjectTemplateVersion,
    ObjectTemplateVersionStatus,
)
from netauto.persistence.memory.datatype_repository import InMemoryDataTypeRepository
from netauto.persistence.memory.objecttemplate_repository import InMemoryObjectTemplateRepository


class FakeUnitOfWork(DataTypeUnitOfWork):
    def __init__(
        self,
        repo: InMemoryDataTypeRepository,
        object_templates: InMemoryObjectTemplateRepository,
        commit_counter: list[int],
    ) -> None:
        self._repo = repo
        self._object_templates = object_templates
        self._commit_counter = commit_counter

    @property
    def datatypes(self) -> InMemoryDataTypeRepository:
        return self._repo

    @property
    def object_templates(self) -> InMemoryObjectTemplateRepository:
        return self._object_templates

    def __enter__(self) -> FakeUnitOfWork:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    def commit(self) -> None:
        self._commit_counter[0] += 1


def _service() -> tuple[
    DataTypeApplicationService,
    InMemoryDataTypeRepository,
    InMemoryObjectTemplateRepository,
    list[int],
]:
    repo = InMemoryDataTypeRepository()
    object_templates = InMemoryObjectTemplateRepository()
    commit_counter = [0]

    def factory() -> FakeUnitOfWork:
        return FakeUnitOfWork(repo, object_templates, commit_counter)

    return (
        DataTypeApplicationService(
            factory,
            model_write_uow_factory=factory,
        ),
        repo,
        object_templates,
        commit_counter,
    )


def test_create_invokes_one_commit() -> None:
    service, repo, _object_templates, commits = _service()

    datatype, version = service.create_datatype(
        namespace="network",
        name="hostname",
        description="Network hostname",
        base_type="core.string",
        constraints=(Constraint(name=ConstraintName.MIN_LENGTH, value=1),),
    )

    assert commits[0] == 1
    assert repo.get(datatype.id) == datatype
    assert repo.get_version(datatype.id, 1) == version


def test_reads_do_not_commit() -> None:
    service, repo, _object_templates, commits = _service()
    datatype, version = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description="Network hostname",
        base_type="core.string",
    )
    repo.add(datatype)
    repo.add_version(version)

    assert service.list_datatypes() == (datatype,)
    assert service.get_datatype(datatype.id) == datatype
    assert service.get_datatype_by_name("network", "hostname") == datatype
    assert service.list_versions(datatype.id) == (version,)
    assert service.get_version(datatype.id, 1) == version
    assert commits[0] == 0


def test_missing_datatype_and_version_become_focused_exceptions() -> None:
    service, repo, _object_templates, _ = _service()
    datatype, version = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description="Network hostname",
        base_type="core.string",
    )
    repo.add(datatype)

    with pytest.raises(DataTypeNotFound):
        service.get_datatype(uuid4())
    with pytest.raises(DataTypeNotFound):
        service.list_versions(uuid4())
    with pytest.raises(DataTypeVersionNotFound):
        service.get_version(datatype.id, version.version)


def test_revise_publish_deprecate_replace_and_commit() -> None:
    service, repo, _object_templates, commits = _service()
    datatype, draft = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description="Network hostname",
        base_type="core.string",
        constraints=(Constraint(name=ConstraintName.MIN_LENGTH, value=1),),
    )
    repo.add(datatype)
    repo.add_version(draft)

    revised = service.revise_version(
        datatype_id=datatype.id,
        version=1,
        constraints=(
            Constraint(name=ConstraintName.MIN_LENGTH, value=5),
            Constraint(name=ConstraintName.MAX_LENGTH, value=253),
        ),
    )
    published = service.publish_version(datatype_id=datatype.id, version=1)
    deprecated = service.deprecate_version(datatype_id=datatype.id, version=1)

    assert revised.status is DataTypeVersionStatus.DRAFT
    assert revised.base_type == draft.base_type
    assert published.status is DataTypeVersionStatus.PUBLISHED
    assert deprecated.status is DataTypeVersionStatus.DEPRECATED
    assert repo.get_version(datatype.id, 1) == deprecated
    assert commits[0] == 3


def test_create_next_uses_exact_source_and_all_existing_versions() -> None:
    service, repo, _object_templates, commits = _service()
    datatype, v1_draft = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description="Network hostname",
        base_type="core.string",
        constraints=(Constraint(name=ConstraintName.MIN_LENGTH, value=1),),
    )
    versioning = DataTypeVersioningService()
    v1_published = versioning.publish(v1_draft)
    v2_published = versioning.publish(
        DataTypeVersioningService().create_next_version(
            v1_published,
            existing_versions=(v1_published,),
        )
    )
    v3_published = versioning.publish(
        DataTypeVersioningService().create_next_version(
            v2_published,
            existing_versions=(v1_published, v2_published),
        )
    )
    v5_deprecated = versioning.deprecate(v3_published)
    v5_deprecated = type(v5_deprecated)(
        datatype_id=v5_deprecated.datatype_id,
        version=5,
        status=v5_deprecated.status,
        base_type=v5_deprecated.base_type,
        constraints=v5_deprecated.constraints,
    )

    repo.add(datatype)
    repo.add_version(v1_published)
    repo.add_version(v2_published)
    repo.add_version(v5_deprecated)

    next_version = service.create_next_version(datatype_id=datatype.id, source_version=1)

    assert next_version.version == 6
    assert next_version.status is DataTypeVersionStatus.DRAFT
    assert next_version.constraints == v1_published.constraints
    assert commits[0] == 1


def test_create_next_accepts_deprecated_source_and_commits_once() -> None:
    service, repo, _object_templates, commits = _service()
    datatype, v1_draft = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description="Network hostname",
        base_type="core.string",
        constraints=(Constraint(name=ConstraintName.MIN_LENGTH, value=1),),
    )
    versioning = DataTypeVersioningService()
    v1_published = versioning.publish(v1_draft)
    v2_draft = versioning.create_next_version(v1_published, existing_versions=(v1_published,))
    v2_published = versioning.publish(v2_draft)
    v1_deprecated = versioning.deprecate(v1_published)
    v2_deprecated = versioning.deprecate(v2_published)

    repo.add(datatype)
    repo.add_version(v1_deprecated)
    repo.add_version(v2_deprecated)

    next_version = service.create_next_version(datatype_id=datatype.id, source_version=2)

    assert next_version.version == 3
    assert next_version.status is DataTypeVersionStatus.DRAFT
    assert next_version.base_type == v2_deprecated.base_type
    assert next_version.constraints == v2_deprecated.constraints
    assert repo.get_version(datatype.id, 2) == v2_deprecated
    assert commits[0] == 1


def test_create_next_from_draft_source_raises_without_commit() -> None:
    service, repo, _object_templates, commits = _service()
    datatype, draft = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description="Network hostname",
        base_type="core.string",
        constraints=(Constraint(name=ConstraintName.MIN_LENGTH, value=1),),
    )
    repo.add(datatype)
    repo.add_version(draft)

    with pytest.raises(InvalidDataTypeVersionTransition):
        service.create_next_version(datatype_id=datatype.id, source_version=1)

    assert commits[0] == 0

def test_mutation_does_not_commit_after_exception() -> None:
    service, _repo, _object_templates, commits = _service()

    service.create_datatype(
        namespace="network",
        name="hostname",
        description=None,
        base_type="core.string",
        constraints=(),
    )

    with pytest.raises(Exception):
        service.create_datatype(
            namespace="network",
            name="hostname",
            description=None,
            base_type="core.string",
            constraints=(),
        )

    assert commits[0] == 1


def test_delete_missing_datatype_raises_without_commit() -> None:
    service, _repo, _object_templates, commits = _service()

    with pytest.raises(DataTypeNotFound):
        service.delete_datatype(uuid4())

    assert commits[0] == 0


def test_delete_unreferenced_datatype_removes_identity_and_all_versions() -> None:
    service, repo, _object_templates, commits = _service()
    datatype, draft = DataTypeFactory().create(
        namespace="common",
        name="email",
        description="Email address",
        base_type="core.string",
        constraints=(),
    )
    versioning = DataTypeVersioningService()
    published = versioning.publish(draft)
    next_draft = versioning.create_next_version(published, existing_versions=(published,))
    deprecated = versioning.deprecate(published)
    deprecated = type(deprecated)(
        datatype_id=deprecated.datatype_id,
        version=3,
        status=deprecated.status,
        base_type=deprecated.base_type,
        constraints=deprecated.constraints,
    )
    repo.add(datatype)
    repo.add_version(draft)
    repo.add_version(next_draft)
    repo.add_version(deprecated)

    service.delete_datatype(datatype.id)

    assert repo.get(datatype.id) is None
    assert repo.list_versions(datatype.id) == ()
    assert commits[0] == 1


@pytest.mark.parametrize("status", list(ObjectTemplateVersionStatus))
def test_delete_referenced_datatype_is_blocked_for_all_template_statuses(
    status: ObjectTemplateVersionStatus,
) -> None:
    service, repo, object_templates, commits = _service()
    datatype, version = DataTypeFactory().create(
        namespace="common",
        name="email",
        description="Email address",
        base_type="core.string",
        constraints=(),
    )
    repo.add(datatype)
    repo.add_version(version)
    template = ObjectTemplate(id=uuid4(), namespace="network", name=f"device_{status.value}")
    template_version = ObjectTemplateVersion(
        template_id=template.id,
        version=1,
        status=status,
        properties=(
            ObjectTemplateProperty(
                name="email",
                datatype_id=datatype.id,
                datatype_version=1,
                required=False,
            ),
        ),
    )
    object_templates.add(template)
    object_templates.add_version(template_version)

    with pytest.raises(DataTypeInUse):
        service.delete_datatype(datatype.id)

    assert repo.get(datatype.id) == datatype
    assert repo.list_versions(datatype.id) == (version,)
    assert commits[0] == 0


def test_delete_referenced_datatype_is_blocked_for_older_referenced_version() -> None:
    service, repo, object_templates, commits = _service()
    datatype, v1 = DataTypeFactory().create(
        namespace="common",
        name="email",
        description="Email address",
        base_type="core.string",
        constraints=(),
    )
    published_v1 = DataTypeVersioningService().publish(v1)
    v2 = DataTypeVersioningService().create_next_version(
        published_v1,
        existing_versions=(published_v1,),
    )
    repo.add(datatype)
    repo.add_version(v1)
    repo.add_version(v2)
    template = ObjectTemplate(id=uuid4(), namespace="network", name="device")
    template_version = ObjectTemplateVersion(
        template_id=template.id,
        version=1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        properties=(
            ObjectTemplateProperty(
                name="email",
                datatype_id=datatype.id,
                datatype_version=1,
                required=False,
            ),
        ),
    )
    object_templates.add(template)
    object_templates.add_version(template_version)

    with pytest.raises(DataTypeInUse):
        service.delete_datatype(datatype.id)

    assert repo.list_versions(datatype.id) == (v1, v2)
    assert commits[0] == 0


def test_delete_unrelated_datatype_ignores_other_template_references() -> None:
    service, repo, object_templates, commits = _service()
    datatype_a, version_a = DataTypeFactory().create(
        namespace="common",
        name="email",
        description="Email address",
        base_type="core.string",
        constraints=(),
    )
    datatype_b, version_b = DataTypeFactory().create(
        namespace="common",
        name="hostname",
        description="Hostname",
        base_type="core.string",
        constraints=(),
    )
    repo.add(datatype_a)
    repo.add_version(version_a)
    repo.add(datatype_b)
    repo.add_version(version_b)
    template = ObjectTemplate(id=uuid4(), namespace="network", name="device")
    template_version = ObjectTemplateVersion(
        template_id=template.id,
        version=1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        properties=(
            ObjectTemplateProperty(
                name="hostname",
                datatype_id=datatype_b.id,
                datatype_version=1,
                required=False,
            ),
        ),
    )
    object_templates.add(template)
    object_templates.add_version(template_version)

    service.delete_datatype(datatype_a.id)

    assert repo.get(datatype_a.id) is None
    assert repo.get(datatype_b.id) == datatype_b
    assert commits[0] == 1
