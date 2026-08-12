from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from typer.testing import CliRunner

from netauto.cli.app import app

pytestmark = pytest.mark.postgresql

runner = CliRunner()

_BASE_URL: str | None = None


class _NoopEngine:
    def dispose(self) -> None:
        return None


@pytest.fixture(autouse=True)
def _configure_postgresql_base_url(postgresql_application_base_url: str) -> Iterator[None]:
    global _BASE_URL
    _BASE_URL = postgresql_application_base_url
    try:
        yield
    finally:
        _BASE_URL = None


def _server_url(tmp_path: Path):
    del tmp_path
    assert _BASE_URL is not None
    return _NoopEngine(), _single_use_server(_BASE_URL)


@contextmanager
def _single_use_server(base_url: str):
    yield base_url


def test_cli_objecttemplate_acceptance_flow(tmp_path: Path) -> None:
    engine, server = _server_url(tmp_path)
    try:
        with server as base_url:
            hostname_created = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "datatype",
                    "create",
                    "--namespace",
                    "network",
                    "--name",
                    "hostname",
                    "--description",
                    "Hostname",
                    "--base-type",
                    "core.string",
                ],
            )
            assert hostname_created.exit_code == 0
            hostname_payload = json.loads(hostname_created.stdout)
            hostname_id = hostname_payload["datatype"]["id"]

            serial_created = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "datatype",
                    "create",
                    "--namespace",
                    "network",
                    "--name",
                    "serial",
                    "--description",
                    "Serial",
                    "--base-type",
                    "core.string",
                ],
            )
            assert serial_created.exit_code == 0
            serial_payload = json.loads(serial_created.stdout)
            serial_id = serial_payload["datatype"]["id"]

            assert (
                runner.invoke(
                    app,
                    [
                        "--api-url",
                        base_url,
                        "datatype",
                        "version",
                        "publish",
                        hostname_id,
                        "1",
                    ],
                ).exit_code
                == 0
            )
            assert (
                runner.invoke(
                    app,
                    [
                        "--api-url",
                        base_url,
                        "datatype",
                        "version",
                        "publish",
                        serial_id,
                        "1",
                    ],
                ).exit_code
                == 0
            )

            device_payload = {
                "namespace": "network",
                "name": "device",
                "description": "Device template",
                "abstract": True,
                "parent": None,
                "properties": [
                    {
                        "name": "hostname",
                        "datatype_id": hostname_id,
                        "required": True,
                    }
                ],
            }
            router_payload = {
                "namespace": "network",
                "name": "router",
                "description": "Router template",
                "abstract": False,
                "properties": [
                    {
                        "name": "serial",
                        "datatype_id": serial_id,
                        "required": False,
                    }
                ],
            }

            with TemporaryDirectory() as temp_dir:
                device_path = Path(temp_dir) / "device.json"
                device_path.write_text(json.dumps(device_payload), encoding="utf-8")
                device_created = runner.invoke(
                    app,
                    [
                        "--api-url",
                        base_url,
                        "--output",
                        "json",
                        "object-template",
                        "create",
                        "--file",
                        str(device_path),
                    ],
                )
                assert device_created.exit_code == 0
                device_created_payload = json.loads(device_created.stdout)
                device_id = device_created_payload["object_template"]["id"]
                assert device_created_payload["object_template"]["abstract"] is True
                assert device_created_payload["version"]["properties"][0]["datatype_version"] == 1

                assert (
                    runner.invoke(
                        app,
                        [
                            "--api-url",
                            base_url,
                            "object-template",
                            "version",
                            "publish",
                            device_id,
                            "1",
                        ],
                    ).exit_code
                    == 0
                )

                router_payload["parent"] = {"template_id": device_id, "version": 1}
                router_path = Path(temp_dir) / "router.json"
                router_path.write_text(json.dumps(router_payload), encoding="utf-8")
                router_created = runner.invoke(
                    app,
                    [
                        "--api-url",
                        base_url,
                        "--output",
                        "json",
                        "object-template",
                        "create",
                        "--file",
                        str(router_path),
                    ],
                )
                assert router_created.exit_code == 0
                router_created_payload = json.loads(router_created.stdout)
                router_id = router_created_payload["object_template"]["id"]
                assert router_created_payload["version"]["parent"] == {
                    "template_id": device_id,
                    "version": 1,
                }
                assert router_created_payload["version"]["properties"] == [
                    {
                        "name": "serial",
                        "datatype_id": serial_id,
                        "datatype_version": 1,
                        "required": False,
                    }
                ]

                router_published = runner.invoke(
                    app,
                    [
                        "--api-url",
                        base_url,
                        "--output",
                        "json",
                        "object-template",
                        "version",
                        "publish",
                        router_id,
                        "1",
                    ],
                )
                assert router_published.exit_code == 0
                assert json.loads(router_published.stdout)["status"] == "published"

                listed = runner.invoke(
                    app,
                    [
                        "--api-url",
                        base_url,
                        "--output",
                        "json",
                        "object-template",
                        "list",
                    ],
                )
                assert listed.exit_code == 0
                listed_payload = json.loads(listed.stdout)
                assert {item["qualified_name"] for item in listed_payload} == {
                    "network.device",
                    "network.router",
                }

                shown_name = runner.invoke(
                    app,
                    [
                        "--api-url",
                        base_url,
                        "--output",
                        "json",
                        "object-template",
                        "show-name",
                        "network",
                        "router",
                    ],
                )
                assert shown_name.exit_code == 0
                shown_name_payload = json.loads(shown_name.stdout)
                assert shown_name_payload["id"] == router_id
                assert shown_name_payload["qualified_name"] == "network.router"
                assert shown_name_payload["abstract"] is False

                version_list = runner.invoke(
                    app,
                    [
                        "--api-url",
                        base_url,
                        "--output",
                        "json",
                        "object-template",
                        "version",
                        "list",
                        router_id,
                    ],
                )
                assert version_list.exit_code == 0
                assert json.loads(version_list.stdout) == [
                    {
                        "template_id": router_id,
                        "version": 1,
                        "status": "published",
                        "parent": {"template_id": device_id, "version": 1},
                        "properties": [
                            {
                                "name": "serial",
                                "datatype_id": serial_id,
                                "datatype_version": 1,
                                "required": False,
                            }
                        ],
                        "components": [],
                    }
                ]

                version_show = runner.invoke(
                    app,
                    [
                        "--api-url",
                        base_url,
                        "--output",
                        "json",
                        "object-template",
                        "version",
                        "show",
                        router_id,
                        "1",
                    ],
                )
                assert version_show.exit_code == 0
                version_show_payload = json.loads(version_show.stdout)
                assert version_show_payload["parent"] == {"template_id": device_id, "version": 1}
                assert version_show_payload["properties"][0]["datatype_version"] == 1
                assert version_show_payload["components"] == []
                assert version_show_payload["status"] == "published"

                human_show = runner.invoke(
                    app,
                    [
                        "--api-url",
                        base_url,
                        "object-template",
                        "show-name",
                        "network",
                        "device",
                    ],
                )
                assert human_show.exit_code == 0
                assert "Qualified Name: network.device" in human_show.stdout
                assert "Abstract: yes" in human_show.stdout

                router_v2 = runner.invoke(
                    app,
                    [
                        "--api-url",
                        base_url,
                        "--output",
                        "json",
                        "object-template",
                        "version",
                        "create",
                        router_id,
                        "--source-version",
                        "1",
                    ],
                )
                assert router_v2.exit_code == 0
                router_v2_payload = json.loads(router_v2.stdout)
                assert router_v2_payload == {
                    "template_id": router_id,
                    "version": 2,
                    "status": "draft",
                    "parent": {"template_id": device_id, "version": 1},
                    "properties": [
                        {
                            "name": "serial",
                            "datatype_id": serial_id,
                            "datatype_version": 1,
                            "required": False,
                        }
                    ],
                    "components": [],
                }

                router_v2_published = runner.invoke(
                    app,
                    [
                        "--api-url",
                        base_url,
                        "--output",
                        "json",
                        "object-template",
                        "version",
                        "publish",
                        router_id,
                        "2",
                    ],
                )
                assert router_v2_published.exit_code == 0
                assert json.loads(router_v2_published.stdout)["status"] == "published"

                router_v1_deprecated = runner.invoke(
                    app,
                    [
                        "--api-url",
                        base_url,
                        "--output",
                        "json",
                        "object-template",
                        "version",
                        "deprecate",
                        router_id,
                        "1",
                    ],
                )
                assert router_v1_deprecated.exit_code == 0
                assert json.loads(router_v1_deprecated.stdout)["status"] == "deprecated"

                final_versions = runner.invoke(
                    app,
                    [
                        "--api-url",
                        base_url,
                        "--output",
                        "json",
                        "object-template",
                        "version",
                        "list",
                        router_id,
                    ],
                )
                assert final_versions.exit_code == 0
                final_versions_payload = json.loads(final_versions.stdout)
                assert [(item["version"], item["status"]) for item in final_versions_payload] == [
                    (1, "deprecated"),
                    (2, "published"),
                ]
    finally:
        engine.dispose()


