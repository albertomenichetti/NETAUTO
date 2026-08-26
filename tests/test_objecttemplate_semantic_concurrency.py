"""Canonical ObjectTemplate semantic races on independent PostgreSQL sessions."""

import asyncio
from collections.abc import Awaitable, Callable, Iterable
from typing import cast
from uuid import UUID

import pytest
from sqlalchemy import Engine
from sqlalchemy.ext.asyncio import AsyncConnection

import netauto.application.objecttemplates as objecttemplate_application
from netauto.application.objects import ObjectService
from netauto.application.objecttemplates import (
    ComponentCandidate,
    ObjectTemplateService,
    PropertyCandidate,
)
from netauto.domain.datatypes import VersionStatus
from netauto.domain.objects import Object
from netauto.domain.objecttemplates import (
    CreateObjectTemplateResult,
    LocalComponent,
    LocalProperty,
    ObjectTemplate,
    ObjectTemplateVersion,
    ValueMode,
)
from netauto.failures import ApplicationFailure
from netauto.persistence.locking import (
    AdvisoryGate,
    LockPlan,
    RowLockClass,
    RowLockIntent,
    RowLockMode,
)
from netauto.persistence.objecttemplates import ObjectTemplateStore
from netauto.persistence.uow import UnitOfWorkFactory
from tests.support.semantic_concurrency import (
    ObservedUnitOfWorkFactory,
    PhaseCut,
    SemanticActors,
    blocked_race,
    capture,
    install_lock_plan_cut,
    progress_race,
    run_worker,
    semantic_actors,
)

type InsertDeclarations = Callable[
    [
        ObjectTemplateStore,
        UUID,
        int,
        tuple[LocalProperty, ...],
        tuple[LocalComponent, ...],
    ],
    Awaitable[None],
]


