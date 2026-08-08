import ast
from pathlib import Path

FORBIDDEN_ROOTS = (
    "netauto.api",
    "netauto.application",
    "netauto.core",
    "netauto.persistence",
)
CLI_PACKAGE = ("netauto", "cli")


def _join_parts(parts: tuple[str, ...]) -> str:
    return ".".join(parts)


def _resolve_relative_module(
    path: Path,
    module: str | None,
    level: int,
) -> tuple[str, ...]:
    package_parts = CLI_PACKAGE + path.relative_to("src/netauto/cli").with_suffix("").parts[:-1]
    if level <= 0:
        return tuple(module.split(".")) if module else ()

    parent_hops = level - 1
    if parent_hops > len(package_parts):
        return ()

    base_parts = package_parts[: len(package_parts) - parent_hops]
    module_parts = tuple(module.split(".")) if module else ()
    return base_parts + module_parts


def _import_targets(path: Path, source: str) -> list[str]:
    targets: list[str] = []
    tree = ast.parse(source, filename=str(path))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                targets.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            base_parts = _resolve_relative_module(path, node.module, node.level)
            base_target = _join_parts(base_parts)
            if base_target:
                targets.append(base_target)

            for alias in node.names:
                alias_parts = tuple(alias.name.split("."))
                effective_target = _join_parts(base_parts + alias_parts)
                if effective_target:
                    targets.append(effective_target)

    return targets


def _violations_for_source(path: Path, source: str) -> list[str]:
    violations: list[str] = []

    for target in _import_targets(path, source):
        if target == "httpx2" or target.startswith("httpx2."):
            violations.append(f"{path}: forbidden import {target}")
            continue

        if target.startswith(FORBIDDEN_ROOTS):
            violations.append(f"{path}: forbidden import {target}")

    return violations


def test_import_guard_rejects_forbidden_backend_import_forms() -> None:
    path = Path("src/netauto/cli/example.py")
    source = """
import netauto.core
import netauto.core.datatype

from netauto import core
from netauto.core import datatype
from netauto.core.datatype import DataType

from ..core import datatype
from ..core.datatype import DataType
from ..application import datatype
from ..application.datatype import DataTypeApplicationService
"""

    violations = _violations_for_source(path, source)

    assert f"{path}: forbidden import netauto.core" in violations
    assert f"{path}: forbidden import netauto.core.datatype" in violations
    assert f"{path}: forbidden import netauto.application" in violations
    assert f"{path}: forbidden import netauto.application.datatype" in violations


def test_import_guard_rejects_httpx2() -> None:
    path = Path("src/netauto/cli/example.py")
    source = """
import httpx2
from httpx2 import AsyncClient
"""

    violations = _violations_for_source(path, source)

    assert f"{path}: forbidden import httpx2" in violations
    assert f"{path}: forbidden import httpx2.AsyncClient" in violations


def test_import_guard_allows_cli_local_imports() -> None:
    path = Path("src/netauto/cli/example.py")
    source = """
from netauto.cli.errors import CliError
from .errors import CliError
"""

    assert _violations_for_source(path, source) == []


def test_cli_imports_only_transport_side_dependencies() -> None:
    cli_root = Path("src/netauto/cli")
    violations: list[str] = []

    for path in cli_root.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue

        source = path.read_text(encoding="utf-8")
        violations.extend(_violations_for_source(path, source))

    assert violations == []
