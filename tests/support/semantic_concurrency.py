"""Reusable semantic-operation orchestration over independent PostgreSQL UoWs."""

from __future__ import annotations

import asyncio
import os
import re
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from types import ModuleType, TracebackType
from typing import cast

import pytest
from sqlalchemy import event, text
from sqlalchemy.engine import ExceptionContext
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
type BlockedObservation = Callable[[int, int], Awaitable[None]]
type AcquireLockPlan = Callable[
    [AsyncConnection, LockPlan], Awaitable[tuple[RowLockKey, ...]]
]


@dataclass(frozen=True, slots=True)
class WorkerOutcome:
    """One complete test-harness observation of a semantic worker."""

    pytest_node_id: str
    scenario_ids: frozenset[str]
    role: str
    returned: object | None
    application_failure: ApplicationFailure | None
    unexpected_exception: BaseException | None
    unexpected_exception_type: str | None
    safe_diagnostic: str | None
    sqlstate: str | None
    last_phase: str
    transaction_outcome: str
    transaction_outcomes: tuple[str, ...]
    uow_identities: tuple[tuple[int, int], ...]
    negative_control: bool


@dataclass(slots=True)
class ConnectionTracker:
    pids: dict[str, int] = field(default_factory=lambda: dict[str, int]())
    transactions: dict[str, list[tuple[int, int]]] = field(
        default_factory=lambda: dict[str, list[tuple[int, int]]]()
    )
    ready: dict[str, asyncio.Event] = field(
        default_factory=lambda: {"T1": asyncio.Event(), "T2": asyncio.Event()}
    )
    last_phase: dict[str, str] = field(default_factory=lambda: dict[str, str]())
    transaction_outcomes: dict[str, list[str]] = field(
        default_factory=lambda: dict[str, list[str]]()
    )
    observed_sqlstates: dict[str, list[str]] = field(
        default_factory=lambda: dict[str, list[str]]()
    )
    worker_outcomes: list[WorkerOutcome] = field(
        default_factory=lambda: list[WorkerOutcome]()
    )

    def reset(self) -> None:
        self.ready = {"T1": asyncio.Event(), "T2": asyncio.Event()}

    def mark(self, role: str, phase: str) -> None:
        self.last_phase[role] = phase

    def record_sqlstate(self, role: str, sqlstate: str) -> None:
        self.observed_sqlstates.setdefault(role, []).append(sqlstate)


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
        self._tracker.mark(self._role, "UOW_STARTED")
        self._tracker.ready.setdefault(self._role, asyncio.Event()).set()
        return entered

    async def commit(self) -> None:
        await super().commit()
        self._tracker.mark(self._role, "COMMITTED")
        self._tracker.transaction_outcomes.setdefault(self._role, []).append(
            "COMMITTED"
        )

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        transaction = self._transaction
        rolled_back = transaction is not None and transaction.is_active
        await super().__aexit__(exc_type, exc_value, traceback)
        if rolled_back:
            self._tracker.mark(self._role, "ROLLED_BACK")
            self._tracker.transaction_outcomes.setdefault(self._role, []).append(
                "ROLLED_BACK"
            )


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


_ACTIVE_TRACKER: ContextVar[ConnectionTracker | None] = ContextVar(
    "semantic_concurrency_active_tracker", default=None
)
_ACTIVE_SCENARIOS: ContextVar[frozenset[str]] = ContextVar(
    "semantic_concurrency_active_scenarios", default=frozenset()
)
_SESSION_WORKER_OUTCOMES: list[WorkerOutcome] = []


def extract_sqlstate(error: BaseException) -> str | None:
    """Return a real SQLSTATE from bounded wrapper/chaining shapes.

    PostgreSQL state is structural data.  Error messages are deliberately never
    parsed because they are neither stable nor authoritative.
    """
    pending: list[BaseException] = [error]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        identity = id(current)
        if identity in seen:
            continue
        seen.add(identity)
        for attribute in ("sqlstate", "pgcode"):
            value = getattr(current, attribute, None)
            if isinstance(value, str):
                return value
        for attribute in ("orig", "driver_exception", "__cause__", "__context__"):
            nested = getattr(current, attribute, None)
            if isinstance(nested, BaseException):
                pending.append(nested)
    return None


def _current_node_id() -> str:
    value = os.environ.get("PYTEST_CURRENT_TEST", "<direct-harness-call>")
    return value.rpartition(" (")[0]


def _scenario_ids(value: str) -> frozenset[str]:
    return frozenset(
        match.group(0)
        for match in re.finditer(
            r"(?:ROW|ARB|REF|GATE|SNAP|ATOMIC|PAR|PLAN)-\d{2}", value
        )
    )


