"""Bounded static-analysis helpers for M2-S08 negative-surface evidence."""

from __future__ import annotations

import ast
from collections import deque
from collections.abc import Iterable, Mapping, Sequence
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


def _normalized_path(raw_path: str) -> str:
    return raw_path.replace("\\", "/").strip("/").lower()


def forbidden_deployment_assets(paths: Iterable[str]) -> frozenset[str]:
    """Return forbidden deployment/operations assets at any repository depth."""
    findings: set[str] = set()
    for raw_path in paths:
        normalized = _normalized_path(raw_path)
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
class AbstractCapabilityPolicy:
    """Finite repository surfaces that would realize one abstract non-goal."""

    identifier: str
    path_fragments: frozenset[str] = frozenset()
    basenames: frozenset[str] = frozenset()
    directory_parts: frozenset[str] = frozenset()
    production_modules: frozenset[str] = frozenset()
    dependency_tokens: frozenset[str] = frozenset()
    script_tokens: frozenset[str] = frozenset()


def _policy(
    identifier: str,
    *,
    paths: Sequence[str] = (),
    basenames: Sequence[str] = (),
    directories: Sequence[str] = (),
    modules: Sequence[str] = (),
    dependencies: Sequence[str] = (),
    scripts: Sequence[str] = (),
) -> AbstractCapabilityPolicy:
    return AbstractCapabilityPolicy(
        identifier=identifier,
        path_fragments=frozenset(paths),
        basenames=frozenset(basenames),
        directory_parts=frozenset(directories),
        production_modules=frozenset(modules),
        dependency_tokens=frozenset(dependencies),
        script_tokens=frozenset(scripts),
    )


ABSTRACT_NEGATIVE_CAPABILITY_POLICIES = (
    _policy(
        "data_protection::backup or restore automation",
        paths=("/backup.", "/restore."),
        basenames=("backup.py", "backup.sh", "restore.py", "restore.sh"),
        modules=("netauto.backup", "netauto.restore"),
        scripts=("backup", "restore"),
    ),
    _policy(
        "data_protection::PostgreSQL replica management",
        paths=("postgresql-replica", "postgresql-replicas", "/replication."),
        modules=("netauto.replication",),
        dependencies=("patroni", "repmgr"),
        scripts=("replica", "replication"),
    ),
    _policy(
        "data_protection::point-in-time recovery procedure",
        paths=("/pitr.", "point-in-time-recovery"),
        basenames=("pitr.md", "pitr.sh"),
        scripts=("pitr", "point-in-time-recovery"),
    ),
    _policy(
        "data_protection::business-continuity SLA",
        paths=("business-continuity",),
        scripts=("business-continuity",),
    ),
    _policy(
        "deployment_platform::multi-region operation",
        paths=("multi-region",),
        scripts=("multi-region",),
    ),
    _policy(
        "deployment_platform::service discovery, clustering or high availability",
        paths=("high-availability", "service-discovery"),
        directories=("cluster", "clustering"),
        modules=("netauto.cluster", "netauto.discovery"),
        dependencies=("consul", "etcd", "kazoo"),
        scripts=("cluster", "service-discovery", "high-availability"),
    ),
    _policy(
        "deployment_platform::CI/CD deployment pipeline",
        basenames=(
            ".gitlab-ci.yml",
            "azure-pipelines.yml",
            "buildkite.yml",
            "jenkinsfile",
        ),
        directories=(".circleci", "workflows"),
        dependencies=("ansible-runner",),
        scripts=("deploy", "release-deploy"),
    ),
    _policy(
        "security_network::reverse-proxy or firewall automation",
        basenames=(
            "caddyfile",
            "firewall-rules.nft",
            "haproxy.cfg",
            "nginx.conf",
        ),
        directories=("firewall", "proxy"),
        dependencies=("nginx",),
        scripts=("firewall", "reverse-proxy"),
    ),
    _policy(
        "security_network::VPN or load-balancer configuration",
        basenames=("haproxy.cfg", "keepalived.conf", "vpn.conf", "wg0.conf"),
        directories=("load-balancer", "vpn"),
        dependencies=("haproxy", "wireguard"),
        scripts=("load-balancer", "vpn"),
    ),
    _policy(
        "observability::dashboards or alerting",
        basenames=("alertmanager.yml", "alertmanager.yaml", "grafana.ini"),
        directories=("dashboards", "grafana"),
        dependencies=("grafana", "prometheus-client"),
        scripts=("dashboard", "alert"),
    ),
    _policy(
        "observability::central log shipping or rotation",
        basenames=(
            "filebeat.yml",
            "fluent-bit.conf",
            "fluent.conf",
            "logrotate.conf",
            "vector.toml",
        ),
        directories=("fluent-bit", "logrotate"),
        dependencies=("fluent-logger", "python-logstash"),
        scripts=("log-ship", "log-rotate"),
    ),
)

