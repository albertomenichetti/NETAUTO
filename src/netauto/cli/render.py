"""Canonical JSON and deterministic plain-text CLI rendering."""

import json
from collections.abc import Callable
from types import MappingProxyType

from netauto.cli.model import (
    CliResult,
    CommandSpec,
    FrozenJsonArray,
    FrozenJsonObject,
    FrozenJsonValue,
    JsonValue,
    thaw_json,
)
from netauto.cli.registry import COMMAND_REGISTRY

type Renderer = Callable[[CliResult, CommandSpec, JsonValue | None], str]


def render_json(result: CliResult) -> str:
    """Render one deterministic compact process result line."""

    return (
        json.dumps(
            result.as_json(), ensure_ascii=False, separators=(",", ":"), sort_keys=False
        )
        + "\n"
    )


def _json_text(value: JsonValue | FrozenJsonValue | None) -> str:
    ordinary = (
        thaw_json(value)
        if isinstance(value, FrozenJsonObject | FrozenJsonArray)
        else value
    )
    return json.dumps(ordinary, ensure_ascii=False, indent=2, sort_keys=True)


def _error(result: CliResult) -> str:
    error = result.error
    if error is None:
        return "status: error\ncode: cli_internal_error\n"
    lines = [
        "status: error",
        f"source: {error.source.value}",
        f"code: {error.code}",
        f"message: {error.message}",
        f"http_status: {error.http_status if error.http_status is not None else '-'}",
        "details:",
        _json_text(error.details),
    ]
    return "\n".join(lines) + "\n"


def _response_metadata(result: CliResult, spec: CommandSpec) -> list[str]:
    for exchange in result.exchanges:
        response = exchange.response
        if response is None or response.status_code != spec.expected_status:
            continue
        if spec.expected_status != 204 and response.body != result.result:
            continue
        lines = [f"http_status: {response.status_code}"]
        locations = response.headers.get("location", ())
        if locations:
            lines.append(f"location: {locations[0]}")
        return lines
    return [f"http_status: {spec.expected_status}"]


def _resource(
    result: CliResult, spec: CommandSpec, presentation: JsonValue | None
) -> str:
    command = result.command
    lines = ["status: ok", *_response_metadata(result, spec)]
    if command is not None:
        lines.append(f"command: {command.key.resource} {command.key.operation}")
        if command.selector is not None:
            lines.append(f"selector: {command.selector}")
    lines.append("result:")
    lines.append(_json_text(presentation))
    return "\n".join(lines) + "\n"


def _page(result: CliResult, spec: CommandSpec, presentation: JsonValue | None) -> str:
    text = _resource(result, spec, presentation).rstrip("\n")
    page = presentation if isinstance(presentation, dict) else None
    cursor = None if page is None else page.get("next_cursor")
    suffix = "end" if cursor is None else str(cursor)
    return f"{text}\npage_cursor: {suffix}\n"


def _no_content(
    result: CliResult, spec: CommandSpec, presentation: JsonValue | None
) -> str:
    del presentation
    command = result.command
    target = "-" if command is None or command.selector is None else command.selector
    return (
        "\n".join(
            [
                "status: ok",
                *_response_metadata(result, spec),
                f"target: {target}",
            ]
        )
        + "\n"
    )


def _strategy(renderer_key: str) -> Renderer:
    if renderer_key == "no-content":
        return _no_content
    if renderer_key.endswith(".page") or renderer_key.endswith("-page"):
        return _page
    return _resource


RENDERER_REGISTRY = MappingProxyType(
    {
        renderer_key: _strategy(renderer_key)
        for renderer_key in {spec.renderer_key for spec in COMMAND_REGISTRY.values()}
    }
)


def render_formatted(
    result: CliResult,
    spec: CommandSpec | None = None,
    presentation: JsonValue | None = None,
) -> str:
    """Render one complete interactive result without style-dependent meaning."""

    if result.error is not None:
        return _error(result)
    if result.command is not None and result.command.key.resource == "local":
        return "status: ok\nresult:\n" + _json_text(presentation) + "\n"
    if spec is None:
        return "status: ok\nresult:\n" + _json_text(presentation) + "\n"
    renderer = RENDERER_REGISTRY[spec.renderer_key]
    return renderer(result, spec, presentation)
