"""SQLAlchemy Core persistence for RelationshipDefinition aggregates."""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import cast
from uuid import UUID

from sqlalchemy import case, func, select, text, tuple_
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection

from netauto.domain.datatypes import VersionStatus
from netauto.domain.objecttemplates import ValueMode
from netauto.domain.primitives import JsonValue
from netauto.domain.relationships import (
    ObjectRelationshipView,
    Relationship,
    RelationshipCapability,
    RelationshipDefinition,
    RelationshipDefinitionProperty,
    RelationshipDefinitionVersion,
    RelationshipDefinitionVersionSummary,
    RelationshipResolution,
    RuntimeRelationshipResolution,
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
    object_templates,
    objects,
    relationship_definition_properties,
    relationship_definition_versions,
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


@dataclass(frozen=True, slots=True)
class RuntimeRelationshipHeader:
    id: UUID
    relationship_definition_id: UUID
    relationship_definition_version: int


@dataclass(frozen=True, slots=True)
class RelationshipCapabilityPageProjection:
    target_exists: bool
    items: tuple[RelationshipCapability, ...]


def _aggregate_statement():
    return select(
        relationship_definitions.c.id.label("definition_id"),
        relationship_definitions.c.symmetric,
        relationship_definitions.c.default_version,
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
    current_default_version: int | None = None
    resolutions: list[RelationshipResolution] = []

    def append_current() -> None:
        if current_id is not None:
            definitions.append(
                RelationshipDefinition(
                    current_id,
                    current_symmetric,
                    tuple(resolutions),
                    current_default_version,
                )
            )

    for row in rows:
        definition_id = cast(UUID, row["definition_id"])
        if definition_id != current_id:
            append_current()
            current_id = definition_id
            current_symmetric = cast(bool, row["symmetric"])
            current_default_version = cast(int | None, row["default_version"])
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


def _definition_property(row: RowMapping) -> RelationshipDefinitionProperty:
    return RelationshipDefinitionProperty(
        name=cast(str, row["name"]),
        position=cast(int, row["position"]),
        datatype_id=cast(UUID, row["datatype_id"]),
        datatype_version=cast(int, row["datatype_version"]),
        value_mode=ValueMode(cast(str, row["value_mode"])),
    )


def _definition_version_header(row: RowMapping) -> RelationshipDefinitionVersion:
    return RelationshipDefinitionVersion(
        relationship_definition_id=cast(UUID, row["relationship_definition_id"]),
        version=cast(int, row["version"]),
        revision=cast(int, row["revision"]),
        status=VersionStatus(cast(str, row["status"])),
        properties=(),
    )


def _definition_version_summary(
    row: RowMapping,
) -> RelationshipDefinitionVersionSummary:
    header = _definition_version_header(row)
    return RelationshipDefinitionVersionSummary(
        header.relationship_definition_id,
        header.version,
        header.revision,
        header.status,
    )


class RelationshipDefinitionStore:
    def __init__(self, connection: AsyncConnection) -> None:
        self.connection = connection

    async def insert(
        self,
        value: RelationshipDefinition,
        version: RelationshipDefinitionVersion,
    ) -> None:
        await self.connection.execute(
            relationship_definitions.insert().values(
                id=value.id, symmetric=value.symmetric, default_version=None
            )
        )
        for item in sorted(
            value.resolutions,
            key=lambda row: row.id.int,
        ):
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
                constraint_name = classify_postgresql_failure(error).constraint_name
                if constraint_name == "fk_relationship_resolutions_from_template":
                    raise RelationshipEndpointReferenceError(
                        item.from_template_id
                    ) from error
                if constraint_name == "fk_relationship_resolutions_to_template":
                    raise RelationshipEndpointReferenceError(
                        item.to_template_id
                    ) from error
                raise
        await RelationshipDefinitionVersionStore(self.connection).insert_version(
            version
        )

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

    async def get_many(
        self, definition_ids: Iterable[UUID]
    ) -> dict[UUID, RelationshipDefinition]:
        """Load only the requested aggregate set in one deterministic statement."""
        ordered = tuple(sorted(set(definition_ids), key=lambda item: item.int))
        if not ordered:
            return {}
        rows = (
            (
                await self.connection.execute(
                    _aggregate_statement()
                    .where(relationship_definitions.c.id.in_(ordered))
                    .order_by(
                        relationship_definitions.c.id,
                        relationship_resolutions.c.id,
                    )
                )
            )
            .mappings()
            .all()
        )
        return {value.id: value for value in _decode_aggregates(rows)}

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
        return (
            await self.connection.execute(
                row_lock_statement(
                    RowLockIntent(
                        RowLockKey(
                            RowLockClass.RELATIONSHIP_DEFINITION_HEADER,
                            definition_id,
                        ),
                        RowLockMode.NKU,
                    )
                )
            )
        ).first() is not None

    async def lock_update(self, definition_id: UUID) -> bool:
        return (
            await self.connection.execute(
                row_lock_statement(
                    RowLockIntent(
                        RowLockKey(
                            RowLockClass.RELATIONSHIP_DEFINITION_HEADER,
                            definition_id,
                        ),
                        RowLockMode.U,
                    )
                )
            )
        ).first() is not None

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
                relationship_definitions.update()
                .where(relationship_definitions.c.id == definition_id)
                .values(default_version=None)
            )
            await self.connection.execute(
                relationship_definitions.delete().where(
                    relationship_definitions.c.id == definition_id
                )
            )
        except IntegrityError as error:
            classified = classify_postgresql_failure(error)
            if classified.constraint_name == "fk_relationships_definition_version":
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
        template_id: UUID,
        name: str | None,
        after: UUID | None,
        limit: int,
    ) -> RelationshipCapabilityPageProjection:
        conditions = [
            "resolution.from_template_id IN (SELECT id FROM stable_ancestry)",
            "EXISTS ("
            "SELECT 1 FROM relationship_definition_versions AS published "
            "WHERE published.relationship_definition_id = "
            "resolution.relationship_definition_id "
            "AND published.status = 'PUBLISHED'"
            ")",
        ]
        parameters: dict[str, object] = {
            "template_id": template_id,
            "limit": limit,
        }
        if name is not None:
            conditions.append("resolution.name = :name")
            parameters["name"] = name
        if after is not None:
            conditions.append("resolution.id > :after")
            parameters["after"] = after
        membership = " AND ".join(conditions)
        statement = text(
            f"""
            WITH RECURSIVE stable_ancestry AS (
                SELECT
                    lineage.id,
                    lineage.parent_template_id,
                    ARRAY[lineage.id]::uuid[] AS visited
                FROM object_templates AS lineage
                WHERE lineage.id = :template_id

                UNION ALL

                SELECT
                    parent.id,
                    parent.parent_template_id,
                    child.visited || parent.id
                FROM stable_ancestry AS child
                JOIN object_templates AS parent
                  ON parent.id = child.parent_template_id
                WHERE NOT parent.id = ANY(child.visited)
            ), capability_page AS (
                SELECT
                    resolution.id AS resolution_id,
                    resolution.relationship_definition_id,
                    resolution.name,
                    resolution.from_template_id,
                    resolution.to_template_id,
                    definition.default_version
                FROM relationship_resolutions AS resolution
                JOIN relationship_definitions AS definition
                  ON definition.id = resolution.relationship_definition_id
                WHERE {membership}
                ORDER BY resolution.id
                LIMIT :limit
            )
            SELECT
                target.id AS target_id,
                capability_page.resolution_id,
                capability_page.relationship_definition_id,
                capability_page.name,
                capability_page.from_template_id,
                capability_page.to_template_id,
                capability_page.default_version
            FROM object_templates AS target
            LEFT JOIN capability_page ON TRUE
            WHERE target.id = :template_id
            ORDER BY capability_page.resolution_id
            """
        )
        rows = (await self.connection.execute(statement, parameters)).mappings().all()
        if not rows:
            return RelationshipCapabilityPageProjection(False, ())
        return RelationshipCapabilityPageProjection(
            True,
            tuple(
                RelationshipCapability(
                    resolution_id=cast(UUID, row["resolution_id"]),
                    relationship_definition_id=cast(
                        UUID, row["relationship_definition_id"]
                    ),
                    name=cast(str, row["name"]),
                    from_template_id=cast(UUID, row["from_template_id"]),
                    to_template_id=cast(UUID, row["to_template_id"]),
                    default_version=cast(int | None, row["default_version"]),
                )
                for row in rows
                if row["resolution_id"] is not None
            ),
        )


