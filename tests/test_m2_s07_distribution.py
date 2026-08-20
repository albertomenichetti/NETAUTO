"""M2-VER-24 wheel, lock, and isolated installed-distribution evidence."""

from __future__ import annotations

import configparser
import email.parser
import hashlib
import json
import shutil
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from tests.support.s07_release import (
    LOCK_MEMBER,
    RELEASE_VERSION,
    ROOT,
    WHEEL_BASENAME,
    InstalledRelease,
    PtyProcess,
    applicable_locked_packages,
    isolated_environment,
    require_success,
)

COMMITTED_LOCK = ROOT / "src/netauto/release/runtime.pylock.toml"
DEV_ONLY = frozenset(
    {
        "coverage",
        "hypothesis",
        "pyright",
        "pytest",
        "pytest-asyncio",
        "pytest-timeout",
        "pytest-xdist",
        "ruff",
    }
)


def test_pty_read_until_preserves_split_needle_and_exact_tail() -> None:
    process = cast(subprocess.Popen[bytes], MagicMock(spec=subprocess.Popen))
    pty = PtyProcess(process, 123)
    with (
        patch(
            "tests.support.s07_release.select.select",
            side_effect=[([123], [], []), ([123], [], [])],
        ),
        patch(
            "tests.support.s07_release.os.read",
            side_effect=[b"netau", b"to>tail"],
        ) as read,
    ):
        assert pty.read_until(b"netauto>") == b"netauto>"

    assert read.call_count == 2
    assert bytes(pty.pending) == b"tail"
    assert pty.read_until(b"tail") == b"tail"
    assert pty.pending == bytearray()


def test_installed_server_import_and_factory_are_independent_from_cli(
    s07_release: InstalledRelease,
) -> None:
    script = """
import builtins
import json
import socket
import sys
from importlib.metadata import version
from pathlib import Path

real_import = builtins.__import__
rejected_imports = []
def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name == "netauto.cli" or name.startswith("netauto.cli."):
        rejected_imports.append(name)
        raise AssertionError(f"server imported forbidden CLI module: {name}")
    return real_import(name, globals, locals, fromlist, level)
builtins.__import__ = guarded_import

network_attempts = 0
def reject_connect(*args, **kwargs):
    global network_attempts
    network_attempts += 1
    raise AssertionError("app construction attempted network I/O")
socket.socket.connect = reject_connect

from netauto.entrypoints.http import build_app
from netauto.settings import Settings

app = build_app(
    Settings(
        database_url=(
            "postgresql+psycopg://installed-server-guard:"
            "non-secret@example.invalid/netauto"
        )
    )
)
schema = app.openapi()
operations = sorted(
    (method.upper(), path)
    for path, path_item in schema["paths"].items()
    for method in path_item
    if method in {"get", "post", "put", "patch", "delete"}
)
print(json.dumps({
    "version": version("netauto"),
    "module_path": str(Path(sys.modules["netauto"].__file__).resolve()),
    "cwd": str(Path.cwd().resolve()),
    "operation_count": len(operations),
    "path_count": len(schema["paths"]),
    "has_health": ("GET", "/health/core") in operations,
    "has_business_read": (
        "GET", "/api/v1/core/datatypes"
    ) in operations,
    "has_business_mutation": (
        "POST", "/api/v1/core/datatypes"
    ) in operations,
    "cli_modules": sorted(
        name for name in sys.modules
        if name == "netauto.cli" or name.startswith("netauto.cli.")
    ),
    "rejected_imports": rejected_imports,
    "network_attempts": network_attempts,
}, sort_keys=True))
"""
    result = s07_release.run([str(s07_release.python), "-c", script])
    require_success(result)
    assert result.stderr == ""
    assert len(result.stdout) < 4_000
    payload = json.loads(result.stdout)
    assert payload == {
        "cli_modules": [],
        "cwd": str(s07_release.target_root.resolve()),
        "has_business_mutation": True,
        "has_business_read": True,
        "has_health": True,
        "module_path": payload["module_path"],
        "network_attempts": 0,
        "operation_count": 64,
        "path_count": 52,
        "rejected_imports": [],
        "version": RELEASE_VERSION,
    }
    module_path = Path(payload["module_path"])
    assert s07_release.venv.resolve() in module_path.parents
    assert ROOT.resolve() not in module_path.parents


