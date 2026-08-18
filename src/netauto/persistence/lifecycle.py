"""Shared persistence authority for every durable lifecycle event family."""

import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import cast
from uuid import UUID

from sqlalchemy import null, or_, select, tuple_
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncConnection

from netauto.domain.objects import Object
from netauto.domain.primitives import JsonValue
from netauto.domain.relationships import Relationship, RelationshipLifecycleView
from netauto.persistence.metadata import (
    object_lifecycle_events,
    objects,
    relationship_resolutions,
    runtime_relationship_resolutions,
)


class EventKind(StrEnum):
    CREATED = "CREATED"
    RENAME = "RENAME"
    DATA_CHANGE = "DATA_CHANGE"
    SCHEMA_CHANGE = "SCHEMA_CHANGE"
    ATTACH_TO = "ATTACH_TO"
    DETACH_FROM = "DETACH_FROM"
    RELATIONSHIP_CREATED = "RELATIONSHIP_CREATED"
    RELATIONSHIP_DATA_CHANGE = "RELATIONSHIP_DATA_CHANGE"
    RELATIONSHIP_SCHEMA_CHANGE = "RELATIONSHIP_SCHEMA_CHANGE"
    RELATIONSHIP_DELETED = "RELATIONSHIP_DELETED"
    DELETED = "DELETED"


INTRINSIC_KINDS = {
    EventKind.CREATED,
    EventKind.RENAME,
    EventKind.DATA_CHANGE,
    EventKind.SCHEMA_CHANGE,
    EventKind.DELETED,
}
RELATIONSHIP_KINDS = {
    EventKind.RELATIONSHIP_CREATED,
    EventKind.RELATIONSHIP_DATA_CHANGE,
    EventKind.RELATIONSHIP_SCHEMA_CHANGE,
    EventKind.RELATIONSHIP_DELETED,
}


@dataclass(frozen=True, slots=True)
class IntrinsicLifecycleEvent:
    id: UUID
    occurred_at: datetime
    kind: EventKind
    object_id: UUID
    canonical_name: str
    before: Object | None
    after: Object | None


@dataclass(frozen=True, slots=True)
class OwnershipLifecycleEvent:
    id: UUID
    occurred_at: datetime
    kind: EventKind
    object_id: UUID
    canonical_name: str
    destination_object_id: UUID
    destination_canonical_name: str
    slot_declaring_template_id: UUID
    slot_name: str
    before: None = None
    after: None = None


@dataclass(frozen=True, slots=True)
class RelationshipFactualState:
    relationship_definition_version: int
    properties: dict[str, JsonValue]


@dataclass(frozen=True, slots=True)
class RelationshipLifecycleEvent:
    id: UUID
    occurred_at: datetime
    kind: EventKind
    object_id: UUID
    canonical_name: str
    destination_object_id: UUID
    destination_canonical_name: str
    relationship_id: UUID
    relationship_definition_id: UUID
    relationship_name: str
    before: RelationshipFactualState | None
    after: RelationshipFactualState | None


type LifecycleEvent = (
    IntrinsicLifecycleEvent | OwnershipLifecycleEvent | RelationshipLifecycleEvent
)


def object_snapshot(value: Object) -> dict[str, JsonValue]:
    return {
        "id": str(value.id),
        "canonical_name": value.canonical_name,
        "template_id": str(value.template_id),
        "template_version": value.template_version,
        "properties": value.properties,
    }


_HISTORICAL_PROPERTY_NAME = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")


def decode_historical_properties(raw: object) -> dict[str, JsonValue]:
    """Decode the sole historical runtime-property carrier grammar."""
    if not isinstance(raw, dict):
        raise RuntimeError("persisted lifecycle properties are invalid")
    candidate = cast(dict[object, object], raw)
    if not all(
        isinstance(name, str) and _HISTORICAL_PROPERTY_NAME.fullmatch(name)
        for name in candidate
    ):
        raise RuntimeError("persisted lifecycle properties are invalid")
    result: dict[str, JsonValue] = {}
    for raw_name, value in candidate.items():
        name = cast(str, raw_name)
        if isinstance(value, (str, bool)) or (
            isinstance(value, int) and not isinstance(value, bool)
        ):
            result[name] = value
            continue
        if not isinstance(value, list) or not value:
            raise RuntimeError("persisted lifecycle property carrier is invalid")
        items = cast(list[object], value)
        kinds: set[type[object]] = set()
        for item in items:
            if isinstance(item, bool):
                kinds.add(bool)
            elif isinstance(item, int):
                kinds.add(int)
            elif isinstance(item, str):
                kinds.add(str)
            else:
                raise RuntimeError("persisted lifecycle property carrier is invalid")
        if len(kinds) != 1:
            raise RuntimeError("persisted lifecycle property carrier is invalid")
        result[name] = cast(list[JsonValue], items)
    return result


