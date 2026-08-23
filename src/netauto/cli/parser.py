"""Shared strict process and remote-command parser."""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn
from urllib.parse import urlsplit
from uuid import UUID

from netauto.cli.model import (
    CliError,
    CommandKey,
    CommandSpec,
    ErrorSource,
    JsonValue,
    ParameterKind,
    ParameterSpec,
    ParsedCommand,
)
from netauto.cli.registry import COMMAND_REGISTRY
from netauto.transport.http.common import datetime_carrier

_TOKEN = re.compile(r"[a-z]+(?:-[a-z]+)*\Z")
_PARAMETER = re.compile(r"[a-z][a-z0-9_]*\Z")
_POSITIVE_INTEGER = re.compile(r"[1-9][0-9]*\Z")

_MESSAGES = {
    "cli_invalid_invocation": "The non-interactive invocation is malformed.",
    "cli_invalid_command": "The requested command does not exist.",
    "cli_missing_selector": "The command requires a selector.",
    "cli_unexpected_selector": "The command does not accept that selector.",
    "cli_missing_parameter": "A required command parameter is missing.",
    "cli_unexpected_parameter": "The command parameter is not accepted.",
    "cli_duplicate_parameter": "A command parameter was supplied more than once.",
    "cli_invalid_parameter": "A command parameter is invalid.",
    "cli_json_error": "A structured parameter is not valid JSON.",
    "cli_file_error": "A structured parameter file cannot be read.",
}


class ParseFailure(Exception):
    """A bounded local parse result, never rendered from exception text."""

    def __init__(self, error: CliError, command: ParsedCommand | None = None) -> None:
        self.error = error
        self.command = command
        super().__init__(error.code)


@dataclass(slots=True)
class ParseProgress:
    """Last immutable command state safely recognized by the parser."""

    command: ParsedCommand | None = None

    def publish(self, command: ParsedCommand) -> ParsedCommand:
        self.command = command
        return command


def _command_snapshot(
    progress: ParseProgress | None,
    key: CommandKey,
    selector: str | None,
    parameters: dict[str, JsonValue],
) -> ParsedCommand:
    command = ParsedCommand.create(key, selector, parameters)
    return command if progress is None else progress.publish(command)


def _fail(
    code: str,
    *,
    details: dict[str, JsonValue] | None = None,
    command: ParsedCommand | None = None,
) -> NoReturn:
    raise ParseFailure(
        CliError.create(ErrorSource.LOCAL, code, _MESSAGES[code], details), command
    )


def _explicit_port(authority: str) -> int | None:
    if authority.startswith("["):
        closing_bracket = authority.find("]")
        if closing_bracket < 0:
            raise ValueError("invalid bracketed authority")
        suffix = authority[closing_bracket + 1 :]
        if not suffix:
            return None
        if not suffix.startswith(":"):
            raise ValueError("invalid bracketed authority suffix")
        port_text = suffix[1:]
    else:
        if authority.count(":") > 1:
            raise ValueError("unbracketed IPv6 authority")
        if ":" not in authority:
            return None
        _, port_text = authority.rsplit(":", 1)
    if re.fullmatch(r"[0-9]+", port_text) is None:
        raise ValueError("invalid explicit port")
    port = int(port_text)
    if not 1 <= port <= 65535:
        raise ValueError("explicit port outside TCP range")
    return port


def normalize_endpoint_root(value: str) -> str:
    try:
        parts = urlsplit(value)
        host = parts.hostname
    except ValueError:
        _fail("cli_invalid_invocation")
    scheme = parts.scheme.lower()
    if (
        scheme not in {"http", "https"}
        or host is None
        or parts.username is not None
        or parts.password is not None
        or parts.path not in {"", "/"}
        or parts.query
        or parts.fragment
        or "?" in value
        or "#" in value
    ):
        _fail("cli_invalid_invocation")
    try:
        port = _explicit_port(parts.netloc)
    except ValueError:
        _fail("cli_invalid_invocation")
    normalized_host = host.lower()
    if ":" in normalized_host:
        normalized_host = f"[{normalized_host}]"
    authority = normalized_host if port is None else f"{normalized_host}:{port}"
    return f"{scheme}://{authority}"


def _structured_value(raw: str, spec: ParameterSpec) -> JsonValue:
    source = raw
    if raw.startswith("@"):
        path = Path(raw[1:])
        try:
            if not path.is_file():
                _fail("cli_file_error", details={"parameter": spec.name})
            source = path.read_text(encoding="utf-8")
        except ParseFailure:
            raise
        except OSError, UnicodeError:
            _fail("cli_file_error", details={"parameter": spec.name})
    try:
        value: JsonValue = json.loads(source)
    except json.JSONDecodeError, UnicodeError:
        _fail("cli_json_error", details={"parameter": spec.name})
    if spec.kind is ParameterKind.JSON_OBJECT and not isinstance(value, dict):
        _fail("cli_invalid_parameter", details={"parameter": spec.name})
    if spec.kind is ParameterKind.JSON_ARRAY and not isinstance(value, list):
        _fail("cli_invalid_parameter", details={"parameter": spec.name})
    return value


