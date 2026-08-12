from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from netauto.core.object import (
    Object,
    ObjectChange,
    ObjectChangeAlreadyExists,
    ObjectChangeKind,
    ObjectChangeSnapshot,
    ObjectPersistenceError,
)
from netauto.core.objecttemplate import ObjectTemplateVersionStatus
from netauto.persistence.sqlalchemy.models import (
    ObjectChangeRow,
    ObjectTemplateRow,
    ObjectTemplateVersionRow,
)
from netauto.persistence.sqlalchemy.object_change_repository import (
    SqlAlchemyObjectChangeRepository,
)
from netauto.persistence.sqlalchemy.object_repository import SqlAlchemyObjectRepository

pytestmark = pytest.mark.postgresql

DEFAULT_TEMPLATE_ID = UUID("00000000-0000-0000-0000-0000000000ab")


def _object(*, object_id: UUID | None = None) -> Object:
    return Object(
        id=object_id or uuid4(),
        template_id=DEFAULT_TEMPLATE_ID,
        template_version=1,
        properties={},
    )


def _snapshot(
    *,
    template_version: int = 1,
    properties: dict[str, object] | None = None,
) -> ObjectChangeSnapshot:
    return ObjectChangeSnapshot(
        template_id=uuid4(),
        template_version=template_version,
        properties=properties or {},
    )


def _change(
    *,
    change_id: UUID | None = None,
    object_id: UUID,
    occurred_at: datetime,
    kind: ObjectChangeKind = ObjectChangeKind.UPDATED,
    before: ObjectChangeSnapshot | None = None,
    after: ObjectChangeSnapshot | None = None,
) -> ObjectChange:
    return ObjectChange(
        id=change_id or uuid4(),
        object_id=object_id,
        occurred_at=occurred_at,
        kind=kind,
        before=before,
        after=after,
    )


def _store_template_version(
    session: Session,
    *,
    template_id: UUID,
    version: int = 1,
    status: ObjectTemplateVersionStatus = ObjectTemplateVersionStatus.PUBLISHED,
) -> None:
    session.add(
        ObjectTemplateRow(
            id=str(template_id),
            namespace=f"network_{template_id.hex[:8]}",
            name=f"template_{template_id.hex[:8]}",
            description=None,
            abstract=False,
        )
    )
    session.flush()
    session.add(
        ObjectTemplateVersionRow(
            template_id=str(template_id),
            version=version,
            status=status.value,
            parent_template_id=None,
            parent_version=None,
        )
    )
    session.flush()


def _repos(
    session: Session,
) -> tuple[SqlAlchemyObjectChangeRepository, SqlAlchemyObjectRepository]:
    _store_template_version(session, template_id=DEFAULT_TEMPLATE_ID)
    return (
        SqlAlchemyObjectChangeRepository(session),
        SqlAlchemyObjectRepository(session),
    )


def test_postgresql_object_change_add_and_list_round_trip_with_nullable_snapshots(
    postgresql_model_session: Session,
) -> None:
    repo, _object_repo = _repos(postgresql_model_session)
    object_id = uuid4()
    created = _change(
        object_id=object_id,
        occurred_at=datetime(2026, 8, 11, 12, 0, tzinfo=UTC),
        kind=ObjectChangeKind.CREATED,
        before=None,
        after=_snapshot(properties={"hostname": "router-01"}),
    )
    deleted = _change(
        object_id=object_id,
        occurred_at=datetime(2026, 8, 11, 12, 1, tzinfo=UTC),
        kind=ObjectChangeKind.DELETED,
        before=_snapshot(properties={"hostname": "router-01"}),
        after=None,
    )

    repo.add(deleted)
    repo.add(created)

    assert repo.list_by_object(object_id) == (created, deleted)
    assert repo.list_by_object(uuid4()) == ()


def test_postgresql_object_change_snapshot_json_and_kind_round_trip(
    postgresql_model_session: Session,
) -> None:
    repo, _object_repo = _repos(postgresql_model_session)
    object_id = uuid4()
    change = _change(
        object_id=object_id,
        occurred_at=datetime(2026, 8, 11, 12, 0, tzinfo=UTC),
        kind=ObjectChangeKind.MIGRATED,
        before=_snapshot(
            properties={
                "hostname": "router-01",
                "enabled": True,
                "note": None,
                "metric": 1.5,
                "tags": ["edge", 7],
                "nested": {"rack": "A1"},
            }
        ),
        after=_snapshot(properties={"hostname": "router-02"}),
    )

    repo.add(change)

    loaded = repo.list_by_object(object_id)
    assert loaded == (change,)
    assert loaded[0].kind is ObjectChangeKind.MIGRATED
    assert isinstance(loaded[0].id, UUID)
    assert isinstance(loaded[0].object_id, UUID)


def test_postgresql_object_change_timestamp_ordering_and_canonical_utc_behavior(
    postgresql_model_session: Session,
) -> None:
    repo, _object_repo = _repos(postgresql_model_session)
    object_id = uuid4()
    earlier = _change(
        object_id=object_id,
        occurred_at=datetime(2026, 8, 11, 10, 30, tzinfo=timezone(timedelta(hours=2))),
        before=_snapshot(),
        after=_snapshot(),
    )
    later = _change(
        object_id=object_id,
        occurred_at=datetime(2026, 8, 11, 9, 0, tzinfo=UTC),
        before=_snapshot(),
        after=_snapshot(),
    )

    repo.add(later)
    repo.add(earlier)

    listed = repo.list_by_object(object_id)
    assert listed == (earlier, later)
    assert listed[0].occurred_at == datetime(2026, 8, 11, 8, 30, tzinfo=UTC)
    assert listed[1].occurred_at == datetime(2026, 8, 11, 9, 0, tzinfo=UTC)
    assert listed[0].occurred_at.tzinfo is UTC