def decode_relationship_factual_state(
    raw: object,
) -> RelationshipFactualState | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise RuntimeError("persisted Relationship factual state is invalid")
    value = cast(dict[object, object], raw)
    if set(value) != {"relationship_definition_version", "properties"}:
        raise RuntimeError("persisted Relationship factual state is invalid")
    version = value["relationship_definition_version"]
    if isinstance(version, bool) or not isinstance(version, int) or version <= 0:
        raise RuntimeError("persisted Relationship factual state is invalid")
    return RelationshipFactualState(
        version, decode_historical_properties(value["properties"])
    )


def decode_object_snapshot(raw: object) -> Object | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise RuntimeError("persisted lifecycle snapshot has invalid shape")
    value = cast(dict[object, object], raw)
    if set(value) != {
        "id",
        "canonical_name",
        "template_id",
        "template_version",
        "properties",
    }:
        raise RuntimeError("persisted lifecycle snapshot has invalid shape")
    name = value["canonical_name"]
    version = value["template_version"]
    if (
        not isinstance(name, str)
        or not 1 <= len(name) <= 255
        or isinstance(version, bool)
        or not isinstance(version, int)
        or version <= 0
    ):
        raise RuntimeError("persisted lifecycle snapshot is invalid")
    raw_id = value["id"]
    raw_template_id = value["template_id"]
    if not isinstance(raw_id, str) or not isinstance(raw_template_id, str):
        raise RuntimeError("persisted lifecycle snapshot UUID is invalid")
    try:
        object_id = UUID(raw_id)
        template_id = UUID(raw_template_id)
    except (TypeError, ValueError) as error:
        raise RuntimeError("persisted lifecycle snapshot UUID is invalid") from error
    return Object(
        object_id,
        name,
        template_id,
        version,
        decode_historical_properties(value["properties"]),
    )


