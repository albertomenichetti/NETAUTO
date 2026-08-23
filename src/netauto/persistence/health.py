"""PostgreSQL adapter for the Core database-readiness probe."""

from sqlalchemy import text
from sqlalchemy.exc import (
    DBAPIError,
    DisconnectionError,
    MultipleResultsFound,
    NoResultFound,
)
from sqlalchemy.exc import TimeoutError as PoolTimeout
from sqlalchemy.ext.asyncio import AsyncEngine

from netauto.application.health import DatabaseProbeTimedOut, DatabaseProbeUnavailable


class PostgreSQLHealthProbe:
    """Borrow one runtime connection and execute the exact active readiness query."""

    def __init__(self, engine: AsyncEngine) -> None:
        self.engine = engine

    async def check(self) -> None:
        try:
            async with self.engine.connect() as connection:
                result = await connection.execute(text("SELECT 1"))
                value = result.scalar_one()
        except PoolTimeout as error:
            raise DatabaseProbeTimedOut from error
        except (
            DBAPIError,
            DisconnectionError,
            MultipleResultsFound,
            NoResultFound,
        ) as error:
            raise DatabaseProbeUnavailable from error

        if type(value) is not int or value != 1:
            raise DatabaseProbeUnavailable
