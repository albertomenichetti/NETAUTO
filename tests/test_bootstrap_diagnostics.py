"""Complete factory, ASGI and Uvicorn bootstrap diagnostic evidence."""

import asyncio
import logging
import traceback
from collections.abc import Callable
from pathlib import Path
from typing import Any, Never, cast
from unittest.mock import AsyncMock

import pytest
from alembic.config import Config as AlembicConfig
from fastapi import FastAPI
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.types import Message, Receive, Scope, Send
from uvicorn import Config
from uvicorn.lifespan.on import LifespanOn

import netauto.entrypoints.http as http_module
import netauto.runtime.schema_guard as guard_module
import netauto.settings as settings_module
from netauto.entrypoints.http import build_app, create_app
from netauto.persistence.engine import RuntimeContext
from netauto.persistence.uow import UnitOfWorkFactory
from netauto.runtime.schema_guard import (
    MigrationGraphInvalid,
    SchemaGuardUnavailable,
    load_current_database_heads,
)
from netauto.settings import Settings, SettingsBootstrapError, load_settings

SAFE_RUNTIME_URL = "postgresql+psycopg://runtime@example/runtime"
RAW_SENTINELS = (
    "DRIVER_SENTINEL",
    "USER_SENTINEL",
    "PASSWORD_SENTINEL",
    "HOST_SENTINEL",
    "6543",
    "DATABASE_SENTINEL",
    "QUERY_SENTINEL",
    "PATH_SENTINEL",
    "SQL_SENTINEL",
    "SQLSTATE_SENTINEL",
    "CONSTRAINT_SENTINEL",
    "PROTOCOL_SENTINEL",
)
INVALID_CREDENTIAL_URL = (
    "postgresql+DRIVER_SENTINEL://USER_SENTINEL:PASSWORD_SENTINEL@"
    "HOST_SENTINEL:6543/DATABASE_SENTINEL?QUERY_SENTINEL=value"
)


def _assert_sanitized(text: str) -> None:
    assert all(sentinel not in text for sentinel in RAW_SENTINELS)


def _rendered_exception(error: BaseException) -> str:
    return f"{error!s}\n{error!r}\n{''.join(traceback.format_exception(error))}"


def _capture_bootstrap_failure(
    operation: Callable[[], object],
) -> tuple[SettingsBootstrapError, str]:
    try:
        operation()
    except SettingsBootstrapError as error:
        return error, _rendered_exception(error) + traceback.format_exc()
    pytest.fail("invalid bootstrap input was accepted")