ABSTRACT_NEGATIVE_CAPABILITY_IDS = frozenset(
    policy.identifier for policy in ABSTRACT_NEGATIVE_CAPABILITY_POLICIES
)


@dataclass(frozen=True, slots=True)
class AbstractCapabilityFinding:
    """One finite repository surface matching an abstract negative capability."""

    identifier: str
    surface: str
    value: str


def _is_normative_or_test_path(path: PurePosixPath) -> bool:
    parts = path.parts
    return (
        (bool(parts) and parts[0] == "tests")
        or parts[:2] == ("docs", "architecture")
        or (
            parts[:3] == ("docs", "milestones", "m2")
            and (
                path.name == "contract.md"
                or (len(parts) > 3 and parts[3] in {"architecture", "wip"})
            )
        )
    )


def _production_module(path: PurePosixPath) -> str | None:
    parts = path.parts
    if len(parts) < 3 or parts[:2] != ("src", "netauto") or path.suffix != ".py":
        return None
    module_parts = parts[1:-1]
    if path.stem != "__init__":
        module_parts = (*module_parts, path.stem)
    return ".".join(module_parts)


def find_abstract_capability_findings(
    paths: Iterable[str],
    *,
    dependencies: Iterable[str] = (),
    scripts: Iterable[str] = (),
) -> tuple[AbstractCapabilityFinding, ...]:
    """Audit finite implementation surfaces without grepping normative prose."""
    normalized_paths = tuple(
        PurePosixPath(normalized)
        for item in paths
        if (normalized := _normalized_path(item))
    )
    normalized_dependencies = tuple(item.lower() for item in dependencies)
    normalized_scripts = tuple(item.lower() for item in scripts)
    findings: set[AbstractCapabilityFinding] = set()
    for policy in ABSTRACT_NEGATIVE_CAPABILITY_POLICIES:
        for path in normalized_paths:
            if _is_normative_or_test_path(path):
                continue
            rendered = path.as_posix()
            module = _production_module(path)
            if (
                path.name in policy.basenames
                or any(fragment in rendered for fragment in policy.path_fragments)
                or bool(set(path.parts[:-1]) & policy.directory_parts)
                or module in policy.production_modules
            ):
                findings.add(
                    AbstractCapabilityFinding(policy.identifier, "path", rendered)
                )
        for dependency in normalized_dependencies:
            if any(token in dependency for token in policy.dependency_tokens):
                findings.add(
                    AbstractCapabilityFinding(
                        policy.identifier, "dependency", dependency
                    )
                )
        for script in normalized_scripts:
            if any(token in script for token in policy.script_tokens):
                findings.add(
                    AbstractCapabilityFinding(policy.identifier, "script", script)
                )
    return tuple(
        sorted(findings, key=lambda item: (item.identifier, item.surface, item.value))
    )


@dataclass(frozen=True, slots=True)
class AlembicMutationFinding:
    """One reachable mutating Alembic call and its bounded call path."""

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
class _ClassInfo:
    key: str
    module: str
    node: ast.ClassDef
    aliases: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class _ModuleInfo:
    name: str
    tree: ast.Module
    aliases: Mapping[str, str]
    functions: tuple[_FunctionInfo, ...]
    classes: tuple[_ClassInfo, ...]


def _nested_scope_statements(statements: Iterable[ast.stmt]) -> Iterable[ast.stmt]:
    for statement in statements:
        yield statement
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(statement, (ast.If, ast.For, ast.AsyncFor, ast.While)):
            yield from _nested_scope_statements(statement.body)
            yield from _nested_scope_statements(statement.orelse)
        elif isinstance(statement, (ast.With, ast.AsyncWith)):
            yield from _nested_scope_statements(statement.body)
        elif isinstance(statement, (ast.Try, ast.TryStar)):
            yield from _nested_scope_statements(statement.body)
            yield from _nested_scope_statements(statement.orelse)
            yield from _nested_scope_statements(statement.finalbody)
            for handler in statement.handlers:
                yield from _nested_scope_statements(handler.body)
        elif isinstance(statement, ast.Match):
            for case in statement.cases:
                yield from _nested_scope_statements(case.body)