def test_cli_objecttemplate_component_acceptance_flow(tmp_path: Path) -> None:
    engine, server = _server_url(tmp_path)
    try:
        with server as base_url:
            network_interface_created = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "object-template",
                    "create",
                    "--namespace",
                    "network",
                    "--name",
                    "network_interface",
                    "--description",
                    "Network interface template",
                    "--abstract",
                ],
            )
            assert network_interface_created.exit_code == 0
            network_interface_payload = json.loads(network_interface_created.stdout)
            network_interface_id = network_interface_payload["object_template"]["id"]
            assert network_interface_payload["object_template"]["abstract"] is True
            assert network_interface_payload["version"]["components"] == []

            interface_v1_published = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "object-template",
                    "version",
                    "publish",
                    network_interface_id,
                    "1",
                ],
            )
            assert interface_v1_published.exit_code == 0

            interface_v2 = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "object-template",
                    "version",
                    "create",
                    network_interface_id,
                    "--source-version",
                    "1",
                ],
            )
            assert interface_v2.exit_code == 0
            assert json.loads(interface_v2.stdout)["version"] == 2

            interface_v2_published = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "object-template",
                    "version",
                    "publish",
                    network_interface_id,
                    "2",
                ],
            )
            assert interface_v2_published.exit_code == 0

            network_device_created = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "object-template",
                    "create",
                    "--namespace",
                    "network",
                    "--name",
                    "network_device",
                    "--description",
                    "Network device template",
                    "--abstract",
                    "--component-json",
                    json.dumps(
                        {
                            "name": "interfaces",
                            "template_id": network_interface_id,
                        }
                    ),
                ],
            )
            assert network_device_created.exit_code == 0
            network_device_payload = json.loads(network_device_created.stdout)
            network_device_id = network_device_payload["object_template"]["id"]
            assert network_device_payload["version"]["components"] == [
                {
                    "name": "interfaces",
                    "template_id": network_interface_id,
                }
            ]

            device_v1_published = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "object-template",
                    "version",
                    "publish",
                    network_device_id,
                    "1",
                ],
            )
            assert device_v1_published.exit_code == 0

            human_version_show = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "object-template",
                    "version",
                    "show",
                    network_device_id,
                    "1",
                ],
            )
            assert human_version_show.exit_code == 0
            assert "Components:" in human_version_show.stdout
            assert f"interfaces: {network_interface_id}" in human_version_show.stdout

            human_version_list = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "object-template",
                    "version",
                    "list",
                    network_device_id,
                ],
            )
            assert human_version_list.exit_code == 0
            assert "COMPONENTS" in human_version_list.stdout
            assert (
                "  1" in human_version_list.stdout
                or human_version_list.stdout.rstrip().endswith("1")
            )

            interface_v3 = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "object-template",
                    "version",
                    "create",
                    network_interface_id,
                    "--source-version",
                    "2",
                ],
            )
            assert interface_v3.exit_code == 0
            assert json.loads(interface_v3.stdout)["version"] == 3

            interface_v3_published = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "object-template",
                    "version",
                    "publish",
                    network_interface_id,
                    "3",
                ],
            )
            assert interface_v3_published.exit_code == 0

            network_device_v2 = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "object-template",
                    "version",
                    "create",
                    network_device_id,
                    "--source-version",
                    "1",
                ],
            )
            assert network_device_v2.exit_code == 0
            assert json.loads(network_device_v2.stdout) == {
                "template_id": network_device_id,
                "version": 2,
                "status": "draft",
                "parent": None,
                "properties": [],
                "components": [
                    {
                        "name": "interfaces",
                        "template_id": network_interface_id,
                    }
                ],
            }
    finally:
        engine.dispose()


