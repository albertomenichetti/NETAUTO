"""Machine-checkable M3 traceability, census, and non-drift closure."""

import ast
import hashlib
import inspect
import subprocess
import sys
import textwrap
import tomllib
from collections import Counter
from collections.abc import Callable
from functools import cache
from pathlib import Path
from typing import cast

from netauto.application.datatypes import DataTypeService
from netauto.application.objects import ObjectService
from netauto.application.objecttemplates import ObjectTemplateService
from netauto.application.relationshipdefinitions import RelationshipDefinitionService
from netauto.application.relationships import RelationshipService
from netauto.cli.registry import BUSINESS_OPERATION_SET, COMMAND_REGISTRY
from netauto.entrypoints.http import build_app
from netauto.persistence.metadata import metadata
from netauto.settings import Settings
from tests.support.m3_evidence import (
    M3_ACCEPTANCE_CRITERIA,
    M3_ACCEPTANCE_TO_EVIDENCE,
    M3_CLI_201_CENSUS,
    M3_CONTRACT_QUALITY_GATE_TO_OWNERS,
    M3_CONTRACT_QUALITY_GATES,
    M3_CURSOR_ROUTE_CENSUS,
    M3_EVIDENCE_BUNDLES,
    M3_EVIDENCE_TO_ARCHITECTURE_OWNER,
    M3_EVIDENCE_TO_TARGETS,
    M3_GET_ROUTE_CENSUS,
    M3_OUTCOME_TO_ACCEPTANCE,
    M3_OUTCOMES,
)

ROOT = Path(__file__).parents[1]
M3_ROOT = ROOT / "docs/milestones/M3"


def _blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


@cache
def _collected_test_nodes() -> frozenset[str]:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "tests"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return frozenset(
        line.strip()
        for line in result.stdout.splitlines()
        if line.startswith("tests/") and "::test_" in line
    )


def _target_is_collected(target: str, collected: frozenset[str]) -> bool:
    return target in collected or any(
        node.startswith(f"{target}[") for node in collected
    )


def test_m3_frozen_identifier_and_owner_registries_are_exact() -> None:
    assert M3_OUTCOMES == frozenset(f"M3-OUT-{number:02d}" for number in range(1, 9))
    assert M3_ACCEPTANCE_CRITERIA == frozenset(
        f"M3-AC-{number:02d}" for number in range(1, 20)
    )
    assert M3_EVIDENCE_BUNDLES == frozenset(
        f"M3-VER-{number:02d}" for number in range(1, 20)
    )
    assert set(M3_OUTCOME_TO_ACCEPTANCE) == M3_OUTCOMES
    assert all(M3_OUTCOME_TO_ACCEPTANCE.values())
    acceptance_counts = Counter(
        criterion
        for criteria in M3_OUTCOME_TO_ACCEPTANCE.values()
        for criterion in criteria
    )
    assert set(acceptance_counts) == M3_ACCEPTANCE_CRITERIA
    assert set(acceptance_counts.values()) == {1}
    assert M3_ACCEPTANCE_TO_EVIDENCE == {
        f"M3-AC-{number:02d}": f"M3-VER-{number:02d}" for number in range(1, 20)
    }
    assert set(M3_ACCEPTANCE_TO_EVIDENCE.values()) == M3_EVIDENCE_BUNDLES
    assert set(M3_EVIDENCE_TO_ARCHITECTURE_OWNER) == M3_EVIDENCE_BUNDLES
    assert set(M3_EVIDENCE_TO_TARGETS) == M3_EVIDENCE_BUNDLES
    assert all(M3_EVIDENCE_TO_ARCHITECTURE_OWNER.values())
    assert all(M3_EVIDENCE_TO_TARGETS.values())
    for owners in M3_EVIDENCE_TO_ARCHITECTURE_OWNER.values():
        for owner in owners:
            assert (ROOT / owner).is_file(), owner


