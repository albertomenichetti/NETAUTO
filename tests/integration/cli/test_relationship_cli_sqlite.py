from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from netauto.api.app import create_app
from netauto.cli.app import app
from netauto.persistence.sqlalchemy.database import create_schema, create_sqlite_engine
from netauto.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from support.http_server import serve_app_url

runner = CliRunner()


def _database_path(tmp_path: Path) -> Path:
    return tmp_path / "relationship-runtime-cli.sqlite3"


def _server_url(tmp_path: Path):
    engine = create_sqlite_engine(f"sqlite:///{_database_path(tmp_path)}")
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)

    def uow_factory() -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(session_factory)

    return engine, serve_app_url(create_app(uow_factory))


def _invoke_json(base_url: str, args: list[str]):
    result = runner.invoke(app, ["--api-url", base_url, "--output", "json", *args])
    assert result.exit_code == 0, result.stderr
    return json.loads(result.stdout)


def _invoke_json_error(base_url: str, args: list[str]):
    result = runner.invoke(app, ["--api-url", base_url, "--output", "json", *args])
    assert result.exit_code != 0
    assert result.stdout == ""
    return json.loads(result.stderr)


def _publish_object_template_version(
    base_url: str,
    template_id: str,
    version: int,
) -> dict[str, object]:
    return _invoke_json(
        base_url,
        ["object-template", "version", "publish", template_id, str(version)],
    )


def _deprecate_object_template_version(
    base_url: str,
    template_id: str,
    version: int,
) -> dict[str, object]:
    return _invoke_json(
        base_url,
        ["object-template", "version", "deprecate", template_id, str(version)],
    )


def test_cli_runtime_relationship_acceptance_flow(tmp_path: Path) -> None:
    engine, server = _server_url(tmp_path)
    try:
        with server as base_url:
            network_device = _invoke_json(
                base_url,
                [
                    "object-template",
                    "create",
                    "--namespace",
                    "network",
                    "--name",
                    "network_device",
                ],
            )
            credential = _invoke_json(
                base_url,
                [
                    "object-template",
                    "create",
                    "--namespace",
                    "network",
                    "--name",
                    "credential",
                ],
            )
            source_template_id = network_device["object_template"]["id"]
            target_template_id = credential["object_template"]["id"]

            assert (
                runner.invoke(
                    app,
                    [
                        "--api-url",
                        base_url,
                        "object-template",
                        "version",
                        "publish",
                        source_template_id,
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
                        "object-template",
                        "version",
                        "publish",
                        target_template_id,
                        "1",
                    ],
                ).exit_code
                == 0
            )

            definition = _invoke_json(
                base_url,
                [
                    "relationship-definition",
                    "create",
                    "--source-template-id",
                    source_template_id,
                    "--target-template-id",
                    target_template_id,
                    "--forward-name",
                    "uses",
                    "--reverse-name",
                    "is_used_by",
                ],
            )
            definition_id = definition["id"]

            source_object = _invoke_json(
                base_url,
                [
                    "object",
                    "create",
                    "--template-id",
                    source_template_id,
                    "--template-version",
                    "1",
                ],
            )
            target_object = _invoke_json(
                base_url,
                [
                    "object",
                    "create",
                    "--template-id",
                    target_template_id,
                    "--template-version",
                    "1",
                ],
            )
            source_object_id = source_object["id"]
            target_object_id = target_object["id"]

            created = _invoke_json(
                base_url,
                [
                    "relationship",
                    "create",
                    "--relationship-definition-id",
                    definition_id,
                    "--source-object-id",
                    source_object_id,
                    "--target-object-id",
                    target_object_id,
                ],
            )
            relationship_id = created["id"]

            listed = _invoke_json(base_url, ["relationship", "list"])
            shown = _invoke_json(base_url, ["relationship", "show", relationship_id])
            effective_source = _invoke_json(
                base_url,
                ["relationship", "effective-definitions", source_object_id],
            )
            effective_target = _invoke_json(
                base_url,
                ["relationship", "effective-definitions", target_object_id],
            )
            outgoing = _invoke_json(base_url, ["relationship", "outgoing", source_object_id])
            incoming = _invoke_json(base_url, ["relationship", "incoming", target_object_id])
            neighbors = _invoke_json(base_url, ["relationship", "neighbors", source_object_id])

            assert created == {
                "id": relationship_id,
                "relationship_definition_id": definition_id,
                "source_object_id": source_object_id,
                "target_object_id": target_object_id,
            }
            assert listed == [created]
            assert shown == created
            assert effective_source == [
                {
                    "relationship_definition_id": definition_id,
                    "direction": "outgoing",
                    "name": "uses",
                    "related_template_id": target_template_id,
                }
            ]
            assert effective_target == [
                {
                    "relationship_definition_id": definition_id,
                    "direction": "incoming",
                    "name": "is_used_by",
                    "related_template_id": source_template_id,
                }
            ]
            assert outgoing == [
                {
                    "relationship_id": relationship_id,
                    "relationship_definition_id": definition_id,
                    "source_object_id": source_object_id,
                    "target_object_id": target_object_id,
                    "direction": "outgoing",
                    "name": "uses",
                    "related_object_id": target_object_id,
                }
            ]
            assert incoming == [
                {
                    "relationship_id": relationship_id,
                    "relationship_definition_id": definition_id,
                    "source_object_id": source_object_id,
                    "target_object_id": target_object_id,
                    "direction": "incoming",
                    "name": "is_used_by",
                    "related_object_id": source_object_id,
                }
            ]
            assert outgoing[0]["relationship_id"] == incoming[0]["relationship_id"]
            assert neighbors == outgoing

            reversed_endpoints = _invoke_json_error(
                base_url,
                [
                    "relationship",
                    "create",
                    "--relationship-definition-id",
                    definition_id,
                    "--source-object-id",
                    target_object_id,
                    "--target-object-id",
                    source_object_id,
                ],
            )
            assert reversed_endpoints["error"]["code"] == "relationship_endpoint_incompatible"

            deleted = runner.invoke(
                app,
                ["--api-url", base_url, "relationship", "delete", relationship_id],
            )
            assert deleted.exit_code == 0, deleted.stderr
            assert f"Deleted relationship {relationship_id}" in deleted.stdout

            missing_show = _invoke_json_error(base_url, ["relationship", "show", relationship_id])
            assert missing_show["error"]["code"] == "relationship_not_found"
    finally:
        engine.dispose()


