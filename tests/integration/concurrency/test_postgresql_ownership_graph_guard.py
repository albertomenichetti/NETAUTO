from __future__ import annotations

import threading
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from netauto.application.object import ObjectApplicationService
from netauto.application.unit_of_work import OwnershipGraphWriteUnavailable
from netauto.core.object import (
    ComponentMembership,
    Object,
    ObjectChange,
    ObjectChangeKind,
    ObjectChangeSnapshot,
)
from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateComponent,
    ObjectTemplateVersion,
    ObjectTemplateVersionStatus,
)
from netauto.persistence.sqlalchemy.unit_of_work import (
    PostgresqlModelWriteUnitOfWork,
    PostgresqlOwnershipGraphWriteUnitOfWork,
    SqlAlchemyUnitOfWork,
)

pytestmark = pytest.mark.postgresql


def _is_ownership_guard_attempt(statement: str, parameters: object) -> bool:
    return "pg_try_advisory_xact_lock" in statement and (
        parameters == {"namespace_key": 0x4E455441, "guard_key": 2}
        or parameters == (0x4E455441, 2)
    )


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


def _template_version(
    template_id: UUID,
    *,
    version: int = 1,
    status: ObjectTemplateVersionStatus = ObjectTemplateVersionStatus.DRAFT,
    components: tuple[ObjectTemplateComponent, ...] = (),
) -> ObjectTemplateVersion:
    return ObjectTemplateVersion(
        template_id=template_id,
        version=version,
        status=status,
        components=components,
    )


def _object(
    *,
    object_id: UUID | None = None,
    template_id: UUID,
    template_version: int = 1,
) -> Object:
    return Object(
        id=object_id or uuid4(),
        template_id=template_id,
        template_version=template_version,
        properties={},
    )


def _object_change(*, object_id: UUID | None = None) -> ObjectChange:
    template_id = uuid4()
    return ObjectChange(
        id=uuid4(),
        object_id=object_id or uuid4(),
        occurred_at=datetime(2026, 8, 12, 12, 30, tzinfo=UTC),
        kind=ObjectChangeKind.CREATED,
        before=None,
        after=ObjectChangeSnapshot(
            template_id=template_id,
            template_version=1,
            properties={"hostname": "router-01"},
        ),
    )


def _seed_parent_child_graph(
    ordinary_factory: Callable[[], Session],
    *,
    parent_id: UUID | None = None,
    child_id: UUID | None = None,
    slot_name: str = "children",
) -> tuple[UUID, UUID, UUID, str]:
    template_id = uuid4()
    parent_object = _object(object_id=parent_id, template_id=template_id)
    child_object = _object(object_id=child_id, template_id=template_id)

    with SqlAlchemyUnitOfWork(ordinary_factory) as uow:
        template = _template(template_id=template_id, name=f"template_{template_id.hex[:8]}")
        uow.object_templates.add(template)
        uow.object_templates.add_version(
            _template_version(
                template.id,
                components=(ObjectTemplateComponent(name=slot_name, template_id=template.id),),
            )
        )
        uow.objects.add(parent_object)
        uow.objects.add(child_object)
        uow.commit()

    return template_id, parent_object.id, child_object.id, slot_name


class _TrackingPostgresqlOwnershipGraphWriteUnitOfWork(PostgresqlOwnershipGraphWriteUnitOfWork):
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

    def _try_acquire_ownership_graph_guard(self) -> bool:
        assert self._session is not None
        backend_pid = int(self._session.execute(text("SELECT pg_backend_pid()")).scalar_one())
        if backend_pid not in self._backend_pids:
            self._backend_pids.append(backend_pid)
        acquired = super()._try_acquire_ownership_graph_guard()
        self._attempt_results.append(acquired)
        return acquired

    def _initialize_repositories(self) -> None:
        if self._initialized_event is not None:
            self._initialized_event.set()
        super()._initialize_repositories()