def test_m3_route_cursor_and_cli_censuses_equal_live_authorities() -> None:
    expected_get_ids = {
        *(f"DT-GET-{number:02d}" for number in range(1, 5)),
        *(f"OT-GET-{number:02d}" for number in range(1, 7)),
        *(f"OBJ-GET-{number:02d}" for number in range(1, 7)),
        *(f"RD-GET-{number:02d}" for number in range(1, 5)),
        "REL-GET-01",
        "LC-GET-01",
    }
    assert set(M3_GET_ROUTE_CENSUS) == expected_get_ids
    assert len(M3_GET_ROUTE_CENSUS) == 22
    frozen_get_operations = frozenset(
        (route.method, route.path) for route in M3_GET_ROUTE_CENSUS.values()
    )
    assert len(frozen_get_operations) == 22
    assert frozen_get_operations == frozenset(
        operation for operation in BUSINESS_OPERATION_SET if operation[0] == "GET"
    )

    app = build_app(Settings(database_url="postgresql+psycopg://localhost/netauto"))
    openapi = cast(dict[str, object], app.openapi())
    paths = cast(dict[str, dict[str, object]], openapi["paths"])
    live_get_operations = frozenset(
        ("GET", path)
        for path, operations in paths.items()
        if path.startswith("/api/v1/core") and "get" in operations
    )
    assert live_get_operations == frozen_get_operations

    assert set(M3_CURSOR_ROUTE_CENSUS) == {
        "DT-GET-01",
        "DT-GET-03",
        "OT-GET-01",
        "OT-GET-03",
        "OT-GET-06",
        "OBJ-GET-01",
        "OBJ-GET-03",
        "OBJ-GET-05",
        "OBJ-GET-06",
        "RD-GET-01",
        "RD-GET-03",
        "LC-GET-01",
    }
    assert len(M3_CURSOR_ROUTE_CENSUS) == 12
    assert all(
        route.order in {"ASC", "DESC"} for route in M3_CURSOR_ROUTE_CENSUS.values()
    )
    assert all(route.position for route in M3_CURSOR_ROUTE_CENSUS.values())
    assert all(
        "limit" not in route.filters for route in M3_CURSOR_ROUTE_CENSUS.values()
    )

    live_cli_201 = frozenset(
        (key.resource, key.operation)
        for key, spec in COMMAND_REGISTRY.items()
        if spec.expected_status == 201
    )
    assert live_cli_201 == M3_CLI_201_CENSUS
    assert len(live_cli_201) == 8
    assert all(
        spec.location_template is not None
        for spec in COMMAND_REGISTRY.values()
        if spec.expected_status == 201
    )


def test_m3_evidence_targets_exist_and_are_collected() -> None:
    collected = _collected_test_nodes()
    for bundle, targets in M3_EVIDENCE_TO_TARGETS.items():
        assert targets, bundle
        for target in targets:
            path_text, separator, test_name = target.partition("::")
            assert separator and test_name.startswith("test_"), target
            path = ROOT / path_text
            assert path.is_file(), target
            function_name = test_name.partition("[")[0]
            tree = ast.parse(path.read_text(), filename=str(path))
            functions = {
                node.name
                for node in tree.body
                if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
                and node.name.startswith("test_")
            }
            assert function_name in functions, target
            assert _target_is_collected(target, collected), target


def test_m3_contract_quality_gates_and_normative_state_are_closed() -> None:
    assert M3_CONTRACT_QUALITY_GATES == frozenset(
        f"M3-CQG-{number:02d}" for number in range(1, 9)
    )
    assert set(M3_CONTRACT_QUALITY_GATE_TO_OWNERS) == M3_CONTRACT_QUALITY_GATES
    contract = (M3_ROOT / "contract.md").read_text()
    architecture_control = (M3_ROOT / "architecture/README.md").read_text()
    steps = (M3_ROOT / "steps.md").read_text()
    status = (M3_ROOT / "status.md").read_text()
    for gate, owners in M3_CONTRACT_QUALITY_GATE_TO_OWNERS.items():
        assert gate in contract
        assert owners
        assert all((ROOT / owner).is_file() for owner in owners)
    assert "**Status:** FINAL / FROZEN" in contract
    assert (
        "The frozen contract contains no TBD, TODO, unresolved candidate or open "
        "semantic point."
    ) in contract
    assert "**Architecture set status:** FINAL / FROZEN" in architecture_control
    assert "open design points          0 / 8" in architecture_control
    assert "open architecture findings 0" in architecture_control
    assert "**Status:** FINAL / FROZEN" in steps
    assert "blockers                 none" in status
    assert "software implementation  AUTHORIZED — M3-S06 ONLY" in status
    assert "M3-S07" in status and "NOT AUTHORIZED" in status
    assert "PARTIALLY REOPENED" not in architecture_control
    assert "open contract findings   0" in status
    assert "open architecture finding 0" in status
    assert "contract reopening       NOT REQUIRED" in status
    active_prompts = {
        path.name for path in (M3_ROOT / "wip").glob("M3-S*-codex-prompt.md")
    }
    assert active_prompts == {"M3-S06-codex-prompt.md"}


