"""Executed Linux release procedure, process lifecycle, Health, and CLI evidence."""

from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import ClassVar

import pytest
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url

from tests.support.s07_release import (
    ROOT,
    InstalledRelease,
    TCPForwarder,
    free_port,
    http_get,
    installed_alembic,
    listener_open,
    process_output,
    require_success,
    sanitize,
    spawn_installed_pty,
    start_uvicorn,
    terminate_orderly,
    wait_for_http,
    write_secret_directory,
)

OPERATING_GUIDE = ROOT / "docs/milestones/M2/linux-operating-baseline.md"


class PublicReadHandler(BaseHTTPRequestHandler):
    paths: ClassVar[list[str]] = []
    user_agents: ClassVar[list[str]] = []

    def do_GET(self) -> None:
        self.paths.append(self.path)
        self.user_agents.append(self.headers["User-Agent"])
        assert self.path == "/api/v1/core/datatypes?limit=2"
        body = json.dumps({"items": [], "next_cursor": None}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        del format, args


def _sentinel_url(database_url: str, sentinel: str) -> str:
    return (
        make_url(database_url)
        .update_query_dict({"application_name": sentinel})
        .render_as_string(hide_password=False)
    )


def _heads(engine: Engine) -> tuple[str, ...]:
    with engine.connect() as connection:
        return tuple(MigrationContext.configure(connection).get_current_heads())


def _session_count(observer: Engine, application_name: str) -> int:
    with observer.connect() as connection:
        value = connection.execute(
            text(
                "SELECT count(*) FROM pg_stat_activity "
                "WHERE application_name = :application_name"
            ),
            {"application_name": application_name},
        ).scalar_one()
    assert isinstance(value, int)
    return value


def _wait_for_no_session(observer: Engine, application_name: str) -> None:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if _session_count(observer, application_name) == 0:
            return
        time.sleep(0.05)
    raise AssertionError("installed worker retained its dedicated PostgreSQL session")


def _require_failed_start(
    process: subprocess.Popen[str],
    port: int,
    *,
    secrets: tuple[str, ...],
) -> str:
    output = process_output(process, timeout=20)
    assert process.returncode not in (None, 0), sanitize(output, secrets)
    assert not listener_open(port)
    for secret in secrets:
        assert secret not in output
    assert len(output) < 20_000
    return output


def test_linux_operator_document_is_exact_bounded_and_has_no_hidden_facility() -> None:
    document = OPERATING_GUIDE.read_text()
    required = {
        "netauto-0.2.0-py3-none-any.whl",
        "/opt/netauto/releases/0.2.0",
        "CPython 3.14.x",
        "uv pip sync",
        "--no-deps",
        "--output-file src/netauto/release/pylock.runtime.toml",
        "cmp src/netauto/release/pylock.runtime.toml",
        'sudo install -d -o "$NETAUTO_USER" -g "$NETAUTO_GROUP" -m 0755 /opt/netauto',
        'sudo -u "$NETAUTO_USER" install -d -m 0755 /opt/netauto/releases',
        "/opt/netauto/releases/0.2.0/.venv/bin/python -",
        "ln -s releases/0.2.0 /opt/netauto/.current-0.2.0",
        "mv -T /opt/netauto/.current-0.2.0 /opt/netauto/current",
        'test "$(readlink /opt/netauto/current)" = "releases/0.2.0"',
        "script_location = netauto:migrations",
        "path_separator = os",
        "NETAUTO_SECRETS_DIR=/opt/netauto/secrets",
        "--host 127.0.0.1",
        "--workers 1",
        "GET /health/core",
        "engine.dispose()",
        "workers * (pool_size + max_overflow)",
        "1 worker = 10 + 20 = 30",
        "HTTP is supported only",
        "externally managed TLS termination",
        "no CLI insecure or skip-verify mode",
        "solely in `database_url`",
        "Docker or Kubernetes",
        "systemd or another process manager",
        "rolling or zero-downtime",
        "backup or restore",
    }
    assert all(item in document for item in required)
    assert "0700" in document and "0600" in document
    assert "sqlalchemy.url =" not in document
    assert "postgresql+psycopg://" not in document
    assert "NETAUTO_DATABASE_URL=" not in document
    assert "python3.14 -" not in document
    assert "--host 0.0.0.0" not in document
    assert "--insecure" not in document
    assert "verify=false" not in document.lower()
    assert "--skip-verify" not in document.lower()
    assert "docker run" not in document.lower()
    assert "systemctl" not in document.lower()
    assert "netauto migrate" not in document.lower()
    assert document.index("upgrade head") < document.index(
        "ln -s releases/0.2.0 /opt/netauto/.current-0.2.0"
    )
    assert document.index("mv -T /opt/netauto/.current-0.2.0") < document.index(
        "## Foreground start"
    )


@pytest.mark.skipif(sys.platform != "linux", reason="T9 PTY evidence is Linux-owned")
@pytest.mark.slow
def test_installed_cli_local_repl_and_noninteractive_http_need_no_database(
    s07_release: InstalledRelease,
) -> None:
    pty = spawn_installed_pty(s07_release)
    try:
        pty.read_until(b"netauto>")
        pty.write(b"/status\r")
        status = pty.read_until(b"DISCONNECTED")
        assert b"DISCONNECTED" in status
        status += pty.read_until(b"netauto>")
        assert b"FORMATTED" in status
        pty.write(b"/help\r")
        help_output = pty.read_until(b"/connect <endpoint-root>")
        help_output += pty.read_until(b"netauto>")
        assert b"/connect <endpoint-root>" in help_output
        pty.write(b"\x04")
        assert pty.process.wait(timeout=10) == 0
    finally:
        pty.close()

    PublicReadHandler.paths = []
    PublicReadHandler.user_agents = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), PublicReadHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = s07_release.run(
            [
                str(s07_release.netauto),
                "-n",
                f"http://127.0.0.1:{server.server_port}",
                "datatype",
                "list",
                "limit=2",
            ]
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    require_success(result)
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["result"] == {"items": [], "next_cursor": None}
    assert PublicReadHandler.paths == ["/api/v1/core/datatypes?limit=2"]
    assert PublicReadHandler.user_agents == ["netauto/0.2.0"]
    assert "/health/core" not in PublicReadHandler.paths


@pytest.mark.postgresql
@pytest.mark.migration
@pytest.mark.slow
@pytest.mark.timeout(180)
def test_installed_server_migration_start_health_cli_stop_restart_and_mismatch(
    s07_release: InstalledRelease,
    test_database_url: str,
    tmp_path: Path,
) -> None:
    sentinel = f"m2-s07-secret-{uuid.uuid4().hex}"
    database_url = _sentinel_url(test_database_url, sentinel)
    secrets_dir = write_secret_directory(tmp_path, database_url)
    observer = create_engine(test_database_url)
    revision_engine = create_engine(test_database_url)
    active: subprocess.Popen[str] | None = None
    try:
        down = installed_alembic(s07_release, secrets_dir, "downgrade", "base")
        require_success(down, secrets=(database_url, sentinel))
        assert _heads(revision_engine) == ()

        before_port = free_port()
        active = start_uvicorn(s07_release, before_port, secrets_dir)
        before_output = _require_failed_start(
            active,
            before_port,
            secrets=(database_url, sentinel, str(secrets_dir)),
        )
        active = None
        assert "revision mismatch" in before_output.lower()
        assert _heads(revision_engine) == ()

        up = installed_alembic(s07_release, secrets_dir, "upgrade", "head")
        require_success(up, secrets=(database_url, sentinel))
        assert _heads(revision_engine) == ("0001_m2_kernel",)

        first_port = free_port()
        active = start_uvicorn(s07_release, first_port, secrets_dir)
        health, headers = wait_for_http(f"http://127.0.0.1:{first_port}/health/core")
        assert health["app_status"] == {"status": "ok"}
        assert health["db_status"] == {"status": "ok"}
        assert headers["Cache-Control"] == "no-store"
        status, business, _ = http_get(
            f"http://127.0.0.1:{first_port}/api/v1/core/datatypes?limit=1"
        )
        assert status == 200
        assert business == {"items": [], "next_cursor": None}
        assert _session_count(observer, sentinel) >= 1

        noninteractive = s07_release.run(
            [
                str(s07_release.netauto),
                "-n",
                f"http://127.0.0.1:{first_port}",
                "datatype",
                "list",
                "limit=1",
            ]
        )
        require_success(noninteractive, secrets=(database_url, sentinel))
        assert json.loads(noninteractive.stdout)["status"] == "ok"

        first_stdout, first_stderr = terminate_orderly(
            active, secrets=(database_url, sentinel)
        )
        active = None
        assert "NETAUTO process stopping" in first_stdout + first_stderr
        assert sentinel not in first_stdout + first_stderr
        _wait_for_no_session(observer, sentinel)
        assert not listener_open(first_port)

        second_port = free_port()
        active = start_uvicorn(s07_release, second_port, secrets_dir)
        restarted, _ = wait_for_http(f"http://127.0.0.1:{second_port}/health/core")
        assert restarted["db_status"] == {"status": "ok"}

        pty = spawn_installed_pty(s07_release)
        try:
            pty.read_until(b"netauto>")
            pty.write(f"/connect http://127.0.0.1:{second_port}\r".encode())
            connected = pty.read_until(b"CONNECTED")
            assert b"CONNECTED" in connected
            pty.read_until(b"netauto>")
            pty.write(b"/status\r")
            revalidated = pty.read_until(b"CONNECTED")
            assert b"CONNECTED" in revalidated
            pty.read_until(b"netauto>")
            pty.write(b"datatype list limit=1\r")
            formatted = pty.read_until(b"command: datatype list")
            assert b"command: datatype list" in formatted
            pty.read_until(b"netauto>")
            pty.write(b"/output JSON\r")
            pty.read_until(b'"output":"JSON"')
            pty.read_until(b"netauto>")
            pty.write(b"datatype list limit=1\r")
            json_result = pty.read_until(b'"status":"ok"')
            assert b'"status":"ok"' in json_result
            pty.read_until(b"netauto>")
            pty.write(b"/exit\r")
            assert pty.process.wait(timeout=10) == 0
        finally:
            pty.close()

        terminate_orderly(active, secrets=(database_url, sentinel))
        active = None
        _wait_for_no_session(observer, sentinel)

        with revision_engine.begin() as connection:
            connection.execute(text("DELETE FROM alembic_version"))
            connection.execute(
                text("INSERT INTO alembic_version (version_num) VALUES (:value)"),
                {"value": "unknown_revision"},
            )
        mismatch_port = free_port()
        active = start_uvicorn(s07_release, mismatch_port, secrets_dir)
        mismatch = _require_failed_start(
            active,
            mismatch_port,
            secrets=(database_url, sentinel, str(secrets_dir)),
        )
        active = None
        assert "revision mismatch" in mismatch.lower()
        assert _heads(revision_engine) == ("unknown_revision",)
        with revision_engine.begin() as connection:
            connection.execute(text("DELETE FROM alembic_version"))
            connection.execute(
                text("INSERT INTO alembic_version (version_num) VALUES (:value)"),
                {"value": "0001_m2_kernel"},
            )
    finally:
        if active is not None and active.poll() is None:
            active.terminate()
            active.wait(timeout=10)
        restored = installed_alembic(s07_release, secrets_dir, "downgrade", "base")
        assert restored.returncode == 0, sanitize(
            restored.stdout + restored.stderr, (database_url, sentinel)
        )
        observer.dispose()
        revision_engine.dispose()


@pytest.mark.postgresql
@pytest.mark.migration
@pytest.mark.slow
@pytest.mark.timeout(120)
def test_installed_worker_returns_complete_503_when_real_pg_transport_is_cut(
    s07_release: InstalledRelease,
    test_database_url: str,
    tmp_path: Path,
) -> None:
    parsed = make_url(test_database_url)
    upstream_host = parsed.host
    if upstream_host is None:
        query_host = parsed.query.get("host")
        upstream_host = query_host if isinstance(query_host, str) else None
    if upstream_host is None or upstream_host.startswith("/"):
        pytest.fail(
            "TEST_DATABASE_URL does not expose a TCP PostgreSQL host required "
            "for deterministic T9 transport-cut evidence"
        )
    upstream_port = parsed.port or 5432
    sentinel = f"m2-s07-secret-{uuid.uuid4().hex}"
    direct_url = _sentinel_url(test_database_url, sentinel)
    direct_secrets = write_secret_directory(tmp_path / "direct", direct_url)
    process: subprocess.Popen[str] | None = None
    try:
        down = installed_alembic(s07_release, direct_secrets, "downgrade", "base")
        require_success(down, secrets=(direct_url, sentinel))
        up = installed_alembic(s07_release, direct_secrets, "upgrade", "head")
        require_success(up, secrets=(direct_url, sentinel))

        with TCPForwarder(upstream_host, upstream_port) as forwarder:
            forwarded = parsed.difference_update_query(["host", "port"])
            forwarded = forwarded.set(host="127.0.0.1", port=forwarder.port)
            forwarded = forwarded.update_query_dict({"application_name": sentinel})
            forwarded_url = forwarded.render_as_string(hide_password=False)
            proxy_secrets = write_secret_directory(tmp_path / "proxy", forwarded_url)
            port = free_port()
            process = start_uvicorn(s07_release, port, proxy_secrets)
            ready, _ = wait_for_http(f"http://127.0.0.1:{port}/health/core")
            assert ready["db_status"] == {"status": "ok"}
            forwarder.cut()
            unavailable, headers = wait_for_http(
                f"http://127.0.0.1:{port}/health/core", expected_status=503
            )
            assert process.poll() is None
            assert unavailable["app_status"] == {"status": "ok"}
            db_status = unavailable["db_status"]
            assert isinstance(db_status, dict)
            assert db_status["status"] == "error"
            assert db_status["message"] == "database readiness check failed"
            assert isinstance(unavailable["execution_time_ms"], int)
            assert headers["Cache-Control"] == "no-store"
            serialized = json.dumps(unavailable)
            assert sentinel not in serialized
            assert direct_url not in serialized
            terminate_orderly(process, secrets=(direct_url, forwarded_url, sentinel))
            process = None
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
        restored = installed_alembic(s07_release, direct_secrets, "downgrade", "base")
        assert restored.returncode == 0, sanitize(
            restored.stdout + restored.stderr, (direct_url, sentinel)
        )
