"""Deterministic PostgreSQL closure for the M2-S03 concurrency delta."""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, replace
from functools import partial
from types import ModuleType
from typing import cast
from uuid import UUID

import pytest
from sqlalchemy import Engine, func, select
from sqlalchemy.ext.asyncio import AsyncConnection

import netauto.application.objects as object_application
import netauto.application.objecttemplates as object_template_application
import netauto.application.relationshipdefinitions as definition_application
from netauto.application.datatypes import DataTypeService
from netauto.application.objects import ObjectService
from netauto.application.objecttemplates import (
    ComponentCandidate,
    ObjectTemplateService,
    PropertyCandidate,
)
from netauto.application.relationshipdefinitions import RelationshipDefinitionService
from netauto.application.relationships import (
    RelationshipCreateResult,
    RelationshipService,
)
from netauto.domain.datatypes import VersionStatus
from netauto.domain.objecttemplates import ObjectTemplateVersion, ValueMode
from netauto.domain.relationships import (
    RelationshipDefinition,
    RelationshipDefinitionVersion,
    RelationshipPerspective,
    RelationshipPropertyCandidate,
    ResolutionRename,
)
from netauto.failures import ApplicationFailure, FailureClass
from netauto.persistence.datatypes import DataTypeStore
from netauto.persistence.locking import (
    LockPlan,
    RowLockClass,
    RowLockIntent,
    RowLockKey,
    RowLockMode,
    acquire_lock_plan,
    prepare_lock_plan,
)
from netauto.persistence.metadata import (
    datatypes,
    relationship_definition_properties,
    relationship_definitions,
)
from netauto.persistence.objecttemplates import ObjectTemplateStore
from netauto.persistence.relationships import (
    RelationshipDefinitionStore,
    RelationshipDefinitionVersionStore,
)
from netauto.persistence.uow import UnitOfWorkFactory
from tests.support.pg_harness import PgWorker, WorkerRole, wait_for_blocker
from tests.support.semantic_concurrency import (
    ConnectionTracker,
    ObservedUnitOfWorkFactory,
    PhaseCut,
    SemanticActors,
    blocked_race,
    capture,
    capture_worker_outcome,
    extract_sqlstate,
    progress_race,
    semantic_actors,
)

type Operation = Callable[[], Awaitable[object]]
type AcquireLockPlan = Callable[
    [AsyncConnection, LockPlan], Awaitable[tuple[RowLockKey, ...]]
]


@dataclass(frozen=True, slots=True)
class DefinitionSeed:
    definition: RelationshipDefinition
    first_template_id: UUID
    second_template_id: UUID


def _factory(actors: SemanticActors) -> UnitOfWorkFactory:
    return UnitOfWorkFactory(actors.t1_engine)


def _observed_factory(actors: SemanticActors, role: str) -> ObservedUnitOfWorkFactory:
    engine = actors.t1_engine if role == "T1" else actors.t2_engine
    return ObservedUnitOfWorkFactory(engine, actors.tracker, role)


def _templates(
    actors: SemanticActors,
) -> tuple[ObjectTemplateService, ObjectTemplateService]:
    return (
        ObjectTemplateService(_observed_factory(actors, "T1")),
        ObjectTemplateService(_observed_factory(actors, "T2")),
    )


def _definitions(
    actors: SemanticActors,
) -> tuple[RelationshipDefinitionService, RelationshipDefinitionService]:
    return (
        RelationshipDefinitionService(_observed_factory(actors, "T1")),
        RelationshipDefinitionService(_observed_factory(actors, "T2")),
    )


def _objects(actors: SemanticActors) -> tuple[ObjectService, ObjectService]:
    return (
        ObjectService(_observed_factory(actors, "T1")),
        ObjectService(_observed_factory(actors, "T2")),
    )


def _failure(value: object, code: str) -> ApplicationFailure:
    assert isinstance(value, ApplicationFailure)
    assert value.code == code
    return value


async def _published_datatype(actors: SemanticActors, name: str) -> UUID:
    service = DataTypeService(_factory(actors))
    created = await service.create(
        "m2_s03", name.replace("-", "_"), "core.integer", None, {}
    )
    await service.publish(created.datatype.id, 1, 1)
    return created.datatype.id


async def _template(
    actors: SemanticActors,
    name: str,
    *,
    parent_template_id: UUID | None = None,
    parent_version: int | None = None,
    properties: tuple[PropertyCandidate, ...] = (),
    components: tuple[ComponentCandidate, ...] = (),
    publish: bool = False,
) -> UUID:
    service = ObjectTemplateService(_factory(actors))
    created = await service.create(
        "m2_s03",
        name.replace("-", "_"),
        False,
        None,
        parent_template_id,
        parent_version,
        properties,
        components,
    )
    if publish:
        await service.publish(created.object_template.id, 1, 1)
    return created.object_template.id


