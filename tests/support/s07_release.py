"""Reusable wheel-only release infrastructure for the M2-S07 T9 evidence."""

from __future__ import annotations

import errno
import hashlib
import json
import os
import select
import socket
import subprocess
import sys
import threading
import time
import tomllib
import urllib.error
import urllib.request
import zipfile
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

ROOT = Path(__file__).parents[2]
RELEASE_VERSION = "0.2.0"
WHEEL_BASENAME = f"netauto-{RELEASE_VERSION}-py3-none-any.whl"
LOCK_MEMBER = "netauto/release/runtime.pylock.toml"


def isolated_environment(extra: dict[str, str] | None = None) -> dict[str, str]:
    """Return a subprocess environment with no source or database inheritance."""
    environment = dict(os.environ)
    for name in (
        "PYTHONPATH",
        "VIRTUAL_ENV",
        "NETAUTO_DATABASE_URL",
        "NETAUTO_SECRETS_DIR",
        "TEST_DATABASE_URL",
    ):
        environment.pop(name, None)
    if extra:
        environment.update(extra)
    return environment


def sanitize(value: str, secrets: tuple[str, ...] = ()) -> str:
    """Bound diagnostics without retaining a supplied database target or token."""
    safe = value
    for secret in secrets:
        if secret:
            safe = safe.replace(secret, "<redacted>")
    return safe[-4000:]


def require_success(
    completed: subprocess.CompletedProcess[str], *, secrets: tuple[str, ...] = ()
) -> None:
    """Assert a text subprocess succeeded using bounded sanitized diagnostics."""
    assert completed.returncode == 0, sanitize(
        completed.stdout + completed.stderr, secrets
    )


@dataclass(frozen=True, slots=True)
class InstalledRelease:
    """One clean versioned release assembled exclusively from its wheel."""

    target_root: Path
    release_dir: Path
    wheel: Path
    runtime_lock: Path
    venv: Path
    python: Path
    netauto: Path
    uvicorn: Path
    alembic: Path
    alembic_ini: Path
    wheel_sha256: str

    def run(
        self,
        argv: list[str],
        *,
        environment: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            argv,
            cwd=self.target_root,
            env=isolated_environment(environment),
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )


