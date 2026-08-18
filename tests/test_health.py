"""Deterministic application-level Core Health evidence."""

import asyncio
from collections.abc import Iterator

import pytest

import netauto.application.health as health_module
from netauto.application.health import (
    ComponentHealth,
    CoreHealthResult,
    CoreHealthService,
    DatabaseProbeTimedOut,
    DatabaseProbeUnavailable,
    HealthStatus,
)


class ControlledProbe:
    def __init__(self, error: BaseException | None = None) -> None:
        self.calls = 0
        self.error = error

    async def check(self) -> None:
        self.calls += 1
        if self.error is not None:
            raise self.error


def clock(*values: int) -> Iterator[int]:
    return iter(values)


@pytest.mark.parametrize(
    ("error", "status", "message"),
    [
        (None, HealthStatus.OK, None),
        (
            DatabaseProbeUnavailable(),
            HealthStatus.ERROR,
            "database readiness check failed",
        ),
        (
            DatabaseProbeTimedOut(),
            HealthStatus.ERROR,
            "database readiness check timed out",
        ),
    ],
)
@pytest.mark.asyncio
async def test_health_exact_vocabulary_classification_and_one_attempt(
    error: BaseException | None,
    status: HealthStatus,
    message: str | None,
) -> None:
    probe = ControlledProbe(error)
    times = clock(1_000_000, 4_999_999)

    result = await CoreHealthService(probe, lambda: next(times)).check()

    assert probe.calls == 1
    assert result == CoreHealthResult(
        app_status=ComponentHealth(HealthStatus.OK),
        db_status=ComponentHealth(status, message),
        execution_time_ms=3,
    )
    assert result.is_ready is (status is HealthStatus.OK)


@pytest.mark.parametrize(
    ("start", "end", "expected"),
    [
        (2_000_000, 1_000_000, 0),
        (0, 999_999, 0),
        (0, 1_999_999, 1),
    ],
)
@pytest.mark.asyncio
async def test_health_monotonic_conversion_is_exact(
    start: int, end: int, expected: int
) -> None:
    times = clock(start, end)
    result = await CoreHealthService(ControlledProbe(), lambda: next(times)).check()
    assert result.execution_time_ms == expected


def test_health_result_rejects_negative_execution_time() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        CoreHealthResult(
            ComponentHealth(HealthStatus.OK),
            ComponentHealth(HealthStatus.OK),
            -1,
        )


@pytest.mark.asyncio
async def test_health_outer_timeout_waits_for_cleanup_before_measurement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []

    class BlockingProbe:
        async def check(self) -> None:
            try:
                await asyncio.Event().wait()
            finally:
                events.append("cleanup")

    monkeypatch.setattr(health_module, "CORE_DATABASE_HEALTH_TIMEOUT_SECONDS", 0.01)

    def monotonic_ns() -> int:
        events.append("clock")
        return 0 if events.count("clock") == 1 else 2_000_000

    result = await CoreHealthService(BlockingProbe(), monotonic_ns).check()

    assert result.db_status == ComponentHealth(
        HealthStatus.ERROR, "database readiness check timed out"
    )
    assert events == ["clock", "cleanup", "clock"]


@pytest.mark.asyncio
async def test_health_unexpected_programming_failure_propagates() -> None:
    probe = ControlledProbe(RuntimeError("unexpected defect"))
    with pytest.raises(RuntimeError, match="unexpected defect"):
        await CoreHealthService(probe).check()
    assert probe.calls == 1


@pytest.mark.asyncio
async def test_health_cancellation_propagates_after_probe_cleanup() -> None:
    started = asyncio.Event()
    cleaned = asyncio.Event()

    class BlockingProbe:
        async def check(self) -> None:
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                cleaned.set()

    task = asyncio.create_task(CoreHealthService(BlockingProbe()).check())
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert cleaned.is_set()