def test_cli_objecttemplate_revise_rejects_datatype_version_downgrade(tmp_path: Path) -> None:
    engine, server = _server_url(tmp_path)
    try:
        with server as base_url:
            email_created = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "datatype",
                    "create",
                    "--namespace",
                    "common",
                    "--name",
                    "email",
                    "--description",
                    "Email",
                    "--base-type",
                    "core.string",
                ],
            )
            assert email_created.exit_code == 0
            datatype_id = json.loads(email_created.stdout)["datatype"]["id"]

            for version in (1,):
                assert (
                    runner.invoke(
                        app,
                        [
                            "--api-url",
                            base_url,
                            "datatype",
                            "version",
                            "publish",
                            datatype_id,
                            str(version),
                        ],
                    ).exit_code
                    == 0
                )

            for source_version in ("1", "2"):
                created_next = runner.invoke(
                    app,
                    [
                        "--api-url",
                        base_url,
                        "datatype",
                        "version",
                        "create",
                        datatype_id,
                        "--source-version",
                        source_version,
                    ],
                )
                if source_version == "1":
                    assert created_next.exit_code == 0
                    assert (
                        runner.invoke(
                            app,
                            [
                                "--api-url",
                                base_url,
                                "datatype",
                                "version",
                                "publish",
                                datatype_id,
                                "2",
                            ],
                        ).exit_code
                        == 0
                    )
                else:
                    assert created_next.exit_code == 0
                    assert (
                        runner.invoke(
                            app,
                            [
                                "--api-url",
                                base_url,
                                "datatype",
                                "version",
                                "publish",
                                datatype_id,
                                "3",
                            ],
                        ).exit_code
                        == 0
                    )

            object_template_created = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "object-template",
                    "create",
                    "--namespace",
                    "network",
                    "--name",
                    "contact",
                    "--description",
                    "Contact template",
                    "--property-json",
                    json.dumps(
                        {
                            "name": "e_mail",
                            "datatype_id": datatype_id,
                            "datatype_version": 3,
                            "required": False,
                        }
                    ),
                ],
            )
            assert object_template_created.exit_code == 0
            template_id = json.loads(object_template_created.stdout)["object_template"]["id"]

            downgraded = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "object-template",
                    "version",
                    "revise",
                    template_id,
                    "1",
                    "--no-parent",
                    "--property-json",
                    json.dumps(
                        {
                            "name": "e_mail",
                            "datatype_id": datatype_id,
                            "datatype_version": 2,
                            "required": False,
                        }
                    ),
                ],
            )
            assert downgraded.exit_code == 1
            assert "object_template_datatype_version_downgrade" in downgraded.stderr

            shown = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "object-template",
                    "version",
                    "show",
                    template_id,
                    "1",
                ],
            )
            assert shown.exit_code == 0
            shown_payload = json.loads(shown.stdout)
            assert shown_payload["properties"][0]["datatype_version"] == 3

            upgraded = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "object-template",
                    "version",
                    "revise",
                    template_id,
                    "1",
                    "--no-parent",
                    "--property-json",
                    json.dumps(
                        {
                            "name": "e_mail",
                            "datatype_id": datatype_id,
                            "datatype_version": 3,
                            "required": True,
                        }
                    ),
                ],
            )
            assert upgraded.exit_code == 0
            upgraded_payload = json.loads(upgraded.stdout)
            assert upgraded_payload["properties"][0]["datatype_version"] == 3
            assert upgraded_payload["properties"][0]["required"] is True
    finally:
        engine.dispose()


