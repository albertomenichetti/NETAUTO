from __future__ import annotations

import threading
from collections.abc import Callable
from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

import pytest
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from netauto.application.objecttemplate import ObjectTemplateApplicationService
from netauto.application.unit_of_work import ModelWriteUnavailable
from netauto.core.datatype import DataType
from netauto.core.object import ObjectChange, ObjectChangeKind, ObjectChangeSnapshot
from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateVersion,
    ObjectTemplateVersionStatus,
)
from netauto.persistence.sqlalchemy.unit_of_work import (
    PostgresqlModelWriteUnitOfWork,
    SqlAlchemyUnitOfWork,
)

pytestmark = pytest.mark.postgresql


def _template(
    *,
    template_id: UUID | None = None,
    name: str = "device",
) -> ObjectTemplate:
    return ObjectTemplate(
        id=template_id or uuid4(),
        namespace="network",
        name=name,
        description=None,
        abstract=False,
    )


def _draft_version(template_id: UUID, *, version: int = 1) -> ObjectTemplateVersion:
    return ObjectTemplateVersion(
        template_id=template_id,
        version=version,
        status=ObjectTemplateVersionStatus.DRAFT,
    )


def _object_change(*, object_id: UUID | None = None) -> ObjectChange:
    template_id = uuid4()
    return ObjectChange(
        id=uuid4(),
        object_id=object_id or uuid4(),
        occurred_at=datetime(2026, 8, 12, 12, 0, tzinfo=UTC),
        kind=ObjectChangeKind.CREATED,
        before=None,
        after=ObjectChangeSnapshot(
            template_id=template_id,
            template_version=1,
            properties={"hostname": "router-01"},
        ),
    )


class _TrackingPostgresqlModelWriteUnitOfWork(PostgresqlModelWriteUnitOfWork):
    def __init__(
        self,
        session_factory: Callable[[], Session],
        *,
        max_guard_attempts: int = 2,
        retry_delay_seconds: float = 0.0,
        sleeper: Callable[[float], None] = lambda _delay: None,
        backend_pids: list[int] | None = None,
        attempt_results: list[bool] | None = None,
        initialized_event: threading.Event | None = None,
    ) -> None:
        super().__init__(
            session_factory,
            max_guard_attempts=max_guard_attempts,
            retry_delay_seconds=retry_delay_seconds,
            sleeper=sleeper,
        )
        self._backend_pids = backend_pids if backend_pids is not None else []
        self._attempt_results = attempt_results if attempt_results is not None else []
        self._initialized_event = initialized_event

    def _try_acquire_model_plane_guard(self) -> bool:
        assert self._session is not None
        backend_pid = cast(int, self._session.execute(text("SELECT pg_backend_pid()")).scalar_one())
        if backend_pid not in self._backend_pids:
            self._backend_pids.append(backend_pid)
        acquired = super()._try_acquire_model_plane_guard()
        self._attempt_results.append(acquired)
        return acquired

    def _initialize_repositories(self) -> None:
        if self._initialized_event is not None:
            self._initialized_event.set()
        super()._initialize_repositories()


def test_postgresql_model_plane_guard_acquires_before_repository_reads(
    postgresql_engine: Engine,
    postgresql_repository_session_factory: Callable[[], Session],
) -> None:
    statements: list[str] = []

    def capture_sql(_conn, _cursor, statement, _parameters, _context, _executemany) -> None:
        statements.append(statement)

    event.listen(postgresql_engine, "before_cursor_execute", capture_sql)
    try:
        with PostgresqlModelWriteUnitOfWork(postgresql_repository_session_factory) as uow:
            uow.object_templates.list()
    finally:
        event.remove(postgresql_engine, "before_cursor_execute", capture_sql)

    advisory_index = next(
        index
        for index, statement in enumerate(statements)
        if "pg_try_advisory_xact_lock" in statement
    )
    repository_select_index = next(
        index
        for index, statement in enumerate(statements)
        if statement.lstrip().upper().startswith("SELECT")
        and "FROM object_templates" in statement
    )
    assert advisory_index < repository_select_index


def test_postgresql_model_plane_guard_serializes_real_model_writers(
    postgresql_repository_session_factory: Callable[[], Session],
) -> None:
    contention_observed = threading.Event()
    allow_retry = threading.Event()
    writer_b_entered = threading.Event()
    writer_b_initialized = threading.Event()
    writer_b_finished = threading.Event()
    writer_b_errors: list[BaseException] = []
    writer_a_backend_pids: list[int] = []
    writer_b_backend_pids: list[int] = []
    writer_b_attempt_results: list[bool] = []
    persisted_datatype_id = uuid4()

    def sleeper(_delay: float) -> None:
        contention_observed.set()
        assert allow_retry.wait(timeout=5.0)

    def writer_b() -> None:
        try:
            with _TrackingPostgresqlModelWriteUnitOfWork(
                postgresql_repository_session_factory,
                max_guard_attempts=2,
                retry_delay_seconds=0.0,
                sleeper=sleeper,
                backend_pids=writer_b_backend_pids,
                attempt_results=writer_b_attempt_results,
                initialized_event=writer_b_initialized,
            ) as contender:
                writer_b_entered.set()
                contender.datatypes.add(
                    DataType(
                        id=persisted_datatype_id,
                        namespace="network",
                        name="guarded_type",
                        description=None,
                    )
                )
                contender.commit()
        except BaseException as error:  # pragma: no cover - propagated in assertion path
            writer_b_errors.append(error)
        finally:
            writer_b_finished.set()

    with _TrackingPostgresqlModelWriteUnitOfWork(
        postgresql_repository_session_factory,
        backend_pids=writer_a_backend_pids,
    ) as writer_a:
        thread = threading.Thread(target=writer_b, name="postgresql-model-writer-b")
        thread.start()
        assert contention_observed.wait(timeout=5.0)
        assert writer_b_entered.is_set() is False
        assert writer_b_initialized.is_set() is False
        writer_a.object_templates.list()

    allow_retry.set()
    assert writer_b_finished.wait(timeout=5.0)
    thread.join(timeout=5.0)
    assert not thread.is_alive()
    assert writer_b_errors == []
    assert writer_b_entered.is_set() is True
    assert writer_b_initialized.is_set() is True
    assert writer_b_attempt_results == [False, True]
    assert len(writer_a_backend_pids) == 1
    assert len(writer_b_backend_pids) == 1
    assert writer_a_backend_pids[0] != writer_b_backend_pids[0]

    with SqlAlchemyUnitOfWork(postgresql_repository_session_factory) as verifier:
        persisted = verifier.datatypes.get(persisted_datatype_id)
        assert persisted is not None


