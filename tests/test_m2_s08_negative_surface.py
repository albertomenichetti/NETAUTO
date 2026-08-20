"""M2-S08 finite positive/negative surface and authority closure."""

import ast
import re
import subprocess
import tomllib
from collections import deque
from pathlib import Path
from typing import cast

import pytest

from netauto.cli.registry import BUSINESS_OPERATION_SET, COMMAND_REGISTRY
from netauto.cli.repl import LOCAL_COMMAND_REGISTRY
from netauto.entrypoints.api.errors import PUBLIC_STATUS_BY_CODE
from netauto.entrypoints.http import build_app
from netauto.persistence.metadata import metadata
from netauto.settings import Settings
from tests.support.s08_static import (
    ABSTRACT_NEGATIVE_CAPABILITY_IDS,
    AlembicMutationFinding,
    existing_initializer_chain,
    find_abstract_capability_findings,
    find_reachable_alembic_mutations,
    forbidden_deployment_assets,
)
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


def test_negative_surface_mapping_is_entry_specific_and_semantically_owned() -> None:
    expected_keys = {
        f"{category}::{entry}"
        for category, entries in M2_NEGATIVE_SURFACE_CONTRACT.items()
        for entry in entries
    }
    assert set(M2_NEGATIVE_SURFACE_TO_TARGETS) == expected_keys
    assert len(set(M2_NEGATIVE_SURFACE_TO_TARGETS.values())) >= 50
    assert M2_NEGATIVE_SURFACE_TO_TARGETS[
        "cli::persistent history across CLI process restarts"
    ] == {"tests/test_m2_s06_process.py::test_repl_creates_no_persistent_history_file"}
    assert (
        "tests/test_relationship_semantic_concurrency.py::"
        "test_snap_01_delete_event_keeps_one_pre_rename_name_snapshot"
        in M2_NEGATIVE_SURFACE_TO_TARGETS[
            "lifecycle_history::retroactive historical metadata renaming"
        ]
    )
    assert (
        "tests/test_m2_s08_negative_surface.py::"
        "test_automatic_migration_analysis_follows_wrappers_and_allows_introspection"
        in M2_NEGATIVE_SURFACE_TO_TARGETS["alembic::automatic migration at startup"]
    )
    capability_targets = {
        "tests/test_m2_s08_negative_surface.py::"
        "test_abstract_negative_capability_audit_covers_real_repository_surfaces",
        "tests/test_m2_s08_negative_surface.py::"
        "test_abstract_negative_capability_audit_detects_synthetic_counterexamples",
    }
    for identifier in ABSTRACT_NEGATIVE_CAPABILITY_IDS:
        assert capability_targets <= M2_NEGATIVE_SURFACE_TO_TARGETS[identifier]


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
    production = "\n".join(
        path.read_text().lower()
        for path in sorted((ROOT / "src/netauto").rglob("*.py"))
    )
    for forbidden in (
        "compliance_ledger",
        "event_sourcing",
        "replay_current_state",
        "retention_policy",
        "archive_policy",
        "temporal_reconstruction",
    ):
        assert forbidden not in production


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
    assert not any(
        route.__class__.__name__ == "WebSocketRoute"
        for route in build_app(
            Settings(database_url="postgresql+psycopg://unused@example.test/netauto")
        ).routes
    )
    parameter_names: set[str] = set()
    response_codes: set[str] = set()
    for path_item in _mapping(document["paths"]).values():
        for operation in _mapping(path_item).values():
            operation_mapping = _mapping(operation)
            raw_parameters = operation_mapping.get("parameters", [])
            assert isinstance(raw_parameters, list)
            for parameter in cast(list[object], raw_parameters):
                parameter_names.add(str(_mapping(parameter).get("name", "")).lower())
            raw_responses = operation_mapping.get("responses", {})
            response_codes.update(_mapping(raw_responses))
    assert (
        not {
            "offset",
            "page",
            "page_number",
            "sort",
            "order",
            "include_total",
            "total_count",
            "idempotency-key",
            "if-match",
            "snapshot_token",
        }
        & parameter_names
    )
    assert not {"401", "403", "429"} & response_codes


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


