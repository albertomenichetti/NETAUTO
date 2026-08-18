"""Process-lifetime asynchronous PostgreSQL engine composition."""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from netauto.persistence.uow import UnitOfWorkFactory
from netauto.settings import Settings


@dataclass(frozen=True, slots=True)
class RuntimeContext:
    """Persistence resources owned by one application process lifespan."""

    engine: AsyncEngine
    uow_factory: UnitOfWorkFactory


def build_runtime_context(settings: Settings) -> RuntimeContext:
    """Create lazy bounded process resources without opening a connection."""
    engine = create_async_engine(
        settings.database_url,
        isolation_level="READ COMMITTED",
        pool_size=settings.pool_size,
        max_overflow=settings.max_overflow,
        pool_timeout=settings.pool_timeout,
        pool_recycle=-1 if settings.pool_recycle is None else settings.pool_recycle,
        pool_pre_ping=settings.pool_pre_ping,
    )
    return RuntimeContext(engine=engine, uow_factory=UnitOfWorkFactory(engine))
