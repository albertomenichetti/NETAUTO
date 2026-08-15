"""Minimal explicit SQLAlchemy Core Unit of Work substrate."""

from types import TracebackType

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncTransaction


class UnitOfWork:
    """Own exactly one connection and transaction for one semantic operation."""

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine
        self._connection: AsyncConnection | None = None
        self._transaction: AsyncTransaction | None = None

    @property
    def connection(self) -> AsyncConnection:
        """Return the exclusively owned connection while this UoW is active."""
        if self._connection is None:
            raise RuntimeError("UnitOfWork is not active")
        return self._connection

    async def __aenter__(self) -> UnitOfWork:
        if self._connection is not None:
            raise RuntimeError("UnitOfWork cannot be entered more than once")
        self._connection = await self._engine.connect()
        try:
            self._transaction = await self._connection.begin()
        except BaseException:
            await self._connection.close()
            self._connection = None
            raise
        return self

    async def commit(self) -> None:
        """Commit only when the application operation explicitly decides to."""
        if self._transaction is None or not self._transaction.is_active:
            raise RuntimeError("UnitOfWork has no active transaction")
        await self._transaction.commit()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exc_type, exc_value, traceback
        transaction = self._transaction
        connection = self._connection
        try:
            if transaction is not None and transaction.is_active:
                await transaction.rollback()
        finally:
            if connection is not None:
                await connection.close()
            self._transaction = None
            self._connection = None


class CoherentReadUnitOfWork(UnitOfWork):
    """Own a REPEATABLE READ READ ONLY transaction for a composite read."""

    async def __aenter__(self) -> UnitOfWork:
        entered = await super().__aenter__()
        try:
            await self.connection.execute(
                text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
            )
        except BaseException as error:
            await super().__aexit__(type(error), error, error.__traceback__)
            raise
        return entered


class UnitOfWorkFactory:
    """Create independent UoWs backed by the process AsyncEngine."""

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    def __call__(self) -> UnitOfWork:
        return UnitOfWork(self._engine)

    def coherent_read(self) -> UnitOfWork:
        """Create a read-only UoW with one repeatable PostgreSQL snapshot."""
        return CoherentReadUnitOfWork(self._engine)
