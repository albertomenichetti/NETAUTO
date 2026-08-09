"""Typer commands for object templates."""

from uuid import UUID

import typer

from netauto.cli.client import JSONObject
from netauto.cli.common import fail, run_action, uuid_text
from netauto.cli.errors import CliError, InputError
from netauto.cli.input import ensure_modes_are_exclusive, load_json_object, parse_json_object
from netauto.cli.output import (
    render_object_template,
    render_object_template_create_result,
    render_object_template_list,
    render_object_template_version,
    render_object_template_version_list,
)

object_template_app = typer.Typer(help="Manage object templates.")
version_app = typer.Typer(help="Manage object template versions.")
object_template_app.add_typer(version_app, name="version")


def _build_parent(
    *,
    parent_template_id: UUID | None,
    parent_version: int | None,
    required: bool,
    allow_none_mode: bool = False,
    no_parent: bool = False,
) -> object:
    if allow_none_mode and no_parent:
        if parent_template_id is not None or parent_version is not None:
            raise InputError("Use either --no-parent or a complete parent reference.")
        return None

    if parent_template_id is None and parent_version is None:
        if required:
            raise InputError("Explicit parent mode is required.")
        return None

    if parent_template_id is None or parent_version is None:
        raise InputError(
            "Parent reference requires both --parent-template-id and --parent-version."
        )

    return {"template_id": uuid_text(parent_template_id), "version": parent_version}


def _build_create_payload(
    *,
    namespace: str | None,
    name: str | None,
    description: str | None,
    abstract: bool,
    parent_template_id: UUID | None,
    parent_version: int | None,
    property_json: list[str],
    component_json: list[str],
    file: str | None,
) -> JSONObject:
    inline_present = (
        namespace is not None
        or name is not None
        or description is not None
        or abstract
        or parent_template_id is not None
        or parent_version is not None
        or bool(property_json)
        or bool(component_json)
    )
    ensure_modes_are_exclusive(file=file, inline_values_present=inline_present)
    if file is not None:
        return load_json_object(file)
    if namespace is None or name is None:
        raise InputError("Inline create mode requires --namespace and --name.")
    return {
        "namespace": namespace,
        "name": name,
        "description": description,
        "abstract": abstract,
        "parent": _build_parent(
            parent_template_id=parent_template_id,
            parent_version=parent_version,
            required=False,
        ),
        "properties": [parse_json_object(value, kind="Property JSON") for value in property_json],
        "components": [parse_json_object(value, kind="Component JSON") for value in component_json],
    }


def _build_revise_payload(
    *,
    no_parent: bool,
    parent_template_id: UUID | None,
    parent_version: int | None,
    property_json: list[str],
    component_json: list[str],
    file: str | None,
) -> JSONObject:
    inline_present = (
        no_parent
        or parent_template_id is not None
        or parent_version is not None
        or bool(property_json)
        or bool(component_json)
    )
    ensure_modes_are_exclusive(file=file, inline_values_present=inline_present)
    if file is not None:
        return load_json_object(file)
    return {
        "parent": _build_parent(
            parent_template_id=parent_template_id,
            parent_version=parent_version,
            required=True,
            allow_none_mode=True,
            no_parent=no_parent,
        ),
        "properties": [parse_json_object(value, kind="Property JSON") for value in property_json],
        "components": [parse_json_object(value, kind="Component JSON") for value in component_json],
    }


@object_template_app.command("list")
def list_object_templates(ctx: typer.Context) -> None:
    run_action(
        ctx,
        lambda client: client.list_object_templates(),
        render_object_template_list,
    )


@object_template_app.command("show")
def show_object_template(ctx: typer.Context, template_id: UUID) -> None:
    run_action(
        ctx,
        lambda client: client.get_object_template(uuid_text(template_id)),
        render_object_template,
    )


@object_template_app.command("show-name")
def show_object_template_name(ctx: typer.Context, namespace: str, name: str) -> None:
    run_action(
        ctx,
        lambda client: client.get_object_template_by_name(namespace, name),
        render_object_template,
    )


