"""Same-release success and canonical remote-error validation."""

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast

import httpx
from pydantic import TypeAdapter, ValidationError

from netauto.cli.model import (
    CliError,
    ErrorSource,
    HttpExchangeTrace,
    JsonValue,
    thaw_json,
)
from netauto.transport.http.errors import PUBLIC_STATUS_BY_CODE, BusinessErrorDTO

_LOCATION_TOKEN = re.compile(r"\{([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*)\}")


@dataclass(frozen=True, slots=True)
class ProtocolOutcome:
    result: JsonValue | None
    error: CliError | None


def _protocol_error(status: int) -> ProtocolOutcome:
    return ProtocolOutcome(
        None,
        CliError.create(
            ErrorSource.PROTOCOL,
            "cli_protocol_error",
            "The server response violates the same-release HTTP contract.",
            http_status=status,
        ),
    )


def _json_content_type(response: httpx.Response) -> bool:
    content_type = response.headers.get("content-type", "")
    return content_type.split(";", 1)[0].strip().lower() == "application/json"


def location_template_tokens(template: str) -> tuple[str, ...] | None:
    """Parse the closed Location-template DSL without Python format semantics."""

    tokens: list[str] = []
    cursor = 0
    for match in _LOCATION_TOKEN.finditer(template):
        literal = template[cursor : match.start()]
        if "{" in literal or "}" in literal:
            return None
        tokens.append(match.group(1))
        cursor = match.end()
    if "{" in template[cursor:] or "}" in template[cursor:]:
        return None
    return tuple(tokens)


def _lookup(value: JsonValue, path: str) -> JsonValue | None:
    current: JsonValue = value
    for segment in path.split("."):
        if not isinstance(current, dict) or segment not in current:
            return None
        current = current[segment]
    return current


def _location_scalar(value: JsonValue) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    return None


def materialize_location(
    template: str,
    result: JsonValue,
    request_values: Mapping[str, JsonValue],
) -> str | None:
    """Materialize one valid registry template or return non-materializable."""

    tokens = location_template_tokens(template)
    if tokens is None:
        return None
    rendered = template
    for token in dict.fromkeys(tokens):
        value = (
            request_values[token] if token in request_values else _lookup(result, token)
        )
        scalar = _location_scalar(value)
        if scalar is None:
            return None
        rendered = rendered.replace("{" + token + "}", scalar)
    return rendered


def interpret_response(
    response: httpx.Response,
    exchange: HttpExchangeTrace,
    *,
    expected_status: int,
    response_annotation: object | None,
    location_template: str | None = None,
    request_values: Mapping[str, JsonValue] | None = None,
) -> ProtocolOutcome:
    trace = exchange.response
    if trace is None:
        return _protocol_error(response.status_code)
    trace_body = None if trace.body is None else thaw_json(trace.body)
    status = response.status_code
    if status != expected_status:
        if 200 <= status < 400 or not _json_content_type(response):
            return _protocol_error(status)
        if trace.body_format != "json":
            return _protocol_error(status)
        try:
            remote = BusinessErrorDTO.model_validate(trace_body)
        except ValidationError:
            return _protocol_error(status)
        if PUBLIC_STATUS_BY_CODE.get(remote.code) != status:
            return _protocol_error(status)
        return ProtocolOutcome(
            None,
            CliError.create(
                ErrorSource.REMOTE,
                remote.code,
                remote.message,
                cast(Mapping[str, JsonValue], remote.details),
                status,
            ),
        )

    if expected_status == 204:
        if response.content or response_annotation is not None:
            return _protocol_error(status)
        return ProtocolOutcome(None, None)

    if (
        response_annotation is None
        or trace.body_format != "json"
        or not _json_content_type(response)
    ):
        return _protocol_error(status)
    try:
        adapter: TypeAdapter[object] = TypeAdapter(response_annotation)
        validated: object = adapter.validate_python(trace_body)
        canonical = adapter.dump_python(validated, mode="json", exclude_unset=True)
    except ValidationError:
        return _protocol_error(status)
    if canonical != trace_body:
        return _protocol_error(status)

    result = trace_body
    if location_template is not None:
        locations = response.headers.get_list("location")
        expected = materialize_location(location_template, result, request_values or {})
        if len(locations) != 1 or expected is None or locations[0] != expected:
            return _protocol_error(status)
    return ProtocolOutcome(result, None)