def test_cli_objecttemplate_revise_omitted_parent_preserves_existing_parent(tmp_path: Path) -> None:
    engine, server = _server_url(tmp_path)
    try:
        with server as base_url:
            datatype_created = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "datatype",
                    "create",
                    "--namespace",
                    "network",
                    "--name",
                    "hostname_preserve_parent",
                    "--description",
                    "Hostname",
                    "--base-type",
                    "core.string",
                ],
            )
            assert datatype_created.exit_code == 0
            datatype_id = json.loads(datatype_created.stdout)["datatype"]["id"]
            assert (
                runner.invoke(
                    app,
                    [
                        "--api-url",
                        base_url,
                        "datatype",
                        "version",
                        "publish",
                        datatype_id,
                        "1",
                    ],
                ).exit_code
                == 0
            )

            parent_created = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "object-template",
                    "create",
                    "--namespace",
                    "network",
                    "--name",
                    "base_preserve_parent",
                    "--description",
                    "Base template",
                    "--abstract",
                    "--property-json",
                    json.dumps(
                        {
                            "name": "hostname",
                            "datatype_id": datatype_id,
                            "required": True,
                        }
                    ),
                ],
            )
            assert parent_created.exit_code == 0
            parent_id = json.loads(parent_created.stdout)["object_template"]["id"]
            assert (
                runner.invoke(
                    app,
                    [
                        "--api-url",
                        base_url,
                        "object-template",
                        "version",
                        "publish",
                        parent_id,
                        "1",
                    ],
                ).exit_code
                == 0
            )

            child_created = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "object-template",
                    "create",
                    "--namespace",
                    "network",
                    "--name",
                    "device_preserve_parent",
                    "--description",
                    "Device template",
                    "--parent-template-id",
                    parent_id,
                    "--parent-version",
                    "1",
                    "--property-json",
                    json.dumps(
                        {
                            "name": "serial",
                            "datatype_id": datatype_id,
                            "required": False,
                        }
                    ),
                ],
            )
            assert child_created.exit_code == 0
            child_payload = json.loads(child_created.stdout)
            template_id = child_payload["object_template"]["id"]

            revised = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "object-template",
                    "version",
                    "revise",
                    template_id,
                    "1",
                    "--property-json",
                    json.dumps(
                        {
                            "name": "asset_tag",
                            "datatype_id": datatype_id,
                            "required": False,
                        }
                    ),
                ],
            )
            assert revised.exit_code == 0
            revised_payload = json.loads(revised.stdout)
            assert revised_payload["parent"] == {
                "template_id": parent_id,
                "version": 1,
            }
            assert revised_payload["properties"] == [
                {
                    "name": "asset_tag",
                    "datatype_id": datatype_id,
                    "datatype_version": 1,
                    "required": False,
                }
            ]
    finally:
        engine.dispose()


