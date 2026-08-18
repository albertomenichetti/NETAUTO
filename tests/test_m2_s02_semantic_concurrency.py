"""Deterministic real-PostgreSQL M2-S02 Relationship scenarios."""

import asyncio
from collections.abc import Awaitable, Callable, Sequence
from functools import partial
from typing import cast
from uuid import UUID

import pytest
from sqlalchemy import Engine, func, select

import netauto.application.relationships as relationship_application
from netauto.application.cursors import Page
from netauto.application.objects import ObjectService
from netauto.application.objecttemplates import ObjectTemplateService
from netauto.application.relationshipdefinitions import RelationshipDefinitionService
from netauto.application.relationships import (
    RelationshipProjection,
    RelationshipService,
)
from netauto.domain.objects import DataChangeKind, DataChangeOperation, Object
from netauto.domain.objecttemplates import ValueMode
from netauto.domain.primitives import JsonValue
from netauto.domain.relationships import (
    Relationship,
    RelationshipDefinition,
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
from netauto.persistence.locking import RowLockClass, RowLockMode
from netauto.persistence.metadata import (
    object_lifecycle_events,
    relationships,
    runtime_relationship_resolutions,
)
from netauto.persistence.relationships import RuntimeRelationshipStore
from netauto.persistence.uow import UnitOfWorkFactory
from tests.support.semantic_concurrency import (
    ObservedUnitOfWorkFactory,
    PhaseCut,
    SemanticActors,
    blocked_race,
    install_lock_plan_cut,
    progress_race,
    semantic_actors,
)

type Operation = Callable[[], Awaitable[object]]


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
        assert all(not isinstance(item, ApplicationFailure) for item in outcomes)
        assert (await reader.get(created.relationship.id)).properties == {
            "metric": 1,
            "other": 2,
        }
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
            await blocked_race(
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
        assert (await reader.get(created.relationship.id)).properties["metric"] == 3


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_27_data_and_schema_change_have_serial_factual_history(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-27") as actors:
        for prefix, schema_first in (("row27_data", False), ("row27_schema", True)):
            seed = await _property_seed(actors, prefix, versions=2)
            created = await _reader(actors).create(
                seed.first_resolution_id,
                seed.first_object.id,
                seed.second_object.id,
                1,
                {"metric": 0},
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
                data: Operation = partial(
                    second.data_change,
                    created.relationship.id,
                    (DataChangeOperation(DataChangeKind.SET, "metric", 7),),
                )
                schema: Operation = partial(
                    first.schema_change, created.relationship.id, 2
                )
                outcomes = await blocked_race(
                    actors,
                    cut,
                    schema
                    if schema_first
                    else partial(
                        first.data_change,
                        created.relationship.id,
                        (DataChangeOperation(DataChangeKind.SET, "metric", 7),),
                    ),
                    data
                    if schema_first
                    else partial(second.schema_change, created.relationship.id, 2),
                )
            assert all(not isinstance(item, ApplicationFailure) for item in outcomes)
            current = await _reader(actors).get(created.relationship.id)
            assert current.relationship_definition_version == 2
            assert current.properties == {"metric": 7}
            assert (
                await _closure_keys(actors, created.relationship.id) == closure_before
            )
            kinds = await _event_kinds(actors, created.relationship.id)
            assert kinds.count(EventKind.RELATIONSHIP_DATA_CHANGE.value) == 2
            assert kinds.count(EventKind.RELATIONSHIP_SCHEMA_CHANGE.value) == 2


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_28_schema_changes_recheck_forward_target_after_wait(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-28") as actors:
        seed = await _property_seed(actors, "row28_serial", versions=3)
        created = await _reader(actors).create(
            seed.first_resolution_id,
            seed.first_object.id,
            seed.second_object.id,
            1,
            {"metric": 1},
        )
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
                lambda: first.schema_change(created.relationship.id, 2),
                lambda: second.schema_change(created.relationship.id, 3),
            )
        assert all(not isinstance(item, ApplicationFailure) for item in outcomes)
        assert (
            await _reader(actors).get(created.relationship.id)
        ).relationship_definition_version == 3

        seed = await _property_seed(actors, "row28_stale", versions=3)
        created = await _reader(actors).create(
            seed.first_resolution_id,
            seed.first_object.id,
            seed.second_object.id,
            1,
            {"metric": 1},
        )
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
                lambda: first.schema_change(created.relationship.id, 3),
                lambda: second.schema_change(created.relationship.id, 2),
            )
        assert not isinstance(outcomes[0], ApplicationFailure)
        assert isinstance(outcomes[1], ApplicationFailure)
        assert outcomes[1].code == "semantic_validation_failed"


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
async def test_row_30_schema_target_admission_is_stable_through_commit(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-30-SCHEMA") as actors:
        seed = await _property_seed(actors, "row30_schema", versions=2)
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
            outcomes = await blocked_race(
                actors,
                cut,
                lambda: first.schema_change(created.relationship.id, 2),
                lambda: definitions.deprecate(seed.definition.id, 2),
            )
        assert not isinstance(outcomes[0], ApplicationFailure)
        assert not isinstance(outcomes[1], ApplicationFailure)
        assert (
            await _reader(actors).get(created.relationship.id)
        ).relationship_definition_version == 2

        seed = await _property_seed(actors, "row30_deprecated", versions=2)
        await RelationshipDefinitionService(
            UnitOfWorkFactory(actors.t1_engine)
        ).deprecate(seed.definition.id, 2)
        created = await _reader(actors).create(
            seed.first_resolution_id,
            seed.first_object.id,
            seed.second_object.id,
            1,
            {"metric": 1},
        )
        with pytest.raises(ApplicationFailure) as blocked:
            await _reader(actors).schema_change(created.relationship.id, 2)
        assert blocked.value.code == "dependency_not_admissible"

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
@pytest.mark.concurrency
async def test_ref_10_schema_rebind_target_before_owner_has_no_deadlock(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "REF-10-REL-SCHEMA") as actors:
        seed = await _property_seed(actors, "ref10_schema", versions=2)
        created = await _reader(actors).create(
            seed.first_resolution_id,
            seed.first_object.id,
            seed.second_object.id,
            1,
            {"metric": 1},
        )
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
            outcomes = await blocked_race(
                actors,
                cut,
                lambda: writer.schema_change(created.relationship.id, 2),
                lambda: deleter.delete(seed.definition.id),
            )
        assert not isinstance(outcomes[0], ApplicationFailure)
        assert isinstance(outcomes[1], ApplicationFailure)
        assert outcomes[1].code == "delete_blocked"
        assert (
            await _reader(actors).get(created.relationship.id)
        ).relationship_definition_version == 2

        seed = await _property_seed(actors, "ref10_delete_first", versions=2)
        created = await _reader(actors).create(
            seed.first_resolution_id,
            seed.first_object.id,
            seed.second_object.id,
            1,
            {"metric": 1},
        )
        with pytest.raises(ApplicationFailure) as delete_blocked:
            await RelationshipDefinitionService(
                UnitOfWorkFactory(actors.t2_engine)
            ).delete(seed.definition.id)
        assert delete_blocked.value.code == "delete_blocked"
        changed = await _reader(actors).schema_change(created.relationship.id, 2)
        assert changed.relationship_definition_version == 2


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
        writer = RelationshipService(UnitOfWorkFactory(actors.t1_engine))
        objects = ObjectService(UnitOfWorkFactory(actors.t2_engine))
        cut = _metadata_cut(monkeypatch)
        first_task = asyncio.create_task(
            writer.data_change(
                relationship.relationship.id,
                (DataChangeOperation(DataChangeKind.SET, "metric", 1),),
            ),
            name="T1",
        )
        await cut.reached.wait()
        await objects.rename(seed.first_object.id, "snap05-renamed-object")
        await objects.rename(seed.second_object.id, "snap05-renamed-destination")
        cut.release.set()
        data_result = await first_task
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
            writer.schema_change(relationship.relationship.id, 2), name="T1"
        )
        await cut.reached.wait()
        definitions = RelationshipDefinitionService(UnitOfWorkFactory(actors.t2_engine))
        renamed = tuple(
            ResolutionRename(item.id, f"snap05_{index}")
            for index, item in enumerate(seed.definition.resolutions, start=1)
        )
        await definitions.rename_non_symmetric(
            seed.definition.id,
            cast(tuple[ResolutionRename, ResolutionRename], renamed),
        )
        cut.release.set()
        schema_result = await first_task
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
    async with semantic_actors(test_database_url, prefix.upper()) as actors:
        seed = await _property_seed(actors, prefix, versions=2)
        reader = _reader(actors)
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
        operation: Awaitable[RelationshipProjection]
        if transition == "data":
            operation = reader.data_change(
                created.relationship.id,
                (DataChangeOperation(DataChangeKind.SET, "metric", 1),),
            )
            event_kind = EventKind.RELATIONSHIP_DATA_CHANGE
        else:
            operation = reader.schema_change(created.relationship.id, 2)
            event_kind = EventKind.RELATIONSHIP_SCHEMA_CHANGE
        mutation = asyncio.create_task(operation, name="T1")
        await cut.reached.wait()
        if rename_case == "definition":
            renamed = tuple(
                ResolutionRename(item.id, f"{prefix}_{index}")
                for index, item in enumerate(seed.definition.resolutions, start=1)
            )
            await RelationshipDefinitionService(
                UnitOfWorkFactory(actors.t2_engine)
            ).rename_non_symmetric(
                seed.definition.id,
                cast(tuple[ResolutionRename, ResolutionRename], renamed),
            )
        else:
            objects = ObjectService(UnitOfWorkFactory(actors.t2_engine))
            if rename_case in {"from", "both"}:
                await objects.rename(seed.first_object.id, f"{prefix}-renamed-from")
            if rename_case in {"to", "both"}:
                await objects.rename(seed.second_object.id, f"{prefix}-renamed-to")
        cut.release.set()
        result = await mutation
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
        reader = _reader(actors)
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
                await reader.data_change(
                    first.relationship.id,
                    (DataChangeOperation(DataChangeKind.SET, "metric", 1),),
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
                await reader.schema_change(second.relationship.id, 2)
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
