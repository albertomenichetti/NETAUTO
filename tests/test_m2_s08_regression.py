"""M2-S08 exact current AS-IS and historical-delta closure."""

import ast
import re
from pathlib import Path

from netauto.cli.registry import BUSINESS_OPERATION_SET
from netauto.entrypoints.api.errors import PUBLIC_STATUS_BY_CODE
from netauto.persistence.metadata import metadata
from tests.test_m1_traceability import PGTEST_SCENARIOS, SAFETY_PREDICATES
from tests.test_m2_traceability import (
    M2_AS_IS_GUARANTEE_TO_TARGETS,
    M2_CONCURRENCY_SCENARIOS,
    M2_DELIVERED_SCENARIO_DELTA_ALLOWLIST,
    M2_DELTA_ALLOWLIST,
    M2_MUTATIONS,
    M2_PREDICATE_TO_SCENARIOS,
    M2_PUBLIC_WIRE_DELTA_ALLOWLIST,
    M2_SCENARIO_TO_RECIPES,
    M2_SCENARIO_TO_TARGETS,
    M2_SCHEMA_RUNTIME_DELTA_ALLOWLIST,
    PUBLIC_HTTP_OPERATIONS,
    S01_PUBLIC_ROUTE_DELTA,
    S02_PUBLIC_ROUTE_DELTA,
    S04_PUBLIC_ROUTE_DELTA,
    assert_target_exists,
)
from tests.test_schema_metadata import EXPECTED_TABLES

ROOT = Path(__file__).parents[1]


def _documented_business_operations(relative: str) -> frozenset[tuple[str, str]]:
    text = (ROOT / relative).read_text()
    return frozenset(
        re.findall(r"^(GET|POST|DELETE)\s+(/api/v1/core/\S+)$", text, re.MULTILINE)
    )


def _normalized_operations(
    operations: frozenset[tuple[str, str]],
) -> frozenset[tuple[str, str]]:
    return frozenset(
        (method, re.sub(r"\{[^{}]+\}", "{}", path)) for method, path in operations
    )


def _documented_table_inventory(relative: str) -> frozenset[str]:
    text = (ROOT / relative).read_text()
    section = re.search(
        r"^## Authoritative table map\n(?P<body>.*?)^## Exact column inventory$",
        text,
        re.MULTILINE | re.DOTALL,
    )
    assert section is not None
    blocks = re.findall(r"```text\n(.*?)```", section.group("body"), re.DOTALL)
    return frozenset(
        line.strip()
        for block in blocks
        for line in block.splitlines()
        if re.fullmatch(r"[a-z][a-z0-9_]*", line.strip())
    )


def _migration_identity(path: Path) -> tuple[object, object]:
    assignments: dict[str, object] = {}
    for node in ast.parse(path.read_text(), filename=str(path)).body:
        if not isinstance(node, ast.AnnAssign):
            continue
        if not isinstance(node.target, ast.Name) or node.value is None:
            continue
        if node.target.id in {"revision", "down_revision"}:
            assignments[node.target.id] = ast.literal_eval(node.value)
    return assignments["revision"], assignments["down_revision"]


def _documented_row_class_order(relative: str) -> tuple[tuple[int, str], ...]:
    text = (ROOT / relative).read_text()
    match = re.search(
        r"^Every plan uses this exact global row-class order:\n\n"
        r"```text\n(?P<body>.*?)```",
        text,
        re.MULTILINE | re.DOTALL,
    )
    assert match is not None
    entries: list[tuple[int, str]] = []
    for line in match.group("body").splitlines():
        entry = re.fullmatch(r"(\d+)  (.+)", line)
        assert entry is not None
        entries.append((int(entry.group(1)), entry.group(2)))
    return tuple(entries)


def _documented_lock_plan_registry(
    relative: str,
) -> dict[str, tuple[str, str, str, str]]:
    text = (ROOT / relative).read_text()
    section = re.search(
        r"^## Complete initial lock-plan registry\n(?P<body>.*?)"
        r"^## Versioned model realization$",
        text,
        re.MULTILINE | re.DOTALL,
    )
    assert section is not None
    plans: dict[str, tuple[str, str, str, str]] = {}
    for line in section.group("body").splitlines():
        if not line.startswith("| `"):
            continue
        cells = tuple(cell.strip() for cell in line.strip("|").split("|"))
        assert len(cells) == 5
        mutation = cells[0].removeprefix("`").removesuffix("`")
        assert mutation not in plans
        plans[mutation] = (
            cells[1].removeprefix("`").removesuffix("`"),
            cells[2],
            cells[3],
            cells[4],
        )
    return plans


def _documented_reusable_target_intents(relative: str) -> tuple[str, ...]:
    text = (ROOT / relative).read_text()
    match = re.search(
        r"Dependency targets\nfollow these reusable initial intents:\n\n"
        r"```text\n(?P<body>.*?)```",
        text,
        re.DOTALL,
    )
    assert match is not None
    return tuple(line.rstrip() for line in match.group("body").splitlines())