def test_postgresql_object_change_equal_instants_use_uuid_tiebreaker(
    postgresql_model_session: Session,
) -> None:
    repo, _object_repo = _repos(postgresql_model_session)
    object_id = uuid4()
    low = _change(
        change_id=UUID("00000000-0000-0000-0000-000000000001"),
        object_id=object_id,
        occurred_at=datetime(2026, 8, 11, 10, 30, tzinfo=timezone(timedelta(hours=2))),
        before=_snapshot(),
        after=_snapshot(),
    )
    high = _change(
        change_id=UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"),
        object_id=object_id,
        occurred_at=datetime(2026, 8, 11, 8, 30, tzinfo=UTC),
        before=_snapshot(),
        after=_snapshot(),
    )

    repo.add(high)
    repo.add(low)

    listed = repo.list_by_object(object_id)
    assert listed == (low, high)
    assert listed[0].occurred_at == listed[1].occurred_at == datetime(
        2026, 8, 11, 8, 30, tzinfo=UTC
    )


def test_postgresql_object_change_duplicate_uuid_translation_and_recovery(
    postgresql_model_session: Session,
) -> None:
    repo, _object_repo = _repos(postgresql_model_session)
    object_id = uuid4()
    change = _change(
        change_id=uuid4(),
        object_id=object_id,
        occurred_at=datetime(2026, 8, 11, 12, 0, tzinfo=UTC),
        before=_snapshot(),
        after=_snapshot(),
    )
    duplicate = _change(
        change_id=change.id,
        object_id=object_id,
        occurred_at=datetime(2026, 8, 11, 12, 1, tzinfo=UTC),
        before=_snapshot(),
        after=_snapshot(),
    )

    repo.add(change)
    with postgresql_model_session.begin_nested():
        with pytest.raises(ObjectChangeAlreadyExists):
            repo.add(duplicate)

    assert repo.list_by_object(object_id) == (change,)


def test_postgresql_object_change_has_no_object_fk_and_history_survives_delete(
    postgresql_model_session: Session,
) -> None:
    repo, object_repo = _repos(postgresql_model_session)
    missing_object_id = uuid4()
    missing_object_change = _change(
        object_id=missing_object_id,
        occurred_at=datetime(2026, 8, 11, 12, 0, tzinfo=UTC),
        kind=ObjectChangeKind.CREATED,
        before=None,
        after=_snapshot(),
    )
    repo.add(missing_object_change)
    assert repo.list_by_object(missing_object_id) == (missing_object_change,)

    object_value = _object()
    delete_change = _change(
        object_id=object_value.id,
        occurred_at=datetime(2026, 8, 11, 12, 1, tzinfo=UTC),
        kind=ObjectChangeKind.DELETED,
        before=_snapshot(properties={"hostname": "router-01"}),
        after=None,
    )
    object_repo.add(object_value)
    repo.add(delete_change)

    object_repo.delete(object_value.id)

    assert object_repo.get(object_value.id) is None
    assert repo.list_by_object(object_value.id) == (delete_change,)


def test_postgresql_object_change_transaction_rollback_discards_uncommitted_rows(
    postgresql_engine,
    postgresql_repository_schema: str,
) -> None:
    with _fresh_session(postgresql_engine, postgresql_repository_schema) as session:
        change_repo, object_repo = _repos(session)
        object_value = _object()
        change = _change(
            object_id=object_value.id,
            occurred_at=datetime(2026, 8, 11, 12, 0, tzinfo=UTC),
            kind=ObjectChangeKind.CREATED,
            before=None,
            after=_snapshot(),
        )

        object_repo.add(object_value)
        change_repo.add(change)
        session.rollback()

    with _fresh_session(postgresql_engine, postgresql_repository_schema) as fresh_session:
        fresh_change_repo = SqlAlchemyObjectChangeRepository(fresh_session)
        fresh_object_repo = SqlAlchemyObjectRepository(fresh_session)
        assert fresh_object_repo.get(object_value.id) is None
        assert fresh_change_repo.list_by_object(object_value.id) == ()


def test_postgresql_object_change_corrupt_snapshot_json_maps_to_persistence_error(
    postgresql_model_session: Session,
) -> None:
    repo, _object_repo = _repos(postgresql_model_session)
    object_id = uuid4()
    postgresql_model_session.add(
        ObjectChangeRow(
            id=str(uuid4()),
            object_id=str(object_id),
            occurred_at=datetime(2026, 8, 11, 12, 0, tzinfo=UTC).isoformat(),
            kind=ObjectChangeKind.CREATED.value,
            before_json=None,
            after_json="{bad json",
        )
    )
    postgresql_model_session.flush()

    with pytest.raises(ObjectPersistenceError):
        repo.list_by_object(object_id)


@contextmanager
def _fresh_session(
    postgresql_engine,
    schema: str,
) -> Generator[Session, None, None]:
    connection = postgresql_engine.connect()
    quoted_schema = postgresql_engine.dialect.identifier_preparer.quote_identifier(schema)
    connection.execute(text(f"SET search_path TO {quoted_schema}"))
    session = Session(bind=connection, expire_on_commit=False)
    try:
        yield session
    finally:
        session.close()
        connection.close()