def create_installed_release(target_root: Path) -> InstalledRelease:
    """Build once, transfer one wheel, sync its lock, then install with --no-deps."""
    wheel_build = target_root / "wheel-build"
    wheel_build.mkdir(parents=True)
    built = subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(wheel_build)],
        cwd=ROOT,
        env=isolated_environment(),
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    require_success(built)
    wheels = tuple(wheel_build.glob("*.whl"))
    assert tuple(wheel.name for wheel in wheels) == (WHEEL_BASENAME,)
    source_wheel = wheels[0]

    release_dir = target_root / "releases" / RELEASE_VERSION
    release_dir.mkdir(parents=True)
    wheel = release_dir / source_wheel.name
    wheel.write_bytes(source_wheel.read_bytes())
    runtime_lock = release_dir / "runtime.pylock.toml"
    with zipfile.ZipFile(wheel) as archive:
        runtime_lock.write_bytes(archive.read(LOCK_MEMBER))
    uv_compatible_lock = release_dir / "pylock.runtime.toml"
    uv_compatible_lock.write_bytes(runtime_lock.read_bytes())

    venv = release_dir / ".venv"
    created = subprocess.run(
        ["uv", "venv", "--python", sys.executable, str(venv)],
        cwd=target_root,
        env=isolated_environment(),
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    require_success(created)
    python = venv / "bin/python"
    synchronized = subprocess.run(
        [
            "uv",
            "pip",
            "sync",
            "--python",
            str(python),
            str(uv_compatible_lock),
        ],
        cwd=target_root,
        env=isolated_environment(),
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    require_success(synchronized)
    uv_compatible_lock.unlink()
    installed = subprocess.run(
        [
            "uv",
            "pip",
            "install",
            "--python",
            str(python),
            "--no-deps",
            str(wheel),
        ],
        cwd=target_root,
        env=isolated_environment(),
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    require_success(installed)

    alembic_ini = release_dir / "alembic.ini"
    alembic_ini.write_text(
        "[alembic]\nscript_location = netauto:migrations\npath_separator = os\n"
    )
    return InstalledRelease(
        target_root=target_root,
        release_dir=release_dir,
        wheel=wheel,
        runtime_lock=runtime_lock,
        venv=venv,
        python=python,
        netauto=venv / "bin/netauto",
        uvicorn=venv / "bin/uvicorn",
        alembic=venv / "bin/alembic",
        alembic_ini=alembic_ini,
        wheel_sha256=hashlib.sha256(wheel.read_bytes()).hexdigest(),
    )


def applicable_locked_packages(runtime_lock: Path) -> dict[str, str]:
    """Return the exact PEP 751 package set applicable to Linux CPython."""
    data = tomllib.loads(runtime_lock.read_text())
    result: dict[str, str] = {}
    packages = cast(list[dict[str, object]], data["packages"])
    for raw in packages:
        name = raw["name"]
        version = raw["version"]
        marker = raw.get("marker")
        assert isinstance(name, str) and isinstance(version, str)
        if marker == "sys_platform == 'win32'":
            continue
        if marker is not None:
            assert marker == "implementation_name != 'pypy'"
            assert sys.implementation.name != "pypy"
        result[name] = version
    return result


def free_port() -> int:
    """Reserve and release one loopback TCP port for a bounded subprocess test."""
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        assert isinstance(port, int)
        return port


def http_get(
    url: str, timeout: float = 1.0
) -> tuple[int, dict[str, object], Mapping[str, str]]:
    """Read one JSON response while preserving an HTTP error response body."""
    try:
        response = urllib.request.urlopen(url, timeout=timeout)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        raw_body: object = json.loads(response.read())
        assert isinstance(raw_body, dict)
        untyped_body = cast(dict[object, object], raw_body)
        assert all(isinstance(key, str) for key in untyped_body)
        body = cast(dict[str, object], raw_body)
        status = response.status
        assert isinstance(status, int)
        return status, body, cast(Mapping[str, str], response.headers)


def wait_for_http(
    url: str, *, expected_status: int = 200, timeout: float = 15.0
) -> tuple[dict[str, object], Mapping[str, str]]:
    """Poll a local endpoint until the required response or a finite deadline."""
    deadline = time.monotonic() + timeout
    last = "no response"
    while time.monotonic() < deadline:
        try:
            status, body, headers = http_get(url)
            if status == expected_status:
                return body, headers
            last = f"HTTP {status}"
        except OSError as error:
            last = type(error).__name__
        time.sleep(0.05)
    raise AssertionError(f"endpoint did not reach HTTP {expected_status}: {last}")


def listener_open(port: int) -> bool:
    """Return whether a loopback listener accepts a connection right now."""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.2):
            return True
    except OSError:
        return False


def terminate_orderly(
    process: subprocess.Popen[str], *, secrets: tuple[str, ...] = ()
) -> tuple[str, str]:
    """Request SIGTERM and require a normal foreground Uvicorn shutdown."""
    process.terminate()
    try:
        stdout, stderr = process.communicate(timeout=15)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate(timeout=5)
        raise AssertionError(
            "foreground process did not stop after SIGTERM: "
            + sanitize(stdout + stderr, secrets)
        ) from None
    assert process.returncode == 0, sanitize(stdout + stderr, secrets)
    return stdout, stderr


@dataclass(slots=True)
class PtyProcess:
    process: subprocess.Popen[bytes]
    master: int
    pending: bytearray = field(default_factory=bytearray)

    def read_until(self, needle: bytes, timeout: float = 10.0) -> bytes:
        deadline = time.monotonic() + timeout
        output = bytearray()
        while True:
            marker = self.pending.find(needle)
            if marker >= 0:
                end = marker + len(needle)
                output.extend(self.pending[:end])
                del self.pending[:end]
                return bytes(output)
            output.extend(self.pending)
            self.pending.clear()
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise AssertionError(
                    f"PTY output did not contain {needle!r}: {bytes(output)[-2000:]!r}"
                )
            readable, _, _ = select.select([self.master], [], [], remaining)
            if not readable:
                continue
            try:
                chunk = os.read(self.master, 4096)
            except OSError as error:
                if error.errno == errno.EIO:
                    break
                raise
            if not chunk:
                break
            self.pending.extend(chunk)
        raise AssertionError(f"PTY closed before {needle!r}: {bytes(output)[-2000:]!r}")

    def write(self, value: bytes) -> None:
        os.write(self.master, value)

    def close(self) -> None:
        try:
            if self.process.poll() is None:
                self.write(b"/exit\r")
                self.process.wait(timeout=5)
        finally:
            os.close(self.master)
            if self.process.poll() is None:
                self.process.terminate()
                self.process.wait(timeout=5)


def spawn_installed_pty(
    release: InstalledRelease, environment: dict[str, str] | None = None
) -> PtyProcess:
    """Spawn the installed console in a real Linux PTY outside the checkout."""
    master, slave = os.openpty()
    process = subprocess.Popen(
        [str(release.netauto)],
        cwd=release.target_root,
        env=isolated_environment(
            {
                "TERM": "xterm-256color",
                "PROMPT_TOOLKIT_NO_CPR": "1",
                **(environment or {}),
            }
        ),
        stdin=slave,
        stdout=slave,
        stderr=slave,
        close_fds=True,
    )
    os.close(slave)
    return PtyProcess(process, master)


def start_uvicorn(
    release: InstalledRelease,
    port: int,
    secrets_dir: Path,
    *,
    extra_environment: dict[str, str] | None = None,
) -> subprocess.Popen[str]:
    """Start the installed factory as one foreground loopback worker."""
    environment = {
        "NETAUTO_SECRETS_DIR": str(secrets_dir),
        "NETAUTO_POOL_SIZE": "1",
        "NETAUTO_MAX_OVERFLOW": "0",
        "NETAUTO_POOL_TIMEOUT": "1",
        "NETAUTO_POOL_PRE_PING": "true",
        **(extra_environment or {}),
    }
    return subprocess.Popen(
        [
            str(release.uvicorn),
            "netauto.entrypoints.http:create_app",
            "--factory",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--workers",
            "1",
        ],
        cwd=release.target_root,
        env=isolated_environment(environment),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def process_output(process: subprocess.Popen[str], timeout: float = 15.0) -> str:
    """Collect one completed text process using a finite deadline."""
    stdout, stderr = process.communicate(timeout=timeout)
    return stdout + stderr


def installed_alembic(
    release: InstalledRelease, secrets_dir: Path, *arguments: str
) -> subprocess.CompletedProcess[str]:
    """Invoke only the installed Alembic executable and package-resource graph."""
    return release.run(
        [
            str(release.alembic),
            "-c",
            str(release.alembic_ini),
            *arguments,
        ],
        environment={"NETAUTO_SECRETS_DIR": str(secrets_dir)},
        timeout=90,
    )


def write_secret_directory(parent: Path, database_url: str) -> Path:
    """Create the operator-shaped protected secret source."""
    directory = parent / "secrets"
    directory.mkdir(mode=0o700, parents=True)
    directory.chmod(0o700)
    secret = directory / "NETAUTO_DATABASE_URL"
    secret.write_text(f"{database_url}\n")
    secret.chmod(0o600)
    return directory


class TCPForwarder:
    """Controlled test-side TCP transport to a real external PostgreSQL target."""

    def __init__(self, upstream_host: str, upstream_port: int) -> None:
        self._upstream = (upstream_host, upstream_port)
        self._listener = socket.socket()
        self._listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._listener.bind(("127.0.0.1", 0))
        self._listener.listen()
        self._listener.settimeout(0.2)
        address = self._listener.getsockname()
        assert isinstance(address, tuple) and isinstance(address[1], int)
        self.port = address[1]
        self._stopped = threading.Event()
        self._enabled = threading.Event()
        self._enabled.set()
        self._lock = threading.Lock()
        self._connections: set[socket.socket] = set()
        self._workers: list[threading.Thread] = []
        self._thread = threading.Thread(target=self._accept, daemon=True)
        self._thread.start()

    def _accept(self) -> None:
        while not self._stopped.is_set():
            try:
                client, _ = self._listener.accept()
            except TimeoutError:
                continue
            except OSError:
                break
            if not self._enabled.is_set():
                client.close()
                continue
            worker = threading.Thread(target=self._forward, args=(client,), daemon=True)
            self._workers.append(worker)
            worker.start()

    def _forward(self, client: socket.socket) -> None:
        try:
            upstream = socket.create_connection(self._upstream, timeout=5)
        except OSError:
            client.close()
            return
        sockets = (client, upstream)
        with self._lock:
            self._connections.update(sockets)
        try:
            for item in sockets:
                item.setblocking(False)
            while self._enabled.is_set() and not self._stopped.is_set():
                readable, _, exceptional = select.select(sockets, (), sockets, 0.2)
                if exceptional:
                    break
                for source in readable:
                    try:
                        chunk = source.recv(65536)
                    except OSError:
                        return
                    if not chunk:
                        return
                    destination = upstream if source is client else client
                    try:
                        destination.sendall(chunk)
                    except OSError:
                        return
        finally:
            with self._lock:
                self._connections.difference_update(sockets)
            for item in sockets:
                try:
                    item.close()
                except OSError:
                    pass

    def cut(self) -> None:
        """Break established sessions and reject every subsequent connection."""
        self._enabled.clear()
        with self._lock:
            connections = tuple(self._connections)
        for connection in connections:
            try:
                connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            connection.close()

    def close(self) -> None:
        self.cut()
        self._stopped.set()
        self._listener.close()
        self._thread.join(timeout=2)
        for worker in self._workers:
            worker.join(timeout=2)

    def __enter__(self) -> TCPForwarder:
        return self

    def __exit__(self, *args: object) -> None:
        del args
        self.close()