def _absolute_import(module: str, imported: str | None, level: int) -> str:
    if level == 0:
        return imported or ""
    package = module.split(".")[:-1]
    keep = max(0, len(package) - level + 1)
    prefix = package[:keep]
    if imported:
        prefix.extend(imported.split("."))
    return ".".join(prefix)


def _scoped_import_aliases(
    statements: Iterable[ast.stmt], module: str
) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in _nested_scope_statements(statements):
        if isinstance(node, ast.Import):
            for alias in node.names:
                bound = alias.asname or alias.name.split(".", 1)[0]
                aliases[bound] = alias.name if alias.asname else bound
        elif isinstance(node, ast.ImportFrom):
            owner = _absolute_import(module, node.module, node.level)
            for alias in node.names:
                if alias.name == "*":
                    continue
                aliases[alias.asname or alias.name] = ".".join(
                    part for part in (owner, alias.name) if part
                )
    return aliases


def _scoped_definitions(statements: Iterable[ast.stmt], prefix: str) -> dict[str, str]:
    definitions: dict[str, str] = {}
    for node in _nested_scope_statements(statements):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            definitions[node.name] = f"{prefix}.{node.name}"
    return definitions


def _functions_and_classes(
    module: str, tree: ast.Module, module_aliases: Mapping[str, str]
) -> tuple[tuple[_FunctionInfo, ...], tuple[_ClassInfo, ...]]:
    functions: list[_FunctionInfo] = []
    classes: list[_ClassInfo] = []

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.owners: list[str] = []

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            key = ".".join((module, *self.owners, node.name))
            aliases = dict(module_aliases)
            aliases.update(_scoped_import_aliases(node.body, module))
            aliases.update(_scoped_definitions(node.body, key))
            classes.append(_ClassInfo(key, module, node, aliases))
            self.owners.append(node.name)
            self.generic_visit(node)
            self.owners.pop()

        def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
            key = ".".join((module, *self.owners, node.name))
            aliases = dict(module_aliases)
            aliases.update(_scoped_import_aliases(node.body, module))
            aliases.update(_scoped_definitions(node.body, key))
            functions.append(_FunctionInfo(key, module, node, aliases))
            self.owners.append(node.name)
            self.generic_visit(node)
            self.owners.pop()

        visit_FunctionDef = _visit_function
        visit_AsyncFunctionDef = _visit_function

    Visitor().visit(tree)
    return tuple(functions), tuple(classes)


def _module_info(name: str, source: str) -> _ModuleInfo:
    tree = ast.parse(source, filename=f"{name.replace('.', '/')}.py")
    aliases = _scoped_import_aliases(tree.body, name)
    aliases.update(_scoped_definitions(tree.body, name))
    functions, classes = _functions_and_classes(name, tree, aliases)
    return _ModuleInfo(name, tree, aliases, functions, classes)


def _resolve_call(
    expression: ast.expr, *, module: str, aliases: Mapping[str, str]
) -> str | None:
    if isinstance(expression, ast.Name):
        return aliases.get(expression.id, f"{module}.{expression.id}")
    if isinstance(expression, ast.Attribute):
        owner = _resolve_call(expression.value, module=module, aliases=aliases)
        return None if owner is None else f"{owner}.{expression.attr}"
    return None


