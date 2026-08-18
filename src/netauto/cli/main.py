"""Installed ``netauto -n`` process boundary for S05."""

import asyncio
import sys

from netauto.cli.execution import execute
from netauto.cli.model import CliError, CliResult, ErrorSource, ParsedCommand
from netauto.cli.parser import ParseFailure, parse_process
from netauto.cli.render import render_json


def _internal_error(command: ParsedCommand | None = None) -> CliResult:
    return CliResult.failed(
        command,
        (),
        CliError.create(
            ErrorSource.LOCAL,
            "cli_internal_error",
            "The CLI could not safely complete the command.",
        ),
    )


def run(argv: list[str]) -> tuple[CliResult, int]:
    try:
        endpoint, command, spec = parse_process(list(argv))
    except ParseFailure as failure:
        result = CliResult.failed(failure.command, (), failure.error)
        return result, 1
    try:
        result = asyncio.run(execute(endpoint, command, spec))
    except Exception:  # bounded outer process boundary; never catches BaseException
        result = _internal_error(command)
    return result, 0 if result.status == "ok" else 1


def main() -> None:
    result, exit_code = run(sys.argv[1:])
    sys.stdout.write(render_json(result))
    raise SystemExit(exit_code)
