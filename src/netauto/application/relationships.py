"""Factual Relationship application capability and semantic projections."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import NoReturn
from uuid import UUID, uuid4

from netauto.application.cursors import Page, decode_cursor, encode_cursor
from netauto.domain.datatypes import VersionStatus
from netauto.domain.objects import (
    ObjectValidationError,
    RuntimePropertySpec,
    canonicalize_properties,
)
from netauto.domain.primitives import JsonValue, PrimitiveValidationError
from netauto.domain.relationships import (
    ObjectRelationshipView,
    Relationship,
    RelationshipDefinition,
    RelationshipDefinitionValidationError,
    RelationshipValidationError,
    RelationshipView,
    RuntimeRelationshipResolution,
    derive_runtime_closure,
    relationship_views,
    validate_definition,
    validate_lineage_graph,
    validate_relationship,
    validate_relationship_definition_version,
)
from netauto.failures import ApplicationFailure, FailureClass
from netauto.persistence.datatypes import DataTypeStore
from netauto.persistence.locking import (
    MAX_SEMANTIC_UOW_ATTEMPTS,
    RowLockClass,
    RowLockIntent,
    RowLockKey,
    RowLockMode,
    acquire_lock_plan,
    prepare_lock_plan,
)
from netauto.persistence.objects import EventKind, ObjectStore
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


def _relationship_lifetime_intent(relationship_id: UUID) -> RowLockIntent:
    return RowLockIntent(
        RowLockKey(RowLockClass.RELATIONSHIP, relationship_id), RowLockMode.KS
    )


class RelationshipService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def _relationship_specs(
        self,
        version_store: RelationshipDefinitionVersionStore,
        definition_id: UUID,
        version: int,
        *,
        require_published: bool,
    ) -> tuple[RuntimePropertySpec, ...]:
        exact = await version_store.get_version(definition_id, version)
        if exact is None:
            raise _internal("A factual Relationship exact schema is missing.")
        try:
            validate_relationship_definition_version(exact)
        except RelationshipDefinitionValidationError as error:
            raise _internal(
                "A persisted RelationshipDefinitionVersion is invalid."
            ) from error
        if require_published and exact.status is not VersionStatus.PUBLISHED:
            raise _dependency_not_admissible(definition_id, version)
        if exact.status is VersionStatus.DRAFT:
            raise _internal("A factual Relationship is pinned to a DRAFT schema.")
        datatype_store = DataTypeStore(version_store.connection)
        datatypes = await datatype_store.get_versions(
            tuple(
                (item.datatype_id, item.datatype_version) for item in exact.properties
            )
        )
        specs: list[RuntimePropertySpec] = []
        for item in exact.properties:
            datatype = datatypes.get((item.datatype_id, item.datatype_version))
            if datatype is None or datatype.status is VersionStatus.DRAFT:
                raise _internal("A Relationship property dependency is invalid.")
            if (
                exact.status is VersionStatus.PUBLISHED
                and datatype.status is not VersionStatus.PUBLISHED
            ):
                raise _internal("An active Relationship dependency is not PUBLISHED.")
            specs.append(
                RuntimePropertySpec(
                    item.name,
                    item.value_mode,
                    False,
                    datatype.base_type,
                    datatype.constraints,
                )
            )
        return tuple(specs)

    async def _validated(
        self,
        store: RuntimeRelationshipStore,
        definition_store: RelationshipDefinitionStore,
        relationship_id: UUID,
        *,
        restart_if_missing: bool = False,
    ) -> tuple[Relationship, RelationshipDefinition, RelationshipProjection]:
        value = await store.get(relationship_id)
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
                    lifecycle_views = await store.lifecycle_views(relationship.id)
                    expected = relationship_views(relationship, definition)
                    if {
                        (
                            item.object_id,
                            item.destination_object_id,
                            item.relationship_name,
                        )
                        for item in lifecycle_views
                    } != {
                        (item.object_id, item.destination_object_id, item.name)
                        for item in expected
                    }:
                        raise _internal(
                            "The Relationship lifecycle metadata projection is "
                            "incomplete."
                        )
                    await store.insert_lifecycle_events(
                        kind=EventKind.RELATIONSHIP_CREATED.value,
                        relationship=relationship,
                        views=lifecycle_views,
                    )
                    await uow.commit()
                    return RelationshipCreateResult(
                        RelationshipProjection(
                            relationship.id,
                            relationship.relationship_definition_id,
                            relationship.relationship_definition_version,
                            relationship.properties,
                            expected,
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

    async def delete(self, relationship_id: UUID) -> None:
        async with self._uow_factory() as uow:
            store = RuntimeRelationshipStore(uow.connection)
            plan = await prepare_lock_plan(
                uow.connection, intents=(_relationship_intent(relationship_id),)
            )
            if await acquire_lock_plan(uow.connection, plan):
                raise _not_found(relationship_id)
            relationship, definition, _ = await self._validated(
                store, RelationshipDefinitionStore(uow.connection), relationship_id
            )
            lifecycle_views = await store.lifecycle_views(relationship_id)
            expected = relationship_views(relationship, definition)
            if {
                (item.object_id, item.destination_object_id, item.relationship_name)
                for item in lifecycle_views
            } != {
                (item.object_id, item.destination_object_id, item.name)
                for item in expected
            }:
                raise _internal(
                    "The Relationship lifecycle metadata projection is incomplete."
                )
            plan.begin_dml()
            await store.delete(relationship_id)
            await store.insert_lifecycle_events(
                kind=EventKind.RELATIONSHIP_DELETED.value,
                relationship=relationship,
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

        async with self._uow_factory.coherent_read() as uow:
            if await ObjectStore(uow.connection).get(object_id) is None:
                raise ApplicationFailure(
                    FailureClass.NOT_FOUND,
                    "resource_not_found",
                    "The requested Object does not exist.",
                    {"resource_type": "object", "id": str(object_id)},
                )
            store = RuntimeRelationshipStore(uow.connection)
            rows = list(
                await store.list_object_views(
                    object_id,
                    relationship_definition_id=relationship_definition_id,
                    name=name,
                    after=after,
                    limit=limit + 1,
                )
            )
            definition_store = RelationshipDefinitionStore(uow.connection)
            for relationship_id in {item.relationship_id for item in rows}:
                await self._validated(store, definition_store, relationship_id)
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
