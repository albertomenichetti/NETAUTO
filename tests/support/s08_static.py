"""Bounded static-analysis helpers for M2-S08 negative-surface evidence."""

from __future__ import annotations

import ast
from collections import deque
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import PurePosixPath

ALEMBIC_MUTATIONS = frozenset(
    {
        "alembic.command.downgrade",
        "alembic.command.merge",
        "alembic.command.revision",
        "alembic.command.stamp",
        "alembic.command.upgrade",
    }
)

_DEPLOYMENT_BASENAMES = frozenset(
    {
        ".gitlab-ci.yml",
        "alertmanager.yml",
        "alertmanager.yaml",
        "azure-pipelines.yml",
        "backup.sh",
        "compose.yml",
        "compose.yaml",
        "daemonset.yml",
        "daemonset.yaml",
        "deployment.yml",
        "deployment.yaml",
        "docker-compose.yml",
        "docker-compose.yaml",
        "fluent-bit.conf",
        "grafana.ini",
        "ingress.yml",
        "ingress.yaml",
        "jenkinsfile",
        "netauto.service",
        "prometheus.yml",
        "prometheus.yaml",
        "restore.sh",
        "statefulset.yml",
        "statefulset.yaml",
    }
)
_DEPLOYMENT_DIRECTORY_PARTS = frozenset(
    {
        "ansible",
        "charts",
        "helm",
        "k8s",
        "kubernetes",
        "terraform",
    }
)


def forbidden_deployment_assets(paths: Iterable[str]) -> frozenset[str]:
    """Return forbidden deployment/operations assets at any repository depth."""
    findings: set[str] = set()
    for raw_path in paths:
        normalized = raw_path.replace("\\", "/").strip("/").lower()
        if not normalized:
            continue
        path = PurePosixPath(normalized)
        parts = path.parts
        basename = path.name
        forbidden = (
            basename in _DEPLOYMENT_BASENAMES
            or basename.startswith("dockerfile")
            or basename.endswith(".service")
            or basename.startswith(("backup.", "restore."))
            or bool(set(parts[:-1]) & _DEPLOYMENT_DIRECTORY_PARTS)
            or parts[:2] == (".github", "workflows")
        )
        if forbidden:
            findings.add(normalized)
    return frozenset(findings)


@dataclass(frozen=True, slots=True)
class AlembicMutationFinding:
    """One reachable mutating Alembic call and its local call path."""

    module: str
    function: str
    line: int
    target: str
    call_path: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _FunctionInfo:
    key: str
    module: str
    node: ast.FunctionDef | ast.AsyncFunctionDef
    aliases: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class _ModuleInfo:
    name: str
    tree: ast.Module
    aliases: Mapping[str, str]
    imports: frozenset[str]
    functions: tuple[_FunctionInfo, ...]


def _import_aliases(tree: ast.AST) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                bound = alias.asname or alias.name.split(".", 1)[0]
                aliases[bound] = alias.name if alias.asname else bound
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            for alias in node.names:
                if alias.name == "*":
                    continue
                aliases[alias.asname or alias.name] = f"{node.module}.{alias.name}"
    return aliases


def _module_imports(tree: ast.Module) -> frozenset[str]:
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.add(node.module)
    return frozenset(imports)


def _functions(
    module: str, tree: ast.Module, module_aliases: Mapping[str, str]
) -> tuple[_FunctionInfo, ...]:
    result: list[_FunctionInfo] = []

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.owners: list[str] = []

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            self.owners.append(node.name)
            self.generic_visit(node)
            self.owners.pop()

        def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
            key = ".".join((module, *self.owners, node.name))
            aliases = dict(module_aliases)
            aliases.update(_import_aliases(node))
            result.append(_FunctionInfo(key, module, node, aliases))
            self.owners.append(node.name)
            self.generic_visit(node)
            self.owners.pop()

        visit_FunctionDef = _visit_function
        visit_AsyncFunctionDef = _visit_function

    Visitor().visit(tree)
    return tuple(result)


def _module_info(name: str, source: str) -> _ModuleInfo:
    tree = ast.parse(source, filename=f"{name.replace('.', '/')}.py")
    aliases = _import_aliases(tree)
    return _ModuleInfo(
        name=name,
        tree=tree,
        aliases=aliases,
        imports=_module_imports(tree),
        functions=_functions(name, tree, aliases),
    )


def _resolve_call(
    expression: ast.expr, *, module: str, aliases: Mapping[str, str]
) -> str | None:
    if isinstance(expression, ast.Name):
        return aliases.get(expression.id, f"{module}.{expression.id}")
    if isinstance(expression, ast.Attribute):
        owner = _resolve_call(expression.value, module=module, aliases=aliases)
        return None if owner is None else f"{owner}.{expression.attr}"
    return None


def find_reachable_alembic_mutations(
    module_sources: Mapping[str, str], root_modules: Iterable[str]
) -> tuple[AlembicMutationFinding, ...]:
    """Find alias-safe Alembic mutations reachable from the supplied roots."""
    infos = {
        name: _module_info(name, source) for name, source in module_sources.items()
    }
    roots = frozenset(root_modules)
    unknown_roots = roots - set(infos)
    if unknown_roots:
        raise ValueError(f"unknown root modules: {sorted(unknown_roots)!r}")

    module_closure: set[str] = set()
    module_queue = deque(sorted(roots))
    while module_queue:
        module = module_queue.popleft()
        if module in module_closure:
            continue
        module_closure.add(module)
        for imported in infos[module].imports:
            if imported in infos and imported not in module_closure:
                module_queue.append(imported)

    functions = {
        function.key: function
        for module in module_closure
        for function in infos[module].functions
    }
    direct: dict[str, list[tuple[int, str]]] = {key: [] for key in functions}
    edges: dict[str, set[str]] = {key: set() for key in functions}
    for key, function in functions.items():
        for node in ast.walk(function.node):
            if not isinstance(node, ast.Call):
                continue
            target = _resolve_call(
                node.func,
                module=function.module,
                aliases=function.aliases,
            )
            if target in ALEMBIC_MUTATIONS:
                direct[key].append((node.lineno, target))
            if target in functions:
                edges[key].add(target)

    root_functions = sorted(
        key for key, function in functions.items() if function.module in roots
    )
    findings: list[AlembicMutationFinding] = []
    for root in root_functions:
        queue: deque[tuple[str, tuple[str, ...]]] = deque([(root, (root,))])
        visited: set[str] = set()
        while queue:
            key, path = queue.popleft()
            if key in visited:
                continue
            visited.add(key)
            function = functions[key]
            findings.extend(
                AlembicMutationFinding(
                    module=function.module,
                    function=key,
                    line=line,
                    target=target,
                    call_path=path,
                )
                for line, target in direct[key]
            )
            queue.extend(
                (child, (*path, child)) for child in sorted(edges[key] - visited)
            )
    return tuple(
        sorted(
            set(findings),
            key=lambda item: (
                item.module,
                item.function,
                item.line,
                item.target,
                item.call_path,
            ),
        )
    )