def decode_lifecycle_event(row: RowMapping) -> LifecycleEvent:
    try:
        kind = EventKind(cast(str, row["kind"]))
    except ValueError as error:
        raise RuntimeError("persisted lifecycle kind is invalid") from error
    if kind in RELATIONSHIP_KINDS:
        destination_id = cast(UUID | None, row["destination_object_id"])
        destination_name = cast(str | None, row["destination_canonical_name"])
        relationship_id = cast(UUID | None, row["relationship_id"])
        definition_id = cast(UUID | None, row["relationship_definition_id"])
        relationship_name = cast(str | None, row["relationship_name"])
        if (
            destination_id is None
            or destination_name is None
            or relationship_id is None
            or definition_id is None
            or relationship_name is None
            or row["slot_declaring_template_id"] is not None
            or row["slot_name"] is not None
        ):
            raise RuntimeError("persisted Relationship lifecycle event is incoherent")
        before = decode_relationship_factual_state(row["before_state"])
        after = decode_relationship_factual_state(row["after_state"])
        if (
            kind is EventKind.RELATIONSHIP_CREATED
            and (before is not None or after is None)
        ) or (
            kind is EventKind.RELATIONSHIP_DELETED
            and (before is None or after is not None)
        ):
            raise RuntimeError("persisted Relationship lifecycle event is incoherent")
        if kind in {
            EventKind.RELATIONSHIP_DATA_CHANGE,
            EventKind.RELATIONSHIP_SCHEMA_CHANGE,
        } and (before is None or after is None):
            raise RuntimeError("persisted Relationship lifecycle event is incoherent")
        if (
            kind is EventKind.RELATIONSHIP_DATA_CHANGE
            and before is not None
            and after is not None
            and (
                before.relationship_definition_version
                != after.relationship_definition_version
                or before.properties == after.properties
            )
        ):
            raise RuntimeError("persisted Relationship DATA_CHANGE is incoherent")
        if (
            kind is EventKind.RELATIONSHIP_SCHEMA_CHANGE
            and before is not None
            and after is not None
            and after.relationship_definition_version
            <= before.relationship_definition_version
        ):
            raise RuntimeError("persisted Relationship SCHEMA_CHANGE is incoherent")
        return RelationshipLifecycleEvent(
            id=cast(UUID, row["id"]),
            occurred_at=cast(datetime, row["occurred_at"]),
            kind=kind,
            object_id=cast(UUID, row["object_id"]),
            canonical_name=cast(str, row["canonical_name"]),
            destination_object_id=destination_id,
            destination_canonical_name=destination_name,
            relationship_id=relationship_id,
            relationship_definition_id=definition_id,
            relationship_name=relationship_name,
            before=before,
            after=after,
        )
    if kind in {EventKind.ATTACH_TO, EventKind.DETACH_FROM}:
        destination_id = cast(UUID | None, row["destination_object_id"])
        destination_name = cast(str | None, row["destination_canonical_name"])
        declaring_id = cast(UUID | None, row["slot_declaring_template_id"])
        slot_name = cast(str | None, row["slot_name"])
        if (
            destination_id is None
            or destination_name is None
            or declaring_id is None
            or slot_name is None
            or row["before_state"] is not None
            or row["after_state"] is not None
        ):
            raise RuntimeError("persisted ownership lifecycle event is incoherent")
        return OwnershipLifecycleEvent(
            id=cast(UUID, row["id"]),
            occurred_at=cast(datetime, row["occurred_at"]),
            kind=kind,
            object_id=cast(UUID, row["object_id"]),
            canonical_name=cast(str, row["canonical_name"]),
            destination_object_id=destination_id,
            destination_canonical_name=destination_name,
            slot_declaring_template_id=declaring_id,
            slot_name=slot_name,
        )
    if kind not in INTRINSIC_KINDS:
        raise RuntimeError("unsupported persisted lifecycle event family")
    before = decode_object_snapshot(row["before_state"])
    after = decode_object_snapshot(row["after_state"])
    object_id = cast(UUID, row["object_id"])
    name = cast(str, row["canonical_name"])
    if (
        (kind is EventKind.CREATED and (before is not None or after is None))
        or (kind is EventKind.DELETED and (before is None or after is not None))
        or (
            kind in {EventKind.RENAME, EventKind.DATA_CHANGE, EventKind.SCHEMA_CHANGE}
            and (before is None or after is None)
        )
        or (before is not None and before.id != object_id)
        or (after is not None and after.id != object_id)
        or (after is not None and after.canonical_name != name)
    ):
        raise RuntimeError("persisted intrinsic lifecycle event is incoherent")
    if kind is EventKind.RENAME and before is not None and after is not None:
        if (
            before.template_id != after.template_id
            or before.template_version != after.template_version
            or before.properties != after.properties
        ):
            raise RuntimeError("persisted RENAME event is incoherent")
    if kind is EventKind.DATA_CHANGE and before is not None and after is not None:
        if (
            before.canonical_name != after.canonical_name
            or before.template_id != after.template_id
            or before.template_version != after.template_version
            or before.properties == after.properties
        ):
            raise RuntimeError("persisted DATA_CHANGE event is incoherent")
    if kind is EventKind.SCHEMA_CHANGE and before is not None and after is not None:
        if (
            before.canonical_name != after.canonical_name
            or before.template_id != after.template_id
            or after.template_version <= before.template_version
        ):
            raise RuntimeError("persisted SCHEMA_CHANGE event is incoherent")
    if kind is EventKind.DELETED and before is not None:
        if before.canonical_name != name:
            raise RuntimeError("persisted DELETED event is incoherent")
    return IntrinsicLifecycleEvent(
        id=cast(UUID, row["id"]),
        occurred_at=cast(datetime, row["occurred_at"]),
        kind=kind,
        object_id=object_id,
        canonical_name=name,
        before=before,
        after=after,
    )


def _relationship_state(value: Relationship) -> dict[str, JsonValue]:
    return {
        "relationship_definition_version": value.relationship_definition_version,
        "properties": value.properties,
    }


