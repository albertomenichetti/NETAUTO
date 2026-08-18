"""Bounded installed-wheel console evidence owned by M2-S05."""

import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]


class InstalledHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        assert self.path == "/api/v1/core/datatypes?limit=2"
        body = json.dumps({"items": [], "next_cursor": None}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        del format, args


@pytest.mark.slow
def test_installed_candidate_wheel_exposes_working_netauto_console(
    tmp_path: Path,
) -> None:
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
    wheels = tuple(wheel_dir.glob("netauto-*.whl"))
    assert len(wheels) == 1

    environment_dir = tmp_path / "candidate-environment"
    created = subprocess.run(
        ["uv", "venv", "--python", sys.executable, str(environment_dir)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert created.returncode == 0, created.stdout + created.stderr
    candidate_python = environment_dir / "bin/python"
    installed = subprocess.run(
        [
            "uv",
            "pip",
            "install",
            "--offline",
            "--python",
            str(candidate_python),
            str(wheels[0]),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert installed.returncode == 0, installed.stdout + installed.stderr

    imported = subprocess.run(
        [
            str(candidate_python),
            "-c",
            "import netauto,pathlib;print(pathlib.Path(netauto.__file__).resolve())",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert imported.returncode == 0, imported.stdout + imported.stderr
    assert Path(imported.stdout.strip()).is_relative_to(environment_dir)

    server = ThreadingHTTPServer(("127.0.0.1", 0), InstalledHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop("NETAUTO_DATABASE_URL", None)
    environment.pop("TEST_DATABASE_URL", None)
    try:
        invoked = subprocess.run(
            [
                str(environment_dir / "bin/netauto"),
                "-n",
                f"http://127.0.0.1:{server.server_port}",
                "datatype",
                "list",
                "limit=2",
            ],
            cwd=tmp_path,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
    assert invoked.returncode == 0, invoked.stdout + invoked.stderr
    assert invoked.stderr == ""
    assert invoked.stdout.count("\n") == 1
    result = json.loads(invoked.stdout)
    assert result["status"] == "ok"
    assert result["result"] == {"items": [], "next_cursor": None}
