"""Deterministic top-level and nested human-selector resolution."""

from dataclasses import dataclass
from typing import cast
from uuid import UUID

from netauto.cli.model import (
    CliError,
    CommandSpec,
    ErrorSource,
    HttpExchangeTrace,
    JsonValue,
    ParsedCommand,
    RequestPlan,
    ResolvedIdentity,
    SelectorKind,
    thaw_json,
)
from netauto.cli.protocol import interpret_response
from netauto.cli.transport import HttpTransport, TransportFailure
from netauto.transport.http.datatypes import DataTypePageDto
from netauto.transport.http.objects import ObjectPageDto
from netauto.transport.http.objecttemplates import ObjectTemplatePageDto


@dataclass(frozen=True, slots=True)
class ResolutionOutcome:
    selector: str | None
    parameters: dict[str, JsonValue]
    exchanges: tuple[HttpExchangeTrace, ...]
    identities: tuple[ResolvedIdentity, ...]
    error: CliError | None


@dataclass(frozen=True, slots=True)
class _Target:
    kind: SelectorKind
    value: object
    path: tuple[str | int, ...]


def _display(kind: SelectorKind) -> str:
    return {
        SelectorKind.DATATYPE: "DataType",
        SelectorKind.OBJECT_TEMPLATE: "ObjectTemplate",
        SelectorKind.OBJECT: "Object",
        SelectorKind.RELATIONSHIP_DEFINITION: "RelationshipDefinition",
        SelectorKind.RELATIONSHIP: "Relationship",
        SelectorKind.RESOLUTION: "RelationshipResolution",
    }[kind]


def _selector_error(
    kind: SelectorKind,
    code: str,
    value: object,
    *,
    matches: list[str] | None = None,
) -> CliError:
    qualifier = {
        "cli_selector_invalid": "is invalid",
        "cli_selector_not_found": "was not found",
        "cli_selector_ambiguous": "is ambiguous",
    }[code]
    details: dict[str, JsonValue] = {
        "selector_kind": kind.value,
        "input": str(value)[:256],
    }
    if matches is not None:
        details["matched_ids"] = cast(JsonValue, list(matches[:2]))
    return CliError.create(
        ErrorSource.SELECTOR,
        code,
        f"The {_display(kind)} selector {qualifier}.",
        details,
    )


def _walk(
    value: object,
    pattern: tuple[str, ...],
    path: tuple[str | int, ...],
    kind: SelectorKind,
) -> list[_Target]:
    if not pattern:
        return [_Target(kind, value, path)]
    segment, remaining = pattern[0], pattern[1:]
    if segment == "*":
        if not isinstance(value, list):
            return [_Target(kind, value, path)]
        items = cast(list[object], value)
        targets: list[_Target] = []
        for index, item in enumerate(items):
            targets.extend(_walk(item, remaining, (*path, index), kind))
        return targets
    if not isinstance(value, dict) or segment not in value:
        return []
    values = cast(dict[str, object], value)
    return _walk(values[segment], remaining, (*path, segment), kind)


def _targets(
    command: ParsedCommand,
    spec: CommandSpec,
    parameters: dict[str, JsonValue],
) -> list[_Target]:
    targets: list[_Target] = []
    if spec.selector_kind is not None:
        targets.append(_Target(spec.selector_kind, command.selector, ()))
    for parameter in spec.parameters:
        if parameter.name not in parameters:
            continue
        value = parameters[parameter.name]
        if parameter.selector_kind is not None:
            targets.append(_Target(parameter.selector_kind, value, (parameter.name,)))
        for nested in parameter.nested_selectors:
            targets.extend(
                _walk(
                    value,
                    nested.path,
                    (parameter.name,),
                    nested.kind,
                )
            )
    return targets


def _replace(
    root: dict[str, JsonValue], path: tuple[str | int, ...], value: str
) -> None:
    current: object = root
    for segment in path[:-1]:
        if isinstance(segment, int) and isinstance(current, list):
            current = cast(list[object], current)[segment]
        elif isinstance(segment, str) and isinstance(current, dict):
            current = cast(dict[str, object], current)[segment]
        else:
            raise RuntimeError("invalid static selector traversal")
    final = path[-1]
    if isinstance(final, int) and isinstance(current, list):
        cast(list[object], current)[final] = value
    elif isinstance(final, str) and isinstance(current, dict):
        cast(dict[str, object], current)[final] = value
    else:
        raise RuntimeError("invalid static selector target")


