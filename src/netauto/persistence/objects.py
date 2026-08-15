"""SQLAlchemy Core persistence for intrinsic Object state and lifecycle events."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Literal, cast
from uuid import UUID

from sqlalchemy import func, null, or_, select, text, tuple_
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection

from netauto.domain.objects import Object, ObjectSummary
from netauto.domain.primitives import JsonValue
from netauto.persistence.metadata import (
    object_components,
    object_lifecycle_events,
    objects,
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
    RELATIONSHIP_DELETED = "RELATIONSHIP_DELETED"
    DELETED = "DELETED"


INTRINSIC_KINDS = {
    EventKind.CREATED,
    EventKind.RENAME,
    EventKind.DATA_CHANGE,
    EventKind.SCHEMA_CHANGE,
    EventKind.DELETED,
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
    before: None = None
    after: None = None


type LifecycleEvent = (
    IntrinsicLifecycleEvent | OwnershipLifecycleEvent | RelationshipLifecycleEvent
)


@dataclass(frozen=True, slots=True)
class OwnershipFact:
    child_object_id: UUID
    parent_object_id: UUID
    slot_name: str


class ObjectTemplateReferenceError(Exception):
    pass


class OwnershipConflictError(Exception):
    pass


class OwnershipReferenceError(Exception):
    pass


type ObjectDeleteBlockerType = Literal["ownership", "relationship"]


class ObjectDeleteReferenceError(Exception):
    def __init__(self, blocker_type: ObjectDeleteBlockerType) -> None:
        self.blocker_type = blocker_type
        super().__init__("Object deletion is blocked by a current reference")


def _object(row: RowMapping) -> Object:
    properties = cast(object, row["properties"])
    if not isinstance(properties, dict):
        raise RuntimeError("persisted Object properties are invalid")
    raw_properties = cast(dict[object, object], properties)
    if not all(isinstance(key, str) for key in raw_properties):
        raise RuntimeError("persisted Object properties are invalid")
    return Object(
        id=cast(UUID, row["id"]),
        canonical_name=cast(str, row["canonical_name"]),
        template_id=cast(UUID, row["template_id"]),
        template_version=cast(int, row["template_version"]),
        properties=cast(dict[str, JsonValue], raw_properties),
    )


def _summary(row: RowMapping) -> ObjectSummary:
    return ObjectSummary(
        id=cast(UUID, row["id"]),
        canonical_name=cast(str, row["canonical_name"]),
        template_id=cast(UUID, row["template_id"]),
        template_version=cast(int, row["template_version"]),
    )


def snapshot(value: Object) -> dict[str, JsonValue]:
    return {
        "id": str(value.id),
        "canonical_name": value.canonical_name,
        "template_id": str(value.template_id),
        "template_version": value.template_version,
        "properties": value.properties,
    }


def _snapshot(raw: object) -> Object | None:
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
    properties = value["properties"]
    if (
        not isinstance(name, str)
        or not 1 <= len(name) <= 255
        or isinstance(version, bool)
        or not isinstance(version, int)
        or version <= 0
        or not isinstance(properties, dict)
    ):
        raise RuntimeError("persisted lifecycle snapshot is invalid")
    raw_properties = cast(dict[object, object], properties)
    if not all(isinstance(key, str) for key in raw_properties):
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
        cast(dict[str, JsonValue], raw_properties),
    )


def _event(row: RowMapping) -> LifecycleEvent:
    try:
        kind = EventKind(cast(str, row["kind"]))
    except ValueError as error:
        raise RuntimeError("persisted lifecycle kind is invalid") from error
    if kind in {EventKind.RELATIONSHIP_CREATED, EventKind.RELATIONSHIP_DELETED}:
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
            or row["before_state"] is not None
            or row["after_state"] is not None
        ):
            raise RuntimeError("persisted Relationship lifecycle event is incoherent")
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
    before = _snapshot(row["before_state"])
    after = _snapshot(row["after_state"])
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


class ObjectStore:
    def __init__(self, connection: AsyncConnection) -> None:
        self.connection = connection

    async def insert(self, value: Object) -> None:
        try:
            await self.connection.execute(
                objects.insert().values(
                    id=value.id,
                    canonical_name=value.canonical_name,
                    template_id=value.template_id,
                    template_version=value.template_version,
                    properties=value.properties,
                )
            )
        except IntegrityError as error:
            diagnostic = getattr(getattr(error, "orig", None), "diag", None)
            if getattr(diagnostic, "constraint_name", None) == (
                "fk_objects_template_version"
            ):
                raise ObjectTemplateReferenceError from error
            raise

    async def get(self, object_id: UUID) -> Object | None:
        row = (
            (
                await self.connection.execute(
                    select(objects).where(objects.c.id == object_id)
                )
            )
            .mappings()
            .first()
        )
        return None if row is None else _object(row)

    async def lock_no_key(self, object_id: UUID) -> Object | None:
        row = (
            (
                await self.connection.execute(
                    select(objects)
                    .where(objects.c.id == object_id)
                    .with_for_update(key_share=True)
                )
            )
            .mappings()
            .first()
        )
        return None if row is None else _object(row)

    async def lock_update(self, object_id: UUID) -> Object | None:
        row = (
            (
                await self.connection.execute(
                    select(objects).where(objects.c.id == object_id).with_for_update()
                )
            )
            .mappings()
            .first()
        )
        return None if row is None else _object(row)

    async def delete_blocker_counts(self, object_id: UUID) -> dict[str, int]:
        ownership_count = await self.connection.scalar(
            select(func.count())
            .select_from(object_components)
            .where(
                or_(
                    object_components.c.child_object_id == object_id,
                    object_components.c.parent_object_id == object_id,
                )
            )
        )
        relationship_count = await self.connection.scalar(
            select(
                func.count(
                    func.distinct(runtime_relationship_resolutions.c.relationship_id)
                )
            ).where(
                or_(
                    runtime_relationship_resolutions.c.from_object_id == object_id,
                    runtime_relationship_resolutions.c.to_object_id == object_id,
                )
            )
        )
        return {
            "ownership": int(ownership_count or 0),
            "relationship": int(relationship_count or 0),
        }

    async def delete(self, object_id: UUID) -> None:
        try:
            await self.connection.execute(
                objects.delete().where(objects.c.id == object_id)
            )
        except IntegrityError as error:
            diagnostic = getattr(getattr(error, "orig", None), "diag", None)
            constraint = getattr(diagnostic, "constraint_name", None)
            if constraint in {
                "fk_object_components_child",
                "fk_object_components_parent",
            }:
                raise ObjectDeleteReferenceError("ownership") from error
            if constraint in {
                "fk_runtime_resolutions_from_object",
                "fk_runtime_resolutions_to_object",
            }:
                raise ObjectDeleteReferenceError("relationship") from error
            raise

    async def update_name(self, object_id: UUID, canonical_name: str) -> None:
        await self.connection.execute(
            objects.update()
            .where(objects.c.id == object_id)
            .values(canonical_name=canonical_name)
        )

    async def update_properties(
        self, object_id: UUID, properties: dict[str, JsonValue]
    ) -> None:
        await self.connection.execute(
            objects.update()
            .where(objects.c.id == object_id)
            .values(properties=properties)
        )

    async def update_schema(
        self,
        object_id: UUID,
        template_version: int,
        properties: dict[str, JsonValue],
    ) -> None:
        await self.connection.execute(
            objects.update()
            .where(objects.c.id == object_id)
            .values(template_version=template_version, properties=properties)
        )

    async def get_ownership(self, child_object_id: UUID) -> OwnershipFact | None:
        row = (
            (
                await self.connection.execute(
                    select(object_components).where(
                        object_components.c.child_object_id == child_object_id
                    )
                )
            )
            .mappings()
            .first()
        )
        return None if row is None else self._ownership_fact(row)

    async def list_outgoing(self, parent_object_id: UUID) -> Sequence[OwnershipFact]:
        rows = (
            (
                await self.connection.execute(
                    select(object_components)
                    .where(object_components.c.parent_object_id == parent_object_id)
                    .order_by(object_components.c.child_object_id)
                )
            )
            .mappings()
            .all()
        )
        return [self._ownership_fact(row) for row in rows]

    async def list_components(
        self,
        parent_object_id: UUID,
        *,
        slot_name: str | None,
        after: UUID | None,
        limit: int,
    ) -> Sequence[OwnershipFact]:
        statement = select(object_components).where(
            object_components.c.parent_object_id == parent_object_id
        )
        if slot_name is not None:
            statement = statement.where(object_components.c.slot_name == slot_name)
        if after is not None:
            statement = statement.where(object_components.c.child_object_id > after)
        rows = (
            (
                await self.connection.execute(
                    statement.order_by(object_components.c.child_object_id).limit(limit)
                )
            )
            .mappings()
            .all()
        )
        return [self._ownership_fact(row) for row in rows]

    @staticmethod
    def _ownership_fact(row: RowMapping) -> OwnershipFact:
        return OwnershipFact(
            child_object_id=cast(UUID, row["child_object_id"]),
            parent_object_id=cast(UUID, row["parent_object_id"]),
            slot_name=cast(str, row["slot_name"]),
        )

    async def insert_ownership(self, value: OwnershipFact) -> None:
        try:
            await self.connection.execute(
                object_components.insert().values(
                    child_object_id=value.child_object_id,
                    parent_object_id=value.parent_object_id,
                    slot_name=value.slot_name,
                )
            )
        except IntegrityError as error:
            diagnostic = getattr(getattr(error, "orig", None), "diag", None)
            name = getattr(diagnostic, "constraint_name", None)
            if name == "object_components_pkey":
                raise OwnershipConflictError from error
            if name in {
                "fk_object_components_child",
                "fk_object_components_parent",
            }:
                raise OwnershipReferenceError from error
            raise

    async def delete_ownership(self, value: OwnershipFact) -> bool:
        result = await self.connection.execute(
            object_components.delete().where(
                object_components.c.child_object_id == value.child_object_id,
                object_components.c.parent_object_id == value.parent_object_id,
                object_components.c.slot_name == value.slot_name,
            )
        )
        return result.rowcount == 1

    async def would_create_cycle(
        self, parent_object_id: UUID, child_object_id: UUID
    ) -> bool:
        value = await self.connection.scalar(
            text(
                """
                WITH RECURSIVE descendants(child_object_id) AS (
                    SELECT child_object_id
                    FROM object_components
                    WHERE parent_object_id = :child_object_id
                    UNION
                    SELECT edge.child_object_id
                    FROM object_components AS edge
                    JOIN descendants AS current
                      ON edge.parent_object_id = current.child_object_id
                )
                SELECT EXISTS (
                    SELECT 1 FROM descendants
                    WHERE child_object_id = :parent_object_id
                )
                """
            ),
            {
                "parent_object_id": parent_object_id,
                "child_object_id": child_object_id,
            },
        )
        return bool(value)

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
                        before_state=null() if before is None else snapshot(before),
                        after_state=null() if after is None else snapshot(after),
                    )
                    .returning(object_lifecycle_events)
                )
            )
            .mappings()
            .one()
        )
        event = _event(row)
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
        event = _event(row)
        if not isinstance(event, OwnershipLifecycleEvent):
            raise RuntimeError("persisted ownership lifecycle event family mismatch")
        return event

    async def list_objects(
        self,
        *,
        template_id: UUID | None,
        template_version: int | None,
        canonical_name: str | None,
        after: UUID | None,
        limit: int,
    ) -> Sequence[ObjectSummary]:
        statement = select(
            objects.c.id,
            objects.c.canonical_name,
            objects.c.template_id,
            objects.c.template_version,
        )
        if template_id is not None:
            statement = statement.where(objects.c.template_id == template_id)
        if template_version is not None:
            statement = statement.where(objects.c.template_version == template_version)
        if canonical_name is not None:
            statement = statement.where(objects.c.canonical_name == canonical_name)
        if after is not None:
            statement = statement.where(objects.c.id > after)
        rows = (
            (
                await self.connection.execute(
                    statement.order_by(objects.c.id).limit(limit)
                )
            )
            .mappings()
            .all()
        )
        return [_summary(row) for row in rows]

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
        return [_event(row) for row in rows]
