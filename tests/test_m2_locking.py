"""M2-S00 PLAN-01..PLAN-06 evidence for the central lock boundary."""

from collections.abc import Awaitable, Callable
from types import TracebackType
from typing import cast
from uuid import UUID

import pytest
from hypothesis import given
from hypothesis import strategies as st
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncConnection

import netauto.persistence.locking as locking
from netauto.domain.objecttemplates import LocalComponent, LocalProperty, ValueMode
from netauto.persistence.locking import (
    MAX_SEMANTIC_UOW_ATTEMPTS,
    AdvisoryGate,
    LockPlan,
    LockPlanAttemptsExhausted,
    LockPlanPhaseError,
    LockPlanStale,
    PostgreSQLFailureKind,
    RowLockClass,
    RowLockIntent,
    RowLockKey,
    RowLockMode,
    acquire_advisory_gate,
    acquire_lock_plan,
    classify_postgresql_failure,
    prepare_lock_plan,
    row_lock_statement,
    run_semantic_uow_attempts,
)
from netauto.persistence.objecttemplates import declaration_delta


def _uuid(value: int) -> UUID:
    return UUID(int=value)


def _intent(
    row_class: RowLockClass,
    resource_id: int,
    mode: RowLockMode,
    version: int | None = None,
) -> RowLockIntent:
    return RowLockIntent(RowLockKey(row_class, _uuid(resource_id), version), mode)


@pytest.mark.parametrize(
    ("mode", "clause"),
    [
        (RowLockMode.KS, "FOR KEY SHARE OF datatype_versions"),
        (RowLockMode.S, "FOR SHARE OF datatype_versions"),
        (RowLockMode.NKU, "FOR NO KEY UPDATE OF datatype_versions"),
        (RowLockMode.U, "FOR UPDATE OF datatype_versions"),
    ],
)
def test_plan_01_lock_sql_compilation(mode: RowLockMode, clause: str) -> None:
    statement = row_lock_statement(_intent(RowLockClass.DATA_TYPE_VERSION, 1, mode, 2))
    sql = str(
        statement.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )
    assert "FROM datatype_versions" in sql
    assert "JOIN" not in sql
    assert "ORDER BY datatype_versions.datatype_id, datatype_versions.version" in sql
    assert clause in sql
    assert "NOWAIT" not in sql
    assert "SKIP LOCKED" not in sql


def test_plan_02_coalescence_and_canonical_sorting() -> None:
    root = _uuid(20)
    child = _uuid(10)
    unrelated = _uuid(5)
    intents = (
        RowLockIntent(RowLockKey(RowLockClass.RELATIONSHIP, _uuid(1)), RowLockMode.U),
        RowLockIntent(RowLockKey(RowLockClass.OBJECT, _uuid(4)), RowLockMode.NKU),
        RowLockIntent(
            RowLockKey(RowLockClass.DATA_TYPE_HEADER, _uuid(2)), RowLockMode.S
        ),
        RowLockIntent(
            RowLockKey(RowLockClass.OBJECT_TEMPLATE_VERSION, child, 3),
            RowLockMode.S,
        ),
        RowLockIntent(
            RowLockKey(RowLockClass.OBJECT_TEMPLATE_HEADER, child), RowLockMode.KS
        ),
        RowLockIntent(
            RowLockKey(RowLockClass.OBJECT_TEMPLATE_HEADER, root), RowLockMode.KS
        ),
        RowLockIntent(
            RowLockKey(RowLockClass.OBJECT_TEMPLATE_VERSION, root, 2),
            RowLockMode.KS,
        ),
        RowLockIntent(
            RowLockKey(RowLockClass.OBJECT_TEMPLATE_HEADER, unrelated), RowLockMode.S
        ),
        RowLockIntent(RowLockKey(RowLockClass.OBJECT, _uuid(4)), RowLockMode.U),
    )
    plan = LockPlan(
        intents=reversed(intents),
        object_template_parent_by_id={root: None, child: root, unrelated: None},
    )
    assert [
        (item.key.row_class, item.key.resource_id, item.key.version)
        for item in plan.rows
    ] == [
        (RowLockClass.OBJECT_TEMPLATE_HEADER, unrelated, None),
        (RowLockClass.OBJECT_TEMPLATE_HEADER, root, None),
        (RowLockClass.OBJECT_TEMPLATE_VERSION, root, 2),
        (RowLockClass.OBJECT_TEMPLATE_HEADER, child, None),
        (RowLockClass.OBJECT_TEMPLATE_VERSION, child, 3),
        (RowLockClass.DATA_TYPE_HEADER, _uuid(2), None),
        (RowLockClass.OBJECT, _uuid(4), None),
        (RowLockClass.RELATIONSHIP, _uuid(1), None),
    ]
    assert plan.rows[-2].mode is RowLockMode.U


