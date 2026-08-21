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
