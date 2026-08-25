"""RelationshipDefinition model-plane application capability."""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from netauto.application.cursors import Page, decode_cursor, encode_cursor
from netauto.domain.datatypes import DataTypeVersion, VersionStatus
from netauto.domain.primitives import JsonValue
from netauto.domain.relationships import (
    CreateRelationshipDefinitionResult,
    RelationshipCapability,
    RelationshipDefinition,
    RelationshipDefinitionProperty,
    RelationshipDefinitionValidationError,
    RelationshipDefinitionVersion,
    RelationshipDefinitionVersionSummary,
    RelationshipPerspective,
    RelationshipPropertyCandidate,
    ResolutionRename,
    first_conflict,
    new_non_symmetric_definition,
    new_symmetric_definition,
    rename_non_symmetric,
    rename_symmetric,
    semantic_signature,
    validate_definition,
    validate_lineage_graph,
    validate_relationship_definition_version,
    validate_relationship_property_history,
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
from netauto.persistence.relationships import (
    RelationshipDefinitionDeleteReferenceError,
    RelationshipDefinitionStore,
    RelationshipDefinitionVersionStore,
    RelationshipEndpointReferenceError,
)
from netauto.persistence.uow import UnitOfWorkFactory


def _not_found(definition_id: UUID) -> ApplicationFailure:
    return ApplicationFailure(
        FailureClass.NOT_FOUND,
        "resource_not_found",
        "The requested RelationshipDefinition does not exist.",
        {"resource_type": "relationship_definition", "id": str(definition_id)},
    )


def _template_not_found(template_id: UUID) -> ApplicationFailure:
    return ApplicationFailure(
        FailureClass.NOT_FOUND,
        "resource_not_found",
        "The requested ObjectTemplate does not exist.",
        {"resource_type": "object_template", "id": str(template_id)},
    )


def _version_not_found(definition_id: UUID, version: int) -> ApplicationFailure:
    return ApplicationFailure(
        FailureClass.NOT_FOUND,
        "resource_not_found",
        "The requested RelationshipDefinitionVersion does not exist.",
        {
            "resource_type": "relationship_definition_version",
            "id": str(definition_id),
            "version": version,
        },
    )


def _referenced(
    resource_type: str, resource_id: UUID, version: int | None = None
) -> ApplicationFailure:
    details: dict[str, JsonValue] = {
        "resource_type": resource_type,
        "id": str(resource_id),
    }
    if version is not None:
        details["version"] = version
    return ApplicationFailure(
        FailureClass.SEMANTIC_VALIDATION,
        "referenced_resource_not_found",
        "A referenced command operand does not exist.",
        details,
    )


def _referenced_template(template_id: UUID | None = None) -> ApplicationFailure:
    details: dict[str, JsonValue] = {"resource_type": "object_template"}
    if template_id is not None:
        details["id"] = str(template_id)
    return ApplicationFailure(
        FailureClass.SEMANTIC_VALIDATION,
        "referenced_resource_not_found",
        "A referenced ObjectTemplate lineage does not exist.",
        details,
    )


def _semantic(error: RelationshipDefinitionValidationError) -> ApplicationFailure:
    return ApplicationFailure(
        FailureClass.SEMANTIC_VALIDATION,
        "semantic_validation_failed",
        "The RelationshipDefinition candidate is not semantically valid.",
        {"violations": [{"path": error.path, "rule": error.rule}]},
    )


def _state(
    code: str, message: str, details: dict[str, JsonValue]
) -> ApplicationFailure:
    return ApplicationFailure(FailureClass.STATE_CONFLICT, code, message, details)


def _internal(message: str) -> ApplicationFailure:
    return ApplicationFailure(FailureClass.INTERNAL_FAILURE, "internal_error", message)


def _validate_persisted(value: RelationshipDefinition) -> None:
    try:
        validate_definition(value)
    except RelationshipDefinitionValidationError as error:
        raise _internal(
            "A persisted RelationshipDefinition aggregate is invalid."
        ) from error


def _definition_intent(definition_id: UUID, mode: RowLockMode) -> RowLockIntent:
    return RowLockIntent(
        RowLockKey(RowLockClass.RELATIONSHIP_DEFINITION_HEADER, definition_id),
        mode,
    )


def _template_intent(template_id: UUID) -> RowLockIntent:
    return RowLockIntent(
        RowLockKey(RowLockClass.OBJECT_TEMPLATE_HEADER, template_id), RowLockMode.KS
    )


def _definition_version_intent(
    definition_id: UUID, version: int, mode: RowLockMode
) -> RowLockIntent:
    return RowLockIntent(
        RowLockKey(
            RowLockClass.RELATIONSHIP_DEFINITION_VERSION,
            definition_id,
            version,
        ),
        mode,
    )


def _datatype_header_intent(datatype_id: UUID, mode: RowLockMode) -> RowLockIntent:
    return RowLockIntent(RowLockKey(RowLockClass.DATA_TYPE_HEADER, datatype_id), mode)


def _datatype_version_intent(
    datatype_id: UUID, version: int, mode: RowLockMode
) -> RowLockIntent:
    return RowLockIntent(
        RowLockKey(RowLockClass.DATA_TYPE_VERSION, datatype_id, version), mode
    )


@dataclass(frozen=True, slots=True)
class _PropertyDependencySelection:
    property_name: str
    property_position: int
    datatype_id: UUID
    explicit: bool
    requested_version: int | None
    selected_version: int
    current_version: int | None


@dataclass(frozen=True, slots=True)
class _ResolvedPropertyCandidate:
    properties: tuple[RelationshipDefinitionProperty, ...]
    dependencies: tuple[_PropertyDependencySelection, ...]


async def _acquire(
    connection: Any,
    intents: tuple[RowLockIntent, ...],
    gate: AdvisoryGate | None = None,
) -> tuple[LockPlan, tuple[RowLockKey, ...]]:
    plan = await prepare_lock_plan(connection, intents=intents, gate=gate)
    return plan, await acquire_lock_plan(connection, plan)


class RelationshipDefinitionService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    @staticmethod
    def _require_draft(
        current: RelationshipDefinitionVersion, expected_revision: int
    ) -> None:
        if current.status is not VersionStatus.DRAFT:
            raise _state(
                "lifecycle_state_conflict",
                "The operation requires a DRAFT RelationshipDefinitionVersion.",
                {
                    "id": str(current.relationship_definition_id),
                    "version": current.version,
                },
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
    def _require_published(
        dependency: DataTypeVersion | RelationshipDefinitionVersion,
        resource_id: UUID,
        version: int,
    ) -> None:
        if dependency.status is not VersionStatus.PUBLISHED:
            raise _state(
                "dependency_not_admissible",
                "The selected exact dependency is not PUBLISHED.",
                {"id": str(resource_id), "version": version},
            )

    async def _resolve_properties(
        self,
        store: RelationshipDefinitionVersionStore,
        candidates: tuple[RelationshipPropertyCandidate, ...],
        current: RelationshipDefinitionVersion | None,
    ) -> _ResolvedPropertyCandidate:
        datatype_store = DataTypeStore(store.connection)
        current_by_name = (
            {} if current is None else {item.name: item for item in current.properties}
        )
        ordered_candidates = tuple(
            sorted(
                candidates,
                key=lambda item: (
                    item.datatype_id.int,
                    item.datatype_version or 0,
                    item.name,
                ),
            )
        )
        implicit_lineages = await datatype_store.get_lineages(
            tuple(
                candidate.datatype_id
                for candidate in ordered_candidates
                if candidate.datatype_version is None
            )
        )
        selected_keys: dict[tuple[UUID, int | None], tuple[UUID, int]] = {}
        for candidate in ordered_candidates:
            if candidate.datatype_version is None:
                lineage = implicit_lineages.get(candidate.datatype_id)
                if lineage is None:
                    raise _referenced("datatype", candidate.datatype_id)
                if lineage.default_version is None:
                    raise _state(
                        "default_version_unavailable",
                        "The selected DataType has no default version.",
                        {"id": str(candidate.datatype_id)},
                    )
                selected_keys[(candidate.datatype_id, None)] = (
                    candidate.datatype_id,
                    lineage.default_version,
                )
            else:
                selected_keys[(candidate.datatype_id, candidate.datatype_version)] = (
                    candidate.datatype_id,
                    candidate.datatype_version,
                )
        exact_versions = await datatype_store.get_versions(
            tuple(selected_keys.values())
        )
        resolved: dict[tuple[UUID, int | None], DataTypeVersion] = {}
        dependencies: list[_PropertyDependencySelection] = []
        for candidate in ordered_candidates:
            requested_key = (candidate.datatype_id, candidate.datatype_version)
            selected_key = selected_keys[requested_key]
            dependency = exact_versions.get(selected_key)
            old = current_by_name.get(candidate.name)
            same_explicit_target = (
                candidate.datatype_version is not None
                and old is not None
                and old.datatype_id == candidate.datatype_id
                and old.datatype_version == candidate.datatype_version
            )
            if dependency is None:
                if candidate.datatype_version is None:
                    raise _internal("A persisted DataType default target is missing.")
                if same_explicit_target:
                    raise _internal("A persisted DataType dependency is missing.")
                raise _referenced(
                    "datatype_version",
                    candidate.datatype_id,
                    candidate.datatype_version,
                )
            if not same_explicit_target:
                self._require_published(
                    dependency, candidate.datatype_id, dependency.version
                )
            resolved[requested_key] = dependency
            dependencies.append(
                _PropertyDependencySelection(
                    property_name=candidate.name,
                    property_position=candidate.position,
                    datatype_id=candidate.datatype_id,
                    explicit=candidate.datatype_version is not None,
                    requested_version=candidate.datatype_version,
                    selected_version=dependency.version,
                    current_version=(
                        old.datatype_version
                        if old is not None and old.datatype_id == candidate.datatype_id
                        else None
                    ),
                )
            )
        properties = tuple(
            sorted(
                (
                    RelationshipDefinitionProperty(
                        item.name,
                        item.position,
                        item.datatype_id,
                        resolved[(item.datatype_id, item.datatype_version)].version,
                        item.value_mode,
                    )
                    for item in candidates
                ),
                key=lambda item: item.position,
            )
        )
        candidate_version = RelationshipDefinitionVersion(
            UUID(int=0), 1, 1, VersionStatus.DRAFT, properties
        )
        try:
            validate_relationship_definition_version(candidate_version)
        except RelationshipDefinitionValidationError as error:
            raise _semantic(error) from error
        return _ResolvedPropertyCandidate(
            properties=properties,
            dependencies=tuple(
                sorted(
                    dependencies,
                    key=lambda item: (
                        item.property_position,
                        item.property_name,
                        item.datatype_id.int,
                    ),
                )
            ),
        )

    @staticmethod
    def _candidate_dependency_intents(
        resolved: _ResolvedPropertyCandidate,
        current: RelationshipDefinitionVersion | None,
    ) -> tuple[RowLockIntent, ...]:
        current_by_name = (
            {} if current is None else {item.name: item for item in current.properties}
        )
        resolved_by_name = {item.name: item for item in resolved.properties}
        intents: list[RowLockIntent] = []
        for selection in resolved.dependencies:
            item = resolved_by_name[selection.property_name]
            old = current_by_name.get(selection.property_name)
            if old == item:
                continue
            same_target = selection.current_version == item.datatype_version
            intents.extend(
                (
                    _datatype_header_intent(
                        item.datatype_id,
                        RowLockMode.KS
                        if same_target or selection.explicit
                        else RowLockMode.S,
                    ),
                    _datatype_version_intent(
                        item.datatype_id,
                        item.datatype_version,
                        RowLockMode.KS if same_target else RowLockMode.S,
                    ),
                )
            )
        return tuple(intents)

    @staticmethod
    def _missing_dependency_failure(
        missing: tuple[RowLockKey, ...],
        resolved: _ResolvedPropertyCandidate,
    ) -> ApplicationFailure | None:
        missing_headers = {
            key.resource_id
            for key in missing
            if key.row_class is RowLockClass.DATA_TYPE_HEADER
        }
        missing_versions = {
            (key.resource_id, key.version)
            for key in missing
            if key.row_class is RowLockClass.DATA_TYPE_VERSION
        }
        for selection in resolved.dependencies:
            header_missing = selection.datatype_id in missing_headers
            version_missing = (
                selection.datatype_id,
                selection.selected_version,
            ) in missing_versions
            if not header_missing and not version_missing:
                continue
            if selection.explicit:
                requested_version = selection.requested_version
                if requested_version is None:
                    raise RuntimeError("explicit DataTypeVersion selector is missing")
                return _referenced(
                    "datatype_version", selection.datatype_id, requested_version
                )
            if header_missing:
                return _referenced("datatype", selection.datatype_id)
            return _internal("A persisted DataType default target is missing.")
        return None

    @staticmethod
    def _clone_dependency_intents(
        source: RelationshipDefinitionVersion,
    ) -> tuple[RowLockIntent, ...]:
        return tuple(
            intent
            for item in source.properties
            for intent in (
                _datatype_header_intent(item.datatype_id, RowLockMode.KS),
                _datatype_version_intent(
                    item.datatype_id, item.datatype_version, RowLockMode.KS
                ),
            )
        )

    @staticmethod
    def _publish_intents(
        current: RelationshipDefinitionVersion,
    ) -> tuple[RowLockIntent, ...]:
        return (
            *(
                intent
                for item in current.properties
                for intent in (
                    _datatype_header_intent(item.datatype_id, RowLockMode.KS),
                    _datatype_version_intent(
                        item.datatype_id, item.datatype_version, RowLockMode.S
                    ),
                )
            ),
            _definition_intent(current.relationship_definition_id, RowLockMode.NKU),
            _definition_version_intent(
                current.relationship_definition_id,
                current.version,
                RowLockMode.NKU,
            ),
        )

    async def _validate_version_candidate(
        self,
        store: RelationshipDefinitionVersionStore,
        candidate: RelationshipDefinitionVersion,
    ) -> None:
        try:
            validate_relationship_definition_version(candidate)
            validate_relationship_property_history(
                candidate,
                await store.published_history(candidate.relationship_definition_id),
            )
        except RelationshipDefinitionValidationError as error:
            raise _semantic(error) from error

    async def _certify(
        self,
        store: RelationshipDefinitionStore,
        candidate: RelationshipDefinition,
        *,
        create_operands: bool,
    ) -> None:
        certified = await store.certified_set()
        parent_by_id = await store.lineage_parents()
        try:
            validate_lineage_graph(parent_by_id)
        except RelationshipDefinitionValidationError as error:
            raise _internal(
                "The persisted ObjectTemplate ancestry graph is invalid."
            ) from error
        for existing in certified:
            _validate_persisted(existing)
            for resolution in existing.resolutions:
                if (
                    resolution.from_template_id not in parent_by_id
                    or resolution.to_template_id not in parent_by_id
                ):
                    raise _internal(
                        "A persisted RelationshipDefinition endpoint is missing."
                    )

        for resolution in candidate.resolutions:
            for template_id in (
                resolution.from_template_id,
                resolution.to_template_id,
            ):
                if template_id not in parent_by_id:
                    if create_operands:
                        raise _referenced_template(template_id)
                    raise _internal(
                        "A persisted RelationshipDefinition endpoint is missing."
                    )

        candidate_signature = semantic_signature(candidate)
        for existing in certified:
            if existing.id == candidate.id:
                continue
            if semantic_signature(existing) == candidate_signature:
                raise _state(
                    "relationship_definition_equivalent",
                    "An equivalent RelationshipDefinition already exists.",
                    {"relationship_definition_id": str(existing.id)},
                )

        try:
            for existing in certified:
                if existing.id == candidate.id:
                    continue
                conflict = first_conflict(candidate, existing, parent_by_id)
                if conflict is not None:
                    candidate_resolution, _ = conflict
                    raise _state(
                        "relationship_definition_conflict",
                        "A RelationshipDefinition Resolution conflicts with the "
                        "certified set.",
                        {
                            "relationship_definition_id": str(existing.id),
                            "name": candidate_resolution.name,
                        },
                    )
        except RelationshipDefinitionValidationError as error:
            raise _internal(
                "The persisted ObjectTemplate ancestry graph is invalid."
            ) from error

    async def create_non_symmetric(
        self,
        perspectives: tuple[RelationshipPerspective, RelationshipPerspective],
        properties: tuple[RelationshipPropertyCandidate, ...] = (),
    ) -> CreateRelationshipDefinitionResult:
        try:
            candidate = new_non_symmetric_definition(perspectives)
        except RelationshipDefinitionValidationError as error:
            raise _semantic(error) from error
        return await self._create(candidate, properties)

    async def create_symmetric(
        self,
        endpoint_template_ids: tuple[UUID, UUID],
        name: str,
        properties: tuple[RelationshipPropertyCandidate, ...] = (),
    ) -> CreateRelationshipDefinitionResult:
        try:
            candidate = new_symmetric_definition(endpoint_template_ids, name)
        except RelationshipDefinitionValidationError as error:
            raise _semantic(error) from error
        return await self._create(candidate, properties)

    async def _create(
        self,
        candidate: RelationshipDefinition,
        properties: tuple[RelationshipPropertyCandidate, ...],
    ) -> CreateRelationshipDefinitionResult:
        async def attempt(
            uow: Any, attempt_number: int
        ) -> CreateRelationshipDefinitionResult:
            del attempt_number
            endpoint_ids = {
                template_id
                for resolution in candidate.resolutions
                for template_id in (
                    resolution.from_template_id,
                    resolution.to_template_id,
                )
            }
            version_store = RelationshipDefinitionVersionStore(uow.connection)
            resolved_candidate = await self._resolve_properties(
                version_store, properties, None
            )
            version = RelationshipDefinitionVersion(
                candidate.id,
                1,
                1,
                VersionStatus.DRAFT,
                resolved_candidate.properties,
            )
            plan, missing = await _acquire(
                uow.connection,
                (
                    *(_template_intent(item) for item in endpoint_ids),
                    *self._candidate_dependency_intents(resolved_candidate, None),
                ),
                AdvisoryGate.RELATIONSHIP_DEFINITION_CONFLICT_GATE,
            )
            missing_templates = sorted(
                (
                    key.resource_id
                    for key in missing
                    if key.row_class is RowLockClass.OBJECT_TEMPLATE_HEADER
                ),
                key=lambda value: value.int,
            )
            if missing_templates:
                raise _referenced_template(missing_templates[0])
            dependency_failure = self._missing_dependency_failure(
                missing, resolved_candidate
            )
            if dependency_failure is not None:
                raise dependency_failure
            store = RelationshipDefinitionStore(uow.connection)
            await self._certify(store, candidate, create_operands=True)
            resolved_candidate = await self._resolve_properties(
                version_store, properties, None
            )
            version = RelationshipDefinitionVersion(
                candidate.id,
                1,
                1,
                VersionStatus.DRAFT,
                resolved_candidate.properties,
            )
            plan.require_same_plan(
                (
                    *(_template_intent(item) for item in endpoint_ids),
                    *self._candidate_dependency_intents(resolved_candidate, None),
                ),
                gate=AdvisoryGate.RELATIONSHIP_DEFINITION_CONFLICT_GATE,
            )
            await self._validate_version_candidate(version_store, version)
            plan.begin_dml()
            try:
                await store.insert(candidate, version)
            except RelationshipEndpointReferenceError as error:
                raise _referenced_template(error.template_id) from error
            await uow.commit()
            return CreateRelationshipDefinitionResult(candidate, version)

        try:
            return await run_semantic_uow_attempts(self._uow_factory, attempt)
        except LockPlanAttemptsExhausted as error:
            raise _internal(
                "The RelationshipDefinition lock plan did not stabilize."
            ) from error

    async def rename_non_symmetric(
        self,
        definition_id: UUID,
        updates: tuple[ResolutionRename, ResolutionRename],
    ) -> RelationshipDefinition:
        return await self._rename(definition_id, updates=updates, name=None)

    async def rename_symmetric(
        self, definition_id: UUID, name: str
    ) -> RelationshipDefinition:
        return await self._rename(definition_id, updates=None, name=name)

    async def _rename(
        self,
        definition_id: UUID,
        *,
        updates: tuple[ResolutionRename, ResolutionRename] | None,
        name: str | None,
    ) -> RelationshipDefinition:
        async with self._uow_factory() as uow:
            store = RelationshipDefinitionStore(uow.connection)
            plan, missing = await _acquire(
                uow.connection,
                (_definition_intent(definition_id, RowLockMode.KS),),
                AdvisoryGate.RELATIONSHIP_DEFINITION_CONFLICT_GATE,
            )
            if missing:
                raise _not_found(definition_id)
            current = await store.get(definition_id)
            if current is None:
                raise _internal(
                    "A locked RelationshipDefinition aggregate could not be loaded."
                )
            _validate_persisted(current)
            try:
                if updates is not None:
                    candidate = rename_non_symmetric(current, updates)
                elif name is not None:
                    candidate = rename_symmetric(current, name)
                else:
                    raise RuntimeError("rename candidate is missing")
            except RelationshipDefinitionValidationError as error:
                raise _semantic(error) from error
            await self._certify(store, candidate, create_operands=False)
            plan.begin_dml()
            try:
                await store.update_names(candidate)
            except RuntimeError as error:
                raise _internal(
                    "The complete RelationshipDefinition rename could not be applied."
                ) from error
            await uow.commit()
            return candidate

    async def create_next(
        self, definition_id: UUID, source_version: int
    ) -> RelationshipDefinitionVersion:
        async def attempt(
            uow: Any, attempt_number: int
        ) -> RelationshipDefinitionVersion:
            del attempt_number
            definition_store = RelationshipDefinitionStore(uow.connection)
            store = RelationshipDefinitionVersionStore(uow.connection)
            definition = await definition_store.get(definition_id)
            source = await store.get_version(definition_id, source_version)
            if definition is None:
                raise _not_found(definition_id)
            if source is None:
                raise _referenced(
                    "relationship_definition_version",
                    definition_id,
                    source_version,
                )
            if source.status not in {
                VersionStatus.PUBLISHED,
                VersionStatus.DEPRECATED,
            }:
                raise _state(
                    "version_source_conflict",
                    "The selected version is not eligible as a create-next source.",
                    {"id": str(definition_id), "source_version": source_version},
                )
            intents = (
                *self._clone_dependency_intents(source),
                _definition_intent(definition_id, RowLockMode.NKU),
                _definition_version_intent(
                    definition_id, source_version, RowLockMode.KS
                ),
            )
            plan, missing = await _acquire(uow.connection, intents)
            if (
                RowLockKey(RowLockClass.RELATIONSHIP_DEFINITION_HEADER, definition_id)
                in missing
            ):
                raise _not_found(definition_id)
            source = await store.get_version(definition_id, source_version)
            if source is None:
                raise _referenced(
                    "relationship_definition_version",
                    definition_id,
                    source_version,
                )
            if source.status not in {
                VersionStatus.PUBLISHED,
                VersionStatus.DEPRECATED,
            }:
                raise _state(
                    "version_source_conflict",
                    "The selected version is not eligible as a create-next source.",
                    {"id": str(definition_id), "source_version": source_version},
                )
            plan.require_same_plan(
                (
                    *self._clone_dependency_intents(source),
                    _definition_intent(definition_id, RowLockMode.NKU),
                    _definition_version_intent(
                        definition_id, source_version, RowLockMode.KS
                    ),
                )
            )
            created = RelationshipDefinitionVersion(
                definition_id,
                await store.next_version(definition_id),
                1,
                VersionStatus.DRAFT,
                source.properties,
            )
            plan.begin_dml()
            await store.insert_version(created)
            await uow.commit()
            return created

        try:
            return await run_semantic_uow_attempts(self._uow_factory, attempt)
        except LockPlanAttemptsExhausted as error:
            raise _internal(
                "The RelationshipDefinition lock plan did not stabilize."
            ) from error

    async def revise(
        self,
        definition_id: UUID,
        version: int,
        expected_revision: int,
        properties: tuple[RelationshipPropertyCandidate, ...],
    ) -> RelationshipDefinitionVersion:
        async def attempt(
            uow: Any, attempt_number: int
        ) -> RelationshipDefinitionVersion:
            del attempt_number
            definition_store = RelationshipDefinitionStore(uow.connection)
            store = RelationshipDefinitionVersionStore(uow.connection)
            definition = await definition_store.get(definition_id)
            current = await store.get_version(definition_id, version)
            if definition is None or current is None:
                raise _version_not_found(definition_id, version)
            self._require_draft(current, expected_revision)
            resolved = await self._resolve_properties(store, properties, current)
            candidate = RelationshipDefinitionVersion(
                definition_id,
                version,
                current.revision + 1,
                VersionStatus.DRAFT,
                resolved.properties,
            )
            intents = (
                *self._candidate_dependency_intents(resolved, current),
                _definition_intent(definition_id, RowLockMode.KS),
                _definition_version_intent(definition_id, version, RowLockMode.NKU),
            )
            plan, missing = await _acquire(uow.connection, intents)
            if any(
                key.row_class
                in {
                    RowLockClass.RELATIONSHIP_DEFINITION_HEADER,
                    RowLockClass.RELATIONSHIP_DEFINITION_VERSION,
                }
                for key in missing
            ):
                raise _version_not_found(definition_id, version)
            dependency_failure = self._missing_dependency_failure(missing, resolved)
            if dependency_failure is not None:
                raise dependency_failure
            current = await store.get_version(definition_id, version)
            if current is None:
                raise _version_not_found(definition_id, version)
            self._require_draft(current, expected_revision)
            resolved = await self._resolve_properties(store, properties, current)
            candidate = RelationshipDefinitionVersion(
                definition_id,
                version,
                current.revision + 1,
                VersionStatus.DRAFT,
                resolved.properties,
            )
            plan.require_same_plan(
                (
                    *self._candidate_dependency_intents(resolved, current),
                    _definition_intent(definition_id, RowLockMode.KS),
                    _definition_version_intent(definition_id, version, RowLockMode.NKU),
                )
            )
            await self._validate_version_candidate(store, candidate)
            plan.begin_dml()
            await store.replace_candidate(candidate)
            revised = await store.get_version(definition_id, version)
            if revised is None:
                raise _internal(
                    "The revised RelationshipDefinitionVersion disappeared."
                )
            await uow.commit()
            return revised

        try:
            return await run_semantic_uow_attempts(self._uow_factory, attempt)
        except LockPlanAttemptsExhausted as error:
            raise _internal(
                "The RelationshipDefinition lock plan did not stabilize."
            ) from error

    async def publish(
        self, definition_id: UUID, version: int, expected_revision: int
    ) -> RelationshipDefinitionVersion:
        async def attempt(
            uow: Any, attempt_number: int
        ) -> RelationshipDefinitionVersion:
            del attempt_number
            definition_store = RelationshipDefinitionStore(uow.connection)
            store = RelationshipDefinitionVersionStore(uow.connection)
            definition = await definition_store.get(definition_id)
            current = await store.get_version(definition_id, version)
            if definition is None or current is None:
                raise _version_not_found(definition_id, version)
            self._require_draft(current, expected_revision)
            plan, missing = await _acquire(
                uow.connection, self._publish_intents(current)
            )
            if missing:
                key = missing[0]
                if key.row_class in {
                    RowLockClass.RELATIONSHIP_DEFINITION_HEADER,
                    RowLockClass.RELATIONSHIP_DEFINITION_VERSION,
                }:
                    raise _version_not_found(definition_id, version)
                raise _internal("A persisted DataType dependency is missing.")
            definition = await definition_store.get(definition_id)
            current = await store.get_version(definition_id, version)
            if definition is None or current is None:
                raise _version_not_found(definition_id, version)
            self._require_draft(current, expected_revision)
            plan.require_same_plan(self._publish_intents(current))
            await self._validate_version_candidate(store, current)
            datatype_store = DataTypeStore(uow.connection)
            dependencies = await datatype_store.get_versions(
                tuple(
                    (item.datatype_id, item.datatype_version)
                    for item in current.properties
                )
            )
            for item in current.properties:
                dependency = dependencies.get((item.datatype_id, item.datatype_version))
                if dependency is None:
                    raise _internal("A persisted DataType dependency is missing.")
                self._require_published(
                    dependency, item.datatype_id, item.datatype_version
                )
            plan.begin_dml()
            await store.set_status(definition_id, version, VersionStatus.PUBLISHED)
            if definition.default_version is None:
                await store.set_default(definition_id, version)
            published = await store.get_version(definition_id, version)
            if published is None:
                raise _internal(
                    "The published RelationshipDefinitionVersion disappeared."
                )
            await uow.commit()
            return published

        try:
            return await run_semantic_uow_attempts(self._uow_factory, attempt)
        except LockPlanAttemptsExhausted as error:
            raise _internal(
                "The RelationshipDefinition lock plan did not stabilize."
            ) from error

    async def set_default(
        self, definition_id: UUID, version: int
    ) -> RelationshipDefinition:
        async with self._uow_factory() as uow:
            store = RelationshipDefinitionVersionStore(uow.connection)
            plan, missing = await _acquire(
                uow.connection,
                (
                    _definition_intent(definition_id, RowLockMode.NKU),
                    _definition_version_intent(definition_id, version, RowLockMode.S),
                ),
            )
            if (
                RowLockKey(RowLockClass.RELATIONSHIP_DEFINITION_HEADER, definition_id)
                in missing
            ):
                raise _not_found(definition_id)
            target = await store.get_version(definition_id, version)
            if target is None:
                raise _referenced(
                    "relationship_definition_version", definition_id, version
                )
            self._require_published(target, definition_id, version)
            plan.begin_dml()
            result = await store.set_default(definition_id, version)
            await uow.commit()
            return result

    async def clear_default(self, definition_id: UUID) -> RelationshipDefinition:
        async with self._uow_factory() as uow:
            store = RelationshipDefinitionVersionStore(uow.connection)
            plan, missing = await _acquire(
                uow.connection,
                (_definition_intent(definition_id, RowLockMode.NKU),),
            )
            if missing:
                raise _not_found(definition_id)
            plan.begin_dml()
            result = await store.set_default(definition_id, None)
            await uow.commit()
            return result

    async def deprecate(
        self, definition_id: UUID, version: int
    ) -> RelationshipDefinitionVersion:
        async with self._uow_factory() as uow:
            definition_store = RelationshipDefinitionStore(uow.connection)
            store = RelationshipDefinitionVersionStore(uow.connection)
            plan, missing = await _acquire(
                uow.connection,
                (
                    _definition_intent(definition_id, RowLockMode.S),
                    _definition_version_intent(definition_id, version, RowLockMode.NKU),
                ),
            )
            if missing:
                raise _version_not_found(definition_id, version)
            definition = await definition_store.get(definition_id)
            current = await store.get_version(definition_id, version)
            if definition is None or current is None:
                raise _version_not_found(definition_id, version)
            if current.status is not VersionStatus.PUBLISHED:
                raise _state(
                    "lifecycle_state_conflict",
                    "Only a PUBLISHED RelationshipDefinitionVersion can be deprecated.",
                    {"id": str(definition_id), "version": version},
                )
            if definition.default_version == version:
                raise _state(
                    "default_version_conflict",
                    "The current default version cannot be deprecated.",
                    {"id": str(definition_id), "version": version},
                )
            plan.begin_dml()
            await store.set_status(definition_id, version, VersionStatus.DEPRECATED)
            result = await store.get_version(definition_id, version)
            if result is None:
                raise _internal(
                    "The deprecated RelationshipDefinitionVersion disappeared."
                )
            await uow.commit()
            return result

    async def delete_draft(
        self, definition_id: UUID, version: int, expected_revision: int
    ) -> None:
        async with self._uow_factory() as uow:
            store = RelationshipDefinitionVersionStore(uow.connection)
            plan, missing = await _acquire(
                uow.connection,
                (
                    _definition_intent(definition_id, RowLockMode.NKU),
                    _definition_version_intent(definition_id, version, RowLockMode.U),
                ),
            )
            if missing:
                raise _version_not_found(definition_id, version)
            current = await store.get_version(definition_id, version)
            if current is None:
                raise _version_not_found(definition_id, version)
            self._require_draft(current, expected_revision)
            plan.begin_dml()
            await store.delete_draft(definition_id, version)
            await uow.commit()

    async def delete(self, definition_id: UUID) -> None:
        async with self._uow_factory() as uow:
            store = RelationshipDefinitionStore(uow.connection)
            plan, missing = await _acquire(
                uow.connection,
                (_definition_intent(definition_id, RowLockMode.U),),
                AdvisoryGate.MODEL_ROOT_DELETE_GATE,
            )
            if missing:
                raise _not_found(definition_id)
            current = await store.get(definition_id)
            if current is None:
                raise _internal(
                    "A locked RelationshipDefinition aggregate could not be loaded."
                )
            _validate_persisted(current)
            relationship_count = await store.current_relationship_count(definition_id)
            if relationship_count:
                raise _state(
                    "delete_blocked",
                    "Current Relationships prevent RelationshipDefinition deletion.",
                    {
                        "resource_type": "relationship_definition",
                        "id": str(definition_id),
                        "blockers": [
                            {"type": "relationship", "count": relationship_count}
                        ],
                    },
                )
            plan.begin_dml()
            try:
                await store.delete(definition_id)
            except RelationshipDefinitionDeleteReferenceError as error:
                raise _state(
                    "delete_blocked",
                    "A concurrent current Relationship prevented deletion.",
                    {
                        "resource_type": "relationship_definition",
                        "id": str(definition_id),
                        "blockers": [{"type": "relationship", "count": 1}],
                    },
                ) from error
            await uow.commit()

    async def _validate_default_pointers(
        self,
        store: RelationshipDefinitionVersionStore,
        values: tuple[RelationshipDefinition, ...],
    ) -> None:
        targets = await store.get_headers(
            tuple(
                (value.id, value.default_version)
                for value in values
                if value.default_version is not None
            )
        )
        for value in values:
            if value.default_version is None:
                continue
            target = targets.get((value.id, value.default_version))
            if target is None or target.status is not VersionStatus.PUBLISHED:
                raise _internal(
                    "A persisted RelationshipDefinition default pointer is invalid."
                )

    async def get(self, definition_id: UUID) -> RelationshipDefinition:
        async with self._uow_factory.coherent_read() as uow:
            value = await RelationshipDefinitionStore(uow.connection).get(definition_id)
            if value is None:
                raise _not_found(definition_id)
            _validate_persisted(value)
            await self._validate_default_pointers(
                RelationshipDefinitionVersionStore(uow.connection), (value,)
            )
            return value

    async def get_version(
        self, definition_id: UUID, version: int
    ) -> RelationshipDefinitionVersion:
        async with self._uow_factory.coherent_read() as uow:
            if (
                await RelationshipDefinitionStore(uow.connection).get(definition_id)
                is None
            ):
                raise _not_found(definition_id)
            value = await RelationshipDefinitionVersionStore(
                uow.connection
            ).get_version(definition_id, version)
            if value is None:
                raise _version_not_found(definition_id, version)
            try:
                validate_relationship_definition_version(value)
            except RelationshipDefinitionValidationError as error:
                raise _internal(
                    "A persisted RelationshipDefinitionVersion is invalid."
                ) from error
            return value

    async def list_versions(
        self,
        definition_id: UUID,
        *,
        status: VersionStatus | None,
        cursor: str | None,
        limit: int,
    ) -> Page[RelationshipDefinitionVersionSummary]:
        filters: dict[str, JsonValue] = {
            "definition_id": str(definition_id),
            "status": None if status is None else status.value,
        }
        after: int | None = None
        if cursor is not None:
            key = decode_cursor(cursor, "relationship_definition_versions", filters)
            if (
                len(key) != 1
                or isinstance(key[0], bool)
                or not isinstance(key[0], int)
                or key[0] <= 0
            ):
                raise ApplicationFailure(
                    FailureClass.INVALID_REQUEST,
                    "invalid_cursor",
                    "The cursor is malformed or incompatible with this query.",
                )
            after = key[0]
        async with self._uow_factory.coherent_read() as uow:
            definition = await RelationshipDefinitionStore(uow.connection).get(
                definition_id
            )
            if definition is None:
                raise _not_found(definition_id)
            store = RelationshipDefinitionVersionStore(uow.connection)
            await self._validate_default_pointers(store, (definition,))
            rows = list(
                await store.list_versions(
                    definition_id,
                    status=None if status is None else status.value,
                    after=after,
                    limit=limit + 1,
                )
            )
        more = len(rows) > limit
        items = rows[:limit]
        next_cursor = (
            encode_cursor(
                "relationship_definition_versions", filters, [items[-1].version]
            )
            if more
            else None
        )
        return Page(items, next_cursor)

    async def list_definitions(
        self, *, cursor: str | None, limit: int
    ) -> Page[RelationshipDefinition]:
        filters: dict[str, JsonValue] = {}
        after: UUID | None = None
        if cursor is not None:
            key = decode_cursor(cursor, "relationship_definitions", filters)
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
            rows = list(
                await RelationshipDefinitionStore(uow.connection).list_definitions(
                    after=after, limit=limit + 1
                )
            )
            for item in rows:
                _validate_persisted(item)
            await self._validate_default_pointers(
                RelationshipDefinitionVersionStore(uow.connection), tuple(rows)
            )
        more = len(rows) > limit
        items = rows[:limit]
        next_cursor = (
            encode_cursor("relationship_definitions", filters, [str(items[-1].id)])
            if more
            else None
        )
        return Page(items, next_cursor)

    async def list_capabilities(
        self,
        template_id: UUID,
        *,
        name: str | None,
        cursor: str | None,
        limit: int,
    ) -> Page[RelationshipCapability]:
        filters: dict[str, JsonValue] = {
            "template_id": str(template_id),
            "name": name,
        }
        after: UUID | None = None
        if cursor is not None:
            key = decode_cursor(cursor, "relationship_capabilities", filters)
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
            projection = await RelationshipDefinitionStore(
                uow.connection
            ).list_capabilities(
                template_id=template_id,
                name=name,
                after=after,
                limit=limit + 1,
            )
            if not projection.target_exists:
                raise _template_not_found(template_id)
            rows = list(projection.items)
        more = len(rows) > limit
        items = rows[:limit]
        next_cursor = (
            encode_cursor(
                "relationship_capabilities", filters, [str(items[-1].resolution_id)]
            )
            if more
            else None
        )
        return Page(items, next_cursor)
