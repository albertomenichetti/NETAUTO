"""M2-S08 finite positive/negative surface and authority closure."""

import ast
import re
import subprocess
from collections import deque
from pathlib import Path
from typing import cast

from netauto.cli.registry import BUSINESS_OPERATION_SET, COMMAND_REGISTRY
from netauto.cli.repl import LOCAL_COMMAND_REGISTRY
from netauto.entrypoints.api.errors import PUBLIC_STATUS_BY_CODE
from netauto.entrypoints.http import build_app
from netauto.persistence.metadata import metadata
from netauto.settings import Settings
from tests.test_m2_traceability import (
    CLI_REMOTE_OPERATION_COVERAGE,
    HEALTH_LOCAL_COMMAND_COVERAGE,
    M2_NEGATIVE_SURFACE_CONTRACT,
    M2_NEGATIVE_SURFACE_TO_TARGETS,
    PUBLIC_HTTP_OPERATIONS,
)
from tests.test_migrations import FORBIDDEN_INDEXES
from tests.test_schema_metadata import EXPECTED_TABLES

ROOT = Path(__file__).parents[1]
CONTRACT = ROOT / "docs/milestones/M2/contract.md"

_NON_GOAL_HEADINGS = {
    "relationship_model": "Relationship model non-goals",
    "lifecycle_history": "Lifecycle non-goals",
    "api_protocol": "API and protocol non-goals",
    "security_network": "Security and network non-goals",
    "deployment_platform": "Deployment and platform non-goals",
    "data_protection": "Data-protection non-goals",
    "observability": "Observability non-goals",
    "cli": "CLI non-goals",
    "health": "Health non-goals",
    "alembic": "Alembic non-goals",
}


