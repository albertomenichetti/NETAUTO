"""Transport-neutral Core readiness application capability."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

CORE_DATABASE_HEALTH_TIMEOUT_SECONDS = 2.0


class HealthStatus(StrEnum):
    OK = "ok"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class ComponentHealth:
    status: HealthStatus
    message: str | None = None


@dataclass(frozen=True, slots=True)
class CoreHealthResult:
    app_status: ComponentHealth
    db_status: ComponentHealth
    execution_time_ms: int

    def __post_init__(self) -> None:
        if self.execution_time_ms < 0:
            raise ValueError("execution_time_ms must be non-negative")

    @property
    def is_ready(self) -> bool:
        return (
            self.app_status.status is HealthStatus.OK
            and self.db_status.status is HealthStatus.OK
        )


class DatabaseProbeUnavailable(Exception):
    """The database did not complete the expected readiness round trip."""


class DatabaseProbeTimedOut(Exception):
    """The database probe exhausted an owned infrastructure timeout."""


class DatabaseHealthProbe(Protocol):
    async def check(self) -> None: ...


class CoreHealthService:
    """Execute one bounded readiness probe and return one complete result."""

    def __init__(
        self,
        probe: DatabaseHealthProbe,
        monotonic_ns: Callable[[], int] = time.perf_counter_ns,
    ) -> None:
        self._probe = probe
        self._monotonic_ns = monotonic_ns

    async def check(self) -> CoreHealthResult:
        started_ns = self._monotonic_ns()
        app_status = ComponentHealth(HealthStatus.OK)
        try:
            async with asyncio.timeout(CORE_DATABASE_HEALTH_TIMEOUT_SECONDS):
                await self._probe.check()
        except DatabaseProbeTimedOut:
            db_status = ComponentHealth(
                HealthStatus.ERROR, "database readiness check timed out"
            )
        except TimeoutError:
            db_status = ComponentHealth(
                HealthStatus.ERROR, "database readiness check timed out"
            )
        except DatabaseProbeUnavailable:
            db_status = ComponentHealth(
                HealthStatus.ERROR, "database readiness check failed"
            )
        else:
            db_status = ComponentHealth(HealthStatus.OK)

        ended_ns = self._monotonic_ns()
        elapsed_ns = max(0, ended_ns - started_ns)
        return CoreHealthResult(
            app_status=app_status,
            db_status=db_status,
            execution_time_ms=elapsed_ns // 1_000_000,
        )
