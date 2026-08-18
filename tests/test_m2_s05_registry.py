"""Static registry, wire-boundary, and HTTP-only scope evidence for M2-S05."""

import ast
import re
from collections import Counter
from pathlib import Path

from netauto.cli.model import (
    LOCAL_ERROR_CODES,
    SELECTOR_ERROR_CODES,
    TRANSPORT_PROTOCOL_ERROR_CODES,
)
from netauto.cli.registry import BUSINESS_OPERATION_SET, COMMAND_REGISTRY
from netauto.entrypoints.api.datatypes import DataTypeDto as RouteDataTypeDto
from netauto.entrypoints.http import build_app
from netauto.settings import Settings
from netauto.transport.http.datatypes import DataTypeDto

ROOT = Path(__file__).parents[1]


def test_registry_is_exactly_the_server_business_openapi_inventory() -> None:
    app = build_app(
        Settings(database_url="postgresql+psycopg://unused@example.test/netauto")
    )
    operations = {
        (method.upper(), path)
        for path, path_item in app.openapi()["paths"].items()
        if path.startswith("/api/v1/core")
        for method in path_item
        if method.upper() in {"GET", "POST", "DELETE", "PUT", "PATCH"}
    }
    assert len(COMMAND_REGISTRY) == 63
    assert len(BUSINESS_OPERATION_SET) == 63
    assert operations == BUSINESS_OPERATION_SET
    assert not any(path == "/health/core" for _, path in BUSINESS_OPERATION_SET)
    assert Counter(key.resource for key in COMMAND_REGISTRY) == {
        "datatype": 14,
        "object-template": 16,
        "object": 13,
        "relationship-definition": 14,
        "relationship": 5,
        "lifecycle-event": 1,
    }


def test_every_registry_spec_is_complete_and_path_metadata_is_closed() -> None:
    for key, spec in COMMAND_REGISTRY.items():
        assert key == spec.key
        assert spec.method in {"GET", "POST", "DELETE"}
        assert spec.expected_status in {200, 201, 204}
        assert spec.renderer_key
        assert spec.help_text
        assert spec.example
        assert len({parameter.name for parameter in spec.parameters}) == len(
            spec.parameters
        )
        placeholders = set(re.findall(r"\{([^{}]+)\}", spec.path_template))
        path_parameters = {
            parameter.name
            for parameter in spec.parameters
            if parameter.location == "path"
        }
        if spec.selector_parameter is not None:
            path_parameters.add(spec.selector_parameter)
        assert placeholders == path_parameters
        assert (spec.expected_status == 204) == (spec.response_annotation is None)
    assert LOCAL_ERROR_CODES == {
        "cli_invalid_invocation",
        "cli_invalid_command",
        "cli_missing_selector",
        "cli_unexpected_selector",
        "cli_missing_parameter",
        "cli_unexpected_parameter",
        "cli_duplicate_parameter",
        "cli_invalid_parameter",
        "cli_json_error",
        "cli_file_error",
        "cli_not_connected",
        "cli_internal_error",
    }
    assert SELECTOR_ERROR_CODES == {
        "cli_selector_invalid",
        "cli_selector_not_found",
        "cli_selector_ambiguous",
    }
    assert TRANSPORT_PROTOCOL_ERROR_CODES == {
        "cli_transport_error",
        "cli_protocol_error",
    }


def test_fastapi_routes_use_the_neutral_wire_dto_identity() -> None:
    assert RouteDataTypeDto is DataTypeDto


def test_cli_import_closure_has_no_server_or_database_boundary() -> None:
    cli_forbidden = (
        "netauto.application",
        "netauto.persistence",
        "netauto.entrypoints.api",
        "netauto.entrypoints.http",
        "netauto.settings",
        "sqlalchemy",
        "psycopg",
        "alembic",
        "fastapi",
    )
    for path in sorted((ROOT / "src/netauto/cli").glob("*.py")):
        tree = ast.parse(path.read_text())
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported.append(node.module)
        assert not any(
            name == prefix or name.startswith(prefix + ".")
            for name in imported
            for prefix in cli_forbidden
        ), path

    neutral_forbidden = (
        "netauto.application",
        "netauto.persistence",
        "netauto.entrypoints",
        "sqlalchemy",
        "psycopg",
        "alembic",
        "fastapi",
    )
    for path in sorted((ROOT / "src/netauto/transport/http").glob("*.py")):
        tree = ast.parse(path.read_text())
        imported = [
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        ]
        assert not any(
            name == prefix or name.startswith(prefix + ".")
            for name in imported
            for prefix in neutral_forbidden
        ), path

    for path in sorted((ROOT / "src/netauto/entrypoints/api").glob("*.py")):
        tree = ast.parse(path.read_text())
        assert not any(isinstance(node, ast.ClassDef) for node in tree.body), path


def test_s05_has_no_repl_or_insecure_option_surface() -> None:
    cli = "\n".join(
        path.read_text() for path in sorted((ROOT / "src/netauto/cli").glob("*.py"))
    )
    assert not (ROOT / "src/netauto/cli/repl.py").exists()
    for forbidden in (
        "prompt_toolkit",
        "--insecure",
        "verify=False",
        "skip-verify",
        "client_cert",
        "Authorization",
    ):
        assert forbidden not in cli


def test_httpx_is_runtime_dependency_and_console_entrypoint_is_exact() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text()
    project, dev = pyproject.split("[dependency-groups]", 1)
    assert '"httpx>=0.28,<1"' in project
    assert 'netauto = "netauto.cli.main:main"' in project
    assert '"httpx>=0.28,<1"' not in dev