def test_candidate_wheel_has_exact_version_content_entrypoint_and_exclusions(
    s07_release: InstalledRelease,
) -> None:
    assert s07_release.wheel.name == WHEEL_BASENAME
    assert len(s07_release.wheel_sha256) == 64
    assert s07_release.wheel.stat().st_size > COMMITTED_LOCK.stat().st_size

    with zipfile.ZipFile(s07_release.wheel) as archive:
        names = archive.namelist()
        assert len(names) == len(set(names))
        assert names.count(LOCK_MEMBER) == 1
        assert archive.read(LOCK_MEMBER) == COMMITTED_LOCK.read_bytes()
        assert hashlib.sha256(archive.read(LOCK_MEMBER)).hexdigest() == (
            "0114d64cb078cfe3271e974d4aad86628d633d0fbdbcbece37ff3bc8873ddaaf"
        )
        required = {
            "netauto/release/__init__.py",
            "netauto/migrations/__init__.py",
            "netauto/migrations/env.py",
            "netauto/migrations/script.py.mako",
            "netauto/migrations/versions/__init__.py",
            "netauto/migrations/versions/0001_m2_durable_kernel.py",
            "netauto/runtime/schema_guard.py",
            "netauto/entrypoints/http.py",
            "netauto/cli/main.py",
            "netauto/transport/http/health.py",
            "netauto-0.2.0.dist-info/METADATA",
            "netauto-0.2.0.dist-info/entry_points.txt",
            "netauto-0.2.0.dist-info/RECORD",
        }
        assert required <= set(names)
        revisions = tuple(
            name
            for name in names
            if name.startswith("netauto/migrations/versions/")
            and name.endswith(".py")
            and not name.endswith("/__init__.py")
        )
        assert revisions == ("netauto/migrations/versions/0001_m2_durable_kernel.py",)
        forbidden_parts = {
            "tests",
            "docs",
            ".git",
            ".github",
            ".venv",
            "__pycache__",
        }
        assert all(not (set(Path(name).parts) & forbidden_parts) for name in names)
        forbidden_names = {
            "pyproject.toml",
            "uv.lock",
            "alembic.ini",
            "Dockerfile",
            "docker-compose.yml",
        }
        assert all(Path(name).name not in forbidden_names for name in names)
        assert not any(
            name.endswith((".pem", ".key", ".crt", ".pyc")) for name in names
        )

        metadata = email.parser.BytesParser().parsebytes(
            archive.read("netauto-0.2.0.dist-info/METADATA")
        )
        assert metadata["Name"] == "netauto"
        assert metadata["Version"] == RELEASE_VERSION
        parser = configparser.ConfigParser()
        parser.read_string(
            archive.read("netauto-0.2.0.dist-info/entry_points.txt").decode()
        )
        assert dict(parser["console_scripts"]) == {"netauto": "netauto.cli.main:main"}