def test_factory_settings_failure_diagnostic_sanitizes_credentials(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("NETAUTO_DATABASE_URL", INVALID_CREDENTIAL_URL)

    error, rendered = _capture_bootstrap_failure(create_app)

    assert str(error) == "runtime settings are invalid"
    assert error.__cause__ is None
    assert error.__suppress_context__
    _assert_sanitized(rendered + caplog.text)

    try:
        Settings(database_url=INVALID_CREDENTIAL_URL)
    except ValueError as direct_error:
        direct_rendered = _rendered_exception(direct_error) + traceback.format_exc()
    else:
        pytest.fail("invalid direct Settings were accepted")
    _assert_sanitized(direct_rendered)


def test_secret_selector_and_source_diagnostics_hide_selected_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    selected = str(tmp_path / "PATH_SENTINEL-missing")
    monkeypatch.setenv("NETAUTO_DATABASE_URL", SAFE_RUNTIME_URL)
    monkeypatch.setenv("NETAUTO_SECRETS_DIR", selected)

    error, rendered = _capture_bootstrap_failure(load_settings)

    assert str(error) == "NETAUTO_SECRETS_DIR does not exist"
    assert error.__cause__ is None
    assert error.__suppress_context__
    _assert_sanitized(rendered)


class DiagnosticEngine:
    def __init__(self, mode: str = "unused") -> None:
        self.mode = mode
        self.dispose = AsyncMock()

    def connect(self) -> Any:
        if self.mode == "unreachable":
            raise OperationalError(
                "SQL_SENTINEL CONSTRAINT_SENTINEL",
                {},
                RuntimeError("PROTOCOL_SENTINEL SQLSTATE_SENTINEL HOST_SENTINEL"),
            )
        return DiagnosticConnection()


class DiagnosticConnection:
    async def __aenter__(self) -> DiagnosticConnection:
        return self

    async def __aexit__(self, *args: object) -> None:
        del args

    async def run_sync(self, function: Callable[[object], object]) -> object:
        del function
        raise OperationalError(
            "SQL_SENTINEL CONSTRAINT_SENTINEL",
            {},
            RuntimeError("PROTOCOL_SENTINEL SQLSTATE_SENTINEL"),
        )


def _runtime(engine: DiagnosticEngine) -> RuntimeContext:
    typed = cast(AsyncEngine, engine)
    return RuntimeContext(engine=typed, uow_factory=UnitOfWorkFactory(typed))


def _unreadable_graph(_config: AlembicConfig) -> Never:
    raise OSError("PATH_SENTINEL")


async def _lifespan_failure(app: FastAPI) -> tuple[BaseException, str]:
    messages: list[Message] = []
    received = False

    async def receive() -> Message:
        nonlocal received
        if received:
            await asyncio.Event().wait()
        received = True
        return {"type": "lifespan.startup"}

    async def send(message: Message) -> None:
        messages.append(message)

    scope = cast(
        Scope,
        {
            "type": "lifespan",
            "asgi": {"version": "3.0", "spec_version": "2.0"},
            "state": {},
        },
    )
    try:
        await app.router.lifespan(scope, cast(Receive, receive), cast(Send, send))
    except BaseException as error:
        captured = error
    else:
        pytest.fail("failed lifespan entered serving")

    failures = [item for item in messages if item["type"] == "lifespan.startup.failed"]
    assert len(failures) == 1
    return captured, cast(str, failures[0]["message"])


@pytest.mark.parametrize(
    ("mode", "category", "exception_type"),
    [
        ("graph", "installed migration graph is unreadable", MigrationGraphInvalid),
        (
            "unreachable",
            "database revision state could not be inspected",
            SchemaGuardUnavailable,
        ),
        (
            "query",
            "database revision state could not be inspected",
            SchemaGuardUnavailable,
        ),
        ("timeout", "database revision check timed out", SchemaGuardUnavailable),
    ],
)
@pytest.mark.asyncio
async def test_asgi_lifespan_expected_guard_diagnostics_are_sanitized(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    mode: str,
    category: str,
    exception_type: type[BaseException],
) -> None:
    engine = DiagnosticEngine(mode)

    def runtime_factory(_settings: Settings) -> RuntimeContext:
        return _runtime(engine)

    monkeypatch.setattr(http_module, "build_runtime_context", runtime_factory)
    if mode == "graph":
        monkeypatch.setattr(
            guard_module.ScriptDirectory,
            "from_config",
            _unreadable_graph,
        )
    elif mode == "timeout":

        async def blocked(_engine: object) -> None:
            await asyncio.Event().wait()

        monkeypatch.setattr(guard_module, "_check_exact_schema_revision", blocked)
        monkeypatch.setattr(
            guard_module, "CORE_STARTUP_SCHEMA_GUARD_TIMEOUT_SECONDS", 0.01
        )

    app = build_app(Settings(database_url=SAFE_RUNTIME_URL))
    error, message = await _lifespan_failure(app)

    assert isinstance(error, exception_type)
    assert error.__cause__ is None
    assert error.__suppress_context__ or error.__context__ is None
    assert category in message
    _assert_sanitized(message + caplog.text)
    engine.dispose.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_uvicorn_lifespan_logging_sanitizes_expected_guard_failure(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    engine = DiagnosticEngine()

    def runtime_factory(_settings: Settings) -> RuntimeContext:
        return _runtime(engine)

    monkeypatch.setattr(http_module, "build_runtime_context", runtime_factory)
    monkeypatch.setattr(
        guard_module.ScriptDirectory,
        "from_config",
        _unreadable_graph,
    )
    app = build_app(Settings(database_url=SAFE_RUNTIME_URL))
    caplog.set_level(logging.ERROR, logger="uvicorn.error")
    lifespan = LifespanOn(Config(app=app, lifespan="on", log_config=None))

    await lifespan.startup()
    await asyncio.sleep(0)

    assert lifespan.startup_failed
    assert lifespan.should_exit
    assert "installed migration graph is unreadable" in caplog.text
    _assert_sanitized(caplog.text)
    engine.dispose.assert_awaited_once_with()


@pytest.mark.parametrize("boundary", ["settings", "graph", "current-head"])
@pytest.mark.asyncio
async def test_bootstrap_unexpected_defects_are_not_normalized(
    monkeypatch: pytest.MonkeyPatch,
    boundary: str,
) -> None:
    defect = RuntimeError("unexpected programming defect")
    if boundary == "settings":
        monkeypatch.setenv("NETAUTO_DATABASE_URL", SAFE_RUNTIME_URL)

        def broken_settings(**kwargs: object) -> Settings:
            del kwargs
            raise defect

        monkeypatch.setattr(settings_module, "Settings", broken_settings)
        with pytest.raises(RuntimeError) as captured:
            load_settings()
    elif boundary == "graph":

        def broken_graph(_config: AlembicConfig) -> Never:
            raise defect

        monkeypatch.setattr(
            guard_module.ScriptDirectory,
            "from_config",
            broken_graph,
        )
        with pytest.raises(RuntimeError) as captured:
            guard_module.discover_unique_shipped_head()
    else:

        class DefectiveConnection(DiagnosticConnection):
            async def run_sync(self, function: Callable[[object], object]) -> object:
                del function
                raise defect

        class DefectiveEngine(DiagnosticEngine):
            def connect(self) -> Any:
                return DefectiveConnection()

        with pytest.raises(RuntimeError) as captured:
            await load_current_database_heads(cast(AsyncEngine, DefectiveEngine()))

    assert captured.value is defect
