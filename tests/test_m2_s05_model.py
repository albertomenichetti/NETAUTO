"""Pure execution-ledger lifecycle evidence for M2-S05."""

import pytest

from netauto.cli.model import (
    ExecutionLedger,
    HttpRequestTrace,
    HttpResponseTrace,
)


def _request(url: str) -> HttpRequestTrace:
    return HttpRequestTrace("GET", url, {}, {}, None)


def _response(status_code: int) -> HttpResponseTrace:
    return HttpResponseTrace(status_code, {}, "none", None)


def test_execution_ledger_updates_one_provisional_attempt_without_duplication() -> None:
    ledger = ExecutionLedger()
    attempt = ledger.begin(_request("http://example.test/first"))

    provisional = ledger.snapshot()
    assert provisional == ledger.snapshot()
    assert len(provisional) == len(ledger) == 1
    assert provisional[0].response is None
    assert provisional[0].elapsed_ms == 0

    ledger.observe_response(attempt, _response(200), 1)
    assert len(ledger.snapshot()) == 1
    assert ledger.snapshot()[0].response == _response(200)

    ledger.refine_response(attempt, _response(201), 2)
    finalized = ledger.finalize(attempt, 3)
    assert finalized == ledger.snapshot()[0]
    assert finalized.response == _response(201)
    assert finalized.elapsed_ms == 3
    assert ledger.snapshot() == ledger.snapshot()

    with pytest.raises(RuntimeError, match="already finalized"):
        ledger.finalize(attempt, 4)
    with pytest.raises(RuntimeError, match="already recorded"):
        ledger.observe_response(attempt, _response(202), 4)
    assert len(ledger.snapshot()) == 1


def test_execution_ledger_preserves_begin_order_and_rejects_malformed_use() -> None:
    ledger = ExecutionLedger()
    first = ledger.begin(_request("http://example.test/first"))
    second = ledger.begin(_request("http://example.test/second"))

    assert [exchange.request.url for exchange in ledger.snapshot()] == [
        "http://example.test/first",
        "http://example.test/second",
    ]
    ledger.observe_response(second, _response(204), 0)
    ledger.finalize(second, 0)
    ledger.finalize(first, 1)
    assert all(exchange.elapsed_ms >= 0 for exchange in ledger.snapshot())

    foreign = ExecutionLedger().begin(_request("http://example.test/foreign"))
    with pytest.raises(RuntimeError, match="different execution ledger"):
        ledger.finalize(foreign, 0)
    third = ledger.begin(_request("http://example.test/third"))
    ledger.observe_response(third, _response(200), 0)
    with pytest.raises(ValueError, match="non-negative integer"):
        ledger.refine_response(third, _response(201), -1)
    ledger.finalize(third, 0)
    assert len(ledger.snapshot()) == 3
