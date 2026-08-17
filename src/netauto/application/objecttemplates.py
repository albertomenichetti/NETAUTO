"""Complete M1 ObjectTemplate semantic application capability."""

from dataclasses import dataclass
from typing import Any, Final, cast
from uuid import UUID, uuid4

from netauto.application.cursors import Page, decode_cursor, encode_cursor
from netauto.domain.datatypes import (
    DataTypeVersion,
    VersionStatus,
    validate_qualified_name,
)
from netauto.domain.objecttemplates import (
    CreateObjectTemplateResult,
    EffectiveSchema,
    LocalComponent,
    LocalProperty,
    ObjectTemplate,
    ObjectTemplateValidationError,
    ObjectTemplateVersion,
    ObjectTemplateVersionSummary,
    ValueMode,
    resolve_effective_schema,
    validate_local_declarations,
)
from netauto.domain.primitives import (
    JsonValue,
    PrimitiveValidationError,
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
    run_semantic_uow_attempts,
)
from netauto.persistence.objecttemplates import (
    ObjectTemplateComponentTargetReferenceError,
    ObjectTemplateDeleteReferenceError,
    ObjectTemplateQualifiedNameError,
    ObjectTemplateStore,
)
from netauto.persistence.uow import UnitOfWorkFactory

MISSING: Final = object()


@dataclass(frozen=True, slots=True)
class PropertyCandidate:
    name: str
    position: int
    datatype_id: UUID
    datatype_version: int | None
    value_mode: ValueMode
    required: bool
    migration_default: object = MISSING


@dataclass(frozen=True, slots=True)
class ComponentCandidate:
    name: str
    position: int
    target_template_id: UUID


def _not_found(template_id: UUID, version: int | None = None) -> ApplicationFailure:
    details: dict[str, JsonValue] = {
        "resource_type": "object_template"
        if version is None
        else "object_template_version",
        "id": str(template_id),
    }
    if version is not None:
        details["version"] = version
    return ApplicationFailure(
        FailureClass.NOT_FOUND,
        "resource_not_found",
        "The requested ObjectTemplate resource does not exist.",
        details,
    )


def _referenced(
    kind: str, resource_id: UUID, version: int | None = None
) -> ApplicationFailure:
    details: dict[str, JsonValue] = {"resource_type": kind, "id": str(resource_id)}
    if version is not None:
        details["version"] = version
    return ApplicationFailure(
        FailureClass.SEMANTIC_VALIDATION,
        "referenced_resource_not_found",
        "A referenced resource does not exist.",
        details,
    )


def _semantic(
    error: ObjectTemplateValidationError | PrimitiveValidationError | ValueError,
) -> ApplicationFailure:
    return ApplicationFailure(
        FailureClass.SEMANTIC_VALIDATION,
        "semantic_validation_failed",
        "The ObjectTemplate candidate is not semantically valid.",
        {
            "violations": [
                {
                    "path": getattr(error, "path", "object_template"),
                    "rule": getattr(error, "rule", str(error)),
                }
            ]
        },
    )


def _state(
    code: str, message: str, details: dict[str, JsonValue]
) -> ApplicationFailure:
    return ApplicationFailure(FailureClass.STATE_CONFLICT, code, message, details)


def _internal(message: str) -> ApplicationFailure:
    return ApplicationFailure(
        FailureClass.INTERNAL_FAILURE,
        "internal_error",
        message,
    )


def _ot_header(template_id: UUID, mode: RowLockMode) -> RowLockIntent:
    return RowLockIntent(
        RowLockKey(RowLockClass.OBJECT_TEMPLATE_HEADER, template_id), mode
    )


def _ot_version(template_id: UUID, version: int, mode: RowLockMode) -> RowLockIntent:
    return RowLockIntent(
        RowLockKey(RowLockClass.OBJECT_TEMPLATE_VERSION, template_id, version), mode
    )


def _dt_header(datatype_id: UUID, mode: RowLockMode) -> RowLockIntent:
    return RowLockIntent(RowLockKey(RowLockClass.DATA_TYPE_HEADER, datatype_id), mode)


def _dt_version(datatype_id: UUID, version: int, mode: RowLockMode) -> RowLockIntent:
    return RowLockIntent(
        RowLockKey(RowLockClass.DATA_TYPE_VERSION, datatype_id, version), mode
    )


async def _acquire(
    connection: Any,
    store: ObjectTemplateStore,
    intents: tuple[RowLockIntent, ...],
    *,
    gate: AdvisoryGate | None = None,
) -> tuple[LockPlan, tuple[RowLockKey, ...]]:
    plan = LockPlan(
        intents=intents,
        gate=gate,
        object_template_parent_by_id=await store.lineage_parents(),
    )
    missing = await acquire_lock_plan(connection, plan)
    return plan, missing


