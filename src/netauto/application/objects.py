"""M1 intrinsic Object state and lifecycle application capability."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from netauto.application.cursors import Page, decode_cursor, encode_cursor
from netauto.application.objecttemplates import resolve_exact_effective_schema
from netauto.domain.datatypes import DataTypeVersion, VersionStatus
from netauto.domain.objects import (
    DataChangeOperation,
    Object,
    ObjectSummary,
    ObjectValidationError,
    ResolvedComponentSlot,
    RuntimePropertySpec,
    SchemaChangeBlocked,
    SchemaPropertySpec,
    apply_data_change,
    canonicalize_properties,
    migrate_properties,
    validate_canonical_name,
)
from netauto.domain.objecttemplates import (
    EffectiveSchema,
    ObjectTemplate,
    ObjectTemplateVersion,
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
from netauto.persistence.locking import (
    AdvisoryGate,
    LockPlan,
    LockPlanAttemptsExhausted,
    RowLockClass,
    RowLockIntent,
    RowLockKey,
    RowLockMode,
    acquire_lock_plan,
    prepare_lock_plan,
    run_semantic_uow_attempts,
)
from netauto.persistence.objects import (
    EventKind,
    LifecycleEvent,
    ObjectDeleteReferenceError,
    ObjectStore,
    ObjectTemplateReferenceError,
    OwnershipConflictError,
    OwnershipFact,
    OwnershipReferenceError,
)
from netauto.persistence.objecttemplates import ObjectTemplateStore
from netauto.persistence.uow import UnitOfWorkFactory


@dataclass(frozen=True, slots=True)
class ComponentProjection:
    slot_declaring_template_id: UUID
    slot_name: str
    child_object_id: UUID


@dataclass(frozen=True, slots=True)
class OwnerProjection:
    parent_object_id: UUID
    slot_declaring_template_id: UUID
    slot_name: str


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


def _referenced_object(object_id: UUID) -> ApplicationFailure:
    return ApplicationFailure(
        FailureClass.SEMANTIC_VALIDATION,
        "referenced_resource_not_found",
        "The referenced Object does not exist.",
        {"resource_type": "object", "id": str(object_id)},
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


def _object_intent(object_id: UUID, mode: RowLockMode) -> RowLockIntent:
    return RowLockIntent(RowLockKey(RowLockClass.OBJECT, object_id), mode)


def _template_header(template_id: UUID, mode: RowLockMode) -> RowLockIntent:
    return RowLockIntent(
        RowLockKey(RowLockClass.OBJECT_TEMPLATE_HEADER, template_id), mode
    )


def _template_version(
    template_id: UUID, version: int, mode: RowLockMode
) -> RowLockIntent:
    return RowLockIntent(
        RowLockKey(RowLockClass.OBJECT_TEMPLATE_VERSION, template_id, version), mode
    )


async def _acquire(
    connection: Any,
    intents: tuple[RowLockIntent, ...],
    *,
    gate: AdvisoryGate | None = None,
) -> tuple[LockPlan, tuple[RowLockKey, ...]]:
    plan = await prepare_lock_plan(connection, intents=intents, gate=gate)
    missing = await acquire_lock_plan(connection, plan)
    return plan, missing


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

    async def _schema_specs(
        self,
        template_store: ObjectTemplateStore,
        template_id: UUID,
        template_version: int,
    ) -> tuple[EffectiveSchema, tuple[SchemaPropertySpec, ...]]:
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
        specs: list[SchemaPropertySpec] = []
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
                SchemaPropertySpec(
                    effective.declaring_template_id,
                    RuntimePropertySpec(
                        item.name,
                        item.value_mode,
                        item.required,
                        datatype.base_type,
                        datatype.constraints,
                    ),
                    item.migration_default,
                )
            )
        return schema, tuple(specs)

    async def _runtime_specs(
        self,
        template_store: ObjectTemplateStore,
        template_id: UUID,
        template_version: int,
    ) -> tuple[RuntimePropertySpec, ...]:
        _, specs = await self._schema_specs(
            template_store, template_id, template_version
        )
        return tuple(item.runtime for item in specs)

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

    @staticmethod
    def _slot(schema: EffectiveSchema, name: str) -> ResolvedComponentSlot | None:
        matches = [item for item in schema.components if item.declaration.name == name]
        if len(matches) > 1:
            raise RuntimeError("effective component schema is ambiguous")
        if not matches:
            return None
        item = matches[0]
        return ResolvedComponentSlot(
            item.declaring_template_id,
            item.declaration.name,
            item.declaration.target_template_id,
        )

    @staticmethod
    def _component(slot: ResolvedComponentSlot, child_id: UUID) -> ComponentProjection:
        return ComponentProjection(slot.declaring_template_id, slot.name, child_id)

    async def _selected_template(
        self,
        store: ObjectTemplateStore,
        template_id: UUID,
        requested_version: int | None,
    ) -> tuple[ObjectTemplate, ObjectTemplateVersion, int]:
        lineage = await store.get_lineage(template_id)
        if lineage is None:
            raise _referenced(template_id)
        if requested_version is None:
            if lineage.default_version is None:
                raise _state(
                    "default_version_unavailable",
                    "The selected ObjectTemplate has no default version.",
                    {"id": str(template_id)},
                )
            selected_version = lineage.default_version
        else:
            selected_version = requested_version
        header = await store.get_version(template_id, selected_version)
        if header is None:
            if requested_version is None:
                raise _internal(
                    "The persisted ObjectTemplate default target is missing."
                )
            raise _referenced(template_id, requested_version)
        return lineage, header, selected_version

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

        async def attempt(uow: Any, attempt_number: int) -> Object:
            del attempt_number
            template_store = ObjectTemplateStore(uow.connection)
            lineage, header, selected_version = await self._selected_template(
                template_store, template_id, template_version
            )
            intents = (
                _template_header(
                    template_id,
                    RowLockMode.S if template_version is None else RowLockMode.KS,
                ),
                _template_version(template_id, selected_version, RowLockMode.S),
            )
            plan, _ = await _acquire(uow.connection, intents)
            lineage, header, selected_version = await self._selected_template(
                template_store, template_id, template_version
            )
            plan.require_same_plan(
                (
                    _template_header(
                        template_id,
                        RowLockMode.S if template_version is None else RowLockMode.KS,
                    ),
                    _template_version(template_id, selected_version, RowLockMode.S),
                )
            )
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
            plan.begin_dml()
            try:
                await store.insert(result)
            except ObjectTemplateReferenceError as error:
                raise _referenced(template_id, selected_version) from error
            await store.insert_intrinsic_event(EventKind.CREATED, result, None, result)
            await uow.commit()
            return result

        try:
            return await run_semantic_uow_attempts(self._uow_factory, attempt)
        except LockPlanAttemptsExhausted as error:
            raise _internal("The Object lock plan did not stabilize.") from error

    async def get(self, object_id: UUID) -> Object:
        async with self._uow_factory() as uow:
            value = await ObjectStore(uow.connection).get(object_id)
            if value is None:
                raise _not_found(object_id)
            await self._validate_persisted_object(
                ObjectTemplateStore(uow.connection), value
            )
            return value

    async def delete(self, object_id: UUID) -> None:
        async with self._uow_factory() as uow:
            store = ObjectStore(uow.connection)
            template_store = ObjectTemplateStore(uow.connection)
            plan, missing = await _acquire(
                uow.connection,
                (_object_intent(object_id, RowLockMode.U),),
            )
            if missing:
                raise _not_found(object_id)
            before = await store.get(object_id)
            if before is None:
                raise _not_found(object_id)
            await self._validate_persisted_object(template_store, before)
            counts = await store.delete_blocker_counts(object_id)
            blockers: list[JsonValue] = [
                {"type": blocker_type, "count": counts[blocker_type]}
                for blocker_type in ("ownership", "relationship")
                if counts[blocker_type]
            ]
            if blockers:
                raise _state(
                    "delete_blocked",
                    "Current references prevent Object deletion.",
                    {
                        "resource_type": "object",
                        "id": str(object_id),
                        "blockers": blockers,
                    },
                )
            plan.begin_dml()
            try:
                await store.delete(object_id)
            except ObjectDeleteReferenceError as error:
                raise _state(
                    "delete_blocked",
                    "A concurrent current reference prevented Object deletion.",
                    {
                        "resource_type": "object",
                        "id": str(object_id),
                        "blockers": [{"type": error.blocker_type, "count": 1}],
                    },
                ) from error
            await store.insert_intrinsic_event(EventKind.DELETED, before, before, None)
            await uow.commit()

    async def rename(self, object_id: UUID, canonical_name: str) -> Object:
        try:
            validate_canonical_name(canonical_name)
        except ObjectValidationError as error:
            raise _semantic(error) from error
        async with self._uow_factory() as uow:
            store = ObjectStore(uow.connection)
            template_store = ObjectTemplateStore(uow.connection)
            plan, missing = await _acquire(
                uow.connection,
                (_object_intent(object_id, RowLockMode.NKU),),
            )
            if missing:
                raise _not_found(object_id)
            before = await store.get(object_id)
            if before is None:
                raise _not_found(object_id)
            await self._validate_persisted_object(template_store, before)
            after = Object(
                before.id,
                canonical_name,
                before.template_id,
                before.template_version,
                before.properties,
            )
            plan.begin_dml()
            await store.update_name(object_id, canonical_name)
            await store.insert_intrinsic_event(EventKind.RENAME, after, before, after)
            await uow.commit()
            return after

    async def data_change(
        self, object_id: UUID, operations: tuple[DataChangeOperation, ...]
    ) -> Object:
        async with self._uow_factory() as uow:
            store = ObjectStore(uow.connection)
            template_store = ObjectTemplateStore(uow.connection)
            plan, missing = await _acquire(
                uow.connection,
                (_object_intent(object_id, RowLockMode.NKU),),
            )
            if missing:
                raise _not_found(object_id)
            before = await store.get(object_id)
            if before is None:
                raise _not_found(object_id)
            specs = await self._validate_persisted_object(template_store, before)
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
            plan.begin_dml()
            await store.update_properties(object_id, properties)
            await store.insert_intrinsic_event(
                EventKind.DATA_CHANGE, after, before, after
            )
            await uow.commit()
            return after

    async def schema_change(self, object_id: UUID, target_version: int) -> Object:
        async with self._uow_factory() as uow:
            store = ObjectStore(uow.connection)
            before = await store.get(object_id)
            if before is None:
                raise _not_found(object_id)
            template_store = ObjectTemplateStore(uow.connection)
            plan, missing = await _acquire(
                uow.connection,
                (
                    _template_header(before.template_id, RowLockMode.KS),
                    _template_version(
                        before.template_id, target_version, RowLockMode.S
                    ),
                    _object_intent(object_id, RowLockMode.NKU),
                ),
            )
            if RowLockKey(RowLockClass.OBJECT, object_id) in missing:
                raise _not_found(object_id)
            if (
                RowLockKey(
                    RowLockClass.OBJECT_TEMPLATE_VERSION,
                    before.template_id,
                    target_version,
                )
                in missing
            ):
                raise _referenced(before.template_id, target_version)
            before = await store.get(object_id)
            if before is None:
                raise _not_found(object_id)
            source_schema, source_specs = await self._schema_specs(
                template_store,
                before.template_id,
                before.template_version,
            )
            try:
                canonical_source = canonicalize_properties(
                    before.properties, tuple(item.runtime for item in source_specs)
                )
            except (ObjectValidationError, PrimitiveValidationError) as error:
                raise _internal(
                    "The persisted Object runtime state is invalid."
                ) from error
            if canonical_source != before.properties:
                raise _internal("The persisted Object runtime state is not canonical.")
            if target_version <= before.template_version:
                raise _semantic(
                    ObjectValidationError("target_version", "forward_version_required")
                )
            target = await template_store.get_version(
                before.template_id, target_version
            )
            if target is None:
                raise _referenced(before.template_id, target_version)
            if target.status is not VersionStatus.PUBLISHED:
                raise _state(
                    "dependency_not_admissible",
                    "The target ObjectTemplateVersion is not PUBLISHED.",
                    {"id": str(before.template_id), "version": target_version},
                )
            target_schema, target_specs = await self._schema_specs(
                template_store, before.template_id, target_version
            )
            try:
                properties = migrate_properties(
                    before.properties, source_specs, target_specs
                )
            except SchemaChangeBlocked as error:
                raise _state(
                    "schema_change_blocked",
                    "A current property value is incompatible with the target schema.",
                    {
                        "object_id": str(object_id),
                        "target_version": target_version,
                        "blocker_type": "property",
                        "member_name": error.property_name,
                    },
                ) from error
            except (ObjectValidationError, PrimitiveValidationError) as error:
                raise _internal(
                    "The target ObjectTemplate schema is invalid."
                ) from error

            target_slots = {
                (item.declaring_template_id, item.declaration.name): item
                for item in target_schema.components
            }
            for fact in await store.list_outgoing(object_id):
                source_slot = self._slot(source_schema, fact.slot_name)
                if source_slot is None:
                    raise _internal(
                        "A persisted ownership edge has no current semantic slot."
                    )
                target_slot = target_slots.get(
                    (source_slot.declaring_template_id, source_slot.name)
                )
                child = await store.get(fact.child_object_id)
                if child is None:
                    raise _internal("A persisted ownership child is missing.")
                compatible = False
                if target_slot is not None:
                    try:
                        compatible = await template_store.is_ancestor(
                            target_slot.declaration.target_template_id,
                            child.template_id,
                        )
                    except RuntimeError as error:
                        raise _internal(
                            "The persisted ObjectTemplate lineage graph is invalid."
                        ) from error
                if target_slot is None or not compatible:
                    raise _state(
                        "schema_change_blocked",
                        "A current attachment is incompatible with the target schema.",
                        {
                            "object_id": str(object_id),
                            "target_version": target_version,
                            "blocker_type": "attachment",
                            "member_name": fact.slot_name,
                            "child_object_id": str(fact.child_object_id),
                        },
                    )
            after = Object(
                before.id,
                before.canonical_name,
                before.template_id,
                target_version,
                properties,
            )
            plan.begin_dml()
            await store.update_schema(object_id, target_version, properties)
            await store.insert_intrinsic_event(
                EventKind.SCHEMA_CHANGE, after, before, after
            )
            await uow.commit()
            return after

    async def attach(
        self, parent_object_id: UUID, slot_name: str, child_object_id: UUID
    ) -> ComponentProjection:
        async def attempt(uow: Any, attempt_number: int) -> ComponentProjection:
            del attempt_number
            store = ObjectStore(uow.connection)
            template_store = ObjectTemplateStore(uow.connection)

            async def load_candidate() -> tuple[
                Object, Object, ResolvedComponentSlot, OwnershipFact | None
            ]:
                parent = await store.get(parent_object_id)
                if parent is None:
                    raise _not_found(parent_object_id)
                schema, _ = await self._schema_specs(
                    template_store, parent.template_id, parent.template_version
                )
                slot = self._slot(schema, slot_name)
                if slot is None:
                    raise _state(
                        "ownership_slot_unavailable",
                        "The requested ownership slot is unavailable.",
                        {
                            "parent_object_id": str(parent_object_id),
                            "slot_name": slot_name,
                        },
                    )
                child = await store.get(child_object_id)
                if child is None:
                    raise _referenced_object(child_object_id)
                if child.id == parent.id:
                    raise _semantic(
                        ObjectValidationError("child_object_id", "self_attachment")
                    )
                try:
                    compatible = await template_store.is_ancestor(
                        slot.target_template_id, child.template_id
                    )
                except RuntimeError as error:
                    raise _internal(
                        "The persisted ObjectTemplate lineage graph is invalid."
                    ) from error
                if not compatible:
                    raise _semantic(
                        ObjectValidationError("child_object_id", "incompatible_lineage")
                    )
                return (
                    parent,
                    child,
                    slot,
                    await store.get_ownership(child_object_id),
                )

            _, _, _, discovered = await load_candidate()
            intents = (
                _object_intent(parent_object_id, RowLockMode.NKU),
                _object_intent(child_object_id, RowLockMode.KS),
            )
            gate = (
                AdvisoryGate.OWNERSHIP_GRAPH_WRITE_GATE if discovered is None else None
            )
            plan, _ = await _acquire(uow.connection, intents, gate=gate)
            parent, child, slot, current = await load_candidate()
            fresh_gate = (
                AdvisoryGate.OWNERSHIP_GRAPH_WRITE_GATE if current is None else None
            )
            plan.require_same_plan(intents, gate=fresh_gate)
            if current is not None:
                if (
                    current.parent_object_id == parent_object_id
                    and current.slot_name == slot_name
                ):
                    return self._component(slot, child_object_id)
                raise _state(
                    "ownership_conflict",
                    "The child Object already has a different owner.",
                    {"child_object_id": str(child_object_id)},
                )
            if await store.would_create_cycle(parent_object_id, child_object_id):
                raise _state(
                    "ownership_cycle",
                    "The requested ownership edge would introduce a cycle.",
                    {
                        "parent_object_id": str(parent_object_id),
                        "child_object_id": str(child_object_id),
                    },
                )
            fact = OwnershipFact(child_object_id, parent_object_id, slot_name)
            plan.begin_dml()
            try:
                await store.insert_ownership(fact)
            except OwnershipConflictError as error:
                raise _state(
                    "ownership_conflict",
                    "The child Object already has a different owner.",
                    {"child_object_id": str(child_object_id)},
                ) from error
            except OwnershipReferenceError as error:
                raise _referenced_object(child_object_id) from error
            await store.insert_ownership_event(
                EventKind.ATTACH_TO,
                child=child,
                parent=parent,
                slot_declaring_template_id=slot.declaring_template_id,
                slot_name=slot.name,
            )
            await uow.commit()
            return self._component(slot, child_object_id)

        try:
            return await run_semantic_uow_attempts(self._uow_factory, attempt)
        except LockPlanAttemptsExhausted as error:
            raise _internal("The ownership lock plan did not stabilize.") from error

    async def detach(
        self, parent_object_id: UUID, slot_name: str, child_object_id: UUID
    ) -> None:
        async with self._uow_factory() as uow:
            store = ObjectStore(uow.connection)
            template_store = ObjectTemplateStore(uow.connection)
            plan, missing = await _acquire(
                uow.connection,
                (_object_intent(parent_object_id, RowLockMode.NKU),),
            )
            if missing:
                raise _not_found(parent_object_id)
            parent = await store.get(parent_object_id)
            if parent is None:
                raise _not_found(parent_object_id)
            child = await store.get(child_object_id)
            if child is None:
                raise _referenced_object(child_object_id)
            current = await store.get_ownership(child_object_id)
            if current is None:
                return
            if (
                current.parent_object_id != parent_object_id
                or current.slot_name != slot_name
            ):
                raise _state(
                    "ownership_mismatch",
                    "The requested edge is not the child's current ownership fact.",
                    {"child_object_id": str(child_object_id)},
                )
            schema, _ = await self._schema_specs(
                template_store, parent.template_id, parent.template_version
            )
            slot = self._slot(schema, slot_name)
            if slot is None:
                raise _internal(
                    "A persisted ownership edge has no current semantic slot."
                )
            plan.begin_dml()
            if not await store.delete_ownership(current):
                raise _internal("The current ownership edge disappeared unexpectedly.")
            await store.insert_ownership_event(
                EventKind.DETACH_FROM,
                child=child,
                parent=parent,
                slot_declaring_template_id=slot.declaring_template_id,
                slot_name=slot.name,
            )
            await uow.commit()

    async def list_components(
        self,
        parent_object_id: UUID,
        *,
        slot_name: str | None,
        cursor: str | None,
        limit: int,
    ) -> Page[ComponentProjection]:
        filters: dict[str, JsonValue] = {"slot_name": slot_name}
        after: UUID | None = None
        if cursor is not None:
            key = decode_cursor(cursor, "object_components", filters)
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
        async with self._uow_factory.coherent_read() as uow:
            store = ObjectStore(uow.connection)
            parent = await store.get(parent_object_id)
            if parent is None:
                raise _not_found(parent_object_id)
            schema, _ = await self._schema_specs(
                ObjectTemplateStore(uow.connection),
                parent.template_id,
                parent.template_version,
            )
            facts = list(
                await store.list_components(
                    parent_object_id,
                    slot_name=slot_name,
                    after=after,
                    limit=limit + 1,
                )
            )
            projections: list[ComponentProjection] = []
            for fact in facts:
                slot = self._slot(schema, fact.slot_name)
                if slot is None:
                    raise _internal(
                        "A persisted ownership edge has no current semantic slot."
                    )
                projections.append(self._component(slot, fact.child_object_id))
        more = len(projections) > limit
        items = projections[:limit]
        next_cursor = (
            encode_cursor(
                "object_components", filters, [str(items[-1].child_object_id)]
            )
            if more
            else None
        )
        return Page(items, next_cursor)

    async def get_owner(self, child_object_id: UUID) -> OwnerProjection | None:
        async with self._uow_factory.coherent_read() as uow:
            store = ObjectStore(uow.connection)
            if await store.get(child_object_id) is None:
                raise _not_found(child_object_id)
            fact = await store.get_ownership(child_object_id)
            if fact is None:
                return None
            parent = await store.get(fact.parent_object_id)
            if parent is None:
                raise _internal("A persisted ownership parent is missing.")
            schema, _ = await self._schema_specs(
                ObjectTemplateStore(uow.connection),
                parent.template_id,
                parent.template_version,
            )
            slot = self._slot(schema, fact.slot_name)
            if slot is None:
                raise _internal(
                    "A persisted ownership edge has no current semantic slot."
                )
            return OwnerProjection(
                fact.parent_object_id, slot.declaring_template_id, slot.name
            )

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
    ) -> Page[LifecycleEvent]:
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