def test_all_preserved_guarantees_have_concrete_collected_targets() -> None:
    expected = {
        "stable RelationshipDefinition topology and symmetry",
        "RelationshipResolution identity, membership and endpoint lineages",
        "mutable Resolution name as non-key metadata",
        "Definition equivalence and cross-Definition Resolution conflict semantics",
        "Relationship factual identity",
        "symmetric/non-symmetric factual uniqueness",
        "self-loop support",
        "exact runtime-view identity",
        "complete deterministic runtime-resolution closure",
        "Object stable-lineage endpoint admission",
        "Object and RelationshipDefinition delete blockers",
        "Object-relative semantic-view deduplication",
        "/api/v1/core business namespace",
        "strict request bodies",
        "failure-class boundary",
        "bounded error details and no SQL/internal leakage",
        "opaque keyset pagination",
        "single-request coherent reads",
    }
    assert set(M2_AS_IS_GUARANTEE_TO_TARGETS) == expected
    assert len(M2_AS_IS_GUARANTEE_TO_TARGETS) == 18
    for guarantee, targets in M2_AS_IS_GUARANTEE_TO_TARGETS.items():
        assert targets, guarantee
        assert all("::test_" in target for target in targets)
        for target in targets:
            assert_target_exists(target)


def test_delivered_scenario_targets_recipes_predicates_and_deltas_are_closed() -> None:
    delivered = frozenset(PGTEST_SCENARIOS)
    assert len(delivered) == 51
    assert delivered <= M2_CONCURRENCY_SCENARIOS
    assert set(M2_DELIVERED_SCENARIO_DELTA_ALLOWLIST) == {
        "ARB-05",
        "ARB-06",
        "ARB-07",
        "SNAP-01",
        "SNAP-02",
        "ATOMIC-02",
        "ATOMIC-03",
    }
    for scenario, original_targets in PGTEST_SCENARIOS.items():
        expected_targets = frozenset(
            f"{target.module}::{target.function}" for target in original_targets
        )
        assert expected_targets <= M2_SCENARIO_TO_TARGETS[scenario]
        assert M2_SCENARIO_TO_TARGETS[scenario]
        assert M2_SCENARIO_TO_RECIPES[scenario].primary

    assert set(SAFETY_PREDICATES) == set(M2_PREDICATE_TO_SCENARIOS) - {"VH", "RS"}
    assert all(
        SAFETY_PREDICATES[predicate] <= M2_PREDICATE_TO_SCENARIOS[predicate]
        for predicate in SAFETY_PREDICATES
    )
    assert all(M2_PREDICATE_TO_SCENARIOS.values())


def test_m2_delta_allowlists_are_exact_and_closed() -> None:
    assert M2_DELTA_ALLOWLIST == {
        "RelationshipDefinition CREATE includes v1 DRAFT",
        "capability requires one PUBLISHED RDV",
        "Relationship CREATE request/projection adds exact pin and properties",
        "duplicate Relationship CREATE becomes relationship_fact_conflict",
        "missing Relationship DELETE becomes resource_not_found",
        "Relationship lifecycle adds before/after state and new change kinds",
        "startup requires exact shipped Alembic revision",
        "one fresh durable root baseline replaces disposable development history",
        "new Health, CLI, release and Linux-runtime surfaces",
    }
    assert len(M2_PUBLIC_WIRE_DELTA_ALLOWLIST) == 11
    assert len(M2_SCHEMA_RUNTIME_DELTA_ALLOWLIST) == 6
    assert len(M2_DELIVERED_SCENARIO_DELTA_ALLOWLIST) == 7

    contract = (ROOT / "docs/milestones/M2/contract.md").read_text()
    api = (ROOT / "docs/milestones/M2/architecture/api.md").read_text()
    assert (
        "No other observable divergence from the delivered AS-IS is authorized"
        in contract
    )
    assert "No additional observable divergence is authorized" in api
    for fragment in (
        "response becomes {relationship_definition, version}",
        "default_version added",
        "nested command/read routes and DTOs added",
        "409 relationship_fact_conflict replaces successful convergence",
        "404 replaces idempotent 204",
        "GET /health/core",
    ):
        assert fragment in api


