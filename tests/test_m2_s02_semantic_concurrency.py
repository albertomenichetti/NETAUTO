"""Deterministic real-PostgreSQL M2-S02 Relationship scenarios."""

import asyncio
from collections.abc import Awaitable, Callable, Iterable, Sequence
from datetime import datetime
from functools import partial
from types import ModuleType
from typing import cast
from uuid import UUID

import pytest
from sqlalchemy import Engine, event, func, select
from sqlalchemy.ext.asyncio import AsyncConnection

import netauto.application.relationshipdefinitions as definition_application
import netauto.application.relationships as relationship_application
from netauto.application.cursors import Page
from netauto.application.objects import ObjectService
from netauto.application.objecttemplates import ObjectTemplateService
from netauto.application.relationshipdefinitions import RelationshipDefinitionService
from netauto.application.relationships import (
    RelationshipProjection,
    RelationshipService,
)
from netauto.domain.datatypes import VersionStatus
from netauto.domain.objects import DataChangeKind, DataChangeOperation, Object
from netauto.domain.objecttemplates import ValueMode
from netauto.domain.primitives import JsonValue
from netauto.domain.relationships import (
    Relationship,
    RelationshipDefinition,
    RelationshipDefinitionProperty,
    RelationshipDefinitionVersion,
    RelationshipLifecycleView,
    RelationshipPerspective,
    RelationshipPropertyCandidate,
    ResolutionRename,
)
from netauto.failures import ApplicationFailure, FailureClass
from netauto.persistence.lifecycle import (
    EventKind,
    LifecycleStore,
    RelationshipLifecycleEvent,
)
from netauto.persistence.locking import (
    AdvisoryGate,
    LockPlan,
    RowLockClass,
    RowLockKey,
    RowLockMode,
)
from netauto.persistence.metadata import (
    object_lifecycle_events,
    relationships,
    runtime_relationship_resolutions,
)
from netauto.persistence.relationships import (
    RelationshipDefinitionStore,
    RelationshipDefinitionVersionStore,
    RuntimeRelationshipStore,
)
from netauto.persistence.uow import UnitOfWorkFactory
from tests.support.semantic_concurrency import (
    ObservedUnitOfWorkFactory,
    PhaseCut,
    SemanticActors,
    blocked_race,
    install_lock_plan_cut,
    progress_race,
    run_worker,
    semantic_actors,
)

type Operation = Callable[[], Awaitable[object]]
type AcquireLockPlan = Callable[
    [AsyncConnection, LockPlan], Awaitable[tuple[RowLockKey, ...]]
]


class RelationshipSeed:
    def __init__(
        self,
        definition: RelationshipDefinition,
        first_object: Object,
        second_object: Object,
    ) -> None:
        self.definition = definition
        self.first_object = first_object
        self.second_object = second_object

    @property
    def first_resolution_id(self) -> UUID:
        return next(
            item.id
            for item in self.definition.resolutions
            if item.from_template_id == self.first_object.template_id
        )


async def _property_seed(
    actors: SemanticActors,
    prefix: str,
    *,
    versions: int = 1,
    property_count: int = 1,
) -> RelationshipSeed:
    factory = UnitOfWorkFactory(actors.t1_engine)
    datatype = await actors.t1.create(
        "relationship_s02", f"{prefix}_integer", "core.integer", None, {}
    )
    await actors.t1.publish(datatype.datatype.id, 1, 1)
    templates = ObjectTemplateService(factory)
    first_template = await templates.create(
        "relationship_s02", f"{prefix}_first", False, None, None, None, (), ()
    )
    second_template = await templates.create(
        "relationship_s02", f"{prefix}_second", False, None, None, None, (), ()
    )
    await templates.publish(first_template.object_template.id, 1, 1)
    await templates.publish(second_template.object_template.id, 1, 1)
    objects = ObjectService(factory)
    first_object = await objects.create(
        first_template.object_template.id, 1, f"{prefix}-first", {}
    )
    second_object = await objects.create(
        second_template.object_template.id, 1, f"{prefix}-second", {}
    )
    candidates = tuple(
        RelationshipPropertyCandidate(
            "metric" if position == 1 else "other",
            position,
            datatype.datatype.id,
            1,
            ValueMode.SCALAR,
        )
        for position in range(1, property_count + 1)
    )
    definitions = RelationshipDefinitionService(factory)
    created = await definitions.create_non_symmetric(
        (
            RelationshipPerspective(
                first_template.object_template.id, f"{prefix}_contains"
            ),
            RelationshipPerspective(
                second_template.object_template.id, f"{prefix}_contained_by"
            ),
        ),
        candidates,
    )
    await definitions.publish(created.relationship_definition.id, 1, 1)
    for version in range(2, versions + 1):
        await definitions.create_next(created.relationship_definition.id, version - 1)
        await definitions.publish(created.relationship_definition.id, version, 1)
    return RelationshipSeed(
        created.relationship_definition, first_object, second_object
    )


async def _symmetric_property_seed(
    actors: SemanticActors,
    prefix: str,
    *,
    self_loop: bool,
    inheritance_overlap: bool,
) -> RelationshipSeed:
    factory = UnitOfWorkFactory(actors.t1_engine)
    datatype = await actors.t1.create(
        "relationship_s02", f"{prefix}_integer", "core.integer", None, {}
    )
    await actors.t1.publish(datatype.datatype.id, 1, 1)
    templates = ObjectTemplateService(factory)
    root = await templates.create(
        "relationship_s02", f"{prefix}_root", False, None, None, None, (), ()
    )
    await templates.publish(root.object_template.id, 1, 1)
    endpoint_template_id = root.object_template.id
    definition_templates = (endpoint_template_id, endpoint_template_id)
    if inheritance_overlap:
        child = await templates.create(
            "relationship_s02",
            f"{prefix}_child",
            False,
            None,
            root.object_template.id,
            None,
            (),
            (),
        )
        await templates.publish(child.object_template.id, 1, 1)
        endpoint_template_id = child.object_template.id
        definition_templates = (root.object_template.id, child.object_template.id)
    objects = ObjectService(factory)
    first_object = await objects.create(endpoint_template_id, 1, f"{prefix}-first", {})
    second_object = (
        first_object
        if self_loop
        else await objects.create(endpoint_template_id, 1, f"{prefix}-second", {})
    )
    definitions = RelationshipDefinitionService(factory)
    created = await definitions.create_symmetric(
        definition_templates,
        f"{prefix}_linked",
        (
            RelationshipPropertyCandidate(
                "metric", 1, datatype.datatype.id, 1, ValueMode.SCALAR
            ),
        ),
    )
    await definitions.publish(created.relationship_definition.id, 1, 1)
    await definitions.create_next(created.relationship_definition.id, 1)
    await definitions.publish(created.relationship_definition.id, 2, 1)
    return RelationshipSeed(
        created.relationship_definition, first_object, second_object
    )


def _services(
    actors: SemanticActors,
) -> tuple[RelationshipService, RelationshipService]:
    return (
        RelationshipService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        ),
        RelationshipService(
            ObservedUnitOfWorkFactory(actors.t2_engine, actors.tracker, "T2")
        ),
    )


def _reader(actors: SemanticActors) -> RelationshipService:
    return RelationshipService(UnitOfWorkFactory(actors.t1_engine))


async def _event_kinds(actors: SemanticActors, relationship_id: UUID) -> list[str]:
    async with actors.t1_engine.connect() as connection:
        values = await connection.scalars(
            select(object_lifecycle_events.c.kind).where(
                object_lifecycle_events.c.relationship_id == relationship_id
            )
        )
        return list(values)


async def _closure_keys(
    actors: SemanticActors, relationship_id: UUID
) -> tuple[tuple[UUID, UUID, UUID], ...]:
    async with actors.t1_engine.connect() as connection:
        rows = await connection.execute(
            select(
                runtime_relationship_resolutions.c.resolution_id,
                runtime_relationship_resolutions.c.from_object_id,
                runtime_relationship_resolutions.c.to_object_id,
            )
            .where(
                runtime_relationship_resolutions.c.relationship_id == relationship_id
            )
            .order_by(
                runtime_relationship_resolutions.c.resolution_id,
                runtime_relationship_resolutions.c.from_object_id,
                runtime_relationship_resolutions.c.to_object_id,
            )
        )
        return tuple((row[0], row[1], row[2]) for row in rows)


