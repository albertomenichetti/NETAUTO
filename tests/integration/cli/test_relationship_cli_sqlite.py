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


def _server_url(tmp_path: Path):
    engine = create_sqlite_engine(f"sqlite:///{tmp_path / 'relationship-runtime-cli.sqlite3'}")
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

            assert created == {
                "id": relationship_id,
                "relationship_definition_id": definition_id,
                "source_object_id": source_object_id,
                "target_object_id": target_object_id,
            }
            assert listed == [created]
            assert shown == created

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