def _services(
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


def _reader(actors: SemanticActors) -> ObjectTemplateService:
    return ObjectTemplateService(UnitOfWorkFactory(actors.t1_engine))


async def _published_datatype(actors: SemanticActors, name: str) -> UUID:
    created = await actors.t1.create("ot_concurrency", name, "core.integer", None, {})
    await actors.t1.publish(created.datatype.id, 1, 1)
    return created.datatype.id


async def _root(
    service: ObjectTemplateService,
    name: str,
    *,
    properties: tuple[PropertyCandidate, ...] = (),
    components: tuple[ComponentCandidate, ...] = (),
) -> UUID:
    created = await service.create(
        "ot_concurrency", name, False, None, None, None, properties, components
    )
    return created.object_template.id


def _failure_code(value: object) -> str | None:
    return value.code if isinstance(value, ApplicationFailure) else None


def _lineage_no_key_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    return install_lock_plan_cut(
        monkeypatch,
        objecttemplate_application,
        RowLockClass.OBJECT_TEMPLATE_HEADER,
        RowLockMode.NKU,
    )


def _version_no_key_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    return install_lock_plan_cut(
        monkeypatch,
        objecttemplate_application,
        RowLockClass.OBJECT_TEMPLATE_VERSION,
        RowLockMode.NKU,
    )


def _description_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    cut = PhaseCut()
    original = ObjectTemplateStore.set_description

    async def intercepted(
        store: ObjectTemplateStore, template_id: UUID, description: str | None
    ) -> object:
        result = await original(store, template_id, description)
        task = asyncio.current_task()
        if task is not None and task.get_name() == "T1":
            cut.reached.set()
            await cut.release.wait()
        return result

    monkeypatch.setattr(ObjectTemplateStore, "set_description", intercepted)
    return cut


def _datatype_share_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    return install_lock_plan_cut(
        monkeypatch,
        objecttemplate_application,
        RowLockClass.DATA_TYPE_VERSION,
        RowLockMode.S,
    )


def _datatype_lineage_share_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    return install_lock_plan_cut(
        monkeypatch,
        objecttemplate_application,
        RowLockClass.DATA_TYPE_HEADER,
        RowLockMode.S,
    )


def _template_share_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    return install_lock_plan_cut(
        monkeypatch,
        objecttemplate_application,
        RowLockClass.OBJECT_TEMPLATE_HEADER,
        RowLockMode.S,
    )


def _template_version_share_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    return install_lock_plan_cut(
        monkeypatch,
        objecttemplate_application,
        RowLockClass.OBJECT_TEMPLATE_VERSION,
        RowLockMode.S,
    )


def _status_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    cut = PhaseCut()
    original = ObjectTemplateStore.set_status

    async def intercepted(
        store: ObjectTemplateStore,
        template_id: UUID,
        version: int,
        status: VersionStatus,
    ) -> None:
        await original(store, template_id, version, status)
        task = asyncio.current_task()
        if task is not None and task.get_name() == "T1":
            cut.reached.set()
            await cut.release.wait()

    monkeypatch.setattr(ObjectTemplateStore, "set_status", intercepted)
    return cut


def _reference_precheck_cut(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[PhaseCut, list[dict[str, int]]]:
    cut = PhaseCut()
    observations: list[dict[str, int]] = []
    original = ObjectTemplateStore.external_reference_counts

    async def intercepted(
        store: ObjectTemplateStore, template_id: UUID
    ) -> dict[str, int]:
        result = await original(store, template_id)
        task = asyncio.current_task()
        if task is not None and task.get_name() == "T1":
            observations.append(result)
            cut.reached.set()
            await cut.release.wait()
        return result

    monkeypatch.setattr(ObjectTemplateStore, "external_reference_counts", intercepted)
    return cut, observations


def _lineage_delete_plan_cut(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[PhaseCut, list[dict[str, int]]]:
    cut = PhaseCut()
    observations: list[dict[str, int]] = []
    original_prepare = objecttemplate_application.prepare_lock_plan
    original_counts = ObjectTemplateStore.external_reference_counts

    async def intercepted_prepare(
        connection: AsyncConnection,
        *,
        intents: Iterable[RowLockIntent] = (),
        gate: AdvisoryGate | None = None,
    ) -> LockPlan:
        requested = tuple(intents)
        task = asyncio.current_task()
        if (
            task is not None
            and task.get_name() == "T1"
            and gate is AdvisoryGate.MODEL_ROOT_DELETE_GATE
            and any(
                item.key.row_class is RowLockClass.OBJECT_TEMPLATE_HEADER
                and item.mode is RowLockMode.U
                for item in requested
            )
        ):
            cut.reached.set()
            await cut.release.wait()
        return await original_prepare(connection, intents=requested, gate=gate)

    async def observed_counts(
        store: ObjectTemplateStore, template_id: UUID
    ) -> dict[str, int]:
        result = await original_counts(store, template_id)
        observations.append(result)
        return result

    monkeypatch.setattr(
        objecttemplate_application, "prepare_lock_plan", intercepted_prepare
    )
    monkeypatch.setattr(
        ObjectTemplateStore, "external_reference_counts", observed_counts
    )
    return cut, observations


def _aggregate_created_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    cut = PhaseCut()
    original = ObjectTemplateStore.create

    async def intercepted(
        store: ObjectTemplateStore,
        lineage: ObjectTemplate,
        version: ObjectTemplateVersion,
    ) -> None:
        await original(store, lineage, version)
        task = asyncio.current_task()
        if task is not None and task.get_name() == "T1":
            cut.reached.set()
            await cut.release.wait()

    monkeypatch.setattr(ObjectTemplateStore, "create", intercepted)
    return cut


def _lineage_deleted_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
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


def _version_projection_read_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    cut = PhaseCut()
    original = ObjectTemplateStore.project_version

    async def intercepted(
        store: ObjectTemplateStore, template_id: UUID, version: int
    ) -> ObjectTemplateVersion | None:
        result = await original(store, template_id, version)
        task = asyncio.current_task()
        if task is not None and task.get_name() == "T1":
            cut.reached.set()
            await cut.release.wait()
        return result

    monkeypatch.setattr(ObjectTemplateStore, "project_version", intercepted)
    return cut


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_01_ot_create_next_allocates_serial_versions(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-01-OT") as actors:
        first, second = _services(actors)
        template_id = await _root(first, "row_01")
        await first.publish(template_id, 1, 1)
        cut = _lineage_no_key_cut(monkeypatch)
        outcomes = await blocked_race(
            actors,
            cut,
            lambda: first.create_next(template_id, 1),
            lambda: second.create_next(template_id, 1),
        )
        assert {
            value.version
            for value in outcomes
            if isinstance(value, ObjectTemplateVersion)
        } == {2, 3}


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_02_ot_create_next_reuses_serially_deleted_max(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-02-OT") as actors:
        first, second = _services(actors)
        template_id = await _root(first, "row_02")
        await first.publish(template_id, 1, 1)
        await first.create_next(template_id, 1)
        cut = _lineage_no_key_cut(monkeypatch)
        deleted, created = await blocked_race(
            actors,
            cut,
            lambda: first.delete_draft(template_id, 2, 1),
            lambda: second.create_next(template_id, 1),
        )
        assert deleted is None
        assert isinstance(created, ObjectTemplateVersion)
        assert created.version == 2


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_03_ot_revise_same_generation_has_one_stale_loser(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-03-OT") as actors:
        first, second = _services(actors)
        template_id = await _root(first, "row_03")
        cut = _version_no_key_cut(monkeypatch)
        outcomes = await blocked_race(
            actors,
            cut,
            lambda: first.revise(template_id, 1, 1, None, (), ()),
            lambda: second.revise(template_id, 1, 1, None, (), ()),
        )
        assert {_failure_code(value) for value in outcomes} == {None, "stale_revision"}
        current = await _reader(actors).get_version(template_id, 1)
        assert current.revision == 2


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_04b_ot_publish_serializes_delete_draft(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-04B-OT") as actors:
        first, second = _services(actors)
        template_id = await _root(first, "row_04b")
        cut = _version_no_key_cut(monkeypatch)
        published, deleted = await blocked_race(
            actors,
            cut,
            lambda: first.publish(template_id, 1, 1),
            lambda: second.delete_draft(template_id, 1, 1),
        )
        assert isinstance(published, ObjectTemplateVersion)
        assert _failure_code(deleted) == "lifecycle_state_conflict"
        assert (
            await _reader(actors).get_version(template_id, 1)
        ).status is VersionStatus.PUBLISHED


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_04a_ot_revise_serializes_publish_and_forces_fresh_revision(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-04A-OT") as actors:
        first, second = _services(actors)
        template_id = await _root(first, "row_04a")
        cut = _version_no_key_cut(monkeypatch)
        revised, published = await blocked_race(
            actors,
            cut,
            lambda: first.revise(template_id, 1, 1, None, (), ()),
            lambda: second.publish(template_id, 1, 1),
        )
        assert isinstance(revised, ObjectTemplateVersion)
        assert _failure_code(published) == "stale_revision"
        current = await _reader(actors).get_version(template_id, 1)
        assert current.revision == 2
        assert current.status is VersionStatus.DRAFT


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_05_ot_first_serial_publisher_becomes_default(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-05-OT") as actors:
        first, second = _services(actors)
        template_id = await _root(first, "row_05")
        await first.publish(template_id, 1, 1)
        await first.create_next(template_id, 1)
        await first.create_next(template_id, 1)
        await first.clear_default(template_id)
        cut = _lineage_no_key_cut(monkeypatch)
        outcomes = await blocked_race(
            actors,
            cut,
            lambda: first.publish(template_id, 2, 1),
            lambda: second.publish(template_id, 3, 1),
        )
        assert all(isinstance(value, ObjectTemplateVersion) for value in outcomes)
        assert (await first.get_lineage(template_id)).default_version == 2


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_06_ot_set_default_serializes_target_deprecation(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-06-OT") as actors:
        first, second = _services(actors)
        template_id = await _root(first, "row_06")
        await first.publish(template_id, 1, 1)
        await first.create_next(template_id, 1)
        await first.publish(template_id, 2, 1)
        cut = _lineage_no_key_cut(monkeypatch)
        defaulted, deprecated = await blocked_race(
            actors,
            cut,
            lambda: first.set_default(template_id, 2),
            lambda: second.deprecate(template_id, 2),
        )
        assert not isinstance(defaulted, ApplicationFailure)
        assert _failure_code(deprecated) == "default_version_conflict"
        assert (await first.get_lineage(template_id)).default_version == 2


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_15_and_par_07_description_lock_topology(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-15-OT") as actors:
        first, second = _services(actors)
        template_id = await _root(first, "row_15")
        cut = _description_cut(monkeypatch)
        await blocked_race(
            actors,
            cut,
            lambda: first.set_description(template_id, "first"),
            lambda: second.set_description(template_id, "second"),
        )
        assert (await first.get_lineage(template_id)).description == "second"

    monkeypatch.undo()
    async with semantic_actors(test_database_url, "PAR-07B-OT") as actors:
        first, second = _services(actors)
        template_id = await _root(first, "par_07b")
        cut = _description_cut(monkeypatch)
        description, revision = await progress_race(
            cut,
            lambda: first.set_description(template_id, "metadata"),
            lambda: second.revise(template_id, 1, 1, None, (), ()),
        )
        assert not isinstance(description, ApplicationFailure)
        assert isinstance(revision, ObjectTemplateVersion)

    monkeypatch.undo()
    async with semantic_actors(test_database_url, "PAR-07A-OT") as actors:
        first, second = _services(actors)
        template_id = await _root(first, "par_07a")
        await first.publish(template_id, 1, 1)
        cut = _description_cut(monkeypatch)
        description, defaulted = await blocked_race(
            actors,
            cut,
            lambda: first.set_description(template_id, "metadata"),
            lambda: second.set_default(template_id, 1),
        )
        assert not isinstance(description, ApplicationFailure)
        assert not isinstance(defaulted, ApplicationFailure)


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_par_06_ot_deprecates_distinct_versions_without_lineage_contention(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "PAR-06-OT") as actors:
        first, second = _services(actors)
        template_id = await _root(first, "par_06")
        await first.publish(template_id, 1, 1)
        await first.create_next(template_id, 1)
        await first.publish(template_id, 2, 1)
        await first.clear_default(template_id)
        cut = _template_share_cut(monkeypatch)
        first_result, second_result = await progress_race(
            cut,
            lambda: first.deprecate(template_id, 1),
            lambda: second.deprecate(template_id, 2),
        )
        assert isinstance(first_result, ObjectTemplateVersion)
        assert isinstance(second_result, ObjectTemplateVersion)


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_07_explicit_binding_stabilizes_dtv_until_consumer_commit(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-07-OT") as actors:
        first, _ = _services(actors)
        datatype_id = await _published_datatype(actors, "row_07")
        await actors.t1.clear_default(datatype_id)
        cut = _datatype_share_cut(monkeypatch)
        created, deprecated = await blocked_race(
            actors,
            cut,
            lambda: first.create(
                "ot_concurrency",
                "row_07_consumer",
                False,
                None,
                None,
                None,
                (
                    PropertyCandidate(
                        "value",
                        1,
                        datatype_id,
                        1,
                        ValueMode.SCALAR,
                        False,
                    ),
                ),
                (),
            ),
            lambda: actors.t2.deprecate(datatype_id, 1),
        )
        assert not isinstance(created, ApplicationFailure)
        assert not isinstance(deprecated, ApplicationFailure)
        assert (
            await actors.t1.get_version(datatype_id, 1)
        ).status is VersionStatus.DEPRECATED


@pytest.mark.parametrize("default_action", ["set", "clear"])
@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_08_implicit_binding_materializes_one_serial_default(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
    default_action: str,
) -> None:
    del migrated_database_engine
    scenario_id = "ROW-08A-OT" if default_action == "set" else "ROW-08B-OT"
    async with semantic_actors(test_database_url, scenario_id) as actors:
        first, _ = _services(actors)
        datatype_id = await _published_datatype(actors, f"row_08_{default_action}")
        await actors.t1.create_next(datatype_id, 1)
        await actors.t1.publish(datatype_id, 2, 1)
        cut = _datatype_lineage_share_cut(monkeypatch)

        async def change_default() -> object:
            if default_action == "set":
                return await actors.t2.set_default(datatype_id, 2)
            return await actors.t2.clear_default(datatype_id)

        created, changed = await blocked_race(
            actors,
            cut,
            lambda: first.create(
                "ot_concurrency",
                f"row_08_consumer_{default_action}",
                False,
                None,
                None,
                None,
                (
                    PropertyCandidate(
                        "value",
                        1,
                        datatype_id,
                        None,
                        ValueMode.SCALAR,
                        False,
                    ),
                ),
                (),
            ),
            change_default,
        )
        assert not isinstance(created, ApplicationFailure)
        assert not isinstance(changed, ApplicationFailure)
        assert isinstance(created, CreateObjectTemplateResult)
        assert created.version.properties[0].datatype_version == 1


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_09_publish_property_rendezvous_with_dependency_deprecate(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-09-DTV") as actors:
        first, _ = _services(actors)
        datatype_id = await _published_datatype(actors, "row_09")
        await actors.t1.clear_default(datatype_id)
        template_id = await _root(
            first,
            "row_09",
            properties=(
                PropertyCandidate(
                    "value",
                    1,
                    datatype_id,
                    1,
                    ValueMode.SCALAR,
                    False,
                ),
            ),
        )
        cut = _datatype_share_cut(monkeypatch)
        published, deprecated = await blocked_race(
            actors,
            cut,
            lambda: first.publish(template_id, 1, 1),
            lambda: actors.t2.deprecate(datatype_id, 1),
        )
        assert isinstance(published, ObjectTemplateVersion)
        assert _failure_code(deprecated) == "active_dependency_conflict"
        assert (
            await actors.t1.get_version(datatype_id, 1)
        ).status is VersionStatus.PUBLISHED


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_09_publish_child_rendezvous_with_parent_deprecate(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-09-PARENT") as actors:
        first, second = _services(actors)
        parent_id = await _root(first, "row_09_parent")
        await first.publish(parent_id, 1, 1)
        child = await first.create(
            "ot_concurrency",
            "row_09_child",
            False,
            None,
            parent_id,
            1,
            (),
            (),
        )
        await first.clear_default(parent_id)
        cut = _template_version_share_cut(monkeypatch)
        published, deprecated = await blocked_race(
            actors,
            cut,
            lambda: first.publish(child.object_template.id, 1, 1),
            lambda: second.deprecate(parent_id, 1),
        )
        assert isinstance(published, ObjectTemplateVersion)
        assert _failure_code(deprecated) == "active_dependency_conflict"


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_10_active_removal_is_conservative_during_dependency_deprecate(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-10A-OT") as actors:
        first, _ = _services(actors)
        datatype_id = await _published_datatype(actors, "row_10a")
        consumer_id = await _root(
            first,
            "row_10a_consumer",
            properties=(
                PropertyCandidate("value", 1, datatype_id, 1, ValueMode.SCALAR, False),
            ),
        )
        await first.publish(consumer_id, 1, 1)
        await first.clear_default(consumer_id)
        await actors.t1.clear_default(datatype_id)
        cut = _status_cut(monkeypatch)
        removed, dependency = await progress_race(
            cut,
            lambda: first.deprecate(consumer_id, 1),
            lambda: actors.t2.deprecate(datatype_id, 1),
        )
        assert isinstance(removed, ObjectTemplateVersion)
        assert _failure_code(dependency) == "active_dependency_conflict"

    monkeypatch.undo()
    async with semantic_actors(test_database_url, "ROW-10B-OT") as actors:
        first, _ = _services(actors)
        datatype_id = await _published_datatype(actors, "row_10b")
        consumer_id = await _root(
            first,
            "row_10b_consumer",
            properties=(
                PropertyCandidate("value", 1, datatype_id, 1, ValueMode.SCALAR, False),
            ),
        )
        await first.publish(consumer_id, 1, 1)
        await actors.t1.clear_default(datatype_id)
        cut, _ = _reference_precheck_cut(monkeypatch)
        removed, dependency = await progress_race(
            cut,
            lambda: first.delete_lineage(consumer_id),
            lambda: actors.t2.deprecate(datatype_id, 1),
        )
        assert removed is None
        assert _failure_code(dependency) == "active_dependency_conflict"


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_ref_06b_object_template_cascade_loses_to_object_restrict(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "REF-06B-OT-CASCADE") as actors:
        first, _ = _services(actors)
        datatype_id = await _published_datatype(actors, "ref_06b_value")
        template_id = await _root(
            first,
            "ref_06b",
            properties=(
                PropertyCandidate("value", 1, datatype_id, 1, ValueMode.SCALAR, False),
            ),
        )
        await first.publish(template_id, 1, 1)
        second_version = await first.create_next(template_id, 1)
        assert second_version.version == 2
        cut, precheck_counts = _lineage_delete_plan_cut(monkeypatch)
        object_service = ObjectService(UnitOfWorkFactory(actors.t2_engine))
        deleted, created = await progress_race(
            cut,
            lambda: first.delete_lineage(template_id),
            lambda: object_service.create(template_id, 1, "concurrent-reference", {}),
        )
        assert precheck_counts == [
            {
                "child_object_template": 0,
                "object_template_component": 0,
                "object": 1,
                "relationship_resolution": 0,
            }
        ]
        assert isinstance(created, Object)
        assert isinstance(deleted, ApplicationFailure)
        assert deleted.code == "delete_blocked"
        assert deleted.details == {
            "resource_type": "object_template",
            "id": str(template_id),
            "blockers": [{"type": "object", "count": 1}],
        }
        assert (await first.get_lineage(template_id)).id == template_id
        versions = await first.list_versions(
            template_id, status=None, cursor=None, limit=10
        )
        assert [item.version for item in versions.items] == [1, 2]
        persisted_v1 = await first.get_version(template_id, 1)
        assert [(item.name, item.datatype_id) for item in persisted_v1.properties] == [
            ("value", datatype_id)
        ]
        assert await object_service.get(created.id) == created


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_ref_01_component_reference_creation_blocks_target_delete(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "REF-01-OT") as actors:
        first, second = _services(actors)
        target_id = await _root(first, "ref_target")
        cut = _aggregate_created_cut(monkeypatch)
        created, deleted = await blocked_race(
            actors,
            cut,
            lambda: first.create(
                "ot_concurrency",
                "ref_consumer",
                False,
                None,
                None,
                None,
                (),
                (ComponentCandidate("slot", 1, target_id),),
            ),
            lambda: second.delete_lineage(target_id),
        )
        assert not isinstance(created, ApplicationFailure)
        assert _failure_code(deleted) == "delete_blocked"
        assert (await first.get_lineage(target_id)).id == target_id


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_ref_01_target_delete_winner_rejects_component_reference(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "REF-01-OT-DELETE-FIRST") as actors:
        first, second = _services(actors)
        target_id = await _root(first, "ref_delete_first_target")
        cut = _lineage_deleted_cut(monkeypatch)
        deleted, created = await blocked_race(
            actors,
            cut,
            lambda: first.delete_lineage(target_id),
            lambda: second.create(
                "ot_concurrency",
                "ref_delete_first_consumer",
                False,
                None,
                None,
                None,
                (),
                (ComponentCandidate("slot", 1, target_id),),
            ),
        )
        assert deleted is None
        assert _failure_code(created) == "referenced_resource_not_found"
        consumers = await second.list_lineages(
            namespace="ot_concurrency",
            name="ref_delete_first_consumer",
            abstract=None,
            parent_template_id=None,
            parent_filter_set=False,
            cursor=None,
            limit=10,
        )
        assert consumers.items == []


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_component_self_reference_does_not_contend_with_description(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "PAR-REF-OT") as actors:
        first, second = _services(actors)
        template_id = await _root(first, "self_component")
        cut = _description_cut(monkeypatch)
        description, revised = await progress_race(
            cut,
            lambda: first.set_description(template_id, "metadata"),
            lambda: second.revise(
                template_id,
                1,
                1,
                None,
                (),
                (ComponentCandidate("self_slot", 1, template_id),),
            ),
        )
        assert not isinstance(description, ApplicationFailure)
        assert isinstance(revised, ObjectTemplateVersion)
        assert revised.components[0].target_template_id == template_id


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_composite_exact_read_never_mixes_candidate_generations(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "SNAP-OTV") as actors:
        first, second = _services(actors)
        datatype_id = await _published_datatype(actors, "snapshot_value")
        template_id = await _root(
            first,
            "snapshot_consumer",
            properties=(
                PropertyCandidate("before", 1, datatype_id, 1, ValueMode.SCALAR, False),
            ),
        )
        cut = _version_projection_read_cut(monkeypatch)
        read_task = asyncio.create_task(
            _reader(actors).get_version(template_id, 1), name="T1"
        )
        await cut.reached.wait()
        revised = await second.revise(
            template_id,
            1,
            1,
            None,
            (PropertyCandidate("after", 1, datatype_id, 1, ValueMode.SCALAR, False),),
            (),
        )
        assert revised.revision == 2
        cut.release.set()
        async with asyncio.timeout(5):
            observed = await read_task
        assert observed.revision == 1
        assert [item.name for item in observed.properties] == ["before"]
        current = await _reader(actors).get_version(template_id, 1)
        assert current.revision == 2
        assert [item.name for item in current.properties] == ["after"]


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_ref_01_property_reference_creation_blocks_datatype_delete(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "REF-01-DTV") as actors:
        first, _ = _services(actors)
        datatype_id = await _published_datatype(actors, "ref_datatype")
        await actors.t1.clear_default(datatype_id)
        cut = _datatype_share_cut(monkeypatch)
        created, deleted = await blocked_race(
            actors,
            cut,
            lambda: first.create(
                "ot_concurrency",
                "ref_property_consumer",
                False,
                None,
                None,
                None,
                (
                    PropertyCandidate(
                        "value",
                        1,
                        datatype_id,
                        1,
                        ValueMode.SCALAR,
                        False,
                    ),
                ),
                (),
            ),
            lambda: actors.t2.delete_lineage(datatype_id),
        )
        assert isinstance(created, CreateObjectTemplateResult)
        assert _failure_code(deleted) == "delete_blocked"
        assert (await actors.t1.get_lineage(datatype_id)).id == datatype_id


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_16_revise_serializes_whole_lineage_delete(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-16-OT") as actors:
        first, second = _services(actors)
        template_id = await _root(first, "row_16")
        cut = _version_no_key_cut(monkeypatch)
        revised, deleted = await blocked_race(
            actors,
            cut,
            lambda: first.revise(template_id, 1, 1, None, (), ()),
            lambda: second.delete_lineage(template_id),
        )
        assert isinstance(revised, ObjectTemplateVersion)
        assert deleted is None
        with pytest.raises(ApplicationFailure) as failure:
            await first.get_lineage(template_id)
        assert failure.value.code == "resource_not_found"


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_arb_01_ot_qualified_name_uses_unique_final_authority(
    migrated_database_engine: Engine,
    test_database_url: str,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ARB-01-OT") as actors:
        first, second = _services(actors)
        outcomes = await asyncio.gather(
            capture(lambda: _root(first, "same_name")),
            capture(lambda: _root(second, "same_name")),
        )
        assert sum(isinstance(value, UUID) for value in outcomes) == 1
        assert [_failure_code(value) for value in outcomes].count(
            "qualified_name_conflict"
        ) == 1


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_atomic_01_failed_multirow_revise_rolls_back_complete_generation(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ATOMIC-01-OT") as actors:
        first, _ = _services(actors)
        datatype_id = await _published_datatype(actors, "atomic_value")
        template_id = await _root(first, "atomic")
        original = cast(
            InsertDeclarations,
            vars(ObjectTemplateStore)["_insert_declarations"],
        )

        async def fail_after_real_insert(
            store: ObjectTemplateStore,
            target_id: UUID,
            version: int,
            properties: tuple[LocalProperty, ...],
            components: tuple[LocalComponent, ...],
        ) -> None:
            await original(
                store,
                target_id,
                version,
                properties,
                components,
            )
            raise RuntimeError("forced persistence phase failure")

        monkeypatch.setattr(
            ObjectTemplateStore, "_insert_declarations", fail_after_real_insert
        )
        with pytest.raises(RuntimeError, match="forced persistence phase failure"):
            await run_worker(
                lambda: first.revise(
                    template_id,
                    1,
                    1,
                    None,
                    (
                        PropertyCandidate(
                            "value",
                            1,
                            datatype_id,
                            1,
                            ValueMode.SCALAR,
                            False,
                        ),
                    ),
                    (),
                ),
                actors.tracker,
                "T1",
            )
        monkeypatch.undo()
        current = await _reader(actors).get_version(template_id, 1)
        assert current.revision == 1
        assert current.properties == ()
        assert current.components == ()
