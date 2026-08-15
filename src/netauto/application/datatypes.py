"""Complete M1 DataType semantic application capability."""

from dataclasses import dataclass
from typing import cast
from uuid import UUID, uuid4

from netauto.application.cursors import decode_cursor, encode_cursor
from netauto.domain.datatypes import (
    CreateDataTypeResult,
    DataType,
    DataTypeVersion,
    DataTypeVersionSummary,
    VersionStatus,
    validate_qualified_name,
)
from netauto.domain.primitives import (
    JsonValue,
    PrimitiveValidationError,
    canonicalize_constraints,
    parse_primitive_type,
)
from netauto.failures import ApplicationFailure, FailureClass
from netauto.persistence.datatypes import (
    DataTypeStore,
    DeleteReferenceError,
    QualifiedNameArbitrationError,
)
from netauto.persistence.uow import UnitOfWorkFactory


@dataclass(frozen=True, slots=True)
class Page[T]:
    items: list[T]
    next_cursor: str | None


def _not_found(datatype_id: UUID, version: int | None = None) -> ApplicationFailure:
    details: dict[str, JsonValue] = {
        "resource_type": "datatype" if version is None else "datatype_version",
        "id": str(datatype_id),
    }
    if version is not None:
        details["version"] = version
    return ApplicationFailure(
        FailureClass.NOT_FOUND,
        "resource_not_found",
        "The requested DataType resource does not exist.",
        details,
    )


def _referenced_version_not_found(
    datatype_id: UUID, version: int
) -> ApplicationFailure:
    return ApplicationFailure(
        FailureClass.SEMANTIC_VALIDATION,
        "referenced_resource_not_found",
        "The referenced DataTypeVersion does not exist.",
        {
            "resource_type": "datatype_version",
            "id": str(datatype_id),
            "version": version,
        },
    )


def _semantic(error: PrimitiveValidationError | ValueError) -> ApplicationFailure:
    path = getattr(error, "path", "datatype")
    rule = getattr(error, "rule", str(error))
    return ApplicationFailure(
        FailureClass.SEMANTIC_VALIDATION,
        "semantic_validation_failed",
        "The DataType candidate is not semantically valid.",
        {"violations": [{"path": path, "rule": rule}]},
    )


def _state(
    code: str, message: str, details: dict[str, JsonValue]
) -> ApplicationFailure:
    return ApplicationFailure(FailureClass.STATE_CONFLICT, code, message, details)