async def _definition(
    actors: SemanticActors,
    name: str,
    *,
    properties: tuple[RelationshipPropertyCandidate, ...] = (),
    publish: bool = False,
) -> DefinitionSeed:
    safe_name = name.replace("-", "_")
    first_id = await _template(actors, f"{name}_first", publish=True)
    second_id = await _template(actors, f"{name}_second", publish=True)
    service = RelationshipDefinitionService(_factory(actors))
    created = await service.create_non_symmetric(
        (
            RelationshipPerspective(first_id, f"{safe_name}_forward"),
            RelationshipPerspective(second_id, f"{safe_name}_reverse"),
        ),
        properties,
    )
    if publish:
        await service.publish(created.relationship_definition.id, 1, 1)
    return DefinitionSeed(created.relationship_definition, first_id, second_id)


def _after_store_call_cut(
    monkeypatch: pytest.MonkeyPatch,
    store_type: type[object],
    method_name: str,
    *,
    selected_role: str = "T1",
) -> PhaseCut:
    cut = PhaseCut()
    original = cast(Callable[..., Awaitable[object]], getattr(store_type, method_name))

    async def intercepted(*args: object, **kwargs: object) -> object:
        result = await original(*args, **kwargs)
        task = asyncio.current_task()
        if task is not None and task.get_name() == selected_role:
            cut.reached.set()
            await cut.release.wait()
        return result

    monkeypatch.setattr(store_type, method_name, intercepted)
    return cut


def _record_plans(
    monkeypatch: pytest.MonkeyPatch, application_module: ModuleType
) -> list[LockPlan]:
    plans: list[LockPlan] = []
    original = cast(AcquireLockPlan, application_module.acquire_lock_plan)

    async def observed(
        connection: AsyncConnection, plan: LockPlan
    ) -> tuple[RowLockKey, ...]:
        plans.append(plan)
        return await original(connection, plan)

    monkeypatch.setattr(application_module, "acquire_lock_plan", observed)
    return plans


def _intent(
    plan: LockPlan,
    row_class: RowLockClass,
    resource_id: UUID,
    version: int | None = None,
) -> RowLockIntent:
    return next(
        item
        for item in plan.rows
        if item.key == RowLockKey(row_class, resource_id, version)
    )


@pytest.mark.postgresql
@pytest.mark.concurrency
@pytest.mark.parametrize("shape", ["parent", "component", "property"])
@pytest.mark.parametrize("order", ["clone-first", "delete-first"])
async def test_ref_08_clone_reference_lifetimes(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
    shape: str,
    order: str,
) -> None:
    """OT.CN protects every cloned FK shape in both physical winner orders."""
    del migrated_database_engine
    async with semantic_actors(test_database_url, f"REF-08-{shape}-{order}") as actors:
        datatype_id = await _published_datatype(actors, f"ref08_{shape}_datatype")
        target_id = await _template(actors, f"ref08_{shape}_target", publish=True)
        properties = (
            (PropertyCandidate("value", 1, datatype_id, 1, ValueMode.SCALAR, False),)
            if shape == "property"
            else ()
        )
        components = (
            (ComponentCandidate("part", 1, target_id),) if shape == "component" else ()
        )
        consumer_id = await _template(
            actors,
            f"ref08_{shape}_consumer",
            parent_template_id=target_id if shape == "parent" else None,
            parent_version=1 if shape == "parent" else None,
            properties=properties,
            components=components,
            publish=True,
        )
        reader = ObjectTemplateService(_factory(actors))
        source_before = await reader.get_version(consumer_id, 1)
        target_lineage_before: object
        target_version_before: object | None
        if shape == "property":
            datatype_reader = DataTypeService(_factory(actors))
            target_lineage_before = await datatype_reader.get_lineage(datatype_id)
            target_version_before = await datatype_reader.get_version(datatype_id, 1)
        else:
            target_lineage_before = await reader.get_lineage(target_id)
            target_version_before = (
                await reader.get_version(target_id, 1) if shape == "parent" else None
            )
        first_template, second_template = _templates(actors)
        plans = _record_plans(monkeypatch, object_template_application)

        if shape == "property":

            def first_delete():
                return DataTypeService(_observed_factory(actors, "T1")).delete_lineage(
                    datatype_id
                )

            def second_delete():
                return DataTypeService(_observed_factory(actors, "T2")).delete_lineage(
                    datatype_id
                )

            target_store: type[object] = DataTypeStore
            target_row_class = RowLockClass.DATA_TYPE_HEADER
            exact_row_class = RowLockClass.DATA_TYPE_VERSION
            target_resource_id = datatype_id
        else:

            def first_delete():
                return first_template.delete_lineage(target_id)

            def second_delete():
                return second_template.delete_lineage(target_id)

            target_store = ObjectTemplateStore
            target_row_class = RowLockClass.OBJECT_TEMPLATE_HEADER
            exact_row_class = RowLockClass.OBJECT_TEMPLATE_VERSION
            target_resource_id = target_id

        if order == "clone-first":
            cut = _after_store_call_cut(
                monkeypatch, ObjectTemplateStore, "insert_version"
            )
            clone, deletion = await blocked_race(
                actors,
                cut,
                lambda: first_template.create_next(consumer_id, 1),
                second_delete,
            )
        else:
            cut = _after_store_call_cut(
                monkeypatch, target_store, "external_reference_counts"
            )
            deletion, clone = await blocked_race(
                actors,
                cut,
                first_delete,
                lambda: second_template.create_next(consumer_id, 1),
            )

        assert isinstance(clone, ObjectTemplateVersion)
        assert clone == replace(
            source_before,
            version=2,
            revision=1,
            status=VersionStatus.DRAFT,
        )
        _failure(deletion, "delete_blocked")
        source_after = await reader.get_version(consumer_id, 1)
        clone_after = await reader.get_version(consumer_id, 2)
        assert source_after == source_before
        assert clone_after == clone
        versions = await reader.list_versions(
            consumer_id, status=None, cursor=None, limit=10
        )
        assert [
            (item.version, item.revision, item.status) for item in versions.items
        ] == [
            (1, source_before.revision, source_before.status),
            (2, 1, VersionStatus.DRAFT),
        ]
        assert versions.next_cursor is None
        if shape == "property":
            datatype_reader = DataTypeService(_factory(actors))
            assert (
                await datatype_reader.get_lineage(datatype_id) == target_lineage_before
            )
            assert (
                await datatype_reader.get_version(datatype_id, 1)
                == target_version_before
            )
        else:
            assert await reader.get_lineage(target_id) == target_lineage_before
            if shape == "parent":
                assert await reader.get_version(target_id, 1) == target_version_before
        clone_plan = next(
            plan
            for plan in plans
            if any(
                item.key == RowLockKey(RowLockClass.OBJECT_TEMPLATE_HEADER, consumer_id)
                for item in plan.rows
            )
        )
        assert (
            _intent(clone_plan, target_row_class, target_resource_id).mode
            is RowLockMode.KS
        )
        if shape != "component":
            assert (
                _intent(clone_plan, exact_row_class, target_resource_id, 1).mode
                is RowLockMode.KS
            )
        assert all(
            item.mode is not RowLockMode.S
            for item in clone_plan.rows
            if item.key.resource_id == target_resource_id
        )