async def _transition_history(
    actors: SemanticActors, relationship_id: UUID
) -> list[tuple[datetime, str, object, object]]:
    async with actors.t1_engine.connect() as connection:
        rows = (
            await connection.execute(
                select(
                    object_lifecycle_events.c.occurred_at,
                    object_lifecycle_events.c.kind,
                    object_lifecycle_events.c.before_state,
                    object_lifecycle_events.c.after_state,
                )
                .where(
                    object_lifecycle_events.c.relationship_id == relationship_id,
                    object_lifecycle_events.c.kind.in_(
                        (
                            EventKind.RELATIONSHIP_DATA_CHANGE.value,
                            EventKind.RELATIONSHIP_SCHEMA_CHANGE.value,
                        )
                    ),
                )
                .order_by(
                    object_lifecycle_events.c.occurred_at,
                    object_lifecycle_events.c.id,
                )
            )
        ).all()
    result: list[tuple[datetime, str, object, object]] = []
    for row in rows:
        transition = (row.occurred_at, row.kind, row.before_state, row.after_state)
        if result and result[-1] == transition:
            continue
        fanout = [
            item
            for item in rows
            if (item.occurred_at, item.kind) == (row.occurred_at, row.kind)
        ]
        assert len(fanout) == 2
        assert all(
            item.before_state == row.before_state
            and item.after_state == row.after_state
            for item in fanout
        )
        result.append(transition)
    return result


def _observe_t2_lock_plan(
    monkeypatch: pytest.MonkeyPatch, application_module: ModuleType
) -> tuple[asyncio.Event, list[LockPlan]]:
    completed = asyncio.Event()
    plans: list[LockPlan] = []
    original = cast(AcquireLockPlan, application_module.acquire_lock_plan)

    async def intercepted(
        connection: AsyncConnection, plan: LockPlan
    ) -> tuple[RowLockKey, ...]:
        task = asyncio.current_task()
        if task is not None and task.get_name() == "T2":
            plans.append(plan)
        missing = await original(connection, plan)
        if task is not None and task.get_name() == "T2":
            completed.set()
        return missing

    monkeypatch.setattr(application_module, "acquire_lock_plan", intercepted)
    return completed, plans


def _capture_t1_lock_plans(
    monkeypatch: pytest.MonkeyPatch, application_module: ModuleType
) -> list[LockPlan]:
    plans: list[LockPlan] = []
    original = cast(AcquireLockPlan, application_module.acquire_lock_plan)

    async def intercepted(
        connection: AsyncConnection, plan: LockPlan
    ) -> tuple[RowLockKey, ...]:
        task = asyncio.current_task()
        if task is not None and task.get_name() == "T1":
            plans.append(plan)
        return await original(connection, plan)

    monkeypatch.setattr(application_module, "acquire_lock_plan", intercepted)
    return plans


