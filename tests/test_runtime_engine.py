"""Permanent evidence for the one exact lazy runtime engine."""

import socket
from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.pool import QueuePool

from netauto.persistence.engine import build_runtime_context
from netauto.settings import Settings

RUNTIME_DATABASE_URL = "postgresql+psycopg://runtime@example/runtime"


def test_build_runtime_context_maps_exact_engine_keywords() -> None:
    sentinel = object()
    captured: list[tuple[str, dict[str, object]]] = []

    def fake_create(url: str, **kwargs: object) -> object:
        captured.append((url, kwargs))
        return sentinel

    settings = Settings(
        database_url=RUNTIME_DATABASE_URL,
        pool_size=3,
        max_overflow=4,
        pool_timeout=2.5,
        pool_recycle=60,
        pool_pre_ping=True,
    )
    with patch("netauto.persistence.engine.create_async_engine", fake_create):
        runtime = build_runtime_context(settings)

    assert captured == [
        (
            RUNTIME_DATABASE_URL,
            {
                "isolation_level": "READ COMMITTED",
                "pool_size": 3,
                "max_overflow": 4,
                "pool_timeout": 2.5,
                "pool_recycle": 60,
                "pool_pre_ping": True,
            },
        )
    ]
    assert runtime.engine is sentinel
    assert vars(runtime.uow_factory)["_engine"] is sentinel
    assert vars(runtime.uow_factory())["_engine"] is sentinel
    assert vars(runtime.uow_factory.coherent_read())["_engine"] is sentinel


def test_null_pool_recycle_maps_to_sqlalchemy_disabled_value() -> None:
    captured: dict[str, object] = {}

    def fake_create(url: str, **kwargs: object) -> object:
        del url
        captured.update(kwargs)
        return object()

    with patch("netauto.persistence.engine.create_async_engine", fake_create):
        build_runtime_context(Settings(database_url=RUNTIME_DATABASE_URL))

    assert captured["pool_recycle"] == -1


@pytest.mark.asyncio
async def test_real_engine_build_is_lazy_bounded_and_worker_local() -> None:
    settings = Settings(
        database_url=RUNTIME_DATABASE_URL,
        pool_size=2,
        max_overflow=1,
        pool_timeout=3.0,
    )
    with patch.object(
        socket.socket,
        "connect",
        side_effect=AssertionError("engine construction attempted network I/O"),
    ):
        first = build_runtime_context(settings)
        second = build_runtime_context(settings)

    try:
        assert isinstance(first.engine, AsyncEngine)
        assert first.engine is not second.engine
        pool = first.engine.sync_engine.pool
        assert isinstance(pool, QueuePool)
        assert pool.size() == 2
        assert pool.overflow() <= 1
        assert pool.timeout() == 3.0
    finally:
        await first.engine.dispose()
        await second.engine.dispose()
