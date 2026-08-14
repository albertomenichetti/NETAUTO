"""Tests for side-effect-free HTTP composition."""

import importlib
import socket
from unittest.mock import patch

import pytest
from fastapi import FastAPI

import netauto
from netauto.entrypoints.http import build_app, create_app
from netauto.settings import Settings

RUNTIME_DATABASE_URL = "postgresql+psycopg://runtime@example/runtime"


def test_app_factory_uses_injected_settings_without_database_connection() -> None:
    settings = Settings(database_url=RUNTIME_DATABASE_URL)

    with patch.object(
        socket.socket,
        "connect",
        side_effect=AssertionError("composition attempted network I/O"),
    ):
        app = build_app(settings)

    assert isinstance(app, FastAPI)
    assert app.state.settings is settings


def test_no_argument_uvicorn_factory_uses_process_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NETAUTO_DATABASE_URL", RUNTIME_DATABASE_URL)

    with patch.object(
        socket.socket,
        "connect",
        side_effect=AssertionError("factory attempted network I/O"),
    ):
        app = create_app()

    assert isinstance(app, FastAPI)
    assert app.state.settings.database_url == RUNTIME_DATABASE_URL


@pytest.mark.asyncio
async def test_fastapi_lifespan_does_not_execute_migrations() -> None:
    app = build_app(Settings(database_url=RUNTIME_DATABASE_URL))

    with patch("alembic.command.upgrade") as upgrade:
        async with app.router.lifespan_context(app):
            pass

    upgrade.assert_not_called()


def test_importing_package_performs_no_network_io() -> None:
    with patch.object(
        socket.socket,
        "connect",
        side_effect=AssertionError("package import attempted network I/O"),
    ):
        importlib.reload(netauto)
