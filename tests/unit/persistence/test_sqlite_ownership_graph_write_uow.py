from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from sqlalchemy import event
from sqlalchemy.engine import Engine, create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from netauto.application.unit_of_work import OwnershipGraphWriteUnavailable
from netauto.core.object import Object
from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateVersion,
    ObjectTemplateVersionStatus,
)
from netauto.persistence.sqlalchemy.database import create_schema
from netauto.persistence.sqlalchemy.object_repository import SqlAlchemyObjectRepository
from netauto.persistence.sqlalchemy.objecttemplate_repository import (
    SqlAlchemyObjectTemplateRepository,
)
from netauto.persistence.sqlalchemy.unit_of_work import (
    SqlAlchemyUnitOfWork,
    SqliteOwnershipGraphWriteUnitOfWork,
)


def _engine(tmp_path: Path, filename: str, *, timeout: float = 5.0) -> Engine:
    engine = create_engine(
        f"sqlite:///{tmp_path / filename}",
        connect_args={
            "check_same_thread": False,
            "timeout": timeout,
        },
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection: sqlite3.Connection, _record: object) -> None:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()

    return engine


def _template(
    *,
    name: str = "device",
    template_id: UUID | None = None,
) -> ObjectTemplate:
    return ObjectTemplate(
        id=template_id or uuid4(),
        namespace="network",
        name=name,
        description=f"{name} template",
        abstract=False,
    )


def _version(template_id: UUID, *, version: int = 1) -> ObjectTemplateVersion:
    return ObjectTemplateVersion(
        template_id=template_id,
        version=version,
        status=ObjectTemplateVersionStatus.PUBLISHED,
    )


def _store_published_template_version(
    uow: SqlAlchemyUnitOfWork,
    template_id: UUID,
    *,
    version: int = 1,
) -> None:
    uow.object_templates.add_version(
        ObjectTemplateVersion(
            template_id=template_id,
            version=version,
            status=ObjectTemplateVersionStatus.DRAFT,
        )
    )
    uow.object_templates.replace_version(_version(template_id, version=version))


def _object(*, template_id: UUID, template_version: int = 1) -> Object:
    return Object(
        id=uuid4(),
        template_id=template_id,
        template_version=template_version,
        properties={},
    )


class _SqliteErrorWithCode(sqlite3.OperationalError):
    def __init__(self, sqlite_errorcode: int) -> None:
        super().__init__("sqlite error")
        self.sqlite_errorcode = sqlite_errorcode


def _locked_operational_error() -> OperationalError:
    return OperationalError("BEGIN IMMEDIATE", {}, _SqliteErrorWithCode(sqlite3.SQLITE_LOCKED))


def test_ownership_graph_uow_emits_begin_immediate_before_repository_reads(
    tmp_path: Path,
) -> None:
    engine = _engine(tmp_path, "ownership-begin-order.sqlite3")
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    statements: list[str] = []
    event.listen(
        engine,
        "before_cursor_execute",
        lambda *_args: statements.append(cast(str, _args[2])),
    )

    try:
        with SqliteOwnershipGraphWriteUnitOfWork(session_factory) as uow:
            uow.objects.list()

        begin_index = next(
            index
            for index, statement in enumerate(statements)
            if statement == "BEGIN IMMEDIATE"
        )
        select_index = next(
            index
            for index, statement in enumerate(statements)
            if statement.lstrip().upper().startswith("SELECT")
        )
        assert begin_index < select_index
    finally:
        engine.dispose()


def test_second_ownership_graph_uow_raises_unavailable_when_writer_stays_busy(
    tmp_path: Path,
) -> None:
    database = "ownership-exhaustion.sqlite3"
    first_engine = _engine(tmp_path, database)
    second_engine = _engine(tmp_path, database, timeout=0.0)
    create_schema(first_engine)
    first_factory = sessionmaker(first_engine, expire_on_commit=False)
    second_factory = sessionmaker(second_engine, expire_on_commit=False)
    attempts: list[str] = []
    sleeps: list[float] = []

    event.listen(
        second_engine,
        "before_cursor_execute",
        lambda *_args: attempts.append(cast(str, _args[2])),
    )

    try:
        with SqliteOwnershipGraphWriteUnitOfWork(first_factory):
            with pytest.raises(OwnershipGraphWriteUnavailable) as exc_info:
                with SqliteOwnershipGraphWriteUnitOfWork(
                    second_factory,
                    max_reservation_attempts=2,
                    retry_delay_seconds=0.0,
                    sleeper=sleeps.append,
                ):
                    pass
        assert isinstance(exc_info.value.__cause__, OperationalError)
        assert [statement for statement in attempts if statement == "BEGIN IMMEDIATE"] == [
            "BEGIN IMMEDIATE",
            "BEGIN IMMEDIATE",
        ]
        assert sleeps == [0.0]
    finally:
        first_engine.dispose()
        second_engine.dispose()


