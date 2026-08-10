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

    def list_object_templates(self) -> Any:
        return self._call("list_object_templates")

    def get_object_template(self, template_id: str) -> Any:
        return self._call("get_object_template", template_id)

    def get_object_template_by_name(self, namespace: str, name: str) -> Any:
        return self._call("get_object_template_by_name", namespace, name)

    def create_object_template(self, payload: dict[str, object]) -> Any:
        return self._call("create_object_template", payload)

    def list_object_template_versions(self, template_id: str) -> Any:
        return self._call("list_object_template_versions", template_id)

    def get_object_template_version(self, template_id: str, version: int) -> Any:
        return self._call("get_object_template_version", template_id, version)

    def revise_object_template_version(
        self,
        template_id: str,
        version: int,
        payload: dict[str, object],
    ) -> Any:
        return self._call("revise_object_template_version", template_id, version, payload)

    def create_object_template_version(self, template_id: str, source_version: int) -> Any:
        return self._call("create_object_template_version", template_id, source_version)

    def publish_object_template_version(self, template_id: str, version: int) -> Any:
        return self._call("publish_object_template_version", template_id, version)

    def deprecate_object_template_version(self, template_id: str, version: int) -> Any:
        return self._call("deprecate_object_template_version", template_id, version)

    def get_object_migration_analysis(
        self,
        template_id: str,
        source_version: int,
        target_version: int,
    ) -> Any:
        return self._call(
            "get_object_migration_analysis",
            template_id,
            source_version,
            target_version,
        )

    def migrate_objects(
        self,
        template_id: str,
        source_version: int,
        payload: dict[str, object],
    ) -> Any:
        return self._call("migrate_objects", template_id, source_version, payload)

    def list_objects(self) -> Any:
        return self._call("list_objects")

    def get_object(self, object_id: str) -> Any:
        return self._call("get_object", object_id)

    def create_object(self, payload: dict[str, object]) -> Any:
        return self._call("create_object", payload)

    def update_object(self, object_id: str, payload: dict[str, object]) -> Any:
        return self._call("update_object", object_id, payload)

    def delete_object(self, object_id: str) -> Any:
        return self._call("delete_object", object_id)

    def list_object_components(self, object_id: str) -> Any:
        return self._call("list_object_components", object_id)

    def attach_object_component(self, object_id: str, payload: dict[str, object]) -> Any:
        return self._call("attach_object_component", object_id, payload)

    def detach_object_component(self, component_object_id: str) -> Any:
        return self._call("detach_object_component", component_object_id)


