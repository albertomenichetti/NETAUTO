"""Permanent regression evidence for the four M2-S05 review findings."""

import asyncio
import json
import sys
from collections.abc import MutableMapping, MutableSequence
from typing import NoReturn, cast

import httpx
import pytest

from netauto.cli import execution
from netauto.cli.main import main, run
from netauto.cli.model import (
    CliError,
    CliResult,
    CommandKey,
    ErrorSource,
    FrozenJsonValue,
    HttpExchangeTrace,
    HttpRequestTrace,
    HttpResponseTrace,
    JsonValue,
    ParsedCommand,
)
from netauto.cli.render import render_json
from netauto.cli.transport import HttpTransport

DATATYPE_ID = "11111111-1111-1111-1111-111111111111"
SENTINEL = "sentinel-secret-internal-text"


def _selector_response(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/api/v1/core/datatypes":
        return httpx.Response(
            200,
            headers={"Content-Type": "application/json"},
            json={
                "items": [
                    {
                        "id": DATATYPE_ID,
                        "namespace": "core",
                        "name": "string",
                        "description": None,
                        "default_version": 1,
                    }
                ],
                "next_cursor": None,
            },
        )
    return httpx.Response(
        200,
        headers={"Content-Type": "application/json"},
        json={
            "id": DATATYPE_ID,
            "namespace": "core",
            "name": "string",
            "description": None,
            "default_version": 1,
        },
    )


def _raise_internal(*args: object, **kwargs: object) -> NoReturn:
    del args, kwargs
    raise RuntimeError(SENTINEL)


def _assert_internal_result(result: CliResult, expected_exchanges: int) -> None:
    assert result.status == "error"
    assert result.result is None
    assert result.error is not None
    assert result.error.source == "local"
    assert result.error.code == "cli_internal_error"
    assert len(result.exchanges) == expected_exchanges
    assert SENTINEL not in render_json(result)


def test_internal_failure_before_any_attempt_has_empty_truthful_trace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(execution, "_request_plan", _raise_internal)
    result, exit_code = run(
        ["-n", "http://example.test", "datatype", "list"],
        http_transport=httpx.MockTransport(
            lambda request: pytest.fail(f"unexpected request: {request.url}")
        ),
    )
    assert exit_code == 1
    _assert_internal_result(result, 0)


def test_internal_failure_after_selector_preserves_selector_exchange(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(execution, "_request_plan", _raise_internal)
    result, exit_code = run(
        ["-n", "http://example.test", "datatype", "get", "core.string"],
        http_transport=httpx.MockTransport(_selector_response),
    )
    assert exit_code == 1
    _assert_internal_result(result, 1)
    assert result.exchanges[0].request.url.endswith("/api/v1/core/datatypes")


def test_internal_failure_after_primary_response_preserves_ordered_trace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(execution, "interpret_response", _raise_internal)
    result, exit_code = run(
        ["-n", "http://example.test", "datatype", "get", "core.string"],
        http_transport=httpx.MockTransport(_selector_response),
    )
    assert exit_code == 1
    _assert_internal_result(result, 2)
    assert [exchange.request.url for exchange in result.exchanges] == [
        "http://example.test/api/v1/core/datatypes",
        f"http://example.test/api/v1/core/datatypes/{DATATYPE_ID}",
    ]


def test_internal_failure_during_cleanup_preserves_primary_exchange(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_exit = HttpTransport.__aexit__

    async def failing_exit(
        self: HttpTransport,
        exception_type: object,
        exception: object,
        traceback: object,
    ) -> None:
        await original_exit(self, exception_type, exception, traceback)
        raise RuntimeError(SENTINEL)

    monkeypatch.setattr(HttpTransport, "__aexit__", failing_exit)
    result, exit_code = run(
        ["-n", "http://example.test", "datatype", "list"],
        http_transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                headers={"Content-Type": "application/json"},
                json={"items": [], "next_cursor": None},
            )
        ),
    )
    assert exit_code == 1
    _assert_internal_result(result, 1)
    assert result.exchanges[0].response is not None


def test_internal_exception_text_never_reaches_process_channels(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    async def failing_execute(*args: object, **kwargs: object) -> CliResult:
        del args, kwargs
        raise RuntimeError(SENTINEL)

    monkeypatch.setattr("netauto.cli.main.execute", failing_execute)
    monkeypatch.setattr(
        sys,
        "argv",
        ["netauto", "-n", "http://example.test", "datatype", "list"],
    )
    with pytest.raises(SystemExit) as caught:
        main()
    captured = capsys.readouterr()
    assert caught.value.code == 1
    assert captured.err == ""
    assert captured.out.count("\n") == 1
    assert SENTINEL not in captured.out
    assert json.loads(captured.out)["error"]["code"] == "cli_internal_error"


@pytest.mark.parametrize(
    "failure",
    [asyncio.CancelledError, KeyboardInterrupt, SystemExit],
)
def test_base_exception_and_cancellation_are_not_normalized(
    monkeypatch: pytest.MonkeyPatch,
    failure: type[BaseException],
) -> None:
    async def failing_execute(*args: object, **kwargs: object) -> CliResult:
        del args, kwargs
        raise failure()

    monkeypatch.setattr("netauto.cli.main.execute", failing_execute)
    with pytest.raises(failure):
        run(["-n", "http://example.test", "datatype", "list"])


def _nested_payload(label: str) -> dict[str, JsonValue]:
    return {"label": label, "nested": {"items": [{"value": 1}, [2, 3]]}}


def test_recursive_snapshots_detach_every_original_constructor_input() -> None:
    command_input = _nested_payload("command")
    error_input = _nested_payload("error")
    request_input = _nested_payload("request")
    response_input = _nested_payload("response")
    result_input = _nested_payload("result")

    command = ParsedCommand.create(
        CommandKey("datatype", "list"),
        None,
        command_input,
    )
    error = CliError.create(
        ErrorSource.LOCAL,
        "cli_internal_error",
        "bounded",
        error_input,
    )
    request = HttpRequestTrace(
        "POST",
        "http://example.test/api/v1/core/datatypes",
        {"limit": ("1",)},
        {"accept": ("application/json",)},
        cast(FrozenJsonValue, request_input),
    )
    response = HttpResponseTrace(
        200,
        {"content-type": ("application/json",)},
        "json",
        cast(FrozenJsonValue, response_input),
    )
    exchange = HttpExchangeTrace(request, response, 1)
    success = CliResult.ok(
        command,
        (exchange,),
        result_input,
    )
    failure = CliResult.failed(command, (exchange,), error)

    for original in (
        command_input,
        error_input,
        request_input,
        response_input,
        result_input,
    ):
        original["label"] = "mutated"
        cast(dict[str, JsonValue], original["nested"])["new"] = True

    assert command.as_json()["parameters"] == _nested_payload("command")
    assert error.as_json()["details"] == _nested_payload("error")
    assert request.as_json()["body"] == _nested_payload("request")
    assert response.as_json()["body"] == _nested_payload("response")
    assert success.as_json()["result"] == _nested_payload("result")
    assert failure.as_json()["command"] == command.as_json()
    assert failure.as_json()["exchanges"] == [exchange.as_json()]
    assert failure.as_json()["error"] == error.as_json()


def test_every_public_nested_json_view_is_recursively_immutable() -> None:
    payload = _nested_payload("immutable")
    parameters: dict[str, JsonValue] = {"payload": payload}
    command = ParsedCommand.create(CommandKey("datatype", "list"), None, parameters)
    error = CliError.create(
        ErrorSource.LOCAL,
        "cli_internal_error",
        "bounded",
        parameters,
    )
    request = HttpRequestTrace(
        "POST",
        "http://example.test/api/v1/core/datatypes",
        {},
        {},
        cast(FrozenJsonValue, payload),
    )
    response = HttpResponseTrace(200, {}, "json", cast(FrozenJsonValue, payload))
    result = CliResult.ok(command, (HttpExchangeTrace(request, response, 1),), payload)

    public_values = (
        command.parameters["payload"],
        error.details["payload"],
        request.body,
        response.body,
        result.result,
    )
    for public_value in public_values:
        mapping = cast(MutableMapping[str, object], public_value)
        with pytest.raises(TypeError):
            mapping["new"] = "forbidden"
        nested = cast(MutableMapping[str, object], mapping["nested"])
        items = cast(MutableSequence[object], nested["items"])
        with pytest.raises((AttributeError, TypeError)):
            items.append("forbidden")


def test_as_json_mutation_is_detached_and_rendering_is_byte_stable() -> None:
    parameters: dict[str, JsonValue] = {"payload": _nested_payload("command")}
    command = ParsedCommand.create(CommandKey("datatype", "list"), None, parameters)
    request = HttpRequestTrace(
        "POST",
        "http://example.test/api/v1/core/datatypes",
        {"limit": ("1",)},
        {"accept": ("application/json",)},
        cast(FrozenJsonValue, _nested_payload("request")),
    )
    response = HttpResponseTrace(
        200,
        {"content-type": ("application/json",)},
        "json",
        cast(FrozenJsonValue, _nested_payload("response")),
    )
    result = CliResult.ok(
        command,
        (HttpExchangeTrace(request, response, 1),),
        _nested_payload("result"),
    )
    expected = result.as_json()
    rendered = render_json(result)

    detached = result.as_json()
    cast(dict[str, object], detached["result"])["label"] = "mutated"
    command_json = cast(dict[str, object], detached["command"])
    cast(dict[str, object], command_json["parameters"])["new"] = True
    exchanges = cast(list[dict[str, object]], detached["exchanges"])
    request_json = cast(dict[str, object], exchanges[0]["request"])
    cast(dict[str, object], request_json["body"])["new"] = True

    assert result.as_json() == expected
    assert render_json(result) == rendered
