"""Pure and real-PostgreSQL evidence for the exact startup revision guard."""

import asyncio
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncEngine

import netauto.runtime.schema_guard as guard_module
from netauto.persistence.engine import build_runtime_context
from netauto.runtime.schema_guard import (
    MigrationGraphInvalid,
    SchemaGuardUnavailable,
    SchemaRevisionMismatch,
    discover_unique_shipped_head,
    load_current_database_heads,
    require_exact_schema_revision,
)
from netauto.settings import Settings

ROOT = Path(__file__).parents[1]


class FakeScript:
    def __init__(self, bases: tuple[str, ...], heads: tuple[str, ...]) -> None:
        self.bases = bases
        self.heads = heads

    def get_bases(self) -> tuple[str, ...]:
        return self.bases

    def get_heads(self) -> tuple[str, ...]:
        return self.heads


def test_installed_graph_discovers_one_base_and_head_without_alembic_ini() -> None:
    assert discover_unique_shipped_head() == "0001_m2_kernel"


@pytest.mark.parametrize(
    ("bases", "heads"),
    [
        ((), ("head",)),
        (("base-a", "base-b"), ("head",)),
        (("base",), ()),
        (("base",), ("head-a", "head-b")),
    ],
)
def test_installed_graph_rejects_non_unique_base_or_head(
    bases: tuple[str, ...], heads: tuple[str, ...]
) -> None:
    with patch.object(
        guard_module.ScriptDirectory,
        "from_config",
        return_value=FakeScript(bases, heads),
    ):
        with pytest.raises(MigrationGraphInvalid, match="exactly one"):
            discover_unique_shipped_head()


def test_installed_graph_rejects_unreadable_package_safely() -> None:
    with patch.object(
        guard_module.ScriptDirectory,
        "from_config",
        side_effect=OSError("sensitive filesystem detail"),
    ):
        with pytest.raises(MigrationGraphInvalid) as captured:
            discover_unique_shipped_head()
    assert "sensitive" not in str(captured.value)


@pytest.mark.asyncio
async def test_guard_requires_exact_singleton_revision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def actual(_engine: object) -> tuple[str, ...]:
        return ("different", "head")

    monkeypatch.setattr(
        guard_module, "discover_unique_shipped_head", lambda: "expected"
    )
    monkeypatch.setattr(guard_module, "load_current_database_heads", actual)

    with pytest.raises(SchemaRevisionMismatch) as captured:
        await require_exact_schema_revision(object())  # pyright: ignore[reportArgumentType]

    message = str(captured.value)
    assert "expected" in message
    assert "different,head" in message
    assert "postgresql" not in message


@pytest.mark.asyncio
async def test_guard_timeout_is_one_safe_owned_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def blocked(_engine: object) -> None:
        await asyncio.Event().wait()

    monkeypatch.setattr(guard_module, "_check_exact_schema_revision", blocked)
    monkeypatch.setattr(guard_module, "CORE_STARTUP_SCHEMA_GUARD_TIMEOUT_SECONDS", 0.01)

    with pytest.raises(SchemaGuardUnavailable, match="timed out"):
        await require_exact_schema_revision(object())  # pyright: ignore[reportArgumentType]


class UnreachableEngine:
    def connect(self) -> Any:
        raise OperationalError("sensitive SQL", {}, Exception("sensitive DSN"))


@pytest.mark.asyncio
async def test_current_head_inspection_translates_unreachable_database_safely() -> None:
    with pytest.raises(SchemaGuardUnavailable) as captured:
        await load_current_database_heads(cast(AsyncEngine, UnreachableEngine()))
    assert "sensitive" not in str(captured.value)


def _set_revision_state(engine: Engine, state: str) -> None:
    with engine.begin() as connection:
        if state == "missing-table":
            connection.execute(text("DROP TABLE alembic_version"))
            return
        connection.execute(text("DELETE FROM alembic_version"))
        if state == "base-empty":
            return
        revisions = {
            "old": ("0000_old",),
            "newer": ("9999_newer",),
            "unknown": ("unknown_revision",),
            "multiple": ("head_a", "head_b"),
        }[state]
        for revision in revisions:
            connection.execute(
                text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
                {"revision": revision},
            )


def _restore_expected_revision(engine: Engine, expected: str) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE IF NOT EXISTS alembic_version "
                "(version_num VARCHAR(32) NOT NULL, "
                "CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))"
            )
        )
        connection.execute(text("DELETE FROM alembic_version"))
        connection.execute(
            text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
            {"revision": expected},
        )


@pytest.mark.postgresql
@pytest.mark.migration
@pytest.mark.asyncio
async def test_real_postgresql_exact_head_uses_runtime_engine(
    migrated_database_engine: Engine, test_database_url: str
) -> None:
    del migrated_database_engine
    runtime = build_runtime_context(Settings(database_url=test_database_url))
    try:
        assert await load_current_database_heads(runtime.engine) == (
            discover_unique_shipped_head(),
        )
        await require_exact_schema_revision(runtime.engine)
    finally:
        await runtime.engine.dispose()


@pytest.mark.parametrize(
    "state", ["missing-table", "base-empty", "old", "newer", "unknown", "multiple"]
)
@pytest.mark.postgresql
@pytest.mark.migration
@pytest.mark.asyncio
async def test_real_postgresql_rejects_every_non_exact_revision_state_and_restores(
    migrated_database_engine: Engine,
    test_database_url: str,
    state: str,
) -> None:
    expected = discover_unique_shipped_head()
    _set_revision_state(migrated_database_engine, state)
    runtime = build_runtime_context(Settings(database_url=test_database_url))
    try:
        with pytest.raises(SchemaRevisionMismatch):
            await require_exact_schema_revision(runtime.engine)
    finally:
        await runtime.engine.dispose()
        _restore_expected_revision(migrated_database_engine, expected)

    runtime = build_runtime_context(Settings(database_url=test_database_url))
    try:
        await require_exact_schema_revision(runtime.engine)
    finally:
        await runtime.engine.dispose()


def test_startup_guard_source_has_no_revision_constant_migration_or_repair() -> None:
    source = (ROOT / "src/netauto/runtime/schema_guard.py").read_text()
    forbidden = (
        "0001_m2_kernel",
        "alembic.command",
        "command.upgrade",
        "command.stamp",
        "CREATE TABLE",
        "DROP TABLE",
        "ALTER TABLE",
        "compare_metadata",
    )
    assert all(fragment not in source for fragment in forbidden)
