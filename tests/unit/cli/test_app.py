from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from uuid import uuid4

import pytest
from typer.testing import CliRunner

from netauto.cli.app import app
from netauto.cli.errors import ApiError, InputError, ProtocolError, TransportError

runner = CliRunner()


@dataclass
class FakeClient:
    api_url: str
    payloads: dict[str, Any]
    calls: list[tuple[str, tuple[Any, ...]]]
    error: Exception | None = None

    def __enter__(self) -> FakeClient:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    def _call(self, name: str, *args: Any) -> Any:
        self.calls.append((name, args))
        if self.error is not None:
            raise self.error
        return self.payloads[name]

    def list_datatypes(self) -> Any:
        return self._call("list_datatypes")

    def get_datatype(self, datatype_id: str) -> Any:
        return self._call("get_datatype", datatype_id)

    def get_datatype_by_name(self, namespace: str, name: str) -> Any:
        return self._call("get_datatype_by_name", namespace, name)

    def create_datatype(self, payload: dict[str, object]) -> Any:
        return self._call("create_datatype", payload)

    def list_versions(self, datatype_id: str) -> Any:
        return self._call("list_versions", datatype_id)

    def get_version(self, datatype_id: str, version: int) -> Any:
        return self._call("get_version", datatype_id, version)

    def revise_version(self, datatype_id: str, version: int, payload: dict[str, object]) -> Any:
        return self._call("revise_version", datatype_id, version, payload)

    def create_version(self, datatype_id: str, source_version: int) -> Any:
        return self._call("create_version", datatype_id, source_version)

    def publish_version(self, datatype_id: str, version: int) -> Any:
        return self._call("publish_version", datatype_id, version)

    def deprecate_version(self, datatype_id: str, version: int) -> Any:
        return self._call("deprecate_version", datatype_id, version)


def _patch_client(monkeypatch: pytest.MonkeyPatch, client: FakeClient) -> None:
    monkeypatch.setattr(
        "netauto.cli.datatypes.NetautoApiClient",
        lambda api_url: client.__class__(
            api_url,
            client.payloads,
            client.calls,
            client.error,
        ),
    )


def _datatype_payload() -> dict[str, object]:
    return {
        "id": str(uuid4()),
        "namespace": "network",
        "name": "vlan_id",
        "qualified_name": "network.vlan_id",
        "description": "VLAN identifier",
    }


def _version_payload() -> dict[str, object]:
    return {
        "datatype_id": str(uuid4()),
        "version": 1,
        "status": "draft",
        "base_type": "core.integer",
        "constraints": [
            {"name": "minimum", "value": 1},
            {"name": "maximum", "value": 4094},
        ],
    }


def test_version_and_help() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip()

    assert runner.invoke(app, ["--help"]).exit_code == 0
    assert runner.invoke(app, ["datatype", "--help"]).exit_code == 0
    assert runner.invoke(app, ["datatype", "version", "--help"]).exit_code == 0


def test_api_url_precedence(monkeypatch: pytest.MonkeyPatch) -> None:
    payloads = {"list_datatypes": []}
    calls: list[tuple[str, tuple[Any, ...]]] = []
    created_urls: list[str] = []

    def factory(api_url: str) -> FakeClient:
        created_urls.append(api_url)
        return FakeClient(api_url, payloads, calls)

    monkeypatch.setattr("netauto.cli.datatypes.NetautoApiClient", factory)

    result = runner.invoke(
        app,
        ["--api-url", "http://cli.example", "datatype", "list"],
        env={"NETAUTO_API_URL": "http://env.example"},
    )

    assert result.exit_code == 0
    assert created_urls == ["http://cli.example"]
    assert calls == [("list_datatypes", ())]


def test_list_show_and_show_name_json(monkeypatch: pytest.MonkeyPatch) -> None:
    datatype = _datatype_payload()
    payloads = {
        "list_datatypes": [datatype],
        "get_datatype": datatype,
        "get_datatype_by_name": datatype,
    }
    calls: list[tuple[str, tuple[Any, ...]]] = []
    monkeypatch.setattr(
        "netauto.cli.datatypes.NetautoApiClient",
        lambda api_url: FakeClient(api_url, payloads, calls),
    )

    listed = runner.invoke(app, ["--output", "json", "datatype", "list"])
    shown = runner.invoke(app, ["--output", "json", "datatype", "show", str(datatype["id"])])
    shown_name = runner.invoke(
        app,
        ["--output", "json", "datatype", "show-name", "network", "vlan_id"],
    )

    assert listed.exit_code == 0
    assert json.loads(listed.stdout) == [datatype]
    assert shown.exit_code == 0
    assert json.loads(shown.stdout) == datatype
    assert shown_name.exit_code == 0
    assert json.loads(shown_name.stdout) == datatype


