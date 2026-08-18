"""Kernel-level semantic outcomes for canonical S02 PostgreSQL races."""

import asyncio
from collections.abc import AsyncGenerator, Awaitable, Callable, Iterable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Engine, func, select, text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

import netauto.application.datatypes as datatype_application
from netauto.application.datatypes import DataTypeService
from netauto.application.objecttemplates import ObjectTemplateService, PropertyCandidate
from netauto.domain.datatypes import DataTypeVersion, VersionStatus
from netauto.domain.objecttemplates import CreateObjectTemplateResult, ValueMode
from netauto.failures import ApplicationFailure
from netauto.persistence.datatypes import DataTypeStore
from netauto.persistence.locking import (
    AdvisoryGate,
    LockPlan,
    RowLockClass,
    RowLockIntent,
    RowLockMode,
)
from netauto.persistence.metadata import datatype_versions, datatypes
from netauto.persistence.uow import UnitOfWork, UnitOfWorkFactory
from tests.support.pg_harness import PgWorker, WorkerRole, wait_for_blocker
from tests.support.semantic_concurrency import PhaseCut, install_lock_plan_cut

Operation = Callable[[], Awaitable[object]]


@dataclass(slots=True)
class Actors:
    t1: DataTypeService
    t2: DataTypeService
    t1_engine: AsyncEngine
    t2_engine: AsyncEngine
    observer: PgWorker
    t1_name: str
    t2_name: str
    tracker: ConnectionTracker


@dataclass(slots=True)
class ConnectionTracker:
    pids: dict[str, int] = field(default_factory=lambda: {})
    ready: dict[str, asyncio.Event] = field(
        default_factory=lambda: {"T1": asyncio.Event(), "T2": asyncio.Event()}
    )

    def reset(self) -> None:
        self.ready = {"T1": asyncio.Event(), "T2": asyncio.Event()}


class ObservedUnitOfWork(UnitOfWork):
    def __init__(
        self, engine: AsyncEngine, tracker: ConnectionTracker, role: str
    ) -> None:
        super().__init__(engine)
        self._tracker = tracker
        self._role = role

    async def __aenter__(self) -> UnitOfWork:
        entered = await super().__aenter__()
        pid = await self.connection.scalar(text("SELECT pg_backend_pid()"))
        self._tracker.pids[self._role] = int(pid)
        self._tracker.ready[self._role].set()
        return entered


class ObservedUnitOfWorkFactory(UnitOfWorkFactory):
    def __init__(
        self, engine: AsyncEngine, tracker: ConnectionTracker, role: str
    ) -> None:
        super().__init__(engine)
        self._observed_engine = engine
        self._tracker = tracker
        self._role = role

    def __call__(self) -> UnitOfWork:
        return ObservedUnitOfWork(self._observed_engine, self._tracker, self._role)


def _service_engine(database_url: str, application_name: str) -> AsyncEngine:
    return create_async_engine(
        database_url,
        isolation_level="READ COMMITTED",
        connect_args={"application_name": application_name},
    )


@asynccontextmanager
async def _actors(database_url: str, scenario_id: str) -> AsyncGenerator[Actors]:
    t1_name = f"netauto-semantic:{scenario_id}:T1"
    t2_name = f"netauto-semantic:{scenario_id}:T2"
    t1_engine = _service_engine(database_url, t1_name)
    t2_engine = _service_engine(database_url, t2_name)
    observer = await PgWorker.open(database_url, scenario_id, WorkerRole.OBS)
    tracker = ConnectionTracker()
    try:
        yield Actors(
            DataTypeService(ObservedUnitOfWorkFactory(t1_engine, tracker, "T1")),
            DataTypeService(ObservedUnitOfWorkFactory(t2_engine, tracker, "T2")),
            t1_engine,
            t2_engine,
            observer,
            t1_name,
            t2_name,
            tracker,
        )
    finally:
        await observer.close()
        await t1_engine.dispose()
        await t2_engine.dispose()


async def _capture(operation: Operation) -> object:
    try:
        return await operation()
    except ApplicationFailure as failure:
        return failure