@object_template_app.command("create")
def create_object_template(
    ctx: typer.Context,
    namespace: str | None = typer.Option(None, "--namespace"),
    name: str | None = typer.Option(None, "--name"),
    description: str | None = typer.Option(None, "--description"),
    abstract: bool = typer.Option(False, "--abstract"),
    parent_template_id: UUID | None = typer.Option(None, "--parent-template-id"),
    parent_version: int | None = typer.Option(None, "--parent-version", min=1),
    property_json: list[str] | None = typer.Option(None, "--property-json"),
    component_json: list[str] | None = typer.Option(None, "--component-json"),
    file: str | None = typer.Option(None, "--file"),
) -> None:
    try:
        payload = _build_create_payload(
            namespace=namespace,
            name=name,
            description=description,
            abstract=abstract,
            parent_template_id=parent_template_id,
            parent_version=parent_version,
            property_json=property_json or [],
            component_json=component_json or [],
            file=file,
        )
    except CliError as error:
        fail(ctx, error)
    run_action(
        ctx,
        lambda client: client.create_object_template(payload),
        render_object_template_create_result,
    )


@version_app.command("list")
def list_object_template_versions(ctx: typer.Context, template_id: UUID) -> None:
    run_action(
        ctx,
        lambda client: client.list_object_template_versions(uuid_text(template_id)),
        render_object_template_version_list,
    )


@version_app.command("show")
def show_object_template_version(
    ctx: typer.Context,
    template_id: UUID,
    version: int = typer.Argument(..., min=1),
) -> None:
    run_action(
        ctx,
        lambda client: client.get_object_template_version(uuid_text(template_id), version),
        lambda payload, mode: render_object_template_version(payload, mode),
    )


@version_app.command("revise")
def revise_object_template_version(
    ctx: typer.Context,
    template_id: UUID,
    version: int = typer.Argument(..., min=1),
    no_parent: bool = typer.Option(False, "--no-parent"),
    parent_template_id: UUID | None = typer.Option(None, "--parent-template-id"),
    parent_version: int | None = typer.Option(None, "--parent-version", min=1),
    property_json: list[str] | None = typer.Option(None, "--property-json"),
    component_json: list[str] | None = typer.Option(None, "--component-json"),
    file: str | None = typer.Option(None, "--file"),
) -> None:
    try:
        payload = _build_revise_payload(
            no_parent=no_parent,
            parent_template_id=parent_template_id,
            parent_version=parent_version,
            property_json=property_json or [],
            component_json=component_json or [],
            file=file,
        )
    except CliError as error:
        fail(ctx, error)
    run_action(
        ctx,
        lambda client: client.revise_object_template_version(
            uuid_text(template_id),
            version,
            payload,
        ),
        lambda payload, mode: render_object_template_version(
            payload,
            mode,
            prefix="Revised object template version",
        ),
    )


@version_app.command("create")
def create_object_template_version(
    ctx: typer.Context,
    template_id: UUID,
    source_version: int = typer.Option(..., "--source-version", min=1),
) -> None:
    run_action(
        ctx,
        lambda client: client.create_object_template_version(
            uuid_text(template_id),
            source_version,
        ),
        lambda payload, mode: render_object_template_version(
            payload,
            mode,
            prefix="Created object template version",
        ),
    )


@version_app.command("publish")
def publish_object_template_version(
    ctx: typer.Context,
    template_id: UUID,
    version: int = typer.Argument(..., min=1),
) -> None:
    run_action(
        ctx,
        lambda client: client.publish_object_template_version(uuid_text(template_id), version),
        lambda payload, mode: render_object_template_version(
            payload,
            mode,
            prefix="Published object template version",
        ),
    )


@version_app.command("deprecate")
def deprecate_object_template_version(
    ctx: typer.Context,
    template_id: UUID,
    version: int = typer.Argument(..., min=1),
) -> None:
    run_action(
        ctx,
        lambda client: client.deprecate_object_template_version(uuid_text(template_id), version),
        lambda payload, mode: render_object_template_version(
            payload,
            mode,
            prefix="Deprecated object template version",
        ),
    )