def test_postgresql_ownership_graph_guard_acquires_before_repository_reads(
    postgresql_engine: Engine,
    postgresql_repository_session_factory: Callable[[], Session],
) -> None:
    statements: list[tuple[str, object]] = []

    def capture_sql(_conn, _cursor, statement, parameters, _context, _executemany) -> None:
        statements.append((statement, parameters))

    event.listen(postgresql_engine, "before_cursor_execute", capture_sql)
    try:
        with PostgresqlOwnershipGraphWriteUnitOfWork(postgresql_repository_session_factory) as uow:
            uow.objects.list()
    finally:
        event.remove(postgresql_engine, "before_cursor_execute", capture_sql)

    advisory_index = next(
        index
        for index, (statement, parameters) in enumerate(statements)
        if _is_ownership_guard_attempt(statement, parameters)
    )
    repository_select_index = next(
        index
        for index, (statement, _parameters) in enumerate(statements)
        if statement.lstrip().upper().startswith("SELECT")
        and "FROM objects" in statement
    )
    assert advisory_index < repository_select_index


def test_postgresql_ownership_graph_guard_serializes_real_ownership_writers(
    postgresql_repository_session_factory: Callable[[], Session],
) -> None:
    template_id, parent_id, child_id, slot_name = _seed_parent_child_graph(
        postgresql_repository_session_factory
    )
    contention_observed = threading.Event()
    allow_retry = threading.Event()
    writer_b_entered = threading.Event()
    writer_b_initialized = threading.Event()
    writer_b_finished = threading.Event()
    writer_b_errors: list[BaseException] = []
    writer_a_backend_pids: list[int] = []
    writer_b_backend_pids: list[int] = []
    writer_b_attempt_results: list[bool] = []

    def sleeper(_delay: float) -> None:
        contention_observed.set()
        assert allow_retry.wait(timeout=5.0)

    def writer_b() -> None:
        try:
            with _TrackingPostgresqlOwnershipGraphWriteUnitOfWork(
                postgresql_repository_session_factory,
                max_guard_attempts=2,
                retry_delay_seconds=0.0,
                sleeper=sleeper,
                backend_pids=writer_b_backend_pids,
                attempt_results=writer_b_attempt_results,
                initialized_event=writer_b_initialized,
            ) as contender:
                writer_b_entered.set()
                contender.objects.add_membership(
                    ComponentMembership(
                        parent_object_id=parent_id,
                        slot_name=slot_name,
                        child_object_id=child_id,
                    )
                )
                contender.commit()
        except BaseException as error:  # pragma: no cover
            writer_b_errors.append(error)
        finally:
            writer_b_finished.set()

    with _TrackingPostgresqlOwnershipGraphWriteUnitOfWork(
        postgresql_repository_session_factory,
        backend_pids=writer_a_backend_pids,
    ) as writer_a:
        thread = threading.Thread(target=writer_b, name="postgresql-ownership-writer-b")
        thread.start()
        assert contention_observed.wait(timeout=5.0)
        assert writer_b_entered.is_set() is False
        assert writer_b_initialized.is_set() is False
        assert writer_a.objects.get(child_id) is not None

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
        owner = verifier.objects.get_owner(child_id)
        assert owner is not None
        assert owner.parent_object_id == parent_id
        assert owner.child_object_id == child_id
        assert owner.slot_name == slot_name