def test_public_route_error_and_schema_runtime_deltas_are_exact() -> None:
    documented_current = _documented_business_operations("docs/architecture/api.md")
    frozen_m2 = _documented_business_operations(
        "docs/milestones/M2/architecture/api.md"
    )
    additions = S01_PUBLIC_ROUTE_DELTA | S02_PUBLIC_ROUTE_DELTA

    assert _normalized_operations(documented_current) == _normalized_operations(
        BUSINESS_OPERATION_SET
    )
    assert len(documented_current) == len(BUSINESS_OPERATION_SET) == 63
    assert _normalized_operations(frozen_m2) == _normalized_operations(
        BUSINESS_OPERATION_SET
    )
    assert len(frozen_m2) == 63
    assert len(S01_PUBLIC_ROUTE_DELTA) == 9
    assert len(S02_PUBLIC_ROUTE_DELTA) == 2
    assert len(additions) == 11
    assert S01_PUBLIC_ROUTE_DELTA.isdisjoint(S02_PUBLIC_ROUTE_DELTA)
    assert _normalized_operations(additions) <= _normalized_operations(
        BUSINESS_OPERATION_SET
    )
    assert S04_PUBLIC_ROUTE_DELTA == {("GET", "/health/core")}
    assert PUBLIC_HTTP_OPERATIONS == BUSINESS_OPERATION_SET | S04_PUBLIC_ROUTE_DELTA
    assert len(PUBLIC_HTTP_OPERATIONS) == 64
    assert len(PUBLIC_STATUS_BY_CODE) == 23

    documented_tables = _documented_table_inventory("docs/architecture/persistence.md")
    assert documented_tables == EXPECTED_TABLES
    assert len(documented_tables) == len(EXPECTED_TABLES) == 15
    assert set(metadata.tables) == EXPECTED_TABLES
    migration_paths = sorted(
        path
        for path in (ROOT / "src/netauto/migrations/versions").glob("*.py")
        if path.name != "__init__.py"
    )
    assert [path.name for path in migration_paths] == ["0001_m2_durable_kernel.py"]
    assert _migration_identity(migration_paths[0]) == ("0001_m2_kernel", None)

    concurrency_owner = "docs/architecture/concurrency.md"
    assert _documented_row_class_order(concurrency_owner) == (
        (10, "ObjectTemplate headers and exact versions"),
        (20, "DataType headers and exact versions"),
        (30, "RelationshipDefinition headers and exact versions"),
        (40, "Object rows"),
        (50, "factual Relationship rows"),
    )
    lock_plans = _documented_lock_plan_registry(concurrency_owner)
    assert set(lock_plans) == M2_MUTATIONS
    assert len(lock_plans) == 41
    allowed_gates = {
        "OWNERSHIP_GRAPH_WRITE_GATE",
        "RELATIONSHIP_DEFINITION_CONFLICT_GATE",
        "MODEL_ROOT_DELETE_GATE",
    }
    assert {gate for gate, *_ in lock_plans.values() if gate != "none"} == allowed_gates
    for mutation, (gate, row_plan, targets, boundary) in lock_plans.items():
        assert gate == "none" or gate in allowed_gates, mutation
        assert row_plan, mutation
        assert targets, mutation
        assert boundary, mutation
        documented_modes = set(re.findall(r"@([A-Za-z0-9_]+)", row_plan))
        assert documented_modes <= {"KS", "S", "NKU", "U"}, mutation

    assert _documented_reusable_target_intents(concurrency_owner) == (
        "explicit new or rebound exact dependency  target H@KS + target V@S",
        "implicit new or rebound exact dependency  target H@S  + target V@S",
        "same-pin physical reinsertion             target H@KS + target V@KS",
        "unchanged physical declaration/reference  no outgoing target lock",
        "removed declaration/reference             no outgoing target lock",
        "historical clone into a new physical row  target H@KS + target V@KS",
    )
    owner_text = (ROOT / concurrency_owner).read_text()
    assert "Every target named by the command" not in owner_text
    assert "retained/inserted targets" not in owner_text

    ot_revise_plan = lock_plans["OT.R"][1]
    for sentinel in (
        "unchanged parent: no target reacquisition",
        "changed explicit parent: `OT.H@KS + OT.V@S`",
        "changed implicit parent: `OT.H@S + OT.V@S`",
        "changed component target: `OT.H@KS`",
        "unchanged component target: no outgoing target lock",
        "removed component declaration: no outgoing target lock",
        "unchanged property declaration: no outgoing target lock",
        "removed property declaration: no outgoing target lock",
        "same-pin physical reinsertion: `DT.H@KS + DT.V@KS`",
        "explicit new/rebound property: `DT.H@KS + DT.V@S`",
        "implicit new/rebound property: `DT.H@S + DT.V@S`",
    ):
        assert sentinel in ot_revise_plan

    rd_revise_plan = lock_plans["RD.R"][1]
    for sentinel in (
        "unchanged property declaration: no outgoing target lock",
        "removed property declaration: no outgoing target lock",
        "same-pin physical reinsertion: `DT.H@KS + DT.V@KS`",
        "explicit new/rebound property: `DT.H@KS + DT.V@S`",
        "implicit new/rebound property: `DT.H@S + DT.V@S`",
    ):
        assert sentinel in rd_revise_plan