@given(st.permutations(tuple(range(9))))
def test_plan_02_arbitrary_input_permutations_are_canonical(
    permutation: list[int],
) -> None:
    root = _uuid(20)
    child = _uuid(10)
    unrelated = _uuid(5)
    intents = (
        _intent(RowLockClass.RELATIONSHIP, 1, RowLockMode.U),
        _intent(RowLockClass.OBJECT, 4, RowLockMode.NKU),
        _intent(RowLockClass.DATA_TYPE_HEADER, 2, RowLockMode.S),
        RowLockIntent(
            RowLockKey(RowLockClass.OBJECT_TEMPLATE_VERSION, child, 3),
            RowLockMode.S,
        ),
        RowLockIntent(
            RowLockKey(RowLockClass.OBJECT_TEMPLATE_HEADER, child), RowLockMode.KS
        ),
        RowLockIntent(
            RowLockKey(RowLockClass.OBJECT_TEMPLATE_HEADER, root), RowLockMode.KS
        ),
        RowLockIntent(
            RowLockKey(RowLockClass.OBJECT_TEMPLATE_VERSION, root, 2), RowLockMode.KS
        ),
        RowLockIntent(
            RowLockKey(RowLockClass.OBJECT_TEMPLATE_HEADER, unrelated), RowLockMode.S
        ),
        _intent(RowLockClass.OBJECT, 4, RowLockMode.U),
    )
    parents = {root: None, child: root, unrelated: None}
    expected = LockPlan(intents=intents, object_template_parent_by_id=parents).rows
    permuted = LockPlan(
        intents=(intents[index] for index in permutation),
        object_template_parent_by_id=parents,
    )
    assert permuted.rows == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("row_class", "version"),
    [
        (RowLockClass.DATA_TYPE_HEADER, None),
        (RowLockClass.RELATIONSHIP_DEFINITION_HEADER, None),
        (RowLockClass.OBJECT, None),
        (RowLockClass.RELATIONSHIP, None),
    ],
)
async def test_plan_02_non_template_plans_do_not_load_ancestry(
    monkeypatch: pytest.MonkeyPatch,
    row_class: RowLockClass,
    version: int | None,
) -> None:
    async def forbidden_loader(
        connection: AsyncConnection, lineage_ids: object
    ) -> dict[UUID, UUID | None]:
        del connection, lineage_ids
        raise AssertionError("non-OT plan invoked the ancestry loader")

    monkeypatch.setattr(locking, "load_object_template_ancestry", forbidden_loader)
    connection = cast(AsyncConnection, object())
    intent = RowLockIntent(RowLockKey(row_class, _uuid(80), version), RowLockMode.KS)
    plan = await prepare_lock_plan(connection, intents=(intent,))
    assert plan.rows == (intent,)


def test_plan_02_missing_object_template_header_remains_plannable() -> None:
    missing = _uuid(99)
    plan = LockPlan(
        intents=(
            RowLockIntent(
                RowLockKey(RowLockClass.OBJECT_TEMPLATE_HEADER, missing),
                RowLockMode.KS,
            ),
        ),
        object_template_parent_by_id={},
    )
    assert plan.rows[0].key.resource_id == missing


