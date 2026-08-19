"""M2-VER-26 interactive Health and connection-transition evidence."""

from collections.abc import Callable

import httpx
import pytest

from netauto.cli.repl import ConnectionState, InteractiveSession

READY = {
    "app_status": {"status": "ok"},
    "db_status": {"status": "ok"},
    "execution_time_ms": 1,
}
DATATYPE_PAGE: dict[str, object] = {"items": [], "next_cursor": None}


def _response(
    request: httpx.Request,
    status: int,
    payload: object,
    *,
    content_type: str = "application/json",
) -> httpx.Response:
    return httpx.Response(
        status,
        headers={"Content-Type": content_type},
        json=payload,
        request=request,
    )


def _transport(
    handler: Callable[[httpx.Request], httpx.Response],
) -> httpx.MockTransport:
    return httpx.MockTransport(handler)


def _health_503(request: httpx.Request) -> httpx.Response:
    return _response(
        request,
        503,
        {
            "app_status": {"status": "ok"},
            "db_status": {"status": "error", "message": "unavailable"},
            "execution_time_ms": 2,
        },
    )


def _health_non_ready_200(request: httpx.Request) -> httpx.Response:
    return _response(
        request,
        200,
        {
            "app_status": {"status": "ok"},
            "db_status": {"status": "error", "message": "unavailable"},
            "execution_time_ms": 2,
        },
    )


def _health_invalid(request: httpx.Request) -> httpx.Response:
    return _response(request, 200, {"not": "health"})


def _health_wrong_content(request: httpx.Request) -> httpx.Response:
    return _response(request, 200, READY, content_type="text/plain")


def _health_redirect(request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        307,
        headers={"Location": "http://other.test/health/core"},
        request=request,
    )


def _health_null_message(request: httpx.Request) -> httpx.Response:
    return _response(
        request,
        200,
        {
            "app_status": {"status": "ok", "message": None},
            "db_status": {"status": "ok"},
            "execution_time_ms": 1,
        },
    )


@pytest.mark.asyncio
async def test_connect_uses_exact_health_get_and_adopts_only_ready_200() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return _response(request, 200, READY)

    session = InteractiveSession(http_transport=_transport(handler))
    outcome = await session.submit("/connect HTTPS://Example.TEST:8443/")
    assert outcome is not None and outcome.result.status == "ok"
    assert session.connection is ConnectionState.CONNECTED
    assert session.endpoint == "https://example.test:8443"
    assert [(request.method, request.url.path) for request in requests] == [
        ("GET", "/health/core")
    ]
    assert len(outcome.result.exchanges) == 1
    assert outcome.result.exchanges[0].request.url == (
        "https://example.test:8443/health/core"
    )
    await session.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response_factory",
    [
        _health_503,
        _health_non_ready_200,
        _health_invalid,
        _health_wrong_content,
        _health_redirect,
        _health_null_message,
    ],
)
async def test_connect_http_and_protocol_failures_remain_disconnected(
    response_factory: Callable[[httpx.Request], httpx.Response],
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return response_factory(request)

    session = InteractiveSession(http_transport=_transport(handler))
    outcome = await session.submit("/connect http://example.test")
    assert outcome is not None and outcome.result.status == "error"
    assert outcome.result.error is not None
    assert outcome.result.error.code == "cli_protocol_error"
    assert session.connection is ConnectionState.DISCONNECTED
    assert session.endpoint is None
    assert len(requests) == 1
    assert len(outcome.result.exchanges) == 1


@pytest.mark.asyncio
async def test_connect_transport_failure_is_traced_once_and_disconnected() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        del request
        raise httpx.ConnectError("controlled")

    session = InteractiveSession(http_transport=_transport(handler))
    outcome = await session.submit("/connect http://example.test")
    assert outcome is not None and outcome.result.error is not None
    assert outcome.result.error.source == "transport"
    assert session.connection is ConnectionState.DISCONNECTED
    assert len(outcome.result.exchanges) == 1
    assert outcome.result.exchanges[0].response is None


@pytest.mark.asyncio
async def test_failed_replacement_closes_old_before_new_endpoint_validation() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return _response(request, 200, READY)

    session = InteractiveSession(http_transport=_transport(handler))
    connected = await session.submit("/connect http://first.test")
    assert connected is not None and connected.result.status == "ok"
    old_transport = session.transport
    assert old_transport is not None and not old_transport.is_closed

    failed = await session.submit("/connect not-a-url")
    assert failed is not None and failed.result.error is not None
    assert failed.result.error.code == "cli_invalid_invocation"
    assert old_transport.is_closed
    assert session.transport is None
    assert session.endpoint is None
    assert session.connection is ConnectionState.DISCONNECTED


@pytest.mark.asyncio
async def test_disconnect_is_local_idempotent_and_closes_client() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return _response(request, 200, READY)

    session = InteractiveSession(http_transport=_transport(handler))
    await session.submit("/connect http://example.test")
    transport = session.transport
    first = await session.submit("/disconnect")
    second = await session.submit("/disconnect")
    assert first is not None and second is not None
    assert first.result.exchanges == second.result.exchanges == ()
    assert transport is not None and transport.is_closed
    assert session.connection is ConnectionState.DISCONNECTED
    assert len(requests) == 1


@pytest.mark.asyncio
async def test_status_disconnected_is_local_and_connected_revalidates_once() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return _response(request, 200, READY)

    session = InteractiveSession(http_transport=_transport(handler))
    local = await session.submit("/status")
    assert local is not None and local.result.status == "ok"
    assert local.result.exchanges == ()
    assert requests == []
    await session.submit("/connect http://example.test")
    requests.clear()
    connected = await session.submit("/status")
    assert connected is not None and connected.result.status == "ok"
    assert len(connected.result.exchanges) == 1
    assert [request.url.path for request in requests] == ["/health/core"]
    assert session.connection is ConnectionState.CONNECTED
    await session.close()


@pytest.mark.asyncio
async def test_status_failure_closes_and_disconnects() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return _response(request, 200, READY)
        return _response(request, 200, {"invalid": True})

    session = InteractiveSession(http_transport=_transport(handler))
    await session.submit("/connect http://example.test")
    transport = session.transport
    outcome = await session.submit("/status")
    assert outcome is not None and outcome.result.status == "error"
    assert session.connection is ConnectionState.DISCONNECTED
    assert transport is not None and transport.is_closed


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["remote", "protocol"])
async def test_business_remote_and_protocol_errors_preserve_connection(
    mode: str,
) -> None:
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        if request.url.path == "/health/core":
            return _response(request, 200, READY)
        if mode == "remote":
            return _response(
                request,
                404,
                {
                    "code": "resource_not_found",
                    "message": "The resource was not found.",
                    "details": {},
                },
            )
        return _response(request, 200, {"invalid": True})

    session = InteractiveSession(http_transport=_transport(handler))
    await session.submit("/connect http://example.test")
    outcome = await session.submit("datatype list")
    assert outcome is not None and outcome.result.error is not None
    assert outcome.result.error.source == mode
    assert session.connection is ConnectionState.CONNECTED
    assert paths == ["/health/core", "/api/v1/core/datatypes"]
    await session.close()