def _assert_schema_waits_before_factual_owner(
    completed: asyncio.Event,
    plans: list[LockPlan],
    definition_id: UUID,
    target_version: int,
    relationship_id: UUID,
) -> None:
    assert not completed.is_set()
    assert len(plans) == 1
    keys = [intent.key for intent in plans[0].rows]
    assert keys.index(
        RowLockKey(
            RowLockClass.RELATIONSHIP_DEFINITION_VERSION,
            definition_id,
            target_version,
        )
    ) < keys.index(RowLockKey(RowLockClass.RELATIONSHIP, relationship_id))


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_26_data_changes_reread_fresh_state_and_waiter_can_be_noop(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-26") as actors:
        seed = await _property_seed(actors, "row26", property_count=2)
        reader = _reader(actors)
        created = await reader.create(
            seed.first_resolution_id,
            seed.first_object.id,
            seed.second_object.id,
            1,
            {"metric": 0, "other": 0},
        )
        closure_before = await _closure_keys(actors, created.relationship.id)
        first, second = _services(actors)
        with monkeypatch.context() as context:
            cut = install_lock_plan_cut(
                context,
                relationship_application,
                RowLockClass.RELATIONSHIP,
                RowLockMode.NKU,
            )
            outcomes = await blocked_race(
                actors,
                cut,
                lambda: first.data_change(
                    created.relationship.id,
                    (DataChangeOperation(DataChangeKind.SET, "metric", 1),),
                ),
                lambda: second.data_change(
                    created.relationship.id,
                    (DataChangeOperation(DataChangeKind.SET, "other", 2),),
                ),
            )
        assert isinstance(outcomes[0], RelationshipProjection)
        assert outcomes[0].relationship_definition_version == 1
        assert outcomes[0].properties == {"metric": 1, "other": 0}
        assert isinstance(outcomes[1], RelationshipProjection)
        assert outcomes[1].relationship_definition_version == 1
        assert outcomes[1].properties == {"metric": 1, "other": 2}
        before_count = (await _event_kinds(actors, created.relationship.id)).count(
            EventKind.RELATIONSHIP_DATA_CHANGE.value
        )
        update_calls = 0
        original_update = RuntimeRelationshipStore.update_properties

        async def counted_update(
            store: RuntimeRelationshipStore,
            relationship_id: UUID,
            properties: dict[str, JsonValue],
        ) -> None:
            nonlocal update_calls
            update_calls += 1
            await original_update(store, relationship_id, properties)

        with monkeypatch.context() as context:
            context.setattr(
                RuntimeRelationshipStore, "update_properties", counted_update
            )
            cut = install_lock_plan_cut(
                context,
                relationship_application,
                RowLockClass.RELATIONSHIP,
                RowLockMode.NKU,
            )
            outcomes = await blocked_race(
                actors,
                cut,
                lambda: first.data_change(
                    created.relationship.id,
                    (DataChangeOperation(DataChangeKind.SET, "metric", 3),),
                ),
                lambda: second.data_change(
                    created.relationship.id,
                    (DataChangeOperation(DataChangeKind.SET, "metric", 3),),
                ),
            )
        after_count = (await _event_kinds(actors, created.relationship.id)).count(
            EventKind.RELATIONSHIP_DATA_CHANGE.value
        )
        assert after_count - before_count == 2
        assert update_calls == 1
        assert all(isinstance(item, RelationshipProjection) for item in outcomes)
        assert all(
            cast(RelationshipProjection, item).relationship_definition_version == 1
            and cast(RelationshipProjection, item).properties
            == {"metric": 3, "other": 2}
            for item in outcomes
        )
        current = await reader.get(created.relationship.id)
        assert current.relationship_definition_version == 1
        assert current.properties == {"metric": 3, "other": 2}
        assert await _closure_keys(actors, created.relationship.id) == closure_before
        history = await _transition_history(actors, created.relationship.id)
        assert [(kind, before, after) for _, kind, before, after in history] == [
            (
                EventKind.RELATIONSHIP_DATA_CHANGE.value,
                {
                    "relationship_definition_version": 1,
                    "properties": {"metric": 0, "other": 0},
                },
                {
                    "relationship_definition_version": 1,
                    "properties": {"metric": 1, "other": 0},
                },
            ),
            (
                EventKind.RELATIONSHIP_DATA_CHANGE.value,
                {
                    "relationship_definition_version": 1,
                    "properties": {"metric": 1, "other": 0},
                },
                {
                    "relationship_definition_version": 1,
                    "properties": {"metric": 1, "other": 2},
                },
            ),
            (
                EventKind.RELATIONSHIP_DATA_CHANGE.value,
                {
                    "relationship_definition_version": 1,
                    "properties": {"metric": 1, "other": 2},
                },
                {
                    "relationship_definition_version": 1,
                    "properties": {"metric": 3, "other": 2},
                },
            ),
        ]


@pytest.mark.postgresql
@pytest.mark.concurrency
@pytest.mark.parametrize("winner", ["data-first", "schema-first"])
async def test_row_27_data_and_schema_change_have_serial_factual_history(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
    winner: str,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, f"ROW-27-{winner}") as actors:
        seed = await _property_seed(
            actors, f"row27_{winner.replace('-', '_')}", versions=2
        )
        created = await _reader(actors).create(
            seed.first_resolution_id,
            seed.first_object.id,
            seed.second_object.id,
            1,
            {"metric": 0},
        )
        closure_before = await _closure_keys(actors, created.relationship.id)
        first, second = _services(actors)
        if winner == "schema-first":
            first_operation: Operation = partial(
                first.schema_change, created.relationship.id, 2
            )
            second_operation: Operation = partial(
                second.data_change,
                created.relationship.id,
                (DataChangeOperation(DataChangeKind.SET, "metric", 7),),
            )
        else:
            first_operation = partial(
                first.data_change,
                created.relationship.id,
                (DataChangeOperation(DataChangeKind.SET, "metric", 7),),
            )
            second_operation = partial(second.schema_change, created.relationship.id, 2)
        with monkeypatch.context() as context:
            cut = install_lock_plan_cut(
                context,
                relationship_application,
                RowLockClass.RELATIONSHIP,
                RowLockMode.NKU,
            )
            outcomes = await blocked_race(
                actors, cut, first_operation, second_operation
            )
        assert all(isinstance(item, RelationshipProjection) for item in outcomes)
        current = await _reader(actors).get(created.relationship.id)
        assert current.relationship_definition_version == 2
        assert current.properties == {"metric": 7}
        assert await _closure_keys(actors, created.relationship.id) == closure_before
        initial = {
            "relationship_definition_version": 1,
            "properties": {"metric": 0},
        }
        data_v1 = {
            "relationship_definition_version": 1,
            "properties": {"metric": 7},
        }
        schema_v2_before_data = {
            "relationship_definition_version": 2,
            "properties": {"metric": 0},
        }
        final = {
            "relationship_definition_version": 2,
            "properties": {"metric": 7},
        }
        expected = (
            [
                (
                    EventKind.RELATIONSHIP_SCHEMA_CHANGE.value,
                    initial,
                    schema_v2_before_data,
                ),
                (
                    EventKind.RELATIONSHIP_DATA_CHANGE.value,
                    schema_v2_before_data,
                    final,
                ),
            ]
            if winner == "schema-first"
            else [
                (EventKind.RELATIONSHIP_DATA_CHANGE.value, initial, data_v1),
                (EventKind.RELATIONSHIP_SCHEMA_CHANGE.value, data_v1, final),
            ]
        )
        history = await _transition_history(actors, created.relationship.id)
        assert [(kind, before, after) for _, kind, before, after in history] == expected


@pytest.mark.postgresql
@pytest.mark.concurrency
@pytest.mark.parametrize("winner", ["lower-first", "higher-first"])
async def test_row_28_schema_changes_recheck_forward_target_after_wait(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
    winner: str,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, f"ROW-28-{winner}") as actors:
        seed = await _property_seed(
            actors, f"row28_{winner.replace('-', '_')}", versions=3
        )
        created = await _reader(actors).create(
            seed.first_resolution_id,
            seed.first_object.id,
            seed.second_object.id,
            1,
            {"metric": 1},
        )
        closure_before = await _closure_keys(actors, created.relationship.id)
        first, second = _services(actors)
        with monkeypatch.context() as context:
            cut = install_lock_plan_cut(
                context,
                relationship_application,
                RowLockClass.RELATIONSHIP,
                RowLockMode.NKU,
            )
            outcomes = await blocked_race(
                actors,
                cut,
                lambda: first.schema_change(
                    created.relationship.id, 2 if winner == "lower-first" else 3
                ),
                lambda: second.schema_change(
                    created.relationship.id, 3 if winner == "lower-first" else 2
                ),
            )
        assert isinstance(outcomes[0], RelationshipProjection)
        if winner == "lower-first":
            assert isinstance(outcomes[1], RelationshipProjection)
        else:
            assert isinstance(outcomes[1], ApplicationFailure)
            assert outcomes[1].failure_class is FailureClass.SEMANTIC_VALIDATION
            assert outcomes[1].code == "semantic_validation_failed"
            assert outcomes[1].details == {
                "violations": [
                    {"path": "target_version", "rule": "forward_version_required"}
                ]
            }
        current = await _reader(actors).get(created.relationship.id)
        assert current.relationship_definition_version == 3
        assert current.properties == {"metric": 1}
        assert await _closure_keys(actors, created.relationship.id) == closure_before
        state_v1 = {
            "relationship_definition_version": 1,
            "properties": {"metric": 1},
        }
        state_v2 = {
            "relationship_definition_version": 2,
            "properties": {"metric": 1},
        }
        state_v3 = {
            "relationship_definition_version": 3,
            "properties": {"metric": 1},
        }
        expected = (
            [
                (EventKind.RELATIONSHIP_SCHEMA_CHANGE.value, state_v1, state_v2),
                (EventKind.RELATIONSHIP_SCHEMA_CHANGE.value, state_v2, state_v3),
            ]
            if winner == "lower-first"
            else [(EventKind.RELATIONSHIP_SCHEMA_CHANGE.value, state_v1, state_v3)]
        )
        history = await _transition_history(actors, created.relationship.id)
        assert [(kind, before, after) for _, kind, before, after in history] == expected


@pytest.mark.parametrize("mutation", ["data", "schema"])
@pytest.mark.parametrize("delete_first", [False, True])
@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_29_mutation_delete_both_winner_orders(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    delete_first: bool,
) -> None:
    del migrated_database_engine
    scenario = f"ROW-29-{mutation}-{delete_first}"
    async with semantic_actors(test_database_url, scenario) as actors:
        seed = await _property_seed(
            actors, scenario.lower().replace("-", "_"), versions=2
        )
        created = await _reader(actors).create(
            seed.first_resolution_id,
            seed.first_object.id,
            seed.second_object.id,
            1,
            {"metric": 0},
        )
        first, second = _services(actors)
        mutation_operation: Operation
        if mutation == "data":
            mutation_operation = partial(
                second.data_change,
                created.relationship.id,
                (DataChangeOperation(DataChangeKind.SET, "metric", 1),),
            )
        else:
            mutation_operation = partial(
                second.schema_change, created.relationship.id, 2
            )
        first_operation: Operation
        second_operation: Operation
        mode: RowLockMode
        if delete_first:
            first_operation = partial(first.delete, created.relationship.id)
            second_operation = mutation_operation
            mode = RowLockMode.U
        else:
            if mutation == "data":
                first_operation = partial(
                    first.data_change,
                    created.relationship.id,
                    (DataChangeOperation(DataChangeKind.SET, "metric", 1),),
                )
            else:
                first_operation = partial(
                    first.schema_change, created.relationship.id, 2
                )
            second_operation = partial(second.delete, created.relationship.id)
            mode = RowLockMode.NKU
        with monkeypatch.context() as context:
            cut = install_lock_plan_cut(
                context,
                relationship_application,
                RowLockClass.RELATIONSHIP,
                mode,
            )
            outcomes = await blocked_race(
                actors, cut, first_operation, second_operation
            )
        if delete_first:
            assert outcomes[0] is None
            assert isinstance(outcomes[1], ApplicationFailure)
            assert outcomes[1].code == "resource_not_found"
        else:
            assert not isinstance(outcomes[0], ApplicationFailure)
            assert outcomes[1] is None
        with pytest.raises(ApplicationFailure) as missing:
            await _reader(actors).get(created.relationship.id)
        assert missing.value.code == "resource_not_found"
        async with actors.t1_engine.connect() as connection:
            rows = (
                await connection.execute(
                    select(
                        object_lifecycle_events.c.kind,
                        object_lifecycle_events.c.before_state,
                        object_lifecycle_events.c.after_state,
                    ).where(
                        object_lifecycle_events.c.relationship_id
                        == created.relationship.id
                    )
                )
            ).all()
        mutation_kind = (
            EventKind.RELATIONSHIP_DATA_CHANGE.value
            if mutation == "data"
            else EventKind.RELATIONSHIP_SCHEMA_CHANGE.value
        )
        mutation_rows = [row for row in rows if row.kind == mutation_kind]
        deleted_rows = [
            row for row in rows if row.kind == EventKind.RELATIONSHIP_DELETED.value
        ]
        assert len(deleted_rows) == 2
        expected_deleted_before = {
            "relationship_definition_version": 2 if mutation == "schema" else 1,
            "properties": {"metric": 1 if mutation == "data" else 0},
        }
        if delete_first:
            assert mutation_rows == []
            expected_deleted_before = {
                "relationship_definition_version": 1,
                "properties": {"metric": 0},
            }
        else:
            assert len(mutation_rows) == 2
        assert all(
            row.before_state == expected_deleted_before and row.after_state is None
            for row in deleted_rows
        )


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_30_schema_change_first_blocks_target_deprecation(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-30-SCHEMA-FIRST") as actors:
        seed = await _property_seed(actors, "row30_schema_first", versions=2)
        created = await _reader(actors).create(
            seed.first_resolution_id,
            seed.first_object.id,
            seed.second_object.id,
            1,
            {"metric": 1},
        )
        closure_before = await _closure_keys(actors, created.relationship.id)
        first = RelationshipService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        )
        definitions = RelationshipDefinitionService(
            ObservedUnitOfWorkFactory(actors.t2_engine, actors.tracker, "T2")
        )
        with monkeypatch.context() as context:
            cut = install_lock_plan_cut(
                context,
                relationship_application,
                RowLockClass.RELATIONSHIP,
                RowLockMode.NKU,
            )
            t2_completed, t2_plans = _observe_t2_lock_plan(
                context, definition_application
            )

            async def observe_blocked(_: int, __: int) -> None:
                assert not t2_completed.is_set()
                assert len(t2_plans) == 1
                assert any(
                    intent.key
                    == RowLockKey(
                        RowLockClass.RELATIONSHIP_DEFINITION_VERSION,
                        seed.definition.id,
                        2,
                    )
                    and intent.mode is RowLockMode.NKU
                    for intent in t2_plans[0].rows
                )

            outcomes = await blocked_race(
                actors,
                cut,
                lambda: first.schema_change(created.relationship.id, 2),
                lambda: definitions.deprecate(seed.definition.id, 2),
                observe_blocked=observe_blocked,
            )
        assert isinstance(outcomes[0], RelationshipProjection)
        assert outcomes[0].relationship_definition_version == 2
        assert outcomes[0].properties == {"metric": 1}
        assert isinstance(outcomes[1], RelationshipDefinitionVersion)
        assert outcomes[1].status is VersionStatus.DEPRECATED
        current = await _reader(actors).get(created.relationship.id)
        assert current.relationship_definition_version == 2
        assert current.properties == {"metric": 1}
        assert await _closure_keys(actors, created.relationship.id) == closure_before
        history = await _transition_history(actors, created.relationship.id)
        assert [(kind, before, after) for _, kind, before, after in history] == [
            (
                EventKind.RELATIONSHIP_SCHEMA_CHANGE.value,
                {
                    "relationship_definition_version": 1,
                    "properties": {"metric": 1},
                },
                {
                    "relationship_definition_version": 2,
                    "properties": {"metric": 1},
                },
            )
        ]


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_30_target_deprecation_first_blocks_schema_change(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-30-DEPRECATE-FIRST") as actors:
        seed = await _property_seed(actors, "row30_deprecate_first", versions=2)
        created = await _reader(actors).create(
            seed.first_resolution_id,
            seed.first_object.id,
            seed.second_object.id,
            1,
            {"metric": 1},
        )
        closure_before = await _closure_keys(actors, created.relationship.id)
        definitions = RelationshipDefinitionService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        )
        writer = RelationshipService(
            ObservedUnitOfWorkFactory(actors.t2_engine, actors.tracker, "T2")
        )
        with monkeypatch.context() as context:
            cut = install_lock_plan_cut(
                context,
                definition_application,
                RowLockClass.RELATIONSHIP_DEFINITION_VERSION,
                RowLockMode.NKU,
            )
            t2_completed, t2_plans = _observe_t2_lock_plan(
                context, relationship_application
            )

            async def observe_blocked(_: int, __: int) -> None:
                _assert_schema_waits_before_factual_owner(
                    t2_completed,
                    t2_plans,
                    seed.definition.id,
                    2,
                    created.relationship.id,
                )

            outcomes = await blocked_race(
                actors,
                cut,
                lambda: definitions.deprecate(seed.definition.id, 2),
                lambda: writer.schema_change(created.relationship.id, 2),
                observe_blocked=observe_blocked,
            )
        assert isinstance(outcomes[0], RelationshipDefinitionVersion)
        assert outcomes[0].status is VersionStatus.DEPRECATED
        assert isinstance(outcomes[1], ApplicationFailure)
        assert outcomes[1].failure_class is FailureClass.STATE_CONFLICT
        assert outcomes[1].code == "dependency_not_admissible"
        assert outcomes[1].details == {"id": str(seed.definition.id), "version": 2}
        current = await _reader(actors).get(created.relationship.id)
        assert current.relationship_definition_version == 1
        assert current.properties == {"metric": 1}
        assert await _closure_keys(actors, created.relationship.id) == closure_before
        assert await _transition_history(actors, created.relationship.id) == []


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_30_definition_default_change_is_independent(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-30-DEFAULT") as actors:
        seed = await _property_seed(actors, "row30_default", versions=2)
        created = await _reader(actors).create(
            seed.first_resolution_id,
            seed.first_object.id,
            seed.second_object.id,
            1,
            {"metric": 1},
        )
        first = RelationshipService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        )
        definitions = RelationshipDefinitionService(
            ObservedUnitOfWorkFactory(actors.t2_engine, actors.tracker, "T2")
        )
        with monkeypatch.context() as context:
            cut = install_lock_plan_cut(
                context,
                relationship_application,
                RowLockClass.RELATIONSHIP,
                RowLockMode.NKU,
            )
            schema_outcome, default_outcome = await progress_race(
                cut,
                lambda: first.schema_change(created.relationship.id, 2),
                lambda: definitions.clear_default(seed.definition.id),
            )
        assert isinstance(schema_outcome, RelationshipProjection)
        assert schema_outcome.relationship_definition_version == 2
        assert isinstance(default_outcome, RelationshipDefinition)
        assert default_outcome.default_version is None


@pytest.mark.postgresql
async def test_object_relationship_page_batches_only_represented_definitions(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "S02-PAGE-BATCH") as actors:
        factory = UnitOfWorkFactory(actors.t1_engine)
        templates = ObjectTemplateService(factory)
        template = await templates.create(
            "relationship_s02", "page_batch_endpoint", False, None, None, None, (), ()
        )
        await templates.publish(template.object_template.id, 1, 1)
        objects_service = ObjectService(factory)
        source = await objects_service.create(
            template.object_template.id, 1, "page-batch-source", {}
        )
        destinations = tuple(
            [
                await objects_service.create(
                    template.object_template.id,
                    1,
                    f"page-batch-destination-{index}",
                    {},
                )
                for index in range(3)
            ]
        )
        definitions_service = RelationshipDefinitionService(factory)
        reader = RelationshipService(factory)
        represented_definition_ids: set[UUID] = set()
        relationship_ids: set[UUID] = set()
        all_definition_ids: set[UUID] = set()
        for index in range(5):
            definition = await definitions_service.create_symmetric(
                (template.object_template.id, template.object_template.id),
                f"page_batch_link_{index}",
                (),
            )
            definition_id = definition.relationship_definition.id
            all_definition_ids.add(definition_id)
            await definitions_service.publish(definition_id, 1, 1)
            if index < len(destinations):
                represented_definition_ids.add(definition_id)
                relationship = await reader.create(
                    definition.relationship_definition.resolutions[0].id,
                    source.id,
                    destinations[index].id,
                    1,
                    {},
                )
                relationship_ids.add(relationship.relationship.id)

        statements: list[str] = []
        loaded_definition_sets: list[set[UUID]] = []
        parent_graph_calls = 0
        original_get_many = RelationshipDefinitionStore.get_many
        original_lineage_parents = RelationshipDefinitionStore.lineage_parents

        def observe_statement(
            connection: object,
            cursor: object,
            statement: str,
            parameters: object,
            context: object,
            executemany: bool,
        ) -> None:
            del connection, cursor, parameters, context, executemany
            statements.append(statement.lower())

        async def observed_get_many(
            store: RelationshipDefinitionStore, definition_ids: Iterable[UUID]
        ) -> dict[UUID, RelationshipDefinition]:
            requested = set(definition_ids)
            loaded_definition_sets.append(requested)
            return await original_get_many(store, requested)

        async def forbidden_certified_set(
            store: RelationshipDefinitionStore,
        ) -> tuple[RelationshipDefinition, ...]:
            del store
            raise AssertionError("page reads must not load the certified global set")

        async def observed_lineage_parents(
            store: RelationshipDefinitionStore,
        ) -> dict[UUID, UUID | None]:
            nonlocal parent_graph_calls
            parent_graph_calls += 1
            return await original_lineage_parents(store)

        event.listen(
            actors.t1_engine.sync_engine,
            "before_cursor_execute",
            observe_statement,
        )
        try:
            async with actors.t1_engine.connect() as connection:
                assert await RelationshipDefinitionStore(connection).get_many(()) == {}
            assert statements == []
            with monkeypatch.context() as context:
                context.setattr(
                    RelationshipDefinitionStore, "get_many", observed_get_many
                )
                context.setattr(
                    RelationshipDefinitionStore,
                    "certified_set",
                    forbidden_certified_set,
                )
                context.setattr(
                    RelationshipDefinitionStore,
                    "lineage_parents",
                    observed_lineage_parents,
                )
                page = await reader.list_for_object(
                    source.id,
                    relationship_definition_id=None,
                    name=None,
                    cursor=None,
                    limit=10,
                )
        finally:
            event.remove(
                actors.t1_engine.sync_engine,
                "before_cursor_execute",
                observe_statement,
            )

        assert {item.relationship_id for item in page.items} == relationship_ids
        assert loaded_definition_sets == []
        assert represented_definition_ids < all_definition_ids
        assert parent_graph_calls == 0
        definition_statements = [
            statement
            for statement in statements
            if "from relationship_definitions" in statement
            and "relationship_resolutions" in statement
        ]
        assert definition_statements == []
        assert len(statements) == 1


@pytest.mark.postgresql
async def test_published_relationship_history_is_set_based_and_schema_change_uses_it(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "S02-HISTORY-BATCH") as actors:
        single = await _property_seed(actors, "history_batch_single")
        multiple = await _property_seed(actors, "history_batch_multiple", versions=4)
        reader = _reader(actors)
        relationship = await reader.create(
            multiple.first_resolution_id,
            multiple.first_object.id,
            multiple.second_object.id,
            1,
            {"metric": 1},
        )
        definitions = RelationshipDefinitionService(UnitOfWorkFactory(actors.t1_engine))
        await definitions.clear_default(multiple.definition.id)
        await definitions.deprecate(multiple.definition.id, 1)
        draft = await definitions.create_next(multiple.definition.id, 4)
        assert draft.version == 5
        assert draft.status is VersionStatus.DRAFT

        statements: list[str] = []

        def observe_statement(
            connection: object,
            cursor: object,
            statement: str,
            parameters: object,
            context: object,
            executemany: bool,
        ) -> None:
            del connection, cursor, parameters, context, executemany
            statements.append(statement.lower())

        async def forbidden_get_version(
            store: RelationshipDefinitionVersionStore,
            definition_id: UUID,
            version: int,
        ) -> RelationshipDefinitionVersion | None:
            del store, definition_id, version
            raise AssertionError("published history must not perform per-version reads")

        async def read_history(
            definition_id: UUID,
        ) -> tuple[
            list[
                tuple[
                    int,
                    VersionStatus,
                    tuple[RelationshipDefinitionProperty, ...],
                ]
            ],
            int,
        ]:
            statements.clear()
            async with actors.t1_engine.connect() as connection:
                values = await RelationshipDefinitionVersionStore(
                    connection
                ).published_history(definition_id)
            statement_count = len(statements)
            return (
                [(value.version, value.status, value.properties) for value in values],
                statement_count,
            )

        event.listen(
            actors.t1_engine.sync_engine,
            "before_cursor_execute",
            observe_statement,
        )
        try:
            with monkeypatch.context() as context:
                context.setattr(
                    RelationshipDefinitionVersionStore,
                    "get_version",
                    forbidden_get_version,
                )
                single_history, single_count = await read_history(single.definition.id)
                multiple_history, multiple_count = await read_history(
                    multiple.definition.id
                )
        finally:
            event.remove(
                actors.t1_engine.sync_engine,
                "before_cursor_execute",
                observe_statement,
            )

        assert single_count == multiple_count == 2
        assert [
            (version, status) for version, status, _properties in single_history
        ] == [(1, VersionStatus.PUBLISHED)]
        assert tuple(item.name for item in single_history[0][2]) == ("metric",)
        assert [
            (version, status) for version, status, _properties in multiple_history
        ] == [
            (1, VersionStatus.DEPRECATED),
            (2, VersionStatus.PUBLISHED),
            (3, VersionStatus.PUBLISHED),
            (4, VersionStatus.PUBLISHED),
        ]
        expected_properties = multiple_history[0][2]
        assert tuple(item.name for item in expected_properties) == ("metric",)
        assert all(
            properties == expected_properties for _, _, properties in multiple_history
        )
        history_calls = 0
        original_history = RelationshipDefinitionVersionStore.published_history

        async def observed_history(
            store: RelationshipDefinitionVersionStore, definition_id: UUID
        ) -> tuple[RelationshipDefinitionVersion, ...]:
            nonlocal history_calls
            history_calls += 1
            return await original_history(store, definition_id)

        with monkeypatch.context() as context:
            context.setattr(
                RelationshipDefinitionVersionStore,
                "published_history",
                observed_history,
            )
            changed = await reader.schema_change(relationship.relationship.id, 2)
        assert history_calls == 1
        assert changed.relationship_definition_version == 2
        assert changed.properties == {"metric": 1}


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_ref_10_schema_change_first_blocks_definition_delete(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "REF-10-SCHEMA-FIRST") as actors:
        seed = await _property_seed(actors, "ref10_schema_first", versions=2)
        created = await _reader(actors).create(
            seed.first_resolution_id,
            seed.first_object.id,
            seed.second_object.id,
            1,
            {"metric": 1},
        )
        closure_before = await _closure_keys(actors, created.relationship.id)
        writer = RelationshipService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        )
        deleter = RelationshipDefinitionService(
            ObservedUnitOfWorkFactory(actors.t2_engine, actors.tracker, "T2")
        )
        with monkeypatch.context() as context:
            cut = install_lock_plan_cut(
                context,
                relationship_application,
                RowLockClass.RELATIONSHIP,
                RowLockMode.NKU,
            )
            t2_completed, t2_plans = _observe_t2_lock_plan(
                context, definition_application
            )

            async def observe_blocked(_: int, __: int) -> None:
                assert not t2_completed.is_set()
                assert len(t2_plans) == 1
                assert t2_plans[0].rows == (t2_plans[0].rows[0],)
                assert t2_plans[0].rows[0].key == RowLockKey(
                    RowLockClass.RELATIONSHIP_DEFINITION_HEADER,
                    seed.definition.id,
                )
                assert t2_plans[0].rows[0].mode is RowLockMode.U

            outcomes = await blocked_race(
                actors,
                cut,
                lambda: writer.schema_change(created.relationship.id, 2),
                lambda: deleter.delete(seed.definition.id),
                observe_blocked=observe_blocked,
            )
        assert isinstance(outcomes[0], RelationshipProjection)
        assert isinstance(outcomes[1], ApplicationFailure)
        assert outcomes[1].failure_class is FailureClass.STATE_CONFLICT
        assert outcomes[1].code == "delete_blocked"
        assert outcomes[1].details == {
            "resource_type": "relationship_definition",
            "id": str(seed.definition.id),
            "blockers": [{"type": "relationship", "count": 1}],
        }
        verifier = RelationshipDefinitionService(UnitOfWorkFactory(actors.t1_engine))
        assert (await verifier.get(seed.definition.id)).id == seed.definition.id
        assert (await verifier.get_version(seed.definition.id, 2)).version == 2
        current = await _reader(actors).get(created.relationship.id)
        assert current.relationship_definition_version == 2
        assert current.properties == {"metric": 1}
        assert await _closure_keys(actors, created.relationship.id) == closure_before
        history = await _transition_history(actors, created.relationship.id)
        assert [(kind, before, after) for _, kind, before, after in history] == [
            (
                EventKind.RELATIONSHIP_SCHEMA_CHANGE.value,
                {
                    "relationship_definition_version": 1,
                    "properties": {"metric": 1},
                },
                {
                    "relationship_definition_version": 2,
                    "properties": {"metric": 1},
                },
            )
        ]


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_ref_10_definition_delete_first_rolls_back_then_schema_changes(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "REF-10-DELETE-FIRST") as actors:
        seed = await _property_seed(actors, "ref10_delete_first", versions=2)
        created = await _reader(actors).create(
            seed.first_resolution_id,
            seed.first_object.id,
            seed.second_object.id,
            1,
            {"metric": 1},
        )
        closure_before = await _closure_keys(actors, created.relationship.id)
        deleter = RelationshipDefinitionService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        )
        writer = RelationshipService(
            ObservedUnitOfWorkFactory(actors.t2_engine, actors.tracker, "T2")
        )
        with monkeypatch.context() as context:
            t1_plans = _capture_t1_lock_plans(context, definition_application)
            cut = install_lock_plan_cut(
                context,
                definition_application,
                RowLockClass.RELATIONSHIP_DEFINITION_HEADER,
                RowLockMode.U,
            )
            t2_completed, t2_plans = _observe_t2_lock_plan(
                context, relationship_application
            )

            async def observe_blocked(_: int, __: int) -> None:
                assert len(t1_plans) == 1
                assert t1_plans[0].gate is AdvisoryGate.MODEL_ROOT_DELETE_GATE
                assert t1_plans[0].rows[0].key == RowLockKey(
                    RowLockClass.RELATIONSHIP_DEFINITION_HEADER,
                    seed.definition.id,
                )
                assert t1_plans[0].rows[0].mode is RowLockMode.U
                _assert_schema_waits_before_factual_owner(
                    t2_completed,
                    t2_plans,
                    seed.definition.id,
                    2,
                    created.relationship.id,
                )

            outcomes = await blocked_race(
                actors,
                cut,
                lambda: deleter.delete(seed.definition.id),
                lambda: writer.schema_change(created.relationship.id, 2),
                observe_blocked=observe_blocked,
            )
        assert isinstance(outcomes[0], ApplicationFailure)
        assert outcomes[0].failure_class is FailureClass.STATE_CONFLICT
        assert outcomes[0].code == "delete_blocked"
        assert outcomes[0].details == {
            "resource_type": "relationship_definition",
            "id": str(seed.definition.id),
            "blockers": [{"type": "relationship", "count": 1}],
        }
        assert isinstance(outcomes[1], RelationshipProjection)
        assert outcomes[1].relationship_definition_version == 2
        assert outcomes[1].properties == {"metric": 1}
        verifier = RelationshipDefinitionService(UnitOfWorkFactory(actors.t1_engine))
        assert (await verifier.get(seed.definition.id)).id == seed.definition.id
        assert (await verifier.get_version(seed.definition.id, 2)).version == 2
        current = await _reader(actors).get(created.relationship.id)
        assert current.relationship_definition_version == 2
        assert current.properties == {"metric": 1}
        assert await _closure_keys(actors, created.relationship.id) == closure_before
        history = await _transition_history(actors, created.relationship.id)
        assert [(kind, before, after) for _, kind, before, after in history] == [
            (
                EventKind.RELATIONSHIP_SCHEMA_CHANGE.value,
                {
                    "relationship_definition_version": 1,
                    "properties": {"metric": 1},
                },
                {
                    "relationship_definition_version": 2,
                    "properties": {"metric": 1},
                },
            )
        ]


