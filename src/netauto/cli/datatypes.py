"""Typer commands for datatypes."""

from uuid import UUID

import typer

from netauto.cli.client import JSONObject
from netauto.cli.common import fail, run_action, uuid_text
from netauto.cli.errors import CliError, InputError
from netauto.cli.input import ensure_modes_are_exclusive, load_json_object, parse_constraints
from netauto.cli.output import (
    render_create_result,
    render_datatype,
    render_datatype_delete_result,
    render_datatype_list,
    render_version,
    render_version_list,
)

datatype_app = typer.Typer(help="Manage datatypes.")
version_app = typer.Typer(help="Manage datatype versions.")
datatype_app.add_typer(version_app, name="version")


def _build_create_payload(
    *,
    namespace: str | None,
    name: str | None,
    description: str | None,
    base_type: str | None,
    constraints: list[str],
    file: str | None,
) -> JSONObject:
    inline_present = any(
        value is not None for value in (namespace, name, description, base_type)
    ) or bool(constraints)
    ensure_modes_are_exclusive(file=file, inline_values_present=inline_present)
    if file is not None:
        return load_json_object(file)
    if namespace is None or name is None or base_type is None:
        raise InputError("Inline create mode requires --namespace, --name, and --base-type.")
    return {
        "namespace": namespace,
        "name": name,
        "description": description,
        "base_type": base_type,
        "constraints": parse_constraints(constraints),
    }


def _build_revise_payload(
    *,
    constraints: list[str],
    file: str | None,
) -> JSONObject:
    inline_present = bool(constraints)
    ensure_modes_are_exclusive(file=file, inline_values_present=inline_present)
    if file is not None:
        return load_json_object(file)
    return {
        "constraints": parse_constraints(constraints),
    }


@datatype_app.command("list")
def list_datatypes(ctx: typer.Context) -> None:
    run_action(ctx, lambda client: client.list_datatypes(), render_datatype_list)


@datatype_app.command("show")
def show_datatype(ctx: typer.Context, datatype_id: UUID) -> None:
    run_action(ctx, lambda client: client.get_datatype(uuid_text(datatype_id)), render_datatype)


@datatype_app.command("show-name")
def show_datatype_name(ctx: typer.Context, namespace: str, name: str) -> None:
    run_action(ctx, lambda client: client.get_datatype_by_name(namespace, name), render_datatype)


@datatype_app.command("delete")
def delete_datatype(ctx: typer.Context, datatype_id: UUID) -> None:
    run_action(
        ctx,
        lambda client: client.delete_datatype(uuid_text(datatype_id)),
        lambda _payload, mode: render_datatype_delete_result(uuid_text(datatype_id), mode),
    )


@datatype_app.command("create")
def create_datatype(
    ctx: typer.Context,
    namespace: str | None = typer.Option(None, "--namespace"),
    name: str | None = typer.Option(None, "--name"),
    description: str | None = typer.Option(None, "--description"),
    base_type: str | None = typer.Option(None, "--base-type"),
    constraint: list[str] | None = typer.Option(None, "--constraint"),
    file: str | None = typer.Option(None, "--file"),
) -> None:
    try:
        payload = _build_create_payload(
            namespace=namespace,
            name=name,
            description=description,
            base_type=base_type,
            constraints=constraint or [],
            file=file,
        )
    except CliError as error:
        fail(ctx, error)
    run_action(ctx, lambda client: client.create_datatype(payload), render_create_result)


@version_app.command("list")
def list_versions(ctx: typer.Context, datatype_id: UUID) -> None:
    run_action(
        ctx,
        lambda client: client.list_versions(uuid_text(datatype_id)),
        render_version_list,
    )


@version_app.command("show")
def show_version(
    ctx: typer.Context,
    datatype_id: UUID,
    version: int = typer.Argument(..., min=1),
) -> None:
    run_action(
        ctx,
        lambda client: client.get_version(uuid_text(datatype_id), version),
        lambda payload, mode: render_version(payload, mode),
    )


@version_app.command("revise")
def revise_version(
    ctx: typer.Context,
    datatype_id: UUID,
    version: int = typer.Argument(..., min=1),
    constraint: list[str] | None = typer.Option(None, "--constraint"),
    file: str | None = typer.Option(None, "--file"),
) -> None:
    try:
        payload = _build_revise_payload(
            constraints=constraint or [],
            file=file,
        )
    except CliError as error:
        fail(ctx, error)
    run_action(
        ctx,
        lambda client: client.revise_version(uuid_text(datatype_id), version, payload),
        lambda payload, mode: render_version(payload, mode, prefix="Revised datatype version"),
    )


@version_app.command("create")
def create_version(
    ctx: typer.Context,
    datatype_id: UUID,
    source_version: int = typer.Option(..., "--source-version", min=1),
) -> None:
    run_action(
        ctx,
        lambda client: client.create_version(uuid_text(datatype_id), source_version),
        lambda payload, mode: render_version(payload, mode, prefix="Created datatype version"),
    )


@version_app.command("publish")
def publish_version(
    ctx: typer.Context,
    datatype_id: UUID,
    version: int = typer.Argument(..., min=1),
) -> None:
    run_action(
        ctx,
        lambda client: client.publish_version(uuid_text(datatype_id), version),
        lambda payload, mode: render_version(payload, mode, prefix="Published datatype version"),
    )


@version_app.command("deprecate")
def deprecate_version(
    ctx: typer.Context,
    datatype_id: UUID,
    version: int = typer.Argument(..., min=1),
) -> None:
    run_action(
        ctx,
        lambda client: client.deprecate_version(uuid_text(datatype_id), version),
        lambda payload, mode: render_version(payload, mode, prefix="Deprecated datatype version"),
    )