@pytest.mark.postgresql
@pytest.mark.concurrency
@pytest.mark.parametrize("family", ["object-template-component", "rdv-property"])
@pytest.mark.parametrize("order", ["rebind-first", "delete-first"])
async def test_ref_09_differential_rebind_lifetimes(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
    family: str,
    order: str,
) -> None:
    """New/rebound child rows stabilize their exact target before owner DML."""
    del migrated_database_engine
    async with semantic_actors(test_database_url, f"REF-09-{family}-{order}") as actors:
        old_datatype = await _published_datatype(actors, f"ref09_{family}_old_dt")
        new_datatype = await _published_datatype(actors, f"ref09_{family}_new_dt")
        old_template = await _template(actors, f"ref09_{family}_old_ot")
        new_template = await _template(actors, f"ref09_{family}_new_ot")

        if family == "object-template-component":
            consumer_id = await _template(
                actors,
                f"ref09_{family}_consumer",
                components=(ComponentCandidate("part", 1, old_template),),
            )
            first_ot, second_ot = _templates(actors)
            plans = _record_plans(monkeypatch, object_template_application)
            first_rebind: Operation = partial(
                first_ot.revise,
                consumer_id,
                1,
                1,
                None,
                (),
                (ComponentCandidate("part", 1, new_template),),
            )
            second_rebind: Operation = partial(
                second_ot.revise,
                consumer_id,
                1,
                1,
                None,
                (),
                (ComponentCandidate("part", 1, new_template),),
            )
            first_delete: Operation = partial(first_ot.delete_lineage, new_template)
            second_delete: Operation = partial(second_ot.delete_lineage, new_template)

            target_store: type[object] = ObjectTemplateStore
            target_id = new_template
            target_class = RowLockClass.OBJECT_TEMPLATE_HEADER
            exact_class: RowLockClass | None = None
            owner_class = RowLockClass.OBJECT_TEMPLATE_VERSION
        else:
            seed = await _definition(
                actors,
                f"ref09_{family}",
                properties=(
                    RelationshipPropertyCandidate(
                        "value", 1, old_datatype, 1, ValueMode.SCALAR
                    ),
                ),
            )
            consumer_id = seed.definition.id
            first_rd, second_rd = _definitions(actors)
            plans = _record_plans(monkeypatch, definition_application)
            candidate = (
                RelationshipPropertyCandidate(
                    "value", 1, new_datatype, 1, ValueMode.SCALAR
                ),
            )

            first_rebind = partial(first_rd.revise, consumer_id, 1, 1, candidate)
            second_rebind = partial(second_rd.revise, consumer_id, 1, 1, candidate)

            first_delete = partial(
                DataTypeService(_observed_factory(actors, "T1")).delete_lineage,
                new_datatype,
            )
            second_delete = partial(
                DataTypeService(_observed_factory(actors, "T2")).delete_lineage,
                new_datatype,
            )

            target_store = DataTypeStore
            target_id = new_datatype
            target_class = RowLockClass.DATA_TYPE_HEADER
            exact_class = RowLockClass.DATA_TYPE_VERSION
            owner_class = RowLockClass.RELATIONSHIP_DEFINITION_VERSION

        if order == "rebind-first":
            store_type = (
                ObjectTemplateStore
                if family == "object-template-component"
                else RelationshipDefinitionVersionStore
            )
            cut = _after_store_call_cut(monkeypatch, store_type, "replace_candidate")
            rebound, deletion = await blocked_race(
                actors, cut, first_rebind, second_delete
            )
            assert not isinstance(rebound, ApplicationFailure)
            _failure(deletion, "delete_blocked")
        else:
            cut = _after_store_call_cut(
                monkeypatch, target_store, "external_reference_counts"
            )
            deletion, rebound = await blocked_race(
                actors, cut, first_delete, second_rebind
            )
            assert deletion is None
            _failure(rebound, "referenced_resource_not_found")

        rebind_plan = next(
            plan
            for plan in plans
            if any(item.key.row_class is owner_class for item in plan.rows)
        )
        assert _intent(rebind_plan, target_class, target_id).mode is RowLockMode.KS
        if exact_class is not None:
            assert _intent(rebind_plan, exact_class, target_id, 1).mode is RowLockMode.S