def _metadata_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    cut = PhaseCut()
    original = LifecycleStore.relationship_views

    async def intercepted(
        store: LifecycleStore, relationship: Relationship
    ) -> tuple[RelationshipLifecycleView, ...]:
        value = await original(store, relationship)
        task = asyncio.current_task()
        if task is not None and task.get_name() == "T1":
            cut.reached.set()
            await cut.release.wait()
        return value

    monkeypatch.setattr(LifecycleStore, "relationship_views", intercepted)
    return cut


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_snap_05_relationship_mutations_capture_one_metadata_statement(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "SNAP-05") as actors:
        seed = await _property_seed(actors, "snap05_data", versions=2)
        relationship = await _reader(actors).create(
            seed.first_resolution_id,
            seed.first_object.id,
            seed.second_object.id,
            1,
            {"metric": 0},
        )
        writer = RelationshipService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        )
        objects = ObjectService(
            ObservedUnitOfWorkFactory(actors.t2_engine, actors.tracker, "T2")
        )
        cut = _metadata_cut(monkeypatch)
        first_task = asyncio.create_task(
            run_worker(
                lambda: writer.data_change(
                    relationship.relationship.id,
                    (DataChangeOperation(DataChangeKind.SET, "metric", 1),),
                ),
                actors.tracker,
                "T1",
            ),
            name="T1",
        )
        await cut.reached.wait()
        await run_worker(
            lambda: objects.rename(seed.first_object.id, "snap05-renamed-object"),
            actors.tracker,
            "T2",
        )
        await run_worker(
            lambda: objects.rename(seed.second_object.id, "snap05-renamed-destination"),
            actors.tracker,
            "T2",
        )
        cut.release.set()
        data_result = await first_task
        assert isinstance(data_result, RelationshipProjection)
        assert {view.name for view in data_result.views} == {
            item.name for item in seed.definition.resolutions
        }
        events = await ObjectService(UnitOfWorkFactory(actors.t1_engine)).list_events(
            kind=EventKind.RELATIONSHIP_DATA_CHANGE,
            object_id=None,
            destination_object_id=None,
            relationship_id=relationship.relationship.id,
            relationship_definition_id=None,
            relationship_name=None,
            occurred_from=None,
            occurred_to=None,
            involving_object_id=None,
            cursor=None,
            limit=100,
        )
        assert len(events.items) == 2
        historical_names = {item.canonical_name for item in events.items}
        assert "snap05-renamed-object" not in historical_names
        assert "snap05-renamed-destination" not in historical_names

        seed = await _property_seed(actors, "snap05_schema", versions=2)
        relationship = await _reader(actors).create(
            seed.first_resolution_id,
            seed.first_object.id,
            seed.second_object.id,
            1,
            {"metric": 0},
        )
        cut = _metadata_cut(monkeypatch)
        first_task = asyncio.create_task(
            run_worker(
                lambda: writer.schema_change(relationship.relationship.id, 2),
                actors.tracker,
                "T1",
            ),
            name="T1",
        )
        await cut.reached.wait()
        definitions = RelationshipDefinitionService(
            ObservedUnitOfWorkFactory(actors.t2_engine, actors.tracker, "T2")
        )
        renamed = tuple(
            ResolutionRename(item.id, f"snap05_{index}")
            for index, item in enumerate(seed.definition.resolutions, start=1)
        )
        await run_worker(
            lambda: definitions.rename_non_symmetric(
                seed.definition.id,
                cast(tuple[ResolutionRename, ResolutionRename], renamed),
            ),
            actors.tracker,
            "T2",
        )
        cut.release.set()
        schema_result = await first_task
        assert isinstance(schema_result, RelationshipProjection)
        assert {view.name for view in schema_result.views} == {
            item.name for item in seed.definition.resolutions
        }


