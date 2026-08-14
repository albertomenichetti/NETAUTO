"""Process-lifetime asynchronous PostgreSQL engine composition."""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from netauto.persistence.uow import UnitOfWorkFactory


@dataclass(frozen=True, slots=True)
class RuntimeContext:
    """Persistence resources owned by one application process lifespan."""

    engine: AsyncEngine
    uow_factory: UnitOfWorkFactory


def build_runtime_context(database_url: str) -> RuntimeContext:
    """Create lazy process resources without opening a database connection."""
    engine = create_async_engine(database_url, isolation_level="READ COMMITTED")
    return RuntimeContext(engine=engine, uow_factory=UnitOfWorkFactory(engine))