async def load_exact_effective_chain(
    store: ObjectTemplateStore,
    leaf: ObjectTemplateVersion,
    leaf_lineage: ObjectTemplate | None = None,
) -> tuple[ObjectTemplateVersion, ...]:
    """Load one definitive exact parent chain on the caller-owned connection."""
    chain = [leaf]
    current = leaf
    seen = {leaf.template_id}
    while current.parent_template_id is not None:
        parent_id = current.parent_template_id
        parent_version = current.parent_version
        if parent_version is None or parent_id in seen:
            raise RuntimeError("persisted ObjectTemplate inheritance graph is invalid")
        lineage = (
            leaf_lineage
            if leaf_lineage is not None and current.template_id == leaf.template_id
            else await store.get_lineage(current.template_id)
        )
        if lineage is None or lineage.parent_template_id != parent_id:
            raise RuntimeError(
                "persisted exact parent pin contradicts its stable lineage"
            )
        parent = await store.get_version(parent_id, parent_version)
        if parent is None:
            raise RuntimeError("persisted exact parent version is missing")
        seen.add(parent_id)
        chain.append(parent)
        current = parent
    root_lineage = (
        leaf_lineage
        if leaf_lineage is not None and current.template_id == leaf.template_id
        else await store.get_lineage(current.template_id)
    )
    if (
        root_lineage is None
        or root_lineage.parent_template_id is not None
        or current.parent_version is not None
    ):
        raise RuntimeError("persisted ObjectTemplate root is invalid")
    return tuple(reversed(chain))


async def resolve_exact_effective_schema(
    store: ObjectTemplateStore,
    leaf: ObjectTemplateVersion,
    leaf_lineage: ObjectTemplate | None = None,
) -> EffectiveSchema:
    """Resolve effective schema without opening or committing another UoW."""
    validate_local_declarations(leaf.properties, leaf.components)
    return resolve_effective_schema(
        leaf.template_id,
        leaf.version,
        await load_exact_effective_chain(store, leaf, leaf_lineage),
    )