def _production_module_sources() -> dict[str, str]:
    sources: dict[str, str] = {}
    for path in sorted((ROOT / "src/netauto").rglob("*.py")):
        relative = path.relative_to(ROOT / "src").with_suffix("")
        parts = relative.parts[:-1] if relative.name == "__init__" else relative.parts
        sources[".".join(parts)] = path.read_text()
    return sources


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
        "instance_discovery",
        "plugin_registry",
        "macro_language",
        "offline_mode",
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

    sources = _production_module_sources()
    execution_roots = {
        module
        for module in sources
        if module == "netauto.entrypoints.http"
        or module == "netauto.runtime"
        or module.startswith("netauto.runtime.")
        or module == "netauto.cli"
        or module.startswith("netauto.cli.")
    }
    assert "netauto.entrypoints.http" in execution_roots
    assert "netauto.runtime.schema_guard" in execution_roots
    assert "netauto.cli.main" in execution_roots
    assert find_reachable_alembic_mutations(sources, execution_roots) == ()


@pytest.mark.parametrize(
    ("import_statement", "invocation", "target"),
    [
        (
            "from alembic.command import upgrade as apply_head",
            "apply_head(None, 'head')",
            "alembic.command.upgrade",
        ),
        (
            "from alembic import command as operations",
            "operations.stamp(None, 'head')",
            "alembic.command.stamp",
        ),
        (
            "import alembic.command as operations",
            "operations.downgrade(None, 'base')",
            "alembic.command.downgrade",
        ),
    ],
)
def test_automatic_migration_analysis_resolves_import_aliases(
    import_statement: str, invocation: str, target: str
) -> None:
    findings = find_reachable_alembic_mutations(
        {
            "sample.runtime": f"{import_statement}\n\ndef start():\n    {invocation}\n",
        },
        {"sample.runtime"},
    )
    assert tuple(item.target for item in findings) == (target,)


def test_automatic_migration_analysis_follows_wrappers_and_allows_introspection() -> (
    None
):
    findings = find_reachable_alembic_mutations(
        {
            "sample.server": (
                "from sample.migration_adapter import apply\n\n"
                "async def lifespan():\n"
                "    apply()\n"
            ),
            "sample.migration_adapter": (
                "from alembic.command import upgrade as run_upgrade\n\n"
                "def apply():\n"
                "    run_upgrade(None, 'head')\n"
            ),
        },
        {"sample.server"},
    )
    assert len(findings) == 1
    assert findings[0].target == "alembic.command.upgrade"
    assert findings[0].call_path == (
        "sample.server.lifespan",
        "sample.migration_adapter.apply",
    )

    introspection_only = {
        "sample.runtime": (
            "from alembic.config import Config as AlembicConfig\n"
            "from alembic.runtime.migration import MigrationContext as Context\n"
            "from alembic.script import ScriptDirectory as Scripts\n\n"
            "def inspect(connection):\n"
            "    config = AlembicConfig()\n"
            "    Scripts.from_config(config).get_heads()\n"
            "    Context.configure(connection).get_current_heads()\n"
        )
    }
    assert (
        find_reachable_alembic_mutations(introspection_only, {"sample.runtime"}) == ()
    )


def _assert_import_time_finding(
    findings: tuple[AlembicMutationFinding, ...],
    *,
    module: str,
    owner_fragment: str,
    target: str,
) -> None:
    matching = [
        finding
        for finding in findings
        if finding.module == module
        and owner_fragment in finding.function
        and finding.target == target
    ]
    assert matching
    for finding in matching:
        assert isinstance(finding.line, int)
        assert finding.line > 0
        call_path = finding.call_path
        assert isinstance(call_path, tuple)
        assert 1 <= len(call_path) <= 8
        assert call_path[-1] == finding.function


def test_import_time_alembic_analysis_detects_direct_top_level_alias() -> None:
    findings = find_reachable_alembic_mutations(
        {
            "sample.runtime": (
                "from alembic.command import upgrade as migrate\n"
                "migrate(None, 'head')\n"
            )
        },
        {"sample.runtime"},
    )
    _assert_import_time_finding(
        findings,
        module="sample.runtime",
        owner_fragment="<module_init>",
        target="alembic.command.upgrade",
    )


