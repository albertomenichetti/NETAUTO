"""Deterministic real-PostgreSQL intrinsic Object concurrency scenarios."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import cast
from uuid import UUID

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.ext.asyncio import AsyncConnection

import netauto.application.objects as object_application
import netauto.persistence.locking as locking_persistence
from netauto.application.objects import ObjectService
from netauto.application.objecttemplates import (
    ComponentCandidate,
    ObjectTemplateService,
    PropertyCandidate,
)
from netauto.domain.objects import DataChangeKind, DataChangeOperation, Object
from netauto.domain.objecttemplates import ValueMode
from netauto.failures import ApplicationFailure
from netauto.persistence.locking import AdvisoryGate, RowLockClass, RowLockMode
from netauto.persistence.objects import EventKind, ObjectStore, OwnershipLifecycleEvent
from netauto.persistence.objecttemplates import ObjectTemplateStore
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

type InsertObject = Callable[[ObjectStore, Object], Awaitable[None]]


def _object_services(
    actors: SemanticActors,
) -> tuple[ObjectService, ObjectService]:
    return (
        ObjectService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        ),
        ObjectService(
            ObservedUnitOfWorkFactory(actors.t2_engine, actors.tracker, "T2")
        ),
    )


def _template_services(
    actors: SemanticActors,
) -> tuple[ObjectTemplateService, ObjectTemplateService]:
    return (
        ObjectTemplateService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        ),
        ObjectTemplateService(
            ObservedUnitOfWorkFactory(actors.t2_engine, actors.tracker, "T2")
        ),
    )


def _object_reader(actors: SemanticActors) -> ObjectService:
    return ObjectService(UnitOfWorkFactory(actors.t1_engine))


def _template_reader(actors: SemanticActors) -> ObjectTemplateService:
    return ObjectTemplateService(UnitOfWorkFactory(actors.t1_engine))


async def _template(
    actors: SemanticActors, name: str, *, two_properties: bool = False
) -> UUID:
    datatype = await actors.t1.create(
        "object_concurrency", f"{name}_value", "core.integer", None, {}
    )
    await actors.t1.publish(datatype.datatype.id, 1, 1)
    properties = (
        (
            PropertyCandidate("a", 1, datatype.datatype.id, 1, ValueMode.SCALAR, False),
            PropertyCandidate("b", 2, datatype.datatype.id, 1, ValueMode.SCALAR, False),
        )
        if two_properties
        else ()
    )
    service = _template_reader(actors)
    created = await service.create(
        "object_concurrency", name, False, None, None, None, properties, ()
    )
    await service.publish(created.object_template.id, 1, 1)
    return created.object_template.id


async def _schema_change_template(actors: SemanticActors, name: str) -> UUID:
    datatype = await actors.t1.create(
        "object_concurrency", f"{name}_value", "core.integer", None, {}
    )
    await actors.t1.publish(datatype.datatype.id, 1, 1)
    service = _template_reader(actors)
    first = PropertyCandidate("a", 1, datatype.datatype.id, 1, ValueMode.SCALAR, False)
    created = await service.create(
        "object_concurrency", name, False, None, None, None, (first,), ()
    )
    template_id = created.object_template.id
    await service.publish(template_id, 1, 1)
    await service.create_next(template_id, 1)
    second = PropertyCandidate("b", 2, datatype.datatype.id, 1, ValueMode.SCALAR, False)
    await service.revise(template_id, 2, 1, None, (first, second), ())
    await service.publish(template_id, 2, 2)
    return template_id


async def _ownership_template(actors: SemanticActors, name: str) -> UUID:
    service = _template_reader(actors)
    created = await service.create(
        "object_concurrency", name, False, None, None, None, (), ()
    )
    template_id = created.object_template.id
    await service.publish(template_id, 1, 1)
    await service.create_next(template_id, 1)
    slot = ComponentCandidate("children", 1, template_id)
    await service.revise(template_id, 2, 1, None, (), (slot,))
    await service.publish(template_id, 2, 2)
    await service.create_next(template_id, 2)
    await service.revise(template_id, 3, 1, None, (), ())
    await service.publish(template_id, 3, 2)
    return template_id


def _object_owner_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    return install_lock_plan_cut(
        monkeypatch,
        object_application,
        RowLockClass.OBJECT,
        RowLockMode.NKU,
    )


def _object_delete_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    cut = PhaseCut()
    original = ObjectStore.delete

    async def intercepted(store: ObjectStore, object_id: UUID) -> None:
        await original(store, object_id)
        task = asyncio.current_task()
        if task is not None and task.get_name() == "T1":
            cut.reached.set()
            await cut.release.wait()

    monkeypatch.setattr(ObjectStore, "delete", intercepted)
    return cut


def _ownership_gate_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    cut = PhaseCut()
    original = locking_persistence.acquire_advisory_gate

    async def intercepted(connection: AsyncConnection, gate: AdvisoryGate) -> None:
        await original(connection, gate)
        task = asyncio.current_task()
        if task is not None and task.get_name() == "T1":
            cut.reached.set()
            await cut.release.wait()

    monkeypatch.setattr(locking_persistence, "acquire_advisory_gate", intercepted)
    return cut


def _version_share_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    return install_lock_plan_cut(
        monkeypatch,
        object_application,
        RowLockClass.OBJECT_TEMPLATE_VERSION,
        RowLockMode.S,
    )


def _lineage_share_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    return install_lock_plan_cut(
        monkeypatch,
        object_application,
        RowLockClass.OBJECT_TEMPLATE_HEADER,
        RowLockMode.S,
    )


def _object_insert_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    cut = PhaseCut()
    original = cast(InsertObject, ObjectStore.insert)

    async def intercepted(store: ObjectStore, value: Object) -> None:
        await original(store, value)
        task = asyncio.current_task()
        if task is not None and task.get_name() == "T1":
            cut.reached.set()
            await cut.release.wait()

    monkeypatch.setattr(ObjectStore, "insert", intercepted)
    return cut


def _ownership_insert_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    cut = PhaseCut()
    original = ObjectStore.insert_ownership

    async def intercepted(store: ObjectStore, value: object) -> None:
        await cast(Callable[[ObjectStore, object], Awaitable[None]], original)(
            store, value
        )
        task = asyncio.current_task()
        if task is not None and task.get_name() == "T1":
            cut.reached.set()
            await cut.release.wait()

    monkeypatch.setattr(ObjectStore, "insert_ownership", intercepted)
    return cut


def _lineage_delete_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    cut = PhaseCut()
    original = ObjectTemplateStore.delete_lineage

    async def intercepted(store: ObjectTemplateStore, template_id: UUID) -> None:
        await original(store, template_id)
        task = asyncio.current_task()
        if task is not None and task.get_name() == "T1":
            cut.reached.set()
            await cut.release.wait()

    monkeypatch.setattr(ObjectTemplateStore, "delete_lineage", intercepted)
    return cut


def _failure_code(value: object) -> str | None:
    return value.code if isinstance(value, ApplicationFailure) else None


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_11_data_change_serializes_and_rereads_fresh_state(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-11-OBJECT") as actors:
        template_id = await _template(actors, "row11", two_properties=True)
        reader = _object_reader(actors)
        created = await reader.create(template_id, 1, "row11", {"a": 0, "b": 0})
        first, second = _object_services(actors)
        cut = _object_owner_cut(monkeypatch)
        outcomes = await blocked_race(
            actors,
            cut,
            lambda: first.data_change(
                created.id,
                (DataChangeOperation(DataChangeKind.SET, "a", 1),),
            ),
            lambda: second.data_change(
                created.id,
                (DataChangeOperation(DataChangeKind.SET, "b", 2),),
            ),
        )
        assert all(isinstance(item, Object) for item in outcomes)
        assert (await reader.get(created.id)).properties == {"a": 1, "b": 2}
        events = (
            await reader.list_events(
                kind=None,
                object_id=None,
                destination_object_id=None,
                relationship_id=None,
                relationship_definition_id=None,
                relationship_name=None,
                occurred_from=None,
                occurred_to=None,
                involving_object_id=created.id,
                cursor=None,
                limit=100,
            )
        ).items
        data_events = [item for item in events if item.kind.value == "DATA_CHANGE"]
        assert len(data_events) == 2
        assert data_events[1].before is not None
        assert data_events[1].after is not None
        assert data_events[1].before.properties == {"a": 0, "b": 0}
        assert data_events[1].after.properties == {"a": 1, "b": 0}
        assert data_events[0].before is not None
        assert data_events[0].after is not None
        assert data_events[0].before.properties == {"a": 1, "b": 0}
        assert data_events[0].after.properties == {"a": 1, "b": 2}


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_12_data_change_and_schema_change_share_object_owner(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-12-DATA-SCHEMA") as actors:
        template_id = await _schema_change_template(actors, "row12")
        reader = _object_reader(actors)
        created = await reader.create(template_id, 1, "row12", {"a": 0})
        first, second = _object_services(actors)
        cut = _object_owner_cut(monkeypatch)
        changed, migrated = await blocked_race(
            actors,
            cut,
            lambda: first.data_change(
                created.id,
                (DataChangeOperation(DataChangeKind.SET, "a", 1),),
            ),
            lambda: second.schema_change(created.id, 2),
        )
        assert isinstance(changed, Object)
        assert isinstance(migrated, Object)
        assert migrated.template_version == 2
        assert migrated.properties == {"a": 1}
        events = (
            await reader.list_events(
                kind=None,
                object_id=None,
                destination_object_id=None,
                relationship_id=None,
                relationship_definition_id=None,
                relationship_name=None,
                occurred_from=None,
                occurred_to=None,
                involving_object_id=created.id,
                cursor=None,
                limit=100,
            )
        ).items
        assert [item.kind.value for item in events[:2]] == [
            "SCHEMA_CHANGE",
            "DATA_CHANGE",
        ]
        assert events[0].before is not None
        assert events[0].before.properties == {"a": 1}


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_13_attach_then_schema_change_observes_edge(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-13-ATTACH-SCHEMA") as actors:
        template_id = await _ownership_template(actors, "row13")
        reader = _object_reader(actors)
        parent = await reader.create(template_id, 2, "parent", {})
        child = await reader.create(template_id, 2, "child", {})
        first, second = _object_services(actors)
        cut = _object_owner_cut(monkeypatch)
        attached, migrated = await blocked_race(
            actors,
            cut,
            lambda: first.attach(parent.id, "children", child.id),
            lambda: second.schema_change(parent.id, 3),
        )
        assert getattr(attached, "child_object_id", None) == child.id
        assert _failure_code(migrated) == "schema_change_blocked"
        assert (await reader.get(parent.id)).template_version == 2
        assert (await reader.get_owner(child.id)) is not None


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_13_schema_change_then_attach_observes_removed_slot(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-13-SCHEMA-ATTACH") as actors:
        template_id = await _ownership_template(actors, "row13_reverse")
        reader = _object_reader(actors)
        parent = await reader.create(template_id, 2, "parent", {})
        child = await reader.create(template_id, 2, "child", {})
        first, second = _object_services(actors)
        cut = _object_owner_cut(monkeypatch)
        migrated, attached = await blocked_race(
            actors,
            cut,
            lambda: first.schema_change(parent.id, 3),
            lambda: second.attach(parent.id, "children", child.id),
        )
        assert isinstance(migrated, Object)
        assert migrated.template_version == 3
        assert _failure_code(attached) == "ownership_slot_unavailable"
        assert await reader.get_owner(child.id) is None
        events = (
            await reader.list_events(
                kind=None,
                object_id=None,
                destination_object_id=parent.id,
                relationship_id=None,
                relationship_definition_id=None,
                relationship_name=None,
                occurred_from=None,
                occurred_to=None,
                involving_object_id=None,
                cursor=None,
                limit=100,
            )
        ).items
        assert not any(item.kind.value == "ATTACH_TO" for item in events)


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_gate_01_opposite_attach_uses_fresh_protected_graph(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "GATE-01-OPPOSITE") as actors:
        template_id = await _ownership_template(actors, "gate01")
        reader = _object_reader(actors)
        first_node = await reader.create(template_id, 2, "first", {})
        second_node = await reader.create(template_id, 2, "second", {})
        first, second = _object_services(actors)
        cut = _ownership_gate_cut(monkeypatch)
        forward, reverse = await blocked_race(
            actors,
            cut,
            lambda: first.attach(first_node.id, "children", second_node.id),
            lambda: second.attach(second_node.id, "children", first_node.id),
        )
        assert getattr(forward, "child_object_id", None) == second_node.id
        assert _failure_code(reverse) == "ownership_cycle"
        assert (await reader.get_owner(second_node.id)) is not None
        assert await reader.get_owner(first_node.id) is None


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_gate_02a_rejects_longer_cycle_without_mutating_graph(
    migrated_database_engine: Engine,
    test_database_url: str,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "GATE-02A-LONG-CYCLE") as actors:
        template_id = await _ownership_template(actors, "gate02a")
        reader = _object_reader(actors)
        first_node = await reader.create(template_id, 2, "a", {})
        second_node = await reader.create(template_id, 2, "b", {})
        third_node = await reader.create(template_id, 2, "c", {})
        await reader.attach(first_node.id, "children", second_node.id)
        await reader.attach(second_node.id, "children", third_node.id)

        with pytest.raises(ApplicationFailure) as caught:
            await reader.attach(third_node.id, "children", first_node.id)

        assert caught.value.code == "ownership_cycle"
        assert await reader.get_owner(first_node.id) is None
        second_owner = await reader.get_owner(second_node.id)
        assert second_owner is not None
        assert second_owner.parent_object_id == first_node.id
        third_owner = await reader.get_owner(third_node.id)
        assert third_owner is not None
        assert third_owner.parent_object_id == second_node.id
        events = (
            await reader.list_events(
                kind=None,
                object_id=None,
                destination_object_id=None,
                relationship_id=None,
                relationship_definition_id=None,
                relationship_name=None,
                occurred_from=None,
                occurred_to=None,
                involving_object_id=None,
                cursor=None,
                limit=100,
            )
        ).items
        assert sum(item.kind.value == "ATTACH_TO" for item in events) == 2


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_gate_02b_attach_sees_concurrent_detach_before_cycle_check(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "GATE-02B-DETACH-PATH") as actors:
        template_id = await _ownership_template(actors, "gate02b")
        reader = _object_reader(actors)
        first_node = await reader.create(template_id, 2, "a", {})
        second_node = await reader.create(template_id, 2, "b", {})
        third_node = await reader.create(template_id, 2, "c", {})
        await reader.attach(first_node.id, "children", second_node.id)
        await reader.attach(second_node.id, "children", third_node.id)
        first, second = _object_services(actors)
        cut = _ownership_gate_cut(monkeypatch)

        attached, detached = await progress_race(
            cut,
            lambda: first.attach(third_node.id, "children", first_node.id),
            lambda: second.detach(second_node.id, "children", third_node.id),
        )

        assert getattr(attached, "child_object_id", None) == first_node.id
        assert detached is None
        first_owner = await reader.get_owner(first_node.id)
        assert first_owner is not None
        assert first_owner.parent_object_id == third_node.id
        second_owner = await reader.get_owner(second_node.id)
        assert second_owner is not None
        assert second_owner.parent_object_id == first_node.id
        assert await reader.get_owner(third_node.id) is None
        events = (
            await reader.list_events(
                kind=None,
                object_id=None,
                destination_object_id=None,
                relationship_id=None,
                relationship_definition_id=None,
                relationship_name=None,
                occurred_from=None,
                occurred_to=None,
                involving_object_id=None,
                cursor=None,
                limit=100,
            )
        ).items
        assert sum(item.kind.value == "ATTACH_TO" for item in events) == 3
        assert sum(item.kind.value == "DETACH_FROM" for item in events) == 1


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_12_schema_change_rechecks_source_after_wait(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-12-SCHEMA-SCHEMA") as actors:
        template_id = await _schema_change_template(actors, "row12_schema")
        reader = _object_reader(actors)
        value = await reader.create(template_id, 1, "value", {"a": 1})
        first, second = _object_services(actors)
        cut = _object_owner_cut(monkeypatch)
        winner, waiter = await blocked_race(
            actors,
            cut,
            lambda: first.schema_change(value.id, 2),
            lambda: second.schema_change(value.id, 2),
        )
        assert isinstance(winner, Object)
        assert _failure_code(waiter) == "semantic_validation_failed"
        assert (await reader.get(value.id)).template_version == 2


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_14_detach_then_schema_change_observes_removal(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-14-DETACH-SCHEMA") as actors:
        template_id = await _ownership_template(actors, "row14")
        reader = _object_reader(actors)
        parent = await reader.create(template_id, 2, "parent", {})
        child = await reader.create(template_id, 2, "child", {})
        await reader.attach(parent.id, "children", child.id)
        first, second = _object_services(actors)
        cut = _object_owner_cut(monkeypatch)
        detached, migrated = await blocked_race(
            actors,
            cut,
            lambda: first.detach(parent.id, "children", child.id),
            lambda: second.schema_change(parent.id, 3),
        )
        assert detached is None
        assert isinstance(migrated, Object)
        assert migrated.template_version == 3
        assert await reader.get_owner(child.id) is None


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_14_schema_change_then_detach_removes_exact_edge(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-14-SCHEMA-DETACH") as actors:
        template_id = await _ownership_template(actors, "row14_reverse")
        reader = _object_reader(actors)
        parent = await reader.create(template_id, 2, "parent", {})
        child = await reader.create(template_id, 2, "child", {})
        await reader.attach(parent.id, "children", child.id)
        first, second = _object_services(actors)
        cut = _object_owner_cut(monkeypatch)
        migrated, detached = await blocked_race(
            actors,
            cut,
            lambda: first.schema_change(parent.id, 3),
            lambda: second.detach(parent.id, "children", child.id),
        )
        assert _failure_code(migrated) == "schema_change_blocked"
        assert detached is None
        assert (await reader.get(parent.id)).template_version == 2
        assert await reader.get_owner(child.id) is None
        events = (
            await reader.list_events(
                kind=None,
                object_id=None,
                destination_object_id=None,
                relationship_id=None,
                relationship_definition_id=None,
                relationship_name=None,
                occurred_from=None,
                occurred_to=None,
                involving_object_id=child.id,
                cursor=None,
                limit=100,
            )
        ).items
        assert sum(item.kind.value == "ATTACH_TO" for item in events) == 1
        assert sum(item.kind.value == "DETACH_FROM" for item in events) == 1


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_arb_02_and_gate_03_same_child_reread_after_gate(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ARB-02-GATE-03B") as actors:
        template_id = await _ownership_template(actors, "arb02")
        reader = _object_reader(actors)
        first_parent = await reader.create(template_id, 2, "p1", {})
        second_parent = await reader.create(template_id, 2, "p2", {})
        child = await reader.create(template_id, 2, "child", {})
        first, second = _object_services(actors)
        cut = _ownership_gate_cut(monkeypatch)
        winner, loser = await blocked_race(
            actors,
            cut,
            lambda: first.attach(first_parent.id, "children", child.id),
            lambda: second.attach(second_parent.id, "children", child.id),
        )
        assert getattr(winner, "child_object_id", None) == child.id
        assert _failure_code(loser) == "ownership_conflict"
        owner = await reader.get_owner(child.id)
        assert owner is not None
        assert owner.parent_object_id == first_parent.id


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_arb_04_attach_then_detach_is_serially_explainable(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ARB-04-ATTACH-DETACH") as actors:
        template_id = await _ownership_template(actors, "arb04")
        reader = _object_reader(actors)
        parent = await reader.create(template_id, 2, "parent", {})
        child = await reader.create(template_id, 2, "child", {})
        first, second = _object_services(actors)
        cut = _object_owner_cut(monkeypatch)
        attached, detached = await blocked_race(
            actors,
            cut,
            lambda: first.attach(parent.id, "children", child.id),
            lambda: second.detach(parent.id, "children", child.id),
        )
        assert getattr(attached, "child_object_id", None) == child.id
        assert detached is None
        assert await reader.get_owner(child.id) is None
        events = (
            await reader.list_events(
                kind=None,
                object_id=None,
                destination_object_id=None,
                relationship_id=None,
                relationship_definition_id=None,
                relationship_name=None,
                occurred_from=None,
                occurred_to=None,
                involving_object_id=child.id,
                cursor=None,
                limit=100,
            )
        ).items
        structural = [
            item.kind.value
            for item in events
            if "_TO" in item.kind.value or "_FROM" in item.kind.value
        ]
        assert structural == ["DETACH_FROM", "ATTACH_TO"]


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_par_04_unrelated_real_attaches_share_global_gate(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "PAR-04-GLOBAL-GATE") as actors:
        template_id = await _ownership_template(actors, "par04")
        reader = _object_reader(actors)
        first_parent = await reader.create(template_id, 2, "p1", {})
        first_child = await reader.create(template_id, 2, "c1", {})
        second_parent = await reader.create(template_id, 2, "p2", {})
        second_child = await reader.create(template_id, 2, "c2", {})
        first, second = _object_services(actors)
        cut = _ownership_gate_cut(monkeypatch)
        outcomes = await blocked_race(
            actors,
            cut,
            lambda: first.attach(first_parent.id, "children", first_child.id),
            lambda: second.attach(second_parent.id, "children", second_child.id),
        )
        assert all(
            getattr(item, "child_object_id", None) is not None for item in outcomes
        )


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_arb_03_identical_attach_converges_with_one_event(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ARB-03-IDENTICAL-ATTACH") as actors:
        template_id = await _ownership_template(actors, "arb03")
        reader = _object_reader(actors)
        parent = await reader.create(template_id, 2, "parent", {})
        child = await reader.create(template_id, 2, "child", {})
        first, second = _object_services(actors)
        cut = _object_owner_cut(monkeypatch)
        outcomes = await blocked_race(
            actors,
            cut,
            lambda: first.attach(parent.id, "children", child.id),
            lambda: second.attach(parent.id, "children", child.id),
        )
        assert all(
            getattr(item, "child_object_id", None) == child.id for item in outcomes
        )
        events = (
            await reader.list_events(
                kind=None,
                object_id=None,
                destination_object_id=None,
                relationship_id=None,
                relationship_definition_id=None,
                relationship_name=None,
                occurred_from=None,
                occurred_to=None,
                involving_object_id=child.id,
                cursor=None,
                limit=100,
            )
        ).items
        assert sum(item.kind.value == "ATTACH_TO" for item in events) == 1


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_arb_03b_identical_detach_converges_with_one_event(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ARB-03B-IDENTICAL-DETACH") as actors:
        template_id = await _ownership_template(actors, "arb03b")
        reader = _object_reader(actors)
        parent = await reader.create(template_id, 2, "parent", {})
        child = await reader.create(template_id, 2, "child", {})
        await reader.attach(parent.id, "children", child.id)
        first, second = _object_services(actors)
        cut = _object_owner_cut(monkeypatch)
        outcomes = await blocked_race(
            actors,
            cut,
            lambda: first.detach(parent.id, "children", child.id),
            lambda: second.detach(parent.id, "children", child.id),
        )
        assert all(outcome is None for outcome in outcomes)
        assert await reader.get_owner(child.id) is None
        events = (
            await reader.list_events(
                kind=None,
                object_id=None,
                destination_object_id=None,
                relationship_id=None,
                relationship_definition_id=None,
                relationship_name=None,
                occurred_from=None,
                occurred_to=None,
                involving_object_id=child.id,
                cursor=None,
                limit=100,
            )
        ).items
        assert sum(item.kind.value == "ATTACH_TO" for item in events) == 1
        assert sum(item.kind.value == "DETACH_FROM" for item in events) == 1


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_idempotent_conflict_and_detach_paths_skip_ownership_gate(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "GATE-SKIP-OWNERSHIP") as actors:
        template_id = await _ownership_template(actors, "gate_skip")
        reader = _object_reader(actors)
        first_parent = await reader.create(template_id, 2, "p1", {})
        second_parent = await reader.create(template_id, 2, "p2", {})
        first_child = await reader.create(template_id, 2, "c1", {})
        second_child = await reader.create(template_id, 2, "c2", {})
        await reader.attach(first_parent.id, "children", first_child.id)
        await reader.attach(second_parent.id, "children", second_child.id)

        calls = 0

        async def forbidden_gate(
            connection: AsyncConnection, gate: AdvisoryGate
        ) -> None:
            del connection, gate
            nonlocal calls
            calls += 1
            raise AssertionError("ownership graph gate must not be acquired")

        monkeypatch.setattr(
            locking_persistence, "acquire_advisory_gate", forbidden_gate
        )

        projection = await reader.attach(first_parent.id, "children", first_child.id)
        assert projection.child_object_id == first_child.id
        with pytest.raises(ApplicationFailure) as caught:
            await reader.attach(first_parent.id, "children", second_child.id)
        assert caught.value.code == "ownership_conflict"
        assert await reader.detach(first_parent.id, "children", first_child.id) is None
        assert await reader.detach(first_parent.id, "children", first_child.id) is None
        assert calls == 0
        assert await reader.get_owner(first_child.id) is None
        second_owner = await reader.get_owner(second_child.id)
        assert second_owner is not None
        assert second_owner.parent_object_id == second_parent.id
        events = (
            await reader.list_events(
                kind=None,
                object_id=None,
                destination_object_id=None,
                relationship_id=None,
                relationship_definition_id=None,
                relationship_name=None,
                occurred_from=None,
                occurred_to=None,
                involving_object_id=first_child.id,
                cursor=None,
                limit=100,
            )
        ).items
        assert sum(item.kind.value == "ATTACH_TO" for item in events) == 1
        assert sum(item.kind.value == "DETACH_FROM" for item in events) == 1


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_snap_04_child_rename_progresses_during_attach_parent_hold(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "SNAP-04-OWNERSHIP-NAME") as actors:
        template_id = await _ownership_template(actors, "snap04")
        reader = _object_reader(actors)
        parent = await reader.create(template_id, 2, "parent", {})
        child = await reader.create(template_id, 2, "old-child", {})
        first, second = _object_services(actors)
        cut = _object_owner_cut(monkeypatch)
        attached, renamed = await progress_race(
            cut,
            lambda: first.attach(parent.id, "children", child.id),
            lambda: second.rename(child.id, "new-child"),
        )
        assert getattr(attached, "child_object_id", None) == child.id
        assert isinstance(renamed, Object)
        events = (
            await reader.list_events(
                kind=None,
                object_id=None,
                destination_object_id=None,
                relationship_id=None,
                relationship_definition_id=None,
                relationship_name=None,
                occurred_from=None,
                occurred_to=None,
                involving_object_id=child.id,
                cursor=None,
                limit=100,
            )
        ).items
        attach_event = next(item for item in events if item.kind.value == "ATTACH_TO")
        assert attach_event.canonical_name == "new-child"


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_12_schema_target_admission_lives_through_commit(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-12-TARGET-ADMISSION") as actors:
        template_id = await _schema_change_template(actors, "target_admission")
        reader = _object_reader(actors)
        value = await reader.create(template_id, 1, "value", {"a": 1})
        first, _ = _object_services(actors)
        _, second_template = _template_services(actors)
        cut = _version_share_cut(monkeypatch)
        migrated, deprecated = await blocked_race(
            actors,
            cut,
            lambda: first.schema_change(value.id, 2),
            lambda: second_template.deprecate(template_id, 2),
        )
        assert isinstance(migrated, Object)
        assert _failure_code(deprecated) is None
        assert (await reader.get(value.id)).template_version == 2


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_par_03_parent_rename_and_attach_share_non_key_owner(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "PAR-03-RENAME-ATTACH") as actors:
        template_id = await _ownership_template(actors, "par03")
        reader = _object_reader(actors)
        parent = await reader.create(template_id, 2, "old-parent", {})
        child = await reader.create(template_id, 2, "child", {})
        first, second = _object_services(actors)
        cut = _object_owner_cut(monkeypatch)
        renamed, attached = await blocked_race(
            actors,
            cut,
            lambda: first.rename(parent.id, "new-parent"),
            lambda: second.attach(parent.id, "children", child.id),
        )
        assert isinstance(renamed, Object)
        assert getattr(attached, "child_object_id", None) == child.id
        events = (
            await reader.list_events(
                kind=None,
                object_id=None,
                destination_object_id=parent.id,
                relationship_id=None,
                relationship_definition_id=None,
                relationship_name=None,
                occurred_from=None,
                occurred_to=None,
                involving_object_id=None,
                cursor=None,
                limit=100,
            )
        ).items
        attach_event = next(
            item for item in events if isinstance(item, OwnershipLifecycleEvent)
        )
        assert attach_event.destination_canonical_name == "new-parent"


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_rename_and_data_change_share_non_key_object_owner(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-11-RENAME-DATA") as actors:
        template_id = await _template(actors, "rename_data", two_properties=True)
        reader = _object_reader(actors)
        created = await reader.create(template_id, 1, "old", {"a": 0})
        first, second = _object_services(actors)
        cut = _object_owner_cut(monkeypatch)
        await blocked_race(
            actors,
            cut,
            lambda: first.rename(created.id, "new"),
            lambda: second.data_change(
                created.id,
                (DataChangeOperation(DataChangeKind.SET, "a", 1),),
            ),
        )
        current = await reader.get(created.id)
        assert current.canonical_name == "new"
        assert current.properties == {"a": 1}
        events = (
            await reader.list_events(
                kind=None,
                object_id=None,
                destination_object_id=None,
                relationship_id=None,
                relationship_definition_id=None,
                relationship_name=None,
                occurred_from=None,
                occurred_to=None,
                involving_object_id=created.id,
                cursor=None,
                limit=100,
            )
        ).items
        assert events[0].before is not None
        assert events[0].before.canonical_name == "new"


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_object_non_key_owner_allows_key_share_progress(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "OBJECT-NO-KEY") as actors:
        template_id = await _template(actors, "no_key")
        reader = _object_reader(actors)
        created = await reader.create(template_id, 1, "old", {})
        first, _ = _object_services(actors)
        cut = _object_owner_cut(monkeypatch)
        rename_task = asyncio.create_task(first.rename(created.id, "new"), name="T1")
        await cut.reached.wait()
        async with actors.t2_engine.connect() as connection:
            async with connection.begin():
                async with asyncio.timeout(5):
                    selected = await connection.scalar(
                        text("SELECT id FROM objects WHERE id = :id FOR KEY SHARE"),
                        {"id": created.id},
                    )
                assert selected == created.id
                assert not rename_task.done()
        cut.release.set()
        async with asyncio.timeout(5):
            assert (await rename_task).canonical_name == "new"


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_object_create_exact_admission_blocks_deprecate_until_commit(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "OBJECT-ADMISSION") as actors:
        template_id = await _template(actors, "admission")
        template_reader = _template_reader(actors)
        await template_reader.clear_default(template_id)
        first, _ = _object_services(actors)
        _, second_template = _template_services(actors)
        cut = _version_share_cut(monkeypatch)
        created, deprecated = await blocked_race(
            actors,
            cut,
            lambda: first.create(template_id, 1, "admitted", {}),
            lambda: second_template.deprecate(template_id, 1),
        )
        assert isinstance(created, Object)
        assert isinstance(deprecated, object) and _failure_code(deprecated) is None
        assert (await template_reader.get_version(template_id, 1)).status.value == (
            "DEPRECATED"
        )
        assert (await _object_reader(actors).get(created.id)).template_version == 1


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_implicit_default_selection_is_exact_and_coherent(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "OBJECT-DEFAULT") as actors:
        template_id = await _template(actors, "default_race")
        template_reader = _template_reader(actors)
        version_two = await template_reader.create_next(template_id, 1)
        await template_reader.publish(template_id, version_two.version, 1)
        first, _ = _object_services(actors)
        _, second_template = _template_services(actors)
        cut = _lineage_share_cut(monkeypatch)
        created, selected = await blocked_race(
            actors,
            cut,
            lambda: first.create(template_id, None, "implicit", {}),
            lambda: second_template.set_default(template_id, 2),
        )
        assert isinstance(created, Object)
        assert created.template_version == 1
        assert _failure_code(selected) is None
        assert (await template_reader.get_lineage(template_id)).default_version == 2


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_ref_01_object_exact_otv_fk_both_directions(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "REF-01-OBJECT") as actors:
        template_id = await _template(actors, "reference_first")
        first, _ = _object_services(actors)
        _, second_template = _template_services(actors)
        with monkeypatch.context() as context:
            cut = _object_insert_cut(context)
            created, deleted = await blocked_race(
                actors,
                cut,
                lambda: first.create(template_id, 1, "reference-first", {}),
                lambda: second_template.delete_lineage(template_id),
            )
        assert isinstance(created, Object)
        assert _failure_code(deleted) == "delete_blocked"
        assert await _object_reader(actors).get(created.id) == created

        delete_target = await _template(actors, "delete_first")
        first_template, _ = _template_services(actors)
        _, second_object = _object_services(actors)
        with monkeypatch.context() as context:
            cut = _lineage_delete_cut(context)
            deleted, created_after_delete = await blocked_race(
                actors,
                cut,
                lambda: first_template.delete_lineage(delete_target),
                lambda: second_object.create(delete_target, 1, "delete-first", {}),
            )
        assert deleted is None
        assert _failure_code(created_after_delete) == "referenced_resource_not_found"


@pytest.mark.parametrize("mutation", ["rename", "data_change", "schema_change"])
@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_object_delete_serializes_with_intrinsic_writers_in_both_orders(
    mutation: str,
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(
        test_database_url, f"OBJECT-DELETE-{mutation}"
    ) as actors:
        initial_properties: dict[str, object]
        if mutation == "schema_change":
            template_id = await _schema_change_template(actors, f"delete_{mutation}")
            initial_properties = {"a": 0}
        elif mutation == "data_change":
            template_id = await _template(
                actors, f"delete_{mutation}", two_properties=True
            )
            initial_properties = {"a": 0}
        else:
            template_id = await _template(actors, f"delete_{mutation}")
            initial_properties = {}
        reader = _object_reader(actors)

        async def mutate(service: ObjectService, object_id: UUID) -> object:
            if mutation == "rename":
                return await service.rename(object_id, "latest-name")
            if mutation == "data_change":
                return await service.data_change(
                    object_id,
                    (DataChangeOperation(DataChangeKind.SET, "a", 1),),
                )
            return await service.schema_change(object_id, 2)

        writer_first = await reader.create(
            template_id, 1, "writer-first", initial_properties
        )
        first, second = _object_services(actors)
        with monkeypatch.context() as context:
            cut = _object_owner_cut(context)
            written, deleted = await blocked_race(
                actors,
                cut,
                lambda: mutate(first, writer_first.id),
                lambda: second.delete(writer_first.id),
            )
        assert isinstance(written, Object)
        assert deleted is None
        with pytest.raises(ApplicationFailure) as missing:
            await reader.get(writer_first.id)
        assert missing.value.code == "resource_not_found"
        events = (
            await reader.list_events(
                kind=EventKind.DELETED,
                object_id=writer_first.id,
                destination_object_id=None,
                relationship_id=None,
                relationship_definition_id=None,
                relationship_name=None,
                occurred_from=None,
                occurred_to=None,
                involving_object_id=None,
                cursor=None,
                limit=10,
            )
        ).items
        assert len(events) == 1
        deleted_event = events[0]
        assert deleted_event.before == written
        assert deleted_event.after is None

        delete_first = await reader.create(
            template_id, 1, "delete-first", initial_properties
        )
        first, second = _object_services(actors)
        with monkeypatch.context() as context:
            cut = _object_delete_cut(context)
            deleted, later_write = await blocked_race(
                actors,
                cut,
                lambda: first.delete(delete_first.id),
                lambda: mutate(second, delete_first.id),
            )
        assert deleted is None
        assert _failure_code(later_write) == "resource_not_found"


@pytest.mark.parametrize("deleted_role", ["parent", "child"])
@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_ref_02_attach_and_object_delete_arbitrate_both_lifetime_orders(
    deleted_role: str,
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, f"REF-02-{deleted_role}") as actors:
        template_id = await _ownership_template(actors, f"ref02_{deleted_role}")
        reader = _object_reader(actors)

        async def pair(prefix: str) -> tuple[Object, Object]:
            return (
                await reader.create(template_id, 2, f"{prefix}-parent", {}),
                await reader.create(template_id, 2, f"{prefix}-child", {}),
            )

        parent, child = await pair("reference-first")
        target = parent if deleted_role == "parent" else child
        first, second = _object_services(actors)
        with monkeypatch.context() as context:
            cut = _ownership_insert_cut(context)
            attached, deleted = await blocked_race(
                actors,
                cut,
                lambda: first.attach(parent.id, "children", child.id),
                lambda: second.delete(target.id),
            )
        assert _failure_code(attached) is None
        assert _failure_code(deleted) == "delete_blocked"
        assert isinstance(deleted, ApplicationFailure)
        assert deleted.details == {
            "resource_type": "object",
            "id": str(target.id),
            "blockers": [{"type": "ownership", "count": 1}],
        }
        await reader.detach(parent.id, "children", child.id)

        parent, child = await pair("delete-first")
        target = parent if deleted_role == "parent" else child
        first, second = _object_services(actors)
        with monkeypatch.context() as context:
            cut = _object_delete_cut(context)
            deleted, attached = await blocked_race(
                actors,
                cut,
                lambda: first.delete(target.id),
                lambda: second.attach(parent.id, "children", child.id),
            )
        assert deleted is None
        expected = (
            "resource_not_found"
            if deleted_role == "parent"
            else "referenced_resource_not_found"
        )
        assert _failure_code(attached) == expected


@pytest.mark.parametrize("deleted_role", ["parent", "child"])
@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_ref_05_detach_removes_final_object_delete_blocker(
    deleted_role: str,
    migrated_database_engine: Engine,
    test_database_url: str,
) -> None:
    del migrated_database_engine
    async with semantic_actors(
        test_database_url, f"REF-05-DETACH-{deleted_role}"
    ) as actors:
        template_id = await _ownership_template(actors, f"ref05_{deleted_role}")
        reader = _object_reader(actors)
        parent = await reader.create(template_id, 2, "parent", {})
        child = await reader.create(template_id, 2, "child", {})
        await reader.attach(parent.id, "children", child.id)
        target = parent if deleted_role == "parent" else child
        with pytest.raises(ApplicationFailure) as conservative:
            await reader.delete(target.id)
        assert conservative.value.code == "delete_blocked"
        await reader.detach(parent.id, "children", child.id)
        await reader.delete(target.id)
        with pytest.raises(ApplicationFailure) as missing:
            await reader.get(target.id)
        assert missing.value.code == "resource_not_found"