def test_cli_runtime_relationship_self_link_neighbors_show_two_views(tmp_path: Path) -> None:
    engine, server = _server_url(tmp_path)
    try:
        with server as base_url:
            device = _invoke_json(
                base_url,
                [
                    "object-template",
                    "create",
                    "--namespace",
                    "network",
                    "--name",
                    "device",
                ],
            )
            template_id = device["object_template"]["id"]

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

            definition = _invoke_json(
                base_url,
                [
                    "relationship-definition",
                    "create",
                    "--source-template-id",
                    template_id,
                    "--target-template-id",
                    template_id,
                    "--forward-name",
                    "connects_to",
                    "--reverse-name",
                    "connected_from",
                ],
            )
            definition_id = definition["id"]

            object_value = _invoke_json(
                base_url,
                [
                    "object",
                    "create",
                    "--template-id",
                    template_id,
                    "--template-version",
                    "1",
                ],
            )
            object_id = object_value["id"]

            created = _invoke_json(
                base_url,
                [
                    "relationship",
                    "create",
                    "--relationship-definition-id",
                    definition_id,
                    "--source-object-id",
                    object_id,
                    "--target-object-id",
                    object_id,
                ],
            )
            neighbors = _invoke_json(base_url, ["relationship", "neighbors", object_id])
            listed = _invoke_json(base_url, ["relationship", "list"])

            assert listed == [created]
            assert neighbors == [
                {
                    "relationship_id": created["id"],
                    "relationship_definition_id": definition_id,
                    "source_object_id": object_id,
                    "target_object_id": object_id,
                    "direction": "outgoing",
                    "name": "connects_to",
                    "related_object_id": object_id,
                },
                {
                    "relationship_id": created["id"],
                    "relationship_definition_id": definition_id,
                    "source_object_id": object_id,
                    "target_object_id": object_id,
                    "direction": "incoming",
                    "name": "connected_from",
                    "related_object_id": object_id,
                },
            ]
    finally:
        engine.dispose()


