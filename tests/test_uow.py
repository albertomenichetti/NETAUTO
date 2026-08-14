"""Real-PostgreSQL evidence for explicit async Unit of Work semantics."""

from uuid import uuid4

import pytest
from sqlalchemy import Engine, select, text
from sqlalchemy.ext.asyncio import create_async_engine

from netauto.persistence.metadata import datatypes
from netauto.persistence.uow import UnitOfWorkFactory


@pytest.mark.postgresql
@pytest.mark.asyncio
async def test_uow_commit_rollback_isolation_and_independent_connections(
    test_database_url: str, migrated_database_engine: Engine
) -> None:
    del migrated_database_engine
    engine = create_async_engine(test_database_url, isolation_level="READ COMMITTED")
    factory = UnitOfWorkFactory(engine)
    committed_id, implicit_rollback_id, exception_id = uuid4(), uuid4(), uuid4()

    try:
        async with factory() as uow:
            isolation = await uow.connection.scalar(text("SHOW transaction_isolation"))
            assert isolation == "read committed"
            await uow.connection.execute(
                datatypes.insert().values(
                    id=committed_id, namespace="s01", name="committed"
                )
            )
            await uow.commit()

        async with factory() as uow:
            await uow.connection.execute(
                datatypes.insert().values(
                    id=implicit_rollback_id,
                    namespace="s01",
                    name="implicit_rollback",
                )
            )

        with pytest.raises(RuntimeError, match="force rollback"):
            async with factory() as uow:
                await uow.connection.execute(
                    datatypes.insert().values(
                        id=exception_id, namespace="s01", name="exception_rollback"
                    )
                )
                raise RuntimeError("force rollback")

        async with factory() as first, factory() as second:
            first_pid = await first.connection.scalar(text("SELECT pg_backend_pid()"))
            second_pid = await second.connection.scalar(text("SELECT pg_backend_pid()"))
            assert first_pid != second_pid

        async with engine.connect() as connection:
            persisted = set(
                (
                    await connection.execute(
                        select(datatypes.c.id).where(
                            datatypes.c.id.in_(
                                [committed_id, implicit_rollback_id, exception_id]
                            )
                        )
                    )
                ).scalars()
            )
            assert persisted == {committed_id}
    finally:
        await engine.dispose()
