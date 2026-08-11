from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from netauto.core.object import (
    ObjectChange,
    ObjectChangeAlreadyExists,
    ObjectChangeKind,
    ObjectChangeSnapshot,
)
from netauto.persistence.memory.object_change_repository import (
    InMemoryObjectChangeRepository,
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
        before=before if before is not None else _snapshot(properties={"before": True}),
        after=after if after is not None else _snapshot(properties={"after": True}),
    )


def test_add_and_list_round_trip() -> None:
    repo = InMemoryObjectChangeRepository()
    object_id = uuid4()
    change = _change(object_id=object_id, occurred_at=datetime(2026, 8, 11, 12, 0, tzinfo=UTC))

    repo.add(change)

    assert repo.list_by_object(object_id) == (change,)


def test_list_by_object_is_deterministic_by_occurred_at_then_uuid() -> None:
    repo = InMemoryObjectChangeRepository()
    object_id = uuid4()
    first = _change(
        change_id=UUID("00000000-0000-0000-0000-000000000001"),
        object_id=object_id,
        occurred_at=datetime(2026, 8, 11, 12, 0, tzinfo=UTC),
    )
    second = _change(
        change_id=UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"),
        object_id=object_id,
        occurred_at=datetime(2026, 8, 11, 12, 0, tzinfo=UTC),
    )
    third = _change(
        object_id=object_id,
        occurred_at=datetime(2026, 8, 11, 12, 1, tzinfo=UTC),
    )

    for change in (third, second, first):
        repo.add(change)

    assert repo.list_by_object(object_id) == (first, second, third)


def test_mixed_offset_inputs_are_ordered_chronologically_after_utc_canonicalization() -> None:
    repo = InMemoryObjectChangeRepository()
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
    )
    later = _change(
        object_id=object_id,
        occurred_at=datetime(2026, 8, 11, 9, 0, tzinfo=UTC),
    )

    repo.add(later)
    repo.add(earlier)

    listed = repo.list_by_object(object_id)
    assert listed == (earlier, later)
    assert listed[0].occurred_at == datetime(2026, 8, 11, 8, 30, tzinfo=UTC)
    assert listed[1].occurred_at == datetime(2026, 8, 11, 9, 0, tzinfo=UTC)


def test_equal_instants_with_different_offsets_use_uuid_tiebreaker() -> None:
    repo = InMemoryObjectChangeRepository()
    object_id = uuid4()
    low = _change(
        change_id=UUID("00000000-0000-0000-0000-000000000001"),
        object_id=object_id,
        occurred_at=datetime(2026, 8, 11, 10, 30, tzinfo=timezone(timedelta(hours=2))),
    )
    high = _change(
        change_id=UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"),
        object_id=object_id,
        occurred_at=datetime(2026, 8, 11, 8, 30, tzinfo=UTC),
    )

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


def test_duplicate_change_uuid_is_rejected() -> None:
    repo = InMemoryObjectChangeRepository()
    object_id = uuid4()
    change = _change(object_id=object_id, occurred_at=datetime(2026, 8, 11, 12, 0, tzinfo=UTC))
    duplicate = _change(
        change_id=change.id,
        object_id=object_id,
        occurred_at=datetime(2026, 8, 11, 12, 1, tzinfo=UTC),
    )

    repo.add(change)

    with pytest.raises(ObjectChangeAlreadyExists):
        repo.add(duplicate)


def test_list_by_object_filters_unrelated_changes() -> None:
    repo = InMemoryObjectChangeRepository()
    object_id = uuid4()
    repo.add(_change(object_id=object_id, occurred_at=datetime(2026, 8, 11, 12, 0, tzinfo=UTC)))
    repo.add(_change(object_id=uuid4(), occurred_at=datetime(2026, 8, 11, 12, 1, tzinfo=UTC)))

    assert len(repo.list_by_object(object_id)) == 1