@pytest.mark.parametrize("transition", ["data", "schema"])
@pytest.mark.parametrize("rename_case", ["from", "to", "both", "definition"])
@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_snap_05_each_mutation_observes_each_independent_rename_cut(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
    transition: str,
    rename_case: str,
) -> None:
    del migrated_database_engine
    prefix = f"snap05_{transition}_{rename_case}"
    represented_scenarios = frozenset(
        {"SNAP-05", "SNAP-01" if rename_case == "definition" else "SNAP-02"}
    )
    async with semantic_actors(
        test_database_url, f"SNAP-05-{prefix.upper()}"
    ) as actors:
        seed = await _property_seed(actors, prefix, versions=2)
        reader = RelationshipService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        )
        created = await reader.create(
            seed.first_resolution_id,
            seed.first_object.id,
            seed.second_object.id,
            1,
            {"metric": 0},
        )
        original_object_names = {
            seed.first_object.canonical_name,
            seed.second_object.canonical_name,
        }
        original_relationship_names = {
            item.name for item in seed.definition.resolutions
        }
        cut = _metadata_cut(monkeypatch)
        operation: Operation
        if transition == "data":

            async def data_change() -> object:
                return await reader.data_change(
                    created.relationship.id,
                    (DataChangeOperation(DataChangeKind.SET, "metric", 1),),
                )

            operation = data_change
            event_kind = EventKind.RELATIONSHIP_DATA_CHANGE
        else:

            async def schema_change() -> object:
                return await reader.schema_change(created.relationship.id, 2)

            operation = schema_change
            event_kind = EventKind.RELATIONSHIP_SCHEMA_CHANGE
        mutation = asyncio.create_task(
            run_worker(
                operation,
                actors.tracker,
                "T1",
                scenario_ids=represented_scenarios,
            ),
            name="T1",
        )
        await cut.reached.wait()
        if rename_case == "definition":
            renamed = tuple(
                ResolutionRename(item.id, f"{prefix}_{index}")
                for index, item in enumerate(seed.definition.resolutions, start=1)
            )
            definitions = RelationshipDefinitionService(
                ObservedUnitOfWorkFactory(actors.t2_engine, actors.tracker, "T2")
            )
            await run_worker(
                lambda: definitions.rename_non_symmetric(
                    seed.definition.id,
                    cast(tuple[ResolutionRename, ResolutionRename], renamed),
                ),
                actors.tracker,
                "T2",
                scenario_ids=represented_scenarios,
            )
        else:
            objects = ObjectService(
                ObservedUnitOfWorkFactory(actors.t2_engine, actors.tracker, "T2")
            )
            if rename_case in {"from", "both"}:
                await run_worker(
                    lambda: objects.rename(
                        seed.first_object.id, f"{prefix}-renamed-from"
                    ),
                    actors.tracker,
                    "T2",
                    scenario_ids=represented_scenarios,
                )
            if rename_case in {"to", "both"}:
                await run_worker(
                    lambda: objects.rename(
                        seed.second_object.id, f"{prefix}-renamed-to"
                    ),
                    actors.tracker,
                    "T2",
                    scenario_ids=represented_scenarios,
                )
        cut.release.set()
        result = await mutation
        assert isinstance(result, RelationshipProjection)
        assert {view.name for view in result.views} == original_relationship_names
        events = await ObjectService(UnitOfWorkFactory(actors.t1_engine)).list_events(
            kind=event_kind,
            object_id=None,
            destination_object_id=None,
            relationship_id=created.relationship.id,
            relationship_definition_id=None,
            relationship_name=None,
            occurred_from=None,
            occurred_to=None,
            involving_object_id=None,
            cursor=None,
            limit=100,
        )
        assert len(events.items) == 2
        assert all(
            isinstance(item, RelationshipLifecycleEvent) for item in events.items
        )
        relationship_events = cast(Sequence[RelationshipLifecycleEvent], events.items)
        assert {
            item.canonical_name for item in relationship_events
        } == original_object_names
        assert {
            item.destination_canonical_name for item in relationship_events
        } == original_object_names
        assert {item.relationship_name for item in relationship_events} == (
            original_relationship_names
        )


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_atomic_06_07_real_dml_rolls_back_when_shared_writer_fails(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ATOMIC-06-07") as actors:
        seed = await _property_seed(actors, "atomic06", versions=2)
        reader = RelationshipService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        )
        first = await reader.create(
            seed.first_resolution_id,
            seed.first_object.id,
            seed.second_object.id,
            1,
            {"metric": 0},
        )
        original = LifecycleStore.insert_relationship_events

        async def fail_after_data_dml(
            store: LifecycleStore,
            *,
            kind: EventKind,
            before: Relationship | None,
            after: Relationship | None,
            views: Sequence[RelationshipLifecycleView],
        ) -> None:
            if kind is EventKind.RELATIONSHIP_DATA_CHANGE:
                assert after is not None
                properties = await store.connection.scalar(
                    select(relationships.c.properties).where(
                        relationships.c.id == after.id
                    )
                )
                assert properties == {"metric": 1}
                raise ApplicationFailure(
                    FailureClass.INTERNAL_FAILURE,
                    "internal_error",
                    "forced ATOMIC-06 event failure",
                )
            await original(store, kind=kind, before=before, after=after, views=views)

        with monkeypatch.context() as context:
            context.setattr(
                LifecycleStore,
                "insert_relationship_events",
                fail_after_data_dml,
            )
            with pytest.raises(ApplicationFailure):
                await run_worker(
                    lambda: reader.data_change(
                        first.relationship.id,
                        (DataChangeOperation(DataChangeKind.SET, "metric", 1),),
                    ),
                    actors.tracker,
                    "T1",
                    scenario_ids=frozenset({"ATOMIC-06", "ATOMIC-07"}),
                )
        assert (await reader.get(first.relationship.id)).properties == {"metric": 0}
        assert EventKind.RELATIONSHIP_DATA_CHANGE.value not in await _event_kinds(
            actors, first.relationship.id
        )

        second_seed = await _property_seed(actors, "atomic07", versions=2)
        second = await reader.create(
            second_seed.first_resolution_id,
            second_seed.first_object.id,
            second_seed.second_object.id,
            1,
            {"metric": 0},
        )

        async def fail_after_schema_dml(
            store: LifecycleStore,
            *,
            kind: EventKind,
            before: Relationship | None,
            after: Relationship | None,
            views: Sequence[RelationshipLifecycleView],
        ) -> None:
            if kind is EventKind.RELATIONSHIP_SCHEMA_CHANGE:
                assert after is not None
                version = await store.connection.scalar(
                    select(relationships.c.relationship_definition_version).where(
                        relationships.c.id == after.id
                    )
                )
                assert version == 2
                raise ApplicationFailure(
                    FailureClass.INTERNAL_FAILURE,
                    "internal_error",
                    "forced ATOMIC-07 event failure",
                )
            await original(store, kind=kind, before=before, after=after, views=views)

        with monkeypatch.context() as context:
            context.setattr(
                LifecycleStore,
                "insert_relationship_events",
                fail_after_schema_dml,
            )
            with pytest.raises(ApplicationFailure):
                await run_worker(
                    lambda: reader.schema_change(second.relationship.id, 2),
                    actors.tracker,
                    "T1",
                    scenario_ids=frozenset({"ATOMIC-06", "ATOMIC-07"}),
                )
        current = await reader.get(second.relationship.id)
        assert current.relationship_definition_version == 1
        assert current.properties == {"metric": 0}
        assert EventKind.RELATIONSHIP_SCHEMA_CHANGE.value not in await _event_kinds(
            actors, second.relationship.id
        )


