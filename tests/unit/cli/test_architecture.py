import ast
from pathlib import Path

FORBIDDEN_PREFIXES = (
    "netauto.api",
    "netauto.application",
    "netauto.core",
    "netauto.persistence",
)


def test_cli_imports_only_transport_side_dependencies() -> None:
    cli_root = Path("src/netauto/cli")
    violations: list[str] = []

    for path in cli_root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("httpx2"):
                        violations.append(f"{path}: forbidden import {alias.name}")
                    if alias.name.startswith(FORBIDDEN_PREFIXES):
                        violations.append(f"{path}: forbidden import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module.startswith("httpx2"):
                    violations.append(f"{path}: forbidden import {module}")
                if module.startswith(FORBIDDEN_PREFIXES):
                    violations.append(f"{path}: forbidden import {module}")

    assert violations == []