class LifecycleStore:
    """Sole SQL/codec boundary for the shared lifecycle event table."""

    def __init__(self, connection: AsyncConnection) -> None:
        self.connection = connection

    async def insert_intrinsic_event(
        self,
        kind: EventKind,
        value: Object,
        before: Object | None,
        after: Object | None,
    ) -> IntrinsicLifecycleEvent:
        row = (
            (
                await self.connection.execute(
                    object_lifecycle_events.insert()
                    .values(
                        kind=kind.value,
                        object_id=value.id,
                        canonical_name=value.canonical_name,
                        before_state=null()
                        if before is None
                        else object_snapshot(before),
                        after_state=null() if after is None else object_snapshot(after),
                    )
                    .returning(object_lifecycle_events)
                )
            )
            .mappings()
            .one()
        )
        event = decode_lifecycle_event(row)
        if not isinstance(event, IntrinsicLifecycleEvent):
            raise RuntimeError("persisted intrinsic lifecycle event family mismatch")
        return event

    async def insert_ownership_event(
        self,
        kind: EventKind,
        *,
        child: Object,
        parent: Object,
        slot_declaring_template_id: UUID,
        slot_name: str,
    ) -> OwnershipLifecycleEvent:
        if kind not in {EventKind.ATTACH_TO, EventKind.DETACH_FROM}:
            raise ValueError("ownership lifecycle kind required")
        row = (
            (
                await self.connection.execute(
                    object_lifecycle_events.insert()
                    .values(
                        kind=kind.value,
                        object_id=child.id,
                        canonical_name=child.canonical_name,
                        destination_object_id=parent.id,
                        destination_canonical_name=parent.canonical_name,
                        slot_declaring_template_id=slot_declaring_template_id,
                        slot_name=slot_name,
                    )
                    .returning(object_lifecycle_events)
                )
            )
            .mappings()
            .one()
        )
        event = decode_lifecycle_event(row)
        if not isinstance(event, OwnershipLifecycleEvent):
            raise RuntimeError("persisted ownership lifecycle event family mismatch")
        return event

    async def relationship_views(
        self, relationship: Relationship
    ) -> tuple[RelationshipLifecycleView, ...]:
        """Capture every historical display name in one authoritative statement."""
        from_objects = objects.alias("relationship_from_objects")
        to_objects = objects.alias("relationship_to_objects")
        rows = (
            await self.connection.execute(
                select(
                    runtime_relationship_resolutions.c.relationship_definition_id,
                    runtime_relationship_resolutions.c.resolution_id,
                    runtime_relationship_resolutions.c.from_object_id,
                    from_objects.c.canonical_name.label("from_canonical_name"),
                    runtime_relationship_resolutions.c.to_object_id,
                    to_objects.c.canonical_name.label("to_canonical_name"),
                    relationship_resolutions.c.name,
                )
                .select_from(
                    runtime_relationship_resolutions.join(
                        relationship_resolutions,
                        relationship_resolutions.c.id
                        == runtime_relationship_resolutions.c.resolution_id,
                    )
                    .join(
                        from_objects,
                        from_objects.c.id
                        == runtime_relationship_resolutions.c.from_object_id,
                    )
                    .join(
                        to_objects,
                        to_objects.c.id
                        == runtime_relationship_resolutions.c.to_object_id,
                    )
                )
                .where(
                    runtime_relationship_resolutions.c.relationship_id
                    == relationship.id
                )
            )
        ).all()
        expected = {
            (item.resolution_id, item.from_object_id, item.to_object_id)
            for item in relationship.resolutions
        }
        actual = {
            (
                cast(UUID, row.resolution_id),
                cast(UUID, row.from_object_id),
                cast(UUID, row.to_object_id),
            )
            for row in rows
            if row.relationship_definition_id == relationship.relationship_definition_id
        }
        if not expected or actual != expected or len(rows) != len(expected):
            raise RuntimeError("Relationship lifecycle projection is incomplete")
        views = {
            RelationshipLifecycleView(
                object_id=cast(UUID, row.from_object_id),
                canonical_name=cast(str, row.from_canonical_name),
                destination_object_id=cast(UUID, row.to_object_id),
                destination_canonical_name=cast(str, row.to_canonical_name),
                relationship_name=cast(str, row.name),
            )
            for row in rows
        }
        if not views:
            raise RuntimeError("Relationship lifecycle projection is incomplete")
        return tuple(
            sorted(
                views,
                key=lambda item: (
                    item.object_id.int,
                    item.destination_object_id.int,
                    item.relationship_name,
                ),
            )
        )

    async def insert_relationship_events(
        self,
        *,
        kind: EventKind,
        before: Relationship | None,
        after: Relationship | None,
        views: Sequence[RelationshipLifecycleView],
    ) -> None:
        factual = after if after is not None else before
        if factual is None or kind not in RELATIONSHIP_KINDS:
            raise RuntimeError("unsupported Relationship lifecycle transition")
        if (
            before is not None
            and after is not None
            and (
                before.id != after.id
                or before.relationship_definition_id != after.relationship_definition_id
                or before.resolutions != after.resolutions
            )
        ):
            raise RuntimeError("incoherent Relationship lifecycle transition")
        if kind is EventKind.RELATIONSHIP_CREATED:
            valid = before is None and after is not None
        elif kind is EventKind.RELATIONSHIP_DELETED:
            valid = before is not None and after is None
        elif kind is EventKind.RELATIONSHIP_DATA_CHANGE:
            valid = (
                before is not None
                and after is not None
                and before.relationship_definition_version
                == after.relationship_definition_version
                and before.properties != after.properties
            )
        else:
            valid = (
                before is not None
                and after is not None
                and after.relationship_definition_version
                > before.relationship_definition_version
            )
        if not valid:
            raise RuntimeError("incoherent Relationship lifecycle transition")
        ordered_views = tuple(
            sorted(
                set(views),
                key=lambda item: (
                    item.object_id.int,
                    item.destination_object_id.int,
                    item.relationship_name,
                ),
            )
        )
        if not ordered_views or len(ordered_views) != len(views):
            raise RuntimeError("Relationship lifecycle projection is incomplete")
        before_state = None if before is None else _relationship_state(before)
        after_state = None if after is None else _relationship_state(after)
        await self.connection.execute(
            object_lifecycle_events.insert(),
            [
                {
                    "kind": kind.value,
                    "object_id": item.object_id,
                    "canonical_name": item.canonical_name,
                    "destination_object_id": item.destination_object_id,
                    "destination_canonical_name": item.destination_canonical_name,
                    "relationship_id": factual.id,
                    "relationship_definition_id": (factual.relationship_definition_id),
                    "relationship_name": item.relationship_name,
                    "before_state": before_state,
                    "after_state": after_state,
                }
                for item in ordered_views
            ],
        )

    async def list_events(
        self,
        *,
        kind: EventKind | None,
        object_id: UUID | None,
        destination_object_id: UUID | None,
        relationship_id: UUID | None,
        relationship_definition_id: UUID | None,
        relationship_name: str | None,
        occurred_from: datetime | None,
        occurred_to: datetime | None,
        involving_object_id: UUID | None,
        after: tuple[datetime, UUID] | None,
        limit: int,
    ) -> Sequence[LifecycleEvent]:
        statement = select(object_lifecycle_events)
        if kind is not None:
            statement = statement.where(object_lifecycle_events.c.kind == kind.value)
        if object_id is not None:
            statement = statement.where(
                object_lifecycle_events.c.object_id == object_id
            )
        if destination_object_id is not None:
            statement = statement.where(
                object_lifecycle_events.c.destination_object_id == destination_object_id
            )
        if relationship_id is not None:
            statement = statement.where(
                object_lifecycle_events.c.relationship_id == relationship_id
            )
        if relationship_definition_id is not None:
            statement = statement.where(
                object_lifecycle_events.c.relationship_definition_id
                == relationship_definition_id
            )
        if relationship_name is not None:
            statement = statement.where(
                object_lifecycle_events.c.relationship_name == relationship_name
            )
        if occurred_from is not None:
            statement = statement.where(
                object_lifecycle_events.c.occurred_at >= occurred_from
            )
        if occurred_to is not None:
            statement = statement.where(
                object_lifecycle_events.c.occurred_at <= occurred_to
            )
        if involving_object_id is not None:
            statement = statement.where(
                or_(
                    object_lifecycle_events.c.object_id == involving_object_id,
                    object_lifecycle_events.c.destination_object_id
                    == involving_object_id,
                )
            )
        if after is not None:
            statement = statement.where(
                tuple_(
                    object_lifecycle_events.c.occurred_at,
                    object_lifecycle_events.c.id,
                )
                < after
            )
        rows = (
            (
                await self.connection.execute(
                    statement.order_by(
                        object_lifecycle_events.c.occurred_at.desc(),
                        object_lifecycle_events.c.id.desc(),
                    ).limit(limit)
                )
            )
            .mappings()
            .all()
        )
        return [decode_lifecycle_event(row) for row in rows]
