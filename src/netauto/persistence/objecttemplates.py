"""SQLAlchemy Core persistence for the ObjectTemplate aggregate."""

from collections.abc import Sequence
from typing import Literal, cast
from uuid import UUID

from sqlalchemy import and_, func, null, or_, select, tuple_, update
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection

from netauto.domain.datatypes import VersionStatus
from netauto.domain.objecttemplates import (
    LocalComponent,
    LocalProperty,
    ObjectTemplate,
    ObjectTemplateVersion,
    ObjectTemplateVersionSummary,
    ValueMode,
)
from netauto.domain.primitives import JsonValue
from netauto.persistence.metadata import (
    object_template_components,
    object_template_properties,
    object_template_versions,
    object_templates,
    objects,
    relationship_resolutions,
)


class ObjectTemplateQualifiedNameError(Exception):
    pass


type ObjectTemplateDeleteBlockerType = Literal[
    "child_object_template",
    "object_template_component",
    "object",
    "relationship_resolution",
]


class ObjectTemplateDeleteReferenceError(Exception):
    def __init__(self, blocker_type: ObjectTemplateDeleteBlockerType) -> None:
        self.blocker_type = blocker_type
        super().__init__("ObjectTemplate deletion is blocked by a current reference")


class ObjectTemplateComponentTargetReferenceError(Exception):
    def __init__(self, target_template_id: UUID) -> None:
        self.target_template_id = target_template_id
        super().__init__("ObjectTemplate component target disappeared")


def _lineage(row: RowMapping) -> ObjectTemplate:
    return ObjectTemplate(
        id=cast(UUID, row["id"]),
        namespace=cast(str, row["namespace"]),
        name=cast(str, row["name"]),
        description=cast(str | None, row["description"]),
        abstract=cast(bool, row["abstract"]),
        parent_template_id=cast(UUID | None, row["parent_template_id"]),
        default_version=cast(int | None, row["default_version"]),
    )


def _property(row: RowMapping) -> LocalProperty:
    return LocalProperty(
        name=cast(str, row["name"]),
        position=cast(int, row["position"]),
        datatype_id=cast(UUID, row["datatype_id"]),
        datatype_version=cast(int, row["datatype_version"]),
        value_mode=ValueMode(cast(str, row["value_mode"])),
        required=cast(bool, row["required"]),
        migration_default=cast(JsonValue | None, row["migration_default"]),
    )


def _component(row: RowMapping) -> LocalComponent:
    return LocalComponent(
        name=cast(str, row["name"]),
        position=cast(int, row["position"]),
        target_template_id=cast(UUID, row["target_template_id"]),
    )


def _header(row: RowMapping) -> ObjectTemplateVersion:
    return ObjectTemplateVersion(
        template_id=cast(UUID, row["template_id"]),
        version=cast(int, row["version"]),
        revision=cast(int, row["revision"]),
        status=VersionStatus(cast(str, row["status"])),
        parent_template_id=cast(UUID | None, row["parent_template_id"]),
        parent_version=cast(int | None, row["parent_version"]),
        properties=(),
        components=(),
    )


def _summary(row: RowMapping) -> ObjectTemplateVersionSummary:
    header = _header(row)
    return ObjectTemplateVersionSummary(
        header.template_id,
        header.version,
        header.revision,
        header.status,
        header.parent_template_id,
        header.parent_version,
    )


