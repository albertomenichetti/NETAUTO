"""Immutable CLI command, request, trace, error, and result values."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Final

from netauto.domain.primitives import JsonValue

type JsonObject = dict[str, JsonValue]

LOCAL_ERROR_CODES: Final = frozenset(
    {
        "cli_invalid_invocation",
        "cli_invalid_command",
        "cli_missing_selector",
        "cli_unexpected_selector",
        "cli_missing_parameter",
        "cli_unexpected_parameter",
        "cli_duplicate_parameter",
        "cli_invalid_parameter",
        "cli_json_error",
        "cli_file_error",
        "cli_not_connected",
        "cli_internal_error",
    }
)
SELECTOR_ERROR_CODES: Final = frozenset(
    {
        "cli_selector_invalid",
        "cli_selector_not_found",
        "cli_selector_ambiguous",
    }
)
TRANSPORT_PROTOCOL_ERROR_CODES: Final = frozenset(
    {"cli_transport_error", "cli_protocol_error"}
)


class SelectorKind(StrEnum):
    DATATYPE = "datatype"
    OBJECT_TEMPLATE = "object-template"
    OBJECT = "object"
    RELATIONSHIP_DEFINITION = "relationship-definition"
    RELATIONSHIP = "relationship"
    RESOLUTION = "relationship-resolution"


class ParameterKind(StrEnum):
    STRING = "string"
    NULLABLE_STRING = "nullable-string"
    POSITIVE_INTEGER = "positive-integer"
    BOOLEAN = "boolean"
    UUID = "uuid"
    JSON_OBJECT = "json-object"
    JSON_ARRAY = "json-array"
    JSON_VALUE = "json-value"
    ENUM = "enum"
    DATETIME = "datetime"


class ParameterLocation(StrEnum):
    PATH = "path"
    QUERY = "query"
    BODY = "body"


class ErrorSource(StrEnum):
    LOCAL = "local"
    SELECTOR = "selector"
    TRANSPORT = "transport"
    REMOTE = "remote"
    PROTOCOL = "protocol"


@dataclass(frozen=True, slots=True, order=True)
class CommandKey:
    resource: str
    operation: str


@dataclass(frozen=True, slots=True)
class NestedSelector:
    path: tuple[str, ...]
    kind: SelectorKind


@dataclass(frozen=True, slots=True)
class ParameterSpec:
    name: str
    kind: ParameterKind
    location: ParameterLocation
    required: bool = False
    nullable: bool = False
    choices: frozenset[str] = frozenset()
    selector_kind: SelectorKind | None = None
    nested_selectors: tuple[NestedSelector, ...] = ()


@dataclass(frozen=True, slots=True)
class CommandSpec:
    key: CommandKey
    method: str
    path_template: str
    selector_kind: SelectorKind | None
    selector_parameter: str | None
    parameters: tuple[ParameterSpec, ...]
    expected_status: int
    response_annotation: object | None
    request_annotation: object | None
    location_template: str | None
    help_text: str
    example: str
    renderer_key: str


@dataclass(frozen=True, slots=True)
class ParsedCommand:
    key: CommandKey
    selector: str | None
    parameters: Mapping[str, JsonValue]

    @classmethod
    def create(
        cls,
        key: CommandKey,
        selector: str | None,
        parameters: dict[str, JsonValue],
    ) -> ParsedCommand:
        return cls(key, selector, MappingProxyType(dict(parameters)))

    def as_json(self) -> JsonObject:
        return {
            "resource": self.key.resource,
            "operation": self.key.operation,
            "selector": self.selector,
            "parameters": dict(self.parameters),
        }


@dataclass(frozen=True, slots=True)
class RequestPlan:
    method: str
    path: str
    query: tuple[tuple[str, str], ...]
    body: JsonValue | None


@dataclass(frozen=True, slots=True)
class HttpRequestTrace:
    method: str
    url: str
    query: Mapping[str, tuple[str, ...]]
    headers: Mapping[str, tuple[str, ...]]
    body: JsonValue | None

    def as_json(self) -> JsonObject:
        return {
            "method": self.method,
            "url": self.url,
            "query": {key: list(value) for key, value in self.query.items()},
            "headers": {key: list(value) for key, value in self.headers.items()},
            "body": self.body,
        }


@dataclass(frozen=True, slots=True)
class HttpResponseTrace:
    status_code: int
    headers: Mapping[str, tuple[str, ...]]
    body_format: str
    body: JsonValue | None

    def as_json(self) -> JsonObject:
        return {
            "status_code": self.status_code,
            "headers": {key: list(value) for key, value in self.headers.items()},
            "body_format": self.body_format,
            "body": self.body,
        }


@dataclass(frozen=True, slots=True)
class HttpExchangeTrace:
    request: HttpRequestTrace
    response: HttpResponseTrace | None
    elapsed_ms: int

    def as_json(self) -> JsonObject:
        return {
            "request": self.request.as_json(),
            "response": None if self.response is None else self.response.as_json(),
            "elapsed_ms": self.elapsed_ms,
        }


@dataclass(frozen=True, slots=True)
class CliError:
    source: ErrorSource
    code: str
    message: str
    details: Mapping[str, JsonValue]
    http_status: int | None = None

    @classmethod
    def create(
        cls,
        source: ErrorSource,
        code: str,
        message: str,
        details: dict[str, JsonValue] | None = None,
        http_status: int | None = None,
    ) -> CliError:
        return cls(
            source,
            code,
            message,
            MappingProxyType({} if details is None else dict(details)),
            http_status,
        )

    def as_json(self) -> JsonObject:
        return {
            "source": self.source.value,
            "code": self.code,
            "message": self.message,
            "details": dict(self.details),
            "http_status": self.http_status,
        }


@dataclass(frozen=True, slots=True)
class CliResult:
    status: str
    command: ParsedCommand | None
    exchanges: tuple[HttpExchangeTrace, ...]
    result: JsonValue | None
    error: CliError | None

    @classmethod
    def ok(
        cls,
        command: ParsedCommand,
        exchanges: tuple[HttpExchangeTrace, ...],
        result: JsonValue | None,
    ) -> CliResult:
        return cls("ok", command, exchanges, result, None)

    @classmethod
    def failed(
        cls,
        command: ParsedCommand | None,
        exchanges: tuple[HttpExchangeTrace, ...],
        error: CliError,
    ) -> CliResult:
        return cls("error", command, exchanges, None, error)

    def as_json(self) -> JsonObject:
        return {
            "status": self.status,
            "command": None if self.command is None else self.command.as_json(),
            "exchanges": [exchange.as_json() for exchange in self.exchanges],
            "result": self.result,
            "error": None if self.error is None else self.error.as_json(),
        }