@pytest.mark.parametrize(
    ("shape", "self_loop", "overlap", "expected_raw", "expected_views"),
    [
        ("symmetric_distinct", False, False, 2, 2),
        ("symmetric_self", True, False, 1, 1),
        ("inheritance_overlap", False, True, 4, 2),
    ],
)
@pytest.mark.postgresql
async def test_m2_s02_all_transition_families_use_distinct_semantic_fanout(
    migrated_database_engine: Engine,
    test_database_url: str,
    shape: str,
    self_loop: bool,
    overlap: bool,
    expected_raw: int,
    expected_views: int,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, f"S02-FANOUT-{shape}") as actors:
        seed = await _symmetric_property_seed(
            actors,
            f"fanout_{shape}",
            self_loop=self_loop,
            inheritance_overlap=overlap,
        )
        service = _reader(actors)
        created = await service.create(
            seed.first_resolution_id,
            seed.first_object.id,
            seed.second_object.id,
            1,
            {"metric": 0},
        )
        async with actors.t1_engine.connect() as connection:
            raw_count = await connection.scalar(
                select(func.count())
                .select_from(runtime_relationship_resolutions)
                .where(
                    runtime_relationship_resolutions.c.relationship_id
                    == created.relationship.id
                )
            )
        assert raw_count == expected_raw
        assert len(created.relationship.views) == expected_views
        await service.data_change(
            created.relationship.id,
            (DataChangeOperation(DataChangeKind.SET, "metric", 1),),
        )
        await service.schema_change(created.relationship.id, 2)
        await service.delete(created.relationship.id)
        kinds = await _event_kinds(actors, created.relationship.id)
        for kind in (
            EventKind.RELATIONSHIP_CREATED,
            EventKind.RELATIONSHIP_DATA_CHANGE,
            EventKind.RELATIONSHIP_SCHEMA_CHANGE,
            EventKind.RELATIONSHIP_DELETED,
        ):
            assert kinds.count(kind.value) == expected_views


