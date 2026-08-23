"""M2-VER-25 pure interactive state, local-command, and history evidence."""

import json

import httpx
import pytest

from netauto.cli.parser import parse_process, parse_remote_tokens
from netauto.cli.registry import COMMAND_REGISTRY
from netauto.cli.repl import (
    LOCAL_COMMAND_REGISTRY,
    ConnectionState,
    InteractiveSession,
    OutputMode,
    render_interactive,
)


def test_initial_state_and_exact_local_inventory_are_closed() -> None:
    session = InteractiveSession()
    assert session.connection is ConnectionState.DISCONNECTED
    assert session.output is OutputMode.FORMATTED
    assert session.endpoint is None
    assert session.history == []
    assert tuple(LOCAL_COMMAND_REGISTRY) == (
        "connect",
        "disconnect",
        "status",
        "output",
        "help",
        "history",
        "clear",
        "exit",
    )


def test_interactive_and_noninteractive_use_the_same_remote_parser() -> None:
    tokens = ["datatype", "list", "namespace=core", "limit=2"]
    interactive_command, interactive_spec = parse_remote_tokens(tokens)
    endpoint, process_command, process_spec = parse_process(
        ["-n", "http://example.test", *tokens]
    )
    assert endpoint == "http://example.test"
    assert interactive_command == process_command
    assert interactive_spec is process_spec
    assert interactive_spec is COMMAND_REGISTRY[interactive_command.key]


@pytest.mark.asyncio
async def test_blank_submission_has_no_result_or_history() -> None:
    session = InteractiveSession()
    assert await session.submit("") is None
    assert await session.submit("   \t") is None
    assert session.history == []


@pytest.mark.asyncio
async def test_remote_while_disconnected_is_local_and_has_no_exchange() -> None:
    session = InteractiveSession()
    outcome = await session.submit("datatype list")
    assert outcome is not None
    assert outcome.result.error is not None
    assert outcome.result.error.source == "local"
    assert outcome.result.error.code == "cli_not_connected"
    assert outcome.result.exchanges == ()
    assert session.connection is ConnectionState.DISCONNECTED


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("line", "code"),
    [
        ("/unknown", "cli_invalid_command"),
        ("/connect", "cli_invalid_invocation"),
        ("/disconnect extra", "cli_invalid_invocation"),
        ("/status extra", "cli_invalid_invocation"),
        ("/output json", "cli_invalid_parameter"),
        ("/help a b c", "cli_invalid_invocation"),
        ("/history extra", "cli_invalid_invocation"),
        ("/clear extra", "cli_invalid_invocation"),
        ("/exit extra", "cli_invalid_invocation"),
        ('/help "unterminated', "cli_invalid_invocation"),
    ],
)
async def test_local_spelling_arity_and_quoting_failures_are_bounded(
    line: str, code: str
) -> None:
    session = InteractiveSession()
    outcome = await session.submit(line)
    assert outcome is not None
    assert outcome.result.error is not None
    assert outcome.result.error.code == code
    assert outcome.result.exchanges == ()


@pytest.mark.asyncio
async def test_output_switch_applies_before_acknowledgement() -> None:
    session = InteractiveSession()
    json_outcome = await session.submit("/output JSON")
    assert json_outcome is not None
    assert session.output is OutputMode.JSON
    rendered_json = render_interactive(session, json_outcome)
    assert json.loads(rendered_json)["result"]["output"] == "JSON"

    formatted_outcome = await session.submit("/output FORMATTED")
    assert formatted_outcome is not None
    assert session.output is OutputMode.FORMATTED
    rendered_formatted = render_interactive(session, formatted_outcome)
    assert rendered_formatted.startswith("status: ok\n")
    assert '"output": "FORMATTED"' in rendered_formatted


@pytest.mark.asyncio
async def test_help_is_registry_derived_and_uses_no_http() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        raise AssertionError("help must not issue HTTP")

    session = InteractiveSession(http_transport=httpx.MockTransport(handler))
    overview = await session.submit("/help")
    resource = await session.submit("/help datatype")
    operation = await session.submit("/help datatype get-version")
    assert overview is not None and resource is not None and operation is not None
    overview_result = overview.result.as_json()["result"]
    resource_result = resource.result.as_json()["result"]
    operation_result = operation.result.as_json()["result"]
    assert isinstance(overview_result, dict)
    assert overview_result["local_commands"] == [
        spec.usage for spec in LOCAL_COMMAND_REGISTRY.values()
    ]
    assert isinstance(resource_result, dict)
    assert resource_result["operations"] == [
        spec.key.operation
        for spec in COMMAND_REGISTRY.values()
        if spec.key.resource == "datatype"
    ]
    assert isinstance(operation_result, dict)
    assert operation_result["http"] == {
        "method": "GET",
        "path": "/api/v1/core/datatypes/{datatype_id}/versions/{version}",
    }
    assert requests == []


@pytest.mark.asyncio
async def test_history_is_chronological_and_excludes_current_invocation() -> None:
    session = InteractiveSession()
    help_outcome = await session.submit("/help")
    assert help_outcome is not None
    assert session.history == []
    session.complete_line("/help")

    history_outcome = await session.submit("/history")
    assert history_outcome is not None
    result = history_outcome.result.as_json()["result"]
    assert result == {"entries": [{"number": 1, "line": "/help"}]}
    assert session.history == ["/help"]
    session.complete_line("/history")
    assert session.history == ["/help", "/history"]


@pytest.mark.asyncio
async def test_clear_preserves_connection_output_and_history() -> None:
    cleared: list[bool] = []
    session = InteractiveSession(clear_terminal=lambda: cleared.append(True))
    session.output = OutputMode.JSON
    session.complete_line("/output JSON")
    outcome = await session.submit("/clear")
    assert outcome is not None
    assert outcome.result.status == "ok"
    assert cleared == [True]
    assert session.connection is ConnectionState.DISCONNECTED
    assert session.output is OutputMode.JSON
    assert session.history == ["/output JSON"]


@pytest.mark.asyncio
async def test_local_json_identity_is_canonical_and_deterministic() -> None:
    session = InteractiveSession()
    outcome = await session.submit("/help datatype get")
    assert outcome is not None
    command = outcome.result.as_json()["command"]
    assert command == {
        "resource": "local",
        "operation": "help",
        "selector": "datatype",
        "parameters": {"arguments": ["get"]},
    }
    assert outcome.result.exchanges == ()


@pytest.mark.asyncio
async def test_ordinary_errors_do_not_terminate_session_and_exit_is_normal() -> None:
    session = InteractiveSession()
    first = await session.submit("/unknown")
    second = await session.submit("/status")
    exited = await session.submit("/exit")
    assert first is not None and first.result.status == "error"
    assert second is not None and second.result.status == "ok"
    assert exited is not None and exited.exit_requested
    assert session.connection is ConnectionState.DISCONNECTED