def _identity_label(spec: CommandSpec, target: _Target) -> str:
    if not target.path:
        if spec.selector_parameter is None:
            raise RuntimeError("selector registry identity has no parameter name")
        return spec.selector_parameter
    label = ""
    for segment in target.path:
        if isinstance(segment, int):
            label += f"[{segment}]"
        else:
            label += ("." if label else "") + segment
    return label


async def _lookup(
    transport: HttpTransport,
    kind: SelectorKind,
    value: str,
) -> tuple[str | None, HttpExchangeTrace | None, CliError | None]:
    if kind in {
        SelectorKind.RELATIONSHIP_DEFINITION,
        SelectorKind.RELATIONSHIP,
        SelectorKind.RESOLUTION,
    }:
        try:
            return str(UUID(value)), None, None
        except ValueError:
            return None, None, _selector_error(kind, "cli_selector_invalid", value)
    try:
        return str(UUID(value)), None, None
    except ValueError:
        pass

    if kind in {SelectorKind.DATATYPE, SelectorKind.OBJECT_TEMPLATE}:
        namespace, dot, name = value.rpartition(".")
        if not dot or not namespace or not name:
            return None, None, _selector_error(kind, "cli_selector_invalid", value)
        if kind is SelectorKind.DATATYPE:
            path = "/api/v1/core/datatypes"
            annotation: object = DataTypePageDto
        else:
            path = "/api/v1/core/object-templates"
            annotation = ObjectTemplatePageDto
        query = (("namespace", namespace), ("name", name), ("limit", "2"))
    else:
        if not value or len(value) > 255:
            return None, None, _selector_error(kind, "cli_selector_invalid", value)
        path = "/api/v1/core/objects"
        annotation = ObjectPageDto
        query = (("canonical_name", value), ("limit", "2"))

    try:
        response, exchange = await transport.exchange(
            RequestPlan.create("GET", path, query, None)
        )
    except TransportFailure as failure:
        return (
            None,
            failure.exchange,
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
        response_annotation=annotation,
    )
    if outcome.error is not None:
        return None, exchange, outcome.error
    body = cast(dict[str, JsonValue], outcome.result)
    items = cast(list[JsonValue], body["items"])
    next_cursor = body["next_cursor"]
    ids = [str(cast(dict[str, JsonValue], item)["id"]) for item in items[:2]]
    if not items:
        return None, exchange, _selector_error(kind, "cli_selector_not_found", value)
    if len(items) != 1 or next_cursor is not None:
        return (
            None,
            exchange,
            _selector_error(
                kind,
                "cli_selector_ambiguous",
                value,
                matches=ids,
            ),
        )
    return ids[0], exchange, None


async def resolve_selectors(
    transport: HttpTransport,
    command: ParsedCommand,
    spec: CommandSpec,
) -> ResolutionOutcome:
    mutable_parameters = thaw_json(command.parameters)
    if not isinstance(mutable_parameters, dict):
        raise RuntimeError("parsed command parameters are not an object")
    parameters = mutable_parameters
    resolved_selector: str | None = None
    first_exchange = transport.exchange_count
    cache: dict[tuple[SelectorKind, str], str] = {}
    identities: list[ResolvedIdentity] = []
    for target in _targets(command, spec, parameters):
        if not isinstance(target.value, str):
            return ResolutionOutcome(
                resolved_selector,
                parameters,
                transport.exchanges_since(first_exchange),
                tuple(identities),
                _selector_error(target.kind, "cli_selector_invalid", target.value),
            )
        key = (target.kind, target.value)
        resolved = cache.get(key)
        if resolved is None:
            resolved, _, error = await _lookup(transport, target.kind, target.value)
            if error is not None:
                return ResolutionOutcome(
                    resolved_selector,
                    parameters,
                    transport.exchanges_since(first_exchange),
                    tuple(identities),
                    error,
                )
            if resolved is None:
                raise RuntimeError("selector resolver returned no outcome")
            cache[key] = resolved
        if not target.path:
            resolved_selector = resolved
        else:
            _replace(parameters, target.path, resolved)
        identities.append(ResolvedIdentity(_identity_label(spec, target), resolved))
    return ResolutionOutcome(
        resolved_selector,
        parameters,
        transport.exchanges_since(first_exchange),
        tuple(identities),
        None,
    )
