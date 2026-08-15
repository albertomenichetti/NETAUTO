"""Deterministic real-PostgreSQL S02 concurrency contract scenarios."""

import asyncio
from collections.abc import Awaitable, Callable
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Engine, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine

from netauto.persistence.datatypes import DataTypeStore
from netauto.persistence.metadata import datatype_versions, datatypes
from tests.support.pg_harness import PgWorker, WorkerRole, wait_for_blocker

WorkerAction = Callable[[PgWorker], Awaitable[object]]


async def _run_action(action: WorkerAction, worker: PgWorker) -> object:
    return await action(worker)


async def _seed_lineages(database_url: str, count: int) -> list[UUID]:
    identifiers = [uuid4() for _ in range(count)]
    engine = create_async_engine(database_url, isolation_level="READ COMMITTED")
    try:
        async with engine.begin() as connection:
            await connection.execute(
                datatypes.insert(),
                [
                    {
                        "id": identifier,
                        "namespace": "pgtest",
                        "name": f"datatype_{index}",
                        "description": None,
                        "default_version": None,
                    }
                    for index, identifier in enumerate(identifiers)
                ],
            )
            await connection.execute(
                datatype_versions.insert(),
                [
                    {
                        "datatype_id": identifier,
                        "version": version,
                        "revision": 1,
                        "status": "DRAFT",
                        "base_type": "core.string",
                        "constraints": {},
                    }
                    for identifier in identifiers
                    for version in (1, 2)
                ],
            )
    finally:
        await engine.dispose()
    return identifiers


async def _assert_blocked(
    database_url: str,
    scenario_id: str,
    holder_action: WorkerAction,
    waiter_action: WorkerAction,
) -> None:
    holder = await PgWorker.open(database_url, scenario_id, WorkerRole.T1)
    waiter = await PgWorker.open(database_url, scenario_id, WorkerRole.T2)
    observer = await PgWorker.open(database_url, scenario_id, WorkerRole.OBS)
    waiter_task: asyncio.Task[object] | None = None
    try:
        await holder_action(holder)
        waiter_task = asyncio.create_task(_run_action(waiter_action, waiter))
        blockers = await wait_for_blocker(
            observer, waiter.backend_pid, holder.backend_pid
        )
        assert holder.backend_pid in blockers
        await holder.commit()
        async with asyncio.timeout(5):
            await waiter_task
    finally:
        if waiter_task is not None and not waiter_task.done():
            waiter_task.cancel()
            await asyncio.gather(waiter_task, return_exceptions=True)
        await holder.close()
        await waiter.close()
        await observer.close()


