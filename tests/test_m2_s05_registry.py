"""Static registry, wire-boundary, and HTTP-only scope evidence for M2-S05."""

import ast
import re
import shlex
from collections import Counter
from pathlib import Path

from netauto.cli.model import (
    LOCAL_ERROR_CODES,
    SELECTOR_ERROR_CODES,
    TRANSPORT_PROTOCOL_ERROR_CODES,
)
from netauto.cli.parser import parse_command_example
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


def test_all_registry_examples_parse_to_their_own_command_without_http() -> None:
    example_count = 0
    for spec in COMMAND_REGISTRY.values():
        assert spec.examples
        for index, example in enumerate(spec.examples):
            command = parse_command_example(spec, index)
            example_count += 1
            assert command.key == spec.key
            assert (command.selector is not None) == spec.selector_required
            required = {
                parameter.name for parameter in spec.parameters if parameter.required
            }
            assert required <= command.parameters.keys()
            assert shlex.split(spec.example) == list(spec.example_argv)
            assert example[:2] == (spec.key.resource, spec.key.operation)
    assert example_count == 65


def test_registry_descriptions_and_help_metadata_are_bounded_and_usable() -> None:
    for spec in COMMAND_REGISTRY.values():
        assert 24 <= len(spec.help_text) <= 160
        assert spec.help_text.lower() not in {
            f"{spec.key.operation} {spec.key.resource}",
            f"{spec.key.resource} {spec.key.operation}",
        }
        assert len(spec.help_text.split()) >= 6
        assert spec.renderer_key != f"{spec.key.resource}.{spec.key.operation}"
        assert spec.method in {"GET", "POST", "DELETE"}
        assert spec.path_template.startswith("/api/v1/core/")
        for parameter in spec.parameters:
            assert parameter.location in {"path", "query", "body"}
            assert isinstance(parameter.required, bool)
            assert isinstance(parameter.nullable, bool)
    assert any(
        parameter.required
        for spec in COMMAND_REGISTRY.values()
        for parameter in spec.parameters
    )
    assert any(
        not parameter.required
        for spec in COMMAND_REGISTRY.values()
        for parameter in spec.parameters
    )
    assert any(
        parameter.nullable
        for spec in COMMAND_REGISTRY.values()
        for parameter in spec.parameters
    )


def test_registry_examples_preserve_exact_selector_presence_and_required_operands() -> (
    None
):
    for spec in COMMAND_REGISTRY.values():
        for index in range(len(spec.examples)):
            command = parse_command_example(spec, index)
            assert (command.selector is not None) == spec.selector_required
            for parameter in spec.parameters:
                if parameter.required:
                    assert parameter.name in command.parameters


def test_relationship_definition_examples_cover_both_discriminated_shapes() -> None:
    create = COMMAND_REGISTRY[
        next(
            key
            for key in COMMAND_REGISTRY
            if key.resource == "relationship-definition" and key.operation == "create"
        )
    ]
    rename = COMMAND_REGISTRY[
        next(
            key
            for key in COMMAND_REGISTRY
            if key.resource == "relationship-definition" and key.operation == "rename"
        )
    ]
    assert len(create.examples) == 2
    assert len(rename.examples) == 2
    create_commands = [
        parse_command_example(create, index) for index in range(len(create.examples))
    ]
    rename_commands = [
        parse_command_example(rename, index) for index in range(len(rename.examples))
    ]
    assert [command.parameters["symmetric"] for command in create_commands] == [
        False,
        True,
    ]
    assert {"perspectives", "endpoint_template_ids"} <= {
        name for command in create_commands for name in command.parameters
    }
    assert {"resolutions", "name"} == {
        name for command in rename_commands for name in command.parameters
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
    assert (ROOT / "src/netauto/cli/repl.py").is_file()
    assert "prompt_toolkit" in cli
    for forbidden in (
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
    assert '"prompt-toolkit>=3.0,<4"' in project
    assert 'netauto = "netauto.cli.main:main"' in project
    assert '"httpx>=0.28,<1"' not in dev
    assert '"prompt-toolkit>=3.0,<4"' not in dev