def test_import_time_alembic_analysis_detects_imported_module_side_effect() -> None:
    findings = find_reachable_alembic_mutations(
        {
            "sample.server": "import sample.adapter\n\ndef build_app():\n    pass\n",
            "sample.adapter": (
                "from alembic import command\ncommand.stamp(None, 'head')\n"
            ),
        },
        {"sample.server"},
    )
    _assert_import_time_finding(
        findings,
        module="sample.adapter",
        owner_fragment="<module_init>",
        target="alembic.command.stamp",
    )
    assert any(
        finding.call_path
        == (
            "sample.server.<module_init>",
            "sample.adapter.<module_init>",
        )
        for finding in findings
    )


def test_import_time_alembic_analysis_detects_class_body_side_effect() -> None:
    findings = find_reachable_alembic_mutations(
        {
            "sample.runtime": (
                "import alembic.command as command\n\n"
                "class Runtime:\n"
                "    state = command.downgrade(None, 'base')\n"
            )
        },
        {"sample.runtime"},
    )
    _assert_import_time_finding(
        findings,
        module="sample.runtime",
        owner_fragment="Runtime.<class_init>",
        target="alembic.command.downgrade",
    )


def test_import_time_alembic_analysis_follows_local_helper() -> None:
    findings = find_reachable_alembic_mutations(
        {
            "sample.runtime": (
                "from alembic import command\n\n"
                "def apply():\n"
                "    command.upgrade(None, 'head')\n\n"
                "apply()\n"
            )
        },
        {"sample.runtime"},
    )
    _assert_import_time_finding(
        findings,
        module="sample.runtime",
        owner_fragment="sample.runtime.apply",
        target="alembic.command.upgrade",
    )
    assert any(
        finding.call_path
        == (
            "sample.runtime.<module_init>",
            "sample.runtime.apply",
        )
        for finding in findings
    )


@pytest.mark.parametrize("definition_kind", ["decorator", "default"])
def test_import_time_alembic_analysis_detects_definition_time_wrapper(
    definition_kind: str,
) -> None:
    definition = (
        "@apply\ndef configured():\n    pass\n"
        if definition_kind == "decorator"
        else "def configured(value=apply()):\n    pass\n"
    )
    findings = find_reachable_alembic_mutations(
        {
            "sample.runtime": ("from sample.adapter import apply\n\n" + definition),
            "sample.adapter": (
                "from alembic.command import merge as mutate\n\n"
                "def apply(value=None):\n"
                "    mutate(None, 'heads')\n"
                "    return value\n"
            ),
        },
        {"sample.runtime"},
    )
    _assert_import_time_finding(
        findings,
        module="sample.adapter",
        owner_fragment="sample.adapter.apply",
        target="alembic.command.merge",
    )
    assert any(
        finding.call_path[0] == "sample.runtime.<module_init>"
        and finding.call_path[-1] == "sample.adapter.apply"
        for finding in findings
    )


def test_automatic_migration_analysis_preserves_lexical_import_scopes() -> None:
    local_import_only = {
        "sample.runtime": (
            "def bind_local_alias():\n"
            "    from alembic.command import revision as action\n"
            "    return action\n\n"
            "def harmless():\n"
            "    action()\n"
        )
    }
    assert find_reachable_alembic_mutations(local_import_only, {"sample.runtime"}) == ()


def test_import_time_alembic_analysis_detects_root_package_initializer_side_effect():
    findings = find_reachable_alembic_mutations(
        {
            "sample": ("from alembic.command import upgrade\nupgrade(None, 'head')\n"),
            "sample.server": "import sample\n\ndef build_app():\n    pass\n",
        },
        {"sample.server"},
    )
    assert len(findings) == 1
    finding = findings[0]
    assert finding.module == "sample"
    assert finding.function == "sample.<module_init>"
    assert finding.target == "alembic.command.upgrade"
    assert finding.line > 0
    assert 1 <= len(finding.call_path) <= 8
    assert finding.call_path[-1] == finding.function


def test_import_time_alembic_analysis_detects_imported_package_initializer_mutation():
    findings = find_reachable_alembic_mutations(
        {
            "sample.server": "import vendor.adapter\n",
            "vendor": ("from alembic.command import stamp\nstamp(None, 'head')\n"),
            "vendor.adapter": "SAFE = True\n",
        },
        {"sample.server"},
    )
    assert len(findings) == 1
    finding = findings[0]
    assert finding.module == "vendor"
    assert finding.function == "vendor.<module_init>"
    assert finding.target == "alembic.command.stamp"
    assert finding.line > 0
    assert finding.call_path == (
        "sample.server.<module_init>",
        "vendor.<module_init>",
    )


