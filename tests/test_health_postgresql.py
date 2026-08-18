"""Real-PostgreSQL evidence for the shared-engine Core Health probe."""

import time

import pytest
from sqlalchemy import Engine, event
from sqlalchemy.pool import QueuePool

from netauto.application.health import CoreHealthService, HealthStatus
from netauto.persistence.engine import build_runtime_context
from netauto.persistence.health import PostgreSQLHealthProbe
from netauto.settings import Settings


@pytest.mark.postgresql
@pytest.mark.asyncio
async def test_real_health_uses_same_engine_exact_select_and_returns_connection(
    migrated_database_engine: Engine,
    test_database_url: str,
) -> None:
    del migrated_database_engine
    runtime = build_runtime_context(Settings(database_url=test_database_url))
    statements: list[str] = []
    commits = 0

    def statement_listener(
        _connection: object,
        _cursor: object,
        statement: str,
        _parameters: object,
        _context: object,
        _executemany: bool,
    ) -> None:
        statements.append(statement)

    def commit_listener(_connection: object) -> None:
        nonlocal commits
        commits += 1

    try:
        # Initialize the dialect before observing the one active Health operation.
        async with runtime.engine.connect():
            pass
        event.listen(
            runtime.engine.sync_engine, "before_cursor_execute", statement_listener
        )
        event.listen(runtime.engine.sync_engine, "commit", commit_listener)
        probe = PostgreSQLHealthProbe(runtime.engine)
        service = CoreHealthService(probe)

        result = await service.check()

        assert probe.engine is runtime.engine
        assert vars(runtime.uow_factory)["_engine"] is runtime.engine
        assert result.is_ready
        assert result.db_status.status is HealthStatus.OK
        assert result.db_status.message is None
        assert [statement.strip() for statement in statements] == ["SELECT 1"]
        assert commits == 0
        pool = runtime.engine.sync_engine.pool
        assert isinstance(pool, QueuePool)
        assert pool.checkedout() == 0
    finally:
        await runtime.engine.dispose()


@pytest.mark.postgresql
@pytest.mark.slow
@pytest.mark.asyncio
async def test_real_pool_starvation_times_out_then_recovers_on_same_engine(
    migrated_database_engine: Engine,
    test_database_url: str,
) -> None:
    del migrated_database_engine
    runtime = build_runtime_context(
        Settings(
            database_url=test_database_url,
            pool_size=1,
            max_overflow=0,
            pool_timeout=5.0,
        )
    )
    engine_identity = id(runtime.engine)
    service = CoreHealthService(PostgreSQLHealthProbe(runtime.engine))
    try:
        async with runtime.engine.connect():
            started = time.perf_counter()
            unavailable = await service.check()
            elapsed = time.perf_counter() - started

            assert unavailable.db_status.status is HealthStatus.ERROR
            assert unavailable.db_status.message == (
                "database readiness check timed out"
            )
            assert 1.7 <= elapsed < 4.0
            pool = runtime.engine.sync_engine.pool
            assert isinstance(pool, QueuePool)
            assert elapsed < pool.timeout()
            assert pool.checkedout() == 1

        recovered = await service.check()
        assert recovered.is_ready
        assert id(runtime.engine) == engine_identity
        assert isinstance(runtime.engine.sync_engine.pool, QueuePool)
        assert runtime.engine.sync_engine.pool.checkedout() == 0
    finally:
        await runtime.engine.dispose()