def test_plan_03_stale_and_post_dml_expansion_are_distinct() -> None:
    initial = (_intent(RowLockClass.OBJECT, 1, RowLockMode.NKU),)
    expanded = (*initial, _intent(RowLockClass.OBJECT, 2, RowLockMode.KS))
    plan = LockPlan(intents=initial)
    with pytest.raises(LockPlanStale):
        plan.require_same_plan(expanded)
    plan.begin_acquisition()
    plan.finish_acquisition()
    plan.begin_dml()
    with pytest.raises(LockPlanPhaseError):
        plan.require_same_plan(expanded)


@pytest.mark.parametrize(
    ("sqlstate", "constraint", "expected"),
    [
        (
            "23505",
            "uq_datatypes_namespace_name",
            PostgreSQLFailureKind.UNIQUE_VIOLATION,
        ),
        (
            "23503",
            "fk_objects_template_version",
            PostgreSQLFailureKind.FOREIGN_KEY_VIOLATION,
        ),
        ("23514", None, PostgreSQLFailureKind.INVARIANT_VIOLATION),
        ("23502", None, PostgreSQLFailureKind.INVARIANT_VIOLATION),
        ("40P01", None, PostgreSQLFailureKind.DEADLOCK),
        ("40001", None, PostgreSQLFailureKind.SERIALIZATION_FAILURE),
        ("55P03", None, PostgreSQLFailureKind.OPERATIONAL_FAILURE),
        ("57014", None, PostgreSQLFailureKind.OPERATIONAL_FAILURE),
        ("23505", "unknown_unique", PostgreSQLFailureKind.INTERNAL_ERROR),
        ("23503", "unknown_fk", PostgreSQLFailureKind.INTERNAL_ERROR),
        ("99999", None, PostgreSQLFailureKind.INTERNAL_ERROR),
    ],
)
def test_plan_04_finite_postgresql_failure_classifier(
    sqlstate: str, constraint: str | None, expected: PostgreSQLFailureKind
) -> None:
    classified = classify_postgresql_failure(
        sqlstate=sqlstate, constraint_name=constraint
    )
    assert classified.kind is expected
    if expected is PostgreSQLFailureKind.INTERNAL_ERROR:
        assert classified.constraint_name is None


class _FakeUow:
    def __init__(self, identity: int) -> None:
        self.identity = identity
        self.connection = cast(AsyncConnection, object())

    async def __aenter__(self) -> _FakeUow:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exc_type, exc_value, traceback


@pytest.mark.asyncio
async def test_plan_05_exactly_four_fresh_uow_attempts() -> None:
    created: list[_FakeUow] = []

    def factory() -> _FakeUow:
        value = _FakeUow(len(created) + 1)
        created.append(value)
        return value

    seen: list[tuple[int, int]] = []

    async def attempt(uow: object, number: int) -> None:
        value = cast(_FakeUow, uow)
        seen.append((value.identity, number))
        raise LockPlanStale

    typed_attempt = cast(Callable[[object, int], Awaitable[None]], attempt)
    with pytest.raises(LockPlanAttemptsExhausted):
        await run_semantic_uow_attempts(factory, typed_attempt)
    assert len(created) == MAX_SEMANTIC_UOW_ATTEMPTS == 4
    assert seen == [(1, 1), (2, 2), (3, 3), (4, 4)]
    assert len({id(item) for item in created}) == 4


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error",
    [
        ValueError("semantic failure"),
        RuntimeError("40P01"),
        RuntimeError("40001"),
        RuntimeError("unapproved SQLSTATE"),
    ],
)
async def test_plan_05_does_not_retry_unapproved_failures(
    error: BaseException,
) -> None:
    created: list[_FakeUow] = []

    def factory() -> _FakeUow:
        value = _FakeUow(len(created) + 1)
        created.append(value)
        return value

    async def attempt(uow: object, number: int) -> None:
        del uow, number
        raise error

    typed_attempt = cast(Callable[[object, int], Awaitable[None]], attempt)
    with pytest.raises(type(error)):
        await run_semantic_uow_attempts(factory, typed_attempt)
    assert len(created) == 1


