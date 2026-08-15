"""M1 intrinsic Object state and lifecycle application capability."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from netauto.application.cursors import Page, decode_cursor, encode_cursor
from netauto.application.objecttemplates import resolve_exact_effective_schema
from netauto.domain.datatypes import DataTypeVersion, VersionStatus
from netauto.domain.objects import (
    DataChangeOperation,
    Object,
    ObjectSummary,
    ObjectValidationError,
    RuntimePropertySpec,
    apply_data_change,
    canonicalize_properties,
    validate_canonical_name,
)
from netauto.domain.primitives import (
    JsonValue,
    PrimitiveType,
    PrimitiveValidationError,
    canonicalize_constraints,
    validate_value,
)
from netauto.failures import ApplicationFailure, FailureClass
from netauto.persistence.datatypes import DataTypeStore
from netauto.persistence.objects import (
    EventKind,
    IntrinsicLifecycleEvent,
    ObjectStore,
    ObjectTemplateReferenceError,
)
from netauto.persistence.objecttemplates import ObjectTemplateStore
from netauto.persistence.uow import UnitOfWorkFactory


def _not_found(object_id: UUID) -> ApplicationFailure:
    return ApplicationFailure(
        FailureClass.NOT_FOUND,
        "resource_not_found",
        "The requested Object does not exist.",
        {"resource_type": "object", "id": str(object_id)},
    )


def _referenced(template_id: UUID, version: int | None = None) -> ApplicationFailure:
    details: dict[str, JsonValue] = {
        "resource_type": (
            "object_template" if version is None else "object_template_version"
        ),
        "id": str(template_id),
    }
    if version is not None:
        details["version"] = version
    return ApplicationFailure(
        FailureClass.SEMANTIC_VALIDATION,
        "referenced_resource_not_found",
        "The selected ObjectTemplate resource does not exist.",
        details,
    )


def _semantic(
    error: ObjectValidationError | PrimitiveValidationError,
) -> ApplicationFailure:
    return ApplicationFailure(
        FailureClass.SEMANTIC_VALIDATION,
        "semantic_validation_failed",
        "The Object candidate is not semantically valid.",
        {
            "violations": [
                {"path": error.path, "rule": error.rule},
            ]
        },
    )


def _state(
    code: str, message: str, details: dict[str, JsonValue]
) -> ApplicationFailure:
    return ApplicationFailure(FailureClass.STATE_CONFLICT, code, message, details)


def _internal(message: str) -> ApplicationFailure:
    return ApplicationFailure(FailureClass.INTERNAL_FAILURE, "internal_error", message)


def _canonical_timestamp(value: datetime) -> str:
    utc = value.astimezone(UTC)
    return str(
        validate_value(
            PrimitiveType.DATETIME, utc.isoformat(timespec="microseconds"), {}
        )
    )


def _cursor_timestamp(value: object) -> datetime:
    try:
        canonical = validate_value(PrimitiveType.DATETIME, value, {}, "cursor")
        return datetime.fromisoformat(str(canonical).replace("Z", "+00:00"))
    except (PrimitiveValidationError, ValueError) as error:
        raise ApplicationFailure(
            FailureClass.INVALID_REQUEST,
            "invalid_cursor",
            "The cursor is malformed or incompatible with this query.",
        ) from error


class ObjectService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def _runtime_specs(
        self,
        template_store: ObjectTemplateStore,
        template_id: UUID,
        template_version: int,
    ) -> tuple[RuntimePropertySpec, ...]:
        exact = await template_store.get_version(template_id, template_version)
        if exact is None:
            raise _internal("A persisted exact ObjectTemplateVersion is missing.")
        if exact.status is VersionStatus.DRAFT:
            raise _internal("A persisted Object is pinned to a DRAFT schema.")
        try:
            schema = await resolve_exact_effective_schema(template_store, exact)
        except (RuntimeError, ValueError) as error:
            raise _internal(
                "The persisted ObjectTemplate effective schema is invalid."
            ) from error
        datatype_store = DataTypeStore(template_store.connection)
        resolved: dict[tuple[UUID, int], DataTypeVersion] = {}
        specs: list[RuntimePropertySpec] = []
        for effective in schema.properties:
            item = effective.declaration
            key = (item.datatype_id, item.datatype_version)
            datatype = resolved.get(key)
            if datatype is None:
                loaded = await datatype_store.get_version(*key)
                if loaded is None:
                    raise _internal("A persisted exact DataTypeVersion is missing.")
                if loaded.status is VersionStatus.DRAFT:
                    raise _internal(
                        "A persisted Object schema references a DRAFT DataTypeVersion."
                    )
                try:
                    canonical_constraints = canonicalize_constraints(
                        loaded.base_type, loaded.constraints
                    )
                except PrimitiveValidationError as error:
                    raise _internal(
                        "A persisted DataTypeVersion constraint set is invalid."
                    ) from error
                if canonical_constraints != loaded.constraints:
                    raise _internal(
                        "A persisted DataTypeVersion constraint set is not canonical."
                    )
                datatype = loaded
                resolved[key] = loaded
            specs.append(
                RuntimePropertySpec(
                    item.name,
                    item.value_mode,
                    item.required,
                    datatype.base_type,
                    datatype.constraints,
                )
            )
        return tuple(specs)

    async def _validate_persisted_object(
        self, template_store: ObjectTemplateStore, value: Object
    ) -> tuple[RuntimePropertySpec, ...]:
        specs = await self._runtime_specs(
            template_store, value.template_id, value.template_version
        )
        try:
            canonical = canonicalize_properties(value.properties, specs)
        except (ObjectValidationError, PrimitiveValidationError) as error:
            raise _internal("The persisted Object runtime state is invalid.") from error
        if canonical != value.properties:
            raise _internal("The persisted Object runtime state is not canonical.")
        return specs

    async def create(
        self,
        template_id: UUID,
        template_version: int | None,
        canonical_name: str | None,
        properties: dict[str, object],
    ) -> Object:
        object_id = uuid4()
        name = str(object_id) if canonical_name is None else canonical_name
        try:
            validate_canonical_name(name)
        except ObjectValidationError as error:
            raise _semantic(error) from error
        async with self._uow_factory() as uow:
            template_store = ObjectTemplateStore(uow.connection)
            if template_version is None:
                admitted = await template_store.admit_default(template_id)
                if admitted is None:
                    raise _referenced(template_id)
                lineage, header = admitted
                if lineage.default_version is None:
                    raise _state(
                        "default_version_unavailable",
                        "The selected ObjectTemplate has no default version.",
                        {"id": str(template_id)},
                    )
                if header is None:
                    raise _internal(
                        "The persisted ObjectTemplate default target is missing."
                    )
                selected_version = lineage.default_version
            else:
                header = await template_store.admit_exact(template_id, template_version)
                if header is None:
                    raise _referenced(template_id, template_version)
                lineage = await template_store.get_lineage(template_id)
                if lineage is None:
                    raise _internal("The persisted ObjectTemplate lineage is missing.")
                selected_version = template_version
            if header.status is not VersionStatus.PUBLISHED:
                raise _state(
                    "dependency_not_admissible",
                    "The selected ObjectTemplateVersion is not PUBLISHED.",
                    {"id": str(template_id), "version": selected_version},
                )
            if lineage.abstract:
                raise _semantic(
                    ObjectValidationError("template_id", "abstract_template")
                )
            specs = await self._runtime_specs(
                template_store, template_id, selected_version
            )
            try:
                canonical = canonicalize_properties(properties, specs)
            except (ObjectValidationError, PrimitiveValidationError) as error:
                raise _semantic(error) from error
            result = Object(object_id, name, template_id, selected_version, canonical)
            store = ObjectStore(uow.connection)
            try:
                await store.insert(result)
            except ObjectTemplateReferenceError as error:
                raise _referenced(template_id, selected_version) from error
            await store.insert_intrinsic_event(EventKind.CREATED, result, None, result)
            await uow.commit()
            return result

    async def get(self, object_id: UUID) -> Object:
        async with self._uow_factory() as uow:
            value = await ObjectStore(uow.connection).get(object_id)
            if value is None:
                raise _not_found(object_id)
            await self._validate_persisted_object(
                ObjectTemplateStore(uow.connection), value
            )
            return value

    async def rename(self, object_id: UUID, canonical_name: str) -> Object:
        try:
            validate_canonical_name(canonical_name)
        except ObjectValidationError as error:
            raise _semantic(error) from error
        async with self._uow_factory() as uow:
            store = ObjectStore(uow.connection)
            before = await store.lock_no_key(object_id)
            if before is None:
                raise _not_found(object_id)
            await self._validate_persisted_object(
                ObjectTemplateStore(uow.connection), before
            )
            after = Object(
                before.id,
                canonical_name,
                before.template_id,
                before.template_version,
                before.properties,
            )
            await store.update_name(object_id, canonical_name)
            await store.insert_intrinsic_event(EventKind.RENAME, after, before, after)
            await uow.commit()
            return after

    async def data_change(
        self, object_id: UUID, operations: tuple[DataChangeOperation, ...]
    ) -> Object:
        async with self._uow_factory() as uow:
            store = ObjectStore(uow.connection)
            before = await store.lock_no_key(object_id)
            if before is None:
                raise _not_found(object_id)
            specs = await self._validate_persisted_object(
                ObjectTemplateStore(uow.connection), before
            )
            try:
                properties = apply_data_change(before.properties, operations, specs)
            except (ObjectValidationError, PrimitiveValidationError) as error:
                raise _semantic(error) from error
            if properties == before.properties:
                return before
            after = Object(
                before.id,
                before.canonical_name,
                before.template_id,
                before.template_version,
                properties,
            )
            await store.update_properties(object_id, properties)
            await store.insert_intrinsic_event(
                EventKind.DATA_CHANGE, after, before, after
            )
            await uow.commit()
            return after

    async def list_objects(
        self,
        *,
        template_id: UUID | None,
        template_version: int | None,
        canonical_name: str | None,
        cursor: str | None,
        limit: int,
    ) -> Page[ObjectSummary]:
        if template_version is not None and template_id is None:
            raise ApplicationFailure(
                FailureClass.INVALID_REQUEST,
                "invalid_request",
                "template_version requires template_id.",
            )
        filters: dict[str, JsonValue] = {
            "template_id": None if template_id is None else str(template_id),
            "template_version": template_version,
            "canonical_name": canonical_name,
        }
        after: UUID | None = None
        if cursor is not None:
            key = decode_cursor(cursor, "objects", filters)
            if len(key) != 1 or not isinstance(key[0], str):
                raise ApplicationFailure(
                    FailureClass.INVALID_REQUEST,
                    "invalid_cursor",
                    "The cursor is malformed or incompatible with this query.",
                )
            try:
                after = UUID(key[0])
            except ValueError as error:
                raise ApplicationFailure(
                    FailureClass.INVALID_REQUEST,
                    "invalid_cursor",
                    "The cursor is malformed or incompatible with this query.",
                ) from error
        async with self._uow_factory() as uow:
            rows = list(
                await ObjectStore(uow.connection).list_objects(
                    template_id=template_id,
                    template_version=template_version,
                    canonical_name=canonical_name,
                    after=after,
                    limit=limit + 1,
                )
            )
        more = len(rows) > limit
        items = rows[:limit]
        next_cursor = (
            encode_cursor("objects", filters, [str(items[-1].id)]) if more else None
        )
        return Page(items, next_cursor)

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
        cursor: str | None,
        limit: int,
    ) -> Page[IntrinsicLifecycleEvent]:
        filters: dict[str, JsonValue] = {
            "kind": None if kind is None else kind.value,
            "object_id": None if object_id is None else str(object_id),
            "destination_object_id": (
                None if destination_object_id is None else str(destination_object_id)
            ),
            "relationship_id": (
                None if relationship_id is None else str(relationship_id)
            ),
            "relationship_definition_id": (
                None
                if relationship_definition_id is None
                else str(relationship_definition_id)
            ),
            "relationship_name": relationship_name,
            "occurred_from": (
                None if occurred_from is None else _canonical_timestamp(occurred_from)
            ),
            "occurred_to": (
                None if occurred_to is None else _canonical_timestamp(occurred_to)
            ),
            "involving_object_id": (
                None if involving_object_id is None else str(involving_object_id)
            ),
        }
        after: tuple[datetime, UUID] | None = None
        if cursor is not None:
            key = decode_cursor(cursor, "lifecycle_events", filters)
            if len(key) != 2 or not all(isinstance(item, str) for item in key):
                raise ApplicationFailure(
                    FailureClass.INVALID_REQUEST,
                    "invalid_cursor",
                    "The cursor is malformed or incompatible with this query.",
                )
            first = key[0]
            second = key[1]
            if not isinstance(first, str) or not isinstance(second, str):
                raise ApplicationFailure(
                    FailureClass.INVALID_REQUEST,
                    "invalid_cursor",
                    "The cursor is malformed or incompatible with this query.",
                )
            try:
                after = (_cursor_timestamp(first), UUID(second))
            except ValueError as error:
                raise ApplicationFailure(
                    FailureClass.INVALID_REQUEST,
                    "invalid_cursor",
                    "The cursor is malformed or incompatible with this query.",
                ) from error
        async with self._uow_factory() as uow:
            store = ObjectStore(uow.connection)
            if involving_object_id is not None:
                if await store.get(involving_object_id) is None:
                    raise _not_found(involving_object_id)
            try:
                rows = list(
                    await store.list_events(
                        kind=kind,
                        object_id=object_id,
                        destination_object_id=destination_object_id,
                        relationship_id=relationship_id,
                        relationship_definition_id=relationship_definition_id,
                        relationship_name=relationship_name,
                        occurred_from=occurred_from,
                        occurred_to=occurred_to,
                        involving_object_id=involving_object_id,
                        after=after,
                        limit=limit + 1,
                    )
                )
            except RuntimeError as error:
                raise _internal(
                    "The persisted lifecycle event state is invalid."
                ) from error
        more = len(rows) > limit
        items = rows[:limit]
        next_cursor = (
            encode_cursor(
                "lifecycle_events",
                filters,
                [_canonical_timestamp(items[-1].occurred_at), str(items[-1].id)],
            )
            if more
            else None
        )
        return Page(items, next_cursor)
