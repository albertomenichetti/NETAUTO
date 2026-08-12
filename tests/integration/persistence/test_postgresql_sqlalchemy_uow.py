from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

import pytest
from sqlalchemy.orm import Session

from netauto.core.datatype import (
    DataType,
    DataTypeAlreadyExists,
    DataTypeFactory,
    DataTypeVersion,
)
from netauto.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork

pytestmark = pytest.mark.postgresql


class _ExpectedError(Exception):
    pass


def _datatype_pair(*, namespace: str, name: str) -> tuple[DataType, DataTypeVersion]:
    return DataTypeFactory().create(
        namespace=namespace,
        name=name,
        description=f"{namespace}.{name}",
        base_type="core.string",
    )


def _persist_pair(
    uow: SqlAlchemyUnitOfWork,
    *,
    datatype: DataType,
    version: DataTypeVersion,
) -> None:
    uow.datatypes.add(datatype)
    uow.datatypes.add_version(version)


def _load_pair(
    session_factory: Callable[[], Session],
    datatype_id: UUID,
) -> tuple[DataType | None, DataTypeVersion | None]:
    with SqlAlchemyUnitOfWork(session_factory) as uow:
        return (
            uow.datatypes.get(datatype_id),
            uow.datatypes.get_version(datatype_id, 1),
        )


def test_commit_persists(
    postgresql_clean_repository_session_factory: Callable[[], Session],
) -> None:
    datatype, version = _datatype_pair(namespace="network", name="hostname")

    with SqlAlchemyUnitOfWork(postgresql_clean_repository_session_factory) as uow:
        _persist_pair(uow, datatype=datatype, version=version)
        uow.commit()

    persisted_datatype, persisted_version = _load_pair(
        postgresql_clean_repository_session_factory,
        datatype.id,
    )
    assert persisted_datatype == datatype
    assert persisted_version == version


def test_exit_without_commit_rolls_back(
    postgresql_clean_repository_session_factory: Callable[[], Session],
) -> None:
    datatype, version = _datatype_pair(namespace="network", name="transient_hostname")

    with SqlAlchemyUnitOfWork(postgresql_clean_repository_session_factory) as uow:
        _persist_pair(uow, datatype=datatype, version=version)

    persisted_datatype, persisted_version = _load_pair(
        postgresql_clean_repository_session_factory,
        datatype.id,
    )
    assert persisted_datatype is None
    assert persisted_version is None


def test_exception_exit_rolls_back(
    postgresql_clean_repository_session_factory: Callable[[], Session],
) -> None:
    datatype, version = _datatype_pair(namespace="network", name="rolled_back_hostname")

    with pytest.raises(_ExpectedError, match="boom"):
        with SqlAlchemyUnitOfWork(postgresql_clean_repository_session_factory) as uow:
            _persist_pair(uow, datatype=datatype, version=version)
            raise _ExpectedError("boom")

    persisted_datatype, persisted_version = _load_pair(
        postgresql_clean_repository_session_factory,
        datatype.id,
    )
    assert persisted_datatype is None
    assert persisted_version is None


def test_commit_then_later_uncommitted_work_persists_only_first_transaction(
    postgresql_clean_repository_session_factory: Callable[[], Session],
) -> None:
    first_datatype, first_version = _datatype_pair(namespace="network", name="first_hostname")
    second_datatype, second_version = _datatype_pair(namespace="network", name="second_hostname")

    with SqlAlchemyUnitOfWork(postgresql_clean_repository_session_factory) as uow:
        _persist_pair(uow, datatype=first_datatype, version=first_version)
        uow.commit()

        _persist_pair(uow, datatype=second_datatype, version=second_version)

    persisted_first, persisted_first_version = _load_pair(
        postgresql_clean_repository_session_factory,
        first_datatype.id,
    )
    persisted_second, persisted_second_version = _load_pair(
        postgresql_clean_repository_session_factory,
        second_datatype.id,
    )
    assert persisted_first == first_datatype
    assert persisted_first_version == first_version
    assert persisted_second is None
    assert persisted_second_version is None


def test_two_explicit_commits_persist_both_transactions(
    postgresql_clean_repository_session_factory: Callable[[], Session],
) -> None:
    first_datatype, first_version = _datatype_pair(namespace="network", name="multi_first")
    second_datatype, second_version = _datatype_pair(namespace="network", name="multi_second")

    with SqlAlchemyUnitOfWork(postgresql_clean_repository_session_factory) as uow:
        _persist_pair(uow, datatype=first_datatype, version=first_version)
        uow.commit()

        _persist_pair(uow, datatype=second_datatype, version=second_version)
        uow.commit()

    persisted_first, persisted_first_version = _load_pair(
        postgresql_clean_repository_session_factory,
        first_datatype.id,
    )
    persisted_second, persisted_second_version = _load_pair(
        postgresql_clean_repository_session_factory,
        second_datatype.id,
    )
    assert persisted_first == first_datatype
    assert persisted_first_version == first_version
    assert persisted_second == second_datatype
    assert persisted_second_version == second_version


def test_failed_repository_operation_rolls_back_whole_uow_transaction(
    postgresql_clean_repository_session_factory: Callable[[], Session],
) -> None:
    first_datatype, first_version = _datatype_pair(namespace="network", name="duplicate_candidate")
    duplicate_datatype, _ = _datatype_pair(namespace="network", name="duplicate_candidate")

    with pytest.raises(DataTypeAlreadyExists):
        with SqlAlchemyUnitOfWork(postgresql_clean_repository_session_factory) as uow:
            _persist_pair(uow, datatype=first_datatype, version=first_version)
            uow.datatypes.add(duplicate_datatype)

    persisted_datatype, persisted_version = _load_pair(
        postgresql_clean_repository_session_factory,
        first_datatype.id,
    )
    assert persisted_datatype is None
    assert persisted_version is None
