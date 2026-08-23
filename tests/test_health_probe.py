"""Pure adapter evidence for the bounded PostgreSQL Health probe."""

from typing import Any, cast

import pytest
from sqlalchemy.exc import OperationalError, TimeoutError
from sqlalchemy.ext.asyncio import AsyncEngine

from netauto.application.health import DatabaseProbeTimedOut, DatabaseProbeUnavailable
from netauto.persistence.health import PostgreSQLHealthProbe


class FakeResult:
    def __init__(self, value: object) -> None:
        self.value = value

    def scalar_one(self) -> object:
        return self.value


class FakeConnection:
    def __init__(self, value: object = 1, error: BaseException | None = None) -> None:
        self.value = value
        self.error = error
        self.statements: list[str] = []
        self.exited = False

    async def __aenter__(self) -> FakeConnection:
        return self

    async def __aexit__(self, *args: object) -> None:
        del args
        self.exited = True

    async def execute(self, statement: object) -> FakeResult:
        self.statements.append(str(statement))
        if self.error is not None:
            raise self.error
        return FakeResult(self.value)


class FakeEngine:
    def __init__(self, connection: FakeConnection | None = None) -> None:
        self.connection = connection

    def connect(self) -> Any:
        if self.connection is None:
            raise TimeoutError("pool exhausted")
        return self.connection


@pytest.mark.asyncio
async def test_probe_executes_exact_select_one_and_requires_exact_integer() -> None:
    connection = FakeConnection()
    engine = FakeEngine(connection)
    probe = PostgreSQLHealthProbe(cast(AsyncEngine, engine))

    await probe.check()

    assert probe.engine is engine
    assert connection.statements == ["SELECT 1"]
    assert connection.exited


@pytest.mark.parametrize("value", [True, 0, 2, "1", None])
@pytest.mark.asyncio
async def test_probe_rejects_non_exact_scalar(value: object) -> None:
    probe = PostgreSQLHealthProbe(cast(AsyncEngine, FakeEngine(FakeConnection(value))))
    with pytest.raises(DatabaseProbeUnavailable):
        await probe.check()


@pytest.mark.asyncio
async def test_probe_translates_pool_timeout_without_raw_message() -> None:
    probe = PostgreSQLHealthProbe(cast(AsyncEngine, FakeEngine()))
    with pytest.raises(DatabaseProbeTimedOut) as captured:
        await probe.check()
    assert str(captured.value) == ""


@pytest.mark.asyncio
async def test_probe_translates_expected_database_failure_after_cleanup() -> None:
    raw = OperationalError("sensitive SQL", {}, Exception("sensitive driver text"))
    connection = FakeConnection(error=raw)
    probe = PostgreSQLHealthProbe(cast(AsyncEngine, FakeEngine(connection)))

    with pytest.raises(DatabaseProbeUnavailable) as captured:
        await probe.check()

    assert str(captured.value) == ""
    assert connection.exited


@pytest.mark.asyncio
async def test_probe_does_not_normalize_unexpected_failure() -> None:
    connection = FakeConnection(error=RuntimeError("programming defect"))
    probe = PostgreSQLHealthProbe(cast(AsyncEngine, FakeEngine(connection)))
    with pytest.raises(RuntimeError, match="programming defect"):
        await probe.check()
    assert connection.exited