def test_ownership_graph_uow_retries_busy_reservation_then_succeeds(tmp_path: Path) -> None:
    database = "ownership-retry-then-success.sqlite3"
    first_engine = _engine(tmp_path, database)
    second_engine = _engine(tmp_path, database, timeout=0.0)
    create_schema(first_engine)
    first_factory = sessionmaker(first_engine, expire_on_commit=False)
    second_factory = sessionmaker(second_engine, expire_on_commit=False)
    statements: list[str] = []
    init_calls: list[str] = []

    class TrackingOwnershipGraphWriteUnitOfWork(SqliteOwnershipGraphWriteUnitOfWork):
        def _initialize_repositories(self) -> None:
            init_calls.append("initialized")
            super()._initialize_repositories()

    def sleeper(_delay: float) -> None:
        first.__exit__(None, None, None)

    event.listen(
        second_engine,
        "before_cursor_execute",
        lambda *_args: statements.append(cast(str, _args[2])),
    )

    first = SqliteOwnershipGraphWriteUnitOfWork(first_factory)
    first.__enter__()
    try:
        with TrackingOwnershipGraphWriteUnitOfWork(
            second_factory,
            max_reservation_attempts=2,
            retry_delay_seconds=0.0,
            sleeper=sleeper,
        ) as contender:
            assert init_calls == ["initialized"]
            contender.objects.list()
    finally:
        first.__exit__(None, None, None)
        first_engine.dispose()
        second_engine.dispose()

    begin_attempts = [statement for statement in statements if statement == "BEGIN IMMEDIATE"]
    assert len(begin_attempts) == 2
    select_statements = [
        statement for statement in statements if statement.lstrip().upper().startswith("SELECT")
    ]
    assert len(select_statements) >= 1
    assert statements.index("BEGIN IMMEDIATE") < statements.index(select_statements[0])


def test_non_busy_operational_error_is_not_retried_for_ownership_graph_uow() -> None:
    session_factory = sessionmaker(bind=create_engine("sqlite:///:memory:"), expire_on_commit=False)
    attempts: list[str] = []
    sleeps: list[float] = []

    class NonBusyFailureUnitOfWork(SqliteOwnershipGraphWriteUnitOfWork):
        def _begin_immediate(self) -> None:
            attempts.append("attempt")
            raise _locked_operational_error()

    with pytest.raises(OperationalError):
        with NonBusyFailureUnitOfWork(
            session_factory,
            max_reservation_attempts=2,
            retry_delay_seconds=0.0,
            sleeper=sleeps.append,
        ):
            pass

    assert attempts == ["attempt"]
    assert sleeps == []


def test_ownership_graph_uow_closes_session_when_begin_immediate_acquisition_fails(
    tmp_path: Path,
) -> None:
    database = "ownership-cleanup.sqlite3"
    first_engine = _engine(tmp_path, database)
    second_engine = _engine(tmp_path, database, timeout=0.0)
    create_schema(first_engine)
    first_factory = sessionmaker(first_engine, expire_on_commit=False)
    closed_sessions: list[TrackingSession] = []

    class TrackingSession(Session):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self.closed = False
            closed_sessions.append(self)

        def close(self) -> None:
            self.closed = True
            super().close()

    contender_factory = sessionmaker(
        second_engine,
        expire_on_commit=False,
        class_=TrackingSession,
    )

    try:
        with SqliteOwnershipGraphWriteUnitOfWork(first_factory):
            with pytest.raises(OwnershipGraphWriteUnavailable):
                with SqliteOwnershipGraphWriteUnitOfWork(
                    contender_factory,
                    retry_delay_seconds=0.0,
                ):
                    pass

        assert len(closed_sessions) == 1
        assert closed_sessions[0].closed is True

        with SqliteOwnershipGraphWriteUnitOfWork(contender_factory):
            pass
    finally:
        first_engine.dispose()
        second_engine.dispose()


def test_normal_read_connection_can_read_while_ownership_graph_transaction_is_held(
    tmp_path: Path,
) -> None:
    database = "reader-during-ownership-write.sqlite3"
    engine = _engine(tmp_path, database)
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    template = _template()

    try:
        with SqlAlchemyUnitOfWork(session_factory) as uow:
            uow.object_templates.add(template)
            _store_published_template_version(uow, template.id)
            uow.commit()

        with SqliteOwnershipGraphWriteUnitOfWork(session_factory):
            session = session_factory()
            try:
                repo = SqlAlchemyObjectTemplateRepository(session)
                assert repo.get(template.id) == template
            finally:
                session.close()
    finally:
        engine.dispose()


def test_normal_writer_cannot_complete_while_ownership_graph_transaction_holds_writer_slot(
    tmp_path: Path,
) -> None:
    database = "writer-blocked-by-ownership.sqlite3"
    first_engine = _engine(tmp_path, database)
    second_engine = _engine(tmp_path, database, timeout=0.0)
    create_schema(first_engine)
    first_factory = sessionmaker(first_engine, expire_on_commit=False)
    second_factory = sessionmaker(second_engine, expire_on_commit=False)
    template = _template()

    try:
        with SqlAlchemyUnitOfWork(first_factory) as uow:
            uow.object_templates.add(template)
            _store_published_template_version(uow, template.id)
            uow.commit()

        blocked_object = _object(template_id=template.id)
        with SqliteOwnershipGraphWriteUnitOfWork(first_factory):
            with pytest.raises(OperationalError):
                with SqlAlchemyUnitOfWork(second_factory) as contender:
                    contender.objects.add(blocked_object)
                    contender.commit()

        session = first_factory()
        try:
            repo = SqlAlchemyObjectRepository(session)
            assert repo.get(blocked_object.id) is None
        finally:
            session.close()
    finally:
        first_engine.dispose()
        second_engine.dispose()