def test_committed_runtime_lock_is_exact_runtime_only_regenerated_export(
    tmp_path: Path,
) -> None:
    shutil.copyfile(ROOT / "pyproject.toml", tmp_path / "pyproject.toml")
    shutil.copyfile(ROOT / "uv.lock", tmp_path / "uv.lock")
    regenerated = tmp_path / "src/netauto/release/pylock.runtime.toml"
    regenerated.parent.mkdir(parents=True)
    completed = subprocess.run(
        [
            "uv",
            "export",
            "--frozen",
            "--no-dev",
            "--no-emit-project",
            "--format",
            "pylock.toml",
            "--output-file",
            "src/netauto/release/pylock.runtime.toml",
        ],
        cwd=tmp_path,
        env=isolated_environment(),
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    require_success(completed)
    assert regenerated.read_bytes() == COMMITTED_LOCK.read_bytes()
    parsed = tomllib.loads(COMMITTED_LOCK.read_text())
    assert parsed["lock-version"] == "1.0"
    assert parsed["requires-python"] == "==3.14.*"
    packages = cast(list[dict[str, object]], parsed["packages"])
    assert len(packages) == 29
    assert all(isinstance(package.get("name"), str) for package in packages)
    names = {cast(str, package["name"]) for package in packages}
    assert "netauto" not in names
    assert names.isdisjoint(DEV_ONLY)
    lock_text = COMMITTED_LOCK.read_text()
    assert "file:///" not in lock_text
    assert "editable" not in lock_text
    assert str(ROOT) not in lock_text


@pytest.mark.slow
def test_clean_release_sync_and_no_deps_install_are_exact_and_source_isolated(
    s07_release: InstalledRelease,
) -> None:
    listed = s07_release.run(
        [
            "uv",
            "pip",
            "list",
            "--python",
            str(s07_release.python),
            "--format",
            "json",
        ]
    )
    require_success(listed)
    installed = {
        item["name"].lower(): item["version"] for item in json.loads(listed.stdout)
    }
    expected = applicable_locked_packages(s07_release.runtime_lock)
    assert installed.pop("netauto") == RELEASE_VERSION
    assert installed == expected
    assert set(installed).isdisjoint(DEV_ONLY)
    assert s07_release.runtime_lock.read_bytes() == COMMITTED_LOCK.read_bytes()
    assert all(
        path.is_file()
        for path in (s07_release.netauto, s07_release.uvicorn, s07_release.alembic)
    )

    probe = s07_release.run(
        [
            str(s07_release.python),
            "-c",
            ";".join(
                (
                    "import importlib.metadata as m",
                    "import json,pathlib,sys",
                    "import netauto",
                    "import netauto.cli.main",
                    "import netauto.entrypoints.http",
                    "import netauto.migrations",
                    "import netauto.persistence.engine",
                    "import netauto.release",
                    "import netauto.runtime.schema_guard",
                    "print(json.dumps({'version':m.version('netauto'),"
                    "'root':str(pathlib.Path(netauto.__file__).resolve()),"
                    "'paths':[str(pathlib.Path(v.__file__).resolve()) for k,v in "
                    "sys.modules.items() if k.startswith('netauto') and "
                    "getattr(v,'__file__',None)]}))",
                )
            ),
        ]
    )
    require_success(probe)
    evidence = json.loads(probe.stdout)
    assert evidence["version"] == RELEASE_VERSION
    assert Path(evidence["root"]).is_relative_to(s07_release.venv)
    assert all(
        Path(path).is_relative_to(s07_release.venv) for path in evidence["paths"]
    )
    assert not any(str(ROOT) in path for path in evidence["paths"])
    assert s07_release.target_root.resolve() != ROOT.resolve()
    assert sys.version_info[:2] == (3, 14)


def test_installed_cli_import_boundary_and_user_agent_use_distribution_version(
    s07_release: InstalledRelease,
) -> None:
    completed = s07_release.run(
        [
            str(s07_release.python),
            "-c",
            "\n".join(
                (
                    "import asyncio, json, sys, httpx",
                    "from netauto.cli.execution import execute",
                    "from netauto.cli.parser import parse_process",
                    "seen = {}",
                    "def handler(request):",
                    "    seen['user_agent'] = request.headers['user-agent']",
                    "    return httpx.Response(200, json={'items': [], "
                    "'next_cursor': None})",
                    "async def main():",
                    "    endpoint, command, spec = parse_process(['-n', "
                    "'http://example.test', 'datatype', 'list'])",
                    "    result = await execute(endpoint, command, spec, "
                    "http_transport=httpx.MockTransport(handler))",
                    "    forbidden = sorted(name for name in sys.modules if "
                    "name.startswith(('netauto.settings','netauto.persistence',"
                    "'sqlalchemy','psycopg','alembic'))) ",
                    "    print(json.dumps({'status': result.status, "
                    "'user_agent': seen['user_agent'], 'forbidden': forbidden}))",
                    "asyncio.run(main())",
                )
            ),
        ]
    )
    require_success(completed)
    evidence = json.loads(completed.stdout)
    assert evidence == {
        "status": "ok",
        "user_agent": "netauto/0.2.0",
        "forbidden": [],
    }
