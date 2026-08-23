"""Deterministic local TLS trust and hostname-verification evidence."""

import json
import ssl
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from netauto.cli.execution import execute
from netauto.cli.model import CliResult, CommandKey, ParsedCommand
from netauto.cli.registry import COMMAND_REGISTRY


class TlsHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        body = json.dumps({"items": [], "next_cursor": None}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        del format, args


def _openssl(*arguments: str, cwd: Path) -> None:
    subprocess.run(
        ["openssl", *arguments],
        cwd=cwd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )


def _certificates(directory: Path) -> None:
    _openssl(
        "req",
        "-x509",
        "-newkey",
        "rsa:2048",
        "-nodes",
        "-days",
        "1",
        "-subj",
        "/CN=M2-S05 Test CA",
        "-addext",
        "basicConstraints=critical,CA:TRUE",
        "-addext",
        "keyUsage=critical,keyCertSign,cRLSign",
        "-keyout",
        "ca.key",
        "-out",
        "ca.pem",
        cwd=directory,
    )
    for name, hostname, subject_alt_name in (
        ("matching", "127.0.0.1", "IP:127.0.0.1"),
        ("mismatch", "wrong.test", "DNS:wrong.test"),
    ):
        _openssl(
            "req",
            "-new",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-subj",
            f"/CN={hostname}",
            "-addext",
            f"subjectAltName={subject_alt_name}",
            "-addext",
            "basicConstraints=critical,CA:FALSE",
            "-addext",
            "keyUsage=critical,digitalSignature,keyEncipherment",
            "-addext",
            "extendedKeyUsage=serverAuth",
            "-keyout",
            f"{name}.key",
            "-out",
            f"{name}.csr",
            cwd=directory,
        )
        _openssl(
            "x509",
            "-req",
            "-in",
            f"{name}.csr",
            "-CA",
            "ca.pem",
            "-CAkey",
            "ca.key",
            "-CAcreateserial",
            "-days",
            "1",
            "-copy_extensions",
            "copy",
            "-out",
            f"{name}.pem",
            cwd=directory,
        )


async def _request_with_certificate(directory: Path, name: str) -> CliResult:
    server = ThreadingHTTPServer(("127.0.0.1", 0), TlsHandler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(directory / f"{name}.pem", directory / f"{name}.key")
    server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    command = ParsedCommand.create(CommandKey("datatype", "list"), None, {})
    try:
        return await execute(
            f"https://127.0.0.1:{server.server_port}",
            command,
            COMMAND_REGISTRY[command.key],
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.asyncio
async def test_default_tls_verification_trust_and_hostname_matrix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _certificates(tmp_path)
    monkeypatch.setenv("NO_PROXY", "localhost,127.0.0.1")
    monkeypatch.setenv("SSL_CERT_FILE", str(tmp_path / "ca.pem"))

    trusted = await _request_with_certificate(tmp_path, "matching")
    assert trusted.status == "ok", trusted.as_json()

    mismatch = await _request_with_certificate(tmp_path, "mismatch")
    assert mismatch.error is not None
    assert mismatch.error.code == "cli_transport_error"

    monkeypatch.delenv("SSL_CERT_FILE")
    untrusted = await _request_with_certificate(tmp_path, "matching")
    assert untrusted.error is not None
    assert untrusted.error.code == "cli_transport_error"
    assert all(
        "PRIVATE KEY" not in str(exchange.as_json()) for exchange in untrusted.exchanges
    )
