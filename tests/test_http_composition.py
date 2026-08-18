"""Tests for side-effect-free and fail-closed HTTP composition."""

import asyncio
import importlib
import socket
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import FastAPI

import netauto
import netauto.entrypoints.http as http_module
from netauto.entrypoints.http import build_app, create_app
from netauto.persistence.engine import RuntimeContext
from netauto.persistence.uow import UnitOfWorkFactory
from netauto.runtime.schema_guard import SchemaRevisionMismatch
from netauto.settings import Settings

RUNTIME_DATABASE_URL = "postgresql+psycopg://runtime@example/runtime"


class FakeEngine:
    def __init__(self, events: list[str] | None = None) -> None:
        self.dispose = AsyncMock(side_effect=self._disposed)
        self.events = events

    async def _disposed(self) -> None:
        if self.events is not None:
            self.events.append("dispose")


def fake_runtime(engine: FakeEngine) -> RuntimeContext:
    return RuntimeContext(
        engine=engine,  # pyright: ignore[reportArgumentType]
        uow_factory=UnitOfWorkFactory(engine),  # pyright: ignore[reportArgumentType]
    )


def test_app_factory_uses_injected_settings_without_database_connection() -> None:
    settings = Settings(database_url=RUNTIME_DATABASE_URL)

    with patch.object(
        socket.socket,
        "connect",
        side_effect=AssertionError("composition attempted network I/O"),
    ):
        app = build_app(settings)
        schema = app.openapi()

    assert isinstance(app, FastAPI)
    assert app.state.settings is settings
    assert "/health/core" in schema["paths"]


def test_no_argument_uvicorn_factory_loads_process_settings_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NETAUTO_DATABASE_URL", RUNTIME_DATABASE_URL)

    with (
        patch.object(
            socket.socket,
            "connect",
            side_effect=AssertionError("factory attempted network I/O"),
        ),
        patch.object(
            http_module, "load_settings", wraps=http_module.load_settings
        ) as load,
    ):
        app = create_app()

    assert isinstance(app, FastAPI)
    assert app.state.settings.database_url == RUNTIME_DATABASE_URL
    load.assert_called_once_with()


@pytest.mark.asyncio
async def test_fastapi_lifespan_does_not_execute_migrations() -> None:
    app = build_app(Settings(database_url=RUNTIME_DATABASE_URL))

    with (
        patch.object(http_module, "require_exact_schema_revision", AsyncMock()),
        patch("alembic.command.upgrade") as upgrade,
        patch("alembic.command.stamp") as stamp,
    ):
        async with app.router.lifespan_context(app):
            pass

    upgrade.assert_not_called()
    stamp.assert_not_called()


@pytest.mark.asyncio
async def test_lifespan_order_shares_one_engine_and_disposes_on_shutdown() -> None:
    events: list[str] = []
    engine = FakeEngine(events)
    runtime = fake_runtime(engine)

    def configure(level: str) -> None:
        events.append(f"logging:{level}")

    def build(settings: Settings) -> RuntimeContext:
        assert settings.log_level == "DEBUG"
        events.append("runtime")
        return runtime

    async def guard(candidate: object) -> None:
        assert candidate is engine
        events.append("guard")

    class Probe:
        def __init__(self, candidate: object) -> None:
            assert candidate is engine
            self.engine = candidate
            events.append("probe")

    class Service:
        def __init__(self, probe: Probe) -> None:
            assert probe.engine is engine
            self.probe = probe
            events.append("service")

    with (
        patch.object(http_module, "configure_logging", configure),
        patch.object(http_module, "build_runtime_context", build),
        patch.object(http_module, "require_exact_schema_revision", guard),
        patch.object(http_module, "PostgreSQLHealthProbe", Probe),
        patch.object(http_module, "CoreHealthService", Service),
    ):
        app = build_app(Settings(database_url=RUNTIME_DATABASE_URL, log_level="DEBUG"))
        assert not hasattr(app.state, "runtime")
        async with app.router.lifespan_context(app):
            events.append("serving")
            assert app.state.runtime is runtime
            assert app.state.core_health_service.probe.engine is engine

    assert events == [
        "logging:DEBUG",
        "runtime",
        "guard",
        "probe",
        "service",
        "serving",
        "dispose",
    ]
    engine.dispose.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_guard_failure_prevents_publication_and_disposes_engine() -> None:
    engine = FakeEngine()
    app = build_app(Settings(database_url=RUNTIME_DATABASE_URL))
    with (
        patch.object(
            http_module, "build_runtime_context", return_value=fake_runtime(engine)
        ),
        patch.object(
            http_module,
            "require_exact_schema_revision",
            AsyncMock(side_effect=SchemaRevisionMismatch("expected x; actual y")),
        ),
    ):
        with pytest.raises(SchemaRevisionMismatch):
            async with app.router.lifespan_context(app):
                pytest.fail("failed guard entered serving")

    assert not hasattr(app.state, "runtime")
    assert not hasattr(app.state, "core_health_service")
    engine.dispose.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_composition_failure_after_guard_disposes_engine() -> None:
    engine = FakeEngine()
    app = build_app(Settings(database_url=RUNTIME_DATABASE_URL))
    with (
        patch.object(
            http_module, "build_runtime_context", return_value=fake_runtime(engine)
        ),
        patch.object(http_module, "require_exact_schema_revision", AsyncMock()),
        patch.object(
            http_module,
            "PostgreSQLHealthProbe",
            Mock(side_effect=RuntimeError("composition failure")),
        ),
    ):
        with pytest.raises(RuntimeError, match="composition failure"):
            async with app.router.lifespan_context(app):
                pytest.fail("failed composition entered serving")
    engine.dispose.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_cancelled_startup_disposes_engine_and_propagates() -> None:
    engine = FakeEngine()
    entered_guard = asyncio.Event()

    async def blocked_guard(_engine: object) -> None:
        entered_guard.set()
        await asyncio.Event().wait()

    app = build_app(Settings(database_url=RUNTIME_DATABASE_URL))

    async def startup() -> None:
        async with app.router.lifespan_context(app):
            pytest.fail("cancelled startup entered serving")

    with (
        patch.object(
            http_module, "build_runtime_context", return_value=fake_runtime(engine)
        ),
        patch.object(http_module, "require_exact_schema_revision", blocked_guard),
    ):
        task = asyncio.create_task(startup())
        await entered_guard.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    engine.dispose.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_every_app_lifespan_executes_its_own_guard() -> None:
    guard = AsyncMock()
    first_engine = FakeEngine()
    second_engine = FakeEngine()
    runtimes = iter((fake_runtime(first_engine), fake_runtime(second_engine)))

    def next_runtime(_settings: Settings) -> RuntimeContext:
        return next(runtimes)

    with (
        patch.object(http_module, "build_runtime_context", side_effect=next_runtime),
        patch.object(http_module, "require_exact_schema_revision", guard),
    ):
        first = build_app(Settings(database_url=RUNTIME_DATABASE_URL))
        second = build_app(Settings(database_url=RUNTIME_DATABASE_URL))
        async with first.router.lifespan_context(first):
            pass
        async with second.router.lifespan_context(second):
            pass

    assert guard.await_args_list[0].args == (first_engine,)
    assert guard.await_args_list[1].args == (second_engine,)
    first_engine.dispose.assert_awaited_once()
    second_engine.dispose.assert_awaited_once()


def test_importing_package_performs_no_network_io() -> None:
    with patch.object(
        socket.socket,
        "connect",
        side_effect=AssertionError("package import attempted network I/O"),
    ):
        importlib.reload(netauto)
