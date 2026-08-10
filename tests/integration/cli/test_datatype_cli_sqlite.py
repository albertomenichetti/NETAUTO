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


def test_cli_datatype_revise_without_base_type_and_delete_lifecycle(tmp_path: Path) -> None:
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
                    "common",
                    "--name",
                    "email",
                    "--description",
                    "Email address",
                    "--base-type",
                    "core.string",
                ],
            )
            assert created.exit_code == 0
            created_payload = json.loads(created.stdout)
            datatype_id = created_payload["datatype"]["id"]

            published_v1 = runner.invoke(
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
            assert published_v1.exit_code == 0

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
            assert json.loads(created_v2.stdout)["base_type"] == "core.string"

            revised_v2 = runner.invoke(
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
                    "2",
                    "--constraint",
                    'pattern="^[^@]+@[^@]+[.][^@]+$"',
                ],
            )
            assert revised_v2.exit_code == 0
            revised_payload = json.loads(revised_v2.stdout)
            assert revised_payload["base_type"] == "core.string"
            assert revised_payload["constraints"] == [
                {"name": "pattern", "value": "^[^@]+@[^@]+[.][^@]+$"}
            ]

            published_v2 = runner.invoke(
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
            )
            assert published_v2.exit_code == 0

            template_created = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "object-template",
                    "create",
                    "--namespace",
                    "common",
                    "--name",
                    "contact",
                    "--property-json",
                    json.dumps(
                        {
                            "name": "email",
                            "datatype_id": datatype_id,
                            "datatype_version": 2,
                            "required": True,
                        }
                    ),
                ],
            )
            assert template_created.exit_code == 0

            blocked_delete = runner.invoke(
                app,
                ["--api-url", base_url, "datatype", "delete", datatype_id],
            )
            assert blocked_delete.exit_code == 1
            assert "datatype_in_use" in blocked_delete.stderr
            datatype_show = runner.invoke(
                app,
                [
                    "--api-url",
                    base_url,
                    "--output",
                    "json",
                    "datatype",
                    "show",
                    datatype_id,
                ],
            )
            assert datatype_show.exit_code == 0
            assert json.loads(datatype_show.stdout)["id"] == datatype_id

            listed_versions = runner.invoke(
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
            assert listed_versions.exit_code == 0
            assert [
                (item["version"], item["status"])
                for item in json.loads(listed_versions.stdout)
            ] == [(1, "published"), (2, "published")]

            temp_created = runner.invoke(
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
                    "nickname",
                    "--description",
                    "Nickname",
                    "--base-type",
                    "core.string",
                ],
            )
            assert temp_created.exit_code == 0
            temp_id = json.loads(temp_created.stdout)["datatype"]["id"]

            deleted = runner.invoke(
                app,
                ["--api-url", base_url, "datatype", "delete", temp_id],
            )
            assert deleted.exit_code == 0
            assert f"Deleted datatype {temp_id}" in deleted.stdout

            missing = runner.invoke(
                app,
                ["--api-url", base_url, "datatype", "show", temp_id],
            )
            assert missing.exit_code == 1
            assert "datatype_not_found" in missing.stderr
    finally:
        engine.dispose()


def test_cli_create_next_accepts_deprecated_source(tmp_path: Path) -> None:
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
                    "common",
                    "--name",
                    "email",
                    "--description",
                    "Email address",
                    "--base-type",
                    "core.string",
                    "--constraint",
                    'pattern="^[^@]+@[^@]+[.][^@]+$"',
                ],
            )
            assert created.exit_code == 0
            created_payload = json.loads(created.stdout)
            datatype_id = created_payload["datatype"]["id"]

            published_v1 = runner.invoke(
                app,
                ["--api-url", base_url, "datatype", "version", "publish", datatype_id, "1"],
            )
            assert published_v1.exit_code == 0

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
            created_v2_payload = json.loads(created_v2.stdout)

            published_v2 = runner.invoke(
                app,
                ["--api-url", base_url, "datatype", "version", "publish", datatype_id, "2"],
            )
            assert published_v2.exit_code == 0

            deprecated_v1 = runner.invoke(
                app,
                ["--api-url", base_url, "datatype", "version", "deprecate", datatype_id, "1"],
            )
            assert deprecated_v1.exit_code == 0
            deprecated_v2 = runner.invoke(
                app,
                ["--api-url", base_url, "datatype", "version", "deprecate", datatype_id, "2"],
            )
            assert deprecated_v2.exit_code == 0

            created_v3 = runner.invoke(
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
                    "2",
                ],
            )
            assert created_v3.exit_code == 0
            created_v3_payload = json.loads(created_v3.stdout)

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

            assert created_v3_payload["version"] == 3
            assert created_v3_payload["status"] == "draft"
            assert created_v3_payload["base_type"] == created_v2_payload["base_type"]
            assert created_v3_payload["constraints"] == created_v2_payload["constraints"]
            assert [(v["version"], v["status"]) for v in json.loads(versions.stdout)] == [
                (1, "deprecated"),
                (2, "deprecated"),
                (3, "draft"),
            ]
    finally:
        engine.dispose()
