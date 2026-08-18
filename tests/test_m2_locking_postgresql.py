"""Real-PostgreSQL M2-S00 planner and failure-boundary evidence."""

import asyncio
from collections.abc import Iterable
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Connection, Engine, event, func, insert, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

import netauto.application.objects as object_application
import netauto.persistence.locking as locking
from netauto.application.datatypes import DataTypeService
from netauto.application.objects import ObjectService
from netauto.application.objecttemplates import (
    ComponentCandidate,
    ObjectTemplateService,
    PropertyCandidate,
)
from netauto.application.relationshipdefinitions import RelationshipDefinitionService
from netauto.application.relationships import RelationshipService
from netauto.domain.objects import DataChangeKind, DataChangeOperation
from netauto.domain.objecttemplates import ValueMode
from netauto.domain.relationships import RelationshipPerspective, ResolutionRename
from netauto.failures import ApplicationFailure, FailureClass
from netauto.persistence.locking import (
    AdvisoryGate,
    LockPlan,
    ObjectTemplateAncestryError,
    PostgreSQLFailureKind,
    RowLockClass,
    RowLockIntent,
    RowLockKey,
    RowLockMode,
    acquire_lock_plan,
    classify_postgresql_failure,
    prepare_lock_plan,
    reset_uow_lock_phase,
)
from netauto.persistence.metadata import (
    datatype_versions,
    datatypes,
    object_lifecycle_events,
    object_templates,
    objects,
)
from netauto.persistence.relationships import RelationshipDefinitionStore
from netauto.persistence.uow import UnitOfWorkFactory
from tests.support.pg_harness import PgWorker, WorkerRole, wait_for_blocker
from tests.support.semantic_concurrency import (
    ConnectionTracker,
    ObservedUnitOfWorkFactory,
    PhaseCut,
)


def _header_intent(
    row_class: RowLockClass, resource_id: UUID, mode: RowLockMode
) -> RowLockIntent:
    return RowLockIntent(RowLockKey(row_class, resource_id), mode)


def _insert_datatype(connection: Connection, datatype_id: UUID, name: str) -> None:
    connection.execute(
        insert(datatypes).values(
            id=datatype_id,
            namespace="m2_locking",
            name=name,
            description=None,
            default_version=None,
        )
    )
    connection.execute(
        insert(datatype_versions).values(
            datatype_id=datatype_id,
            version=1,
            revision=1,
            status="DRAFT",
            base_type="core.string",
            constraints={},
        )
    )


@pytest.mark.postgresql
async def test_plan_01_real_postgresql_lock_modes_and_missing_keys(
    migrated_database_engine: Engine, test_database_url: str
) -> None:
    datatype_id = uuid4()
    with migrated_database_engine.begin() as connection:
        _insert_datatype(connection, datatype_id, "plan01")

    engine = create_async_engine(test_database_url, isolation_level="READ COMMITTED")
    try:
        for mode in RowLockMode:
            async with engine.begin() as connection:
                reset_uow_lock_phase(connection)
                key = RowLockKey(RowLockClass.DATA_TYPE_VERSION, datatype_id, version=1)
                plan = await prepare_lock_plan(
                    connection, intents=(RowLockIntent(key, mode),)
                )
                assert await acquire_lock_plan(connection, plan) == ()

        missing_id = uuid4()
        async with engine.begin() as connection:
            reset_uow_lock_phase(connection)
            key = RowLockKey(RowLockClass.DATA_TYPE_HEADER, missing_id)
            plan = await prepare_lock_plan(
                connection, intents=(RowLockIntent(key, RowLockMode.KS),)
            )
            assert await acquire_lock_plan(connection, plan) == (key,)
    finally:
        await engine.dispose()


