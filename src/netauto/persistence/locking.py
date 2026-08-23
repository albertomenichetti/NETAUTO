"""Central PostgreSQL lock planning and finite failure classification.

The module is the single physical authority for NETAUTO advisory gates, explicit
row locks, lock-plan phase discipline, and bounded semantic-UoW restarts.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable, Mapping
from dataclasses import dataclass, field
from enum import IntEnum, StrEnum, auto
from heapq import heappop, heappush
from typing import TYPE_CHECKING, Any, Protocol, cast
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql.schema import Table

from netauto.persistence.metadata import (
    datatype_versions,
    datatypes,
    object_template_versions,
    object_templates,
    objects,
    relationship_definition_versions,
    relationship_definitions,
    relationships,
)

if TYPE_CHECKING:
    from types import TracebackType


MAX_SEMANTIC_UOW_ATTEMPTS = 4


class AdvisoryGate(IntEnum):
    """Stable signed-BIGINT transaction advisory-lock registry."""

    OWNERSHIP_GRAPH_WRITE_GATE = 0x4E45544100000001
    RELATIONSHIP_DEFINITION_CONFLICT_GATE = 0x4E45544100000002
    MODEL_ROOT_DELETE_GATE = 0x4E45544100000003


class RowLockMode(IntEnum):
    """Sufficient initial mode precedence used while coalescing intents."""

    KS = 1
    S = 2
    NKU = 3
    U = 4


class RowLockClass(IntEnum):
    """Semantic lock-owner identities in global acquisition order."""

    OBJECT_TEMPLATE_HEADER = 10
    OBJECT_TEMPLATE_VERSION = 11
    DATA_TYPE_HEADER = 20
    DATA_TYPE_VERSION = 21
    RELATIONSHIP_DEFINITION_HEADER = 30
    RELATIONSHIP_DEFINITION_VERSION = 31
    OBJECT = 40
    RELATIONSHIP = 50

    @property
    def family_rank(self) -> int:
        """Return the frozen global family rank."""
        if self in {
            RowLockClass.OBJECT_TEMPLATE_HEADER,
            RowLockClass.OBJECT_TEMPLATE_VERSION,
        }:
            return 10
        if self in {RowLockClass.DATA_TYPE_HEADER, RowLockClass.DATA_TYPE_VERSION}:
            return 20
        if self in {
            RowLockClass.RELATIONSHIP_DEFINITION_HEADER,
            RowLockClass.RELATIONSHIP_DEFINITION_VERSION,
        }:
            return 30
        return int(self)

    @property
    def resource_rank(self) -> int:
        """Order a stable header before exact versions in one lineage."""
        if self in {
            RowLockClass.OBJECT_TEMPLATE_HEADER,
            RowLockClass.DATA_TYPE_HEADER,
            RowLockClass.RELATIONSHIP_DEFINITION_HEADER,
        }:
            return 0
        if self in {
            RowLockClass.OBJECT_TEMPLATE_VERSION,
            RowLockClass.DATA_TYPE_VERSION,
            RowLockClass.RELATIONSHIP_DEFINITION_VERSION,
        }:
            return 1
        return 0


@dataclass(frozen=True, slots=True)
class RowLockKey:
    """Canonical semantic identity of one explicitly locked row."""

    row_class: RowLockClass
    resource_id: UUID
    version: int | None = None

    def __post_init__(self) -> None:
        version_class = self.row_class in {
            RowLockClass.OBJECT_TEMPLATE_VERSION,
            RowLockClass.DATA_TYPE_VERSION,
            RowLockClass.RELATIONSHIP_DEFINITION_VERSION,
        }
        if version_class != (self.version is not None):
            raise ValueError("exact-version row identities require exactly one version")
        if self.version is not None and self.version < 1:
            raise ValueError("exact-version row identities require a positive version")


@dataclass(frozen=True, slots=True)
class RowLockIntent:
    """One requested initial lock mode for one semantic row."""

    key: RowLockKey
    mode: RowLockMode
    reason: str = field(default="", compare=False)


class LockPlanStale(Exception):
    """Optimistic discovery no longer describes the complete lock set."""


class LockPlanPhaseError(RuntimeError):
    """A gate/row/plan mutation was attempted after its legal phase."""


class LockPlanAttemptsExhausted(RuntimeError):
    """The bounded whole-UoW restart budget was exhausted."""


class ObjectTemplateAncestryError(RuntimeError):
    """Planned ObjectTemplate ancestry is persistently corrupt."""


class _LockPlanPhase(StrEnum):
    PLANNED = auto()
    ACQUIRING = auto()
    ACQUIRED = auto()
    DML = auto()


_LOCK_PHASE_INFO_KEY = "netauto.lock_plan_phase"


def reset_uow_lock_phase(connection: AsyncConnection) -> None:
    """Initialize the per-transaction explicit-lock phase."""
    connection.info[_LOCK_PHASE_INFO_KEY] = _LockPlanPhase.PLANNED


def clear_uow_lock_phase(connection: AsyncConnection) -> None:
    """Remove transaction-local phase state before returning a pooled connection."""
    connection.info.pop(_LOCK_PHASE_INFO_KEY, None)


def _coalesce(intents: Iterable[RowLockIntent]) -> dict[RowLockKey, RowLockIntent]:
    coalesced: dict[RowLockKey, RowLockIntent] = {}
    for intent in intents:
        current = coalesced.get(intent.key)
        if current is None or intent.mode > current.mode:
            coalesced[intent.key] = intent
    return coalesced


def _object_template_order(
    lineage_ids: set[UUID], parent_by_id: Mapping[UUID, UUID | None]
) -> dict[UUID, int]:
    """Produce the UUID-stable topological order for planned OT lineages."""
    for lineage_id in lineage_ids:
        if lineage_id not in parent_by_id:
            raise ValueError("every planned ObjectTemplate lineage needs ancestry")

    edges: dict[UUID, set[UUID]] = {lineage_id: set() for lineage_id in lineage_ids}
    indegree = {lineage_id: 0 for lineage_id in lineage_ids}
    for descendant in lineage_ids:
        seen: set[UUID] = set()
        current = parent_by_id[descendant]
        while current is not None:
            if current in seen or current == descendant:
                raise ValueError("ObjectTemplate ancestry contains a cycle")
            seen.add(current)
            if current not in parent_by_id:
                raise ValueError("ObjectTemplate ancestry contains a missing lineage")
            if current in lineage_ids and descendant not in edges[current]:
                edges[current].add(descendant)
                indegree[descendant] += 1
            current = parent_by_id[current]

    ready: list[tuple[int, UUID]] = []
    for lineage_id, degree in indegree.items():
        if degree == 0:
            heappush(ready, (lineage_id.int, lineage_id))
    result: list[UUID] = []
    while ready:
        _, lineage_id = heappop(ready)
        result.append(lineage_id)
        for child in sorted(edges[lineage_id], key=lambda value: value.int):
            indegree[child] -= 1
            if indegree[child] == 0:
                heappush(ready, (child.int, child))
    if len(result) != len(lineage_ids):
        raise ValueError("ObjectTemplate ancestry contains a cycle")
    return {lineage_id: index for index, lineage_id in enumerate(result)}


def _canonical_intents(
    intents: Iterable[RowLockIntent],
    object_template_parent_by_id: Mapping[UUID, UUID | None],
) -> tuple[RowLockIntent, ...]:
    coalesced = _coalesce(intents)
    ot_lineages = {
        key.resource_id
        for key in coalesced
        if key.row_class
        in {
            RowLockClass.OBJECT_TEMPLATE_HEADER,
            RowLockClass.OBJECT_TEMPLATE_VERSION,
        }
    }
    complete_parent_by_id = dict(object_template_parent_by_id)
    for lineage_id in ot_lineages:
        # A planned header may disappear after optimistic discovery, or may be
        # absent from the outset for an owning referenced-not-found outcome.
        # It still needs a deterministic acquisition position so the missing
        # planned row can be reported by acquire_lock_plan.
        complete_parent_by_id.setdefault(lineage_id, None)
    ot_order = (
        _object_template_order(ot_lineages, complete_parent_by_id)
        if ot_lineages
        else {}
    )

    def sort_key(intent: RowLockIntent) -> tuple[int, int, int, int, int]:
        key = intent.key
        lineage_order = (
            ot_order[key.resource_id]
            if key.row_class
            in {
                RowLockClass.OBJECT_TEMPLATE_HEADER,
                RowLockClass.OBJECT_TEMPLATE_VERSION,
            }
            else key.resource_id.int
        )
        return (
            key.row_class.family_rank,
            lineage_order,
            key.row_class.resource_rank,
            key.version or 0,
            key.resource_id.int,
        )

    return tuple(sorted(coalesced.values(), key=sort_key))


async def load_object_template_ancestry(
    connection: AsyncConnection, lineage_ids: Iterable[UUID]
) -> dict[UUID, UUID | None]:
    """Load only planned OT lineages and their distinct stable ancestors.

    One recursive statement owns planner ancestry materialization. Missing
    planned roots remain representable so row acquisition can report them;
    missing parents of existing rows and cycles are invariant failures.
    """
    planned = tuple(sorted(set(lineage_ids), key=lambda value: value.int))
    if not planned:
        return {}

    ancestry = (
        select(
            object_templates.c.id,
            object_templates.c.parent_template_id,
        )
        .where(object_templates.c.id.in_(planned))
        .cte("planned_object_template_ancestry", recursive=True)
    )
    parent = object_templates.alias("planned_object_template_parent")
    ancestry = ancestry.union(
        select(
            parent.c.id,
            parent.c.parent_template_id,
        ).select_from(
            ancestry.join(parent, parent.c.id == ancestry.c.parent_template_id)
        )
    )

    rows = (await connection.execute(select(ancestry))).mappings().all()
    loaded: dict[UUID, UUID | None] = {}
    for row in rows:
        lineage_id = cast(UUID, row["id"])
        parent_id = cast(UUID | None, row["parent_template_id"])
        previous = loaded.setdefault(lineage_id, parent_id)
        if previous != parent_id:
            raise ObjectTemplateAncestryError(
                "ObjectTemplate ancestry is not stable within one plan"
            )

    loaded_ids = set(loaded)
    if any(
        parent_id is not None and parent_id not in loaded_ids
        for parent_id in loaded.values()
    ):
        raise ObjectTemplateAncestryError(
            "ObjectTemplate ancestry contains a missing parent"
        )

    for lineage_id in loaded:
        current: UUID | None = lineage_id
        seen: set[UUID] = set()
        while current is not None:
            if current in seen:
                raise ObjectTemplateAncestryError(
                    "ObjectTemplate ancestry contains a cycle"
                )
            seen.add(current)
            current = loaded[current]

    for lineage_id in planned:
        loaded.setdefault(lineage_id, None)
    return loaded


async def prepare_lock_plan(
    connection: AsyncConnection,
    *,
    intents: Iterable[RowLockIntent] = (),
    gate: AdvisoryGate | None = None,
) -> LockPlan:
    """Prepare one plan and load targeted OT ancestry only when required."""
    requested = tuple(intents)
    object_template_lineages = {
        intent.key.resource_id
        for intent in requested
        if intent.key.row_class
        in {
            RowLockClass.OBJECT_TEMPLATE_HEADER,
            RowLockClass.OBJECT_TEMPLATE_VERSION,
        }
    }
    parents = (
        await load_object_template_ancestry(connection, object_template_lineages)
        if object_template_lineages
        else {}
    )
    return LockPlan(
        intents=requested,
        gate=gate,
        object_template_parent_by_id=parents,
    )


class LockPlan:
    """One complete, coalesced and canonically ordered pre-DML plan."""

    __slots__ = (
        "_connection",
        "_object_template_parents",
        "_phase",
        "gate",
        "rows",
    )

    def __init__(
        self,
        *,
        intents: Iterable[RowLockIntent] = (),
        gate: AdvisoryGate | None = None,
        object_template_parent_by_id: Mapping[UUID, UUID | None] | None = None,
    ) -> None:
        parents = dict(object_template_parent_by_id or {})
        self.gate = gate
        self.rows = _canonical_intents(intents, parents)
        self._object_template_parents = parents
        self._phase = _LockPlanPhase.PLANNED
        self._connection: AsyncConnection | None = None

    @property
    def phase(self) -> str:
        """Expose a bounded phase name for diagnostics and tests."""
        return self._phase.value

    def begin_dml(self) -> None:
        """Close the explicit-lock phase before the first current-state write."""
        if self._phase is not _LockPlanPhase.ACQUIRED:
            raise LockPlanPhaseError("DML requires one completely acquired lock plan")
        self._phase = _LockPlanPhase.DML
        if self._connection is not None:
            self._connection.info[_LOCK_PHASE_INFO_KEY] = _LockPlanPhase.DML

    def require_same_plan(
        self,
        intents: Iterable[RowLockIntent],
        *,
        gate: AdvisoryGate | None = None,
    ) -> None:
        """Reject plan expansion and signal a whole-UoW restart before DML."""
        if self._phase is _LockPlanPhase.DML:
            raise LockPlanPhaseError("the lock plan cannot change after DML begins")
        candidate = _canonical_intents(intents, self._object_template_parents)
        if gate != self.gate or candidate != self.rows:
            raise LockPlanStale("protected state requires a different complete plan")

    def begin_acquisition(self, connection: AsyncConnection | None = None) -> None:
        """Enter the single legal gate/row acquisition phase."""
        if self._phase is not _LockPlanPhase.PLANNED:
            raise LockPlanPhaseError("a lock plan can be acquired exactly once")
        if connection is not None:
            transaction_phase = connection.info.get(
                _LOCK_PHASE_INFO_KEY, _LockPlanPhase.PLANNED
            )
            if transaction_phase is not _LockPlanPhase.PLANNED:
                raise LockPlanPhaseError(
                    "one UoW permits exactly one pre-DML lock acquisition phase"
                )
            self._connection = connection
            connection.info[_LOCK_PHASE_INFO_KEY] = _LockPlanPhase.ACQUIRING
        self._phase = _LockPlanPhase.ACQUIRING

    def finish_acquisition(self) -> None:
        """Close acquisition after the complete planned key set was attempted."""
        if self._phase is not _LockPlanPhase.ACQUIRING:
            raise LockPlanPhaseError("lock-plan acquisition phase is invalid")
        self._phase = _LockPlanPhase.ACQUIRED
        if self._connection is not None:
            self._connection.info[_LOCK_PHASE_INFO_KEY] = _LockPlanPhase.ACQUIRED


@dataclass(frozen=True, slots=True)
class _RowTarget:
    table: Table
    identity_columns: tuple[Any, ...]


_ROW_TARGETS: dict[RowLockClass, _RowTarget] = {
    RowLockClass.OBJECT_TEMPLATE_HEADER: _RowTarget(
        object_templates, (object_templates.c.id,)
    ),
    RowLockClass.OBJECT_TEMPLATE_VERSION: _RowTarget(
        object_template_versions,
        (object_template_versions.c.template_id, object_template_versions.c.version),
    ),
    RowLockClass.DATA_TYPE_HEADER: _RowTarget(datatypes, (datatypes.c.id,)),
    RowLockClass.DATA_TYPE_VERSION: _RowTarget(
        datatype_versions,
        (datatype_versions.c.datatype_id, datatype_versions.c.version),
    ),
    RowLockClass.RELATIONSHIP_DEFINITION_HEADER: _RowTarget(
        relationship_definitions, (relationship_definitions.c.id,)
    ),
    RowLockClass.RELATIONSHIP_DEFINITION_VERSION: _RowTarget(
        relationship_definition_versions,
        (
            relationship_definition_versions.c.relationship_definition_id,
            relationship_definition_versions.c.version,
        ),
    ),
    RowLockClass.OBJECT: _RowTarget(objects, (objects.c.id,)),
    RowLockClass.RELATIONSHIP: _RowTarget(relationships, (relationships.c.id,)),
}


def row_lock_statement(intent: RowLockIntent) -> Select[tuple[Any, ...]]:
    """Build one exact one-table ordered PostgreSQL row-lock statement."""
    target = _ROW_TARGETS.get(intent.key.row_class)
    if target is None:
        raise ValueError("the requested row class has no table in the S00 schema")
    predicates = [target.identity_columns[0] == intent.key.resource_id]
    if len(target.identity_columns) == 2:
        predicates.append(target.identity_columns[1] == intent.key.version)
    statement = (
        select(*target.identity_columns)
        .select_from(target.table)
        .where(*predicates)
        .order_by(*target.identity_columns)
    )
    flags: dict[str, bool] = {}
    if intent.mode is RowLockMode.KS:
        flags = {"read": True, "key_share": True}
    elif intent.mode is RowLockMode.S:
        flags = {"read": True}
    elif intent.mode is RowLockMode.NKU:
        flags = {"key_share": True}
    return statement.with_for_update(of=target.table, **flags)


async def acquire_advisory_gate(
    connection: AsyncConnection, gate: AdvisoryGate
) -> None:
    """Acquire one transaction-scoped advisory gate."""
    transaction_phase = connection.info.get(
        _LOCK_PHASE_INFO_KEY, _LockPlanPhase.PLANNED
    )
    if transaction_phase in {_LockPlanPhase.ACQUIRED, _LockPlanPhase.DML}:
        raise LockPlanPhaseError("an advisory gate must precede all planned rows")
    direct_gate_only = transaction_phase is _LockPlanPhase.PLANNED
    if direct_gate_only:
        connection.info[_LOCK_PHASE_INFO_KEY] = _LockPlanPhase.ACQUIRING
    await connection.execute(select(func.pg_advisory_xact_lock(int(gate))))
    if direct_gate_only:
        # Low-level gate-only harnesses remain supported, but cannot append a
        # second gate or a fragmented row plan afterward.
        connection.info[_LOCK_PHASE_INFO_KEY] = _LockPlanPhase.ACQUIRED


async def acquire_lock_plan(
    connection: AsyncConnection, plan: LockPlan
) -> tuple[RowLockKey, ...]:
    """Acquire the optional gate and every row, returning missing planned rows."""
    plan.begin_acquisition(connection)
    if plan.gate is not None:
        await acquire_advisory_gate(connection, plan.gate)
    missing: list[RowLockKey] = []
    for intent in plan.rows:
        if (await connection.execute(row_lock_statement(intent))).first() is None:
            missing.append(intent.key)
    plan.finish_acquisition()
    return tuple(missing)


class PostgreSQLFailureKind(StrEnum):
    """Finite internal classes; none is a public transport result."""

    UNIQUE_VIOLATION = auto()
    FOREIGN_KEY_VIOLATION = auto()
    INVARIANT_VIOLATION = auto()
    DEADLOCK = auto()
    SERIALIZATION_FAILURE = auto()
    OPERATIONAL_FAILURE = auto()
    INTERNAL_ERROR = auto()


@dataclass(frozen=True, slots=True)
class ClassifiedPostgreSQLFailure:
    """Bounded internal PostgreSQL failure material."""

    kind: PostgreSQLFailureKind
    constraint_name: str | None = None


_KNOWN_UNIQUE_CONSTRAINTS = frozenset(
    {
        "datatypes_pkey",
        "datatype_versions_pkey",
        "uq_datatypes_namespace_name",
        "object_templates_pkey",
        "object_template_versions_pkey",
        "object_template_properties_pkey",
        "object_template_components_pkey",
        "uq_object_templates_namespace_name",
        "uq_object_template_properties_position",
        "uq_object_template_components_position",
        "relationship_definitions_pkey",
        "relationship_definition_versions_pkey",
        "relationship_definition_properties_pkey",
        "uq_relationship_definition_properties_position",
        "relationship_resolutions_pkey",
        "uq_relationship_resolutions_id_definition",
        "objects_pkey",
        "object_components_pkey",
        "relationships_pkey",
        "uq_relationships_id_definition",
        "runtime_relationship_resolutions_pkey",
        "object_lifecycle_events_pkey",
    }
)

_KNOWN_FOREIGN_KEY_CONSTRAINTS = frozenset(
    {
        "fk_datatype_versions_datatype",
        "fk_datatypes_default_version",
        "fk_object_templates_parent",
        "fk_object_template_versions_template",
        "fk_object_template_versions_parent_version",
        "fk_object_templates_default_version",
        "fk_object_template_properties_version",
        "fk_object_template_properties_datatype_version",
        "fk_object_template_components_version",
        "fk_object_template_components_target",
        "fk_relationship_resolutions_definition",
        "fk_relationship_resolutions_from_template",
        "fk_relationship_resolutions_to_template",
        "fk_relationship_definition_versions_definition",
        "fk_relationship_definitions_default_version",
        "fk_relationship_definition_properties_version",
        "fk_relationship_definition_properties_datatype_version",
        "fk_objects_template_version",
        "fk_object_components_child",
        "fk_object_components_parent",
        "fk_relationships_definition_version",
        "fk_runtime_resolutions_relationship_definition",
        "fk_runtime_resolutions_resolution_definition",
        "fk_runtime_resolutions_from_object",
        "fk_runtime_resolutions_to_object",
    }
)


def classify_postgresql_failure(
    error: BaseException | None = None,
    *,
    sqlstate: str | None = None,
    constraint_name: str | None = None,
) -> ClassifiedPostgreSQLFailure:
    """Classify only the frozen finite SQLSTATE/constraint combinations."""
    if error is not None:
        original = getattr(error, "orig", error)
        sqlstate = cast(str | None, getattr(original, "sqlstate", sqlstate))
        diagnostic = getattr(original, "diag", None)
        constraint_name = cast(
            str | None,
            getattr(diagnostic, "constraint_name", constraint_name),
        )
    if sqlstate == "23505":
        if constraint_name in _KNOWN_UNIQUE_CONSTRAINTS:
            return ClassifiedPostgreSQLFailure(
                PostgreSQLFailureKind.UNIQUE_VIOLATION, constraint_name
            )
        return ClassifiedPostgreSQLFailure(PostgreSQLFailureKind.INTERNAL_ERROR)
    if sqlstate == "23503":
        if constraint_name in _KNOWN_FOREIGN_KEY_CONSTRAINTS:
            return ClassifiedPostgreSQLFailure(
                PostgreSQLFailureKind.FOREIGN_KEY_VIOLATION, constraint_name
            )
        return ClassifiedPostgreSQLFailure(PostgreSQLFailureKind.INTERNAL_ERROR)
    if sqlstate in {"23514", "23502"}:
        return ClassifiedPostgreSQLFailure(PostgreSQLFailureKind.INVARIANT_VIOLATION)
    if sqlstate == "40P01":
        return ClassifiedPostgreSQLFailure(PostgreSQLFailureKind.DEADLOCK)
    if sqlstate == "40001":
        return ClassifiedPostgreSQLFailure(PostgreSQLFailureKind.SERIALIZATION_FAILURE)
    if sqlstate in {"55P03", "57014"}:
        return ClassifiedPostgreSQLFailure(PostgreSQLFailureKind.OPERATIONAL_FAILURE)
    return ClassifiedPostgreSQLFailure(PostgreSQLFailureKind.INTERNAL_ERROR)


class _SemanticUnitOfWork(Protocol):
    @property
    def connection(self) -> AsyncConnection: ...

    async def __aenter__(self) -> _SemanticUnitOfWork: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...


async def run_semantic_uow_attempts[ResultT](
    uow_factory: Callable[[], _SemanticUnitOfWork],
    attempt: Callable[[_SemanticUnitOfWork, int], Awaitable[ResultT]],
) -> ResultT:
    """Run a semantic operation with only bounded LockPlanStale restarts."""
    for attempt_number in range(1, MAX_SEMANTIC_UOW_ATTEMPTS + 1):
        try:
            async with uow_factory() as uow:
                return await attempt(uow, attempt_number)
        except LockPlanStale:
            if attempt_number == MAX_SEMANTIC_UOW_ATTEMPTS:
                break
    raise LockPlanAttemptsExhausted("semantic UoW restart budget exhausted")
