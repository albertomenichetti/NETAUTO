"""Bounded installed-wheel smoke owned by M2-S04."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import Engine

ROOT = Path(__file__).parents[1]


@pytest.mark.postgresql
@pytest.mark.slow
def test_installed_wheel_s04_runtime_smoke(
    tmp_path: Path,
    migrated_database_engine: Engine,
    test_database_url: str,
) -> None:
    del migrated_database_engine
    wheel_dir = tmp_path / "wheels"
    wheel_dir.mkdir()
    build = subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(wheel_dir)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert build.returncode == 0, build.stdout + build.stderr
    wheels = tuple(wheel_dir.glob("*.whl"))
    assert len(wheels) == 1

    installed = tmp_path / "installed"
    install = subprocess.run(
        [
            "uv",
            "pip",
            "install",
            "--python",
            sys.executable,
            "--target",
            str(installed),
            "--no-deps",
            str(wheels[0]),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert install.returncode == 0, install.stdout + install.stderr

    script = r"""
import pathlib
import socket
from unittest.mock import patch

import netauto
import netauto.entrypoints.http as http_module
from fastapi.testclient import TestClient
from netauto.entrypoints.http import build_app, create_app
from netauto.runtime.schema_guard import (
    SchemaRevisionMismatch,
    discover_unique_shipped_head,
)
from netauto.settings import Settings

installed = pathlib.Path(__import__('os').environ['S04_INSTALLED_ROOT']).resolve()
assert pathlib.Path(netauto.__file__).resolve().is_relative_to(installed)
assert discover_unique_shipped_head()

with patch.object(
    socket.socket,
    'connect',
    side_effect=AssertionError('factory network I/O'),
):
    factory_app = create_app()
    assert '/health/core' in factory_app.openapi()['paths']

database_url = __import__('os').environ['TEST_DATABASE_URL']
original_build_runtime_context = http_module.build_runtime_context
original_guard = http_module.require_exact_schema_revision
calls = {'runtime': 0, 'guard': 0}

def counting_runtime(settings):
    calls['runtime'] += 1
    return original_build_runtime_context(settings)

async def counting_guard(engine):
    calls['guard'] += 1
    await original_guard(engine)

http_module.build_runtime_context = counting_runtime
http_module.require_exact_schema_revision = counting_guard
healthy = build_app(
    Settings(
        database_url=database_url,
        pool_size=1,
        max_overflow=0,
        pool_timeout=5.0,
    )
)
with TestClient(healthy) as client:
    response = client.get('/health/core')
    assert response.status_code == 200
    assert response.json()['db_status'] == {'status': 'ok'}
    assert response.headers['cache-control'] == 'no-store'
    runtime_engine = healthy.state.runtime.engine
    assert calls == {'runtime': 1, 'guard': 1}

    held_connection = client.portal.call(runtime_engine.connect)
    try:
        unavailable = client.get('/health/core')
    finally:
        client.portal.call(held_connection.close)

    assert unavailable.status_code == 503
    assert unavailable.headers['cache-control'] == 'no-store'
    unavailable_body = unavailable.json()
    assert unavailable_body['app_status'] == {'status': 'ok'}
    assert unavailable_body['db_status'] == {
        'status': 'error',
        'message': 'database readiness check timed out',
    }
    assert type(unavailable_body['execution_time_ms']) is int
    assert healthy.state.runtime.engine is runtime_engine
    assert calls == {'runtime': 1, 'guard': 1}

    recovered = client.get('/health/core')
    assert recovered.status_code == 200
    assert recovered.headers['cache-control'] == 'no-store'
    assert recovered.json()['db_status'] == {'status': 'ok'}
    assert healthy.state.runtime.engine is runtime_engine
    assert calls == {'runtime': 1, 'guard': 1}

async def reject(_engine):
    raise SchemaRevisionMismatch('controlled mismatch')

http_module.require_exact_schema_revision = reject
failed = build_app(Settings(database_url=database_url))
try:
    with TestClient(failed):
        raise AssertionError('failed guard entered serving')
except SchemaRevisionMismatch:
    pass
"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(installed)
    environment["S04_INSTALLED_ROOT"] = str(installed)
    environment["TEST_DATABASE_URL"] = test_database_url
    environment["NETAUTO_DATABASE_URL"] = test_database_url
    smoke = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    safe_output = (smoke.stdout + smoke.stderr).replace(
        test_database_url, "<TEST_DATABASE_URL>"
    )
    assert smoke.returncode == 0, safe_output
