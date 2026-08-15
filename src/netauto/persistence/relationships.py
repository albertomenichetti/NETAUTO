"""SQLAlchemy Core persistence for RelationshipDefinition aggregates."""

from collections.abc import Iterable, Sequence
from typing import cast
from uuid import UUID

from sqlalchemy import case, func, select, tuple_
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection

from netauto.domain.relationships import (
    ObjectRelationshipView,
    Relationship,
    RelationshipCapability,
    RelationshipDefinition,
    RelationshipLifecycleView,
    RelationshipResolution,
    RuntimeRelationshipResolution,
)
from netauto.persistence.metadata import (
    object_lifecycle_events,
    object_templates,
    objects,
    relationship_definitions,
    relationship_resolutions,
    relationships,
    runtime_relationship_resolutions,
)


class RelationshipEndpointReferenceError(Exception):
    def __init__(self, template_id: UUID) -> None:
        self.template_id = template_id
        super().__init__("RelationshipDefinition endpoint lineage disappeared")


class RelationshipDefinitionDeleteReferenceError(Exception):
    pass


class ExactRelationshipViewCollision(Exception):
    pass


class RuntimeRelationshipModelReferenceError(Exception):
    pass


class RuntimeRelationshipObjectReferenceError(Exception):
    def __init__(self, object_id: UUID) -> None:
        self.object_id = object_id
        super().__init__("Relationship endpoint Object disappeared")


def _aggregate_statement():
    return select(
        relationship_definitions.c.id.label("definition_id"),
        relationship_definitions.c.symmetric,
        relationship_resolutions.c.id.label("resolution_id"),
        relationship_resolutions.c.relationship_definition_id,
        relationship_resolutions.c.from_template_id,
        relationship_resolutions.c.to_template_id,
        relationship_resolutions.c.name,
    ).select_from(
        relationship_definitions.outerjoin(
            relationship_resolutions,
            relationship_resolutions.c.relationship_definition_id
            == relationship_definitions.c.id,
        )
    )


def _decode_aggregates(
    rows: Sequence[RowMapping],
) -> tuple[RelationshipDefinition, ...]:
    definitions: list[RelationshipDefinition] = []
    current_id: UUID | None = None
    current_symmetric = False
    resolutions: list[RelationshipResolution] = []

    def append_current() -> None:
        if current_id is not None:
            definitions.append(
                RelationshipDefinition(
                    current_id, current_symmetric, tuple(resolutions)
                )
            )

    for row in rows:
        definition_id = cast(UUID, row["definition_id"])
        if definition_id != current_id:
            append_current()
            current_id = definition_id
            current_symmetric = cast(bool, row["symmetric"])
            resolutions = []
        resolution_id = cast(UUID | None, row["resolution_id"])
        if resolution_id is not None:
            resolutions.append(
                RelationshipResolution(
                    resolution_id,
                    cast(UUID, row["relationship_definition_id"]),
                    cast(UUID, row["from_template_id"]),
                    cast(UUID, row["to_template_id"]),
                    cast(str, row["name"]),
                )
            )
    append_current()
    return tuple(definitions)


