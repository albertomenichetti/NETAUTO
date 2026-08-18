"""Registry-driven HTTP-only command execution pipeline."""

from typing import cast

import httpx
from pydantic import TypeAdapter, ValidationError

from netauto.cli.model import (
    CliError,
    CliResult,
    CommandSpec,
    ErrorSource,
    JsonValue,
    ParameterLocation,
    ParsedCommand,
    RequestPlan,
)
from netauto.cli.protocol import interpret_response
from netauto.cli.selectors import resolve_selectors
from netauto.cli.transport import HttpTransport, TransportFailure


def _wire_string(value: JsonValue) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str | int | float):
        return str(value)
    raise ValueError("query_or_path_scalar_required")


def _request_plan(
    spec: CommandSpec,
    resolved_selector: str | None,
    parameters: dict[str, JsonValue],
) -> tuple[RequestPlan | None, CliError | None, dict[str, JsonValue]]:
    values = dict(parameters)
    if spec.selector_parameter is not None and resolved_selector is not None:
        values[spec.selector_parameter] = resolved_selector
    path = spec.path_template
    query: list[tuple[str, str]] = []
    body_candidate: dict[str, JsonValue] = {}
    try:
        for parameter in spec.parameters:
            if parameter.name not in parameters:
                continue
            value = parameters[parameter.name]
            if parameter.location is ParameterLocation.PATH:
                path = path.replace("{" + parameter.name + "}", _wire_string(value))
            elif parameter.location is ParameterLocation.QUERY:
                query.append((parameter.name, _wire_string(value)))
            else:
                body_candidate[parameter.name] = value
        if spec.selector_parameter is not None:
            if resolved_selector is None:
                raise ValueError("resolved_selector_required")
            path = path.replace("{" + spec.selector_parameter + "}", resolved_selector)
    except ValueError:
        return (
            None,
            CliError.create(
                ErrorSource.LOCAL,
                "cli_invalid_parameter",
                "A command parameter is invalid.",
            ),
            values,
        )

    body: JsonValue | None = None
    if spec.request_annotation is not None:
        try:
            adapter: TypeAdapter[object] = TypeAdapter(spec.request_annotation)
            validated: object = adapter.validate_python(body_candidate)
            body = cast(
                JsonValue,
                adapter.dump_python(validated, mode="json", exclude_unset=True),
            )
        except ValidationError:
            return (
                None,
                CliError.create(
                    ErrorSource.LOCAL,
                    "cli_invalid_parameter",
                    "A command parameter is invalid.",
                ),
                values,
            )
    elif body_candidate:
        raise RuntimeError("static registry body metadata mismatch")
    if "{" in path or "}" in path:
        raise RuntimeError("static registry path metadata mismatch")
    return RequestPlan(spec.method, path, tuple(query), body), None, values


async def execute(
    endpoint_root: str,
    command: ParsedCommand,
    spec: CommandSpec,
    *,
    http_transport: httpx.AsyncBaseTransport | None = None,
) -> CliResult:
    async with HttpTransport(endpoint_root, transport=http_transport) as transport:
        resolution = await resolve_selectors(transport, command, spec)
        exchanges = list(resolution.exchanges)
        if resolution.error is not None:
            return CliResult.failed(command, tuple(exchanges), resolution.error)
        plan, local_error, request_values = _request_plan(
            spec, resolution.selector, resolution.parameters
        )
        if local_error is not None:
            return CliResult.failed(command, tuple(exchanges), local_error)
        if plan is None:
            raise RuntimeError("request planner returned no plan")
        try:
            response, exchange = await transport.exchange(plan)
        except TransportFailure as failure:
            exchanges.append(failure.exchange)
            return CliResult.failed(
                command,
                tuple(exchanges),
                CliError.create(
                    ErrorSource.TRANSPORT,
                    "cli_transport_error",
                    "The HTTP request could not be completed.",
                ),
            )
        exchanges.append(exchange)
        outcome = interpret_response(
            response,
            exchange,
            expected_status=spec.expected_status,
            response_annotation=spec.response_annotation,
            location_template=spec.location_template,
            request_values=request_values,
        )
        if outcome.error is not None:
            return CliResult.failed(command, tuple(exchanges), outcome.error)
        return CliResult.ok(command, tuple(exchanges), outcome.result)
