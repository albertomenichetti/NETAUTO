"""Central registry for the two frozen M1 transaction advisory gates."""

from enum import IntEnum

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncConnection


class AdvisoryGate(IntEnum):
    """Stable signed-bigint keys in NETAUTO's application advisory-lock namespace."""

    OWNERSHIP_GRAPH_WRITE_GATE = 0x4E45544100000001
    RELATIONSHIP_DEFINITION_CONFLICT_GATE = 0x4E45544100000002


async def acquire_advisory_gate(
    connection: AsyncConnection, gate: AdvisoryGate
) -> None:
    """Acquire one transaction-level gate; PostgreSQL releases it at tx end."""
    await connection.execute(select(func.pg_advisory_xact_lock(int(gate))))