@pytest.mark.asyncio
async def test_plan_06_gate_and_phase_discipline() -> None:
    class PhaseConnection:
        def __init__(self) -> None:
            self.info: dict[str, object] = {}

        async def execute(self, statement: object) -> None:
            del statement

    connection = cast(AsyncConnection, cast(object, PhaseConnection()))
    plan = LockPlan(
        gate=AdvisoryGate.MODEL_ROOT_DELETE_GATE,
        intents=(_intent(RowLockClass.DATA_TYPE_HEADER, 1, RowLockMode.U),),
    )
    assert len(AdvisoryGate) == 3
    assert plan.gate is AdvisoryGate.MODEL_ROOT_DELETE_GATE
    plan.begin_acquisition(connection)
    with pytest.raises(LockPlanPhaseError):
        plan.begin_acquisition()
    plan.finish_acquisition()
    plan.begin_dml()
    with pytest.raises(LockPlanPhaseError):
        plan.begin_acquisition()
    with pytest.raises(LockPlanPhaseError):
        LockPlan().begin_acquisition(connection)
    with pytest.raises(LockPlanPhaseError):
        await acquire_advisory_gate(
            connection, AdvisoryGate.RELATIONSHIP_DEFINITION_CONFLICT_GATE
        )
    with pytest.raises(LockPlanPhaseError):
        await acquire_lock_plan(connection, LockPlan())


@pytest.mark.asyncio
async def test_plan_06_gate_precedes_every_row_statement() -> None:
    class Result:
        @staticmethod
        def first() -> tuple[int]:
            return (1,)

    class RecordingConnection:
        def __init__(self) -> None:
            self.info: dict[str, object] = {}
            self.statements: list[str] = []

        async def execute(self, statement: object) -> Result:
            self.statements.append(str(statement))
            return Result()

    raw_connection = RecordingConnection()
    connection = cast(AsyncConnection, cast(object, raw_connection))
    plan = LockPlan(
        gate=AdvisoryGate.MODEL_ROOT_DELETE_GATE,
        intents=(_intent(RowLockClass.DATA_TYPE_HEADER, 1, RowLockMode.U),),
    )
    assert await acquire_lock_plan(connection, plan) == ()
    assert "pg_advisory_xact_lock" in raw_connection.statements[0]
    assert "FROM datatypes" in raw_connection.statements[1]
    assert len(raw_connection.statements) == 2


def test_object_template_declaration_delta_preserves_unchanged_rows() -> None:
    datatype_id = _uuid(30)
    unchanged = LocalProperty("same", 1, datatype_id, 1, ValueMode.SCALAR, False, None)
    first = LocalProperty("a", 2, datatype_id, 1, ValueMode.SCALAR, False, None)
    second = LocalProperty("b", 3, datatype_id, 1, ValueMode.SCALAR, False, None)
    removed = LocalComponent("removed", 1, _uuid(40))
    added = LocalComponent("added", 1, _uuid(41))
    delta = declaration_delta(
        (unchanged, first, second),
        (removed,),
        (
            unchanged,
            LocalProperty("a", 3, datatype_id, 1, ValueMode.SCALAR, False, None),
            LocalProperty("b", 2, datatype_id, 1, ValueMode.SCALAR, False, None),
        ),
        (added,),
    )
    assert delta.property_deletes == ("a", "b")
    assert tuple(item.name for item in delta.property_inserts) == ("a", "b")
    assert delta.component_deletes == ("removed",)
    assert delta.component_inserts == (added,)
    assert "same" not in delta.property_deletes
    assert all(item.name != "same" for item in delta.property_inserts)
