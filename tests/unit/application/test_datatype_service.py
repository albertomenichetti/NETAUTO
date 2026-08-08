from __future__ import annotations

from uuid import uuid4

import pytest

from netauto.application.datatype import DataTypeApplicationService
from netauto.application.unit_of_work import DataTypeUnitOfWork
from netauto.core.datatype import (
    Constraint,
    ConstraintName,
    DataTypeFactory,
    DataTypeNotFound,
    DataTypeVersioningService,
    DataTypeVersionNotFound,
    DataTypeVersionStatus,
)
from netauto.persistence.memory.datatype_repository import InMemoryDataTypeRepository


class FakeUnitOfWork(DataTypeUnitOfWork):
    def __init__(self, repo: InMemoryDataTypeRepository, commit_counter: list[int]) -> None:
        self._repo = repo
        self._commit_counter = commit_counter

    @property
    def datatypes(self) -> InMemoryDataTypeRepository:
        return self._repo

    def __enter__(self) -> FakeUnitOfWork:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    def commit(self) -> None:
        self._commit_counter[0] += 1


def _service() -> tuple[DataTypeApplicationService, InMemoryDataTypeRepository, list[int]]:
    repo = InMemoryDataTypeRepository()
    commit_counter = [0]

    def factory() -> FakeUnitOfWork:
        return FakeUnitOfWork(repo, commit_counter)

    return DataTypeApplicationService(factory), repo, commit_counter


def test_create_invokes_one_commit() -> None:
    service, repo, commits = _service()

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
    service, repo, commits = _service()
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
    service, repo, _ = _service()
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
    service, repo, commits = _service()
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
        base_type="core.string",
        constraints=(
            Constraint(name=ConstraintName.MIN_LENGTH, value=5),
            Constraint(name=ConstraintName.MAX_LENGTH, value=253),
        ),
    )
    published = service.publish_version(datatype_id=datatype.id, version=1)
    deprecated = service.deprecate_version(datatype_id=datatype.id, version=1)

    assert revised.status is DataTypeVersionStatus.DRAFT
    assert published.status is DataTypeVersionStatus.PUBLISHED
    assert deprecated.status is DataTypeVersionStatus.DEPRECATED
    assert repo.get_version(datatype.id, 1) == deprecated
    assert commits[0] == 3


def test_create_next_uses_exact_source_and_all_existing_versions() -> None:
    service, repo, commits = _service()
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


def test_mutation_does_not_commit_after_exception() -> None:
    service, _repo, commits = _service()

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
