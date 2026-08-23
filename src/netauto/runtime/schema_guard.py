"""Exact installed-graph/database-revision startup compatibility guard."""

from __future__ import annotations

import asyncio

from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from alembic.util.exc import CommandError
from sqlalchemy.exc import DBAPIError, DisconnectionError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

CORE_STARTUP_SCHEMA_GUARD_TIMEOUT_SECONDS = 10.0


class MigrationGraphInvalid(RuntimeError):
    """The installed release does not contain one valid base/head graph."""


class SchemaGuardUnavailable(RuntimeError):
    """The current database revision could not be inspected safely."""


class SchemaRevisionMismatch(RuntimeError):
    """The current database revision is not the installed release head."""


def discover_unique_shipped_head() -> str:
    """Return the sole head from the installed ``netauto:migrations`` graph."""
    config = Config()
    config.set_main_option("script_location", "netauto:migrations")
    try:
        script = ScriptDirectory.from_config(config)
        bases = tuple(script.get_bases())
        heads = tuple(script.get_heads())
    except TimeoutError:
        raise
    except CommandError, ImportError, OSError, ValueError:
        raise MigrationGraphInvalid("installed migration graph is unreadable") from None
    if len(bases) != 1 or len(heads) != 1:
        raise MigrationGraphInvalid(
            "installed migration graph must contain exactly one base and one head"
        )
    return heads[0]


def _current_heads(sync_connection: object) -> tuple[str, ...]:
    context = MigrationContext.configure(sync_connection)  # type: ignore[arg-type]
    values = context.get_current_heads()
    if type(values) is not tuple or any(  # pyright: ignore[reportUnnecessaryIsInstance]
        type(value) is not str or not value  # pyright: ignore[reportUnnecessaryIsInstance]
        for value in values
    ):
        raise SchemaGuardUnavailable("database revision state is malformed")
    return tuple(sorted(values))


async def load_current_database_heads(engine: AsyncEngine) -> tuple[str, ...]:
    """Inspect actual Alembic heads through the runtime engine without writes."""
    try:
        async with engine.connect() as connection:
            return await connection.run_sync(_current_heads)
    except SchemaGuardUnavailable:
        raise
    except DBAPIError, DisconnectionError, SQLAlchemyError:
        raise SchemaGuardUnavailable(
            "database revision state could not be inspected"
        ) from None


async def _check_exact_schema_revision(engine: AsyncEngine) -> None:
    expected = await asyncio.to_thread(discover_unique_shipped_head)
    actual = await load_current_database_heads(engine)
    if actual != (expected,):
        actual_description = ",".join(actual) if actual else "none"
        raise SchemaRevisionMismatch(
            "database revision mismatch: "
            f"expected {expected}; actual {actual_description}"
        )


async def require_exact_schema_revision(engine: AsyncEngine) -> None:
    """Require exact singleton revision equality under the fixed startup deadline."""
    deadline = asyncio.timeout(CORE_STARTUP_SCHEMA_GUARD_TIMEOUT_SECONDS)
    try:
        async with deadline:
            await _check_exact_schema_revision(engine)
    except TimeoutError:
        if not deadline.expired():
            raise
        raise SchemaGuardUnavailable("database revision check timed out") from None
