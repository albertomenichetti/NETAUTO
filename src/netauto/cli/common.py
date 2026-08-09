"""Shared CLI command helpers."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar
from uuid import UUID

import typer

from netauto.cli.client import NetautoApiClient
from netauto.cli.errors import ApiError, CliError, InputError, ProtocolError, TransportError
from netauto.cli.output import OutputMode, render_error

PayloadT = TypeVar("PayloadT")


@dataclass(frozen=True, slots=True)
class CliContext:
    api_url: str
    output: OutputMode


def context_from_typer(ctx: typer.Context) -> CliContext:
    context = ctx.obj
    if not isinstance(context, CliContext):
        raise InputError("CLI context is invalid.")
    return context


def fail(ctx: typer.Context, error: CliError) -> None:
    typer.echo(render_error(error, context_from_typer(ctx).output), err=True)
    raise typer.Exit(code=_exit_code(error))


def run_action(
    ctx: typer.Context,
    action: Callable[[NetautoApiClient], PayloadT],
    renderer: Callable[[PayloadT, OutputMode], str],
) -> None:
    config = context_from_typer(ctx)
    try:
        with NetautoApiClient(config.api_url) as client:
            payload = action(client)
        typer.echo(renderer(payload, config.output))
    except CliError as error:
        fail(ctx, error)


def uuid_text(value: UUID) -> str:
    return str(value)


def _exit_code(error: CliError) -> int:
    if isinstance(error, ApiError):
        return 1
    if isinstance(error, InputError):
        return 2
    if isinstance(error, TransportError):
        return 3
    if isinstance(error, ProtocolError):
        return 4
    return 2