def _patch_client(
    monkeypatch: pytest.MonkeyPatch,
    payloads: dict[str, Any],
    calls: list[tuple[str, tuple[Any, ...]]],
    *,
    error: Exception | None = None,
) -> None:
    monkeypatch.setattr(
        "netauto.cli.common.NetautoApiClient",
        lambda api_url: FakeClient(api_url, payloads, calls, error=error),
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


def _object_template_payload() -> dict[str, object]:
    return {
        "id": str(uuid4()),
        "namespace": "network",
        "name": "device",
        "qualified_name": "network.device",
        "description": "Device template",
        "abstract": True,
    }


def _object_template_version_payload() -> dict[str, object]:
    parent_id = str(uuid4())
    datatype_id = str(uuid4())
    component_template_id = str(uuid4())
    return {
        "template_id": str(uuid4()),
        "version": 1,
        "status": "draft",
        "parent": {"template_id": parent_id, "version": 2},
        "properties": [
            {
                "name": "hostname",
                "datatype_id": datatype_id,
                "datatype_version": 3,
                "required": True,
            },
            {
                "name": "serial",
                "datatype_id": datatype_id,
                "datatype_version": 3,
                "required": False,
            },
        ],
        "components": [
            {
                "name": "interfaces",
                "template_id": component_template_id,
            }
        ],
    }


def _object_payload() -> dict[str, object]:
    return {
        "id": str(uuid4()),
        "template_id": str(uuid4()),
        "template_version": 2,
        "properties": {
            "hostname": "router-01",
            "vlan": 100,
            "enabled": True,
            "description": None,
        },
    }


def _component_membership_payload() -> dict[str, object]:
    return {
        "parent_object_id": str(uuid4()),
        "slot_name": "interfaces",
        "component_object_id": str(uuid4()),
    }


def _object_migration_analysis_payload() -> dict[str, object]:
    return {
        "template_id": str(uuid4()),
        "source_version": 1,
        "target_version": 2,
        "automatic": True,
        "added_properties": [{"name": "serialnumber", "required": True}],
        "added_components": [{"name": "power_supplies", "template_id": str(uuid4())}],
        "blocking_changes": [],
    }


def _object_migration_result_payload() -> dict[str, object]:
    return {
        "template_id": str(uuid4()),
        "source_version": 1,
        "target_version": 2,
        "migrated_count": 3,
    }


def test_version_and_help() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip()

    assert runner.invoke(app, ["--help"]).exit_code == 0
    assert runner.invoke(app, ["datatype", "--help"]).exit_code == 0
    assert runner.invoke(app, ["datatype", "version", "--help"]).exit_code == 0
    assert runner.invoke(app, ["object", "--help"]).exit_code == 0
    assert runner.invoke(app, ["object", "component", "--help"]).exit_code == 0
    assert runner.invoke(app, ["object-template", "--help"]).exit_code == 0
    assert runner.invoke(app, ["object-template", "version", "--help"]).exit_code == 0


def test_api_url_precedence(monkeypatch: pytest.MonkeyPatch) -> None:
    payloads = {"list_datatypes": []}
    calls: list[tuple[str, tuple[Any, ...]]] = []
    created_urls: list[str] = []

    def factory(api_url: str) -> FakeClient:
        created_urls.append(api_url)
        return FakeClient(api_url, payloads, calls)

    monkeypatch.setattr("netauto.cli.common.NetautoApiClient", factory)

    result = runner.invoke(
        app,
        ["--api-url", "http://cli.example", "datatype", "list"],
        env={"NETAUTO_API_URL": "http://env.example"},
    )

    assert result.exit_code == 0
    assert created_urls == ["http://cli.example"]
    assert calls == [("list_datatypes", ())]


def test_datatype_list_show_and_show_name_json(monkeypatch: pytest.MonkeyPatch) -> None:
    datatype = _datatype_payload()
    calls: list[tuple[str, tuple[Any, ...]]] = []
    _patch_client(
        monkeypatch,
        {
            "list_datatypes": [datatype],
            "get_datatype": datatype,
            "get_datatype_by_name": datatype,
        },
        calls,
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


def test_datatype_create_inline_and_file_and_stdin(monkeypatch: pytest.MonkeyPatch) -> None:
    datatype = _datatype_payload()
    version = _version_payload()
    calls: list[tuple[str, tuple[Any, ...]]] = []
    _patch_client(
        monkeypatch,
        {"create_datatype": {"datatype": datatype, "version": version}},
        calls,
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


def test_datatype_version_commands(monkeypatch: pytest.MonkeyPatch) -> None:
    version = _version_payload()
    calls: list[tuple[str, tuple[Any, ...]]] = []
    _patch_client(
        monkeypatch,
        {
            "list_versions": [version],
            "get_version": version,
            "revise_version": version,
            "create_version": version,
            "publish_version": version,
            "deprecate_version": version,
        },
        calls,
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


def test_object_template_read_commands(monkeypatch: pytest.MonkeyPatch) -> None:
    template = _object_template_payload()
    version = _object_template_version_payload()
    calls: list[tuple[str, tuple[Any, ...]]] = []
    _patch_client(
        monkeypatch,
        {
            "list_object_templates": [template],
            "get_object_template": template,
            "get_object_template_by_name": template,
            "list_object_template_versions": [version],
            "get_object_template_version": version,
        },
        calls,
    )

    assert runner.invoke(app, ["object-template", "list"]).exit_code == 0
    assert runner.invoke(app, ["object-template", "show", str(template["id"])]).exit_code == 0
    assert runner.invoke(app, ["object-template", "show-name", "network", "device"]).exit_code == 0
    assert (
        runner.invoke(
            app,
            ["object-template", "version", "list", str(template["id"])],
        ).exit_code
        == 0
    )
    assert (
        runner.invoke(
            app,
            ["object-template", "version", "show", str(template["id"]), "1"],
        ).exit_code
        == 0
    )


def test_object_template_create_inline_variants(monkeypatch: pytest.MonkeyPatch) -> None:
    template = _object_template_payload()
    version = _object_template_version_payload()
    calls: list[tuple[str, tuple[Any, ...]]] = []
    _patch_client(
        monkeypatch,
        {"create_object_template": {"object_template": template, "version": version}},
        calls,
    )
    parent_id = str(uuid4())
    datatype_id = str(uuid4())
    first_component_id = str(uuid4())
    second_component_id = str(uuid4())

    result = runner.invoke(
        app,
        [
            "object-template",
            "create",
            "--namespace",
            "network",
            "--name",
            "device",
            "--description",
            "Device template",
            "--abstract",
            "--parent-template-id",
            parent_id,
            "--parent-version",
            "2",
            "--property-json",
            json.dumps({"name": "hostname", "datatype_id": datatype_id, "required": True}),
            "--property-json",
            json.dumps(
                {
                    "name": "serial",
                    "datatype_id": datatype_id,
                    "datatype_version": 4,
                    "required": False,
                }
            ),
            "--component-json",
            json.dumps({"name": "interfaces", "template_id": first_component_id}),
            "--component-json",
            json.dumps(
                {
                    "name": "modules",
                    "template_id": second_component_id,
                }
            ),
        ],
    )

    assert result.exit_code == 0
    assert calls == [
        (
            "create_object_template",
            (
                {
                    "namespace": "network",
                    "name": "device",
                    "description": "Device template",
                    "abstract": True,
                    "parent": {"template_id": parent_id, "version": 2},
                    "properties": [
                        {"name": "hostname", "datatype_id": datatype_id, "required": True},
                        {
                            "name": "serial",
                            "datatype_id": datatype_id,
                            "datatype_version": 4,
                            "required": False,
                        },
                    ],
                    "components": [
                        {"name": "interfaces", "template_id": first_component_id},
                        {"name": "modules", "template_id": second_component_id},
                    ],
                },
            ),
        )
    ]


def test_object_template_create_inline_without_components_sends_empty_components(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    template = _object_template_payload()
    version = _object_template_version_payload()
    calls: list[tuple[str, tuple[Any, ...]]] = []
    _patch_client(
        monkeypatch,
        {"create_object_template": {"object_template": template, "version": version}},
        calls,
    )

    result = runner.invoke(
        app,
        [
            "object-template",
            "create",
            "--namespace",
            "network",
            "--name",
            "device",
        ],
    )

    assert result.exit_code == 0
    assert calls == [
        (
            "create_object_template",
            (
                {
                    "namespace": "network",
                    "name": "device",
                    "description": None,
                    "abstract": False,
                    "parent": None,
                    "properties": [],
                    "components": [],
                },
            ),
        )
    ]


def test_object_template_create_file_and_stdin(monkeypatch: pytest.MonkeyPatch) -> None:
    template = _object_template_payload()
    version = _object_template_version_payload()
    calls: list[tuple[str, tuple[Any, ...]]] = []
    _patch_client(
        monkeypatch,
        {"create_object_template": {"object_template": template, "version": version}},
        calls,
    )
    payload = {
        "namespace": "network",
        "name": "device",
        "description": "Device template",
        "abstract": False,
        "parent": None,
        "properties": [],
        "components": [{"name": "interfaces", "template_id": str(uuid4())}],
    }

    with TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "template.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        file_result = runner.invoke(app, ["object-template", "create", "--file", str(path)])
        stdin_result = runner.invoke(
            app,
            ["object-template", "create", "--file", "-"],
            input=path.read_text(encoding="utf-8"),
        )

    assert file_result.exit_code == 0
    assert stdin_result.exit_code == 0


def test_object_template_create_json_output_preserves_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    template = _object_template_payload()
    version = _object_template_version_payload()
    calls: list[tuple[str, tuple[Any, ...]]] = []
    _patch_client(
        monkeypatch,
        {"create_object_template": {"object_template": template, "version": version}},
        calls,
    )

    result = runner.invoke(
        app,
        [
            "--output",
            "json",
            "object-template",
            "create",
            "--namespace",
            "network",
            "--name",
            "device",
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout) == {"object_template": template, "version": version}


def test_object_template_create_local_input_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, tuple[Any, ...]]] = []
    _patch_client(monkeypatch, {"create_object_template": {}}, calls)

    with TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "template.json"
        path.write_text("{}", encoding="utf-8")
        mode_conflict = runner.invoke(
            app,
            [
                "object-template",
                "create",
                "--file",
                str(path),
                "--namespace",
                "network",
                "--name",
                "device",
            ],
        )

    incomplete_parent = runner.invoke(
        app,
        [
            "object-template",
            "create",
            "--namespace",
            "network",
            "--name",
            "device",
            "--parent-template-id",
            str(uuid4()),
        ],
    )
    malformed_property = runner.invoke(
        app,
        [
            "object-template",
            "create",
            "--namespace",
            "network",
            "--name",
            "device",
            "--property-json",
            "not-json",
        ],
    )
    non_object_property = runner.invoke(
        app,
        [
            "object-template",
            "create",
            "--namespace",
            "network",
            "--name",
            "device",
            "--property-json",
            "[]",
        ],
    )
    malformed_component = runner.invoke(
        app,
        [
            "object-template",
            "create",
            "--namespace",
            "network",
            "--name",
            "device",
            "--component-json",
            "not-json",
        ],
    )
    non_object_component = runner.invoke(
        app,
        [
            "object-template",
            "create",
            "--namespace",
            "network",
            "--name",
            "device",
            "--component-json",
            "[]",
        ],
    )
    file_component_conflict = runner.invoke(
        app,
        [
            "object-template",
            "create",
            "--file",
            str(path),
            "--component-json",
            json.dumps({"name": "interfaces", "template_id": str(uuid4())}),
        ],
    )

    assert mode_conflict.exit_code == 2
    assert incomplete_parent.exit_code == 2
    assert malformed_property.exit_code == 2
    assert non_object_property.exit_code == 2
    assert malformed_component.exit_code == 2
    assert non_object_component.exit_code == 2
    assert file_component_conflict.exit_code == 2
    assert calls == []


def test_object_template_version_revise_variants(monkeypatch: pytest.MonkeyPatch) -> None:
    version = _object_template_version_payload()
    calls: list[tuple[str, tuple[Any, ...]]] = []
    _patch_client(monkeypatch, {"revise_object_template_version": version}, calls)
    template_id = str(version["template_id"])
    parent_id = str(uuid4())
    datatype_id = str(uuid4())
    first_component_id = str(uuid4())
    second_component_id = str(uuid4())

    no_parent = runner.invoke(
        app,
        [
            "object-template",
            "version",
            "revise",
            template_id,
            "1",
            "--no-parent",
            "--property-json",
            json.dumps({"name": "serial", "datatype_id": datatype_id, "required": False}),
            "--component-json",
            json.dumps({"name": "interfaces", "template_id": first_component_id}),
        ],
    )
    with_parent = runner.invoke(
        app,
        [
            "object-template",
            "version",
            "revise",
            template_id,
            "1",
            "--parent-template-id",
            parent_id,
            "--parent-version",
            "3",
            "--property-json",
            json.dumps(
                {
                    "name": "hostname",
                    "datatype_id": datatype_id,
                    "datatype_version": 2,
                    "required": True,
                }
            ),
            "--component-json",
            json.dumps(
                {
                    "name": "modules",
                    "template_id": second_component_id,
                }
            ),
        ],
    )

    assert no_parent.exit_code == 0
    assert with_parent.exit_code == 0
    assert calls == [
        (
            "revise_object_template_version",
            (
                template_id,
                1,
                {
                    "parent": None,
                    "properties": [
                        {"name": "serial", "datatype_id": datatype_id, "required": False}
                    ],
                    "components": [
                        {"name": "interfaces", "template_id": first_component_id}
                    ],
                },
            ),
        ),
        (
            "revise_object_template_version",
            (
                template_id,
                1,
                {
                    "parent": {"template_id": parent_id, "version": 3},
                    "properties": [
                        {
                            "name": "hostname",
                            "datatype_id": datatype_id,
                            "datatype_version": 2,
                            "required": True,
                        }
                    ],
                    "components": [
                        {"name": "modules", "template_id": second_component_id}
                    ],
                },
            ),
        ),
    ]


def test_object_template_version_revise_without_components_sends_empty_components(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    version = _object_template_version_payload()
    calls: list[tuple[str, tuple[Any, ...]]] = []
    _patch_client(monkeypatch, {"revise_object_template_version": version}, calls)
    template_id = str(version["template_id"])

    result = runner.invoke(
        app,
        [
            "object-template",
            "version",
            "revise",
            template_id,
            "1",
            "--no-parent",
        ],
    )

    assert result.exit_code == 0
    assert calls == [
        (
            "revise_object_template_version",
            (
                template_id,
                1,
                {
                    "parent": None,
                    "properties": [],
                    "components": [],
                },
            ),
        )
    ]


def test_object_template_version_revise_file_and_parent_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    version = _object_template_version_payload()
    calls: list[tuple[str, tuple[Any, ...]]] = []
    _patch_client(monkeypatch, {"revise_object_template_version": version}, calls)
    template_id = str(version["template_id"])
    payload = {
        "parent": None,
        "properties": [],
        "components": [{"name": "interfaces", "template_id": str(uuid4())}],
    }

    with TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "revise.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        file_result = runner.invoke(
            app,
            ["object-template", "version", "revise", template_id, "1", "--file", str(path)],
        )

    missing_parent_mode = runner.invoke(
        app,
        ["object-template", "version", "revise", template_id, "1"],
    )

    assert file_result.exit_code == 0
    assert missing_parent_mode.exit_code == 2


def test_object_template_version_lifecycle_commands(monkeypatch: pytest.MonkeyPatch) -> None:
    version = _object_template_version_payload()
    calls: list[tuple[str, tuple[Any, ...]]] = []
    _patch_client(
        monkeypatch,
        {
            "create_object_template_version": version,
            "publish_object_template_version": version,
            "deprecate_object_template_version": version,
        },
        calls,
    )
    template_id = str(version["template_id"])

    assert (
        runner.invoke(
            app,
            ["object-template", "version", "create", template_id, "--source-version", "1"],
        ).exit_code
        == 0
    )
    assert (
        runner.invoke(
            app,
            ["object-template", "version", "publish", template_id, "1"],
        ).exit_code
        == 0
    )
    assert (
        runner.invoke(
            app,
            ["object-template", "version", "deprecate", template_id, "1"],
        ).exit_code
        == 0
    )


def test_object_read_commands_json(monkeypatch: pytest.MonkeyPatch) -> None:
    object_value = _object_payload()
    calls: list[tuple[str, tuple[Any, ...]]] = []
    _patch_client(
        monkeypatch,
        {
            "list_objects": [object_value],
            "get_object": object_value,
        },
        calls,
    )

    listed = runner.invoke(app, ["--output", "json", "object", "list"])
    shown = runner.invoke(app, ["--output", "json", "object", "show", str(object_value["id"])])

    assert listed.exit_code == 0
    assert json.loads(listed.stdout) == [object_value]
    assert shown.exit_code == 0
    assert json.loads(shown.stdout) == object_value


def test_object_create_inline_preserves_exact_json_values(monkeypatch: pytest.MonkeyPatch) -> None:
    object_value = _object_payload()
    calls: list[tuple[str, tuple[Any, ...]]] = []
    _patch_client(monkeypatch, {"create_object": object_value}, calls)
    template_id = str(uuid4())

    result = runner.invoke(
        app,
        [
            "--output",
            "json",
            "object",
            "create",
            "--template-id",
            template_id,
            "--template-version",
            "3",
            "--property-json",
            json.dumps({"hostname": "router-01", "vlan": "100"}),
            "--property-json",
            json.dumps({"enabled": True, "description": None, "tags": [1, None]}),
            "--property-json",
            json.dumps({"metadata": {"site": "lab"}}),
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout) == object_value
    assert calls == [
        (
            "create_object",
            (
                {
                    "template_id": template_id,
                    "template_version": 3,
                    "properties": {
                        "hostname": "router-01",
                        "vlan": "100",
                        "enabled": True,
                        "description": None,
                        "tags": [1, None],
                        "metadata": {"site": "lab"},
                    },
                },
            ),
        )
    ]


def test_object_create_without_properties_sends_empty_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    object_value = _object_payload()
    calls: list[tuple[str, tuple[Any, ...]]] = []
    _patch_client(monkeypatch, {"create_object": object_value}, calls)
    template_id = str(uuid4())

    result = runner.invoke(
        app,
        [
            "object",
            "create",
            "--template-id",
            template_id,
            "--template-version",
            "1",
        ],
    )

    assert result.exit_code == 0
    assert calls == [
        (
            "create_object",
            (
                {
                    "template_id": template_id,
                    "template_version": 1,
                    "properties": {},
                },
            ),
        )
    ]


def test_object_create_file_and_local_input_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    object_value = _object_payload()
    calls: list[tuple[str, tuple[Any, ...]]] = []
    _patch_client(monkeypatch, {"create_object": object_value}, calls)
    payload = {
        "template_id": str(uuid4()),
        "template_version": 2,
        "properties": {"hostname": "router-01"},
    }

    with TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "object.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        file_result = runner.invoke(app, ["object", "create", "--file", str(path)])
        stdin_result = runner.invoke(
            app,
            ["object", "create", "--file", "-"],
            input=path.read_text(encoding="utf-8"),
        )
        mode_conflict = runner.invoke(
            app,
            [
                "object",
                "create",
                "--file",
                str(path),
                "--template-id",
                str(uuid4()),
                "--template-version",
                "1",
            ],
        )

    missing_template = runner.invoke(app, ["object", "create", "--template-id", str(uuid4())])
    malformed_property = runner.invoke(
        app,
        [
            "object",
            "create",
            "--template-id",
            str(uuid4()),
            "--template-version",
            "1",
            "--property-json",
            "not-json",
        ],
    )
    non_object_property = runner.invoke(
        app,
        [
            "object",
            "create",
            "--template-id",
            str(uuid4()),
            "--template-version",
            "1",
            "--property-json",
            "[]",
        ],
    )

    assert file_result.exit_code == 0
    assert stdin_result.exit_code == 0
    assert mode_conflict.exit_code == 2
    assert missing_template.exit_code == 2
    assert malformed_property.exit_code == 2
    assert non_object_property.exit_code == 2
    assert calls[:2] == [("create_object", (payload,)), ("create_object", (payload,))]


def test_object_update_inline_and_file(monkeypatch: pytest.MonkeyPatch) -> None:
    object_value = _object_payload()
    calls: list[tuple[str, tuple[Any, ...]]] = []
    _patch_client(monkeypatch, {"update_object": object_value}, calls)
    object_id = str(object_value["id"])
    file_payload = {"properties": {"description": None}, "remove_properties": ["serial"]}

    inline = runner.invoke(
        app,
        [
            "--output",
            "json",
            "object",
            "update",
            object_id,
            "--property-json",
            json.dumps({"hostname": "router-02"}),
            "--property-json",
            json.dumps({"description": None}),
            "--remove-property",
            "serial",
        ],
    )

    with TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "object-patch.json"
        path.write_text(json.dumps(file_payload), encoding="utf-8")
        file_result = runner.invoke(app, ["object", "update", object_id, "--file", str(path)])

    assert inline.exit_code == 0
    assert json.loads(inline.stdout) == object_value
    assert file_result.exit_code == 0
    assert calls == [
        (
            "update_object",
            (
                object_id,
                {
                    "properties": {"hostname": "router-02", "description": None},
                    "remove_properties": ["serial"],
                },
            ),
        ),
        ("update_object", (object_id, file_payload)),
    ]


def test_object_update_empty_patch_and_local_input_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    object_value = _object_payload()
    calls: list[tuple[str, tuple[Any, ...]]] = []
    _patch_client(monkeypatch, {"update_object": object_value}, calls)
    object_id = str(object_value["id"])

    empty_patch = runner.invoke(app, ["object", "update", object_id])
    malformed_property = runner.invoke(
        app,
        ["object", "update", object_id, "--property-json", "not-json"],
    )
    non_object_property = runner.invoke(
        app,
        ["object", "update", object_id, "--property-json", "[]"],
    )

    with TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "object-patch.json"
        path.write_text("{}", encoding="utf-8")
        mode_conflict = runner.invoke(
            app,
            [
                "object",
                "update",
                object_id,
                "--file",
                str(path),
                "--remove-property",
                "serial",
            ],
        )

    assert empty_patch.exit_code == 0
    assert malformed_property.exit_code == 2
    assert non_object_property.exit_code == 2
    assert mode_conflict.exit_code == 2
    assert calls == [
        (
            "update_object",
            (
                object_id,
                {
                    "properties": None,
                    "remove_properties": [],
                },
            ),
        )
    ]


def test_object_delete_command(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, tuple[Any, ...]]] = []
    _patch_client(monkeypatch, {"delete_object": None}, calls)
    object_id = str(uuid4())

    result = runner.invoke(app, ["object", "delete", object_id])

    assert result.exit_code == 0
    assert f"Deleted object {object_id}" in result.stdout
    assert calls == [("delete_object", (object_id,))]


def test_object_migration_commands(monkeypatch: pytest.MonkeyPatch) -> None:
    analysis = _object_migration_analysis_payload()
    result_payload = _object_migration_result_payload()
    calls: list[tuple[str, tuple[Any, ...]]] = []
    _patch_client(
        monkeypatch,
        {
            "get_object_migration_analysis": analysis,
            "migrate_objects": result_payload,
        },
        calls,
    )
    template_id = str(uuid4())

    analyzed = runner.invoke(
        app,
        [
            "--output",
            "json",
            "object",
            "migrate-analyze",
            "--template-id",
            template_id,
            "--from-version",
            "1",
            "--to-version",
            "2",
        ],
    )
    migrated = runner.invoke(
        app,
        [
            "--output",
            "json",
            "object",
            "migrate",
            "--template-id",
            template_id,
            "--from-version",
            "1",
            "--to-version",
            "2",
            "--property-json",
            json.dumps({"serialnumber": "UNKNOWN", "metadata": {"site": "lab"}}),
        ],
    )

    assert analyzed.exit_code == 0
    assert json.loads(analyzed.stdout) == analysis
    assert migrated.exit_code == 0
    assert json.loads(migrated.stdout) == result_payload
    assert calls == [
        ("get_object_migration_analysis", (template_id, 1, 2)),
        (
            "migrate_objects",
            (
                template_id,
                1,
                {
                    "target_version": 2,
                    "property_values": {
                        "serialnumber": "UNKNOWN",
                        "metadata": {"site": "lab"},
                    },
                },
            ),
        ),
    ]


def test_object_migrate_file_and_local_input_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    result_payload = _object_migration_result_payload()
    calls: list[tuple[str, tuple[Any, ...]]] = []
    _patch_client(monkeypatch, {"migrate_objects": result_payload}, calls)
    template_id = str(uuid4())
    payload = {"target_version": 2, "property_values": {"serialnumber": "UNKNOWN"}}

    with TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "migration.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        file_result = runner.invoke(
            app,
            [
                "object",
                "migrate",
                "--template-id",
                template_id,
                "--from-version",
                "1",
                "--file",
                str(path),
            ],
        )
        mode_conflict = runner.invoke(
            app,
            [
                "object",
                "migrate",
                "--template-id",
                template_id,
                "--from-version",
                "1",
                "--file",
                str(path),
                "--to-version",
                "2",
            ],
        )

    missing_target = runner.invoke(
        app,
        [
            "object",
            "migrate",
            "--template-id",
            template_id,
            "--from-version",
            "1",
        ],
    )
    malformed_property = runner.invoke(
        app,
        [
            "object",
            "migrate",
            "--template-id",
            template_id,
            "--from-version",
            "1",
            "--to-version",
            "2",
            "--property-json",
            "not-json",
        ],
    )
    non_object_property = runner.invoke(
        app,
        [
            "object",
            "migrate",
            "--template-id",
            template_id,
            "--from-version",
            "1",
            "--to-version",
            "2",
            "--property-json",
            "[]",
        ],
    )

    assert file_result.exit_code == 0
    assert mode_conflict.exit_code == 2
    assert missing_target.exit_code == 2
    assert malformed_property.exit_code == 2
    assert non_object_property.exit_code == 2
    assert calls == [("migrate_objects", (template_id, 1, payload))]


def test_object_component_commands(monkeypatch: pytest.MonkeyPatch) -> None:
    membership = _component_membership_payload()
    calls: list[tuple[str, tuple[Any, ...]]] = []
    _patch_client(
        monkeypatch,
        {
            "list_object_components": [membership],
            "attach_object_component": membership,
            "detach_object_component": membership,
        },
        calls,
    )
    parent_id = str(membership["parent_object_id"])
    component_id = str(membership["component_object_id"])

    listed = runner.invoke(app, ["--output", "json", "object", "component", "list", parent_id])
    attached = runner.invoke(
        app,
        [
            "--output",
            "json",
            "object",
            "component",
            "attach",
            parent_id,
            "--slot-name",
            "interfaces",
            "--component-object-id",
            component_id,
        ],
    )
    detached = runner.invoke(
        app,
        ["--output", "json", "object", "component", "detach", component_id],
    )

    assert listed.exit_code == 0
    assert json.loads(listed.stdout) == [membership]
    assert attached.exit_code == 0
    assert json.loads(attached.stdout) == membership
    assert detached.exit_code == 0
    assert json.loads(detached.stdout) == membership
    assert calls == [
        ("list_object_components", (parent_id,)),
        (
            "attach_object_component",
            (
                parent_id,
                {
                    "slot_name": "interfaces",
                    "component_object_id": component_id,
                },
            ),
        ),
        ("detach_object_component", (component_id,)),
    ]


def test_object_component_attach_file_and_local_input_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    membership = _component_membership_payload()
    calls: list[tuple[str, tuple[Any, ...]]] = []
    _patch_client(monkeypatch, {"attach_object_component": membership}, calls)
    parent_id = str(membership["parent_object_id"])
    payload = {"slot_name": "interfaces", "component_object_id": str(uuid4())}

    with TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "attach.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        file_result = runner.invoke(
            app,
            ["object", "component", "attach", parent_id, "--file", str(path)],
        )
        mode_conflict = runner.invoke(
            app,
            [
                "object",
                "component",
                "attach",
                parent_id,
                "--file",
                str(path),
                "--slot-name",
                "interfaces",
            ],
        )

    missing_inline = runner.invoke(app, ["object", "component", "attach", parent_id])

    assert file_result.exit_code == 0
    assert mode_conflict.exit_code == 2
    assert missing_inline.exit_code == 2
    assert calls == [("attach_object_component", (parent_id, payload))]


def test_object_semantic_api_error_flows_through_existing_cli_error_handling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, tuple[Any, ...]]] = []
    _patch_client(
        monkeypatch,
        {"create_object": {}},
        calls,
        error=ApiError(
            status_code=422,
            code="object_validation_failed",
            message="Object validation failed",
            details=[
                {
                    "path": "/properties/hostname",
                    "code": "required",
                    "message": "Property is required.",
                }
            ],
        ),
    )

    result = runner.invoke(
        app,
        [
            "--output",
            "json",
            "object",
            "create",
            "--template-id",
            str(uuid4()),
            "--template-version",
            "1",
        ],
    )

    assert result.exit_code == 1
    assert result.stdout == ""
    assert json.loads(result.stderr)["error"]["code"] == "object_validation_failed"


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
    assert runner.invoke(app, ["object-template", "show", "not-a-uuid"]).exit_code == 2
    assert (
        runner.invoke(
            app,
            ["object-template", "version", "show", str(uuid4()), "0"],
        ).exit_code
        == 2
    )
    assert (
        runner.invoke(
            app,
            ["object-template", "version", "create", str(uuid4()), "--source-version", "0"],
        ).exit_code
        == 2
    )
    assert runner.invoke(app, ["object", "show", "not-a-uuid"]).exit_code == 2
    assert runner.invoke(app, ["object", "delete", "not-a-uuid"]).exit_code == 2
    assert (
        runner.invoke(
            app,
            [
                "object",
                "migrate-analyze",
                "--template-id",
                "not-a-uuid",
                "--from-version",
                "1",
                "--to-version",
                "2",
            ],
        ).exit_code
        == 2
    )
    assert (
        runner.invoke(
            app,
            [
                "object",
                "migrate",
                "--template-id",
                str(uuid4()),
                "--from-version",
                "0",
                "--to-version",
                "2",
            ],
        ).exit_code
        == 2
    )
    assert (
        runner.invoke(
            app,
            ["object", "create", "--template-id", str(uuid4()), "--template-version", "0"],
        ).exit_code
        == 2
    )
    assert runner.invoke(app, ["object", "component", "list", "not-a-uuid"]).exit_code == 2
    assert (
        runner.invoke(
            app,
            [
                "object",
                "component",
                "attach",
                str(uuid4()),
                "--component-object-id",
                "not-a-uuid",
                "--slot-name",
                "interfaces",
            ],
        ).exit_code
        == 2
    )
    assert (
        runner.invoke(
            app,
            [
                "object-template",
                "create",
                "--namespace",
                "network",
                "--name",
                "device",
                "--parent-template-id",
                str(uuid4()),
                "--parent-version",
                "0",
            ],
        ).exit_code
        == 2
    )


