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

from netauto.application.objecttemplate import ObjectTemplateApplicationService
from netauto.application.relationship import RelationshipDefinitionApplicationService
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
    SqliteModelWriteUnitOfWork,
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


def test_model_write_uow_emits_begin_immediate_before_repository_reads(tmp_path: Path) -> None:
    engine = _engine(tmp_path, "begin-order.sqlite3")
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    statements: list[str] = []
    event.listen(
        engine,
        "before_cursor_execute",
        lambda *_args: statements.append(cast(str, _args[2])),
    )

    try:
        with SqliteModelWriteUnitOfWork(session_factory) as uow:
            uow.object_templates.list()

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


def test_second_model_write_uow_cannot_acquire_while_first_is_active(tmp_path: Path) -> None:
    database = "serialized-writers.sqlite3"
    first_engine = _engine(tmp_path, database)
    second_engine = _engine(tmp_path, database, timeout=0.0)
    create_schema(first_engine)
    first_factory = sessionmaker(first_engine, expire_on_commit=False)
    second_factory = sessionmaker(second_engine, expire_on_commit=False)

    try:
        with SqliteModelWriteUnitOfWork(first_factory):
            with pytest.raises(OperationalError):
                with SqliteModelWriteUnitOfWork(second_factory):
                    pass
    finally:
        first_engine.dispose()
        second_engine.dispose()


def test_model_write_uow_release_after_commit_allows_next_writer(tmp_path: Path) -> None:
    database = "writer-release-commit.sqlite3"
    first_engine = _engine(tmp_path, database)
    second_engine = _engine(tmp_path, database, timeout=0.0)
    create_schema(first_engine)
    first_factory = sessionmaker(first_engine, expire_on_commit=False)
    second_factory = sessionmaker(second_engine, expire_on_commit=False)

    try:
        with SqliteModelWriteUnitOfWork(first_factory) as first:
            first.commit()
        with SqliteModelWriteUnitOfWork(second_factory):
            pass
    finally:
        first_engine.dispose()
        second_engine.dispose()


def test_model_write_uow_release_after_rollback_allows_next_writer(tmp_path: Path) -> None:
    database = "writer-release-rollback.sqlite3"
    first_engine = _engine(tmp_path, database)
    second_engine = _engine(tmp_path, database, timeout=0.0)
    create_schema(first_engine)
    first_factory = sessionmaker(first_engine, expire_on_commit=False)
    second_factory = sessionmaker(second_engine, expire_on_commit=False)

    try:
        with pytest.raises(RuntimeError):
            with SqliteModelWriteUnitOfWork(first_factory):
                raise RuntimeError("abort")
        with SqliteModelWriteUnitOfWork(second_factory):
            pass
    finally:
        first_engine.dispose()
        second_engine.dispose()


def test_normal_read_connection_can_read_while_model_write_transaction_is_held(
    tmp_path: Path,
) -> None:
    database = "reader-during-model-write.sqlite3"
    engine = _engine(tmp_path, database)
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    template = _template()

    try:
        with SqlAlchemyUnitOfWork(session_factory) as uow:
            uow.object_templates.add(template)
            _store_published_template_version(uow, template.id)
            uow.commit()

        with SqliteModelWriteUnitOfWork(session_factory):
            session = session_factory()
            try:
                repo = SqlAlchemyObjectTemplateRepository(session)
                assert repo.get(template.id) == template
            finally:
                session.close()
    finally:
        engine.dispose()


def test_normal_writer_cannot_complete_while_model_write_transaction_holds_writer_slot(
    tmp_path: Path,
) -> None:
    database = "writer-blocked.sqlite3"
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
        with SqliteModelWriteUnitOfWork(first_factory):
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


def test_model_write_uow_closes_session_when_begin_immediate_acquisition_fails(
    tmp_path: Path,
) -> None:
    database = "failed-begin-cleanup.sqlite3"
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
        with SqliteModelWriteUnitOfWork(first_factory):
            with pytest.raises(OperationalError):
                with SqliteModelWriteUnitOfWork(contender_factory):
                    pass

        assert len(closed_sessions) == 1
        assert closed_sessions[0].closed is True
    finally:
        first_engine.dispose()
        second_engine.dispose()


def test_relationship_definition_create_acquires_begin_immediate_before_decision_reads(
    tmp_path: Path,
) -> None:
    engine = _engine(tmp_path, "relationship-definition-order.sqlite3")
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    def ordinary_factory() -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(session_factory)

    def model_factory() -> SqliteModelWriteUnitOfWork:
        return SqliteModelWriteUnitOfWork(session_factory)
    service = RelationshipDefinitionApplicationService(
        ordinary_factory,
        model_write_uow_factory=model_factory,
    )
    source = _template(name="source")
    target = _template(name="target")
    statements: list[str] = []
    event.listen(
        engine,
        "before_cursor_execute",
        lambda *_args: statements.append(cast(str, _args[2])),
    )

    try:
        with ordinary_factory() as uow:
            uow.object_templates.add(source)
            uow.object_templates.add(target)
            _store_published_template_version(uow, source.id)
            _store_published_template_version(uow, target.id)
            uow.commit()

        statements.clear()
        service.create_relationship_definition(
            source_template_id=source.id,
            target_template_id=target.id,
            forward_name="uses",
            reverse_name="is_used_by",
        )

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


def test_object_template_publish_uses_begin_immediate_before_decision_reads(tmp_path: Path) -> None:
    engine = _engine(tmp_path, "object-template-publish-order.sqlite3")
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    def ordinary_factory() -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(session_factory)

    def model_factory() -> SqliteModelWriteUnitOfWork:
        return SqliteModelWriteUnitOfWork(session_factory)
    service = ObjectTemplateApplicationService(
        ordinary_factory,
        model_write_uow_factory=model_factory,
    )
    template = _template(name="device")
    statements: list[str] = []
    event.listen(
        engine,
        "before_cursor_execute",
        lambda *_args: statements.append(cast(str, _args[2])),
    )

    try:
        with ordinary_factory() as uow:
            uow.object_templates.add(template)
            uow.object_templates.add_version(
                ObjectTemplateVersion(
                    template_id=template.id,
                    version=1,
                    status=ObjectTemplateVersionStatus.DRAFT,
                )
            )
            uow.commit()

        statements.clear()
        service.publish_version(template_id=template.id, version=1)

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
