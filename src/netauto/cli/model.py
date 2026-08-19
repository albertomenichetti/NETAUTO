"""Immutable CLI command, request, trace, error, and result values."""

import shlex
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Final, cast, overload

type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]
type JsonObject = dict[str, JsonValue]


class FrozenJsonObject(Mapping[str, "FrozenJsonValue"]):
    """Recursively immutable JSON object with value-based equality."""

    __slots__ = ("_values",)

    def __init__(self, values: Mapping[str, object]) -> None:
        self._values = MappingProxyType(
            {key: _freeze_json(value) for key, value in values.items()}
        )

    def __getitem__(self, key: str) -> FrozenJsonValue:
        return self._values[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Mapping):
            return False
        other_mapping = cast(Mapping[object, object], other)
        return dict(self.items()) == dict(other_mapping.items())

    def __repr__(self) -> str:
        return repr(dict(self.items()))


class FrozenJsonArray(Sequence["FrozenJsonValue"]):
    """Recursively immutable JSON array with value-based equality."""

    __slots__ = ("_values",)

    def __init__(self, values: Sequence[object]) -> None:
        self._values = tuple(_freeze_json(value) for value in values)

    @overload
    def __getitem__(self, index: int) -> FrozenJsonValue: ...

    @overload
    def __getitem__(self, index: slice) -> tuple[FrozenJsonValue, ...]: ...

    def __getitem__(
        self, index: int | slice
    ) -> FrozenJsonValue | tuple[FrozenJsonValue, ...]:
        return self._values[index]

    def __len__(self) -> int:
        return len(self._values)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str | bytes) or not isinstance(other, Sequence):
            return False
        return tuple(self) == tuple(cast(Sequence[object], other))

    def __repr__(self) -> str:
        return repr(list(self._values))


type FrozenJsonValue = JsonScalar | FrozenJsonObject | FrozenJsonArray


def _freeze_json(value: object) -> FrozenJsonValue:
    if isinstance(value, FrozenJsonObject | FrozenJsonArray):
        return value
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, Mapping):
        mapping = cast(Mapping[object, object], value)
        if not all(isinstance(key, str) for key in mapping):
            raise TypeError("JSON object keys must be strings")
        return FrozenJsonObject(cast(Mapping[str, object], mapping))
    if isinstance(value, list):
        return FrozenJsonArray(cast(list[object], value))
    raise TypeError("unsupported JSON value")


def freeze_json(value: JsonValue | FrozenJsonValue) -> FrozenJsonValue:
    """Take a recursive immutable JSON snapshot without coercion."""

    return _freeze_json(value)


def thaw_json(value: FrozenJsonValue) -> JsonValue:
    """Return a recursively detached, ordinary JSON carrier."""

    if isinstance(value, FrozenJsonObject):
        return {key: thaw_json(item) for key, item in value.items()}
    if isinstance(value, FrozenJsonArray):
        return [thaw_json(item) for item in value]
    return value


def freeze_json_object(values: Mapping[str, JsonValue]) -> FrozenJsonObject:
    """Take a recursive immutable snapshot of one JSON object."""

    return FrozenJsonObject(cast(Mapping[str, object], values))


def _freeze_multimap(
    values: Mapping[str, Sequence[str]],
) -> Mapping[str, tuple[str, ...]]:
    return MappingProxyType({key: tuple(items) for key, items in values.items()})


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
    examples: tuple[tuple[str, ...], ...]
    renderer_key: str

    @property
    def selector_required(self) -> bool:
        return self.selector_kind is not None

    @property
    def example_argv(self) -> tuple[str, ...]:
        return self.examples[0]

    @property
    def example(self) -> str:
        return shlex.join(self.example_argv)


@dataclass(frozen=True, slots=True)
class ParsedCommand:
    key: CommandKey
    selector: str | None
    parameters: FrozenJsonObject

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "parameters",
            FrozenJsonObject(cast(Mapping[str, object], self.parameters)),
        )

    @classmethod
    def create(
        cls,
        key: CommandKey,
        selector: str | None,
        parameters: Mapping[str, JsonValue],
    ) -> ParsedCommand:
        return cls(key, selector, freeze_json_object(parameters))

    def as_json(self) -> JsonObject:
        return {
            "resource": self.key.resource,
            "operation": self.key.operation,
            "selector": self.selector,
            "parameters": thaw_json(self.parameters),
        }


