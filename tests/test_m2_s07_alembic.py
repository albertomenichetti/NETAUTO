"""Installed package-resource Alembic and explicit real-PG evidence for S07."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine, make_url

from tests.support.s07_release import (
    ROOT,
    InstalledRelease,
    installed_alembic,
    require_success,
    sanitize,
    write_secret_directory,
)

EXPECTED_TABLES = {
    "alembic_version",
    "datatypes",
    "datatype_versions",
    "object_templates",
    "object_template_versions",
    "object_template_properties",
    "object_template_components",
    "relationship_definitions",
    "relationship_resolutions",
    "relationship_definition_versions",
    "relationship_definition_properties",
    "objects",
    "object_components",
    "relationships",
    "runtime_relationship_resolutions",
    "object_lifecycle_events",
}


def _sentinel_url(database_url: str, sentinel: str) -> str:
    return (
        make_url(database_url)
        .update_query_dict({"application_name": sentinel})
        .render_as_string(hide_password=False)
    )


def _heads(engine: Engine) -> tuple[str, ...]:
    with engine.connect() as connection:
        return tuple(MigrationContext.configure(connection).get_current_heads())


def test_installed_distribution_discovers_exact_single_package_resource_graph(
    s07_release: InstalledRelease,
) -> None:
    probe = s07_release.run(
        [
            str(s07_release.python),
            "-c",
            "\n".join(
                (
                    "import json, pathlib",
                    "from alembic.config import Config",
                    "from alembic.script import ScriptDirectory",
                    "from importlib.resources import files",
                    "from netauto.runtime.schema_guard import "
                    "discover_unique_shipped_head",
                    "cfg=Config()",
                    "cfg.set_main_option('script_location','netauto:migrations')",
                    "script=ScriptDirectory.from_config(cfg)",
                    "root=files('netauto.migrations')",
                    "revisions=sorted(p.name for p in "
                    "root.joinpath('versions').iterdir() if p.name.endswith('.py') "
                    "and p.name != '__init__.py')",
                    "print(json.dumps({'bases':script.get_bases(),"
                    "'heads':script.get_heads(),"
                    "'discovered':discover_unique_shipped_head(),"
                    "'template':root.joinpath('script.py.mako').is_file(),"
                    "'revisions':revisions,'root':str(root)}))",
                )
            ),
        ]
    )
    require_success(probe)
    evidence = json.loads(probe.stdout)
    assert evidence["bases"] == ["0001_m2_kernel"]
    assert evidence["heads"] == ["0001_m2_kernel"]
    assert evidence["discovered"] == "0001_m2_kernel"
    assert evidence["template"] is True
    assert evidence["revisions"] == ["0001_m2_durable_kernel.py"]
    assert Path(evidence["root"]).is_relative_to(s07_release.venv)
    assert not Path(evidence["root"]).is_relative_to(ROOT)

    config = s07_release.alembic_ini.read_text()
    assert config == (
        "[alembic]\nscript_location = netauto:migrations\npath_separator = os\n"
    )
    assert "sqlalchemy.url" not in config
    assert "0001_m2_kernel" not in config
    assert str(ROOT) not in config


def test_root_revision_payload_checksum_is_unchanged_from_s07_baseline() -> None:
    revision = ROOT / ("src/netauto/migrations/versions/0001_m2_durable_kernel.py")
    assert hashlib.sha256(revision.read_bytes()).hexdigest() == (
        "379165a1eda83c226a6c1e5dc4f493c7fa0d0c8dba39449a1d004751aaa39c57"
    )


@pytest.mark.postgresql
@pytest.mark.migration
@pytest.mark.slow
@pytest.mark.timeout(120)
def test_installed_alembic_explicitly_realizes_exact_schema_without_cli_cross_action(
    s07_release: InstalledRelease,
    test_database_url: str,
    tmp_path: Path,
) -> None:
    sentinel = f"m2-s07-secret-{uuid.uuid4().hex}"
    database_url = _sentinel_url(test_database_url, sentinel)
    secrets_dir = write_secret_directory(tmp_path, database_url)
    assert (secrets_dir.stat().st_mode & 0o777) == 0o700
    assert ((secrets_dir / "NETAUTO_DATABASE_URL").stat().st_mode & 0o777) == 0o600
    engine = create_engine(test_database_url)
    try:
        downgraded = installed_alembic(s07_release, secrets_dir, "downgrade", "base")
        require_success(downgraded, secrets=(database_url, sentinel))
        assert _heads(engine) == ()

        local_cli = s07_release.run(
            [str(s07_release.netauto), "--unsupported"], timeout=10
        )
        assert local_cli.returncode == 1
        assert "cli_invalid_invocation" in local_cli.stdout
        assert _heads(engine) == ()

        upgraded = installed_alembic(s07_release, secrets_dir, "upgrade", "head")
        require_success(upgraded, secrets=(database_url, sentinel))
        assert _heads(engine) == ("0001_m2_kernel",)
        assert set(inspect(engine).get_table_names()) == EXPECTED_TABLES
        assert sentinel not in upgraded.stdout + upgraded.stderr
        assert database_url not in upgraded.stdout + upgraded.stderr
        assert "sqlalchemy.url" not in s07_release.alembic_ini.read_text()
        assert os.environ.get("NETAUTO_DATABASE_URL") != database_url
    finally:
        restored = installed_alembic(s07_release, secrets_dir, "downgrade", "base")
        assert restored.returncode == 0, sanitize(
            restored.stdout + restored.stderr, (database_url, sentinel)
        )
        engine.dispose()