def test_m3_ver_06_all_get_services_have_no_mutation_certification_dependencies() -> (
    None
):
    methods: tuple[Callable[..., object], ...] = (
        DataTypeService.list_lineages,
        DataTypeService.get_lineage,
        DataTypeService.list_versions,
        DataTypeService.get_version,
        ObjectTemplateService.list_lineages,
        ObjectTemplateService.get_lineage,
        ObjectTemplateService.list_versions,
        ObjectTemplateService.get_version,
        ObjectTemplateService.get_effective_schema,
        RelationshipDefinitionService.list_capabilities,
        ObjectService.list_objects,
        ObjectService.get,
        ObjectService.list_components,
        ObjectService.get_owner,
        ObjectService.list_object_events,
        RelationshipService.list_for_object,
        RelationshipDefinitionService.list_definitions,
        RelationshipDefinitionService.get,
        RelationshipDefinitionService.list_versions,
        RelationshipDefinitionService.get_version,
        RelationshipService.get,
        ObjectService.list_events,
    )
    forbidden_calls = {
        "_relationship_schema",
        "_relationship_specs",
        "_schema_specs",
        "_validate_default_pointers",
        "_validate_persisted",
        "_validate_persisted_object",
        "_validated",
        "_validated_many",
        "canonicalize_constraints",
        "canonicalize_properties",
        "coherent_read",
        "resolve_exact_effective_schema",
        "validate_definition",
        "validate_relationship",
        "validate_relationship_definition_version",
        "validate_relationship_property_history",
    }
    assert len(methods) == len(M3_GET_ROUTE_CENSUS) == 22
    for method in methods:
        source = textwrap.dedent(inspect.getsource(method))
        tree = ast.parse(source)
        called = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        } | {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        assert called.isdisjoint(forbidden_calls), method.__qualname__
        assert "coherent_read" not in source, method.__qualname__


def test_m3_ver_17_static_non_drift_baselines_are_exact() -> None:
    pyproject_path = ROOT / "pyproject.toml"
    lock_path = ROOT / "uv.lock"
    migration_dir = ROOT / "src/netauto/migrations/versions"
    migration_path = migration_dir / "0001_m2_durable_kernel.py"
    assert _blob_sha(pyproject_path) == "d20bbb94739a74ebfb0bd27291b6e4f130d24c5f"
    assert _blob_sha(lock_path) == "0aa980926fda5f42ee3a7d3cedc64f9fcf8c2d23"
    assert _blob_sha(migration_path) == "27fc85e0b4411332fce87c406b6216b35db6eb20"
    assert {path.name for path in migration_dir.iterdir() if path.is_file()} == {
        "__init__.py",
        "0001_m2_durable_kernel.py",
    }

    project = tomllib.loads(pyproject_path.read_text())["project"]
    assert project["version"] == "0.2.0"
    assert project["requires-python"] == ">=3.14,<3.15"
    assert project["dependencies"] == [
        "alembic>=1.16,<2",
        "fastapi>=0.116,<1",
        "httpx>=0.28,<1",
        "prompt-toolkit>=3.0,<4",
        "psycopg[binary]>=3.2,<4",
        "pydantic>=2.11,<3",
        "pydantic-settings>=2.10,<3",
        "sqlalchemy[asyncio]>=2.0,<3",
        "uvicorn>=0.35,<1",
    ]

    migration_tree = ast.parse(migration_path.read_text(), filename=str(migration_path))
    assignments = {
        target.id: node.value
        for node in migration_tree.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
        for target in (node.target,)
    }
    revision = assignments["revision"]
    down_revision = assignments["down_revision"]
    assert isinstance(revision, ast.Constant) and revision.value == "0001_m2_kernel"
    assert isinstance(down_revision, ast.Constant) and down_revision.value is None
    assert len(metadata.tables) == 15
