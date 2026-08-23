"""Installed process router for the interactive and non-interactive CLI."""

import asyncio
import sys

import httpx

from netauto.cli.execution import execute
from netauto.cli.model import (
    CliError,
    CliResult,
    ErrorSource,
    ExecutionLedger,
    HttpExchangeTrace,
    ParsedCommand,
)
from netauto.cli.parser import ParseFailure, ParseProgress, parse_process
from netauto.cli.render import render_json
from netauto.cli.repl import run_repl


def _internal_error(
    command: ParsedCommand | None = None,
    exchanges: tuple[HttpExchangeTrace, ...] = (),
) -> CliResult:
    return CliResult.failed(
        command,
        exchanges,
        CliError.create(
            ErrorSource.LOCAL,
            "cli_internal_error",
            "The CLI could not safely complete the command.",
        ),
    )


async def _run_noninteractive(
    argv: list[str],
    *,
    http_transport: httpx.AsyncBaseTransport | None = None,
) -> tuple[CliResult, int]:
    progress = ParseProgress()
    ledger = ExecutionLedger()
    try:
        try:
            endpoint, command, spec = parse_process(list(argv), progress=progress)
        except ParseFailure as failure:
            result = CliResult.failed(failure.command, (), failure.error)
            return result, 1
        result = await execute(
            endpoint,
            command,
            spec,
            http_transport=http_transport,
            ledger=ledger,
        )
    except Exception:  # bounded outer process boundary; never catches BaseException
        result = _internal_error(progress.command, ledger.snapshot())
    return result, 0 if result.status == "ok" else 1


def run(
    argv: list[str],
    *,
    http_transport: httpx.AsyncBaseTransport | None = None,
) -> tuple[CliResult, int]:
    """Preserve the accepted synchronous S05 non-interactive test boundary."""

    return asyncio.run(_run_noninteractive(argv, http_transport=http_transport))


async def _main_async(argv: list[str]) -> tuple[CliResult | None, int]:
    if not argv:
        return None, await run_repl()
    return await _run_noninteractive(argv)


def main() -> None:
    result, exit_code = asyncio.run(_main_async(sys.argv[1:]))
    if result is not None:
        sys.stdout.write(render_json(result))
    raise SystemExit(exit_code)
