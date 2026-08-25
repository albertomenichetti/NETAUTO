"""Factual Relationship application capability and semantic projections."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, NoReturn
from uuid import UUID, uuid4

from netauto.application.cursors import Page, decode_cursor, encode_cursor
from netauto.domain.datatypes import DataTypeVersion, VersionStatus
from netauto.domain.objects import (
    DataChangeKind,
    DataChangeOperation,
    ObjectValidationError,
    RuntimePropertySpec,
    apply_data_change,
    canonicalize_properties,
)
from netauto.domain.primitives import JsonValue, PrimitiveValidationError
from netauto.domain.relationships import (
    ObjectRelationshipView,
    Relationship,
    RelationshipDefinition,
    RelationshipDefinitionValidationError,
    RelationshipDefinitionVersion,
    RelationshipLifecycleView,
    RelationshipSchemaChangeBlocked,
    RelationshipSchemaPropertySpec,
    RelationshipValidationError,
    RelationshipView,
    RuntimeRelationshipResolution,
    derive_runtime_closure,
    migrate_relationship_properties,
    relationship_views,
    validate_definition,
    validate_lineage_graph,
    validate_relationship,
    validate_relationship_definition_version,
    validate_relationship_property_history,
)
from netauto.failures import ApplicationFailure, FailureClass
from netauto.persistence.datatypes import DataTypeStore
from netauto.persistence.lifecycle import EventKind, LifecycleStore
from netauto.persistence.locking import (
    MAX_SEMANTIC_UOW_ATTEMPTS,
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
    ExactRelationshipViewCollision,
    RelationshipDefinitionStore,
    RelationshipDefinitionVersionStore,
    RuntimeRelationshipModelReferenceError,
    RuntimeRelationshipObjectReferenceError,
    RuntimeRelationshipStore,
)
from netauto.persistence.uow import UnitOfWorkFactory


@dataclass(frozen=True, slots=True)
class RelationshipProjection:
    id: UUID
    relationship_definition_id: UUID
    relationship_definition_version: int
    properties: dict[str, JsonValue]
    views: tuple[RelationshipView, ...]


@dataclass(frozen=True, slots=True)
class RelationshipCreateResult:
    relationship: RelationshipProjection
    created: bool


class _RestartRelationshipCreate(Exception):
    pass


def _projected_views(
    values: Sequence[RelationshipLifecycleView],
) -> tuple[RelationshipView, ...]:
    return tuple(
        RelationshipView(
            item.object_id,
            item.destination_object_id,
            item.relationship_name,
        )
        for item in values
    )


def _not_found(relationship_id: UUID) -> ApplicationFailure:
    return ApplicationFailure(
        FailureClass.NOT_FOUND,
        "resource_not_found",
        "The requested Relationship does not exist.",
        {"resource_type": "relationship", "id": str(relationship_id)},
    )


def _referenced_resolution(resolution_id: UUID) -> ApplicationFailure:
    return ApplicationFailure(
        FailureClass.SEMANTIC_VALIDATION,
        "referenced_resource_not_found",
        "The selected RelationshipResolution does not exist.",
        {"resource_type": "relationship_resolution", "id": str(resolution_id)},
    )


def _referenced_object(object_id: UUID) -> ApplicationFailure:
    return ApplicationFailure(
        FailureClass.SEMANTIC_VALIDATION,
        "referenced_resource_not_found",
        "A referenced Object does not exist.",
        {"resource_type": "object", "id": str(object_id)},
    )


def _referenced_version(definition_id: UUID, version: int) -> ApplicationFailure:
    return ApplicationFailure(
        FailureClass.SEMANTIC_VALIDATION,
        "referenced_resource_not_found",
        "The selected RelationshipDefinitionVersion does not exist.",
        {
            "resource_type": "relationship_definition_version",
            "id": str(definition_id),
            "version": version,
        },
    )


def _default_unavailable(definition_id: UUID) -> ApplicationFailure:
    return ApplicationFailure(
        FailureClass.STATE_CONFLICT,
        "default_version_unavailable",
        "The selected RelationshipDefinition has no default version.",
        {"id": str(definition_id)},
    )


def _dependency_not_admissible(definition_id: UUID, version: int) -> ApplicationFailure:
    return ApplicationFailure(
        FailureClass.STATE_CONFLICT,
        "dependency_not_admissible",
        "The selected RelationshipDefinitionVersion is not PUBLISHED.",
        {"id": str(definition_id), "version": version},
    )


def _invalid_schema_target(rule: str) -> ApplicationFailure:
    return ApplicationFailure(
        FailureClass.SEMANTIC_VALIDATION,
        "semantic_validation_failed",
        "The Relationship schema-change target is not semantically valid.",
        {"violations": [{"path": "target_version", "rule": rule}]},
    )


def _schema_change_blocked(
    relationship_id: UUID, target_version: int, member_name: str
) -> ApplicationFailure:
    return ApplicationFailure(
        FailureClass.STATE_CONFLICT,
        "schema_change_blocked",
        "A current Relationship property is incompatible with the target schema.",
        {
            "relationship_id": str(relationship_id),
            "target_version": target_version,
            "blocker_type": "property",
            "member_name": member_name,
        },
    )


def _semantic(error: RelationshipValidationError) -> ApplicationFailure:
    return ApplicationFailure(
        FailureClass.SEMANTIC_VALIDATION,
        "semantic_validation_failed",
        "The Relationship candidate is not semantically valid.",
        {"violations": [{"path": error.path, "rule": error.rule}]},
    )


def _internal(message: str) -> ApplicationFailure:
    return ApplicationFailure(FailureClass.INTERNAL_FAILURE, "internal_error", message)


def _fact_conflict(relationship_id: UUID) -> ApplicationFailure:
    return ApplicationFailure(
        FailureClass.STATE_CONFLICT,
        "relationship_fact_conflict",
        "The candidate closure conflicts with a distinct factual Relationship.",
        {"relationship_id": str(relationship_id)},
    )


def _definition_create_intent(definition_id: UUID, *, implicit: bool) -> RowLockIntent:
    return RowLockIntent(
        RowLockKey(RowLockClass.RELATIONSHIP_DEFINITION_HEADER, definition_id),
        RowLockMode.S if implicit else RowLockMode.KS,
    )


def _definition_version_intent(definition_id: UUID, version: int) -> RowLockIntent:
    return RowLockIntent(
        RowLockKey(
            RowLockClass.RELATIONSHIP_DEFINITION_VERSION,
            definition_id,
            version,
        ),
        RowLockMode.S,
    )


def _object_intent(object_id: UUID) -> RowLockIntent:
    return RowLockIntent(RowLockKey(RowLockClass.OBJECT, object_id), RowLockMode.KS)


def _relationship_intent(relationship_id: UUID) -> RowLockIntent:
    return RowLockIntent(
        RowLockKey(RowLockClass.RELATIONSHIP, relationship_id), RowLockMode.U
    )


def _relationship_mutation_intent(relationship_id: UUID) -> RowLockIntent:
    return RowLockIntent(
        RowLockKey(RowLockClass.RELATIONSHIP, relationship_id), RowLockMode.NKU
    )


def _relationship_lifetime_intent(relationship_id: UUID) -> RowLockIntent:
    return RowLockIntent(
        RowLockKey(RowLockClass.RELATIONSHIP, relationship_id), RowLockMode.KS
    )


class RelationshipService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    @staticmethod
    def _resolved_schema(
        exact: RelationshipDefinitionVersion,
        datatypes: Mapping[tuple[UUID, int], DataTypeVersion],
        *,
        require_published: bool,
    ) -> tuple[RelationshipSchemaPropertySpec, ...]:
        try:
            validate_relationship_definition_version(exact)
        except RelationshipDefinitionValidationError as error:
            raise _internal(
                "A persisted RelationshipDefinitionVersion is invalid."
            ) from error
        if require_published and exact.status is not VersionStatus.PUBLISHED:
            raise _dependency_not_admissible(
                exact.relationship_definition_id, exact.version
            )
        if exact.status is VersionStatus.DRAFT:
            raise _internal("A factual Relationship is pinned to a DRAFT schema.")
        specs: list[RelationshipSchemaPropertySpec] = []
        for item in exact.properties:
            datatype = datatypes.get((item.datatype_id, item.datatype_version))
            if not isinstance(datatype, DataTypeVersion) or (
                datatype.status is VersionStatus.DRAFT
            ):
                raise _internal("A Relationship property dependency is invalid.")
            if (
                exact.status is VersionStatus.PUBLISHED
                and datatype.status is not VersionStatus.PUBLISHED
            ):
                raise _internal("An active Relationship dependency is not PUBLISHED.")
            specs.append(
                RelationshipSchemaPropertySpec(
                    item.position,
                    item.datatype_id,
                    RuntimePropertySpec(
                        item.name,
                        item.value_mode,
                        False,
                        datatype.base_type,
                        datatype.constraints,
                    ),
                )
            )
        return tuple(specs)

    async def _relationship_schema(
        self,
        version_store: RelationshipDefinitionVersionStore,
        definition_id: UUID,
        version: int,
        *,
        require_published: bool,
    ) -> tuple[RelationshipSchemaPropertySpec, ...]:
        exact = await version_store.get_version(definition_id, version)
        if exact is None:
            raise _internal("A factual Relationship exact schema is missing.")
        datatype_store = DataTypeStore(version_store.connection)
        datatypes = await datatype_store.get_versions(
            tuple(
                (item.datatype_id, item.datatype_version) for item in exact.properties
            )
        )
        return self._resolved_schema(
            exact, datatypes, require_published=require_published
        )

    async def _relationship_specs(
        self,
        version_store: RelationshipDefinitionVersionStore,
        definition_id: UUID,
        version: int,
        *,
        require_published: bool,
    ) -> tuple[RuntimePropertySpec, ...]:
        schema = await self._relationship_schema(
            version_store,
            definition_id,
            version,
            require_published=require_published,
        )
        return tuple(item.runtime for item in schema)

    async def _validated(
        self,
        store: RuntimeRelationshipStore,
        definition_store: RelationshipDefinitionStore,
        relationship_id: UUID,
        *,
        restart_if_missing: bool = False,
    ) -> tuple[Relationship, RelationshipDefinition, RelationshipProjection]:
        try:
            value = await store.get(relationship_id)
        except RuntimeError as error:
            raise _internal(
                "The persisted factual Relationship aggregate is invalid."
            ) from error
        if value is None:
            if restart_if_missing:
                raise _RestartRelationshipCreate
            raise _internal("A referenced factual Relationship aggregate is missing.")
        definition = await definition_store.get(value.relationship_definition_id)
        if definition is None:
            raise _internal("A factual Relationship has no current Definition.")
        endpoint_ids = {
            endpoint_id
            for item in value.resolutions
            for endpoint_id in (item.from_object_id, item.to_object_id)
        }
        templates = await store.object_template_ids(endpoint_ids)
        parents = await definition_store.lineage_parents()
        try:
            validate_definition(definition)
            validate_lineage_graph(parents)
            validate_relationship(
                value,
                definition,
                parent_by_id=parents,
                template_by_object_id=templates,
            )
            specs = await self._relationship_specs(
                RelationshipDefinitionVersionStore(store.connection),
                value.relationship_definition_id,
                value.relationship_definition_version,
                require_published=False,
            )
            canonical = canonicalize_properties(value.properties, specs)
            if canonical != value.properties:
                raise RelationshipValidationError(
                    "properties", "noncanonical_persisted_properties"
                )
            views = relationship_views(value, definition)
        except (
            ObjectValidationError,
            PrimitiveValidationError,
            RelationshipDefinitionValidationError,
            RelationshipValidationError,
        ) as error:
            raise _internal(
                "The persisted factual Relationship aggregate is invalid."
            ) from error
        return (
            value,
            definition,
            RelationshipProjection(
                value.id,
                value.relationship_definition_id,
                value.relationship_definition_version,
                value.properties,
                views,
            ),
        )

    async def _validated_many(
        self,
        store: RuntimeRelationshipStore,
        definition_store: RelationshipDefinitionStore,
        relationship_ids: set[UUID],
    ) -> dict[UUID, RelationshipProjection]:
        """Validate a page with bounded aggregate/dependency batch reads."""
        try:
            values = await store.get_many(relationship_ids)
        except RuntimeError as error:
            raise _internal(
                "The persisted factual Relationship aggregate is invalid."
            ) from error
        if set(values) != relationship_ids:
            raise _internal("A referenced factual Relationship aggregate is missing.")
        definition_ids = {value.relationship_definition_id for value in values.values()}
        definitions = await definition_store.get_many(definition_ids)
        if set(definitions) != definition_ids:
            raise _internal("A referenced RelationshipDefinition aggregate is missing.")
        endpoint_ids = {
            endpoint_id
            for value in values.values()
            for item in value.resolutions
            for endpoint_id in (item.from_object_id, item.to_object_id)
        }
        templates = await store.object_template_ids(endpoint_ids)
        parents = await definition_store.lineage_parents()
        version_store = RelationshipDefinitionVersionStore(store.connection)
        version_keys = tuple(
            (
                value.relationship_definition_id,
                value.relationship_definition_version,
            )
            for value in values.values()
        )
        versions = await version_store.get_versions(version_keys)
        datatype_keys = tuple(
            (item.datatype_id, item.datatype_version)
            for version in versions.values()
            for item in version.properties
        )
        datatypes = await DataTypeStore(store.connection).get_versions(datatype_keys)
        projections: dict[UUID, RelationshipProjection] = {}
        try:
            validate_lineage_graph(parents)
            for relationship_id in sorted(relationship_ids, key=lambda item: item.int):
                value = values[relationship_id]
                definition = definitions.get(value.relationship_definition_id)
                if definition is None:
                    raise RelationshipValidationError(
                        "relationship", "missing_definition"
                    )
                validate_definition(definition)
                validate_relationship(
                    value,
                    definition,
                    parent_by_id=parents,
                    template_by_object_id=templates,
                )
                exact = versions.get(
                    (
                        value.relationship_definition_id,
                        value.relationship_definition_version,
                    )
                )
                if exact is None:
                    raise RelationshipValidationError(
                        "relationship_definition_version", "missing_exact_schema"
                    )
                schema = self._resolved_schema(
                    exact, datatypes, require_published=False
                )
                canonical = canonicalize_properties(
                    value.properties, tuple(item.runtime for item in schema)
                )
                if canonical != value.properties:
                    raise RelationshipValidationError(
                        "properties", "noncanonical_persisted_properties"
                    )
                projections[relationship_id] = RelationshipProjection(
                    value.id,
                    value.relationship_definition_id,
                    value.relationship_definition_version,
                    value.properties,
                    relationship_views(value, definition),
                )
        except (
            ObjectValidationError,
            PrimitiveValidationError,
            RelationshipDefinitionValidationError,
            RelationshipValidationError,
        ) as error:
            raise _internal(
                "The persisted factual Relationship aggregate is invalid."
            ) from error
        return projections

    async def _classify_exact_view_collision(
        self,
        collision_keys: tuple[RuntimeRelationshipResolution, ...],
        *,
        resolution_id: UUID,
        from_object_id: UUID,
        to_object_id: UUID,
    ) -> NoReturn:
        """Classify a rolled-back collision under one protected owner set."""
        async with self._uow_factory() as uow:
            store = RuntimeRelationshipStore(uow.connection)
            definition_store = RelationshipDefinitionStore(uow.connection)
            observed_owner_ids = tuple(
                sorted(
                    set(await store.current_candidate_relationship_ids(collision_keys)),
                    key=lambda value: value.int,
                )
            )
            if not observed_owner_ids:
                raise _RestartRelationshipCreate

            plan = await prepare_lock_plan(
                uow.connection,
                intents=tuple(
                    _relationship_lifetime_intent(relationship_id)
                    for relationship_id in observed_owner_ids
                ),
            )
            missing = await acquire_lock_plan(uow.connection, plan)
            protected_owner_ids = tuple(
                sorted(
                    set(await store.current_candidate_relationship_ids(collision_keys)),
                    key=lambda value: value.int,
                )
            )
            if missing or protected_owner_ids != observed_owner_ids:
                raise _RestartRelationshipCreate

            projections: dict[UUID, RelationshipProjection] = {}
            for relationship_id in protected_owner_ids:
                _, _, projection = await self._validated(
                    store, definition_store, relationship_id
                )
                projections[relationship_id] = projection

            current_id = await store.exact_relationship_id(
                resolution_id, from_object_id, to_object_id
            )
            if current_id is not None:
                if current_id not in projections:
                    raise _RestartRelationshipCreate
                raise _fact_conflict(current_id)
            raise _fact_conflict(protected_owner_ids[0])

    async def create(
        self,
        resolution_id: UUID,
        from_object_id: UUID,
        to_object_id: UUID,
        relationship_definition_version: int | None = None,
        properties: Mapping[str, object] | None = None,
    ) -> RelationshipCreateResult:
        for attempt_number in range(1, MAX_SEMANTIC_UOW_ATTEMPTS + 1):
            collision_keys: tuple[RuntimeRelationshipResolution, ...] | None = None
            async with self._uow_factory() as uow:
                definition_store = RelationshipDefinitionStore(uow.connection)
                definition = await definition_store.get_by_resolution(resolution_id)
                if definition is None:
                    raise _referenced_resolution(resolution_id)
                implicit = relationship_definition_version is None
                selected_version = (
                    definition.default_version
                    if implicit
                    else relationship_definition_version
                )
                if selected_version is None:
                    raise _default_unavailable(definition.id)
                version_store = RelationshipDefinitionVersionStore(uow.connection)
                target = await version_store.get_version(
                    definition.id, selected_version
                )
                if target is None:
                    if implicit:
                        raise _internal(
                            "A persisted RelationshipDefinition default is missing."
                        )
                    raise _referenced_version(definition.id, selected_version)
                if target.status is not VersionStatus.PUBLISHED:
                    raise _dependency_not_admissible(definition.id, selected_version)
                plan = await prepare_lock_plan(
                    uow.connection,
                    intents=(
                        _definition_create_intent(definition.id, implicit=implicit),
                        _definition_version_intent(definition.id, selected_version),
                        _object_intent(from_object_id),
                        _object_intent(to_object_id),
                    ),
                )
                missing = await acquire_lock_plan(uow.connection, plan)
                if RowLockKey(RowLockClass.OBJECT, from_object_id) in missing:
                    raise _referenced_object(from_object_id)
                if RowLockKey(RowLockClass.OBJECT, to_object_id) in missing:
                    raise _referenced_object(to_object_id)

                definition = await definition_store.get_by_resolution(resolution_id)
                if definition is None:
                    raise _referenced_resolution(resolution_id)
                fresh_selected_version = (
                    definition.default_version
                    if implicit
                    else relationship_definition_version
                )
                if fresh_selected_version is None:
                    raise _default_unavailable(definition.id)
                if fresh_selected_version != selected_version:
                    continue
                target = await version_store.get_version(
                    definition.id, selected_version
                )
                if target is None:
                    if implicit:
                        raise _internal(
                            "A persisted RelationshipDefinition default is missing."
                        )
                    raise _referenced_version(definition.id, selected_version)
                if target.status is not VersionStatus.PUBLISHED:
                    raise _dependency_not_admissible(definition.id, selected_version)
                try:
                    validate_definition(definition)
                except RelationshipDefinitionValidationError as error:
                    raise _internal(
                        "The selected RelationshipDefinition aggregate is invalid."
                    ) from error

                store = RuntimeRelationshipStore(uow.connection)
                templates = await store.object_template_ids(
                    (from_object_id, to_object_id)
                )
                if from_object_id not in templates:
                    raise _referenced_object(from_object_id)
                if to_object_id not in templates:
                    raise _referenced_object(to_object_id)
                parents = await definition_store.lineage_parents()
                try:
                    validate_lineage_graph(parents)
                    relationship_id = uuid4()
                    resolutions = derive_runtime_closure(
                        definition,
                        selected_resolution_id=resolution_id,
                        from_object_id=from_object_id,
                        from_template_id=templates[from_object_id],
                        to_object_id=to_object_id,
                        to_template_id=templates[to_object_id],
                        parent_by_id=parents,
                        relationship_id=relationship_id,
                    )
                except RelationshipValidationError as error:
                    raise _semantic(error) from error
                except RelationshipDefinitionValidationError as error:
                    raise _internal(
                        "The persisted Relationship model or lineage graph is invalid."
                    ) from error

                try:
                    canonical_properties = canonicalize_properties(
                        {} if properties is None else properties,
                        await self._relationship_specs(
                            version_store,
                            definition.id,
                            selected_version,
                            require_published=True,
                        ),
                    )
                except (ObjectValidationError, PrimitiveValidationError) as error:
                    raise ApplicationFailure(
                        FailureClass.SEMANTIC_VALIDATION,
                        "semantic_validation_failed",
                        "The Relationship property candidate is not "
                        "semantically valid.",
                        {
                            "violations": [
                                {
                                    "path": getattr(error, "path", "properties"),
                                    "rule": getattr(error, "rule", "invalid_value"),
                                }
                            ]
                        },
                    ) from error

                current_id = await store.exact_relationship_id(
                    resolution_id, from_object_id, to_object_id
                )
                if current_id is not None:
                    try:
                        _, _, projection = await self._validated(
                            store,
                            definition_store,
                            current_id,
                            restart_if_missing=True,
                        )
                    except _RestartRelationshipCreate:
                        pass
                    else:
                        raise _fact_conflict(projection.id)

                conflicts = await store.current_candidate_relationship_ids(resolutions)
                if conflicts:
                    surviving_conflicts: list[UUID] = []
                    for conflicting_id in conflicts:
                        try:
                            await self._validated(
                                store,
                                definition_store,
                                conflicting_id,
                                restart_if_missing=True,
                            )
                        except _RestartRelationshipCreate:
                            continue
                        surviving_conflicts.append(conflicting_id)
                    if surviving_conflicts:
                        raise _fact_conflict(surviving_conflicts[0])

                relationship = Relationship(
                    id=relationship_id,
                    relationship_definition_id=definition.id,
                    resolutions=resolutions,
                    relationship_definition_version=selected_version,
                    properties=canonical_properties,
                )
                plan.begin_dml()
                try:
                    await store.insert(relationship)
                except ExactRelationshipViewCollision:
                    collision_keys = tuple(resolutions)
                except RuntimeRelationshipModelReferenceError as error:
                    raise _referenced_resolution(resolution_id) from error
                except RuntimeRelationshipObjectReferenceError as error:
                    raise _referenced_object(error.object_id) from error
                if collision_keys is None:
                    lifecycle = LifecycleStore(uow.connection)
                    lifecycle_views = await lifecycle.relationship_views(relationship)
                    projected_views = _projected_views(lifecycle_views)
                    await lifecycle.insert_relationship_events(
                        kind=EventKind.RELATIONSHIP_CREATED,
                        before=None,
                        after=relationship,
                        views=lifecycle_views,
                    )
                    await uow.commit()
                    return RelationshipCreateResult(
                        RelationshipProjection(
                            relationship.id,
                            relationship.relationship_definition_id,
                            relationship.relationship_definition_version,
                            relationship.properties,
                            projected_views,
                        ),
                        True,
                    )

            try:
                return await self._classify_exact_view_collision(
                    collision_keys,
                    resolution_id=resolution_id,
                    from_object_id=from_object_id,
                    to_object_id=to_object_id,
                )
            except _RestartRelationshipCreate:
                pass
            if attempt_number == MAX_SEMANTIC_UOW_ATTEMPTS:
                break
        raise _internal("The Relationship create restart budget was exhausted.")

    async def get(self, relationship_id: UUID) -> RelationshipProjection:
        async with self._uow_factory.coherent_read() as uow:
            store = RuntimeRelationshipStore(uow.connection)
            if await store.get(relationship_id) is None:
                raise _not_found(relationship_id)
            _, _, projection = await self._validated(
                store, RelationshipDefinitionStore(uow.connection), relationship_id
            )
            return projection

    async def data_change(
        self,
        relationship_id: UUID,
        operations: tuple[DataChangeOperation, ...],
    ) -> RelationshipProjection:
        property_names = [operation.property for operation in operations]
        if (
            not operations
            or len(set(property_names)) != len(property_names)
            or any(
                operation.op is DataChangeKind.REMOVE and operation.value is not None
                for operation in operations
            )
        ):
            raise ApplicationFailure(
                FailureClass.INVALID_REQUEST,
                "invalid_request",
                "The Relationship data-change operation set is malformed.",
            )
        async with self._uow_factory() as uow:
            store = RuntimeRelationshipStore(uow.connection)
            if await store.get_header(relationship_id) is None:
                raise _not_found(relationship_id)
            plan = await prepare_lock_plan(
                uow.connection,
                intents=(_relationship_mutation_intent(relationship_id),),
            )
            if await acquire_lock_plan(uow.connection, plan):
                raise _not_found(relationship_id)
            before, _, before_projection = await self._validated(
                store, RelationshipDefinitionStore(uow.connection), relationship_id
            )
            schema = await self._relationship_schema(
                RelationshipDefinitionVersionStore(uow.connection),
                before.relationship_definition_id,
                before.relationship_definition_version,
                require_published=False,
            )
            try:
                properties = apply_data_change(
                    before.properties,
                    operations,
                    tuple(item.runtime for item in schema),
                )
            except (ObjectValidationError, PrimitiveValidationError) as error:
                raise ApplicationFailure(
                    FailureClass.SEMANTIC_VALIDATION,
                    "semantic_validation_failed",
                    "The Relationship property candidate is not semantically valid.",
                    {
                        "violations": [
                            {
                                "path": getattr(error, "path", "properties"),
                                "rule": getattr(error, "rule", "invalid_value"),
                            }
                        ]
                    },
                ) from error
            if properties == before.properties:
                views = await LifecycleStore(uow.connection).relationship_views(before)
                return RelationshipProjection(
                    before_projection.id,
                    before_projection.relationship_definition_id,
                    before_projection.relationship_definition_version,
                    before_projection.properties,
                    _projected_views(views),
                )
            after = Relationship(
                before.id,
                before.relationship_definition_id,
                before.resolutions,
                before.relationship_definition_version,
                properties,
            )
            plan.begin_dml()
            await store.update_properties(relationship_id, properties)
            lifecycle = LifecycleStore(uow.connection)
            views = await lifecycle.relationship_views(after)
            projected_views = _projected_views(views)
            await lifecycle.insert_relationship_events(
                kind=EventKind.RELATIONSHIP_DATA_CHANGE,
                before=before,
                after=after,
                views=views,
            )
            await uow.commit()
            return RelationshipProjection(
                after.id,
                after.relationship_definition_id,
                after.relationship_definition_version,
                after.properties,
                projected_views,
            )

    async def schema_change(
        self, relationship_id: UUID, target_version: int
    ) -> RelationshipProjection:
        if isinstance(target_version, bool) or target_version <= 0:
            raise _invalid_schema_target("positive_required")

        async def attempt(uow: Any, attempt_number: int) -> RelationshipProjection:
            del attempt_number
            return await self._schema_change_attempt(
                uow, relationship_id, target_version
            )

        try:
            return await run_semantic_uow_attempts(self._uow_factory, attempt)
        except LockPlanAttemptsExhausted as error:
            raise _internal(
                "The Relationship schema-change lock plan did not stabilize."
            ) from error

    async def _schema_change_attempt(
        self, uow: Any, relationship_id: UUID, target_version: int
    ) -> RelationshipProjection:
        store = RuntimeRelationshipStore(uow.connection)
        discovered = await store.get_header(relationship_id)
        if discovered is None:
            raise _not_found(relationship_id)
        if target_version <= discovered.relationship_definition_version:
            raise _invalid_schema_target("forward_version_required")
        definition_store = RelationshipDefinitionStore(uow.connection)
        definition = await definition_store.get(discovered.relationship_definition_id)
        if definition is None:
            raise _internal("A factual Relationship has no current Definition.")
        version_store = RelationshipDefinitionVersionStore(uow.connection)
        target = await version_store.get_version(definition.id, target_version)
        if target is None:
            raise _referenced_version(definition.id, target_version)
        if target.status is not VersionStatus.PUBLISHED:
            raise _dependency_not_admissible(definition.id, target_version)
        intents = (
            RowLockIntent(
                RowLockKey(RowLockClass.RELATIONSHIP_DEFINITION_HEADER, definition.id),
                RowLockMode.KS,
            ),
            _definition_version_intent(definition.id, target_version),
            _relationship_mutation_intent(relationship_id),
        )
        plan = await prepare_lock_plan(uow.connection, intents=intents)
        missing = await acquire_lock_plan(uow.connection, plan)
        if RowLockKey(RowLockClass.RELATIONSHIP, relationship_id) in missing:
            raise _not_found(relationship_id)
        if (
            RowLockKey(
                RowLockClass.RELATIONSHIP_DEFINITION_VERSION,
                definition.id,
                target_version,
            )
            in missing
        ):
            raise _referenced_version(definition.id, target_version)
        before, _, _ = await self._validated(store, definition_store, relationship_id)
        fresh_intents = (
            RowLockIntent(
                RowLockKey(
                    RowLockClass.RELATIONSHIP_DEFINITION_HEADER,
                    before.relationship_definition_id,
                ),
                RowLockMode.KS,
            ),
            _definition_version_intent(
                before.relationship_definition_id, target_version
            ),
            _relationship_mutation_intent(relationship_id),
        )
        plan.require_same_plan(fresh_intents)
        if before.relationship_definition_id != definition.id:
            raise _internal(
                "A factual Relationship changed Definition identity unexpectedly."
            )
        if target_version <= before.relationship_definition_version:
            raise _invalid_schema_target("forward_version_required")
        target = await version_store.get_version(definition.id, target_version)
        if target is None:
            raise _referenced_version(definition.id, target_version)
        if target.status is not VersionStatus.PUBLISHED:
            raise _dependency_not_admissible(definition.id, target_version)
        try:
            validate_relationship_property_history(
                target,
                tuple(
                    version
                    for version in await version_store.published_history(definition.id)
                    if version.version < target.version
                ),
            )
        except RelationshipDefinitionValidationError as error:
            raise _internal(
                "The persisted Relationship schema history is invalid."
            ) from error
        source_schema = await self._relationship_schema(
            version_store,
            definition.id,
            before.relationship_definition_version,
            require_published=False,
        )
        target_schema = await self._relationship_schema(
            version_store,
            definition.id,
            target_version,
            require_published=True,
        )
        try:
            properties = migrate_relationship_properties(
                before.properties, source_schema, target_schema
            )
        except RelationshipSchemaChangeBlocked as error:
            raise _schema_change_blocked(
                relationship_id, target_version, error.property_name
            ) from error
        except (ObjectValidationError, RelationshipValidationError) as error:
            raise _internal(
                "The persisted Relationship schema history is invalid."
            ) from error
        after = Relationship(
            before.id,
            before.relationship_definition_id,
            before.resolutions,
            target_version,
            properties,
        )
        plan.begin_dml()
        try:
            await store.update_schema(
                relationship_id, definition.id, target_version, properties
            )
        except RuntimeRelationshipModelReferenceError as error:
            raise _internal(
                "The locked Relationship schema target disappeared."
            ) from error
        lifecycle = LifecycleStore(uow.connection)
        views = await lifecycle.relationship_views(after)
        projected_views = _projected_views(views)
        await lifecycle.insert_relationship_events(
            kind=EventKind.RELATIONSHIP_SCHEMA_CHANGE,
            before=before,
            after=after,
            views=views,
        )
        await uow.commit()
        return RelationshipProjection(
            after.id,
            after.relationship_definition_id,
            after.relationship_definition_version,
            after.properties,
            projected_views,
        )

    async def delete(self, relationship_id: UUID) -> None:
        async with self._uow_factory() as uow:
            store = RuntimeRelationshipStore(uow.connection)
            plan = await prepare_lock_plan(
                uow.connection, intents=(_relationship_intent(relationship_id),)
            )
            if await acquire_lock_plan(uow.connection, plan):
                raise _not_found(relationship_id)
            relationship, _, _ = await self._validated(
                store, RelationshipDefinitionStore(uow.connection), relationship_id
            )
            lifecycle = LifecycleStore(uow.connection)
            lifecycle_views = await lifecycle.relationship_views(relationship)
            plan.begin_dml()
            await store.delete(relationship_id)
            await lifecycle.insert_relationship_events(
                kind=EventKind.RELATIONSHIP_DELETED,
                before=relationship,
                after=None,
                views=lifecycle_views,
            )
            await uow.commit()

    async def list_for_object(
        self,
        object_id: UUID,
        *,
        relationship_definition_id: UUID | None,
        name: str | None,
        cursor: str | None,
        limit: int,
    ) -> Page[ObjectRelationshipView]:
        filters: dict[str, JsonValue] = {
            "object_id": str(object_id),
            "relationship_definition_id": (
                None
                if relationship_definition_id is None
                else str(relationship_definition_id)
            ),
            "name": name,
        }
        after: tuple[UUID, UUID, str] | None = None
        if cursor is not None:
            key = decode_cursor(cursor, "object_relationships", filters)
            if (
                len(key) != 3
                or not isinstance(key[0], str)
                or not isinstance(key[1], str)
                or not isinstance(key[2], str)
            ):
                raise ApplicationFailure(
                    FailureClass.INVALID_REQUEST,
                    "invalid_cursor",
                    "The cursor is malformed or incompatible with this query.",
                )
            try:
                after = (UUID(key[0]), UUID(key[1]), key[2])
            except ValueError as error:
                raise ApplicationFailure(
                    FailureClass.INVALID_REQUEST,
                    "invalid_cursor",
                    "The cursor is malformed or incompatible with this query.",
                ) from error

        async with self._uow_factory() as uow:
            store = RuntimeRelationshipStore(uow.connection)
            try:
                projection = await store.list_object_views(
                    object_id,
                    relationship_definition_id=relationship_definition_id,
                    name=name,
                    after=after,
                    limit=limit + 1,
                )
            except RuntimeError as error:
                raise _internal(
                    "The persisted factual Relationship page is invalid."
                ) from error
            if not projection.target_exists:
                raise ApplicationFailure(
                    FailureClass.NOT_FOUND,
                    "resource_not_found",
                    "The requested Object does not exist.",
                    {"resource_type": "object", "id": str(object_id)},
                )
            rows = list(projection.items)
        more = len(rows) > limit
        items = rows[:limit]
        next_cursor = (
            encode_cursor(
                "object_relationships",
                filters,
                [
                    str(items[-1].relationship_id),
                    str(items[-1].destination_object_id),
                    items[-1].name,
                ],
            )
            if more
            else None
        )
        return Page(items, next_cursor)
