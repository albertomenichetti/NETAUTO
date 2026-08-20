"""Linux PTY and installed process-routing evidence for M2-VER-25."""

import errno
import os
import select
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]


def _console() -> str:
    executable = Path(sys.executable).with_name("netauto")
    assert executable.is_file()
    return str(executable)


def _environment() -> dict[str, str]:
    environment = dict(os.environ)
    environment.pop("NETAUTO_DATABASE_URL", None)
    environment.pop("TEST_DATABASE_URL", None)
    environment["TERM"] = "xterm-256color"
    environment["PROMPT_TOOLKIT_NO_CPR"] = "1"
    return environment


def _spawn(cwd: Path = ROOT) -> tuple[subprocess.Popen[bytes], int]:
    master, slave = os.openpty()
    process = subprocess.Popen(
        [_console()],
        cwd=cwd,
        env=_environment(),
        stdin=slave,
        stdout=slave,
        stderr=slave,
        close_fds=True,
    )
    os.close(slave)
    return process, master


def _read_until(master: int, needle: bytes, timeout: float = 10.0) -> bytes:
    deadline = time.monotonic() + timeout
    output = bytearray()
    while needle not in output:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise AssertionError(
                f"PTY output did not contain {needle!r}: {bytes(output)!r}"
            )
        readable, _, _ = select.select([master], [], [], remaining)
        if not readable:
            continue
        try:
            chunk = os.read(master, 4096)
        except OSError as error:
            if error.errno == errno.EIO:
                break
            raise
        if not chunk:
            break
        output.extend(chunk)
    assert needle in output
    return bytes(output)


def _finish(process: subprocess.Popen[bytes], master: int) -> None:
    try:
        if process.poll() is None:
            os.write(master, b"/exit\r")
            process.wait(timeout=10)
    finally:
        os.close(master)
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)


@pytest.mark.skipif(sys.platform != "linux", reason="M2 PTY evidence is Linux-owned")
def test_no_argument_process_opens_prompt_and_exit_closes_normally() -> None:
    process, master = _spawn()
    try:
        initial = _read_until(master, b"netauto>")
        assert b"cli_invalid_invocation" not in initial
        os.write(master, b"/exit\r")
        output = _read_until(master, b'"exiting": true')
        assert b"status: ok" in output
        assert process.wait(timeout=10) == 0
    finally:
        _finish(process, master)


@pytest.mark.skipif(sys.platform != "linux", reason="M2 PTY evidence is Linux-owned")
def test_ctrl_d_on_empty_prompt_exits_zero() -> None:
    process, master = _spawn()
    try:
        _read_until(master, b"netauto>")
        os.write(master, b"\x04")
        assert process.wait(timeout=10) == 0
    finally:
        _finish(process, master)


@pytest.mark.skipif(sys.platform != "linux", reason="M2 PTY evidence is Linux-owned")
def test_ctrl_c_cancels_current_edit_and_returns_to_prompt() -> None:
    process, master = _spawn()
    try:
        _read_until(master, b"netauto>")
        os.write(master, b"datatype li")
        os.write(master, b"\x03")
        output = _read_until(master, b"netauto>")
        assert process.poll() is None
        assert b"datatype li" in output
        os.write(master, b"/exit\r")
        assert process.wait(timeout=10) == 0
    finally:
        _finish(process, master)


@pytest.mark.skipif(sys.platform != "linux", reason="M2 PTY evidence is Linux-owned")
def test_ctrl_r_searches_only_current_in_memory_history() -> None:
    process, master = _spawn()
    try:
        _read_until(master, b"netauto>")
        os.write(master, b"/help\r")
        _read_until(master, b"netauto>")
        os.write(master, b"\x12")
        searched = _read_until(master, b"/help")
        assert b"/help" in searched
        assert process.poll() is None
        os.write(master, b"\x03/exit\r")
        exited = _read_until(master, b'"exiting": true')
        assert b"status: ok" in exited
        assert process.wait(timeout=10) == 0
    finally:
        _finish(process, master)


@pytest.mark.skipif(sys.platform != "linux", reason="M2 PTY evidence is Linux-owned")
def test_repl_creates_no_persistent_history_file(tmp_path: Path) -> None:
    process, master = _spawn(tmp_path)
    try:
        _read_until(master, b"netauto>")
        os.write(master, b"/help\r")
        _read_until(master, b"netauto>")
        os.write(master, b"/exit\r")
        assert process.wait(timeout=10) == 0
    finally:
        _finish(process, master)
    assert list(tmp_path.iterdir()) == []


def test_unsupported_nonempty_process_shape_never_opens_prompt() -> None:
    completed = subprocess.run(
        [_console(), "--unsupported"],
        cwd=ROOT,
        env=_environment(),
        text=True,
        capture_output=True,
        check=False,
        timeout=10,
    )
    assert completed.returncode == 1
    assert completed.stderr == ""
    assert completed.stdout.count("\n") == 1
    assert "cli_invalid_invocation" in completed.stdout
    assert "netauto>" not in completed.stdout