def activate_outcome_context(
    tracker: ConnectionTracker, scenario_id: str
) -> tuple[Token[ConnectionTracker | None], Token[frozenset[str]]]:
    """Make one tracker/scenario visible to compatibility worker wrappers."""
    return (
        _ACTIVE_TRACKER.set(tracker),
        _ACTIVE_SCENARIOS.set(_scenario_ids(scenario_id)),
    )


def reset_outcome_context(
    tokens: tuple[Token[ConnectionTracker | None], Token[frozenset[str]]],
) -> None:
    _ACTIVE_TRACKER.reset(tokens[0])
    _ACTIVE_SCENARIOS.reset(tokens[1])


def session_worker_outcomes() -> tuple[WorkerOutcome, ...]:
    return tuple(_SESSION_WORKER_OUTCOMES)


def worker_outcomes_for_node(node_id: str) -> tuple[WorkerOutcome, ...]:
    return tuple(
        outcome
        for outcome in _SESSION_WORKER_OUTCOMES
        if outcome.pytest_node_id == node_id
    )


async def capture_worker_outcome(
    operation: Operation,
    tracker: ConnectionTracker | None = None,
    role: str | None = None,
    *,
    allow_forbidden_sqlstates: frozenset[str] = frozenset(),
    negative_control: bool = False,
    scenario_ids: frozenset[str] | None = None,
) -> WorkerOutcome:
    """Capture semantic, unexpected, SQLSTATE, phase and transaction material."""
    active_tracker = tracker or _ACTIVE_TRACKER.get()
    if active_tracker is None:
        raise RuntimeError("semantic worker outcome capture has no active tracker")
    current_task = asyncio.current_task()
    task_role = current_task.get_name() if current_task is not None else "CTL"
    active_role = role or (task_role if task_role in {"B", "T1", "T2", "T3"} else "CTL")
    transaction_offset = len(active_tracker.transaction_outcomes.get(active_role, []))
    identity_offset = len(active_tracker.transactions.get(active_role, []))
    sqlstate_offset = len(active_tracker.observed_sqlstates.get(active_role, []))
    returned: object | None = None
    failure: ApplicationFailure | None = None
    unexpected: BaseException | None = None
    unexpected_type: str | None = None
    sqlstate: str | None = None
    try:
        returned = await operation()
    except ApplicationFailure as error:
        failure = error
        sqlstate = extract_sqlstate(error)
    except BaseException as error:  # test boundary must retain unexpected DB material
        unexpected = error
        unexpected_type = type(error).__name__
        sqlstate = extract_sqlstate(error)
    observed_sqlstates = active_tracker.observed_sqlstates.get(active_role, [])[
        sqlstate_offset:
    ]
    if sqlstate is None and observed_sqlstates:
        sqlstate = observed_sqlstates[-1]
    outcomes = tuple(
        active_tracker.transaction_outcomes.get(active_role, [])[transaction_offset:]
    )
    identities = tuple(
        active_tracker.transactions.get(active_role, [])[identity_offset:]
    )
    transaction_outcome = outcomes[-1] if outcomes else "NO_UOW"
    outcome = WorkerOutcome(
        _current_node_id(),
        _ACTIVE_SCENARIOS.get() if scenario_ids is None else scenario_ids,
        active_role,
        returned,
        failure,
        unexpected,
        unexpected_type,
        unexpected_type,
        sqlstate,
        active_tracker.last_phase.get(active_role, "NO_UOW"),
        transaction_outcome,
        outcomes,
        identities,
        negative_control,
    )
    active_tracker.worker_outcomes.append(outcome)
    _SESSION_WORKER_OUTCOMES.append(outcome)
    if sqlstate in {"40P01", "40001"} and sqlstate not in allow_forbidden_sqlstates:
        raise AssertionError(
            f"forbidden supported-path SQLSTATE {sqlstate} observed by {active_role}"
        )
    return outcome


def unwrap_worker_outcome(outcome: WorkerOutcome) -> object:
    """Preserve the delivered helper result while retaining its ledger record."""
    if outcome.unexpected_exception is not None:
        raise outcome.unexpected_exception
    if outcome.application_failure is not None:
        return outcome.application_failure
    return outcome.returned


