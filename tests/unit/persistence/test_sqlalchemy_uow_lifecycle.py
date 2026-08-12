from __future__ import annotations

from collections.abc import Callable
from typing import cast

import pytest
from sqlalchemy.orm import Session

from netauto.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork


class _ExpectedError(Exception):
    pass


class _SpySession:
    def __init__(self) -> None:
        self.commit_calls = 0
        self.rollback_calls = 0
        self.close_calls = 0
        self._in_transaction = True

    def commit(self) -> None:
        self.commit_calls += 1
        self._in_transaction = False

    def rollback(self) -> None:
        self.rollback_calls += 1
        self._in_transaction = False

    def close(self) -> None:
        self.close_calls += 1

    def in_transaction(self) -> bool:
        return self._in_transaction


class _FailAfterSessionCreatedUoW(SqlAlchemyUnitOfWork):
    def _after_session_created(self) -> None:
        raise _ExpectedError("after-session-created failed")


class _FailInitializeRepositoriesUoW(SqlAlchemyUnitOfWork):
    def _initialize_repositories(self) -> None:
        raise _ExpectedError("initialize-repositories failed")


def _session_factory(session: _SpySession) -> Callable[[], Session]:
    return cast("Callable[[], Session]", lambda: session)


def test_clean_exit_after_explicit_commit_does_not_call_rollback() -> None:
    session = _SpySession()
    uow = SqlAlchemyUnitOfWork(_session_factory(session))

    with uow:
        uow.commit()

    assert session.commit_calls == 1
    assert session.rollback_calls == 0
    assert session.close_calls == 1


def test_clean_exit_without_commit_rolls_back_and_closes() -> None:
    session = _SpySession()
    uow = SqlAlchemyUnitOfWork(_session_factory(session))

    with uow:
        pass

    assert session.commit_calls == 0
    assert session.rollback_calls == 1
    assert session.close_calls == 1


def test_exception_exit_rolls_back_closes_and_propagates() -> None:
    session = _SpySession()
    uow = SqlAlchemyUnitOfWork(_session_factory(session))

    with pytest.raises(_ExpectedError, match="boom"):
        with uow:
            raise _ExpectedError("boom")

    assert session.commit_calls == 0
    assert session.rollback_calls == 1
    assert session.close_calls == 1


@pytest.mark.parametrize(
    "uow_class",
    [_FailAfterSessionCreatedUoW, _FailInitializeRepositoriesUoW],
)
def test_enter_initialization_failure_closes_session_and_leaves_uow_inactive(
    uow_class: type[SqlAlchemyUnitOfWork],
) -> None:
    session = _SpySession()
    uow = uow_class(_session_factory(session))

    with pytest.raises(_ExpectedError):
        with uow:
            pass

    assert session.close_calls == 1
    assert session.commit_calls == 0
    assert session.rollback_calls == 0
    with pytest.raises(RuntimeError, match="Unit of work is not active\\."):
        uow.commit()


def test_commit_outside_active_context_raises() -> None:
    uow = SqlAlchemyUnitOfWork(_session_factory(_SpySession()))

    with pytest.raises(RuntimeError, match="Unit of work is not active\\."):
        uow.commit()
