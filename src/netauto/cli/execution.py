"""Registry-driven HTTP-only command execution pipeline."""

from typing import cast

import httpx
from pydantic import TypeAdapter, ValidationError

from netauto.cli.enrichment import enrich_formatted
from netauto.cli.model import (
    CliError,
    CliResult,
    CommandSpec,
    ErrorSource,
    ExecutionLedger,
    JsonValue,
    ParameterLocation,
    ParsedCommand,
    RequestPlan,
    thaw_json,
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
    return RequestPlan.create(spec.method, path, tuple(query), body), None, values


async def execute(
    endpoint_root: str,
    command: ParsedCommand,
    spec: CommandSpec,
    *,
    http_transport: httpx.AsyncBaseTransport | None = None,
    ledger: ExecutionLedger | None = None,
) -> CliResult:
    execution_ledger = ExecutionLedger() if ledger is None else ledger
    async with HttpTransport(
        endpoint_root,
        transport=http_transport,
        ledger=execution_ledger,
    ) as transport:
        result, _ = await execute_connected(
            transport,
            command,
            spec,
            ledger=execution_ledger,
            formatted=False,
        )
        return result


async def execute_connected(
    transport: HttpTransport,
    command: ParsedCommand,
    spec: CommandSpec,
    *,
    ledger: ExecutionLedger,
    formatted: bool,
) -> tuple[CliResult, JsonValue | None]:
    """Execute one command on a persistent session client with a fresh ledger."""

    transport.use_ledger(ledger)
    resolution = await resolve_selectors(transport, command, spec)
    if resolution.error is not None:
        return CliResult.failed(command, ledger.snapshot(), resolution.error), None
    plan, local_error, request_values = _request_plan(
        spec, resolution.selector, resolution.parameters
    )
    if local_error is not None:
        return CliResult.failed(command, ledger.snapshot(), local_error), None
    if plan is None:
        raise RuntimeError("request planner returned no plan")
    try:
        response, exchange = await transport.exchange(plan)
    except TransportFailure:
        return (
            CliResult.failed(
                command,
                ledger.snapshot(),
                CliError.create(
                    ErrorSource.TRANSPORT,
                    "cli_transport_error",
                    "The HTTP request could not be completed.",
                ),
            ),
            None,
        )
    outcome = interpret_response(
        response,
        exchange,
        expected_status=spec.expected_status,
        response_annotation=spec.response_annotation,
        location_template=spec.location_template,
        request_values=request_values,
    )
    if outcome.error is not None:
        return CliResult.failed(command, ledger.snapshot(), outcome.error), None
    result = CliResult.ok(command, ledger.snapshot(), outcome.result)
    if not formatted:
        return result, outcome.result
    enriched = await enrich_formatted(transport, command, outcome.result)
    if enriched.error is not None:
        return CliResult.failed(command, ledger.snapshot(), enriched.error), None
    # Enrichment may have appended exchanges after the primary result was created.
    final_result = CliResult.ok(
        command,
        ledger.snapshot(),
        None if result.result is None else thaw_json(result.result),
    )
    return final_result, enriched.presentation