class _ExecutionScanner(ast.NodeVisitor):
    def __init__(
        self,
        *,
        owner: str,
        module: str,
        aliases: Mapping[str, str],
        module_names: frozenset[str],
        function_keys: frozenset[str],
        class_keys: Mapping[int, str],
    ) -> None:
        self.owner = owner
        self.module = module
        self.aliases = aliases
        self.module_names = module_names
        self.function_keys = function_keys
        self.class_keys = class_keys
        self.direct: list[tuple[int, str]] = []
        self.edges: set[str] = set()

    def _import_edge(self, candidate: str) -> None:
        if candidate in self.module_names:
            self.edges.add(f"{candidate}.<module_init>")

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self._import_edge(alias.name)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        owner = _absolute_import(self.module, node.module, node.level)
        self._import_edge(owner)
        for alias in node.names:
            self._import_edge(".".join(part for part in (owner, alias.name) if part))

    def visit_Call(self, node: ast.Call) -> None:
        target = _resolve_call(node.func, module=self.module, aliases=self.aliases)
        if target in ALEMBIC_MUTATIONS:
            self.direct.append((node.lineno, target))
        if target in self.function_keys:
            self.edges.add(target)
        self.generic_visit(node)

    def _visit_decorator(self, expression: ast.expr) -> None:
        self.visit(expression)
        target = _resolve_call(expression, module=self.module, aliases=self.aliases)
        if target in self.function_keys:
            self.edges.add(target)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        for expression in node.decorator_list:
            self._visit_decorator(expression)
        for expression in (
            *node.args.defaults,
            *(item for item in node.args.kw_defaults if item is not None),
        ):
            self.visit(expression)
        if node.returns is not None:
            self.visit(node.returns)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        for expression in node.decorator_list:
            self._visit_decorator(expression)
        for expression in (
            *node.args.defaults,
            *(item for item in node.args.kw_defaults if item is not None),
        ):
            self.visit(expression)
        if node.returns is not None:
            self.visit(node.returns)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        for expression in node.decorator_list:
            self._visit_decorator(expression)
        for expression in node.bases:
            self.visit(expression)
        for keyword in node.keywords:
            self.visit(keyword.value)
        class_key = self.class_keys.get(id(node))
        if class_key is not None:
            self.edges.add(f"{class_key}.<class_init>")

    def visit_Lambda(self, node: ast.Lambda) -> None:
        del node


def find_reachable_alembic_mutations(
    module_sources: Mapping[str, str], root_modules: Iterable[str]
) -> tuple[AlembicMutationFinding, ...]:
    """Find Alembic mutations in import and ordinary runtime call closure."""
    infos = {
        name: _module_info(name, source) for name, source in module_sources.items()
    }
    roots = frozenset(root_modules)
    unknown_roots = roots - set(infos)
    if unknown_roots:
        raise ValueError(f"unknown root modules: {sorted(unknown_roots)!r}")

    functions = {
        function.key: function for info in infos.values() for function in info.functions
    }
    classes = {item.key: item for info in infos.values() for item in info.classes}
    class_keys = {id(item.node): item.key for item in classes.values()}
    execution: dict[str, tuple[str, str, Mapping[str, str], Sequence[ast.stmt]]] = {}
    for info in infos.values():
        execution[f"{info.name}.<module_init>"] = (
            info.name,
            f"{info.name}.<module_init>",
            info.aliases,
            info.tree.body,
        )
    for key, function in functions.items():
        execution[key] = (
            function.module,
            key,
            function.aliases,
            function.node.body,
        )
    for key, item in classes.items():
        execution[f"{key}.<class_init>"] = (
            item.module,
            f"{key}.<class_init>",
            item.aliases,
            item.node.body,
        )

    direct: dict[str, tuple[tuple[int, str], ...]] = {}
    edges: dict[str, frozenset[str]] = {}
    module_names = frozenset(infos)
    function_keys = frozenset(functions)
    for key, (module, owner, aliases, statements) in execution.items():
        scanner = _ExecutionScanner(
            owner=owner,
            module=module,
            aliases=aliases,
            module_names=module_names,
            function_keys=function_keys,
            class_keys=class_keys,
        )
        for statement in statements:
            scanner.visit(statement)
        direct[key] = tuple(scanner.direct)
        edges[key] = frozenset(child for child in scanner.edges if child in execution)

    entrypoints = sorted(
        {
            *(f"{module}.<module_init>" for module in roots),
            *(key for key, function in functions.items() if function.module in roots),
        }
    )
    findings: set[AlembicMutationFinding] = set()
    for root in entrypoints:
        queue: deque[tuple[str, tuple[str, ...]]] = deque([(root, (root,))])
        visited: set[str] = set()
        while queue:
            key, path = queue.popleft()
            if key in visited:
                continue
            visited.add(key)
            module, owner, _, _ = execution[key]
            findings.update(
                AlembicMutationFinding(module, owner, line, target, path)
                for line, target in direct[key]
            )
            queue.extend(
                (child, (*path, child)) for child in sorted(edges[key] - visited)
            )
    return tuple(
        sorted(
            findings,
            key=lambda item: (
                item.module,
                item.function,
                item.line,
                item.target,
                item.call_path,
            ),
        )
    )
