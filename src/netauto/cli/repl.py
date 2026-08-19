"""Asynchronous prompt-toolkit REPL and exact interactive session state."""

import shlex
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import TextIO, cast

import httpx
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import clear

from netauto.cli.execution import execute_connected
from netauto.cli.model import (
    CliError,
    CliResult,
    CommandKey,
    CommandSpec,
    ErrorSource,
    ExecutionLedger,
    HttpExchangeTrace,
    JsonValue,
    ParsedCommand,
    RequestPlan,
)
from netauto.cli.parser import (
    ParseFailure,
    ParseProgress,
    normalize_endpoint_root,
    parse_remote_tokens,
)
from netauto.cli.protocol import interpret_response
from netauto.cli.registry import COMMAND_REGISTRY
from netauto.cli.render import render_formatted, render_json
from netauto.cli.transport import HttpTransport, TransportFailure
from netauto.transport.http.health import CoreHealthDTO


class ConnectionState(StrEnum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTED = "CONNECTED"


class OutputMode(StrEnum):
    FORMATTED = "FORMATTED"
    JSON = "JSON"


@dataclass(frozen=True, slots=True)
class LocalCommandSpec:
    name: str
    minimum_arguments: int
    maximum_arguments: int
    usage: str
    help_text: str


_LOCAL_SPECS = (
    LocalCommandSpec(
        "connect",
        1,
        1,
        "/connect <endpoint-root>",
        "Connect after an exact Core Health readiness check.",
    ),
    LocalCommandSpec(
        "disconnect", 0, 0, "/disconnect", "Close the current endpoint connection."
    ),
    LocalCommandSpec(
        "status", 0, 0, "/status", "Show or revalidate the current connection state."
    ),
    LocalCommandSpec(
        "output",
        1,
        1,
        "/output <JSON|FORMATTED>",
        "Select the exact interactive output mode.",
    ),
    LocalCommandSpec(
        "help",
        0,
        2,
        "/help [resource] [operation]",
        "Show registry-derived local and remote help.",
    ),
    LocalCommandSpec(
        "history", 0, 0, "/history", "Show completed non-empty session lines."
    ),
    LocalCommandSpec(
        "clear", 0, 0, "/clear", "Clear the terminal while preserving session state."
    ),
    LocalCommandSpec("exit", 0, 0, "/exit", "Close the connection and exit normally."),
)

LOCAL_COMMAND_REGISTRY: Mapping[str, LocalCommandSpec] = MappingProxyType(
    {spec.name: spec for spec in _LOCAL_SPECS}
)


@dataclass(frozen=True, slots=True)
class InteractiveOutcome:
    result: CliResult
    spec: CommandSpec | None
    presentation: JsonValue | None
    exit_requested: bool = False


def _local_command(name: str, arguments: list[str]) -> ParsedCommand:
    selector = arguments[0] if arguments else None
    parameters: dict[str, JsonValue] = {}
    if len(arguments) > 1:
        parameters["arguments"] = list(arguments[1:])
    return ParsedCommand.create(CommandKey("local", name), selector, parameters)


def _local_error(
    command: ParsedCommand | None,
    code: str,
    message: str,
    *,
    details: dict[str, JsonValue] | None = None,
    exchanges: tuple[HttpExchangeTrace, ...] = (),
) -> InteractiveOutcome:
    return InteractiveOutcome(
        CliResult.failed(
            command,
            exchanges,
            CliError.create(ErrorSource.LOCAL, code, message, details),
        ),
        None,
        None,
    )


def _state_payload(
    state: ConnectionState,
    output: OutputMode,
    endpoint: str | None,
) -> dict[str, JsonValue]:
    return {
        "connection": state.value,
        "endpoint": endpoint,
        "output": output.value,
    }


def _health_protocol_error(status: int) -> CliError:
    return CliError.create(
        ErrorSource.PROTOCOL,
        "cli_protocol_error",
        "The server response violates the same-release HTTP contract.",
        http_status=status,
    )


async def _health_check(
    transport: HttpTransport,
    ledger: ExecutionLedger,
) -> tuple[dict[str, JsonValue] | None, CliError | None]:
    transport.use_ledger(ledger)
    try:
        response, exchange = await transport.exchange(
            # Health is operational and intentionally absent from COMMAND_REGISTRY.
            RequestPlan.create("GET", "/health/core", (), None)
        )
    except TransportFailure:
        return (
            None,
            CliError.create(
                ErrorSource.TRANSPORT,
                "cli_transport_error",
                "The HTTP request could not be completed.",
            ),
        )
    outcome = interpret_response(
        response,
        exchange,
        expected_status=200,
        response_annotation=CoreHealthDTO,
    )
    if outcome.error is not None or not isinstance(outcome.result, dict):
        return None, _health_protocol_error(response.status_code)
    health = cast(dict[str, JsonValue], outcome.result)
    app = health.get("app_status")
    database = health.get("db_status")
    if not isinstance(app, dict) or not isinstance(database, dict):
        return None, _health_protocol_error(response.status_code)
    app_status = cast(dict[str, JsonValue], app)
    db_status = cast(dict[str, JsonValue], database)
    # Exact same-release responses omit absent optional messages rather than using null.
    if (
        app_status.get("status") != "ok"
        or db_status.get("status") != "ok"
        or ("message" in app_status and app_status["message"] is None)
        or ("message" in db_status and db_status["message"] is None)
    ):
        return None, _health_protocol_error(response.status_code)
    return health, None


class InteractiveSession:
    """Mutable process-local state with one endpoint-scoped client."""

    def __init__(
        self,
        *,
        http_transport: httpx.AsyncBaseTransport | None = None,
        clear_terminal: Callable[[], object] = clear,
    ) -> None:
        self.connection = ConnectionState.DISCONNECTED
        self.output = OutputMode.FORMATTED
        self.endpoint: str | None = None
        self.history: list[str] = []
        self._transport: HttpTransport | None = None
        self._http_transport = http_transport
        self._clear_terminal = clear_terminal

    @property
    def transport(self) -> HttpTransport | None:
        return self._transport

    async def _discard_transport(self) -> None:
        transport = self._transport
        self._transport = None
        self.endpoint = None
        self.connection = ConnectionState.DISCONNECTED
        if transport is not None:
            await transport.close()

    async def close(self) -> None:
        await self._discard_transport()

    def complete_line(self, line: str) -> None:
        """Append only after the command result has been fully rendered."""

        if line.strip():
            self.history.append(line)

    def _success(
        self,
        command: ParsedCommand,
        payload: JsonValue | None,
        *,
        ledger: ExecutionLedger | None = None,
        exit_requested: bool = False,
    ) -> InteractiveOutcome:
        exchanges = () if ledger is None else ledger.snapshot()
        return InteractiveOutcome(
            CliResult.ok(command, exchanges, payload),
            None,
            payload,
            exit_requested,
        )

    async def _connect(
        self,
        command: ParsedCommand,
        endpoint_argument: str,
        ledger: ExecutionLedger,
    ) -> InteractiveOutcome:
        await self._discard_transport()
        try:
            endpoint = normalize_endpoint_root(endpoint_argument)
        except ParseFailure as failure:
            return InteractiveOutcome(
                CliResult.failed(command, (), failure.error), None, None
            )
        candidate = HttpTransport(
            endpoint,
            transport=self._http_transport,
            ledger=ledger,
        )
        try:
            health, error = await _health_check(candidate, ledger)
            if error is not None or health is None:
                await candidate.close()
                return InteractiveOutcome(
                    CliResult.failed(
                        command, ledger.snapshot(), error or _health_protocol_error(200)
                    ),
                    None,
                    None,
                )
        except Exception:
            await candidate.close()
            raise
        self._transport = candidate
        self.endpoint = endpoint
        self.connection = ConnectionState.CONNECTED
        payload: dict[str, JsonValue] = {
            **_state_payload(self.connection, self.output, self.endpoint),
            "health": health,
        }
        return self._success(command, payload, ledger=ledger)

    async def _status(
        self, command: ParsedCommand, ledger: ExecutionLedger
    ) -> InteractiveOutcome:
        if self._transport is None:
            payload = _state_payload(self.connection, self.output, self.endpoint)
            return self._success(command, payload)
        health, error = await _health_check(self._transport, ledger)
        if error is not None or health is None:
            await self._discard_transport()
            return InteractiveOutcome(
                CliResult.failed(
                    command, ledger.snapshot(), error or _health_protocol_error(200)
                ),
                None,
                None,
            )
        payload: dict[str, JsonValue] = {
            **_state_payload(self.connection, self.output, self.endpoint),
            "health": health,
        }
        return self._success(command, payload, ledger=ledger)

    def _help(self, arguments: list[str]) -> tuple[JsonValue | None, CliError | None]:
        if not arguments:
            overview: dict[str, JsonValue] = {
                "grammar": ("<resource> <operation> [selector] [parameter=value ...]"),
                "local_commands": cast(
                    list[JsonValue], [spec.usage for spec in _LOCAL_SPECS]
                ),
                "resources": cast(
                    list[JsonValue],
                    sorted({key.resource for key in COMMAND_REGISTRY}),
                ),
            }
            return (
                overview,
                None,
            )
        resource = arguments[0]
        operations = [
            spec for key, spec in COMMAND_REGISTRY.items() if key.resource == resource
        ]
        if not operations:
            return (
                None,
                CliError.create(
                    ErrorSource.LOCAL,
                    "cli_invalid_command",
                    "The requested command does not exist.",
                    {"resource": resource},
                ),
            )
        if len(arguments) == 1:
            return (
                {
                    "resource": resource,
                    "operations": [spec.key.operation for spec in operations],
                },
                None,
            )
        operation = arguments[1]
        spec = COMMAND_REGISTRY.get(CommandKey(resource, operation))
        if spec is None:
            return (
                None,
                CliError.create(
                    ErrorSource.LOCAL,
                    "cli_invalid_command",
                    "The requested command does not exist.",
                    {"resource": resource, "operation": operation},
                ),
            )
        return (
            {
                "resource": resource,
                "operation": operation,
                "description": spec.help_text,
                "selector": (
                    None if spec.selector_kind is None else spec.selector_kind.value
                ),
                "parameters": [
                    {
                        "name": parameter.name,
                        "type": parameter.kind.value,
                        "required": parameter.required,
                        "nullable": parameter.nullable,
                    }
                    for parameter in spec.parameters
                ],
                "http": {"method": spec.method, "path": spec.path_template},
                "examples": [shlex.join(example) for example in spec.examples],
            },
            None,
        )

    async def _local(
        self,
        name: str,
        arguments: list[str],
        progress: ParseProgress,
        ledger: ExecutionLedger,
    ) -> InteractiveOutcome:
        command = progress.publish(_local_command(name, arguments))
        local_spec = LOCAL_COMMAND_REGISTRY.get(name)
        if local_spec is None:
            return _local_error(
                command,
                "cli_invalid_command",
                "The requested command does not exist.",
            )
        if (
            not local_spec.minimum_arguments
            <= len(arguments)
            <= local_spec.maximum_arguments
        ):
            return _local_error(
                command,
                "cli_invalid_invocation",
                "The interactive command invocation is malformed.",
                details={"usage": local_spec.usage},
            )
        if name == "connect":
            return await self._connect(command, arguments[0], ledger)
        if name == "disconnect":
            await self._discard_transport()
            payload = _state_payload(self.connection, self.output, self.endpoint)
            return self._success(command, payload)
        if name == "status":
            return await self._status(command, ledger)
        if name == "output":
            try:
                self.output = OutputMode(arguments[0])
            except ValueError:
                return _local_error(
                    command,
                    "cli_invalid_parameter",
                    "A command parameter is invalid.",
                    details={"parameter": "output"},
                )
            payload = _state_payload(self.connection, self.output, self.endpoint)
            return self._success(command, payload)
        if name == "help":
            help_payload, error = self._help(arguments)
            if error is not None:
                return InteractiveOutcome(
                    CliResult.failed(command, (), error), None, None
                )
            return self._success(command, help_payload)
        if name == "history":
            payload: dict[str, JsonValue] = {
                "entries": [
                    {"number": number, "line": line}
                    for number, line in enumerate(self.history, start=1)
                ]
            }
            return self._success(command, payload)
        if name == "clear":
            self._clear_terminal()
            payload = {
                **_state_payload(self.connection, self.output, self.endpoint),
                "cleared": True,
            }
            return self._success(command, payload)
        if name == "exit":
            await self._discard_transport()
            return self._success(command, {"exiting": True}, exit_requested=True)
        raise RuntimeError("local command registry dispatch mismatch")

    async def submit(self, line: str) -> InteractiveOutcome | None:
        """Execute one non-empty submitted line; ordinary defects are bounded."""

        if not line.strip():
            return None
        progress = ParseProgress()
        ledger = ExecutionLedger()
        try:
            try:
                tokens = shlex.split(line, posix=True)
            except ValueError:
                return _local_error(
                    None,
                    "cli_invalid_invocation",
                    "The interactive command invocation is malformed.",
                )
            if not tokens:
                return None
            if tokens[0].startswith("/"):
                return await self._local(tokens[0][1:], tokens[1:], progress, ledger)
            try:
                command, spec = parse_remote_tokens(tokens, progress=progress)
            except ParseFailure as failure:
                return InteractiveOutcome(
                    CliResult.failed(failure.command, (), failure.error), None, None
                )
            if self._transport is None:
                return _local_error(
                    command,
                    "cli_not_connected",
                    "The CLI is not connected to an endpoint.",
                )
            result, presentation = await execute_connected(
                self._transport,
                command,
                spec,
                ledger=ledger,
                formatted=self.output is OutputMode.FORMATTED,
            )
            if (
                result.error is not None
                and result.error.source is ErrorSource.TRANSPORT
            ):
                await self._discard_transport()
            return InteractiveOutcome(result, spec, presentation)
        except Exception:  # bounded per-command boundary; never catches BaseException
            try:
                await self._discard_transport()
            except Exception:
                # State was cleared before close, so no uncertain client remains
                # adopted.
                pass
            return InteractiveOutcome(
                CliResult.failed(
                    progress.command,
                    ledger.snapshot(),
                    CliError.create(
                        ErrorSource.LOCAL,
                        "cli_internal_error",
                        "The CLI could not safely complete the command.",
                    ),
                ),
                None,
                None,
            )


def render_interactive(session: InteractiveSession, outcome: InteractiveOutcome) -> str:
    if session.output is OutputMode.JSON:
        return render_json(outcome.result)
    return render_formatted(outcome.result, outcome.spec, outcome.presentation)


async def run_repl(
    *,
    prompt_session: PromptSession[str] | None = None,
    state: InteractiveSession | None = None,
    stdout: TextIO | None = None,
) -> int:
    """Run the official asynchronous REPL until /exit or empty-prompt Ctrl-D."""

    interactive = InteractiveSession() if state is None else state
    prompt = (
        PromptSession[str](history=InMemoryHistory(), enable_history_search=True)
        if prompt_session is None
        else prompt_session
    )
    output = sys.stdout if stdout is None else stdout
    try:
        while True:
            try:
                line = await prompt.prompt_async("netauto>")
            except KeyboardInterrupt:
                continue
            except EOFError:
                return 0
            outcome = await interactive.submit(line)
            if outcome is None:
                continue
            output.write(render_interactive(interactive, outcome))
            output.flush()
            interactive.complete_line(line)
            if outcome.exit_requested:
                return 0
    finally:
        await interactive.close()