class DataTypeService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def create(
        self,
        namespace: str,
        name: str,
        base_type: str,
        description: str | None,
        constraints: object,
    ) -> CreateDataTypeResult:
        try:
            validate_qualified_name(namespace, name, public=True)
            primitive = parse_primitive_type(base_type)
            canonical = canonicalize_constraints(primitive, constraints)
        except (PrimitiveValidationError, ValueError) as error:
            raise _semantic(error) from error
        datatype_id = uuid4()
        lineage = DataType(datatype_id, namespace, name, description, None)
        version = DataTypeVersion(
            datatype_id,
            1,
            1,
            VersionStatus.DRAFT,
            primitive,
            canonical,
        )
        try:
            async with self._uow_factory() as uow:
                await DataTypeStore(uow.connection).create(lineage, version)
                await uow.commit()
        except QualifiedNameArbitrationError as error:
            raise _state(
                "qualified_name_conflict",
                "The qualified DataType name is already in use.",
                {"namespace": namespace, "name": name},
            ) from error
        return CreateDataTypeResult(lineage, version)

    async def create_next(
        self, datatype_id: UUID, source_version: int
    ) -> DataTypeVersion:
        async with self._uow_factory() as uow:
            store = DataTypeStore(uow.connection)
            if not await store.lock_lineage_no_key(datatype_id):
                raise _not_found(datatype_id)
            source = await store.get_version(datatype_id, source_version)
            if source is None:
                raise _referenced_version_not_found(datatype_id, source_version)
            if source.status not in {VersionStatus.PUBLISHED, VersionStatus.DEPRECATED}:
                raise _state(
                    "version_source_conflict",
                    "The selected version is not eligible as a create-next source.",
                    {"id": str(datatype_id), "source_version": source_version},
                )
            created = DataTypeVersion(
                datatype_id,
                await store.next_version(datatype_id),
                1,
                VersionStatus.DRAFT,
                source.base_type,
                source.constraints,
            )
            await store.insert_version(created)
            await uow.commit()
            return created

    async def revise(
        self,
        datatype_id: UUID,
        version: int,
        expected_revision: int,
        constraints: object,
    ) -> DataTypeVersion:
        async with self._uow_factory() as uow:
            store = DataTypeStore(uow.connection)
            if not await store.lock_version_no_key(datatype_id, version):
                raise _not_found(datatype_id, version)
            current = await store.get_version(datatype_id, version)
            if current is None:
                raise _not_found(datatype_id, version)
            self._require_draft(current, expected_revision)
            try:
                canonical = canonicalize_constraints(current.base_type, constraints)
            except PrimitiveValidationError as error:
                raise _semantic(error) from error
            revised = await store.revise(datatype_id, version, canonical)
            await uow.commit()
            return revised

    async def publish(
        self, datatype_id: UUID, version: int, expected_revision: int
    ) -> DataTypeVersion:
        async with self._uow_factory() as uow:
            store = DataTypeStore(uow.connection)
            if not await store.lock_lineage_no_key(datatype_id):
                raise _not_found(datatype_id)
            if not await store.lock_version_no_key(datatype_id, version):
                raise _not_found(datatype_id, version)
            lineage = await store.get_lineage(datatype_id)
            current = await store.get_version(datatype_id, version)
            if lineage is None or current is None:
                raise _not_found(datatype_id, version)
            self._require_draft(current, expected_revision)
            published = await store.set_status(
                datatype_id, version, VersionStatus.PUBLISHED
            )
            if lineage.default_version is None:
                await store.set_default(datatype_id, version)
            await uow.commit()
            return published

    async def set_default(self, datatype_id: UUID, version: int) -> DataType:
        async with self._uow_factory() as uow:
            store = DataTypeStore(uow.connection)
            if not await store.lock_lineage_no_key(datatype_id):
                raise _not_found(datatype_id)
            target = await store.admit_exact(datatype_id, version)
            if target is None:
                raise _referenced_version_not_found(datatype_id, version)
            if target.status is not VersionStatus.PUBLISHED:
                raise _state(
                    "dependency_not_admissible",
                    "The selected default version is not PUBLISHED.",
                    {"id": str(datatype_id), "version": version},
                )
            lineage = await store.set_default(datatype_id, version)
            await uow.commit()
            return lineage

    async def clear_default(self, datatype_id: UUID) -> DataType:
        async with self._uow_factory() as uow:
            store = DataTypeStore(uow.connection)
            if not await store.lock_lineage_no_key(datatype_id):
                raise _not_found(datatype_id)
            lineage = await store.set_default(datatype_id, None)
            await uow.commit()
            return lineage

    async def deprecate(self, datatype_id: UUID, version: int) -> DataTypeVersion:
        async with self._uow_factory() as uow:
            store = DataTypeStore(uow.connection)
            if not await store.lock_lineage_share(datatype_id):
                raise _not_found(datatype_id)
            if not await store.lock_version_no_key(datatype_id, version):
                raise _not_found(datatype_id, version)
            lineage = await store.get_lineage(datatype_id)
            current = await store.get_version(datatype_id, version)
            if lineage is None or current is None:
                raise _not_found(datatype_id, version)
            if current.status is not VersionStatus.PUBLISHED:
                raise _state(
                    "lifecycle_state_conflict",
                    "Only a PUBLISHED DataTypeVersion can be deprecated.",
                    {"id": str(datatype_id), "version": version},
                )
            if lineage.default_version == version:
                raise _state(
                    "default_version_conflict",
                    "The current default version cannot be deprecated.",
                    {"id": str(datatype_id), "version": version},
                )
            if await store.has_active_consumer(datatype_id, version):
                raise _state(
                    "active_dependency_conflict",
                    "A PUBLISHED model consumer depends on this version.",
                    {"id": str(datatype_id), "version": version},
                )
            deprecated = await store.set_status(
                datatype_id, version, VersionStatus.DEPRECATED
            )
            await uow.commit()
            return deprecated

    async def delete_draft(
        self, datatype_id: UUID, version: int, expected_revision: int
    ) -> None:
        async with self._uow_factory() as uow:
            store = DataTypeStore(uow.connection)
            if not await store.lock_lineage_no_key(datatype_id):
                raise _not_found(datatype_id)
            if not await store.lock_version_update(datatype_id, version):
                raise _not_found(datatype_id, version)
            current = await store.get_version(datatype_id, version)
            if current is None:
                raise _not_found(datatype_id, version)
            self._require_draft(current, expected_revision)
            await store.delete_draft(datatype_id, version)
            await uow.commit()

    async def delete_lineage(self, datatype_id: UUID) -> None:
        async with self._uow_factory() as uow:
            store = DataTypeStore(uow.connection)
            if not await store.lock_lineage_update(datatype_id):
                raise _not_found(datatype_id)
            count = await store.external_reference_count(datatype_id)
            if count:
                raise _state(
                    "delete_blocked",
                    "Current references prevent DataType deletion.",
                    {
                        "resource_type": "datatype",
                        "id": str(datatype_id),
                        "blockers": [
                            {"type": "object_template_property", "count": count}
                        ],
                    },
                )
            try:
                await store.delete_lineage(datatype_id)
            except DeleteReferenceError as error:
                raise _state(
                    "delete_blocked",
                    "A concurrent current reference prevented DataType deletion.",
                    {"resource_type": "datatype", "id": str(datatype_id)},
                ) from error
            await uow.commit()

    async def set_description(
        self, datatype_id: UUID, description: str | None
    ) -> DataType:
        async with self._uow_factory() as uow:
            lineage = await DataTypeStore(uow.connection).set_description(
                datatype_id, description
            )
            if lineage is None:
                raise _not_found(datatype_id)
            await uow.commit()
            return lineage

    async def get_lineage(self, datatype_id: UUID) -> DataType:
        async with self._uow_factory() as uow:
            lineage = await DataTypeStore(uow.connection).get_lineage(datatype_id)
            if lineage is None:
                raise _not_found(datatype_id)
            return lineage

    async def get_version(self, datatype_id: UUID, version: int) -> DataTypeVersion:
        async with self._uow_factory() as uow:
            current = await DataTypeStore(uow.connection).get_version(
                datatype_id, version
            )
            if current is None:
                raise _not_found(datatype_id, version)
            return current

    async def list_lineages(
        self,
        *,
        namespace: str | None,
        name: str | None,
        cursor: str | None,
        limit: int,
    ) -> Page[DataType]:
        filters: dict[str, JsonValue] = {"namespace": namespace, "name": name}
        after: tuple[str, str] | None = None
        if cursor is not None:
            key = decode_cursor(cursor, "datatypes", filters)
            if len(key) != 2 or not all(isinstance(item, str) for item in key):
                raise ApplicationFailure(
                    FailureClass.INVALID_REQUEST,
                    "invalid_cursor",
                    "The cursor is malformed or incompatible with this query.",
                )
            after = cast(tuple[str, str], (key[0], key[1]))
        async with self._uow_factory() as uow:
            rows = list(
                await DataTypeStore(uow.connection).list_lineages(
                    namespace=namespace,
                    name=name,
                    after=after,
                    limit=limit + 1,
                )
            )
        more = len(rows) > limit
        items = rows[:limit]
        next_cursor = None
        if more:
            last = items[-1]
            next_cursor = encode_cursor(
                "datatypes", filters, [last.namespace, last.name]
            )
        return Page(items, next_cursor)

    async def list_versions(
        self,
        datatype_id: UUID,
        *,
        status: VersionStatus | None,
        cursor: str | None,
        limit: int,
    ) -> Page[DataTypeVersionSummary]:
        filters: dict[str, JsonValue] = {
            "datatype_id": str(datatype_id),
            "status": None if status is None else status.value,
        }
        after: int | None = None
        if cursor is not None:
            key = decode_cursor(cursor, "datatype_versions", filters)
            if len(key) != 1 or isinstance(key[0], bool) or not isinstance(key[0], int):
                raise ApplicationFailure(
                    FailureClass.INVALID_REQUEST,
                    "invalid_cursor",
                    "The cursor is malformed or incompatible with this query.",
                )
            after = key[0]
        async with self._uow_factory() as uow:
            store = DataTypeStore(uow.connection)
            if await store.get_lineage(datatype_id) is None:
                raise _not_found(datatype_id)
            rows = list(
                await store.list_versions(
                    datatype_id, status=status, after=after, limit=limit + 1
                )
            )
        more = len(rows) > limit
        items = rows[:limit]
        next_cursor = None
        if more:
            next_cursor = encode_cursor(
                "datatype_versions", filters, [items[-1].version]
            )
        return Page(items, next_cursor)

    async def admit_exact_binding(
        self, datatype_id: UUID, version: int
    ) -> DataTypeVersion:
        async with self._uow_factory() as uow:
            current = await DataTypeStore(uow.connection).admit_exact(
                datatype_id, version
            )
            if current is None:
                raise _referenced_version_not_found(datatype_id, version)
            if current.status is not VersionStatus.PUBLISHED:
                raise _state(
                    "dependency_not_admissible",
                    "The exact dependency is not PUBLISHED.",
                    {"id": str(datatype_id), "version": version},
                )
            return current

    async def admit_default_binding(self, datatype_id: UUID) -> DataTypeVersion:
        async with self._uow_factory() as uow:
            result = await DataTypeStore(uow.connection).admit_default(datatype_id)
            if result is None:
                raise _referenced_version_not_found(datatype_id, 0)
            lineage, current = result
            if lineage.default_version is None:
                raise _state(
                    "default_version_unavailable",
                    "The DataType has no current default version.",
                    {"id": str(datatype_id)},
                )
            if current is None or current.status is not VersionStatus.PUBLISHED:
                raise _state(
                    "dependency_not_admissible",
                    "The default dependency is not PUBLISHED.",
                    {"id": str(datatype_id), "version": lineage.default_version},
                )
            return current

    @staticmethod
    def _require_draft(current: DataTypeVersion, expected_revision: int) -> None:
        if current.status is not VersionStatus.DRAFT:
            raise _state(
                "lifecycle_state_conflict",
                "The operation requires a DRAFT DataTypeVersion.",
                {"id": str(current.datatype_id), "version": current.version},
            )
        if current.revision != expected_revision:
            raise _state(
                "stale_revision",
                "The draft revision does not match the expected revision.",
                {
                    "expected_revision": expected_revision,
                    "current_revision": current.revision,
                },
            )
