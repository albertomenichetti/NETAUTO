"""Permanent evidence for residual finding S05-RF-01."""

import ast
import asyncio
import json
import sys
from pathlib import Path
from typing import NoReturn, cast

import httpx
import pytest

import netauto.cli.main as main_module
import netauto.cli.parser as parser_module
import netauto.cli.transport as transport_module
from netauto.cli.model import CliResult, FrozenJsonValue, HttpResponseTrace
from netauto.cli.render import render_json

DATATYPE_ID = "11111111-1111-1111-1111-111111111111"
SENTINEL = "residual-secret-internal-text"
ROOT = Path(__file__).parents[1]


def _raise_runtime(*args: object, **kwargs: object) -> NoReturn:
    del args, kwargs
    raise RuntimeError(SENTINEL)


def _assert_internal(result: CliResult, exchange_count: int) -> None:
    assert result.status == "error"
    assert result.result is None
    assert result.error is not None
    assert result.error.source == "local"
    assert result.error.code == "cli_internal_error"
    assert result.error.message == "The CLI could not safely complete the command."
    assert len(result.exchanges) == exchange_count
    assert SENTINEL not in render_json(result)


def _datatype_response(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/api/v1/core/datatypes":
        return httpx.Response(
            200,
            headers={"Content-Type": "application/json", "X-Observed": "yes"},
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
        headers={"Content-Type": "application/json", "X-Observed": "yes"},
        json={
            "id": DATATYPE_ID,
            "namespace": "core",
            "name": "string",
            "description": None,
            "default_version": 1,
        },
    )


def test_unexpected_parse_before_safe_command_is_bounded_by_run_and_main(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(parser_module, "normalize_endpoint_root", _raise_runtime)
    argv = ["-n", "http://example.test", "datatype", "list"]

    result, exit_code = main_module.run(argv)
    assert exit_code == 1
    _assert_internal(result, 0)
    assert result.command is None

    monkeypatch.setattr(sys, "argv", ["netauto", *argv])
    with pytest.raises(SystemExit) as caught:
        main_module.main()
    captured = capsys.readouterr()
    assert caught.value.code == 1
    assert captured.err == ""
    assert captured.out.count("\n") == 1
    assert SENTINEL not in captured.out
    output = json.loads(captured.out)
    assert output["status"] == "error"
    assert output["result"] is None
    assert output["command"] is None
    assert output["exchanges"] == []
    assert output["error"]["code"] == "cli_internal_error"


def test_unexpected_parse_after_safe_command_preserves_exact_typed_intent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        parser_module, "_validate_relationship_definition_shape", _raise_runtime
    )
    result, exit_code = main_module.run(
        ["-n", "http://example.test", "datatype", "list", "limit=2"]
    )

    assert exit_code == 1
    _assert_internal(result, 0)
    assert result.command is not None
    assert result.command.as_json() == {
        "resource": "datatype",
        "operation": "list",
        "selector": None,
        "parameters": {"limit": 2},
    }


def test_expected_parse_failure_preserves_its_finite_local_classification() -> None:
    result, exit_code = main_module.run(
        ["-n", "http://example.test", "datatype", "get"]
    )

    assert exit_code == 1
    assert result.error is not None
    assert result.error.source == "local"
    assert result.error.code == "cli_missing_selector"
    assert result.exchanges == ()


@pytest.mark.parametrize(
    "failure",
    [asyncio.CancelledError, KeyboardInterrupt, SystemExit],
)
def test_parse_base_exceptions_propagate_unchanged(
    monkeypatch: pytest.MonkeyPatch,
    failure: type[BaseException],
) -> None:
    def fail(*args: object, **kwargs: object) -> NoReturn:
        del args, kwargs
        raise failure()

    monkeypatch.setattr(parser_module, "normalize_endpoint_root", fail)
    with pytest.raises(failure):
        main_module.run(["-n", "http://example.test", "datatype", "list"])


def test_pre_send_cookie_failure_has_no_exchange_or_send(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sends = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal sends
        sends += 1
        return _datatype_response(request)

    monkeypatch.setattr(httpx.Cookies, "clear", _raise_runtime)
    result, exit_code = main_module.run(
        ["-n", "http://example.test", "datatype", "list"],
        http_transport=httpx.MockTransport(handler),
    )

    assert exit_code == 1
    _assert_internal(result, 0)
    assert sends == 0


@pytest.mark.parametrize(
    ("failure", "source", "code"),
    [
        (httpx.ConnectError, "transport", "cli_transport_error"),
        (RuntimeError, "local", "cli_internal_error"),
    ],
)
def test_send_failure_is_exactly_one_response_null_attempt(
    failure: type[Exception],
    source: str,
    code: str,
) -> None:
    sends = 0

    def handler(request: httpx.Request) -> NoReturn:
        nonlocal sends
        sends += 1
        if issubclass(failure, httpx.TransportError):
            raise httpx.ConnectError(SENTINEL, request=request)
        raise RuntimeError(SENTINEL)

    result, exit_code = main_module.run(
        ["-n", "http://example.test", "datatype", "list"],
        http_transport=httpx.MockTransport(handler),
    )

    assert exit_code == 1
    assert result.error is not None
    assert result.error.source == source
    assert result.error.code == code
    assert sends == 1
    assert len(result.exchanges) == 1
    assert result.exchanges[0].response is None
    assert result.exchanges[0].elapsed_ms >= 0
    assert SENTINEL not in render_json(result)


def test_response_trace_failure_preserves_observed_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(transport_module, "_response_trace", _raise_runtime)
    result, exit_code = main_module.run(
        ["-n", "http://example.test", "datatype", "list"],
        http_transport=httpx.MockTransport(_datatype_response),
    )

    assert exit_code == 1
    _assert_internal(result, 1)
    response = result.exchanges[0].response
    assert response is not None
    assert response.status_code == 200
    assert response.headers["x-observed"] == ("yes",)
    assert response.body_format == "json"
    assert response.body == {
        "items": [_datatype_response_payload()],
        "next_cursor": None,
    }


def _datatype_response_payload() -> dict[str, object]:
    return {
        "id": DATATYPE_ID,
        "namespace": "core",
        "name": "string",
        "description": None,
        "default_version": 1,
    }


def test_post_send_cookie_failure_preserves_observed_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_clear = httpx.Cookies.clear
    calls = 0

    def fail_second_clear(cookies: httpx.Cookies) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError(SENTINEL)
        original_clear(cookies)

    monkeypatch.setattr(httpx.Cookies, "clear", fail_second_clear)
    result, exit_code = main_module.run(
        ["-n", "http://example.test", "datatype", "list"],
        http_transport=httpx.MockTransport(_datatype_response),
    )

    assert exit_code == 1
    _assert_internal(result, 1)
    assert calls == 2
    assert result.exchanges[0].response is not None


@pytest.mark.parametrize(
    ("failure_stage", "primary_has_response"),
    [("send", False), ("capture", True), ("cleanup", True)],
)
def test_selector_then_primary_failure_preserves_exact_attempt_order_and_intent(
    monkeypatch: pytest.MonkeyPatch,
    failure_stage: str,
    primary_has_response: bool,
) -> None:
    requests: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request.url.path)
        if failure_stage == "send" and len(requests) == 2:
            raise RuntimeError(SENTINEL)
        return _datatype_response(request)

    if failure_stage == "capture":

        def fail_primary_trace(response: httpx.Response) -> HttpResponseTrace:
            if response.request.url.path.endswith(DATATYPE_ID):
                raise RuntimeError(SENTINEL)
            return HttpResponseTrace(
                response.status_code,
                {},
                "json",
                cast(FrozenJsonValue, response.json()),
            )

        monkeypatch.setattr(transport_module, "_response_trace", fail_primary_trace)
    if failure_stage == "cleanup":
        original_clear = httpx.Cookies.clear
        clear_calls = 0

        def fail_primary_cleanup(cookies: httpx.Cookies) -> None:
            nonlocal clear_calls
            clear_calls += 1
            if clear_calls == 4:
                raise RuntimeError(SENTINEL)
            original_clear(cookies)

        monkeypatch.setattr(httpx.Cookies, "clear", fail_primary_cleanup)

    result, exit_code = main_module.run(
        ["-n", "http://example.test", "datatype", "get", "core.string"],
        http_transport=httpx.MockTransport(handler),
    )

    assert exit_code == 1
    _assert_internal(result, 2)
    assert requests == [
        "/api/v1/core/datatypes",
        f"/api/v1/core/datatypes/{DATATYPE_ID}",
    ]
    assert [exchange.request.url for exchange in result.exchanges] == [
        "http://example.test/api/v1/core/datatypes",
        f"http://example.test/api/v1/core/datatypes/{DATATYPE_ID}",
    ]
    assert result.exchanges[0].response is not None
    assert (result.exchanges[1].response is not None) is primary_has_response
    assert result.command is not None
    assert result.command.as_json() == {
        "resource": "datatype",
        "operation": "get",
        "selector": "core.string",
        "parameters": {},
    }


@pytest.mark.parametrize(
    "failure",
    [asyncio.CancelledError, KeyboardInterrupt, SystemExit],
)
def test_transport_base_exceptions_propagate_unchanged(
    failure: type[BaseException],
) -> None:
    def handler(request: httpx.Request) -> NoReturn:
        del request
        raise failure()

    with pytest.raises(failure):
        main_module.run(
            ["-n", "http://example.test", "datatype", "list"],
            http_transport=httpx.MockTransport(handler),
        )


def test_residual_static_boundary_is_finite_and_ledger_owned() -> None:
    main_tree = ast.parse((ROOT / "src/netauto/cli/main.py").read_text())
    main_catches = {
        ast.unparse(handler.type)
        for handler in (
            node for node in ast.walk(main_tree) if isinstance(node, ast.ExceptHandler)
        )
        if handler.type is not None
    }
    assert "Exception" in main_catches
    assert "BaseException" not in main_catches

    parser_tree = ast.parse((ROOT / "src/netauto/cli/parser.py").read_text())
    assert (
        sum(
            isinstance(node, ast.FunctionDef) and node.name == "parse_process"
            for node in ast.walk(parser_tree)
        )
        == 1
    )

    transport_source = (ROOT / "src/netauto/cli/transport.py").read_text()
    transport_tree = ast.parse(transport_source)
    transport_catches = {
        ast.unparse(handler.type)
        for handler in (
            node
            for node in ast.walk(transport_tree)
            if isinstance(node, ast.ExceptHandler)
        )
        if handler.type is not None
    }
    assert "httpx.TransportError" in transport_catches
    assert "Exception" not in transport_catches
    assert "BaseException" not in transport_catches
    assert ".record(" not in transport_source
    assert "retry" not in transport_source.lower()
