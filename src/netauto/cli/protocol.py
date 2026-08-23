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


def _lookup(value: JsonValue, path: str) -> str | None:
    current: JsonValue = value
    for segment in path.split("."):
        if not isinstance(current, dict) or segment not in current:
            return None
        current = current[segment]
    return str(current) if isinstance(current, str | int) else None


def _expected_location(
    template: str,
    result: JsonValue,
    request_values: Mapping[str, JsonValue],
) -> str | None:
    values: dict[str, str] = {}
    for token in re.findall(r"\{([^{}]+)\}", template):
        request_value = request_values.get(token)
        if isinstance(request_value, str | int):
            values[token] = str(request_value)
            continue
        result_value = _lookup(result, token)
        if result_value is None:
            return None
        values[token] = str(result_value)
    return template.format_map(values)


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
        expected = _expected_location(location_template, result, request_values or {})
        if len(locations) != 1 or expected is None or locations[0] != expected:
            return _protocol_error(status)
    return ProtocolOutcome(result, None)
