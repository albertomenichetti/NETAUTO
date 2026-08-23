"""Static negative and unchanged-boundary evidence for M2-S04."""

import ast
from pathlib import Path

from netauto.settings import Settings

ROOT = Path(__file__).parents[1]


def _source(relative: str) -> str:
    return (ROOT / relative).read_text()


def test_s04_runtime_and_health_have_no_forbidden_parallel_mechanisms() -> None:
    runtime = _source("src/netauto/runtime/schema_guard.py")
    health = "\n".join(
        _source(relative)
        for relative in (
            "src/netauto/application/health.py",
            "src/netauto/persistence/health.py",
            "src/netauto/entrypoints/api/health.py",
        )
    )
    assert "0001_m2_kernel" not in runtime
    assert "alembic.command" not in runtime
    assert all(
        fragment not in runtime
        for fragment in (
            "command.upgrade",
            "command.stamp",
            "CREATE TABLE",
            "ALTER TABLE",
        )
    )
    assert all(
        fragment not in health
        for fragment in (
            "UnitOfWork",
            "MigrationContext",
            "alembic",
            "create_async_engine",
            "retry",
            "backoff",
            "cache",
            "NETAUTO_DATABASE_URL",
        )
    )


def test_health_route_reads_only_precomposed_service() -> None:
    tree = ast.parse(_source("src/netauto/entrypoints/api/health.py"))
    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert not ({"Settings", "load_settings", "build_runtime_context"} & calls)


def test_s04_adds_no_cli_domain_schema_migration_or_dependency_surface() -> None:
    assert not (ROOT / "src/netauto/domain/health.py").exists()
    assert not (ROOT / "src/netauto/entrypoints/cli.py").exists()
    assert tuple(Settings.model_fields) == (
        "database_url",
        "log_level",
        "pool_size",
        "max_overflow",
        "pool_timeout",
        "pool_recycle",
        "pool_pre_ping",
    )
    migration_versions = sorted(
        path.name
        for path in (ROOT / "src/netauto/migrations/versions").glob("*.py")
        if path.name != "__init__.py"
    )
    assert migration_versions == ["0001_m2_durable_kernel.py"]
