"""SQLAlchemy Core persistence operations for the DataType capability."""

from collections.abc import Sequence
from typing import cast
from uuid import UUID

from sqlalchemy import and_, func, select, tuple_, update
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection

from netauto.domain.datatypes import (
    DataType,
    DataTypeVersion,
    DataTypeVersionSummary,
    VersionStatus,
)
from netauto.domain.primitives import JsonValue, PrimitiveType
from netauto.persistence.locking import (
    RowLockClass,
    RowLockIntent,
    RowLockKey,
    RowLockMode,
    classify_postgresql_failure,
    row_lock_statement,
)
from netauto.persistence.metadata import (
    datatype_versions,
    datatypes,
    object_template_properties,
    object_template_versions,
)


class QualifiedNameArbitrationError(Exception):
    pass


class DeleteReferenceError(Exception):
    pass


def _lineage(mapping: RowMapping) -> DataType:
    return DataType(
        id=cast(UUID, mapping["id"]),
        namespace=cast(str, mapping["namespace"]),
        name=cast(str, mapping["name"]),
        description=cast(str | None, mapping["description"]),
        default_version=cast(int | None, mapping["default_version"]),
    )


def _version(mapping: RowMapping) -> DataTypeVersion:
    return DataTypeVersion(
        datatype_id=cast(UUID, mapping["datatype_id"]),
        version=cast(int, mapping["version"]),
        revision=cast(int, mapping["revision"]),
        status=VersionStatus(cast(str, mapping["status"])),
        base_type=PrimitiveType(cast(str, mapping["base_type"])),
        constraints=cast(dict[str, JsonValue], mapping["constraints"]),
    )


def _summary(mapping: RowMapping) -> DataTypeVersionSummary:
    version = _version(mapping)
    return DataTypeVersionSummary(
        datatype_id=version.datatype_id,
        version=version.version,
        revision=version.revision,
        status=version.status,
        base_type=version.base_type,
    )