class RelationshipDefinitionVersionStore:
    """Persistence boundary for exact RelationshipDefinitionVersion state."""

    def __init__(self, connection: AsyncConnection) -> None:
        self.connection = connection

    async def _insert_properties(
        self,
        definition_id: UUID,
        version: int,
        properties: tuple[RelationshipDefinitionProperty, ...],
    ) -> None:
        for item in sorted(properties, key=lambda value: value.name):
            await self.connection.execute(
                relationship_definition_properties.insert().values(
                    relationship_definition_id=definition_id,
                    relationship_definition_version=version,
                    name=item.name,
                    position=item.position,
                    datatype_id=item.datatype_id,
                    datatype_version=item.datatype_version,
                    value_mode=item.value_mode.value,
                )
            )

    async def insert_version(self, value: RelationshipDefinitionVersion) -> None:
        await self.connection.execute(
            relationship_definition_versions.insert().values(
                relationship_definition_id=value.relationship_definition_id,
                version=value.version,
                revision=value.revision,
                status=value.status.value,
            )
        )
        await self._insert_properties(
            value.relationship_definition_id, value.version, value.properties
        )

    async def get_header(
        self, definition_id: UUID, version: int
    ) -> RelationshipDefinitionVersion | None:
        row = (
            (
                await self.connection.execute(
                    select(relationship_definition_versions).where(
                        relationship_definition_versions.c.relationship_definition_id
                        == definition_id,
                        relationship_definition_versions.c.version == version,
                    )
                )
            )
            .mappings()
            .first()
        )
        return None if row is None else _definition_version_header(row)

    async def get_headers(
        self, keys: Sequence[tuple[UUID, int]]
    ) -> dict[tuple[UUID, int], RelationshipDefinitionVersion]:
        if not keys:
            return {}
        ordered = tuple(sorted(set(keys), key=lambda item: (item[0].int, item[1])))
        rows = (
            (
                await self.connection.execute(
                    select(relationship_definition_versions).where(
                        tuple_(
                            relationship_definition_versions.c.relationship_definition_id,
                            relationship_definition_versions.c.version,
                        ).in_(ordered)
                    )
                )
            )
            .mappings()
            .all()
        )
        values = map(_definition_version_header, rows)
        return {
            (value.relationship_definition_id, value.version): value for value in values
        }

    async def get_properties(
        self, definition_id: UUID, version: int
    ) -> tuple[RelationshipDefinitionProperty, ...]:
        rows = (
            (
                await self.connection.execute(
                    select(relationship_definition_properties)
                    .where(
                        relationship_definition_properties.c.relationship_definition_id
                        == definition_id,
                        relationship_definition_properties.c.relationship_definition_version
                        == version,
                    )
                    .order_by(relationship_definition_properties.c.position)
                )
            )
            .mappings()
            .all()
        )
        return tuple(_definition_property(row) for row in rows)

    async def get_version(
        self, definition_id: UUID, version: int
    ) -> RelationshipDefinitionVersion | None:
        header = await self.get_header(definition_id, version)
        if header is None:
            return None
        return RelationshipDefinitionVersion(
            header.relationship_definition_id,
            header.version,
            header.revision,
            header.status,
            await self.get_properties(definition_id, version),
        )

    async def get_versions(
        self, keys: Sequence[tuple[UUID, int]]
    ) -> dict[tuple[UUID, int], RelationshipDefinitionVersion]:
        ordered = tuple(sorted(set(keys), key=lambda item: (item[0].int, item[1])))
        if not ordered:
            return {}
        headers = await self.get_headers(ordered)
        property_rows = (
            (
                await self.connection.execute(
                    select(relationship_definition_properties)
                    .where(
                        tuple_(
                            relationship_definition_properties.c.relationship_definition_id,
                            relationship_definition_properties.c.relationship_definition_version,
                        ).in_(ordered)
                    )
                    .order_by(
                        relationship_definition_properties.c.relationship_definition_id,
                        relationship_definition_properties.c.relationship_definition_version,
                        relationship_definition_properties.c.position,
                    )
                )
            )
            .mappings()
            .all()
        )
        properties: dict[tuple[UUID, int], list[RelationshipDefinitionProperty]] = {}
        for row in property_rows:
            key = (
                cast(UUID, row["relationship_definition_id"]),
                cast(int, row["relationship_definition_version"]),
            )
            properties.setdefault(key, []).append(_definition_property(row))
        return {
            key: RelationshipDefinitionVersion(
                header.relationship_definition_id,
                header.version,
                header.revision,
                header.status,
                tuple(properties.get(key, ())),
            )
            for key, header in headers.items()
        }

    async def next_version(self, definition_id: UUID) -> int:
        maximum = await self.connection.scalar(
            select(func.max(relationship_definition_versions.c.version)).where(
                relationship_definition_versions.c.relationship_definition_id
                == definition_id
            )
        )
        return 1 if maximum is None else int(maximum) + 1

    async def replace_candidate(self, value: RelationshipDefinitionVersion) -> None:
        current = {
            item.name: item
            for item in await self.get_properties(
                value.relationship_definition_id, value.version
            )
        }
        desired = {item.name: item for item in value.properties}
        deletes = sorted(
            name for name, item in current.items() if desired.get(name) != item
        )
        inserts = tuple(
            item for name, item in sorted(desired.items()) if current.get(name) != item
        )
        for name in deletes:
            await self.connection.execute(
                relationship_definition_properties.delete().where(
                    relationship_definition_properties.c.relationship_definition_id
                    == value.relationship_definition_id,
                    relationship_definition_properties.c.relationship_definition_version
                    == value.version,
                    relationship_definition_properties.c.name == name,
                )
            )
        await self._insert_properties(
            value.relationship_definition_id, value.version, inserts
        )
        result = await self.connection.execute(
            relationship_definition_versions.update()
            .where(
                relationship_definition_versions.c.relationship_definition_id
                == value.relationship_definition_id,
                relationship_definition_versions.c.version == value.version,
            )
            .values(revision=relationship_definition_versions.c.revision + 1)
        )
        if result.rowcount != 1:
            raise RuntimeError("locked RelationshipDefinitionVersion disappeared")

    async def set_status(
        self, definition_id: UUID, version: int, status: VersionStatus
    ) -> None:
        result = await self.connection.execute(
            relationship_definition_versions.update()
            .where(
                relationship_definition_versions.c.relationship_definition_id
                == definition_id,
                relationship_definition_versions.c.version == version,
            )
            .values(status=status.value)
        )
        if result.rowcount != 1:
            raise RuntimeError("locked RelationshipDefinitionVersion disappeared")

    async def set_default(
        self, definition_id: UUID, version: int | None
    ) -> RelationshipDefinition:
        row = (
            await self.connection.execute(
                relationship_definitions.update()
                .where(relationship_definitions.c.id == definition_id)
                .values(default_version=version)
                .returning(relationship_definitions.c.id)
            )
        ).first()
        if row is None:
            raise RuntimeError("locked RelationshipDefinition disappeared")
        aggregate = await RelationshipDefinitionStore(self.connection).get(
            definition_id
        )
        if aggregate is None:
            raise RuntimeError("updated RelationshipDefinition disappeared")
        return aggregate

    async def published_history(
        self, definition_id: UUID
    ) -> tuple[RelationshipDefinitionVersion, ...]:
        header_rows = (
            (
                await self.connection.execute(
                    select(relationship_definition_versions)
                    .where(
                        relationship_definition_versions.c.relationship_definition_id
                        == definition_id,
                        relationship_definition_versions.c.status.in_(
                            (
                                VersionStatus.PUBLISHED.value,
                                VersionStatus.DEPRECATED.value,
                            )
                        ),
                    )
                    .order_by(relationship_definition_versions.c.version)
                )
            )
            .mappings()
            .all()
        )
        headers = tuple(_definition_version_header(row) for row in header_rows)
        if not headers:
            return ()
        versions = tuple(header.version for header in headers)
        property_rows = (
            (
                await self.connection.execute(
                    select(relationship_definition_properties)
                    .where(
                        relationship_definition_properties.c.relationship_definition_id
                        == definition_id,
                        relationship_definition_properties.c.relationship_definition_version.in_(
                            versions
                        ),
                    )
                    .order_by(
                        relationship_definition_properties.c.relationship_definition_version,
                        relationship_definition_properties.c.position,
                    )
                )
            )
            .mappings()
            .all()
        )
        properties: dict[int, list[RelationshipDefinitionProperty]] = {}
        for row in property_rows:
            version = cast(int, row["relationship_definition_version"])
            properties.setdefault(version, []).append(_definition_property(row))
        return tuple(
            RelationshipDefinitionVersion(
                header.relationship_definition_id,
                header.version,
                header.revision,
                header.status,
                tuple(properties.get(header.version, ())),
            )
            for header in headers
        )

    async def has_published(self, definition_id: UUID) -> bool:
        return bool(
            await self.connection.scalar(
                select(func.count())
                .select_from(relationship_definition_versions)
                .where(
                    relationship_definition_versions.c.relationship_definition_id
                    == definition_id,
                    relationship_definition_versions.c.status
                    == VersionStatus.PUBLISHED.value,
                )
            )
        )

    async def has_factual_reference(self, definition_id: UUID, version: int) -> bool:
        return bool(
            await self.connection.scalar(
                select(func.count())
                .select_from(relationships)
                .where(
                    relationships.c.relationship_definition_id == definition_id,
                    relationships.c.relationship_definition_version == version,
                )
            )
        )

    async def delete_draft(self, definition_id: UUID, version: int) -> None:
        result = await self.connection.execute(
            relationship_definition_versions.delete().where(
                relationship_definition_versions.c.relationship_definition_id
                == definition_id,
                relationship_definition_versions.c.version == version,
            )
        )
        if result.rowcount != 1:
            raise RuntimeError("locked RelationshipDefinitionVersion disappeared")

    async def list_versions(
        self,
        definition_id: UUID,
        *,
        status: str | None,
        after: int | None,
        limit: int,
    ) -> tuple[RelationshipDefinitionVersionSummary, ...]:
        statement = select(relationship_definition_versions).where(
            relationship_definition_versions.c.relationship_definition_id
            == definition_id
        )
        if status is not None:
            statement = statement.where(
                relationship_definition_versions.c.status == status
            )
        if after is not None:
            statement = statement.where(
                relationship_definition_versions.c.version > after
            )
        rows = (
            (
                await self.connection.execute(
                    statement.order_by(
                        relationship_definition_versions.c.version
                    ).limit(limit)
                )
            )
            .mappings()
            .all()
        )
        return tuple(_definition_version_summary(row) for row in rows)