class RelationshipDefinitionStore:
    def __init__(self, connection: AsyncConnection) -> None:
        self.connection = connection

    async def insert(self, value: RelationshipDefinition) -> None:
        await self.connection.execute(
            relationship_definitions.insert().values(
                id=value.id, symmetric=value.symmetric
            )
        )
        for item in value.resolutions:
            try:
                await self.connection.execute(
                    relationship_resolutions.insert().values(
                        id=item.id,
                        relationship_definition_id=item.relationship_definition_id,
                        from_template_id=item.from_template_id,
                        to_template_id=item.to_template_id,
                        name=item.name,
                    )
                )
            except IntegrityError as error:
                diagnostic = getattr(getattr(error, "orig", None), "diag", None)
                constraint_name = getattr(diagnostic, "constraint_name", None)
                if constraint_name == "fk_relationship_resolutions_from_template":
                    raise RelationshipEndpointReferenceError(
                        item.from_template_id
                    ) from error
                if constraint_name == "fk_relationship_resolutions_to_template":
                    raise RelationshipEndpointReferenceError(
                        item.to_template_id
                    ) from error
                raise

    async def get(self, definition_id: UUID) -> RelationshipDefinition | None:
        rows = (
            (
                await self.connection.execute(
                    _aggregate_statement()
                    .where(relationship_definitions.c.id == definition_id)
                    .order_by(
                        relationship_definitions.c.id,
                        relationship_resolutions.c.id,
                    )
                )
            )
            .mappings()
            .all()
        )
        decoded = _decode_aggregates(rows)
        return None if not decoded else decoded[0]

    async def get_by_resolution(
        self, resolution_id: UUID
    ) -> RelationshipDefinition | None:
        definition_id = await self.connection.scalar(
            select(relationship_resolutions.c.relationship_definition_id).where(
                relationship_resolutions.c.id == resolution_id
            )
        )
        if definition_id is None:
            return None
        return await self.get(cast(UUID, definition_id))

    async def certified_set(self) -> tuple[RelationshipDefinition, ...]:
        rows = (
            (
                await self.connection.execute(
                    _aggregate_statement().order_by(
                        relationship_definitions.c.id,
                        relationship_resolutions.c.id,
                    )
                )
            )
            .mappings()
            .all()
        )
        return _decode_aggregates(rows)

    async def list_definitions(
        self, *, after: UUID | None, limit: int
    ) -> tuple[RelationshipDefinition, ...]:
        page_statement = select(relationship_definitions.c.id)
        if after is not None:
            page_statement = page_statement.where(relationship_definitions.c.id > after)
        page = (
            page_statement.order_by(relationship_definitions.c.id)
            .limit(limit)
            .cte("relationship_definition_page")
        )
        statement = (
            _aggregate_statement()
            .join(page, page.c.id == relationship_definitions.c.id)
            .order_by(
                relationship_definitions.c.id,
                relationship_resolutions.c.id,
            )
        )
        rows = (await self.connection.execute(statement)).mappings().all()
        return _decode_aggregates(rows)

    async def lock_no_key(self, definition_id: UUID) -> bool:
        row = (
            await self.connection.execute(
                select(relationship_definitions.c.id)
                .where(relationship_definitions.c.id == definition_id)
                .with_for_update(key_share=True)
            )
        ).first()
        return row is not None

    async def lock_update(self, definition_id: UUID) -> bool:
        row = (
            await self.connection.execute(
                select(relationship_definitions.c.id)
                .where(relationship_definitions.c.id == definition_id)
                .with_for_update()
            )
        ).first()
        return row is not None

    async def update_names(self, value: RelationshipDefinition) -> None:
        names = {item.id: item.name for item in value.resolutions}
        result = await self.connection.execute(
            relationship_resolutions.update()
            .where(
                relationship_resolutions.c.relationship_definition_id == value.id,
                relationship_resolutions.c.id.in_(tuple(names)),
            )
            .values(name=case(names, value=relationship_resolutions.c.id))
        )
        if result.rowcount != len(names):
            raise RuntimeError(
                "complete RelationshipResolution rename set was not updated"
            )

    async def current_relationship_count(self, definition_id: UUID) -> int:
        value = await self.connection.scalar(
            select(func.count())
            .select_from(relationships)
            .where(relationships.c.relationship_definition_id == definition_id)
        )
        return int(value or 0)

    async def delete(self, definition_id: UUID) -> None:
        try:
            await self.connection.execute(
                relationship_definitions.delete().where(
                    relationship_definitions.c.id == definition_id
                )
            )
        except IntegrityError as error:
            diagnostic = getattr(getattr(error, "orig", None), "diag", None)
            if getattr(diagnostic, "constraint_name", None) == (
                "fk_relationships_definition"
            ):
                raise RelationshipDefinitionDeleteReferenceError from error
            raise

    async def lineage_parents(self) -> dict[UUID, UUID | None]:
        rows = (
            await self.connection.execute(
                select(object_templates.c.id, object_templates.c.parent_template_id)
            )
        ).all()
        return {
            cast(UUID, row.id): cast(UUID | None, row.parent_template_id)
            for row in rows
        }

    async def list_capabilities(
        self,
        *,
        applicable_from_template_ids: Iterable[UUID],
        name: str | None,
        after: UUID | None,
        limit: int,
    ) -> tuple[RelationshipCapability, ...]:
        statement = select(
            relationship_resolutions.c.id,
            relationship_resolutions.c.relationship_definition_id,
            relationship_resolutions.c.name,
            relationship_resolutions.c.from_template_id,
            relationship_resolutions.c.to_template_id,
        ).where(
            relationship_resolutions.c.from_template_id.in_(
                tuple(applicable_from_template_ids)
            )
        )
        if name is not None:
            statement = statement.where(relationship_resolutions.c.name == name)
        if after is not None:
            statement = statement.where(relationship_resolutions.c.id > after)
        rows = (
            (
                await self.connection.execute(
                    statement.order_by(relationship_resolutions.c.id).limit(limit)
                )
            )
            .mappings()
            .all()
        )
        return tuple(
            RelationshipCapability(
                resolution_id=cast(UUID, row["id"]),
                relationship_definition_id=cast(
                    UUID, row["relationship_definition_id"]
                ),
                name=cast(str, row["name"]),
                from_template_id=cast(UUID, row["from_template_id"]),
                to_template_id=cast(UUID, row["to_template_id"]),
            )
            for row in rows
        )