def _mapping(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    raw = cast(dict[object, object], value)
    assert all(isinstance(key, str) for key in raw)
    return cast(dict[str, object], raw)


def _fenced_non_goals(text: str, heading: str) -> frozenset[str]:
    match = re.search(
        rf"^## {re.escape(heading)}\n(?P<section>.*?)(?=^## )",
        text,
        re.MULTILINE | re.DOTALL,
    )
    assert match is not None, heading
    fences = re.findall(r"```text\n(.*?)\n```", match.group("section"), re.DOTALL)
    assert len(fences) == 1, heading
    return frozenset(line for line in fences[0].splitlines() if line)


def _openapi_operations() -> tuple[dict[str, object], frozenset[tuple[str, str]]]:
    app = build_app(
        Settings(database_url="postgresql+psycopg://unused@example.test/netauto")
    )
    document = _mapping(app.openapi())
    paths = _mapping(document["paths"])
    operations = frozenset(
        (method.upper(), path)
        for path, value in paths.items()
        for method in _mapping(value)
        if method.upper() in {"GET", "POST", "DELETE", "PUT", "PATCH"}
    )
    return document, operations


def test_contract_non_goal_registry_matches_frozen_contract() -> None:
    text = CONTRACT.read_text()
    contract_categories = {
        *_NON_GOAL_HEADINGS,
        "performance_availability",
    }
    assert contract_categories < set(M2_NEGATIVE_SURFACE_CONTRACT)
    for category, heading in _NON_GOAL_HEADINGS.items():
        expected = _fenced_non_goals(text, heading)
        if category == "cli":
            assert "Persistent history across CLI process restarts" in text
            expected |= {"persistent history across CLI process restarts"}
        assert expected == M2_NEGATIVE_SURFACE_CONTRACT[category]
    performance = next(iter(M2_NEGATIVE_SURFACE_CONTRACT["performance_availability"]))
    assert f"M2 defines no {performance}." in text

    flattened = [
        entry for entries in M2_NEGATIVE_SURFACE_CONTRACT.values() for entry in entries
    ]
    assert len(flattened) == len(set(flattened))
    assert set(M2_NEGATIVE_SURFACE_TO_TARGETS) == {
        f"{category}::{entry}"
        for category, entries in M2_NEGATIVE_SURFACE_CONTRACT.items()
        for entry in entries
    }
    assert all(M2_NEGATIVE_SURFACE_TO_TARGETS.values())


def test_relationship_model_non_goals_and_finite_public_surface() -> None:
    all_columns = {
        column.name for table in metadata.tables.values() for column in table.columns
    }
    assert (
        not {
            "event_set_id",
            "transition_id",
            "relationship_definition_version_id",
            "relationship_definition_property_id",
            "runtime_relationship_resolution_id",
        }
        & all_columns
    )
    assert not {
        "relationship_property_values",
        "relationship_effective_schemas",
        "relationship_schema_cache",
        "relationship_timeline",
    } & set(metadata.tables)
    document, operations = _openapi_operations()
    assert operations == PUBLIC_HTTP_OPERATIONS
    paths = set(_mapping(document["paths"]))
    forbidden = {
        "relationship-resolutions",
        "property-declarations",
        "runtime-relationship-resolutions",
        "property-values",
        "json-schema",
    }
    assert all(fragment not in path for path in paths for fragment in forbidden)


def test_lifecycle_and_history_non_goals_are_absent() -> None:
    assert "object_lifecycle_events" in metadata.tables
    assert not {
        "relationship_lifecycle_events",
        "relationship_timelines",
        "event_sets",
        "transitions",
    } & set(metadata.tables)
    lifecycle = metadata.tables["object_lifecycle_events"]
    assert "event_set_id" not in lifecycle.c
    assert "transition_id" not in lifecycle.c
    assert "before_state" in lifecycle.c
    assert "after_state" in lifecycle.c
    _, operations = _openapi_operations()
    assert not any(
        fragment in path
        for _, path in operations
        for fragment in ("/event-sets", "/transitions", "/relationship-timeline")
    )


def test_public_http_inventory_error_catalog_and_forbidden_surface_are_exact() -> None:
    document, operations = _openapi_operations()
    assert operations == PUBLIC_HTTP_OPERATIONS
    assert len(BUSINESS_OPERATION_SET) == 63
    assert len(operations) == 64
    assert (
        sum(
            method != "GET"
            for method, path in operations
            if path.startswith("/api/v1/core")
        )
        == 41
    )
    assert (
        sum(
            method == "GET"
            for method, path in operations
            if path.startswith("/api/v1/core")
        )
        == 22
    )
    assert {item for item in operations if not item[1].startswith("/api/v1/core")} == {
        ("GET", "/health/core")
    }
    assert len(PUBLIC_STATUS_BY_CODE) == 23
    assert not any(method in {"PUT", "PATCH"} for method, _ in operations)

    paths = set(_mapping(document["paths"]))
    forbidden_fragments = {
        "/actions",
        "/batch",
        "/bulk",
        "/auth",
        "/login",
        "/logout",
        "/tokens",
        "/accounts",
        "/roles",
        "/schema-migration",
    }
    assert "/health" not in paths
    assert all(
        fragment not in path for fragment in forbidden_fragments for path in paths
    )


def _imports(path: Path) -> frozenset[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.add(node.module)
            if node.module.startswith("netauto"):
                imports.update(
                    f"{node.module}.{alias.name}"
                    for alias in node.names
                    if alias.name != "*"
                )
    return frozenset(imports)


def _module_path(module: str) -> Path | None:
    relative = Path("src") / Path(*module.split("."))
    package = ROOT / relative / "__init__.py"
    source = (ROOT / relative).with_suffix(".py")
    if package.is_file():
        return package
    if source.is_file():
        return source
    return None


def test_cli_operation_coverage_import_closure_and_negative_surface_are_exact() -> None:
    assert len(COMMAND_REGISTRY) == 63
    assert CLI_REMOTE_OPERATION_COVERAGE == BUSINESS_OPERATION_SET
    assert len(CLI_REMOTE_OPERATION_COVERAGE) == 63
    assert len({spec.key for spec in COMMAND_REGISTRY.values()}) == 63
    assert (
        len({(spec.method, spec.path_template) for spec in COMMAND_REGISTRY.values()})
        == 63
    )
    assert tuple(LOCAL_COMMAND_REGISTRY) == (
        "connect",
        "disconnect",
        "status",
        "output",
        "help",
        "history",
        "clear",
        "exit",
    )
    assert HEALTH_LOCAL_COMMAND_COVERAGE == {"/connect", "/status"}
    assert {
        LOCAL_COMMAND_REGISTRY[name].usage.split()[0] for name in ("connect", "status")
    } == HEALTH_LOCAL_COMMAND_COVERAGE
    assert sum(len(spec.examples) for spec in COMMAND_REGISTRY.values()) == 65
    assert not any(
        spec.path_template == "/health/core" for spec in COMMAND_REGISTRY.values()
    )

    queue = deque(sorted((ROOT / "src/netauto/cli").glob("*.py")))
    visited: set[Path] = set()
    forbidden = (
        "netauto.application",
        "netauto.persistence",
        "netauto.entrypoints",
        "netauto.runtime",
    )
    while queue:
        path = queue.popleft()
        if path in visited:
            continue
        visited.add(path)
        imports = _imports(path)
        assert not any(
            module == prefix or module.startswith(prefix + ".")
            for module in imports
            for prefix in (*forbidden, "sqlalchemy", "psycopg", "alembic")
        ), path
        for module in imports:
            if not module.startswith("netauto"):
                continue
            child = _module_path(module)
            if child is not None and child not in visited:
                queue.append(child)
    assert all(
        path.is_relative_to(ROOT / "src/netauto/cli")
        or path.is_relative_to(ROOT / "src/netauto/transport/http")
        or path
        in {
            ROOT / "src/netauto/domain/datatypes.py",
            ROOT / "src/netauto/domain/objecttemplates.py",
            ROOT / "src/netauto/domain/primitives.py",
            ROOT / "src/netauto/health.py",
        }
        for path in visited
    )

    source = "\n".join(path.read_text() for path in visited)
    for forbidden_text in (
        "--insecure",
        "--skip-verify",
        "verify=False",
        "Authorization",
        "CookieJar",
        "retry(",
        "persistent_history",
        "credential_store",
        "profile_store",
    ):
        assert forbidden_text not in source


def test_schema_alembic_and_automatic_migration_surfaces_are_exact() -> None:
    assert set(metadata.tables) == EXPECTED_TABLES
    assert len(EXPECTED_TABLES) == 15
    explicit_indexes = {
        str(index.name) for table in metadata.tables.values() for index in table.indexes
    }
    assert FORBIDDEN_INDEXES.isdisjoint(explicit_indexes)
    all_names = set(metadata.tables) | {
        column.name for table in metadata.tables.values() for column in table.columns
    }
    for forbidden in (
        "effective_schema_cache",
        "compiled_schema",
        "reverse_dependencies",
        "property_value",
        "event_set_id",
    ):
        assert forbidden not in all_names

    version_files = sorted(
        path
        for path in (ROOT / "src/netauto/migrations/versions").glob("*.py")
        if path.name != "__init__.py"
    )
    assert [path.name for path in version_files] == ["0001_m2_durable_kernel.py"]
    migration = ast.parse(version_files[0].read_text())
    assignments = {
        node.target.id: ast.literal_eval(node.value)
        for node in migration.body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id in {"revision", "down_revision"}
        and node.value is not None
    }
    assert assignments == {"revision": "0001_m2_kernel", "down_revision": None}

    automatic_migration_roots = {
        ROOT / "src/netauto/entrypoints/http.py",
        ROOT / "src/netauto/runtime/schema_guard.py",
        *sorted((ROOT / "src/netauto/cli").glob("*.py")),
    }
    migration_calls = {"upgrade", "downgrade", "stamp", "revision", "merge"}
    for path in automatic_migration_roots:
        tree = ast.parse(path.read_text(), filename=str(path))
        aliases: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "alembic.command":
                aliases.update(alias.asname or alias.name for alias in node.names)
            elif isinstance(node, ast.Import):
                aliases.update(
                    alias.asname or alias.name
                    for alias in node.names
                    if alias.name == "alembic.command"
                )
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name):
                assert node.func.id not in aliases & migration_calls, path
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in migration_calls, path


def test_security_transport_and_secret_surfaces_remain_external() -> None:
    document, operations = _openapi_operations()
    assert "securitySchemes" not in repr(document)
    assert not any(
        fragment in path
        for _, path in operations
        for fragment in ("auth", "login", "logout", "token", "account", "role")
    )
    assert "401" not in repr(document) and "403" not in repr(document)
    settings = set(Settings.model_fields)
    assert settings == {
        "database_url",
        "log_level",
        "pool_size",
        "max_overflow",
        "pool_timeout",
        "pool_recycle",
        "pool_pre_ping",
    }
    assert not any(
        fragment in field
        for field in settings
        for fragment in ("certificate", "private_key", "credential", "password", "tls")
    )


def test_runtime_deployment_data_protection_and_performance_surfaces_are_absent() -> (
    None
):
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    repository_files = {line.lower() for line in result.stdout.splitlines() if line}
    forbidden_names = {
        "dockerfile",
        "docker-compose.yml",
        "compose.yml",
        "deployment.yaml",
        "statefulset.yaml",
        "netauto.service",
        "backup.sh",
        "restore.sh",
        ".gitlab-ci.yml",
    }
    assert not (repository_files & forbidden_names)
    assert not any(
        path.startswith(("k8s/", "kubernetes/", "helm/", ".github/workflows/"))
        for path in repository_files
    )
    pyproject = (ROOT / "pyproject.toml").read_text()
    assert "gunicorn" not in pyproject.lower()
    assert "prometheus" not in pyproject.lower()
    assert "opentelemetry" not in pyproject.lower()


def test_observability_and_health_non_goals_are_absent() -> None:
    document, operations = _openapi_operations()
    assert {item for item in operations if item[1].startswith("/health")} == {
        ("GET", "/health/core")
    }
    schemas = _mapping(_mapping(document["components"])["schemas"])
    health_schema = repr(
        {
            name: schemas[name]
            for name in ("ComponentHealthDTO", "CoreHealthDTO", "HealthStatus")
        }
    )
    for forbidden in (
        "degraded",
        "warning",
        "prometheus",
        "metric",
        "revision",
        "diagnostics",
    ):
        assert forbidden not in health_schema.lower()
    source = "\n".join(
        (ROOT / relative).read_text()
        for relative in (
            "src/netauto/health.py",
            "src/netauto/application/health.py",
            "src/netauto/persistence/health.py",
            "src/netauto/entrypoints/api/health.py",
        )
    )
    assert "MigrationContext" not in source
    assert "alembic" not in source.lower()
    assert "retry" not in source.lower()


def test_wip_provenance_is_complete_and_never_implementation_authority() -> None:
    production = "\n".join(
        path.read_text() for path in sorted((ROOT / "src").rglob("*.py"))
    )
    assert "docs/milestones/M2/wip" not in production
    assert "M2-S08-codex-prompt" not in production

    for path in sorted((ROOT / "tests").rglob("*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        literals = {
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        }
        assert not any(
            "docs/milestones/M2/wip/" in value and "prompt" in value.lower()
            for value in literals
        ), path

    provenance = (ROOT / "docs/milestones/M2/architecture/provenance.md").read_text()
    rows = re.findall(r"^\| `([^`]+\.md)` \|", provenance, re.MULTILINE)
    assert len(rows) == 19
    assert len(set(rows)) == 19
    assert "classified                        19 / 19" in provenance
    assert "unclassified                       0" in provenance
    assert "implementation dependency on WIP              0" in provenance

    wip_files = {path.name for path in (ROOT / "docs/milestones/M2/wip").glob("*.md")}
    permitted_non_disposition_files = {
        "M2-S08-codex-prompt.md",
        "steps-consistency-closure.md",
        "wip-extraction-closure.md",
    }
    assert wip_files == set(rows) | permitted_non_disposition_files

    normative = {
        ROOT / "docs/milestones/M2/contract.md",
        ROOT / "docs/milestones/M2/steps.md",
        ROOT / "docs/milestones/M2/status.md",
        *sorted((ROOT / "docs/milestones/M2/architecture").glob("*.md")),
    }
    allowed_context = re.compile(
        r"non-normative|historical|discovery|supersed|review record|audit record|"
        r"consistency closure|freeze approval|retir|captured for ratification|"
        r"must\s+\W*not|execution aid",
        re.IGNORECASE,
    )
    for path in normative:
        lines = path.read_text().splitlines()
        for number, line in enumerate(lines, 1):
            if "wip/" in line:
                context = " ".join(lines[max(0, number - 9) : number + 1])
                assert allowed_context.search(context), f"{path}:{number}: {line}"


def test_normative_corpus_has_no_unresolved_placeholder_or_reopen() -> None:
    corpus = {
        *sorted((ROOT / "docs/architecture").glob("*.md")),
        ROOT / "docs/milestones/M2/contract.md",
        *sorted((ROOT / "docs/milestones/M2/architecture").glob("*.md")),
        ROOT / "docs/general/technology_baseline.md",
    }
    placeholder = re.compile(
        r"TBD|TODO|FIXME|OPEN QUESTION|unresolved candidate|open design|"
        r"open contract|PARTIALLY REOPENED",
        re.IGNORECASE,
    )
    allowed_context = re.compile(
        r"contains no TBD, TODO, unresolved candidate or open contract point|"
        r"^## Open contract points$|Open contract points\s+0|"
        r"no relevant open, contradictory or partially reopened|"
        r"no unresolved normative TBD/TODO/open point|"
        r"no normative TBD/TODO/open contract point",
        re.IGNORECASE,
    )
    findings: list[str] = []
    for path in corpus:
        for number, line in enumerate(path.read_text().splitlines(), 1):
            if placeholder.search(line) and not allowed_context.search(line):
                findings.append(f"{path.relative_to(ROOT)}:{number}: {line}")
    assert findings == []

    contract = CONTRACT.read_text()
    architecture = (ROOT / "docs/milestones/M2/architecture/README.md").read_text()
    assert "## Open contract points\n\nNone." in contract
    assert "no relevant open, contradictory or partially reopened" in architecture
    assert architecture.startswith(
        "# M2 Architecture\n\n**Architecture set status:** FINAL / FROZEN"
    )
