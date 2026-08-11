"""SQLAlchemy object change repository implementation."""

import json
from collections.abc import Mapping
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from netauto.core.object import (
    ObjectChange,
    ObjectChangeAlreadyExists,
    ObjectChangeKind,
    ObjectChangeRepository,
    ObjectChangeSnapshot,
    ObjectPersistenceError,
)
from netauto.persistence.sqlalchemy.models import ObjectChangeRow


def _serialize_snapshot_properties(properties: Mapping[str, object]) -> dict[str, object]:
    return dict(properties)


def _serialize_snapshot(snapshot: ObjectChangeSnapshot | None) -> str | None:
    if snapshot is None:
        return None
    payload = {
        "template_id": str(snapshot.template_id),
        "template_version": snapshot.template_version,
        "properties": _serialize_snapshot_properties(snapshot.properties),
    }
    try:
        return json.dumps(
            payload,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except Exception as error:
        raise ObjectPersistenceError(
            "Object change snapshot could not be serialized to JSON."
        ) from error


def _deserialize_snapshot(snapshot_json: str | None) -> ObjectChangeSnapshot | None:
    if snapshot_json is None:
        return None
    try:
        payload = json.loads(snapshot_json)
    except json.JSONDecodeError as error:
        raise ObjectPersistenceError("Stored object change snapshot JSON is invalid.") from error
    if not isinstance(payload, dict):
        raise ObjectPersistenceError("Stored object change snapshot must be a JSON object.")
    if set(payload) != {"template_id", "template_version", "properties"}:
        raise ObjectPersistenceError("Stored object change snapshot has an invalid shape.")
    properties = payload["properties"]
    if not isinstance(properties, dict):
        raise ObjectPersistenceError("Stored object change snapshot properties must be an object.")
    try:
        return ObjectChangeSnapshot(
            template_id=UUID(payload["template_id"]),
            template_version=payload["template_version"],
            properties=properties,
        )
    except Exception as error:
        raise ObjectPersistenceError("Stored object change snapshot is invalid.") from error


def _serialize_occurred_at(occurred_at: datetime) -> str:
    return occurred_at.isoformat()


def _deserialize_occurred_at(occurred_at: str) -> datetime:
    try:
        value = datetime.fromisoformat(occurred_at)
    except ValueError as error:
        raise ObjectPersistenceError("Stored object change occurred_at is invalid.") from error
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ObjectPersistenceError("Stored object change occurred_at must be timezone-aware.")
    return value


def _row_to_object_change(row: ObjectChangeRow) -> ObjectChange:
    try:
        kind = ObjectChangeKind(row.kind)
    except ValueError as error:
        raise ObjectPersistenceError("Stored object change kind is invalid.") from error

    try:
        return ObjectChange(
            id=UUID(row.id),
            object_id=UUID(row.object_id),
            occurred_at=_deserialize_occurred_at(row.occurred_at),
            kind=kind,
            before=_deserialize_snapshot(row.before_json),
            after=_deserialize_snapshot(row.after_json),
        )
    except ObjectPersistenceError:
        raise
    except Exception as error:
        raise ObjectPersistenceError("Stored object change row is invalid.") from error


class SqlAlchemyObjectChangeRepository(ObjectChangeRepository):
    """SQLAlchemy-backed append-only repository for runtime object history."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, change: ObjectChange) -> None:
        self._session.add(
            ObjectChangeRow(
                id=str(change.id),
                object_id=str(change.object_id),
                occurred_at=_serialize_occurred_at(change.occurred_at),
                kind=change.kind.value,
                before_json=_serialize_snapshot(change.before),
                after_json=_serialize_snapshot(change.after),
            )
        )
        try:
            self._session.flush()
        except IntegrityError as error:
            raise ObjectChangeAlreadyExists("Object change UUID already exists.") from error

    def list_by_object(self, object_id: UUID) -> tuple[ObjectChange, ...]:
        rows = self._session.scalars(
            select(ObjectChangeRow)
            .where(ObjectChangeRow.object_id == str(object_id))
            .order_by(ObjectChangeRow.occurred_at.asc(), ObjectChangeRow.id.asc())
        ).all()
        return tuple(_row_to_object_change(row) for row in rows)
