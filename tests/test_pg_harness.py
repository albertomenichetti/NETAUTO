"""Persistence-level deterministic blocker smoke test for the PG harness."""

import asyncio

import pytest
from sqlalchemy import Engine

from netauto.persistence.gates import AdvisoryGate, acquire_advisory_gate
from tests.support.pg_harness import (
    HarnessPhase,
    PgWorker,
    PhaseBarrier,
    WorkerRole,
    activity_snapshot,
    lock_snapshot,
    wait_for_blocker,
)


@pytest.mark.postgresql
@pytest.mark.concurrency
@pytest.mark.asyncio
async def test_real_blocker_is_observed_without_sleep_or_production_hooks(
    test_database_url: str, migrated_database_engine: Engine
) -> None:
    del migrated_database_engine
    scenario_id = "S01-HARNESS-SMOKE"
    barrier = PhaseBarrier()
    blocker = await PgWorker.open(test_database_url, scenario_id, WorkerRole.B)
    waiter = await PgWorker.open(test_database_url, scenario_id, WorkerRole.T2)
    observer = await PgWorker.open(test_database_url, scenario_id, WorkerRole.OBS)

    async def acquire_conflicting_lock() -> None:
        waiter.mark(HarnessPhase.GATE_WAITING, barrier)
        await acquire_advisory_gate(
            waiter.connection, AdvisoryGate.OWNERSHIP_GRAPH_WRITE_GATE
        )
        waiter.mark(HarnessPhase.GATE_ACQUIRED, barrier)

    waiter_task: asyncio.Task[None] | None = None
    try:
        await acquire_advisory_gate(
            blocker.connection, AdvisoryGate.OWNERSHIP_GRAPH_WRITE_GATE
        )
        blocker.mark(HarnessPhase.OWNER_STABILIZED, barrier)
        waiter_task = asyncio.create_task(acquire_conflicting_lock())
        await barrier.wait(WorkerRole.T2, HarnessPhase.GATE_WAITING)

        blockers = await wait_for_blocker(
            observer, waiter.backend_pid, blocker.backend_pid
        )
        activity = await activity_snapshot(observer, waiter.backend_pid)
        locks = await lock_snapshot(observer, waiter.backend_pid)

        assert blocker.backend_pid in blockers
        assert activity["application_name"] == waiter.application_name
        assert activity["wait_event_type"] == "Lock"
        assert any(not row["granted"] for row in locks)

        await blocker.commit()
        async with asyncio.timeout(5):
            await waiter_task
        await barrier.wait(WorkerRole.T2, HarnessPhase.GATE_ACQUIRED)
        await waiter.commit()
    finally:
        if waiter_task is not None and not waiter_task.done():
            waiter_task.cancel()
        await observer.close()
        await waiter.close()
        await blocker.close()
