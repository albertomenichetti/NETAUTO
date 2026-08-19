"""One-attempt HTTPX transport with transparent exchange tracing."""

import json
import time
from collections.abc import Iterable
from importlib.metadata import version
from types import MappingProxyType
from typing import cast

import httpx

from netauto.cli.model import (
    ExecutionLedger,
    HttpExchangeTrace,
    HttpRequestTrace,
    HttpResponseTrace,
    JsonValue,
    RequestPlan,
    freeze_json,
    thaw_json,
)

TIMEOUT = httpx.Timeout(connect=5.0, pool=5.0, read=30.0, write=30.0)


class TransportFailure(Exception):
    """A request attempt that received no HTTP response."""

    def __init__(self, exchange: HttpExchangeTrace) -> None:
        self.exchange = exchange
        super().__init__("cli_transport_error")


def _group(items: Iterable[tuple[str, str]]) -> MappingProxyType[str, tuple[str, ...]]:
    grouped: dict[str, list[str]] = {}
    for name, value in items:
        grouped.setdefault(name.lower(), []).append(value)
    return MappingProxyType({name: tuple(values) for name, values in grouped.items()})


def _response_trace(response: httpx.Response) -> HttpResponseTrace:
    if not response.content:
        body_format = "none"
        body: JsonValue | None = None
    else:
        try:
            body = cast(JsonValue, response.json())
            body_format = "json"
        except ValueError:
            body = response.text
            body_format = "text"
    return HttpResponseTrace(
        response.status_code,
        _group(response.headers.multi_items()),
        body_format,
        None if body is None else freeze_json(body),
    )


def _response_observation(response: httpx.Response) -> HttpResponseTrace:
    """Capture a bounded immutable trace before later response processing."""

    content = bytes(response.content)
    if not content:
        body_format = "none"
        body: JsonValue | None = None
    else:
        try:
            body = cast(JsonValue, json.loads(content))
            body_format = "json"
        except ValueError, UnicodeError:
            try:
                body = content.decode(response.encoding or "utf-8")
            except LookupError, UnicodeError:
                body = content.decode("utf-8", errors="replace")
            body_format = "text"
    return HttpResponseTrace(
        response.status_code,
        _group(response.headers.multi_items()),
        body_format,
        None if body is None else freeze_json(body),
    )


def _elapsed_since(started: float) -> int:
    return max(0, int((time.monotonic() - started) * 1000))


class HttpTransport:
    """One endpoint-scoped client with command-scoped exchange ledgers."""

    def __init__(
        self,
        endpoint_root: str,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        ledger: ExecutionLedger | None = None,
    ) -> None:
        self._root = endpoint_root
        self._ledger = ExecutionLedger() if ledger is None else ledger
        self._client = httpx.AsyncClient(
            timeout=TIMEOUT,
            follow_redirects=False,
            headers={
                "Accept": "application/json",
                "User-Agent": f"netauto/{version('netauto')}",
            },
            transport=transport,
        )

    async def __aenter__(self) -> HttpTransport:
        return self

    async def __aexit__(
        self,
        exception_type: object,
        exception: object,
        traceback: object,
    ) -> None:
        await self.close()

    @property
    def endpoint_root(self) -> str:
        return self._root

    @property
    def is_closed(self) -> bool:
        return self._client.is_closed

    def use_ledger(self, ledger: ExecutionLedger) -> None:
        """Bind a fresh ledger before one session command begins."""

        self._ledger = ledger

    async def close(self) -> None:
        """Close the endpoint client; HTTPX close is idempotent."""

        await self._client.aclose()

    @property
    def exchange_count(self) -> int:
        return len(self._ledger)

    def exchanges_since(self, index: int) -> tuple[HttpExchangeTrace, ...]:
        return self._ledger.since(index)

    async def exchange(
        self, plan: RequestPlan
    ) -> tuple[httpx.Response, HttpExchangeTrace]:
        url = f"{self._root}{plan.path}"
        self._client.cookies.clear()
        if plan.body is None:
            request = self._client.build_request(plan.method, url, params=plan.query)
        else:
            request = self._client.build_request(
                plan.method, url, params=plan.query, json=thaw_json(plan.body)
            )
        request_trace = HttpRequestTrace(
            request.method,
            str(request.url.copy_with(query=None)),
            _group(request.url.params.multi_items()),
            _group(request.headers.multi_items()),
            plan.body,
        )
        started = time.monotonic()
        attempt = self._ledger.begin(request_trace)
        try:
            try:
                response = await self._client.send(request, follow_redirects=False)
            except httpx.TransportError:
                exchange = self._ledger.finalize(attempt, _elapsed_since(started))
                raise TransportFailure(exchange) from None
            observation = _response_observation(response)
            self._ledger.observe_response(attempt, observation, _elapsed_since(started))
            response_trace = _response_trace(response)
            self._ledger.refine_response(
                attempt, response_trace, _elapsed_since(started)
            )
        finally:
            try:
                self._client.cookies.clear()
            finally:
                if not self._ledger.is_finalized(attempt):
                    self._ledger.finalize(attempt, _elapsed_since(started))
        exchange = self._ledger.snapshot()[-1]
        return response, exchange