async def _blocked_race(
    actors: Actors, cut: PhaseCut, first: Operation, second: Operation
) -> tuple[object, object]:
    actors.tracker.reset()
    t1 = asyncio.create_task(_capture(first), name="T1")
    await cut.reached.wait()
    t2 = asyncio.create_task(_capture(second), name="T2")
    await actors.tracker.ready["T1"].wait()
    await actors.tracker.ready["T2"].wait()
    t1_pid = actors.tracker.pids["T1"]
    t2_pid = actors.tracker.pids["T2"]
    blockers = await wait_for_blocker(actors.observer, t2_pid, t1_pid)
    assert t1_pid in blockers
    cut.release.set()
    async with asyncio.timeout(5):
        first_outcome, second_outcome = await asyncio.gather(t1, t2)
    return first_outcome, second_outcome


async def _progress_race(
    cut: PhaseCut, first: Operation, second: Operation
) -> tuple[object, object]:
    t1 = asyncio.create_task(_capture(first), name="T1")
    await cut.reached.wait()
    async with asyncio.timeout(5):
        second_outcome = await _capture(second)
    assert not t1.done()
    cut.release.set()
    async with asyncio.timeout(5):
        first_outcome = await t1
    return first_outcome, second_outcome


def _install_lineage_no_key_cut(
    monkeypatch: pytest.MonkeyPatch,
) -> PhaseCut:
    return install_lock_plan_cut(
        monkeypatch,
        datatype_application,
        RowLockClass.DATA_TYPE_HEADER,
        RowLockMode.NKU,
    )


def _install_lineage_share_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    return install_lock_plan_cut(
        monkeypatch,
        datatype_application,
        RowLockClass.DATA_TYPE_HEADER,
        RowLockMode.S,
    )


def _install_version_no_key_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    return install_lock_plan_cut(
        monkeypatch,
        datatype_application,
        RowLockClass.DATA_TYPE_VERSION,
        RowLockMode.NKU,
    )


def _install_description_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    cut = PhaseCut()
    original = DataTypeStore.set_description

    async def intercepted(
        store: DataTypeStore, datatype_id: UUID, description: str | None
    ) -> object:
        result = await original(store, datatype_id, description)
        task = asyncio.current_task()
        if task is not None and task.get_name() == "T1":
            cut.reached.set()
            await cut.release.wait()
        return result

    monkeypatch.setattr(DataTypeStore, "set_description", intercepted)
    return cut


def _install_reference_precheck_cut(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[PhaseCut, list[int]]:
    cut = PhaseCut()
    observations: list[int] = []
    original_prepare = datatype_application.prepare_lock_plan
    original_count = DataTypeStore.external_reference_count

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
                item.key.row_class is RowLockClass.DATA_TYPE_HEADER
                and item.mode is RowLockMode.U
                for item in requested
            )
        ):
            cut.reached.set()
            await cut.release.wait()
        return await original_prepare(connection, intents=requested, gate=gate)

    async def intercepted(store: DataTypeStore, datatype_id: UUID) -> int:
        result = await original_count(store, datatype_id)
        observations.append(result)
        return result

    monkeypatch.setattr(datatype_application, "prepare_lock_plan", intercepted_prepare)
    monkeypatch.setattr(DataTypeStore, "external_reference_count", intercepted)
    return cut, observations


async def _create(
    service: DataTypeService, name: str, constraints: object | None = None
) -> UUID:
    created = await service.create(
        "semantic_concurrency",
        name,
        "core.integer",
        None,
        {} if constraints is None else constraints,
    )
    return created.datatype.id


async def _published_v1(service: DataTypeService, name: str) -> UUID:
    datatype_id = await _create(service, name)
    await service.publish(datatype_id, 1, 1)
    return datatype_id