def _runtime_relationship(rows: Sequence[RowMapping]) -> Relationship | None:
    if not rows:
        return None
    relationship_id = cast(UUID, rows[0]["relationship_id"])
    definition_id = cast(UUID, rows[0]["relationship_definition_id"])
    definition_version = cast(int, rows[0]["relationship_definition_version"])
    raw_properties = cast(object, rows[0]["properties"])
    if not isinstance(raw_properties, dict):
        raise RuntimeError("persisted Relationship properties are invalid")
    raw_property_map = cast(dict[object, object], raw_properties)
    if not all(isinstance(key, str) for key in raw_property_map):
        raise RuntimeError("persisted Relationship properties are invalid")
    properties = cast(dict[str, JsonValue], raw_property_map)
    resolutions: list[RuntimeRelationshipResolution] = []
    for row in rows:
        if (
            row["relationship_id"] != relationship_id
            or row["relationship_definition_id"] != definition_id
            or row["relationship_definition_version"] != definition_version
            or row["properties"] != properties
        ):
            raise RuntimeError("persisted Relationship aggregate is incoherent")
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
    return Relationship(
        id=relationship_id,
        relationship_definition_id=definition_id,
        resolutions=tuple(resolutions),
        relationship_definition_version=definition_version,
        properties=properties,
    )