async def run_worker(
    operation: Operation,
    tracker: ConnectionTracker | None = None,
    role: str | None = None,
    *,
    scenario_ids: frozenset[str] | None = None,
) -> object:
    """Execute one semantic worker, retaining normal exception propagation."""
    outcome = await capture_worker_outcome(
        operation, tracker, role, scenario_ids=scenario_ids
    )
    if outcome.unexpected_exception is not None:
        raise outcome.unexpected_exception
    if outcome.application_failure is not None:
        raise outcome.application_failure
    return outcome.returned


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


def service_engine(
    database_url: str,
    application_name: str,
    tracker: ConnectionTracker | None = None,
    role: str | None = None,
) -> AsyncEngine:
    engine = create_async_engine(
        database_url,
        isolation_level="READ COMMITTED",
        connect_args={"application_name": application_name},
    )
    if tracker is not None and role is not None:

        def observe_driver_error(context: ExceptionContext) -> None:
            for candidate in (
                context.original_exception,
                context.sqlalchemy_exception,
            ):
                if isinstance(candidate, BaseException):
                    sqlstate = extract_sqlstate(candidate)
                    if sqlstate is not None:
                        tracker.record_sqlstate(role, sqlstate)
                        return

        event.listen(engine.sync_engine, "handle_error", observe_driver_error)

    return engine


@asynccontextmanager
async def semantic_actors(
    database_url: str, scenario_id: str
) -> AsyncGenerator[SemanticActors]:
    tracker = ConnectionTracker()
    t1_engine = service_engine(
        database_url, f"netauto-semantic:{scenario_id}:T1", tracker, "T1"
    )
    t2_engine = service_engine(
        database_url, f"netauto-semantic:{scenario_id}:T2", tracker, "T2"
    )
    observer = await PgWorker.open(database_url, scenario_id, WorkerRole.OBS)
    tokens = activate_outcome_context(tracker, scenario_id)
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
        reset_outcome_context(tokens)
        await observer.close()
        await t1_engine.dispose()
        await t2_engine.dispose()


async def capture(operation: Operation) -> object:
    return unwrap_worker_outcome(await capture_worker_outcome(operation))


async def blocked_race_outcomes(
    actors: SemanticActors,
    cut: PhaseCut,
    first: Operation,
    second: Operation,
    *,
    observe_blocked: BlockedObservation | None = None,
) -> tuple[WorkerOutcome, WorkerOutcome]:
    """Run the canonical blocking recipe through the outcome-aware boundary."""
    actors.tracker.reset()
    first_task = asyncio.create_task(
        capture_worker_outcome(first, actors.tracker, "T1"), name="T1"
    )
    await cut.reached.wait()
    second_task = asyncio.create_task(
        capture_worker_outcome(second, actors.tracker, "T2"), name="T2"
    )
    await actors.tracker.ready["T1"].wait()
    await actors.tracker.ready["T2"].wait()
    first_pid = actors.tracker.pids["T1"]
    second_pid = actors.tracker.pids["T2"]
    blockers = await wait_for_blocker(actors.observer, second_pid, first_pid)
    assert first_pid in blockers
    if observe_blocked is not None:
        await observe_blocked(first_pid, second_pid)
    cut.release.set()
    async with asyncio.timeout(5):
        return await asyncio.gather(first_task, second_task)


async def blocked_race(
    actors: SemanticActors,
    cut: PhaseCut,
    first: Operation,
    second: Operation,
    *,
    observe_blocked: BlockedObservation | None = None,
) -> tuple[object, object]:
    return tuple(
        unwrap_worker_outcome(outcome)
        for outcome in await blocked_race_outcomes(
            actors,
            cut,
            first,
            second,
            observe_blocked=observe_blocked,
        )
    )  # type: ignore[return-value]


async def progress_race_outcomes(
    cut: PhaseCut, first: Operation, second: Operation
) -> tuple[WorkerOutcome, WorkerOutcome]:
    """Run the canonical positive-progress recipe with complete outcomes."""
    tracker = _ACTIVE_TRACKER.get()
    if tracker is None:
        raise RuntimeError("progress race has no active outcome tracker")
    tracker.reset()
    first_task = asyncio.create_task(
        capture_worker_outcome(first, tracker, "T1"), name="T1"
    )
    await cut.reached.wait()
    async with asyncio.timeout(5):
        second_outcome = await capture_worker_outcome(second, tracker, "T2")
    assert not first_task.done()
    cut.release.set()
    async with asyncio.timeout(5):
        first_outcome = await first_task
    return first_outcome, second_outcome


async def progress_race(
    cut: PhaseCut, first: Operation, second: Operation
) -> tuple[object, object]:
    first_outcome, second_outcome = await progress_race_outcomes(cut, first, second)
    return unwrap_worker_outcome(first_outcome), unwrap_worker_outcome(second_outcome)