def _failure_code(outcome: object) -> str | None:
    return outcome.code if isinstance(outcome, ApplicationFailure) else None


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_01_create_next_allocates_distinct_serial_versions(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with _actors(test_database_url, "ROW-01") as actors:
        datatype_id = await _published_v1(actors.t1, "row_01")
        cut = _install_lineage_no_key_cut(monkeypatch)
        outcomes = await _blocked_race(
            actors,
            cut,
            lambda: actors.t1.create_next(datatype_id, 1),
            lambda: actors.t2.create_next(datatype_id, 1),
        )
        assert {
            outcome.version
            for outcome in outcomes
            if isinstance(outcome, DataTypeVersion)
        } == {2, 3}
        versions = await actors.t1.list_versions(
            datatype_id, status=None, cursor=None, limit=10
        )
        assert [item.version for item in versions.items] == [1, 2, 3]


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_02_create_next_reuses_deleted_max_after_wait(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with _actors(test_database_url, "ROW-02") as actors:
        datatype_id = await _published_v1(actors.t1, "row_02")
        await actors.t1.create_next(datatype_id, 1)
        cut = _install_lineage_no_key_cut(monkeypatch)
        deleted, created = await _blocked_race(
            actors,
            cut,
            lambda: actors.t1.delete_draft(datatype_id, 2, 1),
            lambda: actors.t2.create_next(datatype_id, 1),
        )
        assert deleted is None
        assert isinstance(created, DataTypeVersion) and created.version == 2
        assert (await actors.t1.get_version(datatype_id, 2)).revision == 1


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_03_only_one_revise_applies_to_generation(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with _actors(test_database_url, "ROW-03") as actors:
        datatype_id = await _create(actors.t1, "row_03")
        cut = _install_version_no_key_cut(monkeypatch)
        outcomes = await _blocked_race(
            actors,
            cut,
            lambda: actors.t1.revise(datatype_id, 1, 1, {"minimum": 10}),
            lambda: actors.t2.revise(datatype_id, 1, 1, {"maximum": 20}),
        )
        assert sorted(_failure_code(outcome) or "success" for outcome in outcomes) == [
            "stale_revision",
            "success",
        ]
        final = await actors.t1.get_version(datatype_id, 1)
        assert final.revision == 2
        assert final.constraints in ({"minimum": 10}, {"maximum": 20})


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_04a_revise_publish_same_generation_is_serial(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with _actors(test_database_url, "ROW-04A") as actors:
        datatype_id = await _create(actors.t1, "row_04a")
        cut = _install_version_no_key_cut(monkeypatch)
        outcomes = await _blocked_race(
            actors,
            cut,
            lambda: actors.t1.revise(datatype_id, 1, 1, {"minimum": 4}),
            lambda: actors.t2.publish(datatype_id, 1, 1),
        )
        assert sorted(_failure_code(outcome) or "success" for outcome in outcomes) == [
            "stale_revision",
            "success",
        ]
        final = await actors.t1.get_version(datatype_id, 1)
        assert (final.status, final.revision, final.constraints) == (
            VersionStatus.DRAFT,
            2,
            {"minimum": 4},
        )


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_04b_publish_delete_draft_same_generation_is_serial(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with _actors(test_database_url, "ROW-04B") as actors:
        datatype_id = await _create(actors.t1, "row_04b")
        cut = _install_version_no_key_cut(monkeypatch)
        outcomes = await _blocked_race(
            actors,
            cut,
            lambda: actors.t1.publish(datatype_id, 1, 1),
            lambda: actors.t2.delete_draft(datatype_id, 1, 1),
        )
        assert sorted(_failure_code(outcome) or "success" for outcome in outcomes) == [
            "lifecycle_state_conflict",
            "success",
        ]
        final = await actors.t1.get_version(datatype_id, 1)
        assert final.status is VersionStatus.PUBLISHED


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_05_first_serial_publish_sets_stable_default(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with _actors(test_database_url, "ROW-05") as actors:
        datatype_id = await _published_v1(actors.t1, "row_05")
        await actors.t1.create_next(datatype_id, 1)
        await actors.t1.create_next(datatype_id, 1)
        await actors.t1.clear_default(datatype_id)
        cut = _install_lineage_no_key_cut(monkeypatch)
        outcomes = await _blocked_race(
            actors,
            cut,
            lambda: actors.t1.publish(datatype_id, 2, 1),
            lambda: actors.t2.publish(datatype_id, 3, 1),
        )
        assert all(isinstance(outcome, DataTypeVersion) for outcome in outcomes)
        assert (await actors.t1.get_lineage(datatype_id)).default_version == 2
        assert (
            await actors.t1.get_version(datatype_id, 2)
        ).status is VersionStatus.PUBLISHED
        assert (
            await actors.t1.get_version(datatype_id, 3)
        ).status is VersionStatus.PUBLISHED


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_06_default_never_points_to_deprecated_version(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with _actors(test_database_url, "ROW-06") as actors:
        datatype_id = await _published_v1(actors.t1, "row_06")
        await actors.t1.create_next(datatype_id, 1)
        await actors.t1.publish(datatype_id, 2, 1)
        cut = _install_lineage_no_key_cut(monkeypatch)
        outcomes = await _blocked_race(
            actors,
            cut,
            lambda: actors.t1.set_default(datatype_id, 2),
            lambda: actors.t2.deprecate(datatype_id, 2),
        )
        assert sorted(_failure_code(outcome) or "success" for outcome in outcomes) == [
            "default_version_conflict",
            "success",
        ]
        lineage = await actors.t1.get_lineage(datatype_id)
        version = await actors.t1.get_version(datatype_id, 2)
        assert not (
            lineage.default_version == 2 and version.status is VersionStatus.DEPRECATED
        )


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_15_description_writers_commit_complete_lww_values(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with _actors(test_database_url, "ROW-15") as actors:
        datatype_id = await _create(actors.t1, "row_15")
        cut = _install_description_cut(monkeypatch)
        outcomes = await _blocked_race(
            actors,
            cut,
            lambda: actors.t1.set_description(datatype_id, "complete-t1-value"),
            lambda: actors.t2.set_description(datatype_id, "complete-t2-value"),
        )
        assert all(not isinstance(outcome, ApplicationFailure) for outcome in outcomes)
        assert (
            await actors.t1.get_lineage(datatype_id)
        ).description == "complete-t2-value"


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_16_revise_then_delete_has_no_partial_aggregate(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with _actors(test_database_url, "ROW-16") as actors:
        datatype_id = await _create(actors.t1, "row_16")
        cut = _install_version_no_key_cut(monkeypatch)
        outcomes = await _blocked_race(
            actors,
            cut,
            lambda: actors.t1.revise(datatype_id, 1, 1, {"minimum": 16}),
            lambda: actors.t2.delete_lineage(datatype_id),
        )
        assert all(not isinstance(outcome, ApplicationFailure) for outcome in outcomes)
        absent = await _capture(lambda: actors.t1.get_lineage(datatype_id))
        assert _failure_code(absent) == "resource_not_found"


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_arb_01_one_semantic_create_wins_without_orphans(
    migrated_database_engine: Engine,
    test_database_url: str,
) -> None:
    del migrated_database_engine
    async with _actors(test_database_url, "ARB-01") as actors:
        blocker = await PgWorker.open(test_database_url, "ARB-01", WorkerRole.B)
        try:
            await blocker.connection.execute(
                datatypes.insert().values(
                    id=uuid4(),
                    namespace="semantic_concurrency",
                    name="arb_01",
                    description=None,
                    default_version=None,
                )
            )
            actors.tracker.reset()
            t1 = asyncio.create_task(
                _capture(lambda: _create(actors.t1, "arb_01")), name="T1"
            )
            t2 = asyncio.create_task(
                _capture(lambda: _create(actors.t2, "arb_01")), name="T2"
            )
            await actors.tracker.ready["T1"].wait()
            await actors.tracker.ready["T2"].wait()
            t1_pid = actors.tracker.pids["T1"]
            t2_pid = actors.tracker.pids["T2"]
            assert blocker.backend_pid in await wait_for_blocker(
                actors.observer, t1_pid, blocker.backend_pid
            )
            assert blocker.backend_pid in await wait_for_blocker(
                actors.observer, t2_pid, blocker.backend_pid
            )
            await blocker.rollback()
            async with asyncio.timeout(5):
                outcomes = await asyncio.gather(t1, t2)
        finally:
            await blocker.close()

        assert sorted(_failure_code(outcome) or "success" for outcome in outcomes) == [
            "qualified_name_conflict",
            "success",
        ]
        lineage_count = await actors.observer.connection.scalar(
            select(func.count())
            .select_from(datatypes)
            .where(
                datatypes.c.namespace == "semantic_concurrency",
                datatypes.c.name == "arb_01",
            )
        )
        version_count = await actors.observer.connection.scalar(
            select(func.count())
            .select_from(
                datatype_versions.join(
                    datatypes,
                    datatype_versions.c.datatype_id == datatypes.c.id,
                )
            )
            .where(
                datatypes.c.namespace == "semantic_concurrency",
                datatypes.c.name == "arb_01",
            )
        )
        assert (lineage_count, version_count) == (1, 1)


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_par_06_distinct_deprecations_make_semantic_progress(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with _actors(test_database_url, "PAR-06") as actors:
        datatype_id = await _published_v1(actors.t1, "par_06")
        await actors.t1.create_next(datatype_id, 1)
        await actors.t1.publish(datatype_id, 2, 1)
        await actors.t1.clear_default(datatype_id)
        cut = _install_lineage_share_cut(monkeypatch)
        outcomes = await _progress_race(
            cut,
            lambda: actors.t1.deprecate(datatype_id, 1),
            lambda: actors.t2.deprecate(datatype_id, 2),
        )
        assert all(isinstance(outcome, DataTypeVersion) for outcome in outcomes)
        assert (
            await actors.t1.get_version(datatype_id, 1)
        ).status is VersionStatus.DEPRECATED
        assert (
            await actors.t1.get_version(datatype_id, 2)
        ).status is VersionStatus.DEPRECATED


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_par_07a_description_and_set_default_intentionally_contend(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with _actors(test_database_url, "PAR-07A") as actors:
        datatype_id = await _published_v1(actors.t1, "par_07a")
        cut = _install_description_cut(monkeypatch)
        outcomes = await _blocked_race(
            actors,
            cut,
            lambda: actors.t1.set_description(datatype_id, "header metadata"),
            lambda: actors.t2.set_default(datatype_id, 1),
        )
        assert all(not isinstance(outcome, ApplicationFailure) for outcome in outcomes)
        lineage = await actors.t1.get_lineage(datatype_id)
        assert (lineage.description, lineage.default_version) == (
            "header metadata",
            1,
        )


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_par_07b_description_and_revise_make_independent_progress(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with _actors(test_database_url, "PAR-07B") as actors:
        datatype_id = await _create(actors.t1, "par_07b")
        cut = _install_description_cut(monkeypatch)
        outcomes = await _progress_race(
            cut,
            lambda: actors.t1.set_description(datatype_id, "parallel metadata"),
            lambda: actors.t2.revise(datatype_id, 1, 1, {"minimum": 7}),
        )
        assert all(not isinstance(outcome, ApplicationFailure) for outcome in outcomes)
        assert (
            await actors.t1.get_lineage(datatype_id)
        ).description == "parallel metadata"
        revised = await actors.t1.get_version(datatype_id, 1)
        assert (revised.revision, revised.constraints) == (2, {"minimum": 7})


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_ref_06a_datatype_cascade_loses_to_external_property_restrict(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with _actors(test_database_url, "REF-06A-DT-CASCADE") as actors:
        datatype_id = await _published_v1(actors.t1, "ref_06a")
        second_version = await actors.t1.create_next(datatype_id, 1)
        assert second_version.version == 2

        cut, precheck_counts = _install_reference_precheck_cut(monkeypatch)
        consumer = ObjectTemplateService(UnitOfWorkFactory(actors.t2_engine))
        deleted, created = await _progress_race(
            cut,
            lambda: actors.t1.delete_lineage(datatype_id),
            lambda: consumer.create(
                "semantic_concurrency",
                "ref_06a_consumer",
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
        )
        assert precheck_counts == [1]
        assert isinstance(created, CreateObjectTemplateResult)
        assert isinstance(deleted, ApplicationFailure)
        assert deleted.code == "delete_blocked"
        assert deleted.details == {
            "resource_type": "datatype",
            "id": str(datatype_id),
            "blockers": [{"type": "object_template_property", "count": 1}],
        }
        assert (await actors.t1.get_lineage(datatype_id)).id == datatype_id
        versions = await actors.t1.list_versions(
            datatype_id, status=None, cursor=None, limit=10
        )
        assert [item.version for item in versions.items] == [1, 2]
        persisted_consumer = await consumer.get_version(created.object_template.id, 1)
        assert [
            (item.datatype_id, item.datatype_version)
            for item in persisted_consumer.properties
        ] == [(datatype_id, 1)]