@pytest.mark.postgresql
async def test_plan_02_targeted_ancestry_is_one_query_and_deduplicates(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, first_child, second_child = uuid4(), uuid4(), uuid4()
    unrelated = tuple(uuid4() for _ in range(12))
    with migrated_database_engine.begin() as connection:
        connection.execute(
            insert(object_templates),
            [
                {
                    "id": root,
                    "namespace": "m2_locking",
                    "name": "root",
                    "description": None,
                    "abstract": False,
                    "default_version": None,
                    "parent_template_id": None,
                },
                {
                    "id": first_child,
                    "namespace": "m2_locking",
                    "name": "first_child",
                    "description": None,
                    "abstract": False,
                    "default_version": None,
                    "parent_template_id": root,
                },
                {
                    "id": second_child,
                    "namespace": "m2_locking",
                    "name": "second_child",
                    "description": None,
                    "abstract": False,
                    "default_version": None,
                    "parent_template_id": root,
                },
                *(
                    {
                        "id": lineage_id,
                        "namespace": "m2_locking",
                        "name": f"unrelated_{index}",
                        "description": None,
                        "abstract": False,
                        "default_version": None,
                        "parent_template_id": None,
                    }
                    for index, lineage_id in enumerate(unrelated)
                ),
            ],
        )

    engine = create_async_engine(test_database_url, isolation_level="READ COMMITTED")
    ancestry_statements: list[str] = []
    loaded_material: list[dict[UUID, UUID | None]] = []
    original_loader = locking.load_object_template_ancestry

    def observe_statement(
        connection: object,
        cursor: object,
        statement: str,
        parameters: object,
        context: object,
        executemany: bool,
    ) -> None:
        del connection, cursor, parameters, context, executemany
        if "planned_object_template_ancestry" in statement:
            ancestry_statements.append(statement)

    async def observed_loader(
        connection: AsyncConnection, lineage_ids: Iterable[UUID]
    ) -> dict[UUID, UUID | None]:
        loaded = await original_loader(connection, lineage_ids)
        loaded_material.append(loaded)
        return loaded

    event.listen(engine.sync_engine, "before_cursor_execute", observe_statement)
    monkeypatch.setattr(locking, "load_object_template_ancestry", observed_loader)
    try:
        async with engine.begin() as connection:
            reset_uow_lock_phase(connection)
            intents = tuple(
                _header_intent(
                    RowLockClass.OBJECT_TEMPLATE_HEADER,
                    lineage_id,
                    RowLockMode.KS,
                )
                for lineage_id in (second_child, first_child)
            )
            plan = await prepare_lock_plan(connection, intents=intents)
            assert await acquire_lock_plan(connection, plan) == ()
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", observe_statement)
        await engine.dispose()

    assert len(ancestry_statements) == 1
    assert loaded_material == [{root: None, first_child: root, second_child: root}]
    assert set(loaded_material[0]).isdisjoint(unrelated)
    assert tuple(item.key.resource_id for item in plan.rows) == tuple(
        sorted((first_child, second_child), key=lambda value: value.int)
    )


@pytest.mark.postgresql
async def test_plan_02_missing_template_header_is_plannable(
    migrated_database_engine: Engine, test_database_url: str
) -> None:
    del migrated_database_engine
    missing_id = uuid4()
    engine = create_async_engine(test_database_url, isolation_level="READ COMMITTED")
    try:
        async with engine.begin() as connection:
            reset_uow_lock_phase(connection)
            key = RowLockKey(RowLockClass.OBJECT_TEMPLATE_HEADER, missing_id)
            plan = await prepare_lock_plan(
                connection, intents=(RowLockIntent(key, RowLockMode.KS),)
            )
            assert await acquire_lock_plan(connection, plan) == (key,)
    finally:
        await engine.dispose()


@pytest.mark.postgresql
@pytest.mark.parametrize("corruption", ["missing_parent", "cycle"])
async def test_plan_02_corrupt_template_ancestry_is_rejected(
    migrated_database_engine: Engine,
    test_database_url: str,
    corruption: str,
) -> None:
    first, second = uuid4(), uuid4()
    with migrated_database_engine.begin() as connection:
        if corruption == "missing_parent":
            connection.execute(
                text(
                    "ALTER TABLE object_templates "
                    "DROP CONSTRAINT fk_object_templates_parent"
                )
            )
            rows = [
                {
                    "id": first,
                    "namespace": "m2_locking",
                    "name": "missing_parent_child",
                    "description": None,
                    "abstract": False,
                    "default_version": None,
                    "parent_template_id": second,
                }
            ]
        else:
            rows = [
                {
                    "id": first,
                    "namespace": "m2_locking",
                    "name": "cycle_first",
                    "description": None,
                    "abstract": False,
                    "default_version": None,
                    "parent_template_id": None,
                },
                {
                    "id": second,
                    "namespace": "m2_locking",
                    "name": "cycle_second",
                    "description": None,
                    "abstract": False,
                    "default_version": None,
                    "parent_template_id": first,
                },
            ]
        connection.execute(insert(object_templates), rows)
        if corruption == "cycle":
            connection.execute(
                update(object_templates)
                .where(object_templates.c.id == first)
                .values(parent_template_id=second)
            )

    engine = create_async_engine(test_database_url, isolation_level="READ COMMITTED")
    try:
        async with engine.begin() as connection:
            with pytest.raises(ObjectTemplateAncestryError):
                await prepare_lock_plan(
                    connection,
                    intents=(
                        _header_intent(
                            RowLockClass.OBJECT_TEMPLATE_HEADER,
                            first,
                            RowLockMode.KS,
                        ),
                    ),
                )
    finally:
        await engine.dispose()


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_plan_03_real_application_stale_plan_uses_fresh_uow(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    engine = create_async_engine(test_database_url, isolation_level="READ COMMITTED")
    factory = UnitOfWorkFactory(engine)
    templates = ObjectTemplateService(factory)
    template = await templates.create(
        "m2_locking", "stale_default", False, None, None, None, (), ()
    )
    template_id = template.object_template.id
    await templates.publish(template_id, 1, 1)
    await templates.create_next(template_id, 1)
    await templates.publish(template_id, 2, 1)

    tracker = ConnectionTracker()
    cut = PhaseCut()
    cut_used = False
    original_prepare = object_application.prepare_lock_plan

    async def intercepted_prepare(
        connection: AsyncConnection,
        *,
        intents: Iterable[RowLockIntent] = (),
        gate: AdvisoryGate | None = None,
    ) -> LockPlan:
        nonlocal cut_used
        requested = tuple(intents)
        task = asyncio.current_task()
        if (
            not cut_used
            and task is not None
            and task.get_name() == "T1"
            and any(
                item.key.row_class is RowLockClass.OBJECT_TEMPLATE_VERSION
                and item.key.version == 1
                for item in requested
            )
        ):
            cut_used = True
            cut.reached.set()
            await cut.release.wait()
        return await original_prepare(connection, intents=requested, gate=gate)

    monkeypatch.setattr(object_application, "prepare_lock_plan", intercepted_prepare)
    objects_service = ObjectService(ObservedUnitOfWorkFactory(engine, tracker, "T1"))
    task = asyncio.create_task(
        objects_service.create(template_id, None, "stale-plan-object", {}),
        name="T1",
    )
    try:
        await cut.reached.wait()
        await templates.set_default(template_id, 2)
    finally:
        cut.release.set()
    created = await task
    try:
        assert created.template_version == 2
        identities = tracker.transactions["T1"]
        assert len(identities) == 2
        assert len({transaction_id for _, transaction_id in identities}) == 2
        async with engine.connect() as connection:
            assert (
                await connection.scalar(select(func.count()).select_from(objects)) == 1
            )
            assert (
                await connection.scalar(
                    select(func.count())
                    .select_from(object_lifecycle_events)
                    .where(
                        object_lifecycle_events.c.object_id == created.id,
                        object_lifecycle_events.c.kind == "CREATED",
                    )
                )
                == 1
            )
    finally:
        await engine.dispose()


@pytest.mark.postgresql
async def test_plan_04_real_constraint_failures_classify_after_rollback(
    migrated_database_engine: Engine, test_database_url: str
) -> None:
    datatype_id = uuid4()
    with migrated_database_engine.begin() as connection:
        _insert_datatype(connection, datatype_id, "plan04")

    engine = create_async_engine(test_database_url, isolation_level="READ COMMITTED")
    factory = UnitOfWorkFactory(engine)
    failures: list[tuple[IntegrityError, PostgreSQLFailureKind, str]] = []
    try:
        with pytest.raises(IntegrityError) as unique_info:
            async with factory() as uow:
                await uow.connection.execute(
                    insert(datatypes).values(
                        id=uuid4(),
                        namespace="m2_locking",
                        name="plan04",
                        description=None,
                        default_version=None,
                    )
                )
        failures.append(
            (
                unique_info.value,
                PostgreSQLFailureKind.UNIQUE_VIOLATION,
                "uq_datatypes_namespace_name",
            )
        )

        with pytest.raises(IntegrityError) as foreign_key_info:
            async with factory() as uow:
                await uow.connection.execute(
                    insert(datatype_versions).values(
                        datatype_id=uuid4(),
                        version=1,
                        revision=1,
                        status="DRAFT",
                        base_type="core.string",
                        constraints={},
                    )
                )
        failures.append(
            (
                foreign_key_info.value,
                PostgreSQLFailureKind.FOREIGN_KEY_VIOLATION,
                "fk_datatype_versions_datatype",
            )
        )

        for error, kind, constraint in failures:
            classified = classify_postgresql_failure(error)
            assert classified.kind is kind
            assert classified.constraint_name == constraint

        async with factory() as uow:
            assert (
                await uow.connection.scalar(select(func.count()).select_from(datatypes))
                == 1
            )

        service = DataTypeService(factory)
        with pytest.raises(ApplicationFailure) as public_info:
            await service.create("m2_locking", "plan04", "core.string", None, {})
        public = public_info.value
        assert public.failure_class is FailureClass.STATE_CONFLICT
        assert public.code == "qualified_name_conflict"
        public_material = f"{public.message} {public.details}"
        assert "23505" not in public_material
        assert "uq_datatypes_namespace_name" not in public_material
        assert "datatypes" not in public_material
    finally:
        await engine.dispose()


@pytest.mark.postgresql
async def test_plan_02_non_template_mutations_skip_planner_ancestry(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    engine = create_async_engine(test_database_url, isolation_level="READ COMMITTED")
    factory = UnitOfWorkFactory(engine)
    datatypes_service = DataTypeService(factory)
    templates = ObjectTemplateService(factory)
    objects_service = ObjectService(factory)
    definitions = RelationshipDefinitionService(factory)
    relationships_service = RelationshipService(factory)
    try:
        datatype = await datatypes_service.create(
            "m2_locking", "mutation_value", "core.integer", None, {}
        )
        await datatypes_service.publish(datatype.datatype.id, 1, 1)
        target = await templates.create(
            "m2_locking", "mutation_target", False, None, None, None, (), ()
        )
        await templates.publish(target.object_template.id, 1, 1)
        parent = await templates.create(
            "m2_locking",
            "mutation_parent",
            False,
            None,
            None,
            None,
            (
                PropertyCandidate(
                    "value",
                    1,
                    datatype.datatype.id,
                    1,
                    ValueMode.SCALAR,
                    False,
                ),
            ),
            (ComponentCandidate("child", 1, target.object_template.id),),
        )
        await templates.publish(parent.object_template.id, 1, 1)
        parent_object = await objects_service.create(
            parent.object_template.id, 1, "mutation-parent", {"value": 1}
        )
        child_object = await objects_service.create(
            target.object_template.id, 1, "mutation-child", {}
        )
        definition = await definitions.create_non_symmetric(
            (
                RelationshipPerspective(parent.object_template.id, "contains"),
                RelationshipPerspective(target.object_template.id, "contained_by"),
            )
        )

        planner_calls: list[tuple[UUID, ...]] = []
        semantic_reads = 0
        original_loader = locking.load_object_template_ancestry
        original_lineage_parents = RelationshipDefinitionStore.lineage_parents

        async def observed_loader(
            connection: AsyncConnection, lineage_ids: Iterable[UUID]
        ) -> dict[UUID, UUID | None]:
            requested = tuple(lineage_ids)
            planner_calls.append(requested)
            return await original_loader(connection, requested)

        async def observed_lineage_parents(
            store: RelationshipDefinitionStore,
        ) -> dict[UUID, UUID | None]:
            nonlocal semantic_reads
            semantic_reads += 1
            return await original_lineage_parents(store)

        monkeypatch.setattr(locking, "load_object_template_ancestry", observed_loader)
        monkeypatch.setattr(
            RelationshipDefinitionStore,
            "lineage_parents",
            observed_lineage_parents,
        )

        await objects_service.rename(parent_object.id, "mutation-parent-renamed")
        await objects_service.data_change(
            parent_object.id,
            (DataChangeOperation(DataChangeKind.SET, "value", 2),),
        )
        await objects_service.attach(parent_object.id, "child", child_object.id)
        await objects_service.detach(parent_object.id, "child", child_object.id)

        first_resolution, second_resolution = definition.resolutions
        renamed = await definitions.rename_non_symmetric(
            definition.id,
            (
                ResolutionRename(first_resolution.id, "renamed_1"),
                ResolutionRename(second_resolution.id, "renamed_2"),
            ),
        )
        selected_resolution = next(
            item
            for item in renamed.resolutions
            if item.from_template_id == parent.object_template.id
        )
        relationship = await relationships_service.create(
            selected_resolution.id, parent_object.id, child_object.id
        )
        await relationships_service.delete(relationship.relationship.id)
        await definitions.delete(definition.id)
        await objects_service.delete(parent_object.id)
        await objects_service.delete(child_object.id)

        assert planner_calls == []
        assert semantic_reads >= 3
    finally:
        await engine.dispose()


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_plan_06_real_gate_waiter_holds_no_planned_row_lock(
    migrated_database_engine: Engine, test_database_url: str
) -> None:
    first_id, second_id = uuid4(), uuid4()
    with migrated_database_engine.begin() as connection:
        _insert_datatype(connection, first_id, "plan06_first")
        _insert_datatype(connection, second_id, "plan06_second")

    scenario = "PLAN-06-GATE-ROW"
    t1 = await PgWorker.open(test_database_url, scenario, WorkerRole.T1)
    t2 = await PgWorker.open(test_database_url, scenario, WorkerRole.T2)
    t3 = await PgWorker.open(test_database_url, scenario, WorkerRole.T3)
    observer = await PgWorker.open(test_database_url, scenario, WorkerRole.OBS)
    t2_read_after_acquire = False

    async def acquire_second() -> None:
        nonlocal t2_read_after_acquire
        plan = await prepare_lock_plan(
            t2.connection,
            gate=AdvisoryGate.MODEL_ROOT_DELETE_GATE,
            intents=(
                _header_intent(RowLockClass.DATA_TYPE_HEADER, second_id, RowLockMode.U),
            ),
        )
        assert await acquire_lock_plan(t2.connection, plan) == ()
        assert (
            await t2.connection.scalar(
                select(datatypes.c.id).where(datatypes.c.id == second_id)
            )
            == second_id
        )
        t2_read_after_acquire = True

    try:
        first_plan = await prepare_lock_plan(
            t1.connection,
            gate=AdvisoryGate.MODEL_ROOT_DELETE_GATE,
            intents=(
                _header_intent(RowLockClass.DATA_TYPE_HEADER, first_id, RowLockMode.U),
            ),
        )
        assert await acquire_lock_plan(t1.connection, first_plan) == ()

        second_task = asyncio.create_task(acquire_second(), name="T2")
        assert t1.backend_pid in await wait_for_blocker(
            observer, t2.backend_pid, t1.backend_pid
        )

        third_plan = await prepare_lock_plan(
            t3.connection,
            intents=(
                _header_intent(RowLockClass.DATA_TYPE_HEADER, second_id, RowLockMode.U),
            ),
        )
        async with asyncio.timeout(5):
            assert await acquire_lock_plan(t3.connection, third_plan) == ()

        await t1.rollback()
        assert t3.backend_pid in await wait_for_blocker(
            observer, t2.backend_pid, t3.backend_pid
        )
        await t3.rollback()
        async with asyncio.timeout(5):
            await second_task
        assert t2_read_after_acquire
    finally:
        await t1.close()
        await t2.close()
        await t3.close()
        await observer.close()
