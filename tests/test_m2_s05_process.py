"""Installed console-process stdout/stderr/exit and HTTP-only evidence."""

import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import ClassVar

import pytest

ROOT = Path(__file__).parents[1]


class Handler(BaseHTTPRequestHandler):
    requests = 0

    def do_GET(self) -> None:
        type(self).requests += 1
        body = json.dumps({"items": [], "next_cursor": None}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        del format, args


class ScenarioHandler(BaseHTTPRequestHandler):
    mode = "selector"
    paths: ClassVar[list[str]] = []

    def do_GET(self) -> None:
        type(self).paths.append(self.path)
        payload: dict[str, object]
        if self.mode == "selector" and self.path.startswith("/api/v1/core/datatypes?"):
            status = 200
            payload = {
                "items": [
                    {
                        "id": "11111111-1111-1111-1111-111111111111",
                        "namespace": "core",
                        "name": "string",
                        "description": None,
                        "default_version": 1,
                    }
                ],
                "next_cursor": None,
            }
        elif self.mode == "selector":
            status = 200
            payload = {
                "id": "11111111-1111-1111-1111-111111111111",
                "namespace": "core",
                "name": "string",
                "description": None,
                "default_version": 1,
            }
        elif self.mode == "remote":
            status = 404
            payload = {
                "code": "resource_not_found",
                "message": "The resource was not found.",
                "details": {},
            }
        else:
            status = 200
            payload = {"not": "a datatype page"}
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        del format, args


def _console() -> str:
    executable = Path(sys.executable).with_name("netauto")
    assert executable.is_file()
    return str(executable)


def _environment() -> dict[str, str]:
    environment = dict(os.environ)
    environment.pop("NETAUTO_DATABASE_URL", None)
    environment.pop("TEST_DATABASE_URL", None)
    return environment


def _run_scenario(mode: str, arguments: list[str]) -> subprocess.CompletedProcess[str]:
    ScenarioHandler.mode = mode
    ScenarioHandler.paths = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), ScenarioHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        return subprocess.run(
            [
                _console(),
                "-n",
                f"http://127.0.0.1:{server.server_port}",
                *arguments,
            ],
            cwd=ROOT,
            env=_environment(),
            text=True,
            input="",
            capture_output=True,
            check=False,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_console_process_emits_one_json_line_and_needs_no_database_url() -> None:
    Handler.requests = 0
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        completed = subprocess.run(
            [
                _console(),
                "-n",
                f"http://127.0.0.1:{server.server_port}",
                "datatype",
                "list",
                "limit=2",
            ],
            cwd=ROOT,
            env=_environment(),
            text=True,
            input="",
            capture_output=True,
            check=False,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
    assert completed.returncode == 0
    assert completed.stderr == ""
    assert completed.stdout.endswith("\n")
    assert completed.stdout.count("\n") == 1
    result = json.loads(completed.stdout)
    assert result["status"] == "ok"
    assert result["result"] == {"items": [], "next_cursor": None}
    assert Handler.requests == 1


def test_console_local_failure_has_exact_output_channels_and_exit() -> None:
    completed = subprocess.run(
        [_console()],
        cwd=ROOT,
        text=True,
        input="",
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 1
    assert completed.stderr == ""
    assert completed.stdout.count("\n") == 1
    result = json.loads(completed.stdout)
    assert result["status"] == "error"
    assert result["command"] is None
    assert result["exchanges"] == []
    assert result["error"]["code"] == "cli_invalid_invocation"


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://example.test:",
        "http://example.test:/",
        "http://example.test:0",
        "http://example.test:+80",
        "http://example.test:abc",
        "https://[2001:db8::10]:",
        "https://[2001:db8::10]:65536",
    ],
)
def test_console_rejects_malformed_port_before_command_or_exchange(
    endpoint: str,
) -> None:
    completed = subprocess.run(
        [_console(), "-n", endpoint, "datatype", "list"],
        cwd=ROOT,
        env=_environment(),
        text=True,
        input="",
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 1
    assert completed.stderr == ""
    assert completed.stdout.count("\n") == 1
    result = json.loads(completed.stdout)
    assert result["command"] is None
    assert result["exchanges"] == []
    assert result["error"]["code"] == "cli_invalid_invocation"


def test_console_selector_sequence_has_no_health_preflight() -> None:
    completed = _run_scenario("selector", ["datatype", "get", "core.string"])
    assert completed.returncode == 0
    assert completed.stderr == ""
    result = json.loads(completed.stdout)
    assert result["status"] == "ok"
    assert len(result["exchanges"]) == 2
    assert ScenarioHandler.paths == [
        "/api/v1/core/datatypes?namespace=core&name=string&limit=2",
        "/api/v1/core/datatypes/11111111-1111-1111-1111-111111111111",
    ]
    assert "/health/core" not in ScenarioHandler.paths


def test_console_remote_and_protocol_failures_use_structured_stdout() -> None:
    for mode, source, code in (
        ("remote", "remote", "resource_not_found"),
        ("protocol", "protocol", "cli_protocol_error"),
    ):
        completed = _run_scenario(mode, ["datatype", "list"])
        assert completed.returncode == 1
        assert completed.stderr == ""
        assert completed.stdout.count("\n") == 1
        result = json.loads(completed.stdout)
        assert result["status"] == "error"
        assert result["error"]["source"] == source
        assert result["error"]["code"] == code
        assert len(result["exchanges"]) == 1


def test_console_transport_failure_is_structured_and_single_attempt() -> None:
    completed = subprocess.run(
        [
            _console(),
            "-n",
            "http://127.0.0.1:1",
            "datatype",
            "list",
        ],
        cwd=ROOT,
        env=_environment(),
        text=True,
        input="",
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 1
    assert completed.stderr == ""
    result = json.loads(completed.stdout)
    assert result["error"]["source"] == "transport"
    assert result["error"]["code"] == "cli_transport_error"
    assert len(result["exchanges"]) == 1
    assert result["exchanges"][0]["response"] is None