class ObjectTemplateService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    @staticmethod
    def _require_draft(current: ObjectTemplateVersion, expected_revision: int) -> None:
        if current.status is not VersionStatus.DRAFT:
            raise _state(
                "lifecycle_state_conflict",
                "The operation requires a DRAFT ObjectTemplateVersion.",
                {"id": str(current.template_id), "version": current.version},
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

    @staticmethod
    def _require_published_dependency(
        dependency: ObjectTemplateVersion | DataTypeVersion,
        resource_id: UUID,
        version: int,
    ) -> None:
        if dependency.status is not VersionStatus.PUBLISHED:
            raise _state(
                "dependency_not_admissible",
                "The selected dependency version is not PUBLISHED.",
                {"id": str(resource_id), "version": version},
            )

    async def _resolve_parent(
        self,
        store: ObjectTemplateStore,
        lineage: ObjectTemplate,
        requested_version: int | None,
        current: ObjectTemplateVersion | None,
    ) -> tuple[UUID | None, int | None]:
        parent_id = lineage.parent_template_id
        if parent_id is None:
            if requested_version is not None:
                raise _semantic(
                    ObjectTemplateValidationError(
                        "parent_version", "root_parent_version_forbidden"
                    )
                )
            return None, None
        if (
            requested_version is not None
            and current is not None
            and current.parent_version == requested_version
        ):
            return parent_id, requested_version
        if requested_version is not None:
            parent = await store.get_version(parent_id, requested_version)
            if parent is None:
                raise _referenced(
                    "object_template_version", parent_id, requested_version
                )
            self._require_published_dependency(parent, parent_id, requested_version)
            return parent_id, requested_version
        parent_lineage = await store.get_lineage(parent_id)
        if parent_lineage is None:
            raise _referenced("object_template", parent_id)
        if parent_lineage.default_version is None:
            raise _state(
                "default_version_unavailable",
                "The selected parent ObjectTemplate has no default version.",
                {"id": str(parent_id)},
            )
        parent = await store.get_version(parent_id, parent_lineage.default_version)
        if parent is None:
            raise _internal("A persisted ObjectTemplate default target is missing.")
        self._require_published_dependency(parent, parent_id, parent.version)
        return parent_id, parent.version

    async def _resolve_properties(
        self,
        connection_store: ObjectTemplateStore,
        candidates: tuple[PropertyCandidate, ...],
        current: ObjectTemplateVersion | None,
    ) -> tuple[LocalProperty, ...]:
        datatype_store = DataTypeStore(connection_store.connection)
        current_by_name = (
            {} if current is None else {item.name: item for item in current.properties}
        )
        resolved_versions: dict[tuple[UUID, int | None], DataTypeVersion] = {}
        for candidate in sorted(
            candidates,
            key=lambda item: (
                str(item.datatype_id),
                item.datatype_version or 0,
                item.name,
            ),
        ):
            old = current_by_name.get(candidate.name)
            if (
                candidate.datatype_version is not None
                and old is not None
                and old.datatype_id == candidate.datatype_id
                and old.datatype_version == candidate.datatype_version
            ):
                existing = await datatype_store.get_version(
                    candidate.datatype_id, candidate.datatype_version
                )
                if existing is None:
                    raise _internal("A persisted DataType dependency is missing.")
                resolved_versions[
                    (candidate.datatype_id, candidate.datatype_version)
                ] = existing
                continue
            key = (candidate.datatype_id, candidate.datatype_version)
            if key in resolved_versions:
                continue
            if candidate.datatype_version is None:
                lineage = await datatype_store.get_lineage(candidate.datatype_id)
                if lineage is None:
                    raise _referenced("datatype", candidate.datatype_id)
                if lineage.default_version is None:
                    raise _state(
                        "default_version_unavailable",
                        "The selected DataType has no default version.",
                        {"id": str(candidate.datatype_id)},
                    )
                selected = await datatype_store.get_version(
                    candidate.datatype_id, lineage.default_version
                )
                if selected is None:
                    raise _internal("A persisted DataType default target is missing.")
            else:
                selected = await datatype_store.get_version(
                    candidate.datatype_id, candidate.datatype_version
                )
                if selected is None:
                    raise _referenced(
                        "datatype_version",
                        candidate.datatype_id,
                        candidate.datatype_version,
                    )
            self._require_published_dependency(
                selected, candidate.datatype_id, selected.version
            )
            resolved_versions[key] = selected

        properties: list[LocalProperty] = []
        for candidate in candidates:
            selected = resolved_versions[
                (candidate.datatype_id, candidate.datatype_version)
            ]
            raw_default = candidate.migration_default
            if candidate.required:
                if raw_default is MISSING or raw_default is None:
                    raise _semantic(
                        ObjectTemplateValidationError(
                            f"properties.{candidate.name}.migration_default",
                            "required_migration_default",
                        )
                    )
                if candidate.value_mode is ValueMode.LIST:
                    if not isinstance(raw_default, list) or not raw_default:
                        raise _semantic(
                            ObjectTemplateValidationError(
                                f"properties.{candidate.name}.migration_default",
                                "non_empty_list_required",
                            )
                        )
                    raw_items = cast(list[object], raw_default)
                    canonical: JsonValue = [
                        validate_value(
                            selected.base_type,
                            item,
                            selected.constraints,
                            f"properties.{candidate.name}.migration_default.{index}",
                        )
                        for index, item in enumerate(raw_items)
                    ]
                else:
                    canonical = validate_value(
                        selected.base_type,
                        raw_default,
                        selected.constraints,
                        f"properties.{candidate.name}.migration_default",
                    )
            else:
                if raw_default is not MISSING:
                    raise _semantic(
                        ObjectTemplateValidationError(
                            f"properties.{candidate.name}.migration_default",
                            "optional_default_must_be_absent",
                        )
                    )
                canonical = None
            properties.append(
                LocalProperty(
                    candidate.name,
                    candidate.position,
                    candidate.datatype_id,
                    selected.version,
                    candidate.value_mode,
                    candidate.required,
                    canonical,
                )
            )
        return tuple(sorted(properties, key=lambda item: item.position))

    async def _resolve_components(
        self,
        store: ObjectTemplateStore,
        candidates: tuple[ComponentCandidate, ...],
    ) -> tuple[LocalComponent, ...]:
        for target_id in sorted(
            {item.target_template_id for item in candidates}, key=str
        ):
            if await store.get_lineage(target_id) is None:
                raise _referenced("object_template", target_id)
        return tuple(
            sorted(
                (
                    LocalComponent(item.name, item.position, item.target_template_id)
                    for item in candidates
                ),
                key=lambda item: item.position,
            )
        )

    @staticmethod
    def _candidate_dependency_intents(
        *,
        lineage: ObjectTemplate,
        requested_parent_version: int | None,
        resolved: ObjectTemplateVersion,
        property_candidates: tuple[PropertyCandidate, ...],
        current: ObjectTemplateVersion | None,
    ) -> tuple[RowLockIntent, ...]:
        intents: list[RowLockIntent] = []
        old_parent = (
            None
            if current is None
            else (current.parent_template_id, current.parent_version)
        )
        new_parent = (resolved.parent_template_id, resolved.parent_version)
        if resolved.parent_template_id is not None and new_parent != old_parent:
            if resolved.parent_version is None:
                raise RuntimeError("resolved parent exact identity is incomplete")
            intents.extend(
                (
                    _ot_header(
                        resolved.parent_template_id,
                        RowLockMode.S
                        if requested_parent_version is None
                        else RowLockMode.KS,
                    ),
                    _ot_version(
                        resolved.parent_template_id,
                        resolved.parent_version,
                        RowLockMode.S,
                    ),
                )
            )

        candidates_by_name = {item.name: item for item in property_candidates}
        current_properties = (
            {} if current is None else {item.name: item for item in current.properties}
        )
        for item in resolved.properties:
            old = current_properties.get(item.name)
            if old == item:
                continue
            same_target = (
                old is not None
                and old.datatype_id == item.datatype_id
                and old.datatype_version == item.datatype_version
            )
            requested = candidates_by_name[item.name].datatype_version
            intents.extend(
                (
                    _dt_header(
                        item.datatype_id,
                        RowLockMode.KS
                        if same_target or requested is not None
                        else RowLockMode.S,
                    ),
                    _dt_version(
                        item.datatype_id,
                        item.datatype_version,
                        RowLockMode.KS if same_target else RowLockMode.S,
                    ),
                )
            )

        current_components = (
            {} if current is None else {item.name: item for item in current.components}
        )
        for item in resolved.components:
            if current_components.get(item.name) != item:
                intents.append(_ot_header(item.target_template_id, RowLockMode.KS))

        if lineage.parent_template_id != resolved.parent_template_id:
            raise RuntimeError("resolved parent contradicts stable lineage")
        return tuple(intents)

    @staticmethod
    def _clone_dependency_intents(
        source: ObjectTemplateVersion,
    ) -> tuple[RowLockIntent, ...]:
        intents: list[RowLockIntent] = []
        if source.parent_template_id is not None:
            if source.parent_version is None:
                raise RuntimeError("persisted parent exact identity is incomplete")
            intents.extend(
                (
                    _ot_header(source.parent_template_id, RowLockMode.KS),
                    _ot_version(
                        source.parent_template_id,
                        source.parent_version,
                        RowLockMode.KS,
                    ),
                )
            )
        intents.extend(
            _ot_header(item.target_template_id, RowLockMode.KS)
            for item in source.components
        )
        for item in source.properties:
            intents.extend(
                (
                    _dt_header(item.datatype_id, RowLockMode.KS),
                    _dt_version(
                        item.datatype_id, item.datatype_version, RowLockMode.KS
                    ),
                )
            )
        return tuple(intents)

    @staticmethod
    def _publish_intents(current: ObjectTemplateVersion) -> tuple[RowLockIntent, ...]:
        intents: list[RowLockIntent] = [
            _ot_header(current.template_id, RowLockMode.NKU),
            _ot_version(current.template_id, current.version, RowLockMode.NKU),
        ]
        if current.parent_template_id is not None:
            if current.parent_version is None:
                raise RuntimeError("persisted parent exact identity is incomplete")
            intents.extend(
                (
                    _ot_header(current.parent_template_id, RowLockMode.KS),
                    _ot_version(
                        current.parent_template_id,
                        current.parent_version,
                        RowLockMode.S,
                    ),
                )
            )
        for item in current.properties:
            intents.extend(
                (
                    _dt_header(item.datatype_id, RowLockMode.KS),
                    _dt_version(item.datatype_id, item.datatype_version, RowLockMode.S),
                )
            )
        return tuple(intents)

    async def _effective_chain(
        self,
        store: ObjectTemplateStore,
        leaf: ObjectTemplateVersion,
        leaf_lineage: ObjectTemplate | None = None,
    ) -> tuple[ObjectTemplateVersion, ...]:
        try:
            return await load_exact_effective_chain(store, leaf, leaf_lineage)
        except RuntimeError as error:
            raise _internal(str(error)) from error

    async def _validate_candidate(
        self,
        store: ObjectTemplateStore,
        candidate: ObjectTemplateVersion,
        *,
        history: bool,
        leaf_lineage: ObjectTemplate | None = None,
    ) -> EffectiveSchema:
        try:
            validate_local_declarations(candidate.properties, candidate.components)
            schema = resolve_effective_schema(
                candidate.template_id,
                candidate.version,
                await self._effective_chain(store, candidate, leaf_lineage),
            )
            if history:
                for item in candidate.properties:
                    previous = await store.latest_published_property(
                        candidate.template_id, item.name
                    )
                    if previous is not None:
                        if previous.datatype_id != item.datatype_id:
                            raise ObjectTemplateValidationError(
                                f"properties.{item.name}.datatype_id",
                                "property_datatype_lineage_changed",
                            )
                        if (
                            previous.value_mode is ValueMode.LIST
                            and item.value_mode is ValueMode.SCALAR
                        ):
                            raise ObjectTemplateValidationError(
                                f"properties.{item.name}.value_mode",
                                "list_to_scalar_forbidden",
                            )
                for item in candidate.components:
                    previous_component = await store.latest_published_component(
                        candidate.template_id, item.name
                    )
                    if previous_component is not None and not await store.is_ancestor(
                        item.target_template_id, previous_component.target_template_id
                    ):
                        raise ObjectTemplateValidationError(
                            f"components.{item.name}.target_template_id",
                            "component_target_not_widened",
                        )
            return schema
        except ObjectTemplateValidationError as error:
            raise _semantic(error) from error
        except RuntimeError as error:
            raise _internal(str(error)) from error

    async def create(
        self,
        namespace: str,
        name: str,
        abstract: bool,
        description: str | None,
        parent_template_id: UUID | None,
        parent_version: int | None,
        properties: tuple[PropertyCandidate, ...],
        components: tuple[ComponentCandidate, ...],
    ) -> CreateObjectTemplateResult:
        try:
            validate_qualified_name(namespace, name, public=True)
        except ValueError as error:
            raise _semantic(error) from error
        template_id = uuid4()
        try:

            async def attempt(
                uow: Any, attempt_number: int
            ) -> CreateObjectTemplateResult:
                del attempt_number
                store = ObjectTemplateStore(uow.connection)
                if parent_template_id is None:
                    if parent_version is not None:
                        raise _semantic(
                            ObjectTemplateValidationError(
                                "parent_version", "parent_template_required"
                            )
                        )
                    resolved_parent = (None, None)
                else:
                    parent_lineage = await store.get_lineage(parent_template_id)
                    if parent_lineage is None:
                        raise _referenced("object_template", parent_template_id)
                    temporary = ObjectTemplate(
                        template_id,
                        namespace,
                        name,
                        description,
                        abstract,
                        parent_template_id,
                        None,
                    )
                    resolved_parent = await self._resolve_parent(
                        store, temporary, parent_version, None
                    )
                lineage = ObjectTemplate(
                    template_id,
                    namespace,
                    name,
                    description,
                    abstract,
                    resolved_parent[0],
                    None,
                )
                local_properties = await self._resolve_properties(
                    store, properties, None
                )
                local_components = await self._resolve_components(store, components)
                version = ObjectTemplateVersion(
                    template_id,
                    1,
                    1,
                    VersionStatus.DRAFT,
                    *resolved_parent,
                    local_properties,
                    local_components,
                )
                intents = self._candidate_dependency_intents(
                    lineage=lineage,
                    requested_parent_version=parent_version,
                    resolved=version,
                    property_candidates=properties,
                    current=None,
                )
                plan, _ = await _acquire(uow.connection, store, intents)

                resolved_parent = await self._resolve_parent(
                    store, lineage, parent_version, None
                )
                local_properties = await self._resolve_properties(
                    store, properties, None
                )
                local_components = await self._resolve_components(store, components)
                version = ObjectTemplateVersion(
                    template_id,
                    1,
                    1,
                    VersionStatus.DRAFT,
                    *resolved_parent,
                    local_properties,
                    local_components,
                )
                plan.require_same_plan(
                    self._candidate_dependency_intents(
                        lineage=lineage,
                        requested_parent_version=parent_version,
                        resolved=version,
                        property_candidates=properties,
                        current=None,
                    )
                )
                await self._validate_candidate(
                    store, version, history=False, leaf_lineage=lineage
                )
                plan.begin_dml()
                await store.create(lineage, version)
                await uow.commit()
                return CreateObjectTemplateResult(lineage, version)

            return await run_semantic_uow_attempts(self._uow_factory, attempt)
        except LockPlanAttemptsExhausted as error:
            raise _internal(
                "The ObjectTemplate lock plan did not stabilize."
            ) from error
        except ObjectTemplateQualifiedNameError as error:
            raise _state(
                "qualified_name_conflict",
                "The qualified ObjectTemplate name is already in use.",
                {"namespace": namespace, "name": name},
            ) from error
        except ObjectTemplateComponentTargetReferenceError as error:
            raise _referenced("object_template", error.target_template_id) from error

    async def create_next(
        self, template_id: UUID, source_version: int
    ) -> ObjectTemplateVersion:
        async def attempt(uow: Any, attempt_number: int) -> ObjectTemplateVersion:
            del attempt_number
            store = ObjectTemplateStore(uow.connection)
            source = await store.get_version(template_id, source_version)
            if await store.get_lineage(template_id) is None:
                raise _not_found(template_id)
            if source is None:
                raise _referenced(
                    "object_template_version", template_id, source_version
                )
            if source.status not in {VersionStatus.PUBLISHED, VersionStatus.DEPRECATED}:
                raise _state(
                    "version_source_conflict",
                    "The selected version is not eligible as a create-next source.",
                    {"id": str(template_id), "source_version": source_version},
                )
            intents = (
                *self._clone_dependency_intents(source),
                _ot_header(template_id, RowLockMode.NKU),
                _ot_version(template_id, source_version, RowLockMode.KS),
            )
            plan, missing = await _acquire(uow.connection, store, intents)
            if RowLockKey(RowLockClass.OBJECT_TEMPLATE_HEADER, template_id) in missing:
                raise _not_found(template_id)
            source = await store.get_version(template_id, source_version)
            if source is None:
                raise _referenced(
                    "object_template_version", template_id, source_version
                )
            if source.status not in {
                VersionStatus.PUBLISHED,
                VersionStatus.DEPRECATED,
            }:
                raise _state(
                    "version_source_conflict",
                    "The selected version is not eligible as a create-next source.",
                    {"id": str(template_id), "source_version": source_version},
                )
            plan.require_same_plan(
                (
                    *self._clone_dependency_intents(source),
                    _ot_header(template_id, RowLockMode.NKU),
                    _ot_version(template_id, source_version, RowLockMode.KS),
                )
            )
            created = ObjectTemplateVersion(
                template_id,
                await store.next_version(template_id),
                1,
                VersionStatus.DRAFT,
                source.parent_template_id,
                source.parent_version,
                source.properties,
                source.components,
            )
            plan.begin_dml()
            await store.insert_version(created)
            await uow.commit()
            return created

        try:
            return await run_semantic_uow_attempts(self._uow_factory, attempt)
        except LockPlanAttemptsExhausted as error:
            raise _internal(
                "The ObjectTemplate lock plan did not stabilize."
            ) from error

    async def revise(
        self,
        template_id: UUID,
        version: int,
        expected_revision: int,
        parent_version: int | None,
        properties: tuple[PropertyCandidate, ...],
        components: tuple[ComponentCandidate, ...],
    ) -> ObjectTemplateVersion:
        async def attempt(uow: Any, attempt_number: int) -> ObjectTemplateVersion:
            del attempt_number
            store = ObjectTemplateStore(uow.connection)
            lineage = await store.get_lineage(template_id)
            current = await store.get_version(template_id, version)
            if lineage is None or current is None:
                raise _not_found(template_id, version)
            self._require_draft(current, expected_revision)
            resolved_parent = await self._resolve_parent(
                store, lineage, parent_version, current
            )
            local_properties = await self._resolve_properties(
                store, properties, current
            )
            local_components = await self._resolve_components(store, components)
            candidate = ObjectTemplateVersion(
                template_id,
                version,
                current.revision + 1,
                VersionStatus.DRAFT,
                *resolved_parent,
                local_properties,
                local_components,
            )
            intents = (
                *self._candidate_dependency_intents(
                    lineage=lineage,
                    requested_parent_version=parent_version,
                    resolved=candidate,
                    property_candidates=properties,
                    current=current,
                ),
                _ot_header(template_id, RowLockMode.KS),
                _ot_version(template_id, version, RowLockMode.NKU),
            )
            plan, missing = await _acquire(uow.connection, store, intents)
            if RowLockKey(RowLockClass.OBJECT_TEMPLATE_HEADER, template_id) in missing:
                raise _not_found(template_id)
            if (
                RowLockKey(RowLockClass.OBJECT_TEMPLATE_VERSION, template_id, version)
                in missing
            ):
                raise _not_found(template_id, version)

            lineage = await store.get_lineage(template_id)
            current = await store.get_version(template_id, version)
            if lineage is None or current is None:
                raise _not_found(template_id, version)
            self._require_draft(current, expected_revision)
            resolved_parent = await self._resolve_parent(
                store, lineage, parent_version, current
            )
            local_properties = await self._resolve_properties(
                store, properties, current
            )
            local_components = await self._resolve_components(store, components)
            candidate = ObjectTemplateVersion(
                template_id,
                version,
                current.revision + 1,
                VersionStatus.DRAFT,
                *resolved_parent,
                local_properties,
                local_components,
            )
            plan.require_same_plan(
                (
                    *self._candidate_dependency_intents(
                        lineage=lineage,
                        requested_parent_version=parent_version,
                        resolved=candidate,
                        property_candidates=properties,
                        current=current,
                    ),
                    _ot_header(template_id, RowLockMode.KS),
                    _ot_version(template_id, version, RowLockMode.NKU),
                )
            )
            await self._validate_candidate(store, candidate, history=True)
            plan.begin_dml()
            try:
                await store.replace_candidate(candidate)
            except ObjectTemplateComponentTargetReferenceError as error:
                raise _referenced(
                    "object_template", error.target_template_id
                ) from error
            revised = await store.get_version(template_id, version)
            if revised is None:
                raise _internal("The revised ObjectTemplateVersion disappeared.")
            await uow.commit()
            return revised

        try:
            return await run_semantic_uow_attempts(self._uow_factory, attempt)
        except LockPlanAttemptsExhausted as error:
            raise _internal(
                "The ObjectTemplate lock plan did not stabilize."
            ) from error

    async def publish(
        self, template_id: UUID, version: int, expected_revision: int
    ) -> ObjectTemplateVersion:
        async def attempt(uow: Any, attempt_number: int) -> ObjectTemplateVersion:
            del attempt_number
            store = ObjectTemplateStore(uow.connection)
            lineage = await store.get_lineage(template_id)
            current = await store.get_version(template_id, version)
            if lineage is None or current is None:
                raise _not_found(template_id, version)
            self._require_draft(current, expected_revision)
            plan, missing = await _acquire(
                uow.connection, store, self._publish_intents(current)
            )
            if RowLockKey(RowLockClass.OBJECT_TEMPLATE_HEADER, template_id) in missing:
                raise _not_found(template_id)
            if (
                RowLockKey(RowLockClass.OBJECT_TEMPLATE_VERSION, template_id, version)
                in missing
            ):
                raise _not_found(template_id, version)
            lineage = await store.get_lineage(template_id)
            current = await store.get_version(template_id, version)
            if lineage is None or current is None:
                raise _not_found(template_id, version)
            self._require_draft(current, expected_revision)
            plan.require_same_plan(self._publish_intents(current))
            await self._validate_candidate(store, current, history=True)
            datatype_store = DataTypeStore(uow.connection)
            for item in current.properties:
                dependency = await datatype_store.get_version(
                    item.datatype_id, item.datatype_version
                )
                if dependency is None:
                    raise _internal("A persisted direct dependency is missing.")
                self._require_published_dependency(
                    dependency, item.datatype_id, item.datatype_version
                )
            if current.parent_template_id is not None:
                if current.parent_version is None:
                    raise _internal("A persisted direct dependency is incomplete.")
                parent = await store.get_version(
                    current.parent_template_id, current.parent_version
                )
                if parent is None:
                    raise _internal("A persisted direct dependency is missing.")
                self._require_published_dependency(
                    parent, current.parent_template_id, current.parent_version
                )
            plan.begin_dml()
            await store.set_status(template_id, version, VersionStatus.PUBLISHED)
            if lineage.default_version is None:
                await store.set_default(template_id, version)
            published = await store.get_version(template_id, version)
            if published is None:
                raise _internal("The published ObjectTemplateVersion disappeared.")
            await uow.commit()
            return published

        try:
            return await run_semantic_uow_attempts(self._uow_factory, attempt)
        except LockPlanAttemptsExhausted as error:
            raise _internal(
                "The ObjectTemplate lock plan did not stabilize."
            ) from error

    async def set_default(self, template_id: UUID, version: int) -> ObjectTemplate:
        async with self._uow_factory() as uow:
            store = ObjectTemplateStore(uow.connection)
            plan, missing = await _acquire(
                uow.connection,
                store,
                (
                    _ot_header(template_id, RowLockMode.NKU),
                    _ot_version(template_id, version, RowLockMode.S),
                ),
            )
            if RowLockKey(RowLockClass.OBJECT_TEMPLATE_HEADER, template_id) in missing:
                raise _not_found(template_id)
            target = await store.get_version(template_id, version)
            if target is None:
                raise _referenced("object_template_version", template_id, version)
            self._require_published_dependency(target, template_id, version)
            plan.begin_dml()
            lineage = await store.set_default(template_id, version)
            await uow.commit()
            return lineage

    async def clear_default(self, template_id: UUID) -> ObjectTemplate:
        async with self._uow_factory() as uow:
            store = ObjectTemplateStore(uow.connection)
            plan, missing = await _acquire(
                uow.connection,
                store,
                (_ot_header(template_id, RowLockMode.NKU),),
            )
            if missing:
                raise _not_found(template_id)
            plan.begin_dml()
            lineage = await store.set_default(template_id, None)
            await uow.commit()
            return lineage

    async def deprecate(self, template_id: UUID, version: int) -> ObjectTemplateVersion:
        async with self._uow_factory() as uow:
            store = ObjectTemplateStore(uow.connection)
            plan, missing = await _acquire(
                uow.connection,
                store,
                (
                    _ot_header(template_id, RowLockMode.S),
                    _ot_version(template_id, version, RowLockMode.NKU),
                ),
            )
            if RowLockKey(RowLockClass.OBJECT_TEMPLATE_HEADER, template_id) in missing:
                raise _not_found(template_id)
            if (
                RowLockKey(RowLockClass.OBJECT_TEMPLATE_VERSION, template_id, version)
                in missing
            ):
                raise _not_found(template_id, version)
            lineage = await store.get_lineage(template_id)
            current = await store.get_version(template_id, version)
            if lineage is None or current is None:
                raise _not_found(template_id, version)
            if current.status is not VersionStatus.PUBLISHED:
                raise _state(
                    "lifecycle_state_conflict",
                    "Only a PUBLISHED ObjectTemplateVersion can be deprecated.",
                    {"id": str(template_id), "version": version},
                )
            if lineage.default_version == version:
                raise _state(
                    "default_version_conflict",
                    "The current default version cannot be deprecated.",
                    {"id": str(template_id), "version": version},
                )
            if await store.has_active_child(template_id, version):
                raise _state(
                    "active_dependency_conflict",
                    "A PUBLISHED child ObjectTemplateVersion depends on this version.",
                    {"id": str(template_id), "version": version},
                )
            plan.begin_dml()
            await store.set_status(template_id, version, VersionStatus.DEPRECATED)
            deprecated = await store.get_version(template_id, version)
            if deprecated is None:
                raise _internal("The deprecated ObjectTemplateVersion disappeared.")
            await uow.commit()
            return deprecated

    async def delete_draft(
        self, template_id: UUID, version: int, expected_revision: int
    ) -> None:
        async with self._uow_factory() as uow:
            store = ObjectTemplateStore(uow.connection)
            plan, missing = await _acquire(
                uow.connection,
                store,
                (
                    _ot_header(template_id, RowLockMode.NKU),
                    _ot_version(template_id, version, RowLockMode.U),
                ),
            )
            if RowLockKey(RowLockClass.OBJECT_TEMPLATE_HEADER, template_id) in missing:
                raise _not_found(template_id)
            if (
                RowLockKey(RowLockClass.OBJECT_TEMPLATE_VERSION, template_id, version)
                in missing
            ):
                raise _not_found(template_id, version)
            current = await store.get_version(template_id, version)
            if current is None:
                raise _not_found(template_id, version)
            self._require_draft(current, expected_revision)
            plan.begin_dml()
            await store.delete_draft(template_id, version)
            await uow.commit()

    async def delete_lineage(self, template_id: UUID) -> None:
        async with self._uow_factory() as uow:
            store = ObjectTemplateStore(uow.connection)
            plan, missing = await _acquire(
                uow.connection,
                store,
                (_ot_header(template_id, RowLockMode.U),),
                gate=AdvisoryGate.MODEL_ROOT_DELETE_GATE,
            )
            if missing:
                raise _not_found(template_id)
            blockers = await store.external_reference_counts(template_id)
            blockers = {key: value for key, value in blockers.items() if value}
            if blockers:
                raise _state(
                    "delete_blocked",
                    "Current references prevent ObjectTemplate deletion.",
                    {
                        "resource_type": "object_template",
                        "id": str(template_id),
                        "blockers": [
                            {"type": key, "count": value}
                            for key, value in sorted(blockers.items())
                        ],
                    },
                )
            plan.begin_dml()
            try:
                await store.delete_lineage(template_id)
            except ObjectTemplateDeleteReferenceError as error:
                raise _state(
                    "delete_blocked",
                    "A concurrent current reference prevented ObjectTemplate deletion.",
                    {
                        "resource_type": "object_template",
                        "id": str(template_id),
                        "blockers": [{"type": error.blocker_type, "count": 1}],
                    },
                ) from error
            await uow.commit()

    async def set_description(
        self, template_id: UUID, description: str | None
    ) -> ObjectTemplate:
        async with self._uow_factory() as uow:
            store = ObjectTemplateStore(uow.connection)
            plan, missing = await _acquire(
                uow.connection,
                store,
                (_ot_header(template_id, RowLockMode.NKU),),
            )
            if missing:
                raise _not_found(template_id)
            plan.begin_dml()
            lineage = await store.set_description(template_id, description)
            if lineage is None:
                raise _not_found(template_id)
            await uow.commit()
            return lineage

    async def get_lineage(self, template_id: UUID) -> ObjectTemplate:
        async with self._uow_factory() as uow:
            lineage = await ObjectTemplateStore(uow.connection).get_lineage(template_id)
            if lineage is None:
                raise _not_found(template_id)
            return lineage

    async def get_version(
        self, template_id: UUID, version: int
    ) -> ObjectTemplateVersion:
        async with self._uow_factory.coherent_read() as uow:
            current = await ObjectTemplateStore(uow.connection).get_version(
                template_id, version
            )
            if current is None:
                raise _not_found(template_id, version)
            return current

    async def get_effective_schema(
        self, template_id: UUID, version: int
    ) -> EffectiveSchema:
        async with self._uow_factory.coherent_read() as uow:
            store = ObjectTemplateStore(uow.connection)
            current = await store.get_version(template_id, version)
            if current is None:
                raise _not_found(template_id, version)
            try:
                return await resolve_exact_effective_schema(store, current)
            except ObjectTemplateValidationError as error:
                raise _internal(
                    "The persisted ObjectTemplate effective schema is invalid."
                ) from error
            except RuntimeError as error:
                raise _internal(str(error)) from error

    async def list_lineages(
        self,
        *,
        namespace: str | None,
        name: str | None,
        abstract: bool | None,
        parent_template_id: UUID | None,
        parent_filter_set: bool,
        cursor: str | None,
        limit: int,
    ) -> Page[ObjectTemplate]:
        filters: dict[str, JsonValue] = {
            "namespace": namespace,
            "name": name,
            "abstract": abstract,
            "parent_template_id": None
            if not parent_filter_set
            else str(parent_template_id)
            if parent_template_id is not None
            else None,
            "parent_filter_set": parent_filter_set,
        }
        after: tuple[str, str] | None = None
        if cursor is not None:
            key = decode_cursor(cursor, "object_templates", filters)
            if len(key) != 2 or not all(isinstance(item, str) for item in key):
                raise ApplicationFailure(
                    FailureClass.INVALID_REQUEST,
                    "invalid_cursor",
                    "The cursor is malformed or incompatible with this query.",
                )
            after = cast(tuple[str, str], (key[0], key[1]))
        async with self._uow_factory() as uow:
            rows = list(
                await ObjectTemplateStore(uow.connection).list_lineages(
                    namespace=namespace,
                    name=name,
                    abstract=abstract,
                    parent_template_id=parent_template_id,
                    parent_filter_set=parent_filter_set,
                    after=after,
                    limit=limit + 1,
                )
            )
        more = len(rows) > limit
        items = rows[:limit]
        next_cursor = (
            encode_cursor(
                "object_templates", filters, [items[-1].namespace, items[-1].name]
            )
            if more
            else None
        )
        return Page(items, next_cursor)

    async def list_versions(
        self,
        template_id: UUID,
        *,
        status: VersionStatus | None,
        cursor: str | None,
        limit: int,
    ) -> Page[ObjectTemplateVersionSummary]:
        filters: dict[str, JsonValue] = {
            "template_id": str(template_id),
            "status": None if status is None else status.value,
        }
        after: int | None = None
        if cursor is not None:
            key = decode_cursor(cursor, "object_template_versions", filters)
            if len(key) != 1 or isinstance(key[0], bool) or not isinstance(key[0], int):
                raise ApplicationFailure(
                    FailureClass.INVALID_REQUEST,
                    "invalid_cursor",
                    "The cursor is malformed or incompatible with this query.",
                )
            after = key[0]
        async with self._uow_factory() as uow:
            store = ObjectTemplateStore(uow.connection)
            if await store.get_lineage(template_id) is None:
                raise _not_found(template_id)
            rows = list(
                await store.list_versions(
                    template_id, status=status, after=after, limit=limit + 1
                )
            )
        more = len(rows) > limit
        items = rows[:limit]
        next_cursor = (
            encode_cursor("object_template_versions", filters, [items[-1].version])
            if more
            else None
        )
        return Page(items, next_cursor)
