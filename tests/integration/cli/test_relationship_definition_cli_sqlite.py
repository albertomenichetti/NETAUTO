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
    engine = create_sqlite_engine(f"sqlite:///{tmp_path / 'relationship-cli.sqlite3'}")
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


def test_cli_relationship_definition_acceptance_flow(tmp_path: Path) -> None:
    engine, server = _server_url(tmp_path)
    try:
        with server as base_url:
            source = _invoke_json(
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
            target = _invoke_json(
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

            source_id = source["object_template"]["id"]
            target_id = target["object_template"]["id"]

            assert (
                runner.invoke(
                    app,
                    [
                        "--api-url",
                        base_url,
                        "object-template",
                        "version",
                        "publish",
                        source_id,
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
                        target_id,
                        "1",
                    ],
                ).exit_code
                == 0
            )

            created = _invoke_json(
                base_url,
                [
                    "relationship-definition",
                    "create",
                    "--source-template-id",
                    source_id,
                    "--target-template-id",
                    target_id,
                    "--forward-name",
                    "uses",
                    "--reverse-name",
                    "is_used_by",
                ],
            )
            definition_id = created["id"]

            listed = _invoke_json(base_url, ["relationship-definition", "list"])
            shown = _invoke_json(base_url, ["relationship-definition", "show", definition_id])

            assert len(listed) == 1
            assert listed[0] == created
            assert shown == created

            inverse_duplicate = _invoke_json_error(
                base_url,
                [
                    "relationship-definition",
                    "create",
                    "--source-template-id",
                    target_id,
                    "--target-template-id",
                    source_id,
                    "--forward-name",
                    "is_used_by",
                    "--reverse-name",
                    "uses",
                ],
            )
            assert inverse_duplicate["error"]["code"] == (
                "relationship_definition_semantic_conflict"
            )

            deleted = runner.invoke(
                app,
                ["--api-url", base_url, "relationship-definition", "delete", definition_id],
            )
            assert deleted.exit_code == 0, deleted.stderr
            assert f"Deleted relationship definition {definition_id}" in deleted.stdout

            missing_show = _invoke_json_error(
                base_url,
                ["relationship-definition", "show", definition_id],
            )
            assert missing_show["error"]["code"] == "relationship_definition_not_found"

            missing_delete = _invoke_json_error(
                base_url,
                ["relationship-definition", "delete", definition_id],
            )
            assert missing_delete["error"]["code"] == "relationship_definition_not_found"
    finally:
        engine.dispose()
