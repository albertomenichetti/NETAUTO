"""Typer entrypoint for NETAUTO."""

from importlib.metadata import version as package_version

import typer

from netauto.cli.common import CliContext
from netauto.cli.datatypes import datatype_app
from netauto.cli.objects import object_app
from netauto.cli.objecttemplates import object_template_app
from netauto.cli.output import OutputMode
from netauto.cli.relationships import relationship_app, relationship_definition_app

DEFAULT_API_URL = "http://127.0.0.1:8000"

app = typer.Typer(help="NETAUTO CLI")
app.add_typer(datatype_app, name="datatype")
app.add_typer(object_app, name="object")
app.add_typer(object_template_app, name="object-template")
app.add_typer(relationship_app, name="relationship")
app.add_typer(relationship_definition_app, name="relationship-definition")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(package_version("netauto"))
        raise typer.Exit()


@app.callback()
def root_callback(
    ctx: typer.Context,
    api_url: str | None = typer.Option(None, "--api-url", envvar="NETAUTO_API_URL"),
    output: OutputMode = typer.Option(OutputMode.HUMAN, "--output"),
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    del version
    ctx.obj = CliContext(api_url=api_url or DEFAULT_API_URL, output=output)


def main() -> None:
    app()