@pytest.mark.postgresql
@pytest.mark.concurrency
@pytest.mark.parametrize("transition", ["data", "schema", "delete"])
async def test_relationship_read_cuts_expose_only_committed_before_or_after(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
    transition: str,
) -> None:
    del migrated_database_engine
    async with semantic_actors(
        test_database_url, f"S02-READ-CUT-{transition}"
    ) as actors:
        seed = await _property_seed(actors, f"read_cut_{transition}", versions=2)
        reader = _reader(actors)
        created = await reader.create(
            seed.first_resolution_id,
            seed.first_object.id,
            seed.second_object.id,
            1,
            {"metric": 0},
        )
        cut = PhaseCut()
        original = LifecycleStore.insert_relationship_events
        selected_kind = {
            "data": EventKind.RELATIONSHIP_DATA_CHANGE,
            "schema": EventKind.RELATIONSHIP_SCHEMA_CHANGE,
            "delete": EventKind.RELATIONSHIP_DELETED,
        }[transition]

        async def pause_after_dml(
            store: LifecycleStore,
            *,
            kind: EventKind,
            before: Relationship | None,
            after: Relationship | None,
            views: Sequence[RelationshipLifecycleView],
        ) -> None:
            if kind is selected_kind:
                cut.reached.set()
                await cut.release.wait()
            await original(store, kind=kind, before=before, after=after, views=views)

        monkeypatch.setattr(
            LifecycleStore, "insert_relationship_events", pause_after_dml
        )
        operation: Awaitable[object]
        if transition == "data":
            operation = reader.data_change(
                created.relationship.id,
                (DataChangeOperation(DataChangeKind.SET, "metric", 1),),
            )
        elif transition == "schema":
            operation = reader.schema_change(created.relationship.id, 2)
        else:
            operation = reader.delete(created.relationship.id)
        task = asyncio.create_task(operation)
        await cut.reached.wait()
        before_reader = RelationshipService(UnitOfWorkFactory(actors.t2_engine))
        before = await before_reader.get(created.relationship.id)
        page_before = await before_reader.list_for_object(
            seed.first_object.id,
            relationship_definition_id=None,
            name=None,
            cursor=None,
            limit=100,
        )
        assert before.properties == {"metric": 0}
        assert before.relationship_definition_version == 1
        assert page_before.items[0].properties == {"metric": 0}
        assert page_before.items[0].relationship_definition_version == 1
        cut.release.set()
        await task
        after_reader = RelationshipService(UnitOfWorkFactory(actors.t2_engine))
        page_after = await after_reader.list_for_object(
            seed.first_object.id,
            relationship_definition_id=None,
            name=None,
            cursor=None,
            limit=100,
        )
        if transition == "delete":
            with pytest.raises(ApplicationFailure) as missing:
                await after_reader.get(created.relationship.id)
            assert missing.value.code == "resource_not_found"
            assert page_after.items == []
        else:
            after = await after_reader.get(created.relationship.id)
            if transition == "data":
                assert after.properties == {"metric": 1}
                assert after.relationship_definition_version == 1
            else:
                assert after.properties == {"metric": 0}
                assert after.relationship_definition_version == 2
            assert page_after.items[0].properties == after.properties
            assert (
                page_after.items[0].relationship_definition_version
                == after.relationship_definition_version
            )