async def _assert_progress(
    database_url: str,
    scenario_id: str,
    holder_action: WorkerAction,
    independent_action: WorkerAction,
) -> None:
    holder = await PgWorker.open(database_url, scenario_id, WorkerRole.T1)
    independent = await PgWorker.open(database_url, scenario_id, WorkerRole.T2)
    try:
        await holder_action(holder)
        async with asyncio.timeout(5):
            await independent_action(independent)
    finally:
        await holder.close()
        await independent.close()


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_canonical_s02_row_arbitration_and_progress_scenarios(
    migrated_database_engine: Engine, test_database_url: str
) -> None:
    """Probe ROW-01..08, ROW-15/16, ARB-01, PAR-06 and PAR-07A/B mechanisms."""
    del migrated_database_engine
    ids = await _seed_lineages(test_database_url, 13)

    async def lineage_no_key(identifier: UUID, worker: PgWorker) -> object:
        return await DataTypeStore(worker.connection).lock_lineage_no_key(identifier)

    async def lineage_share(identifier: UUID, worker: PgWorker) -> object:
        return await DataTypeStore(worker.connection).lock_lineage_share(identifier)

    async def version_no_key(
        identifier: UUID, version: int, worker: PgWorker
    ) -> object:
        return await DataTypeStore(worker.connection).lock_version_no_key(
            identifier, version
        )

    async def version_update(
        identifier: UUID, version: int, worker: PgWorker
    ) -> object:
        return await DataTypeStore(worker.connection).lock_version_update(
            identifier, version
        )

    # ROW-01 CREATE_NEXT x CREATE_NEXT and ROW-02 CREATE_NEXT x DELETE_DRAFT(max)
    # serialize on the stable lineage owner before version-set decisions.
    for scenario_id, identifier in (("ROW-01", ids[0]), ("ROW-02", ids[1])):
        await _assert_blocked(
            test_database_url,
            scenario_id,
            lambda worker, value=identifier: lineage_no_key(value, worker),
            lambda worker, value=identifier: lineage_no_key(value, worker),
        )

    # ROW-03 REVISE x REVISE and ROW-04 exact terminal races serialize on DTV.
    await _assert_blocked(
        test_database_url,
        "ROW-03",
        lambda worker: version_no_key(ids[2], 1, worker),
        lambda worker: version_no_key(ids[2], 1, worker),
    )
    await _assert_blocked(
        test_database_url,
        "ROW-04",
        lambda worker: version_no_key(ids[3], 1, worker),
        lambda worker: version_update(ids[3], 1, worker),
    )

    # ROW-05 serial auto-default publishers and ROW-06 default/lifecycle race.
    await _assert_blocked(
        test_database_url,
        "ROW-05",
        lambda worker: lineage_no_key(ids[4], worker),
        lambda worker: lineage_no_key(ids[4], worker),
    )
    await _assert_blocked(
        test_database_url,
        "ROW-06",
        lambda worker: lineage_no_key(ids[5], worker),
        lambda worker: lineage_share(ids[5], worker),
    )

    async def update_description(identifier: UUID, worker: PgWorker) -> object:
        return await worker.connection.execute(
            update(datatypes)
            .where(datatypes.c.id == identifier)
            .values(description=str(worker.role))
        )

    # ROW-15: same header value is atomic writer-LWW.
    await _assert_blocked(
        test_database_url,
        "ROW-15",
        lambda worker: update_description(ids[6], worker),
        lambda worker: update_description(ids[6], worker),
    )
    await _assert_blocked(
        test_database_url,
        "PAR-07A",
        lambda worker: update_description(ids[7], worker),
        lambda worker: lineage_no_key(ids[7], worker),
    )

    # ROW-16: aggregate cascade waits for an exact child writer.
    async def delete_lineage(identifier: UUID, worker: PgWorker) -> object:
        return await worker.connection.execute(
            datatypes.delete().where(datatypes.c.id == identifier)
        )

    await _assert_blocked(
        test_database_url,
        "ROW-16",
        lambda worker: version_no_key(ids[8], 1, worker),
        lambda worker: delete_lineage(ids[8], worker),
    )

    # PAR-06: distinct version lifecycle owners progress under compatible SHARE.
    async def hold_first_version(worker: PgWorker) -> object:
        await lineage_share(ids[9], worker)
        return await version_no_key(ids[9], 1, worker)

    async def hold_second_version(worker: PgWorker) -> object:
        await lineage_share(ids[9], worker)
        return await version_no_key(ids[9], 2, worker)

    await _assert_progress(
        test_database_url, "PAR-06", hold_first_version, hold_second_version
    )

    # PAR-07B: version candidate work and lineage description work are independent.
    await _assert_progress(
        test_database_url,
        "PAR-07B",
        lambda worker: version_no_key(ids[7], 1, worker),
        lambda worker: update_description(ids[7], worker),
    )

    # ROW-07/08 DataType-side admission locks remain held by the caller UoW.
    controller = await PgWorker.open(test_database_url, "ROW-07-08", WorkerRole.CTL)
    try:
        await controller.connection.execute(
            datatype_versions.update()
            .where(datatype_versions.c.datatype_id.in_(ids[10:13]))
            .values(status="PUBLISHED")
        )
        await controller.connection.execute(
            datatypes.update()
            .where(datatypes.c.id.in_(ids[11:13]))
            .values(default_version=1)
        )
        await controller.commit()
    finally:
        await controller.close()

    async def admit_exact(identifier: UUID, worker: PgWorker) -> object:
        return await DataTypeStore(worker.connection).admit_exact(identifier, 1)

    async def admit_default(identifier: UUID, worker: PgWorker) -> object:
        return await DataTypeStore(worker.connection).admit_default(identifier)

    await _assert_blocked(
        test_database_url,
        "ROW-07",
        lambda worker: admit_exact(ids[10], worker),
        lambda worker: version_no_key(ids[10], 1, worker),
    )
    await _assert_blocked(
        test_database_url,
        "ROW-08A",
        lambda worker: admit_default(ids[11], worker),
        lambda worker: lineage_no_key(ids[11], worker),
    )
    await _assert_blocked(
        test_database_url,
        "ROW-08B",
        lambda worker: admit_default(ids[12], worker),
        lambda worker: lineage_no_key(ids[12], worker),
    )

    # ARB-01: the database UNIQUE authority arbitrates an identical qualified name.
    holder = await PgWorker.open(test_database_url, "ARB-01", WorkerRole.T1)
    waiter = await PgWorker.open(test_database_url, "ARB-01", WorkerRole.T2)
    observer = await PgWorker.open(test_database_url, "ARB-01", WorkerRole.OBS)
    waiter_task: asyncio.Task[object] | None = None
    duplicate_values = {
        "namespace": "arbitration",
        "name": "same_name",
        "description": None,
        "default_version": None,
    }
    try:
        await holder.connection.execute(
            datatypes.insert().values(id=uuid4(), **duplicate_values)
        )
        waiter_task = asyncio.create_task(
            waiter.connection.execute(
                datatypes.insert().values(id=uuid4(), **duplicate_values)
            )
        )
        blockers = await wait_for_blocker(
            observer, waiter.backend_pid, holder.backend_pid
        )
        assert holder.backend_pid in blockers
        await holder.commit()
        with pytest.raises(IntegrityError):
            async with asyncio.timeout(5):
                await waiter_task
    finally:
        if waiter_task is not None and not waiter_task.done():
            waiter_task.cancel()
            await asyncio.gather(waiter_task, return_exceptions=True)
        await holder.close()
        await waiter.close()
        await observer.close()
