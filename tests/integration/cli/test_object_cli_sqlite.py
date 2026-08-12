from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from netauto.api.app import create_app
from netauto.cli.app import app
from netauto.persistence.sqlalchemy.database import create_schema, create_sqlite_engine
from netauto.persistence.sqlalchemy.unit_of_work import (
    SqlAlchemyUnitOfWork,
    SqliteModelWriteUnitOfWork,
)
from support.http_server import serve_app_url

runner = CliRunner()


def _server_url(tmp_path: Path):
    engine = create_sqlite_engine(f"sqlite:///{tmp_path / 'object-cli.sqlite3'}")
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)

    def uow_factory() -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(session_factory)

    return engine, serve_app_url(
        create_app(
            uow_factory,
            model_write_uow_factory=lambda: SqliteModelWriteUnitOfWork(session_factory),
            ownership_graph_uow_factory=uow_factory,
        )
    )


def _invoke_json(base_url: str, args: list[str]):
    result = runner.invoke(app, ["--api-url", base_url, "--output", "json", *args])
    assert result.exit_code == 0, result.stderr
    return json.loads(result.stdout)


def test_cli_object_acceptance_flow(tmp_path: Path) -> None:
    engine, server = _server_url(tmp_path)
    try:
        with server as base_url:
            hostname_created = _invoke_json(
                base_url,
                [
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
            serial_created = _invoke_json(
                base_url,
                [
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
            hostname_id = hostname_created["datatype"]["id"]
            serial_id = serial_created["datatype"]["id"]

            assert (
                runner.invoke(
                    app,
                    ["--api-url", base_url, "datatype", "version", "publish", hostname_id, "1"],
                ).exit_code
                == 0
            )
            assert (
                runner.invoke(
                    app,
                    ["--api-url", base_url, "datatype", "version", "publish", serial_id, "1"],
                ).exit_code
                == 0
            )

            port_template = _invoke_json(
                base_url,
                [
                    "object-template",
                    "create",
                    "--namespace",
                    "network",
                    "--name",
                    "port",
                ],
            )
            port_template_id = port_template["object_template"]["id"]
            assert (
                runner.invoke(
                    app,
                    [
                        "--api-url",
                        base_url,
                        "object-template",
                        "version",
                        "publish",
                        port_template_id,
                        "1",
                    ],
                ).exit_code
                == 0
            )

            bundle_template = _invoke_json(
                base_url,
                [
                    "object-template",
                    "create",
                    "--namespace",
                    "network",
                    "--name",
                    "bundle",
                    "--component-json",
                    json.dumps({"name": "members", "template_id": port_template_id}),
                ],
            )
            bundle_template_id = bundle_template["object_template"]["id"]
            assert (
                runner.invoke(
                    app,
                    [
                        "--api-url",
                        base_url,
                        "object-template",
                        "version",
                        "publish",
                        bundle_template_id,
                        "1",
                    ],
                ).exit_code
                == 0
            )

            device_template = _invoke_json(
                base_url,
                [
                    "object-template",
                    "create",
                    "--namespace",
                    "network",
                    "--name",
                    "device",
                    "--property-json",
                    json.dumps(
                        {
                            "name": "hostname",
                            "datatype_id": hostname_id,
                            "required": True,
                        }
                    ),
                    "--property-json",
                    json.dumps(
                        {
                            "name": "serial",
                            "datatype_id": serial_id,
                            "required": False,
                        }
                    ),
                    "--component-json",
                    json.dumps({"name": "interfaces", "template_id": bundle_template_id}),
                ],
            )
            device_template_id = device_template["object_template"]["id"]
            assert (
                runner.invoke(
                    app,
                    [
                        "--api-url",
                        base_url,
                        "object-template",
                        "version",
                        "publish",
                        device_template_id,
                        "1",
                    ],
                ).exit_code
                == 0
            )

            device = _invoke_json(
                base_url,
                [
                    "object",
                    "create",
                    "--template-id",
                    device_template_id,
                    "--template-version",
                    "1",
                    "--property-json",
                    json.dumps({"hostname": "router-01"}),
                    "--property-json",
                    json.dumps({"serial": "ABC123"}),
                ],
            )
            device_id = device["id"]
            assert device["template_id"] == device_template_id
            assert device["template_version"] == 1
            assert device["properties"]["hostname"] == "router-01"
            assert device["properties"]["serial"] == "ABC123"

            bundle = _invoke_json(
                base_url,
                [
                    "object",
                    "create",
                    "--template-id",
                    bundle_template_id,
                    "--template-version",
                    "1",
                ],
            )
            bundle_id = bundle["id"]

            port = _invoke_json(
                base_url,
                [
                    "object",
                    "create",
                    "--template-id",
                    port_template_id,
                    "--template-version",
                    "1",
                ],
            )
            port_id = port["id"]

            listed = _invoke_json(base_url, ["object", "list"])
            assert {item["id"] for item in listed} >= {device_id, bundle_id, port_id}

            updated = _invoke_json(
                base_url,
                [
                    "object",
                    "update",
                    device_id,
                    "--property-json",
                    json.dumps({"hostname": "router-02"}),
                ],
            )
            assert updated["properties"]["hostname"] == "router-02"
            assert updated["properties"]["serial"] == "ABC123"

            removed = _invoke_json(
                base_url,
                [
                    "object",
                    "update",
                    device_id,
                    "--remove-property",
                    "serial",
                ],
            )
            assert removed["properties"]["hostname"] == "router-02"
            assert "serial" not in removed["properties"]

            attached_bundle = _invoke_json(
                base_url,
                [
                    "object",
                    "component",
                    "attach",
                    device_id,
                    "--slot-name",
                    "interfaces",
                    "--component-object-id",
                    bundle_id,
                ],
            )
            assert attached_bundle == {
                "parent_object_id": device_id,
                "slot_name": "interfaces",
                "component_object_id": bundle_id,
            }

            attached_port = _invoke_json(
                base_url,
                [
                    "object",
                    "component",
                    "attach",
                    bundle_id,
                    "--slot-name",
                    "members",
                    "--component-object-id",
                    port_id,
                ],
            )
            assert attached_port == {
                "parent_object_id": bundle_id,
                "slot_name": "members",
                "component_object_id": port_id,
            }

            components = _invoke_json(base_url, ["object", "component", "list", device_id])
            assert components == [attached_bundle]

            detached_bundle = _invoke_json(
                base_url,
                ["object", "component", "detach", bundle_id],
            )
            assert detached_bundle == attached_bundle
            assert _invoke_json(base_url, ["object", "show", bundle_id])["id"] == bundle_id
            assert _invoke_json(base_url, ["object", "show", port_id])["id"] == port_id
            detached_components = _invoke_json(base_url, ["object", "component", "list", device_id])
            assert detached_components == []
            bundle_components = _invoke_json(base_url, ["object", "component", "list", bundle_id])
            assert bundle_components == [attached_port]

            _invoke_json(
                base_url,
                [
                    "object",
                    "component",
                    "attach",
                    device_id,
                    "--slot-name",
                    "interfaces",
                    "--component-object-id",
                    bundle_id,
                ],
            )

            deleted = runner.invoke(
                app,
                ["--api-url", base_url, "object", "delete", device_id],
            )
            assert deleted.exit_code == 0
            assert f"Deleted object {device_id}" in deleted.stdout

            device_missing = runner.invoke(
                app,
                ["--api-url", base_url, "object", "show", device_id],
            )
            bundle_missing = runner.invoke(
                app,
                ["--api-url", base_url, "object", "show", bundle_id],
            )
            port_missing = runner.invoke(
                app,
                ["--api-url", base_url, "object", "show", port_id],
            )
            assert device_missing.exit_code == 1
            assert "object_not_found" in device_missing.stderr
            assert bundle_missing.exit_code == 1
            assert "object_not_found" in bundle_missing.stderr
            assert port_missing.exit_code == 1
            assert "object_not_found" in port_missing.stderr
    finally:
        engine.dispose()


def test_cli_object_migration_flow(tmp_path: Path) -> None:
    engine, server = _server_url(tmp_path)
    try:
        with server as base_url:
            hostname_created = _invoke_json(
                base_url,
                [
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
            serial_created = _invoke_json(
                base_url,
                [
                    "datatype",
                    "create",
                    "--namespace",
                    "network",
                    "--name",
                    "serialnumber",
                    "--description",
                    "Serialnumber",
                    "--base-type",
                    "core.string",
                ],
            )
            hostname_id = hostname_created["datatype"]["id"]
            serial_id = serial_created["datatype"]["id"]

            assert (
                runner.invoke(
                    app,
                    ["--api-url", base_url, "datatype", "version", "publish", hostname_id, "1"],
                ).exit_code
                == 0
            )
            assert (
                runner.invoke(
                    app,
                    ["--api-url", base_url, "datatype", "version", "publish", serial_id, "1"],
                ).exit_code
                == 0
            )

            template_created = _invoke_json(
                base_url,
                [
                    "object-template",
                    "create",
                    "--namespace",
                    "network",
                    "--name",
                    "device",
                    "--property-json",
                    json.dumps(
                        {
                            "name": "hostname",
                            "datatype_id": hostname_id,
                            "required": True,
                        }
                    ),
                ],
            )
            template_id = template_created["object_template"]["id"]
            assert (
                runner.invoke(
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
                ).exit_code
                == 0
            )

            created_object = _invoke_json(
                base_url,
                [
                    "object",
                    "create",
                    "--template-id",
                    template_id,
                    "--template-version",
                    "1",
                    "--property-json",
                    json.dumps({"hostname": "router-01"}),
                ],
            )
            object_id = created_object["id"]

            created_v2 = _invoke_json(
                base_url,
                [
                    "object-template",
                    "version",
                    "create",
                    template_id,
                    "--source-version",
                    "1",
                ],
            )
            assert created_v2["version"] == 2

            revise_payload = {
                "parent": None,
                "properties": [
                    {
                        "name": "hostname",
                        "datatype_id": hostname_id,
                        "datatype_version": 1,
                        "required": True,
                    },
                    {
                        "name": "serialnumber",
                        "datatype_id": serial_id,
                        "datatype_version": 1,
                        "required": True,
                    },
                ],
                "components": [],
            }
            revise_path = tmp_path / "migrate-revise.json"
            revise_path.write_text(json.dumps(revise_payload), encoding="utf-8")
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
                    "2",
                    "--file",
                    str(revise_path),
                ],
            )
            assert revised.exit_code == 0
            assert (
                runner.invoke(
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
                ).exit_code
                == 0
            )

            analysis = _invoke_json(
                base_url,
                [
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
            assert analysis["automatic"] is True
            assert analysis["added_properties"] == [
                {"name": "serialnumber", "required": True}
            ]

            migrated = _invoke_json(
                base_url,
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
                    json.dumps({"serialnumber": "UNKNOWN"}),
                ],
            )
            assert migrated == {
                "template_id": template_id,
                "source_version": 1,
                "target_version": 2,
                "migrated_count": 1,
            }

            shown = _invoke_json(base_url, ["object", "show", object_id])
            assert shown["template_version"] == 2
            assert shown["properties"] == {
                "hostname": "router-01",
                "serialnumber": "UNKNOWN",
            }
    finally:
        engine.dispose()


def test_cli_object_validation_accepts_and_rejects_temporal_date_properties(
    tmp_path: Path,
) -> None:
    engine, server = _server_url(tmp_path)
    try:
        with server as base_url:
            datatype_created = _invoke_json(
                base_url,
                [
                    "datatype",
                    "create",
                    "--namespace",
                    "inventory",
                    "--name",
                    "installation_date",
                    "--description",
                    "Installation date",
                    "--base-type",
                    "core.date",
                ],
            )
            datatype_id = datatype_created["datatype"]["id"]
            assert datatype_created["version"]["base_type"] == "core.date"

            assert (
                runner.invoke(
                    app,
                    ["--api-url", base_url, "datatype", "version", "publish", datatype_id, "1"],
                ).exit_code
                == 0
            )

            template_created = _invoke_json(
                base_url,
                [
                    "object-template",
                    "create",
                    "--namespace",
                    "inventory",
                    "--name",
                    "asset",
                    "--property-json",
                    json.dumps(
                        {
                            "name": "installation_date",
                            "datatype_id": datatype_id,
                            "required": True,
                        }
                    ),
                ],
            )
            template_id = template_created["object_template"]["id"]

            assert (
                runner.invoke(
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
                ).exit_code
                == 0
            )

            created = _invoke_json(
                base_url,
                [
                    "object",
                    "create",
                    "--template-id",
                    template_id,
                    "--template-version",
                    "1",
                    "--property-json",
                    json.dumps({"installation_date": "2026-08-10"}),
                ],
            )
            assert created["properties"] == {"installation_date": "2026-08-10"}

            invalid = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "object",
                    "create",
                    "--template-id",
                    template_id,
                    "--template-version",
                    "1",
                    "--property-json",
                    json.dumps({"installation_date": "2026-02-31"}),
                ],
            )
            assert invalid.exit_code == 1
            assert "object_validation_failed" in invalid.stderr
            assert "/properties/installation_date" in invalid.stderr
            assert "[format]" in invalid.stderr
    finally:
        engine.dispose()


def test_cli_object_validation_accepts_and_rejects_ip_and_prefix_properties(
    tmp_path: Path,
) -> None:
    engine, server = _server_url(tmp_path)
    try:
        with server as base_url:
            management_ip_created = _invoke_json(
                base_url,
                [
                    "datatype",
                    "create",
                    "--namespace",
                    "network",
                    "--name",
                    "management_ip",
                    "--description",
                    "IPv4 or IPv6 management address",
                    "--base-type",
                    "core.ip",
                ],
            )
            connected_prefix_created = _invoke_json(
                base_url,
                [
                    "datatype",
                    "create",
                    "--namespace",
                    "network",
                    "--name",
                    "connected_prefix",
                    "--description",
                    "IPv4 or IPv6 connected network",
                    "--base-type",
                    "core.ip_prefix",
                ],
            )
            management_ip_id = management_ip_created["datatype"]["id"]
            connected_prefix_id = connected_prefix_created["datatype"]["id"]
            assert management_ip_created["version"]["base_type"] == "core.ip"
            assert connected_prefix_created["version"]["base_type"] == "core.ip_prefix"

            assert (
                runner.invoke(
                    app,
                    [
                        "--api-url",
                        base_url,
                        "datatype",
                        "version",
                        "publish",
                        management_ip_id,
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
                        connected_prefix_id,
                        "1",
                    ],
                ).exit_code
                == 0
            )

            template_created = _invoke_json(
                base_url,
                [
                    "object-template",
                    "create",
                    "--namespace",
                    "network",
                    "--name",
                    "interface",
                    "--property-json",
                    json.dumps(
                        {
                            "name": "management_ip",
                            "datatype_id": management_ip_id,
                            "required": True,
                        }
                    ),
                    "--property-json",
                    json.dumps(
                        {
                            "name": "connected_prefix",
                            "datatype_id": connected_prefix_id,
                            "required": True,
                        }
                    ),
                ],
            )
            template_id = template_created["object_template"]["id"]

            assert (
                runner.invoke(
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
                ).exit_code
                == 0
            )

            created = _invoke_json(
                base_url,
                [
                    "object",
                    "create",
                    "--template-id",
                    template_id,
                    "--template-version",
                    "1",
                    "--property-json",
                    json.dumps({"management_ip": "2001:db8::10"}),
                    "--property-json",
                    json.dumps({"connected_prefix": "2001:db8:100::/48"}),
                ],
            )
            assert created["properties"] == {
                "management_ip": "2001:db8::10",
                "connected_prefix": "2001:db8:100::/48",
            }

            invalid = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "object",
                    "create",
                    "--template-id",
                    template_id,
                    "--template-version",
                    "1",
                    "--property-json",
                    json.dumps({"management_ip": "192.0.2.999"}),
                    "--property-json",
                    json.dumps({"connected_prefix": "192.0.2.10/24"}),
                ],
            )
            assert invalid.exit_code == 1
            assert "object_validation_failed" in invalid.stderr
            assert "/properties/management_ip" in invalid.stderr
            assert "/properties/connected_prefix" in invalid.stderr
            assert invalid.stderr.count("[format]") >= 2
    finally:
        engine.dispose()