def test_import_time_alembic_analysis_detects_nested_parent_initializer_side_effect():
    findings = find_reachable_alembic_mutations(
        {
            "sample": "SAFE = True\n",
            "sample.api": (
                "from alembic import command\ncommand.merge(None, 'heads')\n"
            ),
            "sample.api.http": "def build_app():\n    pass\n",
        },
        {"sample.api.http"},
    )
    assert len(findings) == 1
    finding = findings[0]
    assert finding.module == "sample.api"
    assert finding.function == "sample.api.<module_init>"
    assert finding.target == "alembic.command.merge"
    assert finding.line > 0
    assert finding.call_path == ("sample.api.<module_init>",)


def test_import_time_alembic_analysis_accepts_safe_package_initializer_chain() -> None:
    findings = find_reachable_alembic_mutations(
        {
            "sample": "import sample.api\n",
            "sample.api": "from .. import adapter\nimport sample\n",
            "sample.api.http": "import sample.api\n",
            "sample.adapter": "SAFE = True\n",
        },
        {"sample.api.http"},
    )
    assert findings == ()


def test_import_time_alembic_analysis_does_not_invent_missing_package_initializer() -> (
    None
):
    sources = {"sample.server": "def build_app():\n    pass\n"}
    assert existing_initializer_chain("a.b.c", {"a", "a.b.c"}) == ("a", "a.b.c")
    assert existing_initializer_chain("sample.server", sources) == ("sample.server",)
    assert find_reachable_alembic_mutations(sources, {"sample.server"}) == ()


def test_real_netauto_root_initializer_chains_include_existing_parents() -> None:
    module_names = frozenset(_production_module_sources())
    assert existing_initializer_chain("netauto", module_names) == ("netauto",)
    assert existing_initializer_chain("netauto.entrypoints", module_names) == (
        "netauto",
        "netauto.entrypoints",
    )
    assert existing_initializer_chain("netauto.entrypoints.http", module_names) == (
        "netauto",
        "netauto.entrypoints",
        "netauto.entrypoints.http",
    )
    assert existing_initializer_chain("netauto.runtime", module_names) == (
        "netauto",
        "netauto.runtime",
    )
    assert existing_initializer_chain("netauto.cli", module_names) == (
        "netauto",
        "netauto.cli",
    )


def test_security_transport_and_secret_surfaces_remain_external() -> None:
    document, operations = _openapi_operations()
    assert "securitySchemes" not in repr(document)
    assert not any(
        fragment in path
        for _, path in operations
        for fragment in ("auth", "login", "logout", "token", "account", "role")
    )
    assert all(code not in repr(document) for code in ("401", "403", "429"))
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
    repository_files = {line for line in result.stdout.splitlines() if line}
    assert forbidden_deployment_assets(repository_files) == frozenset()
    pyproject = (ROOT / "pyproject.toml").read_text()
    assert "gunicorn" not in pyproject.lower()
    assert "prometheus" not in pyproject.lower()
    assert "opentelemetry" not in pyproject.lower()


def _repository_capability_inputs() -> tuple[set[str], set[str], set[str]]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    repository_files = {line for line in result.stdout.splitlines() if line}
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    raw_project = cast(dict[str, object], project["project"])
    dependencies = {
        str(item) for item in cast(list[object], raw_project.get("dependencies", []))
    }
    optional = cast(
        dict[str, list[object]], raw_project.get("optional-dependencies", {})
    )
    dependencies.update(str(item) for group in optional.values() for item in group)
    scripts = {
        f"{name}={target}"
        for name, target in cast(
            dict[str, object], raw_project.get("scripts", {})
        ).items()
    }
    return repository_files, dependencies, scripts


def test_abstract_negative_capability_audit_covers_real_repository_surfaces() -> None:
    repository_files, dependencies, scripts = _repository_capability_inputs()
    assert len(ABSTRACT_NEGATIVE_CAPABILITY_IDS) == 11
    assert (
        find_abstract_capability_findings(
            repository_files,
            dependencies=dependencies,
            scripts=scripts,
        )
        == ()
    )


