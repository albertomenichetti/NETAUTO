"""Exact strict HTTP and OpenAPI contract for Core Health."""

import asyncio
from typing import cast

import httpx
import pytest
from fastapi.testclient import TestClient

import netauto.application.health as health_module
from netauto.application.health import (
    ComponentHealth,
    CoreHealthResult,
    CoreHealthService,
    DatabaseProbeTimedOut,
    DatabaseProbeUnavailable,
    HealthStatus,
)
from netauto.entrypoints.http import build_app
from netauto.settings import Settings

RUNTIME_DATABASE_URL = "postgresql+psycopg://runtime@example/runtime"


class FakeHealthService:
    def __init__(
        self,
        result: CoreHealthResult | None = None,
        error: BaseException | None = None,
    ) -> None:
        self.result = result
        self.error = error
        self.calls = 0

    async def check(self) -> CoreHealthResult:
        self.calls += 1
        if self.error is not None:
            raise self.error
        assert self.result is not None
        return self.result


def result(db: ComponentHealth) -> CoreHealthResult:
    return CoreHealthResult(
        app_status=ComponentHealth(HealthStatus.OK),
        db_status=db,
        execution_time_ms=7,
    )


def client_for(service: object) -> TestClient:
    app = build_app(Settings(database_url=RUNTIME_DATABASE_URL))
    app.state.core_health_service = service
    return TestClient(app, raise_server_exceptions=False)


class RaisingProbe:
    def __init__(self, error: BaseException | None = None) -> None:
        self.error = error
        self.calls = 0

    async def check(self) -> None:
        self.calls += 1
        if self.error is not None:
            raise self.error


def test_health_healthy_response_is_exact_and_non_cacheable() -> None:
    service = FakeHealthService(result(ComponentHealth(HealthStatus.OK)))

    response = cast(
        httpx.Response,
        client_for(service).get(  # pyright: ignore[reportUnknownMemberType]
            "/health/core"
        ),
    )

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {
        "app_status": {"status": "ok"},
        "db_status": {"status": "ok"},
        "execution_time_ms": 7,
    }
    assert service.calls == 1


@pytest.mark.parametrize(
    "message",
    ["database readiness check failed", "database readiness check timed out"],
)
def test_health_unready_response_is_exact_safe_and_non_cacheable(
    message: str,
) -> None:
    service = FakeHealthService(result(ComponentHealth(HealthStatus.ERROR, message)))

    response = cast(
        httpx.Response,
        client_for(service).get(  # pyright: ignore[reportUnknownMemberType]
            "/health/core"
        ),
    )

    assert response.status_code == 503
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {
        "app_status": {"status": "ok"},
        "db_status": {"status": "error", "message": message},
        "execution_time_ms": 7,
    }
    assert RUNTIME_DATABASE_URL not in response.text


@pytest.mark.parametrize(
    ("url", "body"),
    [
        ("/health/core?unknown=1", None),
        ("/health/core?unknown=1&unknown=2", None),
        ("/health/core", b"{}"),
    ],
)
def test_health_invalid_request_is_canonical_400_without_probe(
    url: str, body: bytes | None
) -> None:
    service = FakeHealthService(result(ComponentHealth(HealthStatus.OK)))
    response = cast(
        httpx.Response,
        client_for(service).request(  # pyright: ignore[reportUnknownMemberType]
            "GET", url, content=body
        ),
    )

    assert response.status_code == 400
    assert response.json() == {
        "code": "invalid_request",
        "message": (
            "This command does not accept a request body."
            if body is not None
            else "The request contains unknown or repeated query parameters."
        ),
        "details": {},
    }
    assert service.calls == 0


def test_health_unexpected_service_failure_uses_safe_canonical_500() -> None:
    service = FakeHealthService(error=RuntimeError("sensitive DSN and SQL"))

    response = cast(
        httpx.Response,
        client_for(service).get(  # pyright: ignore[reportUnknownMemberType]
            "/health/core"
        ),
    )

    assert response.status_code == 500
    assert response.json() == {
        "code": "internal_error",
        "message": "An unexpected internal failure occurred.",
        "details": {},
    }
    assert "sensitive" not in response.text
    assert service.calls == 1


def test_health_inner_timeout_is_canonical_safe_500() -> None:
    raw_message = "unexpected-inner-timeout-sentinel"
    probe = RaisingProbe(TimeoutError(raw_message))

    response = cast(
        httpx.Response,
        client_for(CoreHealthService(probe)).get(  # pyright: ignore[reportUnknownMemberType]
            "/health/core"
        ),
    )

    assert response.status_code == 500
    assert response.json() == {
        "code": "internal_error",
        "message": "An unexpected internal failure occurred.",
        "details": {},
    }
    assert raw_message not in response.text
    assert probe.calls == 1


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (DatabaseProbeTimedOut(), "database readiness check timed out"),
        (DatabaseProbeUnavailable(), "database readiness check failed"),
    ],
)
def test_health_owned_probe_failures_are_exact_503(
    error: BaseException, message: str
) -> None:
    probe = RaisingProbe(error)

    response = cast(
        httpx.Response,
        client_for(CoreHealthService(probe)).get(  # pyright: ignore[reportUnknownMemberType]
            "/health/core"
        ),
    )

    body = response.json()
    assert response.status_code == 503
    assert response.headers["cache-control"] == "no-store"
    assert body["app_status"] == {"status": "ok"}
    assert body["db_status"] == {"status": "error", "message": message}
    assert type(body["execution_time_ms"]) is int
    assert probe.calls == 1


def test_health_owned_outer_timeout_is_exact_503(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started = asyncio.Event()

    class BlockingProbe:
        async def check(self) -> None:
            started.set()
            await asyncio.Event().wait()

    monkeypatch.setattr(health_module, "CORE_DATABASE_HEALTH_TIMEOUT_SECONDS", 0.01)

    response = cast(
        httpx.Response,
        client_for(CoreHealthService(BlockingProbe())).get(  # pyright: ignore[reportUnknownMemberType]
            "/health/core"
        ),
    )

    assert response.status_code == 503
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["db_status"] == {
        "status": "error",
        "message": "database readiness check timed out",
    }
    assert started.is_set()


def test_health_openapi_uses_one_dto_for_200_and_503() -> None:
    app = build_app(Settings(database_url=RUNTIME_DATABASE_URL))
    paths = cast(dict[str, object], app.openapi()["paths"])
    assert "/health/core" in paths
    operation = cast(
        dict[str, object], cast(dict[str, object], paths["/health/core"])["get"]
    )
    responses = cast(dict[str, object], operation["responses"])

    def schema_ref(status: str) -> object:
        response = cast(dict[str, object], responses[status])
        content = cast(dict[str, object], response["content"])
        media = cast(dict[str, object], content["application/json"])
        return media["schema"]

    assert schema_ref("200") == {"$ref": "#/components/schemas/CoreHealthDTO"}
    assert schema_ref("503") == {"$ref": "#/components/schemas/CoreHealthDTO"}


def test_health_is_the_only_operational_route() -> None:
    app = build_app(Settings(database_url=RUNTIME_DATABASE_URL))
    public_operations = {
        (method.upper(), path)
        for path, methods in app.openapi()["paths"].items()
        for method in methods
        if method in {"get", "post", "delete", "put", "patch"}
    }
    operational = {
        item for item in public_operations if not item[1].startswith("/api/v1/core")
    }
    assert operational == {("GET", "/health/core")}
    assert ("GET", "/health") not in public_operations
