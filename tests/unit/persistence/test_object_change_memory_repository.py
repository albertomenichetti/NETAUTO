from datetime import UTC, datetime
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
