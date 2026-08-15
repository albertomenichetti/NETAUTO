"""Reusable deterministic real-PostgreSQL concurrency test building blocks."""

import asyncio
from dataclasses import dataclass, field
from enum import StrEnum

from sqlalchemy import text
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncTransaction,
    create_async_engine,
)
from sqlalchemy.pool import NullPool


class WorkerRole(StrEnum):
    CTL = "CTL"
    OBS = "OBS"
    B = "B"
    T1 = "T1"
    T2 = "T2"
    T3 = "T3"


class HarnessPhase(StrEnum):
    UOW_STARTED = "UOW_STARTED"
    OWNER_STABILIZED = "OWNER_STABILIZED"
    DEPENDENCIES_STABILIZED = "DEPENDENCIES_STABILIZED"
    GATE_WAITING = "GATE_WAITING"
    GATE_ACQUIRED = "GATE_ACQUIRED"
    PROTECTED_STATE_REREAD = "PROTECTED_STATE_REREAD"
    CANDIDATE_WRITTEN = "CANDIDATE_WRITTEN"
    CLOSURE_WRITTEN = "CLOSURE_WRITTEN"
    METADATA_SNAPSHOT_CAPTURED = "METADATA_SNAPSHOT_CAPTURED"
    EVENT_SET_WRITTEN = "EVENT_SET_WRITTEN"
    BEFORE_COMMIT = "BEFORE_COMMIT"
    COMMITTED = "COMMITTED"
    ROLLED_BACK = "ROLLED_BACK"


@dataclass(slots=True)
class PhaseBarrier:
    """In-process signalling for phases reached around real database boundaries."""

    _events: dict[tuple[WorkerRole, HarnessPhase], asyncio.Event] = field(
        default_factory=lambda: {}
    )

    def mark(self, role: WorkerRole, phase: HarnessPhase) -> None:
        self._events.setdefault((role, phase), asyncio.Event()).set()

    async def wait(
        self, role: WorkerRole, phase: HarnessPhase, *, timeout_seconds: float = 5.0
    ) -> None:
        event = self._events.setdefault((role, phase), asyncio.Event())
        async with asyncio.timeout(timeout_seconds):
            await event.wait()


@dataclass(slots=True)
class PgWorker:
    """One independent READ COMMITTED PostgreSQL worker session."""

    scenario_id: str
    role: WorkerRole
    engine: AsyncEngine
    connection: AsyncConnection
    transaction: AsyncTransaction
    backend_pid: int
    last_phase: HarnessPhase

    @property
    def application_name(self) -> str:
        return f"netauto-pgtest:{self.scenario_id}:{self.role}"

    @classmethod
    async def open(
        cls, database_url: str, scenario_id: str, role: WorkerRole
    ) -> PgWorker:
        application_name = f"netauto-pgtest:{scenario_id}:{role}"
        engine = create_async_engine(
            database_url,
            isolation_level="READ COMMITTED",
            poolclass=NullPool,
            connect_args={"application_name": application_name},
        )
        connection = await engine.connect()
        try:
            transaction = await connection.begin()
            backend_pid = int(
                (await connection.execute(text("SELECT pg_backend_pid()"))).scalar_one()
            )
        except BaseException:
            await connection.close()
            await engine.dispose()
            raise
        return cls(
            scenario_id=scenario_id,
            role=role,
            engine=engine,
            connection=connection,
            transaction=transaction,
            backend_pid=backend_pid,
            last_phase=HarnessPhase.UOW_STARTED,
        )

    def mark(self, phase: HarnessPhase, barrier: PhaseBarrier | None = None) -> None:
        self.last_phase = phase
        if barrier is not None:
            barrier.mark(self.role, phase)

    async def commit(self) -> None:
        await self.transaction.commit()
        self.last_phase = HarnessPhase.COMMITTED

    async def rollback(self) -> None:
        if self.transaction.is_active:
            await self.transaction.rollback()
        self.last_phase = HarnessPhase.ROLLED_BACK

    async def close(self) -> None:
        try:
            await self.rollback()
        finally:
            await self.connection.close()
            await self.engine.dispose()


async def blocking_pids(observer: PgWorker, worker_pid: int) -> tuple[int, ...]:
    """Read PostgreSQL's authoritative blocker graph from an OBS session."""
    value = (
        await observer.connection.execute(
            text("SELECT pg_blocking_pids(:worker_pid)"),
            {"worker_pid": worker_pid},
        )
    ).scalar_one()
    return tuple(int(pid) for pid in value)


async def wait_for_blocker(
    observer: PgWorker,
    worker_pid: int,
    expected_blocker_pid: int,
    *,
    timeout_seconds: float = 5.0,
) -> tuple[int, ...]:
    """Poll fresh OBS statements until PostgreSQL reports the known blocker.

    The database lock establishes ordering. The deadline only prevents a broken test
    from hanging; no timed sleep determines the interleaving.
    """
    async with asyncio.timeout(timeout_seconds):
        while True:
            blockers = await blocking_pids(observer, worker_pid)
            if expected_blocker_pid in blockers:
                return blockers


async def activity_snapshot(observer: PgWorker, worker_pid: int) -> RowMapping:
    """Capture fresh worker identity/wait diagnostics from pg_stat_activity."""
    result = await observer.connection.execute(
        text(
            "SELECT pid, application_name, state, wait_event_type, wait_event "
            "FROM pg_stat_activity WHERE pid = :worker_pid"
        ),
        {"worker_pid": worker_pid},
    )
    return result.mappings().one()


async def lock_snapshot(observer: PgWorker, worker_pid: int) -> tuple[RowMapping, ...]:
    """Capture supporting pg_locks diagnostics without assuming tuple locks."""
    result = await observer.connection.execute(
        text(
            "SELECT locktype, mode, granted, waitstart "
            "FROM pg_locks WHERE pid = :worker_pid "
            "ORDER BY locktype, mode, granted"
        ),
        {"worker_pid": worker_pid},
    )
    return tuple(result.mappings())