def test_create_inline_and_file_and_stdin(monkeypatch: pytest.MonkeyPatch) -> None:
    datatype = _datatype_payload()
    version = _version_payload()
    payloads = {"create_datatype": {"datatype": datatype, "version": version}}
    calls: list[tuple[str, tuple[Any, ...]]] = []
    monkeypatch.setattr(
        "netauto.cli.datatypes.NetautoApiClient",
        lambda api_url: FakeClient(api_url, payloads, calls),
    )

    inline = runner.invoke(
        app,
        [
            "--output",
            "json",
            "datatype",
            "create",
            "--namespace",
            "network",
            "--name",
            "vlan_id",
            "--description",
            "VLAN identifier",
            "--base-type",
            "core.integer",
            "--constraint",
            "minimum=1",
            "--constraint",
            "maximum=4094",
        ],
    )

    with TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "datatype.json"
        path.write_text(
            json.dumps(
                {
                    "namespace": "network",
                    "name": "vlan_id",
                    "description": "VLAN identifier",
                    "base_type": "core.integer",
                    "constraints": [{"name": "minimum", "value": 1}],
                }
            ),
            encoding="utf-8",
        )
        file_result = runner.invoke(app, ["datatype", "create", "--file", str(path)])
        stdin_result = runner.invoke(
            app,
            ["datatype", "create", "--file", "-"],
            input=path.read_text(encoding="utf-8"),
        )

    assert inline.exit_code == 0
    assert json.loads(inline.stdout)["version"]["status"] == "draft"
    assert file_result.exit_code == 0
    assert stdin_result.exit_code == 0


def test_version_commands(monkeypatch: pytest.MonkeyPatch) -> None:
    version = _version_payload()
    calls: list[tuple[str, tuple[Any, ...]]] = []
    monkeypatch.setattr(
        "netauto.cli.datatypes.NetautoApiClient",
        lambda api_url: FakeClient(
            api_url,
            {
                "list_versions": [version],
                "get_version": version,
                "revise_version": version,
                "create_version": version,
                "publish_version": version,
                "deprecate_version": version,
            },
            calls,
        ),
    )
    datatype_id = str(version["datatype_id"])

    assert runner.invoke(app, ["datatype", "version", "list", datatype_id]).exit_code == 0
    assert runner.invoke(app, ["datatype", "version", "show", datatype_id, "1"]).exit_code == 0
    assert (
        runner.invoke(
            app,
            [
                "datatype",
                "version",
                "revise",
                datatype_id,
                "1",
                "--base-type",
                "core.integer",
                "--constraint",
                "minimum=1",
            ],
        ).exit_code
        == 0
    )
    assert (
        runner.invoke(
            app,
            ["datatype", "version", "create", datatype_id, "--source-version", "1"],
        ).exit_code
        == 0
    )
    assert runner.invoke(app, ["datatype", "version", "publish", datatype_id, "1"]).exit_code == 0
    assert runner.invoke(app, ["datatype", "version", "deprecate", datatype_id, "1"]).exit_code == 0


def test_local_input_errors_use_exit_code_2() -> None:
    with TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "bad.json"
        path.write_text("[]", encoding="utf-8")
        malformed_json = runner.invoke(
            app,
            [
                "datatype",
                "create",
                "--namespace",
                "network",
                "--name",
                "x",
                "--base-type",
                "core.string",
                "--constraint",
                "minimum=not-json",
            ],
        )
        mode_conflict = runner.invoke(
            app,
            [
                "datatype",
                "create",
                "--file",
                str(path),
                "--namespace",
                "network",
                "--name",
                "x",
                "--base-type",
                "core.string",
            ],
        )
        missing_file = runner.invoke(app, ["datatype", "create", "--file", "missing.json"])
        wrong_top_level = runner.invoke(app, ["datatype", "create", "--file", str(path)])

    assert malformed_json.exit_code == 2
    assert mode_conflict.exit_code == 2
    assert missing_file.exit_code == 2
    assert wrong_top_level.exit_code == 2


def test_bad_uuid_and_version_are_local_usage_errors() -> None:
    assert runner.invoke(app, ["datatype", "show", "not-a-uuid"]).exit_code == 2
    assert runner.invoke(app, ["datatype", "version", "show", str(uuid4()), "0"]).exit_code == 2
    assert (
        runner.invoke(
            app,
            ["datatype", "version", "create", str(uuid4()), "--source-version", "0"],
        ).exit_code
        == 2
    )


@pytest.mark.parametrize(
    ("error", "exit_code", "stderr_code"),
    [
        (
            ApiError(
                status_code=404,
                code="datatype_not_found",
                message="Datatype not found",
                details=[],
            ),
            1,
            "datatype_not_found",
        ),
        (TransportError("Could not connect to NETAUTO API."), 3, "cli_transport_error"),
        (ProtocolError("Server returned an incompatible response."), 4, "cli_protocol_error"),
        (InputError("Bad input"), 2, "cli_input_error"),
    ],
)
def test_cli_error_exit_codes_and_stderr(
    monkeypatch: pytest.MonkeyPatch,
    error: Exception,
    exit_code: int,
    stderr_code: str,
) -> None:
    calls: list[tuple[str, tuple[Any, ...]]] = []
    monkeypatch.setattr(
        "netauto.cli.datatypes.NetautoApiClient",
        lambda api_url: FakeClient(api_url, {"list_datatypes": []}, calls, error=error),
    )

    result = runner.invoke(app, ["--output", "json", "datatype", "list"])

    assert result.exit_code == exit_code
    assert result.stdout == ""
    assert stderr_code in result.stderr