@pytest.mark.parametrize("read_kind", ["get", "page"])
@pytest.mark.parametrize("transition", ["data", "schema", "delete"])
@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_relationship_snapshot_cut_commits_between_physical_reads(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
    read_kind: str,
    transition: str,
) -> None:
    del migrated_database_engine
    scenario = f"S02-SNAPSHOT-{read_kind}-{transition}"
    async with semantic_actors(test_database_url, scenario) as actors:
        prefix = f"snapshot_{read_kind}_{transition}"
        seed = await _property_seed(actors, prefix, versions=2)
        writer = RelationshipService(UnitOfWorkFactory(actors.t1_engine))
        relationship = await writer.create(
            seed.first_resolution_id,
            seed.first_object.id,
            seed.second_object.id,
            1,
            {"metric": 0},
        )
        cut = PhaseCut()
        if read_kind == "get":
            original_get = RuntimeRelationshipStore.get

            async def cut_get(
                store: RuntimeRelationshipStore, relationship_id: UUID
            ) -> Relationship | None:
                value = await original_get(store, relationship_id)
                task = asyncio.current_task()
                if (
                    task is not None
                    and task.get_name() == "READER"
                    and not cut.reached.is_set()
                ):
                    cut.reached.set()
                    await cut.release.wait()
                return value

            monkeypatch.setattr(RuntimeRelationshipStore, "get", cut_get)
        else:
            original_page = RuntimeRelationshipStore.list_object_views

            async def cut_page(
                store: RuntimeRelationshipStore,
                object_id: UUID,
                *,
                relationship_definition_id: UUID | None,
                name: str | None,
                after: tuple[UUID, UUID, str] | None,
                limit: int,
            ):
                value = await original_page(
                    store,
                    object_id,
                    relationship_definition_id=relationship_definition_id,
                    name=name,
                    after=after,
                    limit=limit,
                )
                task = asyncio.current_task()
                if (
                    task is not None
                    and task.get_name() == "READER"
                    and not cut.reached.is_set()
                ):
                    cut.reached.set()
                    await cut.release.wait()
                return value

            monkeypatch.setattr(RuntimeRelationshipStore, "list_object_views", cut_page)

        snapshot_reader = RelationshipService(UnitOfWorkFactory(actors.t2_engine))
        if read_kind == "get":
            read_operation = snapshot_reader.get(relationship.relationship.id)
        else:
            read_operation = snapshot_reader.list_for_object(
                seed.first_object.id,
                relationship_definition_id=None,
                name=None,
                cursor=None,
                limit=100,
            )
        read_task = asyncio.create_task(read_operation, name="READER")
        await cut.reached.wait()
        if transition == "data":
            await writer.data_change(
                relationship.relationship.id,
                (DataChangeOperation(DataChangeKind.SET, "metric", 1),),
            )
        elif transition == "schema":
            await writer.schema_change(relationship.relationship.id, 2)
        else:
            await writer.delete(relationship.relationship.id)
        cut.release.set()
        snapshot = await read_task
        if isinstance(snapshot, RelationshipProjection):
            assert snapshot.properties == {"metric": 0}
            assert snapshot.relationship_definition_version == 1
        else:
            assert isinstance(snapshot, Page)
            assert snapshot.items[0].properties == {"metric": 0}
            assert snapshot.items[0].relationship_definition_version == 1