def test_postgresql_model_plane_guard_exhausts_contention_and_cleans_up_session(
    postgresql_repository_session_factory: Callable[[], Session],
) -> None:
    initialized = threading.Event()
    closed_sessions: list[Session] = []

    def tracking_factory() -> Session:
        session = postgresql_repository_session_factory()
        original_close = session.close

        def close() -> None:
            closed_sessions.append(session)
            original_close()

        session.close = close  # type: ignore[method-assign]
        return session

    with PostgresqlModelWriteUnitOfWork(postgresql_repository_session_factory):
        contender = _TrackingPostgresqlModelWriteUnitOfWork(
            tracking_factory,
            max_guard_attempts=1,
            retry_delay_seconds=0.0,
            initialized_event=initialized,
        )
        with pytest.raises(ModelWriteUnavailable):
            contender.__enter__()

        assert initialized.is_set() is False
        assert contender._session is None
        assert len(closed_sessions) == 1

    with PostgresqlModelWriteUnitOfWork(postgresql_repository_session_factory) as retrying:
        retrying.object_templates.list()


def test_postgresql_model_plane_guard_releases_on_commit_without_manual_unlock(
    postgresql_repository_session_factory: Callable[[], Session],
) -> None:
    with PostgresqlModelWriteUnitOfWork(postgresql_repository_session_factory) as first:
        first.commit()
        with PostgresqlModelWriteUnitOfWork(postgresql_repository_session_factory) as second:
            second.object_templates.list()


def test_postgresql_model_plane_guard_releases_on_rollback_without_manual_unlock(
    postgresql_repository_session_factory: Callable[[], Session],
) -> None:
    with pytest.raises(RuntimeError):
        with PostgresqlModelWriteUnitOfWork(postgresql_repository_session_factory):
            raise RuntimeError("abort")

    with PostgresqlModelWriteUnitOfWork(postgresql_repository_session_factory) as second:
        second.object_templates.list()


def test_postgresql_model_plane_guard_does_not_block_ordinary_data_writer(
    postgresql_repository_session_factory: Callable[[], Session],
) -> None:
    change = _object_change()

    with PostgresqlModelWriteUnitOfWork(postgresql_repository_session_factory):
        with SqlAlchemyUnitOfWork(postgresql_repository_session_factory) as ordinary_writer:
            ordinary_writer.object_changes.add(change)
            ordinary_writer.commit()

        with SqlAlchemyUnitOfWork(postgresql_repository_session_factory) as verifier:
            assert verifier.object_changes.list_by_object(change.object_id) == (change,)


def test_postgresql_object_template_publish_acquires_guard_before_decision_reads(
    postgresql_engine: Engine,
    postgresql_repository_session_factory: Callable[[], Session],
) -> None:
    def ordinary_factory() -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(postgresql_repository_session_factory)

    def model_factory() -> PostgresqlModelWriteUnitOfWork:
        return PostgresqlModelWriteUnitOfWork(postgresql_repository_session_factory)

    service = ObjectTemplateApplicationService(
        ordinary_factory,
        model_write_uow_factory=model_factory,
    )
    template = _template(
        template_id=UUID("00000000-0000-0000-0000-0000000008a1"),
        name="service_template",
    )
    statements: list[str] = []

    def capture_sql(_conn, _cursor, statement, _parameters, _context, _executemany) -> None:
        statements.append(statement)

    event.listen(postgresql_engine, "before_cursor_execute", capture_sql)
    try:
        with ordinary_factory() as uow:
            uow.object_templates.add(template)
            uow.object_templates.add_version(_draft_version(template.id))
            uow.commit()

        statements.clear()
        service.publish_version(template_id=template.id, version=1)
    finally:
        event.remove(postgresql_engine, "before_cursor_execute", capture_sql)

    advisory_index = next(
        index
        for index, statement in enumerate(statements)
        if "pg_try_advisory_xact_lock" in statement
    )
    repository_select_index = next(
        index
        for index, statement in enumerate(statements)
        if statement.lstrip().upper().startswith("SELECT")
        and (
            "FROM object_template_versions" in statement
            or "FROM object_templates" in statement
        )
    )
    assert advisory_index < repository_select_index
