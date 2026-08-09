import ast
from pathlib import Path

API_ROOT = Path("src/netauto/api")


def _import_targets(path: Path, source: str) -> list[str]:
    targets: list[str] = []
    tree = ast.parse(source, filename=str(path))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                targets.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level != 0:
                continue
            if node.module:
                targets.append(node.module)
                for alias in node.names:
                    targets.append(f"{node.module}.{alias.name}")

    return targets


def _violations_for_source(path: Path, source: str) -> list[str]:
    violations: list[str] = []

    for target in _import_targets(path, source):
        if target.startswith("sqlalchemy"):
            violations.append(f"{path}: forbidden import {target}")
            continue

        if target.startswith("netauto.persistence"):
            violations.append(f"{path}: forbidden import {target}")

    return violations


def test_api_import_guard_rejects_concrete_persistence_and_sqlalchemy_imports() -> None:
    path = Path("src/netauto/api/example.py")
    source = """
import sqlalchemy
from sqlalchemy.orm import Session
from netauto.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from netauto.persistence.memory.objecttemplate_repository import InMemoryObjectTemplateRepository
"""

    violations = _violations_for_source(path, source)

    assert f"{path}: forbidden import sqlalchemy" in violations
    assert f"{path}: forbidden import sqlalchemy.orm" in violations
    assert f"{path}: forbidden import netauto.persistence.sqlalchemy.unit_of_work" in violations
    assert (
        f"{path}: forbidden import netauto.persistence.memory.objecttemplate_repository"
        in violations
    )


def test_api_import_guard_allows_application_core_fastapi_and_pydantic() -> None:
    path = Path("src/netauto/api/example.py")
    source = """
from fastapi import APIRouter
from pydantic import BaseModel
from netauto.application.objecttemplate import ObjectTemplateApplicationService
from netauto.core.objecttemplate import ObjectTemplateVersion
"""

    assert _violations_for_source(path, source) == []


def test_api_package_avoids_concrete_persistence_and_sqlalchemy_imports() -> None:
    violations: list[str] = []

    for path in API_ROOT.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue

        source = path.read_text(encoding="utf-8")
        violations.extend(_violations_for_source(path, source))

    assert violations == []