def test_postgresql_ownership_graph_guard_exhausts_contention_and_cleans_up_session(
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

    with PostgresqlOwnershipGraphWriteUnitOfWork(postgresql_repository_session_factory):
        contender = _TrackingPostgresqlOwnershipGraphWriteUnitOfWork(
            tracking_factory,
            max_guard_attempts=1,
            retry_delay_seconds=0.0,
            initialized_event=initialized,
        )
        with pytest.raises(OwnershipGraphWriteUnavailable):
            contender.__enter__()

        assert initialized.is_set() is False
        assert contender._session is None
        assert len(closed_sessions) == 1

    with PostgresqlOwnershipGraphWriteUnitOfWork(postgresql_repository_session_factory) as retrying:
        retrying.objects.list()


def test_postgresql_ownership_graph_guard_releases_on_commit_without_manual_unlock(
    postgresql_repository_session_factory: Callable[[], Session],
) -> None:
    with PostgresqlOwnershipGraphWriteUnitOfWork(postgresql_repository_session_factory) as first:
        first.commit()
        with PostgresqlOwnershipGraphWriteUnitOfWork(
            postgresql_repository_session_factory
        ) as second:
            second.objects.list()


def test_postgresql_ownership_graph_guard_releases_on_rollback_without_manual_unlock(
    postgresql_repository_session_factory: Callable[[], Session],
) -> None:
    with pytest.raises(RuntimeError):
        with PostgresqlOwnershipGraphWriteUnitOfWork(postgresql_repository_session_factory):
            raise RuntimeError("abort")

    with PostgresqlOwnershipGraphWriteUnitOfWork(postgresql_repository_session_factory) as second:
        second.objects.list()


def test_postgresql_model_and_ownership_guards_are_independent(
    postgresql_repository_session_factory: Callable[[], Session],
) -> None:
    model_entered = threading.Event()
    ownership_entered = threading.Event()
    release_model = threading.Event()
    release_ownership = threading.Event()
    errors: list[BaseException] = []
    model_backend_pids: list[int] = []
    ownership_backend_pids: list[int] = []

    def model_writer() -> None:
        try:
            with PostgresqlModelWriteUnitOfWork(postgresql_repository_session_factory) as uow:
                assert uow._session is not None
                model_backend_pids.append(
                    int(uow._session.execute(text("SELECT pg_backend_pid()")).scalar_one())
                )
                model_entered.set()
                assert release_model.wait(timeout=5.0)
        except BaseException as error:  # pragma: no cover
            errors.append(error)

    def ownership_writer() -> None:
        try:
            with PostgresqlOwnershipGraphWriteUnitOfWork(
                postgresql_repository_session_factory
            ) as uow:
                assert uow._session is not None
                ownership_backend_pids.append(
                    int(uow._session.execute(text("SELECT pg_backend_pid()")).scalar_one())
                )
                ownership_entered.set()
                assert release_ownership.wait(timeout=5.0)
        except BaseException as error:  # pragma: no cover
            errors.append(error)

    model_thread = threading.Thread(target=model_writer, name="postgresql-model-guard")
    ownership_thread = threading.Thread(
        target=ownership_writer,
        name="postgresql-ownership-guard",
    )
    model_thread.start()
    assert model_entered.wait(timeout=5.0)
    ownership_thread.start()
    assert ownership_entered.wait(timeout=5.0)
    release_ownership.set()
    release_model.set()
    model_thread.join(timeout=5.0)
    ownership_thread.join(timeout=5.0)
    assert not model_thread.is_alive()
    assert not ownership_thread.is_alive()
    assert errors == []
    assert len(model_backend_pids) == 1
    assert len(ownership_backend_pids) == 1
    assert model_backend_pids[0] != ownership_backend_pids[0]


def test_postgresql_ownership_graph_guard_does_not_block_ordinary_data_writer(
    postgresql_repository_session_factory: Callable[[], Session],
) -> None:
    change = _object_change()

    with PostgresqlOwnershipGraphWriteUnitOfWork(postgresql_repository_session_factory):
        with SqlAlchemyUnitOfWork(postgresql_repository_session_factory) as ordinary_writer:
            ordinary_writer.object_changes.add(change)
            ordinary_writer.commit()

        with SqlAlchemyUnitOfWork(postgresql_repository_session_factory) as verifier:
            assert verifier.object_changes.list_by_object(change.object_id) == (change,)


def test_postgresql_delete_object_acquires_ownership_guard_before_decision_reads(
    postgresql_engine: Engine,
    postgresql_repository_session_factory: Callable[[], Session],
) -> None:
    service = ObjectApplicationService(
        lambda: SqlAlchemyUnitOfWork(postgresql_repository_session_factory),
        ownership_graph_uow_factory=lambda: PostgresqlOwnershipGraphWriteUnitOfWork(
            postgresql_repository_session_factory
        ),
    )
    _, parent_id, _child_id, _slot_name = _seed_parent_child_graph(
        postgresql_repository_session_factory
    )
    statements: list[tuple[str, object]] = []

    def capture_sql(_conn, _cursor, statement, parameters, _context, _executemany) -> None:
        statements.append((statement, parameters))

    event.listen(postgresql_engine, "before_cursor_execute", capture_sql)
    try:
        statements.clear()
        service.delete_object(parent_id)
    finally:
        event.remove(postgresql_engine, "before_cursor_execute", capture_sql)

    advisory_index = next(
        index
        for index, (statement, parameters) in enumerate(statements)
        if _is_ownership_guard_attempt(statement, parameters)
    )
    decision_select_index = next(
        index
        for index, (statement, _parameters) in enumerate(statements)
        if statement.lstrip().upper().startswith("SELECT")
        and (
            "FROM objects" in statement
            or "FROM object_components" in statement
        )
    )
    assert advisory_index < decision_select_index