@pytest.mark.postgresql
@pytest.mark.parametrize("family", ["object-template", "rdv"])
async def test_ref_09_same_target_unchanged_and_removed_plan_variants(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
    family: str,
) -> None:
    """Differential replacement uses KS only for reinsertion and none otherwise."""
    del migrated_database_engine
    async with semantic_actors(test_database_url, f"REF-09-PLAN-{family}") as actors:
        datatype_id = await _published_datatype(actors, f"ref09_plan_{family}")
        if family == "object-template":
            consumer_id = await _template(
                actors,
                "ref09_plan_ot",
                properties=(
                    PropertyCandidate(
                        "value", 1, datatype_id, 1, ValueMode.SCALAR, False
                    ),
                ),
            )
            service = ObjectTemplateService(_factory(actors))
            plans = _record_plans(monkeypatch, object_template_application)

            async def revise(revision: int, mode: ValueMode | None) -> object:
                properties = (
                    ()
                    if mode is None
                    else (PropertyCandidate("value", 1, datatype_id, 1, mode, False),)
                )
                return await service.revise(
                    consumer_id, 1, revision, None, properties, ()
                )

        else:
            seed = await _definition(
                actors,
                "ref09_plan_rdv",
                properties=(
                    RelationshipPropertyCandidate(
                        "value", 1, datatype_id, 1, ValueMode.SCALAR
                    ),
                ),
            )
            consumer_id = seed.definition.id
            definition_service = RelationshipDefinitionService(_factory(actors))
            plans = _record_plans(monkeypatch, definition_application)

            async def revise(revision: int, mode: ValueMode | None) -> object:
                properties = (
                    ()
                    if mode is None
                    else (
                        RelationshipPropertyCandidate("value", 1, datatype_id, 1, mode),
                    )
                )
                return await definition_service.revise(
                    consumer_id, 1, revision, properties
                )

        await revise(1, ValueMode.LIST)
        await revise(2, ValueMode.LIST)
        await revise(3, None)
        assert len(plans) == 3
        reinsertion = plans[0]
        assert (
            _intent(reinsertion, RowLockClass.DATA_TYPE_HEADER, datatype_id).mode
            is RowLockMode.KS
        )
        assert (
            _intent(reinsertion, RowLockClass.DATA_TYPE_VERSION, datatype_id, 1).mode
            is RowLockMode.KS
        )
        for plan in plans[1:]:
            assert all(item.key.resource_id != datatype_id for item in plan.rows)