def test_cli_relationship_integration_closure_flow(tmp_path: Path) -> None:
    database_path = _database_path(tmp_path)
    engine, server = _server_url(tmp_path)
    try:
        with server as base_url:
            network_device = _invoke_json(
                base_url,
                [
                    "object-template",
                    "create",
                    "--namespace",
                    "network",
                    "--name",
                    "network_device",
                ],
            )
            network_device_id = network_device["object_template"]["id"]
            assert _publish_object_template_version(base_url, network_device_id, 1)["status"] == (
                "published"
            )

            credential = _invoke_json(
                base_url,
                [
                    "object-template",
                    "create",
                    "--namespace",
                    "network",
                    "--name",
                    "credential",
                ],
            )
            credential_id = credential["object_template"]["id"]
            assert _publish_object_template_version(base_url, credential_id, 1)["status"] == (
                "published"
            )

            module = _invoke_json(
                base_url,
                [
                    "object-template",
                    "create",
                    "--namespace",
                    "network",
                    "--name",
                    "module",
                    "--parent-template-id",
                    network_device_id,
                    "--parent-version",
                    "1",
                ],
            )
            module_id = module["object_template"]["id"]
            assert _publish_object_template_version(base_url, module_id, 1)["status"] == (
                "published"
            )

            router = _invoke_json(
                base_url,
                [
                    "object-template",
                    "create",
                    "--namespace",
                    "network",
                    "--name",
                    "router",
                ],
            )
            router_id = router["object_template"]["id"]
            assert _publish_object_template_version(base_url, router_id, 1)["status"] == (
                "published"
            )

            router_v2_created = _invoke_json(
                base_url,
                [
                    "object-template",
                    "version",
                    "create",
                    router_id,
                    "--source-version",
                    "1",
                ],
            )
            assert router_v2_created["version"] == 2
            router_v2_revised = _invoke_json(
                base_url,
                [
                    "object-template",
                    "version",
                    "revise",
                    router_id,
                    "2",
                    "--parent-template-id",
                    network_device_id,
                    "--parent-version",
                    "1",
                    "--component-json",
                    json.dumps({"name": "modules", "template_id": module_id}),
                ],
            )
            assert router_v2_revised["parent"] == {
                "template_id": network_device_id,
                "version": 1,
            }
            assert router_v2_revised["components"] == [
                {"name": "modules", "template_id": module_id}
            ]
            assert _publish_object_template_version(base_url, router_id, 2)["status"] == (
                "published"
            )

            definition = _invoke_json(
                base_url,
                [
                    "relationship-definition",
                    "create",
                    "--source-template-id",
                    network_device_id,
                    "--target-template-id",
                    credential_id,
                    "--forward-name",
                    "uses",
                    "--reverse-name",
                    "is_used_by",
                ],
            )
            definition_id = definition["id"]

            router_v1_object = _invoke_json(
                base_url,
                [
                    "object",
                    "create",
                    "--template-id",
                    router_id,
                    "--template-version",
                    "1",
                ],
            )
            router_v1_object_id = router_v1_object["id"]
            router_v2_object = _invoke_json(
                base_url,
                [
                    "object",
                    "create",
                    "--template-id",
                    router_id,
                    "--template-version",
                    "2",
                ],
            )
            router_v2_object_id = router_v2_object["id"]
            module_object = _invoke_json(
                base_url,
                [
                    "object",
                    "create",
                    "--template-id",
                    module_id,
                    "--template-version",
                    "1",
                ],
            )
            module_object_id = module_object["id"]
            credential_object = _invoke_json(
                base_url,
                [
                    "object",
                    "create",
                    "--template-id",
                    credential_id,
                    "--template-version",
                    "1",
                ],
            )
            credential_object_id = credential_object["id"]
            unrelated_device = _invoke_json(
                base_url,
                [
                    "object",
                    "create",
                    "--template-id",
                    network_device_id,
                    "--template-version",
                    "1",
                ],
            )
            unrelated_device_id = unrelated_device["id"]
            unrelated_credential = _invoke_json(
                base_url,
                [
                    "object",
                    "create",
                    "--template-id",
                    credential_id,
                    "--template-version",
                    "1",
                ],
            )
            unrelated_credential_id = unrelated_credential["id"]

            attached = _invoke_json(
                base_url,
                [
                    "object",
                    "component",
                    "attach",
                    router_v2_object_id,
                    "--slot-name",
                    "modules",
                    "--component-object-id",
                    module_object_id,
                ],
            )
            assert attached == {
                "parent_object_id": router_v2_object_id,
                "slot_name": "modules",
                "component_object_id": module_object_id,
            }

            router_v1_effective = _invoke_json(
                base_url,
                ["relationship", "effective-definitions", router_v1_object_id],
            )
            router_v2_effective = _invoke_json(
                base_url,
                ["relationship", "effective-definitions", router_v2_object_id],
            )
            credential_effective = _invoke_json(
                base_url,
                ["relationship", "effective-definitions", credential_object_id],
            )

            assert router_v1_effective == []
            assert router_v2_effective == [
                {
                    "relationship_definition_id": definition_id,
                    "direction": "outgoing",
                    "name": "uses",
                    "related_template_id": credential_id,
                }
            ]
            assert credential_effective == [
                {
                    "relationship_definition_id": definition_id,
                    "direction": "incoming",
                    "name": "is_used_by",
                    "related_template_id": network_device_id,
                }
            ]

            r1 = _invoke_json(
                base_url,
                [
                    "relationship",
                    "create",
                    "--relationship-definition-id",
                    definition_id,
                    "--source-object-id",
                    router_v2_object_id,
                    "--target-object-id",
                    credential_object_id,
                ],
            )
            r2 = _invoke_json(
                base_url,
                [
                    "relationship",
                    "create",
                    "--relationship-definition-id",
                    definition_id,
                    "--source-object-id",
                    module_object_id,
                    "--target-object-id",
                    credential_object_id,
                ],
            )
            r3 = _invoke_json(
                base_url,
                [
                    "relationship",
                    "create",
                    "--relationship-definition-id",
                    definition_id,
                    "--source-object-id",
                    unrelated_device_id,
                    "--target-object-id",
                    unrelated_credential_id,
                ],
            )
            r1_id = r1["id"]
            r2_id = r2["id"]
            r3_id = r3["id"]

            router_v2_outgoing = _invoke_json(
                base_url,
                ["relationship", "outgoing", router_v2_object_id],
            )
            credential_incoming = _invoke_json(
                base_url,
                ["relationship", "incoming", credential_object_id],
            )
            router_v2_neighbors = _invoke_json(
                base_url,
                ["relationship", "neighbors", router_v2_object_id],
            )
            credential_neighbors = _invoke_json(
                base_url,
                ["relationship", "neighbors", credential_object_id],
            )

            assert router_v2_outgoing == [
                {
                    "relationship_id": r1_id,
                    "relationship_definition_id": definition_id,
                    "source_object_id": router_v2_object_id,
                    "target_object_id": credential_object_id,
                    "direction": "outgoing",
                    "name": "uses",
                    "related_object_id": credential_object_id,
                }
            ]
            credential_incoming_by_id = {
                item["relationship_id"]: item for item in credential_incoming
            }
            assert set(credential_incoming_by_id) == {r1_id, r2_id}
            assert credential_incoming_by_id[r1_id] == {
                "relationship_id": r1_id,
                "relationship_definition_id": definition_id,
                "source_object_id": router_v2_object_id,
                "target_object_id": credential_object_id,
                "direction": "incoming",
                "name": "is_used_by",
                "related_object_id": router_v2_object_id,
            }
            assert credential_incoming_by_id[r2_id] == {
                "relationship_id": r2_id,
                "relationship_definition_id": definition_id,
                "source_object_id": module_object_id,
                "target_object_id": credential_object_id,
                "direction": "incoming",
                "name": "is_used_by",
                "related_object_id": module_object_id,
            }
            assert router_v2_outgoing[0]["relationship_id"] == credential_incoming_by_id[r1_id][
                "relationship_id"
            ]
            assert router_v2_neighbors == router_v2_outgoing
            assert {item["relationship_id"] for item in credential_neighbors} == {r1_id, r2_id}

            deprecated_router_v2 = _deprecate_object_template_version(base_url, router_id, 2)
            assert deprecated_router_v2["status"] == "deprecated"
            router_v2_effective_after_deprecation = _invoke_json(
                base_url,
                ["relationship", "effective-definitions", router_v2_object_id],
            )
            router_v2_outgoing_after_deprecation = _invoke_json(
                base_url,
                ["relationship", "outgoing", router_v2_object_id],
            )
            assert router_v2_effective_after_deprecation == router_v2_effective
            assert router_v2_outgoing_after_deprecation == router_v2_outgoing

            definition_delete_blocked = _invoke_json_error(
                base_url,
                ["relationship-definition", "delete", definition_id],
            )
            assert definition_delete_blocked["error"]["code"] == "relationship_definition_in_use"
            assert _invoke_json(
                base_url,
                ["relationship-definition", "show", definition_id],
            )["id"] == definition_id
            assert _invoke_json(base_url, ["relationship", "show", r1_id])["id"] == r1_id
            assert _invoke_json(base_url, ["relationship", "show", r2_id])["id"] == r2_id
            assert _invoke_json(base_url, ["relationship", "show", r3_id])["id"] == r3_id

            assert _invoke_json(base_url, ["object", "delete", router_v2_object_id]) is None

            router_v2_missing = _invoke_json_error(
                base_url,
                ["object", "show", router_v2_object_id],
            )
            module_missing = _invoke_json_error(
                base_url,
                ["object", "show", module_object_id],
            )
            r1_missing = _invoke_json_error(base_url, ["relationship", "show", r1_id])
            r2_missing = _invoke_json_error(base_url, ["relationship", "show", r2_id])
            assert router_v2_missing["error"]["code"] == "object_not_found"
            assert module_missing["error"]["code"] == "object_not_found"
            assert r1_missing["error"]["code"] == "relationship_not_found"
            assert r2_missing["error"]["code"] == "relationship_not_found"

            assert _invoke_json(base_url, ["object", "show", credential_object_id])["id"] == (
                credential_object_id
            )
            assert _invoke_json(base_url, ["object", "show", unrelated_device_id])["id"] == (
                unrelated_device_id
            )
            assert _invoke_json(
                base_url,
                ["object", "show", unrelated_credential_id],
            )["id"] == unrelated_credential_id
            assert _invoke_json(base_url, ["relationship", "show", r3_id])["id"] == r3_id
            unrelated_outgoing = _invoke_json(
                base_url,
                ["relationship", "outgoing", unrelated_device_id],
            )
            assert unrelated_outgoing == [
                {
                    "relationship_id": r3_id,
                    "relationship_definition_id": definition_id,
                    "source_object_id": unrelated_device_id,
                    "target_object_id": unrelated_credential_id,
                    "direction": "outgoing",
                    "name": "uses",
                    "related_object_id": unrelated_credential_id,
                }
            ]
            assert _invoke_json(
                base_url,
                ["relationship-definition", "show", definition_id],
            )["id"] == definition_id

            definition_delete_still_blocked = _invoke_json_error(
                base_url,
                ["relationship-definition", "delete", definition_id],
            )
            assert definition_delete_still_blocked["error"]["code"] == (
                "relationship_definition_in_use"
            )

            assert _invoke_json(base_url, ["relationship", "delete", r3_id]) is None
            assert (
                _invoke_json(
                    base_url,
                    ["relationship-definition", "delete", definition_id],
                )
                is None
            )

            r3_missing = _invoke_json_error(base_url, ["relationship", "show", r3_id])
            definition_missing = _invoke_json_error(
                base_url,
                ["relationship-definition", "show", definition_id],
            )
            assert r3_missing["error"]["code"] == "relationship_not_found"
            assert definition_missing["error"]["code"] == "relationship_definition_not_found"
            assert _invoke_json(base_url, ["object", "show", unrelated_device_id])["id"] == (
                unrelated_device_id
            )
            assert _invoke_json(
                base_url,
                ["object", "show", unrelated_credential_id],
            )["id"] == unrelated_credential_id
            assert _invoke_json(base_url, ["object", "show", router_v1_object_id])["id"] == (
                router_v1_object_id
            )
            assert _invoke_json(
                base_url,
                ["relationship", "effective-definitions", router_v1_object_id],
            ) == []

            assert database_path.exists()
    finally:
        engine.dispose()
