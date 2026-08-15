"""SQLAlchemy Core persistence for RelationshipDefinition aggregates."""

from collections.abc import Iterable, Sequence
from typing import cast
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection

from netauto.domain.relationships import (
    RelationshipCapability,
    RelationshipDefinition,
    RelationshipResolution,
)
from netauto.persistence.metadata import (
    object_templates,
    relationship_definitions,
    relationship_resolutions,
    relationships,
)


class RelationshipEndpointReferenceError(Exception):
    def __init__(self, template_id: UUID) -> None:
        self.template_id = template_id
        super().__init__("RelationshipDefinition endpoint lineage disappeared")


class RelationshipDefinitionDeleteReferenceError(Exception):
    pass


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