@dataclass(frozen=True, slots=True)
class RequestPlan:
    method: str
    path: str
    query: tuple[tuple[str, str], ...]
    body: FrozenJsonValue | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "query", tuple(tuple(item) for item in self.query))
        if self.body is not None:
            object.__setattr__(self, "body", freeze_json(self.body))

    @classmethod
    def create(
        cls,
        method: str,
        path: str,
        query: tuple[tuple[str, str], ...],
        body: JsonValue | FrozenJsonValue | None,
    ) -> RequestPlan:
        return cls(method, path, query, None if body is None else freeze_json(body))


@dataclass(frozen=True, slots=True)
class HttpRequestTrace:
    method: str
    url: str
    query: Mapping[str, tuple[str, ...]]
    headers: Mapping[str, tuple[str, ...]]
    body: FrozenJsonValue | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "query", _freeze_multimap(self.query))
        object.__setattr__(self, "headers", _freeze_multimap(self.headers))
        if self.body is not None:
            object.__setattr__(self, "body", freeze_json(self.body))

    def as_json(self) -> JsonObject:
        return {
            "method": self.method,
            "url": self.url,
            "query": {key: list(value) for key, value in self.query.items()},
            "headers": {key: list(value) for key, value in self.headers.items()},
            "body": None if self.body is None else thaw_json(self.body),
        }


@dataclass(frozen=True, slots=True)
class HttpResponseTrace:
    status_code: int
    headers: Mapping[str, tuple[str, ...]]
    body_format: str
    body: FrozenJsonValue | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "headers", _freeze_multimap(self.headers))
        if self.body is not None:
            object.__setattr__(self, "body", freeze_json(self.body))

    def as_json(self) -> JsonObject:
        return {
            "status_code": self.status_code,
            "headers": {key: list(value) for key, value in self.headers.items()},
            "body_format": self.body_format,
            "body": None if self.body is None else thaw_json(self.body),
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
    details: FrozenJsonObject
    http_status: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "details",
            FrozenJsonObject(cast(Mapping[str, object], self.details)),
        )

    @classmethod
    def create(
        cls,
        source: ErrorSource,
        code: str,
        message: str,
        details: Mapping[str, JsonValue] | None = None,
        http_status: int | None = None,
    ) -> CliError:
        return cls(
            source,
            code,
            message,
            freeze_json_object({} if details is None else details),
            http_status,
        )

    def as_json(self) -> JsonObject:
        return {
            "source": self.source.value,
            "code": self.code,
            "message": self.message,
            "details": thaw_json(self.details),
            "http_status": self.http_status,
        }


@dataclass(frozen=True, slots=True)
class CliResult:
    status: str
    command: ParsedCommand | None
    exchanges: tuple[HttpExchangeTrace, ...]
    result: FrozenJsonValue | None
    error: CliError | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "exchanges", tuple(self.exchanges))
        if self.result is not None:
            object.__setattr__(self, "result", freeze_json(self.result))

    @classmethod
    def ok(
        cls,
        command: ParsedCommand,
        exchanges: tuple[HttpExchangeTrace, ...],
        result: JsonValue | FrozenJsonValue | None,
    ) -> CliResult:
        return cls(
            "ok",
            command,
            tuple(exchanges),
            None if result is None else freeze_json(result),
            None,
        )

    @classmethod
    def failed(
        cls,
        command: ParsedCommand | None,
        exchanges: tuple[HttpExchangeTrace, ...],
        error: CliError,
    ) -> CliResult:
        return cls("error", command, tuple(exchanges), None, error)

    def as_json(self) -> JsonObject:
        return {
            "status": self.status,
            "command": None if self.command is None else self.command.as_json(),
            "exchanges": [exchange.as_json() for exchange in self.exchanges],
            "result": None if self.result is None else thaw_json(self.result),
            "error": None if self.error is None else self.error.as_json(),
        }


class ExecutionLedger:
    """Single mutable owner of one command's in-flight exchange history."""

    __slots__ = ("_exchanges",)

    def __init__(self) -> None:
        self._exchanges: list[HttpExchangeTrace] = []

    def record(self, exchange: HttpExchangeTrace) -> None:
        self._exchanges.append(exchange)

    def snapshot(self) -> tuple[HttpExchangeTrace, ...]:
        return tuple(self._exchanges)

    def since(self, index: int) -> tuple[HttpExchangeTrace, ...]:
        return tuple(self._exchanges[index:])

    def __len__(self) -> int:
        return len(self._exchanges)
