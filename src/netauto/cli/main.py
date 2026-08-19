"""Installed ``netauto -n`` process boundary for S05."""

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


def run(
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
        result = asyncio.run(
            execute(
                endpoint,
                command,
                spec,
                http_transport=http_transport,
                ledger=ledger,
            )
        )
    except Exception:  # bounded outer process boundary; never catches BaseException
        result = _internal_error(progress.command, ledger.snapshot())
    return result, 0 if result.status == "ok" else 1


def main() -> None:
    result, exit_code = run(sys.argv[1:])
    sys.stdout.write(render_json(result))
    raise SystemExit(exit_code)
