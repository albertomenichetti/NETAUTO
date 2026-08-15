"""Deterministic real-PostgreSQL intrinsic Object concurrency scenarios."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import cast
from uuid import UUID

import pytest
from sqlalchemy import Engine, text

from netauto.application.objects import ObjectService
from netauto.application.objecttemplates import ObjectTemplateService, PropertyCandidate
from netauto.domain.objects import DataChangeKind, DataChangeOperation, Object
from netauto.domain.objecttemplates import ValueMode
from netauto.failures import ApplicationFailure
from netauto.persistence.objects import ObjectStore
from netauto.persistence.objecttemplates import ObjectTemplateStore
from netauto.persistence.uow import UnitOfWorkFactory
from tests.support.semantic_concurrency import (
    ObservedUnitOfWorkFactory,
    PhaseCut,
    SemanticActors,
    blocked_race,
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


def _object_owner_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    cut = PhaseCut()
    original = ObjectStore.lock_no_key

    async def intercepted(store: ObjectStore, object_id: UUID) -> Object | None:
        result = await original(store, object_id)
        task = asyncio.current_task()
        if task is not None and task.get_name() == "T1":
            cut.reached.set()
            await cut.release.wait()
        return result

    monkeypatch.setattr(ObjectStore, "lock_no_key", intercepted)
    return cut


def _version_share_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    cut = PhaseCut()
    original = ObjectTemplateStore.lock_version_share

    async def intercepted(
        store: ObjectTemplateStore, template_id: UUID, version: int
    ) -> bool:
        result = await original(store, template_id, version)
        task = asyncio.current_task()
        if task is not None and task.get_name() == "T1":
            cut.reached.set()
            await cut.release.wait()
        return result

    monkeypatch.setattr(ObjectTemplateStore, "lock_version_share", intercepted)
    return cut


def _lineage_share_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    cut = PhaseCut()
    original = ObjectTemplateStore.lock_lineage_share

    async def intercepted(store: ObjectTemplateStore, template_id: UUID) -> bool:
        result = await original(store, template_id)
        task = asyncio.current_task()
        if task is not None and task.get_name() == "T1":
            cut.reached.set()
            await cut.release.wait()
        return result

    monkeypatch.setattr(ObjectTemplateStore, "lock_lineage_share", intercepted)
    return cut


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