@pytest.mark.asyncio
async def test_business_transport_failure_disconnects_without_health_preflight() -> (
    None
):
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        if request.url.path == "/health/core":
            return _response(request, 200, READY)
        raise httpx.ReadError("controlled")

    session = InteractiveSession(http_transport=_transport(handler))
    await session.submit("/connect http://example.test")
    outcome = await session.submit("datatype list")
    assert outcome is not None and outcome.result.error is not None
    assert outcome.result.error.source == "transport"
    assert session.connection is ConnectionState.DISCONNECTED
    assert paths == ["/health/core", "/api/v1/core/datatypes"]


@pytest.mark.asyncio
async def test_selector_transport_failure_disconnects_before_primary_request() -> None:
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        if request.url.path == "/health/core":
            return _response(request, 200, READY)
        raise httpx.ReadError("controlled")

    session = InteractiveSession(http_transport=_transport(handler))
    await session.submit("/connect http://example.test")
    outcome = await session.submit("datatype get core.string")
    assert outcome is not None and outcome.result.error is not None
    assert outcome.result.error.source == "transport"
    assert session.connection is ConnectionState.DISCONNECTED
    assert paths == ["/health/core", "/api/v1/core/datatypes"]
    assert len(outcome.result.exchanges) == 1


@pytest.mark.asyncio
async def test_exit_closes_adopted_transport_and_requests_normal_exit() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return _response(request, 200, READY)

    session = InteractiveSession(http_transport=_transport(handler))
    await session.submit("/connect http://example.test")
    transport = session.transport
    outcome = await session.submit("/exit")
    assert outcome is not None and outcome.exit_requested
    assert transport is not None and transport.is_closed
    assert session.connection is ConnectionState.DISCONNECTED


@pytest.mark.asyncio
async def test_persistent_client_has_fresh_command_ledgers_without_trace_leakage() -> (
    None
):
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/health/core":
            return _response(request, 200, READY)
        return _response(request, 200, DATATYPE_PAGE)

    session = InteractiveSession(http_transport=_transport(handler))
    connected = await session.submit("/connect http://example.test")
    transport = session.transport
    first = await session.submit("datatype list")
    second = await session.submit("datatype list limit=2")
    assert connected is not None and first is not None and second is not None
    assert session.transport is transport
    assert len(connected.result.exchanges) == 1
    assert len(first.result.exchanges) == 1
    assert len(second.result.exchanges) == 1
    assert all(
        outcome.result.exchanges[0].request.url.endswith("/api/v1/core/datatypes")
        for outcome in (first, second)
    )
    assert len(requests) == 3
    await session.close()
