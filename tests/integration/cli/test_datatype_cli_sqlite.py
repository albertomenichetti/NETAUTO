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
    engine = create_sqlite_engine(f"sqlite:///{tmp_path / 'cli.sqlite3'}")
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)

    def uow_factory() -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(session_factory)

    return engine, serve_app_url(create_app(uow_factory))


def test_cli_acceptance_flow_and_large_integer_round_trip(tmp_path: Path) -> None:
    engine, server = _server_url(tmp_path)
    huge = 10**1000
    try:
        with server as base_url:
            created = runner.invoke(
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
            assert created.exit_code == 0
            created_payload = json.loads(created.stdout)
            datatype_id = created_payload["datatype"]["id"]
            assert created_payload["version"]["version"] == 1
            assert created_payload["version"]["status"] == "draft"

            assert runner.invoke(
                app,
                ["--api-url", base_url, "--output", "json", "datatype", "show", datatype_id],
            ).exit_code == 0

            shown_name = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "datatype",
                    "show-name",
                    "network",
                    "vlan_id",
                ],
            )
            assert shown_name.exit_code == 0
            assert json.loads(shown_name.stdout)["id"] == datatype_id

            versions = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "datatype",
                    "version",
                    "list",
                    datatype_id,
                ],
            )
            assert versions.exit_code == 0
            assert json.loads(versions.stdout)[0]["status"] == "draft"

            revised = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "datatype",
                    "version",
                    "revise",
                    datatype_id,
                    "1",
                    "--base-type",
                    "core.integer",
                    "--constraint",
                    "minimum=1",
                    "--constraint",
                    "maximum=4094",
                ],
            )
            assert revised.exit_code == 0
            assert json.loads(revised.stdout)["status"] == "draft"

            published_v1 = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "datatype",
                    "version",
                    "publish",
                    datatype_id,
                    "1",
                ],
            )
            assert published_v1.exit_code == 0
            assert json.loads(published_v1.stdout)["status"] == "published"

            created_v2 = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "datatype",
                    "version",
                    "create",
                    datatype_id,
                    "--source-version",
                    "1",
                ],
            )
            assert created_v2.exit_code == 0
            assert json.loads(created_v2.stdout)["version"] == 2

            published_v2 = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "datatype",
                    "version",
                    "publish",
                    datatype_id,
                    "2",
                ],
            )
            assert published_v2.exit_code == 0
            assert json.loads(published_v2.stdout)["status"] == "published"

            versions = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "datatype",
                    "version",
                    "list",
                    datatype_id,
                ],
            )
            assert versions.exit_code == 0
            assert [(v["version"], v["status"]) for v in json.loads(versions.stdout)] == [
                (1, "published"),
                (2, "published"),
            ]

            deprecated_v1 = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "datatype",
                    "version",
                    "deprecate",
                    datatype_id,
                    "1",
                ],
            )
            assert deprecated_v1.exit_code == 0
            assert json.loads(deprecated_v1.stdout)["status"] == "deprecated"

            versions = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "datatype",
                    "version",
                    "list",
                    datatype_id,
                ],
            )
            assert versions.exit_code == 0
            assert [(v["version"], v["status"]) for v in json.loads(versions.stdout)] == [
                (1, "deprecated"),
                (2, "published"),
            ]

            huge_created = runner.invoke(
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
                    "huge_minimum",
                    "--description",
                    "Huge minimum",
                    "--base-type",
                    "core.number",
                    "--constraint",
                    f"minimum={huge}",
                ],
            )
            assert huge_created.exit_code == 0
            huge_payload = json.loads(huge_created.stdout)
            huge_id = huge_payload["datatype"]["id"]
            assert huge_payload["version"]["constraints"][0]["value"] == huge
            assert type(huge_payload["version"]["constraints"][0]["value"]) is int

            huge_show = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "datatype",
                    "version",
                    "show",
                    huge_id,
                    "1",
                ],
            )
            assert huge_show.exit_code == 0
            huge_show_payload = json.loads(huge_show.stdout)
            assert huge_show_payload["constraints"][0]["value"] == huge
            assert type(huge_show_payload["constraints"][0]["value"]) is int
    finally:
        engine.dispose()


def test_cli_end_to_end_api_error(tmp_path: Path) -> None:
    engine, server = _server_url(tmp_path)
    try:
        with server as base_url:
            created = runner.invoke(
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
            datatype_id = json.loads(created.stdout)["datatype"]["id"]

            published = runner.invoke(
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
            )
            assert published.exit_code == 0

            published_again = runner.invoke(
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
            )

            assert published_again.exit_code == 1
            assert published_again.stdout == ""
            assert "invalid_datatype_version_transition" in published_again.stderr
    finally:
        engine.dispose()
