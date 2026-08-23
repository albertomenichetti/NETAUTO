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


class _PtyProcess:
    def __init__(self, process: subprocess.Popen[bytes], master: int) -> None:
        self.process = process
        self.master = master
        self.pending = bytearray()

    def write(self, payload: bytes) -> None:
        os.write(self.master, payload)

    def read_until(self, needle: bytes, timeout: float = 10.0) -> bytes:
        if not needle:
            raise ValueError("PTY sentinel must not be empty")
        deadline = time.monotonic() + timeout
        while True:
            index = self.pending.find(needle)
            if index >= 0:
                end = index + len(needle)
                output = bytes(self.pending[:end])
                del self.pending[:end]
                return output

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                tail = bytes(self.pending[-2000:])
                raise AssertionError(
                    f"PTY output did not contain {needle!r}; tail={tail!r}"
                )
            readable, _, _ = select.select([self.master], [], [], remaining)
            if not readable:
                continue
            try:
                chunk = os.read(self.master, 4096)
            except OSError as error:
                if error.errno != errno.EIO:
                    raise
                tail = bytes(self.pending[-2000:])
                raise AssertionError(
                    f"PTY closed before {needle!r}; tail={tail!r}"
                ) from None
            if not chunk:
                tail = bytes(self.pending[-2000:])
                raise AssertionError(f"PTY closed before {needle!r}; tail={tail!r}")
            self.pending.extend(chunk)


def _spawn(cwd: Path = ROOT) -> _PtyProcess:
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
    return _PtyProcess(process, master)


def _read_help_response(pty: _PtyProcess) -> bytes:
    result = pty.read_until(b'"local_commands"')
    result += pty.read_until(b"netauto>")
    assert b"status: ok" in result
    assert b'"grammar"' in result
    assert b'"local_commands"' in result
    return result


def _finish(pty: _PtyProcess) -> None:
    primary_exception_active = sys.exc_info()[0] is not None
    cleanup_error: BaseException | None = None
    try:
        if pty.process.poll() is None:
            try:
                pty.write(b"\x03")
                pty.write(b"/exit\r")
            except OSError as error:
                if error.errno != errno.EIO:
                    cleanup_error = error
            try:
                pty.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pty.process.terminate()
                try:
                    pty.process.wait(timeout=2)
                except (OSError, subprocess.TimeoutExpired) as error:
                    cleanup_error = cleanup_error or error
    finally:
        try:
            os.close(pty.master)
        except OSError as error:
            cleanup_error = cleanup_error or error
    if cleanup_error is not None and not primary_exception_active:
        raise cleanup_error


def test_pty_reader_detects_split_sentinel_and_preserves_tail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = subprocess.Popen(
        [sys.executable, "-c", "pass"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    chunks = iter((b"netau", b"to>tail"))

    def fake_select(
        readers: list[int],
        writers: list[int],
        exceptional: list[int],
        timeout: float,
    ) -> tuple[list[int], list[int], list[int]]:
        del writers, exceptional, timeout
        return readers, [], []

    def fake_read(file_descriptor: int, size: int) -> bytes:
        del file_descriptor, size
        return next(chunks)

    monkeypatch.setattr(select, "select", fake_select)
    monkeypatch.setattr(os, "read", fake_read)
    pty = _PtyProcess(process, 123)
    try:
        with pytest.raises(ValueError, match="must not be empty"):
            pty.read_until(b"")
        assert pty.read_until(b"netauto>") == b"netauto>"
        assert pty.pending == b"tail"
    finally:
        assert process.wait(timeout=2) == 0


@pytest.mark.skipif(sys.platform != "linux", reason="M2 PTY evidence is Linux-owned")
def test_no_argument_process_opens_prompt_and_exit_closes_normally() -> None:
    pty = _spawn()
    try:
        initial = pty.read_until(b"netauto>")
        assert b"cli_invalid_invocation" not in initial
        pty.write(b"/exit\r")
        output = pty.read_until(b'"exiting": true')
        assert b"status: ok" in output
        assert pty.process.wait(timeout=10) == 0
    finally:
        _finish(pty)


@pytest.mark.skipif(sys.platform != "linux", reason="M2 PTY evidence is Linux-owned")
def test_ctrl_d_on_empty_prompt_exits_zero() -> None:
    pty = _spawn()
    try:
        pty.read_until(b"netauto>")
        pty.write(b"\x04")
        assert pty.process.wait(timeout=10) == 0
    finally:
        _finish(pty)


@pytest.mark.skipif(sys.platform != "linux", reason="M2 PTY evidence is Linux-owned")
def test_ctrl_c_cancels_current_edit_and_returns_to_prompt() -> None:
    pty = _spawn()
    try:
        pty.read_until(b"netauto>")
        pty.write(b"datatype li")
        typed = pty.read_until(b"datatype li")
        pty.write(b"\x03")
        output = pty.read_until(b"netauto>")
        assert pty.process.poll() is None
        assert b"datatype li" in typed
        assert b"netauto>" in output
        pty.write(b"/exit\r")
        assert pty.process.wait(timeout=10) == 0
    finally:
        _finish(pty)


@pytest.mark.skipif(sys.platform != "linux", reason="M2 PTY evidence is Linux-owned")
def test_ctrl_r_searches_only_current_in_memory_history() -> None:
    pty = _spawn()
    try:
        pty.read_until(b"netauto>")
        pty.write(b"/help\r")
        _read_help_response(pty)
        assert b"/help" not in pty.pending

        pty.write(b"\x12")
        pty.read_until(b"reverse-i-search")
        pty.write(b"help")
        pty.read_until(b"help")
        pty.write(b"\r\r")
        _read_help_response(pty)
        assert pty.process.poll() is None

        pty.write(b"\x12")
        pty.read_until(b"reverse-i-search")
        pty.write(b"\x03/exit\r")
        exited = pty.read_until(b'"exiting": true')
        assert b"status: ok" in exited
        assert pty.process.wait(timeout=10) == 0
    finally:
        _finish(pty)


@pytest.mark.skipif(sys.platform != "linux", reason="M2 PTY evidence is Linux-owned")
def test_repl_creates_no_persistent_history_file(tmp_path: Path) -> None:
    pty = _spawn(tmp_path)
    try:
        pty.read_until(b"netauto>")
        pty.write(b"/help\r")
        _read_help_response(pty)
        pty.write(b"/exit\r")
        assert pty.process.wait(timeout=10) == 0
    finally:
        _finish(pty)
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