class RuntimeRelationshipStore:
    """Persistence boundary for complete factual Relationship aggregates."""

    def __init__(self, connection: AsyncConnection) -> None:
        self.connection = connection

    @staticmethod
    def _aggregate_statement():
        return select(
            relationships.c.id.label("relationship_id"),
            relationships.c.relationship_definition_id,
            relationships.c.relationship_definition_version,
            relationships.c.properties,
            runtime_relationship_resolutions.c.relationship_definition_id.label(
                "runtime_relationship_definition_id"
            ),
            runtime_relationship_resolutions.c.resolution_id,
            runtime_relationship_resolutions.c.from_object_id,
            runtime_relationship_resolutions.c.to_object_id,
        ).select_from(
            relationships.outerjoin(
                runtime_relationship_resolutions,
                runtime_relationship_resolutions.c.relationship_id
                == relationships.c.id,
            )
        )

    async def get_header(
        self, relationship_id: UUID
    ) -> RuntimeRelationshipHeader | None:
        row = (
            (
                await self.connection.execute(
                    select(
                        relationships.c.id,
                        relationships.c.relationship_definition_id,
                        relationships.c.relationship_definition_version,
                    ).where(relationships.c.id == relationship_id)
                )
            )
            .mappings()
            .first()
        )
        if row is None:
            return None
        return RuntimeRelationshipHeader(
            cast(UUID, row["id"]),
            cast(UUID, row["relationship_definition_id"]),
            cast(int, row["relationship_definition_version"]),
        )

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
                    self._aggregate_statement()
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

    async def get_many(
        self, relationship_ids: Iterable[UUID]
    ) -> dict[UUID, Relationship]:
        ids = tuple(sorted(set(relationship_ids), key=lambda value: value.int))
        if not ids:
            return {}
        rows = (
            (
                await self.connection.execute(
                    self._aggregate_statement()
                    .where(relationships.c.id.in_(ids))
                    .order_by(
                        relationships.c.id,
                        runtime_relationship_resolutions.c.resolution_id,
                        runtime_relationship_resolutions.c.from_object_id,
                        runtime_relationship_resolutions.c.to_object_id,
                    )
                )
            )
            .mappings()
            .all()
        )
        by_id: dict[UUID, list[RowMapping]] = {}
        for row in rows:
            by_id.setdefault(cast(UUID, row["relationship_id"]), []).append(row)
        result: dict[UUID, Relationship] = {}
        for relationship_id, aggregate_rows in by_id.items():
            value = _runtime_relationship(aggregate_rows)
            if value is not None:
                result[relationship_id] = value
        return result

    async def lock_update(self, relationship_id: UUID) -> bool:
        return (
            await self.connection.execute(
                row_lock_statement(
                    RowLockIntent(
                        RowLockKey(RowLockClass.RELATIONSHIP, relationship_id),
                        RowLockMode.U,
                    )
                )
            )
        ).first() is not None

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
                .order_by(runtime_relationship_resolutions.c.relationship_id)
            )
        ).all()
        return tuple(cast(UUID, value) for value in values)

    async def insert(self, value: Relationship) -> None:
        try:
            await self.connection.execute(
                relationships.insert().values(
                    id=value.id,
                    relationship_definition_id=value.relationship_definition_id,
                    relationship_definition_version=(
                        value.relationship_definition_version
                    ),
                    properties=value.properties,
                )
            )
        except IntegrityError as error:
            classified = classify_postgresql_failure(error)
            if classified.constraint_name == "fk_relationships_definition_version":
                raise RuntimeRelationshipModelReferenceError from error
            raise
        for item in sorted(
            value.resolutions,
            key=lambda row: (
                row.resolution_id.int,
                row.from_object_id.int,
                row.to_object_id.int,
            ),
        ):
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
                constraint_name = classify_postgresql_failure(error).constraint_name
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

    async def update_properties(
        self, relationship_id: UUID, properties: dict[str, JsonValue]
    ) -> None:
        result = await self.connection.execute(
            relationships.update()
            .where(relationships.c.id == relationship_id)
            .values(properties=properties)
        )
        if result.rowcount != 1:
            raise RuntimeError("locked Relationship disappeared before update")

    async def update_schema(
        self,
        relationship_id: UUID,
        definition_id: UUID,
        target_version: int,
        properties: dict[str, JsonValue],
    ) -> None:
        try:
            result = await self.connection.execute(
                relationships.update()
                .where(
                    relationships.c.id == relationship_id,
                    relationships.c.relationship_definition_id == definition_id,
                )
                .values(
                    relationship_definition_version=target_version,
                    properties=properties,
                )
            )
        except IntegrityError as error:
            if (
                classify_postgresql_failure(error).constraint_name
                == "fk_relationships_definition_version"
            ):
                raise RuntimeRelationshipModelReferenceError from error
            raise
        if result.rowcount != 1:
            raise RuntimeError("locked Relationship disappeared before schema update")

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
                relationships.c.relationship_definition_version,
                relationships.c.properties,
                runtime_relationship_resolutions.c.from_object_id,
                runtime_relationship_resolutions.c.to_object_id,
                relationship_resolutions.c.name,
            )
            .join(
                relationship_resolutions,
                relationship_resolutions.c.id
                == runtime_relationship_resolutions.c.resolution_id,
            )
            .join(
                relationships,
                relationships.c.id
                == runtime_relationship_resolutions.c.relationship_id,
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
                relationship_definition_version=cast(
                    int, row.relationship_definition_version
                ),
                properties=cast(dict[str, JsonValue], row.properties),
            )
            for row in rows
        )