def test_abstract_negative_capability_audit_detects_synthetic_counterexamples() -> None:
    expected = {
        "docs/operations/business-continuity.md": (
            "data_protection::business-continuity SLA"
        ),
        "docs/operations/postgresql-replicas.md": (
            "data_protection::PostgreSQL replica management"
        ),
        "docs/operations/pitr.md": (
            "data_protection::point-in-time recovery procedure"
        ),
        "docs/deployment/multi-region.md": (
            "deployment_platform::multi-region operation"
        ),
        "docs/deployment/high-availability.md": (
            "deployment_platform::service discovery, clustering or high availability"
        ),
        "ops/nginx.conf": ("security_network::reverse-proxy or firewall automation"),
        "ops/firewall-rules.nft": (
            "security_network::reverse-proxy or firewall automation"
        ),
        "ops/vpn.conf": ("security_network::VPN or load-balancer configuration"),
        "ops/postgresql-replica.conf": (
            "data_protection::PostgreSQL replica management"
        ),
        "src/netauto/cluster.py": (
            "deployment_platform::service discovery, clustering or high availability"
        ),
        "src/netauto/replication.py": (
            "data_protection::PostgreSQL replica management"
        ),
        "src/netauto/backup.py": "data_protection::backup or restore automation",
        ".circleci/config.yml": "deployment_platform::CI/CD deployment pipeline",
        "dashboards/core.json": "observability::dashboards or alerting",
        "grafana/datasources/netauto.yml": "observability::dashboards or alerting",
        "fluent-bit.conf": "observability::central log shipping or rotation",
    }
    findings = find_abstract_capability_findings(expected)
    observed = {(finding.value, finding.identifier) for finding in findings}
    assert {
        (path.lower(), identifier) for path, identifier in expected.items()
    } <= observed

    legacy_assets = {
        "nested/container/Dockerfile.worker",
        "nested/k8s/deployment.yaml",
        "packaging/systemd/netauto.service",
        "ops/recovery/backup.sh",
        "ops/recovery/restore.sh",
        ".github/workflows/release.yml",
    }
    assert forbidden_deployment_assets(legacy_assets) == frozenset(
        path.lower() for path in legacy_assets
    )


def test_abstract_negative_capability_audit_allows_normative_and_test_surfaces() -> (
    None
):
    safe_paths = {
        "docs/milestones/M2/contract.md",
        "docs/milestones/M2/architecture/runtime-deployment.md",
        "docs/architecture/verification.md",
        "src/netauto/runtime/schema_guard.py",
        "tests/test_non_goals_describe_multi-region-backup-metrics.py",
    }
    assert find_abstract_capability_findings(safe_paths) == ()


def test_deployment_asset_audit_checks_nested_paths_and_basenames() -> None:
    candidates = {
        "Dockerfile",
        "ops/prod/Dockerfile.worker",
        "deploy/base/deployment.yaml",
        "packaging/systemd/netauto.service",
        "ops/recovery/backup.sh",
        ".github/workflows/release.yml",
        "docs/milestones/M2/architecture/runtime-deployment.md",
        "src/netauto/runtime/schema_guard.py",
    }
    assert forbidden_deployment_assets(candidates) == frozenset(
        {
            "dockerfile",
            "ops/prod/dockerfile.worker",
            "deploy/base/deployment.yaml",
            "packaging/systemd/netauto.service",
            "ops/recovery/backup.sh",
            ".github/workflows/release.yml",
        }
    )


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
    closure_records = {
        "steps-consistency-closure.md",
        "wip-extraction-closure.md",
    }
    optional_active_execution_aids = {"M2-S08-review-fixes-codex-prompt.md"}
    permanent_wip_census = set(rows) | closure_records
    assert wip_files - optional_active_execution_aids == permanent_wip_census
    assert wip_files <= permanent_wip_census | optional_active_execution_aids
    assert (wip_files - optional_active_execution_aids) | closure_records == (
        permanent_wip_census
    )

    simulated_after_reviewer_removal = wip_files - optional_active_execution_aids
    assert simulated_after_reviewer_removal == permanent_wip_census

    normative = {
        ROOT / "docs/milestones/M2/contract.md",
        ROOT / "docs/milestones/M2/steps.md",
        ROOT / "docs/milestones/M2/status.md",
        *sorted((ROOT / "docs/milestones/M2/architecture").glob("*.md")),
    }
    allowed_context = re.compile(
        r"non-normative|historical|discovery|supersed|review record|audit record|"
        r"consistency closure|freeze approval|retir|captured for ratification|"
        r"must\s+\W*not|execution aid|corrective aid",
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
