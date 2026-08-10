"""Typer commands for objects."""

from uuid import UUID

import typer

from netauto.cli.client import JSONObject
from netauto.cli.common import fail, run_action, uuid_text
from netauto.cli.errors import CliError, InputError
from netauto.cli.input import ensure_modes_are_exclusive, load_json_object, parse_json_object
from netauto.cli.output import (
    render_component_membership,
    render_component_membership_list,
    render_object,
    render_object_delete_result,
    render_object_list,
)

object_app = typer.Typer(help="Manage objects.")
component_app = typer.Typer(help="Manage object components.")
object_app.add_typer(component_app, name="component")


def _merge_property_json(values: list[str]) -> JSONObject:
    merged: JSONObject = {}
    for value in values:
        merged.update(parse_json_object(value, kind="Property JSON"))
    return merged


def _build_create_payload(
    *,
    template_id: UUID | None,
    template_version: int | None,
    property_json: list[str],
    file: str | None,
) -> JSONObject:
    inline_present = template_id is not None or template_version is not None or bool(property_json)
    ensure_modes_are_exclusive(file=file, inline_values_present=inline_present)
    if file is not None:
        return load_json_object(file)
    if template_id is None or template_version is None:
        raise InputError("Inline create mode requires --template-id and --template-version.")
    return {
        "template_id": uuid_text(template_id),
        "template_version": template_version,
        "properties": _merge_property_json(property_json),
    }


def _build_update_payload(
    *,
    property_json: list[str],
    remove_property: list[str],
    file: str | None,
) -> JSONObject:
    inline_present = bool(property_json) or bool(remove_property)
    ensure_modes_are_exclusive(file=file, inline_values_present=inline_present)
    if file is not None:
        return load_json_object(file)
    return {
        "properties": _merge_property_json(property_json) if property_json else None,
        "remove_properties": list(remove_property),
    }


def _build_attach_payload(
    *,
    slot_name: str | None,
    component_object_id: UUID | None,
    file: str | None,
) -> JSONObject:
    inline_present = slot_name is not None or component_object_id is not None
    ensure_modes_are_exclusive(file=file, inline_values_present=inline_present)
    if file is not None:
        return load_json_object(file)
    if slot_name is None or component_object_id is None:
        raise InputError("Inline attach mode requires --slot-name and --component-object-id.")
    return {
        "slot_name": slot_name,
        "component_object_id": uuid_text(component_object_id),
    }


@object_app.command("list")
def list_objects(ctx: typer.Context) -> None:
    run_action(ctx, lambda client: client.list_objects(), render_object_list)


@object_app.command("show")
def show_object(ctx: typer.Context, object_id: UUID) -> None:
    run_action(ctx, lambda client: client.get_object(uuid_text(object_id)), render_object)


@object_app.command("create")
def create_object(
    ctx: typer.Context,
    template_id: UUID | None = typer.Option(None, "--template-id"),
    template_version: int | None = typer.Option(None, "--template-version", min=1),
    property_json: list[str] | None = typer.Option(None, "--property-json"),
    file: str | None = typer.Option(None, "--file"),
) -> None:
    try:
        payload = _build_create_payload(
            template_id=template_id,
            template_version=template_version,
            property_json=property_json or [],
            file=file,
        )
    except CliError as error:
        fail(ctx, error)
    run_action(
        ctx,
        lambda client: client.create_object(payload),
        lambda payload, mode: render_object(payload, mode, prefix="Created object"),
    )


@object_app.command("update")
def update_object(
    ctx: typer.Context,
    object_id: UUID,
    property_json: list[str] | None = typer.Option(None, "--property-json"),
    remove_property: list[str] | None = typer.Option(None, "--remove-property"),
    file: str | None = typer.Option(None, "--file"),
) -> None:
    try:
        payload = _build_update_payload(
            property_json=property_json or [],
            remove_property=remove_property or [],
            file=file,
        )
    except CliError as error:
        fail(ctx, error)
    run_action(
        ctx,
        lambda client: client.update_object(uuid_text(object_id), payload),
        lambda payload, mode: render_object(payload, mode, prefix="Updated object"),
    )


@object_app.command("delete")
def delete_object(ctx: typer.Context, object_id: UUID) -> None:
    run_action(
        ctx,
        lambda client: client.delete_object(uuid_text(object_id)),
        lambda payload, mode: render_object_delete_result(
            payload,
            mode,
            object_id=uuid_text(object_id),
        ),
    )


@component_app.command("list")
def list_components(ctx: typer.Context, object_id: UUID) -> None:
    run_action(
        ctx,
        lambda client: client.list_object_components(uuid_text(object_id)),
        render_component_membership_list,
    )


@component_app.command("attach")
def attach_component(
    ctx: typer.Context,
    object_id: UUID,
    slot_name: str | None = typer.Option(None, "--slot-name"),
    component_object_id: UUID | None = typer.Option(None, "--component-object-id"),
    file: str | None = typer.Option(None, "--file"),
) -> None:
    try:
        payload = _build_attach_payload(
            slot_name=slot_name,
            component_object_id=component_object_id,
            file=file,
        )
    except CliError as error:
        fail(ctx, error)
    run_action(
        ctx,
        lambda client: client.attach_object_component(uuid_text(object_id), payload),
        lambda payload, mode: render_component_membership(
            payload,
            mode,
            prefix="Attached component",
        ),
    )


@component_app.command("detach")
def detach_component(ctx: typer.Context, component_object_id: UUID) -> None:
    run_action(
        ctx,
        lambda client: client.detach_object_component(uuid_text(component_object_id)),
        lambda payload, mode: render_component_membership(
            payload,
            mode,
            prefix="Detached component",
        ),
    )