def _runtime_relationship(rows: Sequence[RowMapping]) -> Relationship | None:
    if not rows:
        return None
    relationship_id = cast(UUID, rows[0]["relationship_id"])
    definition_id = cast(UUID, rows[0]["relationship_definition_id"])
    resolutions: list[RuntimeRelationshipResolution] = []
    for row in rows:
        resolution_id = cast(UUID | None, row["resolution_id"])
        if resolution_id is None:
            continue
        resolutions.append(
            RuntimeRelationshipResolution(
                relationship_id=relationship_id,
                relationship_definition_id=cast(
                    UUID, row["runtime_relationship_definition_id"]
                ),
                resolution_id=resolution_id,
                from_object_id=cast(UUID, row["from_object_id"]),
                to_object_id=cast(UUID, row["to_object_id"]),
            )
        )
    return Relationship(relationship_id, definition_id, tuple(resolutions))


class RuntimeRelationshipStore:
    """Persistence boundary for complete factual Relationship aggregates."""

    def __init__(self, connection: AsyncConnection) -> None:
        self.connection = connection

    async def exact_relationship_id(
        self, resolution_id: UUID, from_object_id: UUID, to_object_id: UUID
    ) -> UUID | None:
        value = await self.connection.scalar(
            select(runtime_relationship_resolutions.c.relationship_id).where(
                runtime_relationship_resolutions.c.resolution_id == resolution_id,
                runtime_relationship_resolutions.c.from_object_id == from_object_id,
                runtime_relationship_resolutions.c.to_object_id == to_object_id,
            )
        )
        return None if value is None else cast(UUID, value)

    async def get(self, relationship_id: UUID) -> Relationship | None:
        rows = (
            (
                await self.connection.execute(
                    select(
                        relationships.c.id.label("relationship_id"),
                        relationships.c.relationship_definition_id,
                        runtime_relationship_resolutions.c.relationship_definition_id.label(
                            "runtime_relationship_definition_id"
                        ),
                        runtime_relationship_resolutions.c.resolution_id,
                        runtime_relationship_resolutions.c.from_object_id,
                        runtime_relationship_resolutions.c.to_object_id,
                    )
                    .select_from(
                        relationships.outerjoin(
                            runtime_relationship_resolutions,
                            runtime_relationship_resolutions.c.relationship_id
                            == relationships.c.id,
                        )
                    )
                    .where(relationships.c.id == relationship_id)
                    .order_by(
                        runtime_relationship_resolutions.c.resolution_id,
                        runtime_relationship_resolutions.c.from_object_id,
                        runtime_relationship_resolutions.c.to_object_id,
                    )
                )
            )
            .mappings()
            .all()
        )
        return _runtime_relationship(rows)

    async def lock_update(self, relationship_id: UUID) -> bool:
        row = (
            await self.connection.execute(
                select(relationships.c.id)
                .where(relationships.c.id == relationship_id)
                .with_for_update()
            )
        ).first()
        return row is not None

    async def object_template_ids(self, object_ids: Iterable[UUID]) -> dict[UUID, UUID]:
        ids = tuple(set(object_ids))
        if not ids:
            return {}
        rows = (
            await self.connection.execute(
                select(objects.c.id, objects.c.template_id).where(objects.c.id.in_(ids))
            )
        ).all()
        return {cast(UUID, row.id): cast(UUID, row.template_id) for row in rows}

    async def current_candidate_relationship_ids(
        self, rows: Iterable[RuntimeRelationshipResolution]
    ) -> tuple[UUID, ...]:
        keys = tuple(
            (item.resolution_id, item.from_object_id, item.to_object_id)
            for item in rows
        )
        if not keys:
            return ()
        values = (
            await self.connection.scalars(
                select(runtime_relationship_resolutions.c.relationship_id)
                .where(
                    tuple_(
                        runtime_relationship_resolutions.c.resolution_id,
                        runtime_relationship_resolutions.c.from_object_id,
                        runtime_relationship_resolutions.c.to_object_id,
                    ).in_(keys)
                )
                .distinct()
            )
        ).all()
        return tuple(cast(UUID, value) for value in values)

    async def insert(self, value: Relationship) -> None:
        try:
            await self.connection.execute(
                relationships.insert().values(
                    id=value.id,
                    relationship_definition_id=value.relationship_definition_id,
                )
            )
        except IntegrityError as error:
            diagnostic = getattr(getattr(error, "orig", None), "diag", None)
            if getattr(diagnostic, "constraint_name", None) == (
                "fk_relationships_definition"
            ):
                raise RuntimeRelationshipModelReferenceError from error
            raise
        for item in value.resolutions:
            try:
                await self.connection.execute(
                    runtime_relationship_resolutions.insert().values(
                        relationship_id=item.relationship_id,
                        relationship_definition_id=item.relationship_definition_id,
                        resolution_id=item.resolution_id,
                        from_object_id=item.from_object_id,
                        to_object_id=item.to_object_id,
                    )
                )
            except IntegrityError as error:
                diagnostic = getattr(getattr(error, "orig", None), "diag", None)
                constraint_name = getattr(diagnostic, "constraint_name", None)
                if constraint_name == "runtime_relationship_resolutions_pkey":
                    raise ExactRelationshipViewCollision from error
                if constraint_name in {
                    "fk_runtime_resolutions_relationship_definition",
                    "fk_runtime_resolutions_resolution_definition",
                }:
                    raise RuntimeRelationshipModelReferenceError from error
                if constraint_name == "fk_runtime_resolutions_from_object":
                    raise RuntimeRelationshipObjectReferenceError(
                        item.from_object_id
                    ) from error
                if constraint_name == "fk_runtime_resolutions_to_object":
                    raise RuntimeRelationshipObjectReferenceError(
                        item.to_object_id
                    ) from error
                raise

    async def lifecycle_views(
        self, relationship_id: UUID
    ) -> tuple[RelationshipLifecycleView, ...]:
        from_objects = objects.alias("relationship_from_objects")
        to_objects = objects.alias("relationship_to_objects")
        rows = (
            await self.connection.execute(
                select(
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
                    == relationship_id
                )
            )
        ).all()
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

    async def insert_lifecycle_events(
        self,
        *,
        kind: str,
        relationship: Relationship,
        views: Sequence[RelationshipLifecycleView],
    ) -> None:
        if not views:
            raise RuntimeError("Relationship lifecycle projection is incomplete")
        await self.connection.execute(
            object_lifecycle_events.insert(),
            [
                {
                    "kind": kind,
                    "object_id": item.object_id,
                    "canonical_name": item.canonical_name,
                    "destination_object_id": item.destination_object_id,
                    "destination_canonical_name": item.destination_canonical_name,
                    "relationship_id": relationship.id,
                    "relationship_definition_id": (
                        relationship.relationship_definition_id
                    ),
                    "relationship_name": item.relationship_name,
                }
                for item in views
            ],
        )

    async def delete(self, relationship_id: UUID) -> None:
        result = await self.connection.execute(
            relationships.delete().where(relationships.c.id == relationship_id)
        )
        if result.rowcount != 1:
            raise RuntimeError("locked Relationship disappeared before delete")

    async def list_object_views(
        self,
        object_id: UUID,
        *,
        relationship_definition_id: UUID | None,
        name: str | None,
        after: tuple[UUID, UUID, str] | None,
        limit: int,
    ) -> tuple[ObjectRelationshipView, ...]:
        statement = (
            select(
                runtime_relationship_resolutions.c.relationship_id,
                runtime_relationship_resolutions.c.relationship_definition_id,
                runtime_relationship_resolutions.c.from_object_id,
                runtime_relationship_resolutions.c.to_object_id,
                relationship_resolutions.c.name,
            )
            .join(
                relationship_resolutions,
                relationship_resolutions.c.id
                == runtime_relationship_resolutions.c.resolution_id,
            )
            .where(runtime_relationship_resolutions.c.from_object_id == object_id)
            .distinct()
        )
        if relationship_definition_id is not None:
            statement = statement.where(
                runtime_relationship_resolutions.c.relationship_definition_id
                == relationship_definition_id
            )
        if name is not None:
            statement = statement.where(relationship_resolutions.c.name == name)
        ordering = (
            runtime_relationship_resolutions.c.relationship_id,
            runtime_relationship_resolutions.c.to_object_id,
            relationship_resolutions.c.name,
        )
        if after is not None:
            statement = statement.where(tuple_(*ordering) > after)
        rows = (
            await self.connection.execute(statement.order_by(*ordering).limit(limit))
        ).all()
        return tuple(
            ObjectRelationshipView(
                relationship_id=cast(UUID, row.relationship_id),
                relationship_definition_id=cast(UUID, row.relationship_definition_id),
                object_id=cast(UUID, row.from_object_id),
                destination_object_id=cast(UUID, row.to_object_id),
                name=cast(str, row.name),
            )
            for row in rows
        )