class ObjectTemplateStore:
    def __init__(self, connection: AsyncConnection) -> None:
        self.connection = connection

    async def _insert_declarations(
        self,
        template_id: UUID,
        version: int,
        properties: tuple[LocalProperty, ...],
        components: tuple[LocalComponent, ...],
    ) -> None:
        for item in properties:
            values: dict[str, object] = {
                "template_id": template_id,
                "template_version": version,
                "name": item.name,
                "position": item.position,
                "datatype_id": item.datatype_id,
                "datatype_version": item.datatype_version,
                "value_mode": item.value_mode.value,
                "required": item.required,
                "migration_default": (
                    null() if item.migration_default is None else item.migration_default
                ),
            }
            await self.connection.execute(
                object_template_properties.insert().values(**values)
            )
        for item in components:
            try:
                await self.connection.execute(
                    object_template_components.insert().values(
                        template_id=template_id,
                        template_version=version,
                        name=item.name,
                        position=item.position,
                        target_template_id=item.target_template_id,
                    )
                )
            except IntegrityError as error:
                diagnostic = getattr(getattr(error, "orig", None), "diag", None)
                if getattr(diagnostic, "constraint_name", None) == (
                    "fk_object_template_components_target"
                ):
                    raise ObjectTemplateComponentTargetReferenceError(
                        item.target_template_id
                    ) from error
                raise

    async def create(
        self, lineage: ObjectTemplate, version: ObjectTemplateVersion
    ) -> None:
        try:
            await self.connection.execute(
                object_templates.insert().values(
                    id=lineage.id,
                    namespace=lineage.namespace,
                    name=lineage.name,
                    description=lineage.description,
                    abstract=lineage.abstract,
                    default_version=None,
                    parent_template_id=lineage.parent_template_id,
                )
            )
            await self.insert_version(version)
        except IntegrityError as error:
            diagnostic = getattr(getattr(error, "orig", None), "diag", None)
            if getattr(diagnostic, "constraint_name", None) == (
                "uq_object_templates_namespace_name"
            ):
                raise ObjectTemplateQualifiedNameError from error
            raise

    async def insert_version(self, version: ObjectTemplateVersion) -> None:
        await self.connection.execute(
            object_template_versions.insert().values(
                template_id=version.template_id,
                version=version.version,
                revision=version.revision,
                status=version.status.value,
                parent_template_id=version.parent_template_id,
                parent_version=version.parent_version,
            )
        )
        await self._insert_declarations(
            version.template_id,
            version.version,
            version.properties,
            version.components,
        )

    async def get_lineage(self, template_id: UUID) -> ObjectTemplate | None:
        row = (
            (
                await self.connection.execute(
                    select(object_templates).where(object_templates.c.id == template_id)
                )
            )
            .mappings()
            .first()
        )
        return None if row is None else _lineage(row)

    async def get_header(
        self, template_id: UUID, version: int
    ) -> ObjectTemplateVersion | None:
        row = (
            (
                await self.connection.execute(
                    select(object_template_versions).where(
                        object_template_versions.c.template_id == template_id,
                        object_template_versions.c.version == version,
                    )
                )
            )
            .mappings()
            .first()
        )
        return None if row is None else _header(row)

    async def get_properties(
        self, template_id: UUID, version: int
    ) -> tuple[LocalProperty, ...]:
        rows = (
            (
                await self.connection.execute(
                    select(object_template_properties)
                    .where(
                        object_template_properties.c.template_id == template_id,
                        object_template_properties.c.template_version == version,
                    )
                    .order_by(object_template_properties.c.position)
                )
            )
            .mappings()
            .all()
        )
        return tuple(_property(row) for row in rows)

    async def get_components(
        self, template_id: UUID, version: int
    ) -> tuple[LocalComponent, ...]:
        rows = (
            (
                await self.connection.execute(
                    select(object_template_components)
                    .where(
                        object_template_components.c.template_id == template_id,
                        object_template_components.c.template_version == version,
                    )
                    .order_by(object_template_components.c.position)
                )
            )
            .mappings()
            .all()
        )
        return tuple(_component(row) for row in rows)

    async def get_version(
        self, template_id: UUID, version: int
    ) -> ObjectTemplateVersion | None:
        header = await self.get_header(template_id, version)
        if header is None:
            return None
        return ObjectTemplateVersion(
            header.template_id,
            header.version,
            header.revision,
            header.status,
            header.parent_template_id,
            header.parent_version,
            await self.get_properties(template_id, version),
            await self.get_components(template_id, version),
        )

    async def lock_lineage_no_key(self, template_id: UUID) -> bool:
        row = (
            await self.connection.execute(
                select(object_templates.c.id)
                .where(object_templates.c.id == template_id)
                .with_for_update(key_share=True)
            )
        ).first()
        return row is not None

    async def lock_lineage_share(self, template_id: UUID) -> bool:
        row = (
            await self.connection.execute(
                select(object_templates.c.id)
                .where(object_templates.c.id == template_id)
                .with_for_update(read=True)
            )
        ).first()
        return row is not None

    async def lock_lineage_update(self, template_id: UUID) -> bool:
        row = (
            await self.connection.execute(
                select(object_templates.c.id)
                .where(object_templates.c.id == template_id)
                .with_for_update()
            )
        ).first()
        return row is not None

    async def lock_version_no_key(self, template_id: UUID, version: int) -> bool:
        row = (
            await self.connection.execute(
                select(object_template_versions.c.template_id)
                .where(
                    object_template_versions.c.template_id == template_id,
                    object_template_versions.c.version == version,
                )
                .with_for_update(key_share=True)
            )
        ).first()
        return row is not None

    async def lock_version_update(self, template_id: UUID, version: int) -> bool:
        row = (
            await self.connection.execute(
                select(object_template_versions.c.template_id)
                .where(
                    object_template_versions.c.template_id == template_id,
                    object_template_versions.c.version == version,
                )
                .with_for_update()
            )
        ).first()
        return row is not None

    async def lock_version_share(self, template_id: UUID, version: int) -> bool:
        row = (
            await self.connection.execute(
                select(object_template_versions.c.template_id)
                .where(
                    object_template_versions.c.template_id == template_id,
                    object_template_versions.c.version == version,
                )
                .with_for_update(read=True)
            )
        ).first()
        return row is not None

    async def admit_exact(
        self, template_id: UUID, version: int
    ) -> ObjectTemplateVersion | None:
        if not await self.lock_version_share(template_id, version):
            return None
        return await self.get_header(template_id, version)

    async def admit_default(
        self, template_id: UUID
    ) -> tuple[ObjectTemplate, ObjectTemplateVersion | None] | None:
        if not await self.lock_lineage_share(template_id):
            return None
        lineage = await self.get_lineage(template_id)
        if lineage is None:
            return None
        if lineage.default_version is None:
            return lineage, None
        return lineage, await self.admit_exact(template_id, lineage.default_version)

    async def next_version(self, template_id: UUID) -> int:
        maximum = await self.connection.scalar(
            select(func.max(object_template_versions.c.version)).where(
                object_template_versions.c.template_id == template_id
            )
        )
        return 1 if maximum is None else int(maximum) + 1

    async def replace_candidate(self, version: ObjectTemplateVersion) -> None:
        await self.connection.execute(
            object_template_properties.delete().where(
                object_template_properties.c.template_id == version.template_id,
                object_template_properties.c.template_version == version.version,
            )
        )
        await self.connection.execute(
            object_template_components.delete().where(
                object_template_components.c.template_id == version.template_id,
                object_template_components.c.template_version == version.version,
            )
        )
        await self._insert_declarations(
            version.template_id,
            version.version,
            version.properties,
            version.components,
        )
        await self.connection.execute(
            object_template_versions.update()
            .where(
                object_template_versions.c.template_id == version.template_id,
                object_template_versions.c.version == version.version,
            )
            .values(
                parent_template_id=version.parent_template_id,
                parent_version=version.parent_version,
                revision=object_template_versions.c.revision + 1,
            )
        )

    async def set_status(
        self, template_id: UUID, version: int, status: VersionStatus
    ) -> None:
        await self.connection.execute(
            object_template_versions.update()
            .where(
                object_template_versions.c.template_id == template_id,
                object_template_versions.c.version == version,
            )
            .values(status=status.value)
        )

    async def set_default(
        self, template_id: UUID, version: int | None
    ) -> ObjectTemplate:
        row = (
            (
                await self.connection.execute(
                    object_templates.update()
                    .where(object_templates.c.id == template_id)
                    .values(default_version=version)
                    .returning(object_templates)
                )
            )
            .mappings()
            .one()
        )
        return _lineage(row)

    async def set_description(
        self, template_id: UUID, description: str | None
    ) -> ObjectTemplate | None:
        row = (
            (
                await self.connection.execute(
                    object_templates.update()
                    .where(object_templates.c.id == template_id)
                    .values(description=description)
                    .returning(object_templates)
                )
            )
            .mappings()
            .first()
        )
        return None if row is None else _lineage(row)

    async def has_active_child(self, template_id: UUID, version: int) -> bool:
        value = await self.connection.scalar(
            select(func.count())
            .select_from(object_template_versions)
            .where(
                object_template_versions.c.parent_template_id == template_id,
                object_template_versions.c.parent_version == version,
                object_template_versions.c.status == VersionStatus.PUBLISHED.value,
            )
        )
        return bool(value)

    async def latest_published_property(
        self, template_id: UUID, name: str
    ) -> LocalProperty | None:
        row = (
            (
                await self.connection.execute(
                    select(object_template_properties)
                    .join(
                        object_template_versions,
                        and_(
                            object_template_properties.c.template_id
                            == object_template_versions.c.template_id,
                            object_template_properties.c.template_version
                            == object_template_versions.c.version,
                        ),
                    )
                    .where(
                        object_template_properties.c.template_id == template_id,
                        object_template_properties.c.name == name,
                        object_template_versions.c.status.in_(
                            (
                                VersionStatus.PUBLISHED.value,
                                VersionStatus.DEPRECATED.value,
                            )
                        ),
                    )
                    .order_by(object_template_properties.c.template_version.desc())
                    .limit(1)
                )
            )
            .mappings()
            .first()
        )
        return None if row is None else _property(row)

    async def latest_published_component(
        self, template_id: UUID, name: str
    ) -> LocalComponent | None:
        row = (
            (
                await self.connection.execute(
                    select(object_template_components)
                    .join(
                        object_template_versions,
                        and_(
                            object_template_components.c.template_id
                            == object_template_versions.c.template_id,
                            object_template_components.c.template_version
                            == object_template_versions.c.version,
                        ),
                    )
                    .where(
                        object_template_components.c.template_id == template_id,
                        object_template_components.c.name == name,
                        object_template_versions.c.status.in_(
                            (
                                VersionStatus.PUBLISHED.value,
                                VersionStatus.DEPRECATED.value,
                            )
                        ),
                    )
                    .order_by(object_template_components.c.template_version.desc())
                    .limit(1)
                )
            )
            .mappings()
            .first()
        )
        return None if row is None else _component(row)

    async def is_ancestor(self, ancestor_id: UUID, descendant_id: UUID) -> bool:
        current: UUID | None = descendant_id
        seen: set[UUID] = set()
        while current is not None:
            if current in seen:
                raise RuntimeError("persisted inheritance cycle")
            seen.add(current)
            if current == ancestor_id:
                return True
            lineage = await self.get_lineage(current)
            if lineage is None:
                raise RuntimeError("persisted component target lineage is missing")
            current = lineage.parent_template_id
        return False

    async def external_reference_counts(self, template_id: UUID) -> dict[str, int]:
        child_count = await self.connection.scalar(
            select(func.count())
            .select_from(object_templates)
            .where(object_templates.c.parent_template_id == template_id)
        )
        component_count = await self.connection.scalar(
            select(func.count())
            .select_from(object_template_components)
            .where(
                object_template_components.c.target_template_id == template_id,
                object_template_components.c.template_id != template_id,
            )
        )
        object_count = await self.connection.scalar(
            select(func.count())
            .select_from(objects)
            .where(objects.c.template_id == template_id)
        )
        resolution_count = await self.connection.scalar(
            select(func.count())
            .select_from(relationship_resolutions)
            .where(
                or_(
                    relationship_resolutions.c.from_template_id == template_id,
                    relationship_resolutions.c.to_template_id == template_id,
                )
            )
        )
        return {
            "child_object_template": int(child_count or 0),
            "object_template_component": int(component_count or 0),
            "object": int(object_count or 0),
            "relationship_resolution": int(resolution_count or 0),
        }

    async def delete_draft(self, template_id: UUID, version: int) -> None:
        await self.connection.execute(
            object_template_versions.delete().where(
                object_template_versions.c.template_id == template_id,
                object_template_versions.c.version == version,
            )
        )

    async def delete_lineage(self, template_id: UUID) -> None:
        try:
            await self.connection.execute(
                update(object_templates)
                .where(object_templates.c.id == template_id)
                .values(default_version=None)
            )
            await self.connection.execute(
                object_templates.delete().where(object_templates.c.id == template_id)
            )
        except IntegrityError as error:
            diagnostic = getattr(getattr(error, "orig", None), "diag", None)
            constraint = cast(str | None, getattr(diagnostic, "constraint_name", None))
            blocker_by_constraint: dict[str, ObjectTemplateDeleteBlockerType] = {
                "fk_object_templates_parent": "child_object_template",
                "fk_object_template_versions_parent_version": ("child_object_template"),
                "fk_object_template_components_target": "object_template_component",
                "fk_objects_template_version": "object",
                "fk_relationship_resolutions_from_template": (
                    "relationship_resolution"
                ),
                "fk_relationship_resolutions_to_template": ("relationship_resolution"),
            }
            blocker_type = (
                None if constraint is None else blocker_by_constraint.get(constraint)
            )
            if blocker_type is not None:
                raise ObjectTemplateDeleteReferenceError(blocker_type) from error
            raise

    async def list_lineages(
        self,
        *,
        namespace: str | None,
        name: str | None,
        abstract: bool | None,
        parent_template_id: UUID | None,
        parent_filter_set: bool,
        after: tuple[str, str] | None,
        limit: int,
    ) -> Sequence[ObjectTemplate]:
        statement = select(object_templates)
        if namespace is not None:
            statement = statement.where(object_templates.c.namespace == namespace)
        if name is not None:
            statement = statement.where(object_templates.c.name == name)
        if abstract is not None:
            statement = statement.where(object_templates.c.abstract == abstract)
        if parent_filter_set:
            statement = statement.where(
                object_templates.c.parent_template_id == parent_template_id
            )
        if after is not None:
            statement = statement.where(
                tuple_(object_templates.c.namespace, object_templates.c.name) > after
            )
        rows = (
            (
                await self.connection.execute(
                    statement.order_by(
                        object_templates.c.namespace, object_templates.c.name
                    ).limit(limit)
                )
            )
            .mappings()
            .all()
        )
        return [_lineage(row) for row in rows]

    async def list_versions(
        self,
        template_id: UUID,
        *,
        status: VersionStatus | None,
        after: int | None,
        limit: int,
    ) -> Sequence[ObjectTemplateVersionSummary]:
        statement = select(object_template_versions).where(
            object_template_versions.c.template_id == template_id
        )
        if status is not None:
            statement = statement.where(
                object_template_versions.c.status == status.value
            )
        if after is not None:
            statement = statement.where(object_template_versions.c.version > after)
        rows = (
            (
                await self.connection.execute(
                    statement.order_by(object_template_versions.c.version).limit(limit)
                )
            )
            .mappings()
            .all()
        )
        return [_summary(row) for row in rows]