def _decode(raw: str, spec: ParameterSpec) -> JsonValue:
    if raw == "null":
        if spec.nullable:
            return None
        _fail("cli_invalid_parameter", details={"parameter": spec.name})
    if spec.kind in {
        ParameterKind.JSON_OBJECT,
        ParameterKind.JSON_ARRAY,
        ParameterKind.JSON_VALUE,
    }:
        return _structured_value(raw, spec)
    if spec.kind is ParameterKind.POSITIVE_INTEGER:
        if _POSITIVE_INTEGER.fullmatch(raw) is None:
            _fail("cli_invalid_parameter", details={"parameter": spec.name})
        return int(raw)
    if spec.kind is ParameterKind.BOOLEAN:
        if raw == "true":
            return True
        if raw == "false":
            return False
        _fail("cli_invalid_parameter", details={"parameter": spec.name})
    if spec.kind is ParameterKind.ENUM:
        if raw not in spec.choices:
            _fail("cli_invalid_parameter", details={"parameter": spec.name})
        return raw
    if spec.kind is ParameterKind.UUID:
        if spec.selector_kind is not None:
            return raw
        try:
            return str(UUID(raw))
        except ValueError:
            _fail("cli_invalid_parameter", details={"parameter": spec.name})
    if spec.kind is ParameterKind.NULLABLE_STRING and raw.startswith('"'):
        try:
            decoded: object = json.loads(raw)
        except json.JSONDecodeError:
            _fail("cli_invalid_parameter", details={"parameter": spec.name})
        if not isinstance(decoded, str):
            _fail("cli_invalid_parameter", details={"parameter": spec.name})
        return decoded
    if spec.kind is ParameterKind.DATETIME:
        try:
            datetime_carrier(raw)
        except ValueError:
            _fail("cli_invalid_parameter", details={"parameter": spec.name})
    return raw


def _validate_relationship_definition_shape(
    command: ParsedCommand,
) -> None:
    if command.key == CommandKey("relationship-definition", "create"):
        symmetric = command.parameters.get("symmetric")
        present = command.parameters.keys()
        if symmetric is False:
            valid = (
                "perspectives" in present
                and "endpoint_template_ids" not in present
                and "name" not in present
            )
        else:
            valid = (
                symmetric is True
                and "endpoint_template_ids" in present
                and "name" in present
                and "perspectives" not in present
            )
        if not valid:
            _fail(
                "cli_invalid_parameter",
                details={"parameter": "symmetric"},
                command=command,
            )
    if command.key == CommandKey("relationship-definition", "rename"):
        has_resolutions = "resolutions" in command.parameters
        has_name = "name" in command.parameters
        if has_resolutions == has_name:
            _fail(
                "cli_invalid_parameter",
                details={"parameter": "resolutions/name"},
                command=command,
            )


def parse_process(
    argv: list[str],
    *,
    progress: ParseProgress | None = None,
) -> tuple[str, ParsedCommand, CommandSpec]:
    if len(argv) < 4 or argv[0] != "-n":
        _fail("cli_invalid_invocation")
    endpoint = normalize_endpoint_root(argv[1])
    command, spec = parse_remote_tokens(argv[2:], progress=progress)
    return endpoint, command, spec


def parse_remote_tokens(
    tokens: list[str],
    *,
    progress: ParseProgress | None = None,
) -> tuple[ParsedCommand, CommandSpec]:
    """Parse already-tokenized remote command input from argv or POSIX shlex."""

    if len(tokens) < 2:
        _fail("cli_invalid_invocation")
    resource, operation = tokens[0], tokens[1]
    key = CommandKey(resource, operation)
    empty_parameters: dict[str, JsonValue] = {}
    command = _command_snapshot(progress, key, None, empty_parameters)
    if _TOKEN.fullmatch(resource) is None or _TOKEN.fullmatch(operation) is None:
        _fail("cli_invalid_command", command=command)
    spec = COMMAND_REGISTRY.get(key)
    if spec is None:
        _fail("cli_invalid_command", command=command)

    remaining = list(tokens[2:])
    selector: str | None = None
    if spec.selector_kind is not None:
        if not remaining or "=" in remaining[0]:
            _fail("cli_missing_selector", command=command)
        selector = remaining.pop(0)
        command = _command_snapshot(progress, key, selector, empty_parameters)
    elif remaining and "=" not in remaining[0]:
        command = _command_snapshot(progress, key, remaining[0], empty_parameters)
        _fail(
            "cli_unexpected_selector",
            command=command,
        )

    by_name = {parameter.name: parameter for parameter in spec.parameters}
    decoded: dict[str, JsonValue] = {}
    for token in remaining:
        if "=" not in token:
            _fail(
                "cli_unexpected_selector",
                command=_command_snapshot(progress, key, selector, decoded),
            )
        name, raw = token.split("=", 1)
        if _PARAMETER.fullmatch(name) is None or name not in by_name:
            _fail(
                "cli_unexpected_parameter",
                details={"parameter": name},
                command=_command_snapshot(progress, key, selector, decoded),
            )
        if name in decoded:
            _fail(
                "cli_duplicate_parameter",
                details={"parameter": name},
                command=_command_snapshot(progress, key, selector, decoded),
            )
        try:
            decoded[name] = _decode(raw, by_name[name])
        except ParseFailure as error:
            if error.command is None:
                error.command = _command_snapshot(progress, key, selector, decoded)
            raise
        _command_snapshot(progress, key, selector, decoded)

    command = _command_snapshot(progress, key, selector, decoded)
    for parameter in spec.parameters:
        if parameter.required and parameter.name not in decoded:
            _fail(
                "cli_missing_parameter",
                details={"parameter": parameter.name},
                command=command,
            )
    _validate_relationship_definition_shape(command)
    return command, spec


def parse_command_example(
    spec: CommandSpec,
    index: int = 0,
    *,
    endpoint_root: str = "http://example.test",
) -> ParsedCommand:
    """Validate registry-owned example tokens through the production parser."""

    _, command, parsed_spec = parse_process(
        ["-n", endpoint_root, *spec.examples[index]]
    )
    if parsed_spec is not spec:
        raise RuntimeError("registry example resolved to a different command")
    return command
