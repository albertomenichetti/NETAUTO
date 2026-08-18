"""Reusable semantic-operation orchestration over independent PostgreSQL UoWs."""

import asyncio
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from types import ModuleType
from typing import cast

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

from netauto.application.datatypes import DataTypeService
from netauto.failures import ApplicationFailure
from netauto.persistence.locking import (
    LockPlan,
    RowLockClass,
    RowLockKey,
    RowLockMode,
)
from netauto.persistence.uow import UnitOfWork, UnitOfWorkFactory
from tests.support.pg_harness import PgWorker, WorkerRole, wait_for_blocker

type Operation = Callable[[], Awaitable[object]]
type AcquireLockPlan = Callable[
    [AsyncConnection, LockPlan], Awaitable[tuple[RowLockKey, ...]]
]


@dataclass(slots=True)
class ConnectionTracker:
    pids: dict[str, int] = field(default_factory=lambda: dict[str, int]())
    transactions: dict[str, list[tuple[int, int]]] = field(
        default_factory=lambda: dict[str, list[tuple[int, int]]]()
    )
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
        transaction_id = await self.connection.scalar(text("SELECT txid_current()"))
        identity = (int(pid), int(transaction_id))
        self._tracker.pids[self._role] = identity[0]
        self._tracker.transactions.setdefault(self._role, []).append(identity)
        self._tracker.ready.setdefault(self._role, asyncio.Event()).set()
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


@dataclass(slots=True)
class SemanticActors:
    t1: DataTypeService
    t2: DataTypeService
    t1_engine: AsyncEngine
    t2_engine: AsyncEngine
    observer: PgWorker
    tracker: ConnectionTracker


@dataclass(slots=True)
class PhaseCut:
    reached: asyncio.Event = field(default_factory=asyncio.Event)
    release: asyncio.Event = field(default_factory=asyncio.Event)


def install_lock_plan_cut(
    monkeypatch: pytest.MonkeyPatch,
    application_module: ModuleType,
    row_class: RowLockClass,
    mode: RowLockMode,
) -> PhaseCut:
    """Pause T1 after the selected central lock-plan row is held."""
    cut = PhaseCut()
    original = cast(AcquireLockPlan, application_module.acquire_lock_plan)

    async def intercepted(
        connection: AsyncConnection, plan: LockPlan
    ) -> tuple[RowLockKey, ...]:
        missing = await original(connection, plan)
        task = asyncio.current_task()
        selected = any(
            intent.key.row_class is row_class and intent.mode is mode
            for intent in plan.rows
        )
        if task is not None and task.get_name() == "T1" and selected:
            cut.reached.set()
            await cut.release.wait()
        return missing

    monkeypatch.setattr(application_module, "acquire_lock_plan", intercepted)
    return cut


def service_engine(database_url: str, application_name: str) -> AsyncEngine:
    return create_async_engine(
        database_url,
        isolation_level="READ COMMITTED",
        connect_args={"application_name": application_name},
    )


@asynccontextmanager
async def semantic_actors(
    database_url: str, scenario_id: str
) -> AsyncGenerator[SemanticActors]:
    t1_engine = service_engine(database_url, f"netauto-semantic:{scenario_id}:T1")
    t2_engine = service_engine(database_url, f"netauto-semantic:{scenario_id}:T2")
    observer = await PgWorker.open(database_url, scenario_id, WorkerRole.OBS)
    tracker = ConnectionTracker()
    try:
        yield SemanticActors(
            DataTypeService(ObservedUnitOfWorkFactory(t1_engine, tracker, "T1")),
            DataTypeService(ObservedUnitOfWorkFactory(t2_engine, tracker, "T2")),
            t1_engine,
            t2_engine,
            observer,
            tracker,
        )
    finally:
        await observer.close()
        await t1_engine.dispose()
        await t2_engine.dispose()


async def capture(operation: Operation) -> object:
    try:
        return await operation()
    except ApplicationFailure as failure:
        return failure


async def blocked_race(
    actors: SemanticActors,
    cut: PhaseCut,
    first: Operation,
    second: Operation,
) -> tuple[object, object]:
    actors.tracker.reset()
    first_task = asyncio.create_task(capture(first), name="T1")
    await cut.reached.wait()
    second_task = asyncio.create_task(capture(second), name="T2")
    await actors.tracker.ready["T1"].wait()
    await actors.tracker.ready["T2"].wait()
    first_pid = actors.tracker.pids["T1"]
    second_pid = actors.tracker.pids["T2"]
    blockers = await wait_for_blocker(actors.observer, second_pid, first_pid)
    assert first_pid in blockers
    cut.release.set()
    async with asyncio.timeout(5):
        return await asyncio.gather(first_task, second_task)


async def progress_race(
    cut: PhaseCut, first: Operation, second: Operation
) -> tuple[object, object]:
    first_task = asyncio.create_task(capture(first), name="T1")
    await cut.reached.wait()
    async with asyncio.timeout(5):
        second_outcome = await capture(second)
    assert not first_task.done()
    cut.release.set()
    async with asyncio.timeout(5):
        first_outcome = await first_task
    return first_outcome, second_outcome