class DataTypeStore:
    """Query construction isolated inside the persistence boundary."""

    def __init__(self, connection: AsyncConnection) -> None:
        self.connection = connection

    async def _lock(self, key: RowLockKey, mode: RowLockMode) -> bool:
        return (
            await self.connection.execute(row_lock_statement(RowLockIntent(key, mode)))
        ).first() is not None

    async def create(self, datatype: DataType, version: DataTypeVersion) -> None:
        try:
            await self.connection.execute(
                datatypes.insert().values(
                    id=datatype.id,
                    namespace=datatype.namespace,
                    name=datatype.name,
                    description=datatype.description,
                    default_version=None,
                )
            )
            await self.connection.execute(
                datatype_versions.insert().values(
                    datatype_id=version.datatype_id,
                    version=version.version,
                    revision=version.revision,
                    status=version.status.value,
                    base_type=version.base_type.value,
                    constraints=version.constraints,
                )
            )
        except IntegrityError as error:
            classified = classify_postgresql_failure(error)
            if classified.constraint_name == "uq_datatypes_namespace_name":
                raise QualifiedNameArbitrationError from error
            raise

    async def get_lineage(self, datatype_id: UUID) -> DataType | None:
        row = (
            (
                await self.connection.execute(
                    select(datatypes).where(datatypes.c.id == datatype_id)
                )
            )
            .mappings()
            .first()
        )
        return None if row is None else _lineage(row)

    async def get_version(
        self, datatype_id: UUID, version: int
    ) -> DataTypeVersion | None:
        row = (
            (
                await self.connection.execute(
                    select(datatype_versions).where(
                        datatype_versions.c.datatype_id == datatype_id,
                        datatype_versions.c.version == version,
                    )
                )
            )
            .mappings()
            .first()
        )
        return None if row is None else _version(row)

    async def lock_lineage_no_key(self, datatype_id: UUID) -> bool:
        return await self._lock(
            RowLockKey(RowLockClass.DATA_TYPE_HEADER, datatype_id), RowLockMode.NKU
        )

    async def lock_lineage_share(self, datatype_id: UUID) -> bool:
        return await self._lock(
            RowLockKey(RowLockClass.DATA_TYPE_HEADER, datatype_id), RowLockMode.S
        )

    async def lock_lineage_update(self, datatype_id: UUID) -> bool:
        return await self._lock(
            RowLockKey(RowLockClass.DATA_TYPE_HEADER, datatype_id), RowLockMode.U
        )

    async def lock_version_no_key(self, datatype_id: UUID, version: int) -> bool:
        return await self._lock(
            RowLockKey(RowLockClass.DATA_TYPE_VERSION, datatype_id, version),
            RowLockMode.NKU,
        )

    async def lock_version_update(self, datatype_id: UUID, version: int) -> bool:
        return await self._lock(
            RowLockKey(RowLockClass.DATA_TYPE_VERSION, datatype_id, version),
            RowLockMode.U,
        )

    async def lock_version_share(self, datatype_id: UUID, version: int) -> bool:
        return await self._lock(
            RowLockKey(RowLockClass.DATA_TYPE_VERSION, datatype_id, version),
            RowLockMode.S,
        )

    async def next_version(self, datatype_id: UUID) -> int:
        maximum = await self.connection.scalar(
            select(func.max(datatype_versions.c.version)).where(
                datatype_versions.c.datatype_id == datatype_id
            )
        )
        return 1 if maximum is None else int(maximum) + 1

    async def insert_version(self, version: DataTypeVersion) -> None:
        await self.connection.execute(
            datatype_versions.insert().values(
                datatype_id=version.datatype_id,
                version=version.version,
                revision=version.revision,
                status=version.status.value,
                base_type=version.base_type.value,
                constraints=version.constraints,
            )
        )

    async def revise(
        self, datatype_id: UUID, version: int, constraints: dict[str, JsonValue]
    ) -> DataTypeVersion:
        row = (
            (
                await self.connection.execute(
                    datatype_versions.update()
                    .where(
                        datatype_versions.c.datatype_id == datatype_id,
                        datatype_versions.c.version == version,
                    )
                    .values(
                        constraints=constraints,
                        revision=datatype_versions.c.revision + 1,
                    )
                    .returning(datatype_versions)
                )
            )
            .mappings()
            .one()
        )
        return _version(row)

    async def set_status(
        self, datatype_id: UUID, version: int, status: VersionStatus
    ) -> DataTypeVersion:
        row = (
            (
                await self.connection.execute(
                    datatype_versions.update()
                    .where(
                        datatype_versions.c.datatype_id == datatype_id,
                        datatype_versions.c.version == version,
                    )
                    .values(status=status.value)
                    .returning(datatype_versions)
                )
            )
            .mappings()
            .one()
        )
        return _version(row)

    async def set_default(self, datatype_id: UUID, version: int | None) -> DataType:
        row = (
            (
                await self.connection.execute(
                    datatypes.update()
                    .where(datatypes.c.id == datatype_id)
                    .values(default_version=version)
                    .returning(datatypes)
                )
            )
            .mappings()
            .one()
        )
        return _lineage(row)

    async def set_description(
        self, datatype_id: UUID, description: str | None
    ) -> DataType | None:
        row = (
            (
                await self.connection.execute(
                    datatypes.update()
                    .where(datatypes.c.id == datatype_id)
                    .values(description=description)
                    .returning(datatypes)
                )
            )
            .mappings()
            .first()
        )
        return None if row is None else _lineage(row)

    async def has_active_consumer(self, datatype_id: UUID, version: int) -> bool:
        value = await self.connection.scalar(
            select(func.count())
            .select_from(
                object_template_properties.join(
                    object_template_versions,
                    and_(
                        object_template_properties.c.template_id
                        == object_template_versions.c.template_id,
                        object_template_properties.c.template_version
                        == object_template_versions.c.version,
                    ),
                )
            )
            .where(
                object_template_properties.c.datatype_id == datatype_id,
                object_template_properties.c.datatype_version == version,
                object_template_versions.c.status == VersionStatus.PUBLISHED.value,
            )
        )
        return bool(value)

    async def external_reference_count(self, datatype_id: UUID) -> int:
        value = await self.connection.scalar(
            select(func.count())
            .select_from(object_template_properties)
            .where(object_template_properties.c.datatype_id == datatype_id)
        )
        return int(value or 0)

    async def delete_draft(self, datatype_id: UUID, version: int) -> None:
        await self.connection.execute(
            datatype_versions.delete().where(
                datatype_versions.c.datatype_id == datatype_id,
                datatype_versions.c.version == version,
            )
        )

    async def delete_lineage(self, datatype_id: UUID) -> None:
        try:
            await self.connection.execute(
                update(datatypes)
                .where(datatypes.c.id == datatype_id)
                .values(default_version=None)
            )
            await self.connection.execute(
                datatypes.delete().where(datatypes.c.id == datatype_id)
            )
        except IntegrityError as error:
            classified = classify_postgresql_failure(error)
            if classified.constraint_name == (
                "fk_object_template_properties_datatype_version"
            ):
                raise DeleteReferenceError from error
            raise

    async def list_lineages(
        self,
        *,
        namespace: str | None,
        name: str | None,
        after: tuple[str, str] | None,
        limit: int,
    ) -> Sequence[DataType]:
        statement = select(datatypes)
        if namespace is not None:
            statement = statement.where(datatypes.c.namespace == namespace)
        if name is not None:
            statement = statement.where(datatypes.c.name == name)
        if after is not None:
            statement = statement.where(
                tuple_(datatypes.c.namespace, datatypes.c.name) > after
            )
        rows = (
            (
                await self.connection.execute(
                    statement.order_by(datatypes.c.namespace, datatypes.c.name).limit(
                        limit
                    )
                )
            )
            .mappings()
            .all()
        )
        return [_lineage(row) for row in rows]

    async def list_versions(
        self,
        datatype_id: UUID,
        *,
        status: VersionStatus | None,
        after: int | None,
        limit: int,
    ) -> Sequence[DataTypeVersionSummary]:
        statement = select(datatype_versions).where(
            datatype_versions.c.datatype_id == datatype_id
        )
        if status is not None:
            statement = statement.where(datatype_versions.c.status == status.value)
        if after is not None:
            statement = statement.where(datatype_versions.c.version > after)
        rows = (
            (
                await self.connection.execute(
                    statement.order_by(datatype_versions.c.version).limit(limit)
                )
            )
            .mappings()
            .all()
        )
        return [_summary(row) for row in rows]

    async def admit_exact(
        self, datatype_id: UUID, version: int
    ) -> DataTypeVersion | None:
        if not await self.lock_version_share(datatype_id, version):
            return None
        return await self.get_version(datatype_id, version)

    async def admit_default(
        self, datatype_id: UUID
    ) -> tuple[DataType, DataTypeVersion | None] | None:
        if not await self.lock_lineage_share(datatype_id):
            return None
        lineage = await self.get_lineage(datatype_id)
        if lineage is None:
            return None
        if lineage.default_version is None:
            return lineage, None
        version = await self.admit_exact(datatype_id, lineage.default_version)
        return lineage, version
