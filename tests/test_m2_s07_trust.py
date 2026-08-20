"""M2-VER-30 installed HTTPS, bind, secret, and trust-boundary evidence."""

from __future__ import annotations

import json
import ssl
import subprocess
import threading
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from tests.support.s07_release import ROOT, InstalledRelease, require_success


class TLSReadHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        assert self.path == "/api/v1/core/datatypes?limit=1"
        body = json.dumps({"items": [], "next_cursor": None}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        del format, args


def _openssl(arguments: list[str], cwd: Path) -> None:
    completed = subprocess.run(
        ["openssl", *arguments],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    require_success(completed)


def _certificate_authority(directory: Path) -> tuple[Path, Path, Path]:
    ca_key = directory / "ca.key"
    ca_cert = directory / "ca.crt"
    server_key = directory / "server.key"
    server_request = directory / "server.csr"
    server_cert = directory / "server.crt"
    extensions = directory / "server.ext"
    extensions.write_text("subjectAltName=DNS:localhost\nextendedKeyUsage=serverAuth\n")
    _openssl(
        [
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-keyout",
            str(ca_key),
            "-out",
            str(ca_cert),
            "-days",
            "1",
            "-sha256",
            "-subj",
            "/CN=NETAUTO-S07-Test-CA",
            "-addext",
            "basicConstraints=critical,CA:TRUE",
            "-addext",
            "keyUsage=critical,keyCertSign,cRLSign",
        ],
        directory,
    )
    _openssl(
        [
            "req",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-keyout",
            str(server_key),
            "-out",
            str(server_request),
            "-subj",
            "/CN=localhost",
        ],
        directory,
    )
    _openssl(
        [
            "x509",
            "-req",
            "-in",
            str(server_request),
            "-CA",
            str(ca_cert),
            "-CAkey",
            str(ca_key),
            "-CAcreateserial",
            "-out",
            str(server_cert),
            "-days",
            "1",
            "-sha256",
            "-extfile",
            str(extensions),
        ],
        directory,
    )
    return ca_cert, server_cert, server_key


def _invoke(
    release: InstalledRelease,
    endpoint: str,
    *,
    ca_cert: Path | None,
) -> subprocess.CompletedProcess[str]:
    environment = {} if ca_cert is None else {"SSL_CERT_FILE": str(ca_cert)}
    return release.run(
        [
            str(release.netauto),
            "-n",
            endpoint,
            "datatype",
            "list",
            "limit=1",
        ],
        environment=environment,
    )


@pytest.mark.slow
def test_installed_cli_https_verifies_trust_and_hostname_without_bypass(
    s07_release: InstalledRelease,
    tmp_path: Path,
) -> None:
    ca_cert, server_cert, server_key = _certificate_authority(tmp_path)
    server = ThreadingHTTPServer(("127.0.0.1", 0), TLSReadHandler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(server_cert, server_key)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        trusted = _invoke(
            s07_release,
            f"https://localhost:{server.server_port}",
            ca_cert=ca_cert,
        )
        require_success(trusted)
        assert json.loads(trusted.stdout)["status"] == "ok"

        untrusted = _invoke(
            s07_release,
            f"https://localhost:{server.server_port}",
            ca_cert=None,
        )
        assert untrusted.returncode == 1
        assert untrusted.stderr == ""
        untrusted_result = json.loads(untrusted.stdout)
        assert untrusted_result["error"]["code"] == "cli_transport_error"

        mismatch = _invoke(
            s07_release,
            f"https://127.0.0.1:{server.server_port}",
            ca_cert=ca_cert,
        )
        assert mismatch.returncode == 1
        assert mismatch.stderr == ""
        mismatch_result = json.loads(mismatch.stdout)
        assert mismatch_result["error"]["code"] == "cli_transport_error"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_installed_cli_and_settings_expose_no_credentials_or_tls_bypass(
    s07_release: InstalledRelease,
) -> None:
    forbidden_options = (
        "--insecure",
        "--skip-verify",
        "--verify=false",
        "--header",
        "--credential",
        "--token",
        "--username",
        "--password",
    )
    for option in forbidden_options:
        result = s07_release.run(
            [
                str(s07_release.netauto),
                "-n",
                "https://example.test",
                option,
            ]
        )
        assert result.returncode == 1
        assert result.stderr == ""
        payload = json.loads(result.stdout)
        assert payload["error"]["code"] == "cli_invalid_invocation"
        assert payload["exchanges"] == []

    userinfo = s07_release.run(
        [
            str(s07_release.netauto),
            "-n",
            "https://operator:secret@example.test",
            "datatype",
            "list",
        ]
    )
    assert userinfo.returncode == 1
    assert userinfo.stderr == ""
    payload = json.loads(userinfo.stdout)
    assert payload["error"]["code"] == "cli_invalid_invocation"
    assert "operator" not in userinfo.stdout
    assert "secret" not in userinfo.stdout

    inventory = s07_release.run(
        [
            str(s07_release.python),
            "-c",
            "\n".join(
                (
                    "import json",
                    "from netauto.settings import Settings",
                    "print(json.dumps({'fields': sorted(Settings.model_fields),"
                    "'defaults': {k:v.default for k,v in "
                    "Settings.model_fields.items() if not v.is_required()}}))",
                )
            ),
        ]
    )
    require_success(inventory)
    fields = json.loads(inventory.stdout)["fields"]
    assert fields == [
        "database_url",
        "log_level",
        "max_overflow",
        "pool_pre_ping",
        "pool_recycle",
        "pool_size",
        "pool_timeout",
    ]
    assert not any(
        token in field
        for field in fields
        for token in ("host", "port", "auth", "certificate", "private_key", "tls")
    )


def test_installed_public_contract_has_no_401_403_or_security_scheme(
    s07_release: InstalledRelease,
) -> None:
    script = """
import json
import socket
import sys
from importlib.metadata import version
from pathlib import Path

network_attempts = 0
def reject_connect(*args, **kwargs):
    global network_attempts
    network_attempts += 1
    raise AssertionError("OpenAPI construction attempted network I/O")
socket.socket.connect = reject_connect

from netauto.entrypoints.http import build_app
from netauto.settings import Settings

app = build_app(
    Settings(
        database_url=(
            "postgresql+psycopg://installed-contract:"
            "non-secret@example.invalid/netauto"
        )
    )
)
schema = app.openapi()
operation_security = []
header_parameters = []
auth_responses = []
operation_count = 0
methods = {"get", "post", "put", "patch", "delete"}
for path, path_item in schema["paths"].items():
    for parameter in path_item.get("parameters", []):
        if parameter.get("in") == "header":
            header_parameters.append([path, "PATH", parameter.get("name")])
    for method, operation in path_item.items():
        if method not in methods:
            continue
        operation_count += 1
        if "security" in operation:
            operation_security.append([path, method.upper(), operation["security"]])
        for parameter in operation.get("parameters", []):
            if parameter.get("in") == "header":
                header_parameters.append(
                    [path, method.upper(), parameter.get("name")]
                )
        for status in operation.get("responses", {}):
            if str(status) in {"401", "403"}:
                auth_responses.append([path, method.upper(), str(status)])

forbidden_route_segments = {
    "login", "logout", "token", "tokens", "account", "accounts", "role", "roles"
}
auth_routes = sorted(
    path for path in schema["paths"]
    if forbidden_route_segments & set(path.lower().strip("/").split("/"))
)
credential_tokens = (
    "auth", "credential", "username", "password", "token", "api_key", "tls"
)
settings_fields = list(Settings.model_fields)
credential_settings = sorted(
    field for field in settings_fields
    if any(token in field.lower() for token in credential_tokens)
)
components = schema.get("components", {})
print(json.dumps({
    "version": version("netauto"),
    "module_path": str(Path(sys.modules["netauto"].__file__).resolve()),
    "cwd": str(Path.cwd().resolve()),
    "path_count": len(schema["paths"]),
    "operation_count": operation_count,
    "top_level_security_present": "security" in schema,
    "security_schemes_present": "securitySchemes" in components,
    "operation_security": operation_security,
    "header_parameters": header_parameters,
    "auth_responses": auth_responses,
    "auth_routes": auth_routes,
    "credential_settings": credential_settings,
    "settings_fields": settings_fields,
    "network_attempts": network_attempts,
}, sort_keys=True))
"""
    result = s07_release.run([str(s07_release.python), "-c", script])
    require_success(result)
    assert result.stderr == ""
    assert len(result.stdout) < 5_000
    payload = json.loads(result.stdout)
    assert payload["version"] == "0.2.0"
    assert payload["cwd"] == str(s07_release.target_root.resolve())
    module_path = Path(payload["module_path"])
    assert s07_release.venv.resolve() in module_path.parents
    assert ROOT.resolve() not in module_path.parents
    assert payload["path_count"] == 52
    assert payload["operation_count"] == 64
    assert payload["top_level_security_present"] is False
    assert payload["security_schemes_present"] is False
    assert payload["operation_security"] == []
    assert payload["header_parameters"] == []
    assert payload["auth_responses"] == []
    assert payload["auth_routes"] == []
    assert payload["credential_settings"] == []
    assert payload["settings_fields"] == [
        "database_url",
        "log_level",
        "pool_size",
        "max_overflow",
        "pool_timeout",
        "pool_recycle",
        "pool_pre_ping",
    ]
    assert payload["network_attempts"] == 0


def test_secret_sentinel_is_absent_from_artifact_docs_config_and_server_argv(
    s07_release: InstalledRelease,
) -> None:
    sentinel = "M2-S07-UNIQUE-SECRET-MUST-NOT-LEAK-8b7e55"
    assert (
        sentinel
        not in (ROOT / "docs/milestones/M2/linux-operating-baseline.md").read_text()
    )
    assert sentinel not in s07_release.alembic_ini.read_text()
    with zipfile.ZipFile(s07_release.wheel) as archive:
        for name in archive.namelist():
            assert sentinel.encode() not in archive.read(name)
    canonical_argv = [
        str(s07_release.uvicorn),
        "netauto.entrypoints.http:create_app",
        "--factory",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
        "--workers",
        "1",
    ]
    assert sentinel not in " ".join(canonical_argv)
    assert "NETAUTO_DATABASE_URL" not in " ".join(canonical_argv)
