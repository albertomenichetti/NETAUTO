from collections.abc import Mapping
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from netauto.core.object import (
    InvalidObjectChange,
    ObjectChange,
    ObjectChangeKind,
    ObjectChangeSnapshot,
)


def _snapshot(
    *,
    template_version: int = 1,
    properties: Mapping[str, object] | None = None,
) -> ObjectChangeSnapshot:
    return ObjectChangeSnapshot(
        template_id=uuid4(),
        template_version=template_version,
        properties=properties or {"hostname": "router-01"},
    )


def test_created_change_accepts_before_none_and_after_snapshot() -> None:
    change = ObjectChange(
        id=uuid4(),
        object_id=uuid4(),
        occurred_at=datetime(2026, 8, 11, 12, 0, tzinfo=UTC),
        kind=ObjectChangeKind.CREATED,
        before=None,
        after=_snapshot(),
    )

    assert change.before is None
    assert change.after is not None


def test_updated_change_accepts_before_and_after_snapshots() -> None:
    change = ObjectChange(
        id=uuid4(),
        object_id=uuid4(),
        occurred_at=datetime(2026, 8, 11, 12, 0, tzinfo=UTC),
        kind=ObjectChangeKind.UPDATED,
        before=_snapshot(properties={"hostname": "router-01"}),
        after=_snapshot(properties={"hostname": "router-02"}),
    )

    assert change.before is not None
    assert change.after is not None


def test_migrated_change_accepts_before_and_after_snapshots() -> None:
    change = ObjectChange(
        id=uuid4(),
        object_id=uuid4(),
        occurred_at=datetime(2026, 8, 11, 12, 0, tzinfo=UTC),
        kind=ObjectChangeKind.MIGRATED,
        before=_snapshot(template_version=1),
        after=_snapshot(template_version=2),
    )

    assert change.before is not None
    assert change.after is not None


def test_deleted_change_accepts_before_snapshot_and_after_none() -> None:
    change = ObjectChange(
        id=uuid4(),
        object_id=uuid4(),
        occurred_at=datetime(2026, 8, 11, 12, 0, tzinfo=UTC),
        kind=ObjectChangeKind.DELETED,
        before=_snapshot(),
        after=None,
    )

    assert change.before is not None
    assert change.after is None


@pytest.mark.parametrize(
    ("kind", "before", "after"),
    [
        (ObjectChangeKind.CREATED, _snapshot(), _snapshot()),
        (ObjectChangeKind.CREATED, None, None),
        (ObjectChangeKind.UPDATED, None, _snapshot()),
        (ObjectChangeKind.UPDATED, _snapshot(), None),
        (ObjectChangeKind.MIGRATED, None, _snapshot()),
        (ObjectChangeKind.MIGRATED, _snapshot(), None),
        (ObjectChangeKind.DELETED, None, None),
        (ObjectChangeKind.DELETED, _snapshot(), _snapshot()),
    ],
)
def test_invalid_before_after_combinations_are_rejected(
    kind: ObjectChangeKind,
    before: ObjectChangeSnapshot | None,
    after: ObjectChangeSnapshot | None,
) -> None:
    with pytest.raises(InvalidObjectChange):
        ObjectChange(
            id=uuid4(),
            object_id=uuid4(),
            occurred_at=datetime(2026, 8, 11, 12, 0, tzinfo=UTC),
            kind=kind,
            before=before,
            after=after,
        )


def test_naive_timestamp_is_rejected() -> None:
    with pytest.raises(InvalidObjectChange):
        ObjectChange(
            id=uuid4(),
            object_id=uuid4(),
            occurred_at=datetime(2026, 8, 11, 12, 0),
            kind=ObjectChangeKind.CREATED,
            before=None,
            after=_snapshot(),
        )


def test_snapshot_properties_are_immutable_defensive_copy() -> None:
    properties = {"hostname": "router-01"}
    snapshot = _snapshot(properties=properties)
    properties["hostname"] = "router-02"

    assert snapshot.properties["hostname"] == "router-01"
    with pytest.raises(TypeError):
        snapshot.properties["hostname"] = "router-03"  # type: ignore[index]


@pytest.mark.parametrize("template_version", [0, -1, True])
def test_invalid_snapshot_template_version_is_rejected(template_version: object) -> None:
    with pytest.raises(InvalidObjectChange):
        _snapshot(template_version=template_version)  # type: ignore[arg-type]