@pytest.mark.parametrize(
    ("command", "payloads", "expected_text"),
    [
        (
            ["object-template", "list"],
            {"list_object_templates": [_object_template_payload()]},
            "network.device",
        ),
        (
            ["object-template", "show", str(_object_template_payload()["id"])],
            {"get_object_template": _object_template_payload()},
            "Abstract: yes",
        ),
        (
            [
                "object-template",
                "version",
                "list",
                str(_object_template_version_payload()["template_id"]),
            ],
            {"list_object_template_versions": [_object_template_version_payload()]},
            "COMPONENTS",
        ),
        (
            [
                "object-template",
                "version",
                "show",
                str(_object_template_version_payload()["template_id"]),
                "1",
            ],
            {"get_object_template_version": _object_template_version_payload()},
            "Components:",
        ),
    ],
)
def test_object_template_human_rendering(
    monkeypatch: pytest.MonkeyPatch,
    command: list[str],
    payloads: dict[str, Any],
    expected_text: str,
) -> None:
    calls: list[tuple[str, tuple[Any, ...]]] = []
    _patch_client(monkeypatch, payloads, calls)

    result = runner.invoke(app, command)

    assert result.exit_code == 0
    assert expected_text in result.stdout


@pytest.mark.parametrize(
    ("command", "payloads", "expected_text"),
    [
        (
            ["object", "list"],
            {"list_objects": [_object_payload()]},
            "TEMPLATE VERSION",
        ),
        (
            ["object", "show", str(_object_payload()["id"])],
            {"get_object": _object_payload()},
            "Properties:",
        ),
        (
            [
                "object",
                "component",
                "list",
                str(_component_membership_payload()["parent_object_id"]),
            ],
            {"list_object_components": [_component_membership_payload()]},
            "COMPONENT OBJECT ID",
        ),
        (
            [
                "object",
                "component",
                "detach",
                str(_component_membership_payload()["component_object_id"]),
            ],
            {"detach_object_component": _component_membership_payload()},
            "Detached component",
        ),
        (
            [
                "object",
                "migrate-analyze",
                "--template-id",
                str(_object_migration_analysis_payload()["template_id"]),
                "--from-version",
                "1",
                "--to-version",
                "2",
            ],
            {"get_object_migration_analysis": _object_migration_analysis_payload()},
            "Added Properties:",
        ),
        (
            [
                "object",
                "migrate",
                "--template-id",
                str(_object_migration_result_payload()["template_id"]),
                "--from-version",
                "1",
                "--to-version",
                "2",
            ],
            {"migrate_objects": _object_migration_result_payload()},
            "Migrated objects",
        ),
    ],
)
def test_object_human_rendering(
    monkeypatch: pytest.MonkeyPatch,
    command: list[str],
    payloads: dict[str, Any],
    expected_text: str,
) -> None:
    calls: list[tuple[str, tuple[Any, ...]]] = []
    _patch_client(monkeypatch, payloads, calls)

    result = runner.invoke(app, command)

    assert result.exit_code == 0
    assert expected_text in result.stdout