@pytest.mark.postgresql
@pytest.mark.concurrency
@pytest.mark.parametrize("family", ["object-template-parent", "object-schema"])
@pytest.mark.parametrize("order", ["rebind-first", "delete-first"])
async def test_ref_10_direct_owner_rebinds_target_before_owner(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
    family: str,
    order: str,
) -> None:
    """The remaining direct-FK rebind families never wait owner-before-target."""
    del migrated_database_engine
    async with semantic_actors(test_database_url, f"REF-10-{family}-{order}") as actors:
        target_id = await _template(actors, f"ref10_{family}_target", publish=True)
        setup_templates = ObjectTemplateService(_factory(actors))
        await setup_templates.create_next(target_id, 1)
        await setup_templates.publish(target_id, 2, 1)
        first_template, second_template = _templates(actors)

        if family == "object-template-parent":
            owner_id = await _template(
                actors,
                "ref10_parent_owner",
                parent_template_id=target_id,
                parent_version=1,
            )
            plans = _record_plans(monkeypatch, object_template_application)

            first_rebind: Operation = partial(
                first_template.revise, owner_id, 1, 1, 2, (), ()
            )
            second_rebind: Operation = partial(
                second_template.revise, owner_id, 1, 1, 2, (), ()
            )

            owner_class = RowLockClass.OBJECT_TEMPLATE_VERSION
            owner_store: type[object] = ObjectTemplateStore
            owner_write = "replace_candidate"
        else:
            object_template_id = target_id
            setup_objects = ObjectService(_factory(actors))
            owner = await setup_objects.create(
                object_template_id, 1, "ref10-object", {}
            )
            owner_id = owner.id
            first_object, second_object = _objects(actors)
            plans = _record_plans(monkeypatch, object_application)

            first_rebind = partial(first_object.schema_change, owner_id, 2)
            second_rebind = partial(second_object.schema_change, owner_id, 2)

            owner_class = RowLockClass.OBJECT
            from netauto.persistence.objects import ObjectStore

            owner_store = ObjectStore
            owner_write = "update_schema"

        def first_delete():
            return first_template.delete_lineage(target_id)

        def second_delete():
            return second_template.delete_lineage(target_id)

        if order == "rebind-first":
            cut = _after_store_call_cut(monkeypatch, owner_store, owner_write)
            rebound, deletion = await blocked_race(
                actors, cut, first_rebind, second_delete
            )
        else:
            cut = _after_store_call_cut(
                monkeypatch, ObjectTemplateStore, "external_reference_counts"
            )
            deletion, rebound = await blocked_race(
                actors, cut, first_delete, second_rebind
            )
        assert not isinstance(rebound, ApplicationFailure)
        _failure(deletion, "delete_blocked")

        plan = next(
            candidate
            for candidate in plans
            if any(item.key.row_class is owner_class for item in candidate.rows)
        )
        target_version = _intent(
            plan, RowLockClass.OBJECT_TEMPLATE_VERSION, target_id, 2
        )
        assert target_version.mode is RowLockMode.S
        target_position = plan.rows.index(target_version)
        owner_position = next(
            index
            for index, item in enumerate(plan.rows)
            if item.key.row_class is owner_class and item.key.resource_id == owner_id
        )
        assert target_position < owner_position


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_ref_11_mutual_roots_serialize_through_model_delete_gate(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutually referencing roots cannot form inverse root-row waits."""
    del migrated_database_engine
    async with semantic_actors(test_database_url, "REF-11") as actors:
        setup = ObjectTemplateService(_factory(actors))
        first_id = await _template(actors, "ref11_first")
        second_id = await _template(
            actors,
            "ref11_second",
            components=(ComponentCandidate("first", 1, first_id),),
        )
        await setup.revise(
            first_id,
            1,
            1,
            None,
            (),
            (ComponentCandidate("second", 1, second_id),),
        )
        first, second = _templates(actors)
        cut = _after_store_call_cut(
            monkeypatch, ObjectTemplateStore, "external_reference_counts"
        )
        actors.tracker.reset()
        first_task = asyncio.create_task(
            capture(lambda: first.delete_lineage(first_id)), name="T1"
        )
        await cut.reached.wait()
        second_task = asyncio.create_task(
            capture(lambda: second.delete_lineage(second_id)), name="T2"
        )
        await actors.tracker.ready["T2"].wait()
        assert actors.tracker.pids["T1"] in await wait_for_blocker(
            actors.observer,
            actors.tracker.pids["T2"],
            actors.tracker.pids["T1"],
        )

        third = await PgWorker.open(test_database_url, "REF-11", WorkerRole.T3)
        try:
            plan = await prepare_lock_plan(
                third.connection,
                intents=(
                    RowLockIntent(
                        RowLockKey(RowLockClass.OBJECT_TEMPLATE_HEADER, second_id),
                        RowLockMode.U,
                    ),
                ),
            )
            async with asyncio.timeout(5):
                assert await acquire_lock_plan(third.connection, plan) == ()
            await third.rollback()
        finally:
            await third.close()

        cut.release.set()
        first_result, second_result = await asyncio.gather(first_task, second_task)
        _failure(first_result, "delete_blocked")
        _failure(second_result, "delete_blocked")
        reader = ObjectTemplateService(_factory(actors))
        assert (await reader.get_version(first_id, 1)).components[
            0
        ].target_template_id == second_id
        assert (await reader.get_version(second_id, 1)).components[
            0
        ].target_template_id == first_id


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_gate_07_independent_root_deletes_wait_before_rows_and_reread(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A production root-delete gate waiter owns no planned row and rereads."""
    del migrated_database_engine
    async with semantic_actors(test_database_url, "GATE-07") as actors:
        setup = DataTypeService(_factory(actors))
        first = await setup.create("m2_s03", "gate07_first", "core.string", None, {})
        second = await setup.create("m2_s03", "gate07_second", "core.string", None, {})
        cut = PhaseCut()
        reads: list[str] = []
        original = DataTypeStore.external_reference_counts

        async def observed_counts(store: DataTypeStore, datatype_id: UUID) -> object:
            result = await original(store, datatype_id)
            task = asyncio.current_task()
            role = "UNKNOWN" if task is None else task.get_name()
            reads.append(role)
            if role == "T1":
                cut.reached.set()
                await cut.release.wait()
            return result

        monkeypatch.setattr(DataTypeStore, "external_reference_counts", observed_counts)
        actors.tracker.reset()
        first_task = asyncio.create_task(
            capture_worker_outcome(
                lambda: actors.t1.delete_lineage(first.datatype.id),
                actors.tracker,
                "T1",
            ),
            name="T1",
        )
        await cut.reached.wait()
        second_task = asyncio.create_task(
            capture_worker_outcome(
                lambda: actors.t2.delete_lineage(second.datatype.id),
                actors.tracker,
                "T2",
            ),
            name="T2",
        )
        await actors.tracker.ready["T2"].wait()
        assert actors.tracker.pids["T1"] in await wait_for_blocker(
            actors.observer,
            actors.tracker.pids["T2"],
            actors.tracker.pids["T1"],
        )

        third = await PgWorker.open(test_database_url, "GATE-07", WorkerRole.T3)
        try:
            plan = await prepare_lock_plan(
                third.connection,
                intents=(
                    RowLockIntent(
                        RowLockKey(RowLockClass.DATA_TYPE_HEADER, second.datatype.id),
                        RowLockMode.U,
                    ),
                ),
            )
            async with asyncio.timeout(5):
                assert await acquire_lock_plan(third.connection, plan) == ()
            await third.rollback()
        finally:
            await third.close()

        cut.release.set()
        first_outcome, second_outcome = await asyncio.gather(first_task, second_task)
        for outcome in (first_outcome, second_outcome):
            assert outcome.returned is None
            assert outcome.application_failure is None
            assert outcome.unexpected_exception_type is None
            assert outcome.sqlstate is None
            assert outcome.transaction_outcome == "COMMITTED"
        assert reads == ["T1", "T2"]
        async with actors.t1_engine.connect() as connection:
            assert (
                await connection.scalar(select(func.count()).select_from(datatypes))
                == 0
            )


def _rename_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    return _after_store_call_cut(
        monkeypatch, RelationshipDefinitionStore, "update_names"
    )


@pytest.mark.postgresql
@pytest.mark.concurrency
@pytest.mark.parametrize(
    "operation", ["revise", "set-default", "deprecate", "relationship-create"]
)
async def test_par_08_definition_rename_compatible_operations_progress(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
) -> None:
    """Definition rename KS stays compatible with each frozen operation family."""
    del migrated_database_engine
    async with semantic_actors(test_database_url, f"PAR-08-{operation}") as actors:
        seed = await _definition(actors, f"par08_{operation}", publish=True)
        setup_definitions = RelationshipDefinitionService(_factory(actors))
        if operation in {"revise", "deprecate"}:
            await setup_definitions.create_next(seed.definition.id, 1)
        if operation == "deprecate":
            await setup_definitions.publish(seed.definition.id, 2, 1)
        first, second = _definitions(actors)
        updates = tuple(
            ResolutionRename(item.id, f"renamed_{index}")
            for index, item in enumerate(seed.definition.resolutions, 1)
        )
        assert len(updates) == 2

        def rename():
            return first.rename_non_symmetric(
                seed.definition.id,
                updates,
            )

        if operation == "revise":
            compatible: Operation = partial(second.revise, seed.definition.id, 2, 1, ())
        elif operation == "set-default":
            compatible = partial(second.set_default, seed.definition.id, 1)
        elif operation == "deprecate":
            compatible = partial(second.deprecate, seed.definition.id, 2)
        else:
            setup_objects = ObjectService(_factory(actors))
            from_object = await setup_objects.create(
                seed.first_template_id, 1, f"par08-{operation}-from", {}
            )
            to_object = await setup_objects.create(
                seed.second_template_id, 1, f"par08-{operation}-to", {}
            )
            selected = next(
                item
                for item in seed.definition.resolutions
                if item.from_template_id == seed.first_template_id
            )
            relationship_service = RelationshipService(_observed_factory(actors, "T2"))

            compatible = partial(
                relationship_service.create,
                selected.id,
                from_object.id,
                to_object.id,
                relationship_definition_version=1,
            )

        cut = _rename_cut(monkeypatch)
        renamed, compatible_result = await progress_race(cut, rename, compatible)
        assert isinstance(renamed, RelationshipDefinition)
        assert not isinstance(compatible_result, ApplicationFailure)
        if operation == "relationship-create":
            assert isinstance(compatible_result, RelationshipCreateResult)
            names = {view.name for view in compatible_result.relationship.views}
            assert names in (
                {item.name for item in seed.definition.resolutions},
                {item.name for item in updates},
            )


@pytest.mark.postgresql
@pytest.mark.concurrency
@pytest.mark.parametrize("operation", ["deprecate", "revise"])
async def test_par_09_distinct_rdv_operations_make_progress(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
) -> None:
    """Distinct RDV owners remain compatible at the stable Definition header."""
    del migrated_database_engine
    async with semantic_actors(test_database_url, f"PAR-09-{operation}") as actors:
        seed = await _definition(actors, f"par09_{operation}", publish=True)
        setup = RelationshipDefinitionService(_factory(actors))
        await setup.create_next(seed.definition.id, 1)
        if operation == "deprecate":
            await setup.publish(seed.definition.id, 2, 1)
            await setup.create_next(seed.definition.id, 2)
            await setup.publish(seed.definition.id, 3, 1)
            await setup.set_default(seed.definition.id, 3)
            first_version, second_version = 1, 2
        else:
            await setup.create_next(seed.definition.id, 1)
            first_version, second_version = 2, 3
        first, second = _definitions(actors)
        cut = PhaseCut()
        original = cast(AcquireLockPlan, definition_application.acquire_lock_plan)

        async def intercepted(
            connection: AsyncConnection, plan: LockPlan
        ) -> tuple[RowLockKey, ...]:
            missing = await original(connection, plan)
            task = asyncio.current_task()
            if (
                task is not None
                and task.get_name() == "T1"
                and any(
                    item.key.row_class is RowLockClass.RELATIONSHIP_DEFINITION_VERSION
                    and item.key.version == first_version
                    and item.mode is RowLockMode.NKU
                    for item in plan.rows
                )
            ):
                cut.reached.set()
                await cut.release.wait()
            return missing

        monkeypatch.setattr(definition_application, "acquire_lock_plan", intercepted)
        if operation == "deprecate":

            def first_operation():
                return first.deprecate(seed.definition.id, first_version)

            def second_operation():
                return second.deprecate(seed.definition.id, second_version)
        else:

            def first_operation():
                return first.revise(seed.definition.id, first_version, 1, ())

            def second_operation():
                return second.revise(seed.definition.id, second_version, 1, ())

        first_result, second_result = await progress_race(
            cut, first_operation, second_operation
        )
        assert isinstance(first_result, RelationshipDefinitionVersion)
        assert isinstance(second_result, RelationshipDefinitionVersion)
        if operation == "deprecate":
            assert first_result.status is VersionStatus.DEPRECATED
            assert second_result.status is VersionStatus.DEPRECATED
        else:
            assert first_result.revision == 2
            assert second_result.revision == 2


@pytest.mark.postgresql
@pytest.mark.concurrency
@pytest.mark.parametrize("order", ["internal-first", "delete-first"])
async def test_row_16_relationship_definition_internal_and_root_delete_both_orders(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
    order: str,
) -> None:
    """RD internal mutation and whole-root delete share aggregate lifetime."""
    del migrated_database_engine
    async with semantic_actors(test_database_url, f"ROW-16-RD-{order}") as actors:
        seed = await _definition(actors, f"row16_{order}")
        first, second = _definitions(actors)
        if order == "internal-first":
            cut = _after_store_call_cut(
                monkeypatch,
                RelationshipDefinitionVersionStore,
                "replace_candidate",
            )
            internal, deletion = await blocked_race(
                actors,
                cut,
                lambda: first.revise(seed.definition.id, 1, 1, ()),
                lambda: second.delete(seed.definition.id),
            )
            assert isinstance(internal, RelationshipDefinitionVersion)
            assert internal.revision == 2
            assert deletion is None
        else:
            cut = _after_store_call_cut(
                monkeypatch, RelationshipDefinitionStore, "delete"
            )
            deletion, internal = await blocked_race(
                actors,
                cut,
                lambda: first.delete(seed.definition.id),
                lambda: second.revise(seed.definition.id, 1, 1, ()),
            )
            assert deletion is None
            _failure(internal, "resource_not_found")
        async with actors.t1_engine.connect() as connection:
            assert (
                await connection.scalar(
                    select(func.count()).select_from(relationship_definitions)
                )
                == 0
            )
            assert (
                await connection.scalar(
                    select(func.count()).select_from(relationship_definition_properties)
                )
                == 0
            )


def test_m2_harness_phase_vocabulary_and_outcome_boundary_are_exact() -> None:
    from tests.support.pg_harness import HarnessPhase

    assert {phase.value for phase in HarnessPhase} == {
        "UOW_STARTED",
        "DISCOVERY_COMPLETE",
        "LOCK_PLAN_BUILT",
        "GATE_WAITING",
        "GATE_ACQUIRED",
        "ROW_LOCK_WAITING",
        "ROW_LOCKS_ACQUIRED",
        "PROTECTED_STATE_REREAD",
        "LOCK_PLAN_STALE",
        "DEPENDENCIES_STABILIZED",
        "CANDIDATE_WRITTEN",
        "CLOSURE_WRITTEN",
        "METADATA_SNAPSHOT_CAPTURED",
        "EVENT_SET_WRITTEN",
        "CONSTRAINT_ARBITRATED",
        "BEFORE_COMMIT",
        "COMMITTED",
        "ROLLED_BACK",
        "UOW_RESTARTED",
    }
    assert HarnessPhase.OWNER_STABILIZED is HarnessPhase.DEPENDENCIES_STABILIZED


class _SqlstateError(Exception):
    def __init__(self, sqlstate: str) -> None:
        self.sqlstate = sqlstate
        super().__init__("safe synthetic database failure")


class _PgcodeError(Exception):
    def __init__(self, pgcode: str) -> None:
        self.pgcode = pgcode
        super().__init__("safe synthetic driver failure")


class _WrappedError(Exception):
    def __init__(self, attribute: str, error: BaseException) -> None:
        setattr(self, attribute, error)
        super().__init__("safe synthetic wrapper")


def test_s03_sqlstate_extraction_is_structural_nested_and_cycle_safe() -> None:
    direct = _SqlstateError("23505")
    assert extract_sqlstate(direct) == "23505"
    assert extract_sqlstate(_PgcodeError("23503")) == "23503"
    assert extract_sqlstate(_WrappedError("orig", direct)) == "23505"
    assert (
        extract_sqlstate(
            _WrappedError(
                "driver_exception", _WrappedError("orig", _PgcodeError("23503"))
            )
        )
        == "23503"
    )
    caused = RuntimeError("mapped")
    caused.__cause__ = direct
    assert extract_sqlstate(caused) == "23505"
    contextual = RuntimeError("contextual")
    contextual.__context__ = _PgcodeError("23503")
    assert extract_sqlstate(contextual) == "23503"
    cycle = RuntimeError("cycle")
    cycle.__cause__ = cycle
    assert extract_sqlstate(cycle) is None


@pytest.mark.asyncio
async def test_s03_worker_outcome_captures_semantic_and_wrapped_database_results() -> (
    None
):
    tracker = ConnectionTracker()

    async def commit_value() -> int:
        tracker.transactions.setdefault("T1", []).append((101, 201))
        tracker.transaction_outcomes.setdefault("T1", []).append("COMMITTED")
        tracker.mark("T1", "COMMITTED")
        return 7

    committed = await capture_worker_outcome(commit_value, tracker, "T1")
    assert committed.returned == 7
    assert committed.transaction_outcome == "COMMITTED"
    assert committed.transaction_outcomes == ("COMMITTED",)
    assert committed.uow_identities == ((101, 201),)

    failure = ApplicationFailure(
        FailureClass.STATE_CONFLICT,
        "relationship_fact_conflict",
        "The fact already exists.",
    )
    failure.__cause__ = _WrappedError("orig", _SqlstateError("23505"))

    async def mapped_failure() -> None:
        tracker.transaction_outcomes.setdefault("T2", []).append("ROLLED_BACK")
        raise failure

    rolled_back = await capture_worker_outcome(mapped_failure, tracker, "T2")
    assert rolled_back.application_failure is failure
    assert rolled_back.sqlstate == "23505"
    assert rolled_back.transaction_outcome == "ROLLED_BACK"
    assert rolled_back.unexpected_exception is None

    reference_failure = ApplicationFailure(
        FailureClass.STATE_CONFLICT,
        "object_template_referenced",
        "The template is still referenced.",
    )
    reference_failure.__cause__ = _WrappedError("orig", _PgcodeError("23503"))

    async def mapped_reference_failure() -> None:
        tracker.transaction_outcomes.setdefault("T3", []).append("ROLLED_BACK")
        raise reference_failure

    reference_rollback = await capture_worker_outcome(
        mapped_reference_failure, tracker, "T3"
    )
    assert reference_rollback.application_failure is reference_failure
    assert reference_rollback.sqlstate == "23503"
    assert reference_rollback.transaction_outcome == "ROLLED_BACK"
    assert reference_rollback.unexpected_exception is None


@pytest.mark.asyncio
async def test_s03_forbidden_sqlstates_fail_immediately_and_are_never_retried() -> None:
    for sqlstate in ("40P01", "40001"):
        tracker = ConnectionTracker()
        attempts = 0

        async def fail_once(sqlstate_to_raise: str = sqlstate) -> None:
            nonlocal attempts
            attempts += 1
            raise _SqlstateError(sqlstate_to_raise)

        with pytest.raises(AssertionError, match=sqlstate):
            await capture_worker_outcome(
                fail_once, tracker, "T1", negative_control=True
            )
        assert attempts == 1
        assert tracker.worker_outcomes[-1].sqlstate == sqlstate

    tracker = ConnectionTracker()
    attempts = 0

    async def negative_control() -> None:
        nonlocal attempts
        attempts += 1
        raise _SqlstateError("40001")

    outcome = await capture_worker_outcome(
        negative_control,
        tracker,
        "T1",
        allow_forbidden_sqlstates=frozenset({"40001"}),
        negative_control=True,
    )
    assert attempts == 1
    assert outcome.sqlstate == "40001"
    assert outcome.unexpected_exception_type == "_SqlstateError"
