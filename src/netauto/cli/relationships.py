"""Typer commands for relationship definitions."""

from uuid import UUID

import typer

from netauto.cli.client import JSONObject
from netauto.cli.common import fail, run_action, uuid_text
from netauto.cli.errors import CliError, InputError
from netauto.cli.input import ensure_modes_are_exclusive, load_json_object
from netauto.cli.output import (
    render_relationship_definition,
    render_relationship_definition_delete_result,
    render_relationship_definition_list,
)

relationship_definition_app = typer.Typer(help="Manage relationship definitions.")


def _build_create_payload(
    *,
    source_template_id: UUID | None,
    target_template_id: UUID | None,
    forward_name: str | None,
    reverse_name: str | None,
    file: str | None,
) -> JSONObject:
    inline_present = any(
        value is not None
        for value in (
            source_template_id,
            target_template_id,
            forward_name,
            reverse_name,
        )
    )
    ensure_modes_are_exclusive(file=file, inline_values_present=inline_present)
    if file is not None:
        return load_json_object(file)
    if None in (source_template_id, target_template_id, forward_name, reverse_name):
        raise InputError(
            "Inline create mode requires --source-template-id, --target-template-id, "
            "--forward-name, and --reverse-name."
        )
    assert source_template_id is not None
    assert target_template_id is not None
    assert forward_name is not None
    assert reverse_name is not None
    return {
        "source_template_id": uuid_text(source_template_id),
        "target_template_id": uuid_text(target_template_id),
        "forward_name": forward_name,
        "reverse_name": reverse_name,
    }


@relationship_definition_app.command("list")
def list_relationship_definitions(ctx: typer.Context) -> None:
    run_action(
        ctx,
        lambda client: client.list_relationship_definitions(),
        render_relationship_definition_list,
    )


@relationship_definition_app.command("show")
def show_relationship_definition(ctx: typer.Context, definition_id: UUID) -> None:
    run_action(
        ctx,
        lambda client: client.get_relationship_definition(uuid_text(definition_id)),
        render_relationship_definition,
    )


@relationship_definition_app.command("create")
def create_relationship_definition(
    ctx: typer.Context,
    source_template_id: UUID | None = typer.Option(None, "--source-template-id"),
    target_template_id: UUID | None = typer.Option(None, "--target-template-id"),
    forward_name: str | None = typer.Option(None, "--forward-name"),
    reverse_name: str | None = typer.Option(None, "--reverse-name"),
    file: str | None = typer.Option(None, "--file"),
) -> None:
    try:
        payload = _build_create_payload(
            source_template_id=source_template_id,
            target_template_id=target_template_id,
            forward_name=forward_name,
            reverse_name=reverse_name,
            file=file,
        )
    except CliError as error:
        fail(ctx, error)
    run_action(
        ctx,
        lambda client: client.create_relationship_definition(payload),
        lambda payload, mode: render_relationship_definition(
            payload,
            mode,
            prefix="Created relationship definition",
        ),
    )


@relationship_definition_app.command("delete")
def delete_relationship_definition(ctx: typer.Context, definition_id: UUID) -> None:
    run_action(
        ctx,
        lambda client: client.delete_relationship_definition(uuid_text(definition_id)),
        lambda payload, mode: render_relationship_definition_delete_result(
            payload,
            mode,
            definition_id=uuid_text(definition_id),
        ),
    )