@pytest.mark.parametrize(
    ("payload", "command"),
    [
        ({"id": str(uuid4())}, ["object", "show", str(uuid4())]),
        (
            {"parent_object_id": str(uuid4()), "slot_name": "interfaces"},
            ["object", "component", "detach", str(uuid4())],
        ),
    ],
)
def test_object_malformed_success_payload_maps_to_protocol_error(
    monkeypatch: pytest.MonkeyPatch,
    payload: dict[str, object],
    command: list[str],
) -> None:
    calls: list[tuple[str, tuple[Any, ...]]] = []
    payload_key = "get_object" if command[1] == "show" else "detach_object_component"
    _patch_client(monkeypatch, {payload_key: payload}, calls)

    result = runner.invoke(app, command)

    assert result.exit_code == 4
    assert "cli_protocol_error" in result.stderr


def test_object_template_version_human_output_includes_pinned_local_components(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    version = _object_template_version_payload()
    calls: list[tuple[str, tuple[Any, ...]]] = []
    _patch_client(monkeypatch, {"get_object_template_version": version}, calls)

    result = runner.invoke(
        app,
        ["object-template", "version", "show", str(version["template_id"]), "1"],
    )

    components = version["components"]
    assert isinstance(components, list)
    component = components[0]
    assert isinstance(component, dict)
    assert result.exit_code == 0
    expected = (
        f"{component['name']}: "
        f"{component['template_id']}"
    )
    assert expected in result.stdout


def test_object_template_version_human_output_renders_empty_components(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    version = _object_template_version_payload()
    version["components"] = []
    calls: list[tuple[str, tuple[Any, ...]]] = []
    _patch_client(monkeypatch, {"get_object_template_version": version}, calls)

    result = runner.invoke(
        app,
        ["object-template", "version", "show", str(version["template_id"]), "1"],
    )

    assert result.exit_code == 0
    assert "Components:\n  (none)" in result.stdout


@pytest.mark.parametrize(
    "payload",
    [
        {
            "template_id": str(uuid4()),
            "version": 1,
            "status": "draft",
            "parent": None,
            "properties": [],
        },
        {
            "template_id": str(uuid4()),
            "version": 1,
            "status": "draft",
            "parent": None,
            "properties": [],
            "components": {},
        },
        {
            "template_id": str(uuid4()),
            "version": 1,
            "status": "draft",
            "parent": None,
            "properties": [],
            "components": ["bad"],
        },
        {
            "template_id": str(uuid4()),
            "version": 1,
            "status": "draft",
            "parent": None,
            "properties": [],
            "components": [
                {
                    "name": "interfaces",
                    "template_id": 123,
                }
            ],
        },
    ],
)
def test_object_template_version_component_protocol_errors(
    monkeypatch: pytest.MonkeyPatch,
    payload: dict[str, object],
) -> None:
    calls: list[tuple[str, tuple[Any, ...]]] = []
    _patch_client(monkeypatch, {"get_object_template_version": payload}, calls)

    result = runner.invoke(
        app,
        ["object-template", "version", "show", str(uuid4()), "1"],
    )

    assert result.exit_code == 4
    assert "cli_protocol_error" in result.stderr


def test_object_template_malformed_success_payload_maps_to_protocol_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, tuple[Any, ...]]] = []
    _patch_client(monkeypatch, {"get_object_template": {"id": "x"}}, calls)

    result = runner.invoke(app, ["object-template", "show", str(uuid4())])

    assert result.exit_code == 4
    assert "cli_protocol_error" in result.stderr


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
    _patch_client(
        monkeypatch,
        {"list_datatypes": [], "list_object_templates": []},
        calls,
        error=error,
    )

    datatype_result = runner.invoke(app, ["--output", "json", "datatype", "list"])
    object_template_result = runner.invoke(app, ["--output", "json", "object-template", "list"])

    assert datatype_result.exit_code == exit_code
    assert datatype_result.stdout == ""
    assert stderr_code in datatype_result.stderr
    assert object_template_result.exit_code == exit_code
    assert object_template_result.stdout == ""
    assert stderr_code in object_template_result.stderr