def test_cli_objecttemplate_create_next_accepts_deprecated_source(tmp_path: Path) -> None:
    engine, server = _server_url(tmp_path)
    try:
        with server as base_url:
            hostname_created = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "datatype",
                    "create",
                    "--namespace",
                    "network",
                    "--name",
                    "hostname_recovery",
                    "--description",
                    "Hostname",
                    "--base-type",
                    "core.string",
                ],
            )
            assert hostname_created.exit_code == 0
            datatype_id = json.loads(hostname_created.stdout)["datatype"]["id"]

            assert (
                runner.invoke(
                    app,
                    [
                        "--api-url",
                        base_url,
                        "datatype",
                        "version",
                        "publish",
                        datatype_id,
                        "1",
                    ],
                ).exit_code
                == 0
            )

            parent_created = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "object-template",
                    "create",
                    "--namespace",
                    "network",
                    "--name",
                    "base_recovery",
                    "--description",
                    "Base template",
                    "--abstract",
                    "--property-json",
                    json.dumps(
                        {
                            "name": "hostname",
                            "datatype_id": datatype_id,
                            "required": True,
                        }
                    ),
                ],
            )
            assert parent_created.exit_code == 0
            parent_id = json.loads(parent_created.stdout)["object_template"]["id"]
            assert (
                runner.invoke(
                    app,
                    [
                        "--api-url",
                        base_url,
                        "object-template",
                        "version",
                        "publish",
                        parent_id,
                        "1",
                    ],
                ).exit_code
                == 0
            )

            created = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "object-template",
                    "create",
                    "--namespace",
                    "network",
                    "--name",
                    "device_recovery",
                    "--description",
                    "Device template",
                    "--parent-template-id",
                    parent_id,
                    "--parent-version",
                    "1",
                    "--property-json",
                    json.dumps(
                        {
                            "name": "serial",
                            "datatype_id": datatype_id,
                            "required": False,
                        }
                    ),
                ],
            )
            assert created.exit_code == 0
            created_payload = json.loads(created.stdout)
            template_id = created_payload["object_template"]["id"]

            published_v1 = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "object-template",
                    "version",
                    "publish",
                    template_id,
                    "1",
                ],
            )
            assert published_v1.exit_code == 0

            created_v2 = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "object-template",
                    "version",
                    "create",
                    template_id,
                    "--source-version",
                    "1",
                ],
            )
            assert created_v2.exit_code == 0
            v2_payload = json.loads(created_v2.stdout)

            published_v2 = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "object-template",
                    "version",
                    "publish",
                    template_id,
                    "2",
                ],
            )
            assert published_v2.exit_code == 0

            deprecated_v1 = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "object-template",
                    "version",
                    "deprecate",
                    template_id,
                    "1",
                ],
            )
            assert deprecated_v1.exit_code == 0
            deprecated_v2 = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "object-template",
                    "version",
                    "deprecate",
                    template_id,
                    "2",
                ],
            )
            assert deprecated_v2.exit_code == 0

            created_v3 = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "object-template",
                    "version",
                    "create",
                    template_id,
                    "--source-version",
                    "2",
                ],
            )
            assert created_v3.exit_code == 0
            v3_payload = json.loads(created_v3.stdout)

            versions = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "object-template",
                    "version",
                    "list",
                    template_id,
                ],
            )
            assert versions.exit_code == 0

            assert v3_payload["version"] == 3
            assert v3_payload["status"] == "draft"
            assert v3_payload["parent"] == v2_payload["parent"]
            assert v3_payload["properties"] == v2_payload["properties"]
            assert v3_payload["components"] == v2_payload["components"]
            assert [(item["version"], item["status"]) for item in json.loads(versions.stdout)] == [
                (1, "deprecated"),
                (2, "deprecated"),
                (3, "draft"),
            ]
    finally:
        engine.dispose()
