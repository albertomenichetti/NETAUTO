"""SQLAlchemy Core persistence for current Object and ownership state."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, cast
from uuid import UUID

from sqlalchemy import func, or_, select, text
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection

from netauto.domain.objects import Object, ObjectSummary
from netauto.domain.primitives import JsonValue
from netauto.persistence.lifecycle import (
    EventKind,
    IntrinsicLifecycleEvent,
    OwnershipLifecycleEvent,
)
from netauto.persistence.locking import (
    RowLockClass,
    RowLockIntent,
    RowLockKey,
    RowLockMode,
    classify_postgresql_failure,
    row_lock_statement,
)
from netauto.persistence.metadata import (
    object_components,
    objects,
    runtime_relationship_resolutions,
)

__all__ = [
    "ComponentPageProjection",
    "ComponentProjection",
    "EventKind",
    "IntrinsicLifecycleEvent",
    "ObjectDeleteReferenceError",
    "ObjectStore",
    "ObjectTemplateReferenceError",
    "OwnerProjection",
    "OwnerReadProjection",
    "OwnershipConflictError",
    "OwnershipFact",
    "OwnershipLifecycleEvent",
    "OwnershipReferenceError",
]


@dataclass(frozen=True, slots=True)
class ComponentProjection:
    slot_declaring_template_id: UUID
    slot_name: str
    child_object_id: UUID


@dataclass(frozen=True, slots=True)
class ComponentPageProjection:
    parent_exists: bool
    items: tuple[ComponentProjection, ...]


@dataclass(frozen=True, slots=True)
class OwnerProjection:
    parent_object_id: UUID
    slot_declaring_template_id: UUID
    slot_name: str


@dataclass(frozen=True, slots=True)
class OwnerReadProjection:
    child_exists: bool
    owner: OwnerProjection | None


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
            classified = classify_postgresql_failure(error)
            if classified.constraint_name == "fk_objects_template_version":
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
        found = (
            await self.connection.execute(
                row_lock_statement(
                    RowLockIntent(
                        RowLockKey(RowLockClass.OBJECT, object_id), RowLockMode.NKU
                    )
                )
            )
        ).first()
        return None if found is None else await self.get(object_id)

    async def lock_update(self, object_id: UUID) -> Object | None:
        found = (
            await self.connection.execute(
                row_lock_statement(
                    RowLockIntent(
                        RowLockKey(RowLockClass.OBJECT, object_id), RowLockMode.U
                    )
                )
            )
        ).first()
        return None if found is None else await self.get(object_id)

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
            constraint = classify_postgresql_failure(error).constraint_name
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

    async def list_component_projections(
        self,
        parent_object_id: UUID,
        *,
        slot_name: str | None,
        after: UUID | None,
        limit: int,
    ) -> ComponentPageProjection:
        conditions = ["edge.parent_object_id = :parent_object_id"]
        parameters: dict[str, object] = {
            "parent_object_id": parent_object_id,
            "limit": limit,
        }
        if slot_name is not None:
            conditions.append("edge.slot_name = :slot_name")
            parameters["slot_name"] = slot_name
        if after is not None:
            conditions.append("edge.child_object_id > :after")
            parameters["after"] = after
        membership = " AND ".join(conditions)
        statement = text(
            f"""
            WITH RECURSIVE exact_chain(
                template_id,
                template_version,
                parent_template_id,
                parent_version
            ) AS (
                SELECT
                    version.template_id,
                    version.version,
                    version.parent_template_id,
                    version.parent_version
                FROM objects AS parent
                JOIN object_template_versions AS version
                  ON version.template_id = parent.template_id
                 AND version.version = parent.template_version
                WHERE parent.id = :parent_object_id

                UNION

                SELECT
                    ancestor.template_id,
                    ancestor.version,
                    ancestor.parent_template_id,
                    ancestor.parent_version
                FROM exact_chain AS child
                JOIN object_template_versions AS ancestor
                  ON ancestor.template_id = child.parent_template_id
                 AND ancestor.version = child.parent_version
            ), component_page AS (
                SELECT
                    edge.child_object_id,
                    edge.parent_object_id,
                    edge.slot_name
                FROM object_components AS edge
                WHERE {membership}
                ORDER BY edge.child_object_id
                LIMIT :limit
            )
            SELECT
                parent.id AS target_id,
                page.child_object_id,
                page.parent_object_id,
                page.slot_name,
                ARRAY(
                    SELECT declaration.template_id
                    FROM exact_chain AS chain
                    JOIN object_template_components AS declaration
                      ON declaration.template_id = chain.template_id
                     AND declaration.template_version = chain.template_version
                     AND declaration.name = page.slot_name
                    ORDER BY declaration.template_id,
                             declaration.template_version
                ) AS slot_declaring_template_ids
            FROM objects AS parent
            LEFT JOIN component_page AS page ON TRUE
            WHERE parent.id = :parent_object_id
            ORDER BY page.child_object_id
            """
        )
        rows = (await self.connection.execute(statement, parameters)).mappings().all()
        if not rows:
            return ComponentPageProjection(False, ())
        items: list[ComponentProjection] = []
        for row in rows:
            child_object_id = cast(UUID | None, row["child_object_id"])
            if child_object_id is None:
                continue
            declaring_ids = cast(Sequence[UUID], row["slot_declaring_template_ids"])
            if len(declaring_ids) != 1:
                raise RuntimeError(
                    "persisted ownership slot declaration context is incomplete"
                )
            items.append(
                ComponentProjection(
                    slot_declaring_template_id=declaring_ids[0],
                    slot_name=cast(str, row["slot_name"]),
                    child_object_id=child_object_id,
                )
            )
        return ComponentPageProjection(True, tuple(items))

    async def get_owner_projection(self, child_object_id: UUID) -> OwnerReadProjection:
        statement = text(
            """
            WITH RECURSIVE exact_chain(
                template_id,
                template_version,
                parent_template_id,
                parent_version
            ) AS (
                SELECT
                    version.template_id,
                    version.version,
                    version.parent_template_id,
                    version.parent_version
                FROM object_components AS edge
                JOIN objects AS parent ON parent.id = edge.parent_object_id
                JOIN object_template_versions AS version
                  ON version.template_id = parent.template_id
                 AND version.version = parent.template_version
                WHERE edge.child_object_id = :child_object_id

                UNION

                SELECT
                    ancestor.template_id,
                    ancestor.version,
                    ancestor.parent_template_id,
                    ancestor.parent_version
                FROM exact_chain AS child
                JOIN object_template_versions AS ancestor
                  ON ancestor.template_id = child.parent_template_id
                 AND ancestor.version = child.parent_version
            )
            SELECT
                child.id AS target_id,
                edge.parent_object_id,
                edge.slot_name,
                ARRAY(
                    SELECT declaration.template_id
                    FROM exact_chain AS chain
                    JOIN object_template_components AS declaration
                      ON declaration.template_id = chain.template_id
                     AND declaration.template_version = chain.template_version
                     AND declaration.name = edge.slot_name
                    ORDER BY declaration.template_id,
                             declaration.template_version
                ) AS slot_declaring_template_ids
            FROM objects AS child
            LEFT JOIN object_components AS edge
              ON edge.child_object_id = child.id
            WHERE child.id = :child_object_id
            """
        )
        row = (
            (
                await self.connection.execute(
                    statement, {"child_object_id": child_object_id}
                )
            )
            .mappings()
            .first()
        )
        if row is None:
            return OwnerReadProjection(False, None)
        parent_object_id = cast(UUID | None, row["parent_object_id"])
        if parent_object_id is None:
            return OwnerReadProjection(True, None)
        declaring_ids = cast(Sequence[UUID], row["slot_declaring_template_ids"])
        if len(declaring_ids) != 1:
            raise RuntimeError(
                "persisted ownership slot declaration context is incomplete"
            )
        return OwnerReadProjection(
            True,
            OwnerProjection(
                parent_object_id=parent_object_id,
                slot_declaring_template_id=declaring_ids[0],
                slot_name=cast(str, row["slot_name"]),
            ),
        )

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
            name = classify_postgresql_failure(error).constraint_name
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
