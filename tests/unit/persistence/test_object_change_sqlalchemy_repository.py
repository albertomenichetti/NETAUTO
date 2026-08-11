from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Engine, inspect
from sqlalchemy.orm import Session, sessionmaker

from netauto.core.object import (
    Object,
    ObjectChange,
    ObjectChangeAlreadyExists,
    ObjectChangeKind,
    ObjectChangeSnapshot,
    ObjectPersistenceError,
)
from netauto.persistence.sqlalchemy.database import create_schema, create_sqlite_engine
from netauto.persistence.sqlalchemy.models import ObjectChangeRow
from netauto.persistence.sqlalchemy.object_change_repository import (
    SqlAlchemyObjectChangeRepository,
)
from netauto.persistence.sqlalchemy.object_repository import SqlAlchemyObjectRepository


def _repos(
    tmp_path: Path,
    filename: str,
) -> tuple[SqlAlchemyObjectChangeRepository, SqlAlchemyObjectRepository, Session, Engine]:
    engine = create_sqlite_engine(f"sqlite:///{tmp_path / filename}")
    create_schema(engine)
    session = sessionmaker(engine, expire_on_commit=False)()
    return (
        SqlAlchemyObjectChangeRepository(session),
        SqlAlchemyObjectRepository(session),
        session,
        engine,
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


def _object(*, object_id: UUID | None = None) -> Object:
    return Object(
        id=object_id or uuid4(),
        template_id=uuid4(),
        template_version=1,
        properties={},
    )


def test_schema_encodes_object_change_history_without_object_fk(tmp_path: Path) -> None:
    _repo, _object_repo, session, engine = _repos(tmp_path, "object_change_schema.sqlite3")
    session.close()
    try:
        inspector = inspect(engine)
        columns = {column["name"] for column in inspector.get_columns("object_changes")}
        pk = inspector.get_pk_constraint("object_changes")
        fks = inspector.get_foreign_keys("object_changes")
        indexes = inspector.get_indexes("object_changes")

        assert columns == {
            "id",
            "object_id",
            "occurred_at",
            "kind",
            "before_json",
            "after_json",
        }
        assert pk["constrained_columns"] == ["id"]
        assert fks == []
        assert any(
            index["name"] == "ix_object_changes_object_id_occurred_at"
            and index["column_names"] == ["object_id", "occurred_at"]
            for index in indexes
        )
    finally:
        engine.dispose()


def test_add_and_list_round_trip_with_nullable_before_after(tmp_path: Path) -> None:
    repo, _object_repo, session, engine = _repos(tmp_path, "object_change_round_trip.sqlite3")
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
    try:
        repo.add(deleted)
        repo.add(created)

        assert repo.list_by_object(object_id) == (created, deleted)
    finally:
        session.close()
        engine.dispose()


def test_mixed_offset_inputs_are_ordered_chronologically_in_sql(tmp_path: Path) -> None:
    repo, _object_repo, session, engine = _repos(tmp_path, "object_change_mixed_offsets.sqlite3")
    object_id = uuid4()
    earlier = _change(
        object_id=object_id,
        occurred_at=datetime(
            2026,
            8,
            11,
            10,
            30,
            tzinfo=timezone(timedelta(hours=2)),
        ),
        before=_snapshot(),
        after=_snapshot(),
    )
    later = _change(
        object_id=object_id,
        occurred_at=datetime(2026, 8, 11, 9, 0, tzinfo=UTC),
        before=_snapshot(),
        after=_snapshot(),
    )
    try:
        repo.add(later)
        repo.add(earlier)

        listed = repo.list_by_object(object_id)
        assert listed == (earlier, later)
        assert listed[0].occurred_at == datetime(2026, 8, 11, 8, 30, tzinfo=UTC)
        assert listed[1].occurred_at == datetime(2026, 8, 11, 9, 0, tzinfo=UTC)
    finally:
        session.close()
        engine.dispose()


def test_equal_instants_with_different_offsets_use_uuid_tiebreaker_in_sql(
    tmp_path: Path,
) -> None:
    repo, _object_repo, session, engine = _repos(tmp_path, "object_change_equal_instants.sqlite3")
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
    try:
        repo.add(high)
        repo.add(low)

        listed = repo.list_by_object(object_id)
        assert listed == (low, high)
        assert listed[0].occurred_at == listed[1].occurred_at == datetime(
            2026,
            8,
            11,
            8,
            30,
            tzinfo=UTC,
        )
    finally:
        session.close()
        engine.dispose()


def test_arbitrary_valid_property_json_round_trips(tmp_path: Path) -> None:
    repo, _object_repo, session, engine = _repos(tmp_path, "object_change_properties.sqlite3")
    object_id = uuid4()
    change = _change(
        object_id=object_id,
        occurred_at=datetime(2026, 8, 11, 12, 0, tzinfo=UTC),
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
    try:
        repo.add(change)

        assert repo.list_by_object(object_id) == (change,)
    finally:
        session.close()
        engine.dispose()


def test_duplicate_change_uuid_is_rejected(tmp_path: Path) -> None:
    repo, _object_repo, session, engine = _repos(tmp_path, "object_change_duplicate.sqlite3")
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
    try:
        repo.add(change)
        with pytest.raises(ObjectChangeAlreadyExists):
            repo.add(duplicate)
    finally:
        session.close()
        engine.dispose()


def test_corrupted_snapshot_json_maps_to_persistence_error(tmp_path: Path) -> None:
    repo, _object_repo, session, engine = _repos(tmp_path, "object_change_corrupt.sqlite3")
    object_id = uuid4()
    try:
        session.add(
            ObjectChangeRow(
                id=str(uuid4()),
                object_id=str(object_id),
                occurred_at=datetime(2026, 8, 11, 12, 0, tzinfo=UTC).isoformat(),
                kind=ObjectChangeKind.CREATED.value,
                before_json=None,
                after_json="{bad json",
            )
        )
        session.commit()

        with pytest.raises(ObjectPersistenceError):
            repo.list_by_object(object_id)
    finally:
        session.close()
        engine.dispose()


def test_deleting_object_row_does_not_delete_history_rows(tmp_path: Path) -> None:
    repo, object_repo, session, engine = _repos(tmp_path, "object_change_survival.sqlite3")
    object_value = _object()
    change = _change(
        object_id=object_value.id,
        occurred_at=datetime(2026, 8, 11, 12, 0, tzinfo=UTC),
        kind=ObjectChangeKind.DELETED,
        before=_snapshot(properties={"hostname": "router-01"}),
        after=None,
    )
    try:
        object_repo.add(object_value)
        repo.add(change)
        session.commit()

        object_repo.delete(object_value.id)
        session.commit()

        assert object_repo.get(object_value.id) is None
        assert repo.list_by_object(object_value.id) == (change,)
    finally:
        session.close()
        engine.dispose()


def test_sql_round_trip_returns_canonical_utc_timestamp(tmp_path: Path) -> None:
    repo, _object_repo, session, engine = _repos(tmp_path, "object_change_round_trip_utc.sqlite3")
    object_id = uuid4()
    change = _change(
        object_id=object_id,
        occurred_at=datetime(2026, 8, 11, 10, 30, tzinfo=timezone(timedelta(hours=2))),
        before=_snapshot(),
        after=_snapshot(),
    )
    try:
        repo.add(change)

        loaded = repo.list_by_object(object_id)
        assert loaded == (
            _change(
                change_id=change.id,
                object_id=object_id,
                occurred_at=datetime(2026, 8, 11, 8, 30, tzinfo=UTC),
                before=change.before,
                after=change.after,
                kind=change.kind,
            ),
        )
        assert loaded[0].occurred_at.tzinfo is UTC
    finally:
        session.close()
        engine.dispose()


def test_transaction_rollback_discards_uncommitted_object_and_history_rows(tmp_path: Path) -> None:
    repo, object_repo, session, engine = _repos(tmp_path, "object_change_rollback.sqlite3")
    object_value = _object()
    change = _change(
        object_id=object_value.id,
        occurred_at=datetime(2026, 8, 11, 12, 0, tzinfo=UTC),
        kind=ObjectChangeKind.CREATED,
        before=None,
        after=_snapshot(),
    )
    try:
        object_repo.add(object_value)
        repo.add(change)
        session.rollback()

        fresh_session = sessionmaker(engine, expire_on_commit=False)()
        try:
            fresh_object_repo = SqlAlchemyObjectRepository(fresh_session)
            fresh_change_repo = SqlAlchemyObjectChangeRepository(fresh_session)
            assert fresh_object_repo.get(object_value.id) is None
            assert fresh_change_repo.list_by_object(object_value.id) == ()
        finally:
            fresh_session.close()
    finally:
        session.close()
        engine.dispose()
