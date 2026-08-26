"""M3-VER-14..16 ObjectTemplate parent tri-state evidence."""

import json
from collections.abc import AsyncIterator, Callable
from dataclasses import replace
from typing import cast

import httpx
import pytest
from sqlalchemy import Engine

from netauto.cli import execution as cli_execution
from netauto.cli.execution import execute
from netauto.cli.model import CommandKey, ParsedCommand
from netauto.cli.parser import ParseFailure, parse_process
from netauto.cli.registry import COMMAND_REGISTRY
from netauto.cli.repl import InteractiveSession
from netauto.cli.selectors import resolve_selectors
from netauto.cli.transport import HttpTransport
from netauto.entrypoints.http import build_app
from netauto.settings import Settings

PARENT_ID = "11111111-1111-1111-1111-111111111111"
READY = {
    "app_status": {"status": "ok"},
    "db_status": {"status": "ok"},
    "execution_time_ms": 1,
}


@pytest.fixture
async def m3_s01_client(
    migrated_database_engine: Engine, test_database_url: str
) -> AsyncIterator[httpx.AsyncClient]:
    del migrated_database_engine
    app = build_app(Settings(database_url=test_database_url))
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            yield client


async def _create_template(
    client: httpx.AsyncClient,
    name: str,
    *,
    parent_template_id: str | None = None,
    publish: bool = False,
) -> str:
    body: dict[str, object] = {
        "namespace": "m3s01",
        "name": name,
        "abstract": parent_template_id is None,
    }
    if parent_template_id is not None:
        body["parent_template_id"] = parent_template_id
    created = await client.post("/api/v1/core/object-templates", json=body)
    assert created.status_code == 201, created.text
    template_id = cast(str, created.json()["object_template"]["id"])
    if publish:
        published = await client.post(
            f"/api/v1/core/object-templates/{template_id}/versions/1/publish",
            params={"expected_revision": 1},
        )
        assert published.status_code == 200, published.text
    return template_id


def _ids(response: httpx.Response) -> set[str]:
    assert response.status_code == 200, response.text
    return {cast(str, item["id"]) for item in response.json()["items"]}


@pytest.mark.api
@pytest.mark.postgresql
async def test_m3_ver_14_http_parent_tristate_and_public_surface(
    m3_s01_client: httpx.AsyncClient,
) -> None:
    parent_id = await _create_template(m3_s01_client, "parent", publish=True)
    other_root_id = await _create_template(m3_s01_client, "other_root")
    child_id = await _create_template(
        m3_s01_client, "child", parent_template_id=parent_id
    )

    omitted = await m3_s01_client.get(
        "/api/v1/core/object-templates", params={"namespace": "m3s01"}
    )
    exact_parent = await m3_s01_client.get(
        "/api/v1/core/object-templates",
        params={"namespace": "m3s01", "parent_template_id": parent_id},
    )
    roots = await m3_s01_client.get(
        "/api/v1/core/object-templates",
        params={"namespace": "m3s01", "parent_template_id": "null"},
    )

    assert _ids(omitted) == {parent_id, other_root_id, child_id}
    assert _ids(exact_parent) == {child_id}
    assert _ids(roots) == {parent_id, other_root_id}
    assert all("parent_filter_set" not in item for item in roots.json()["items"])

    openapi_response = await m3_s01_client.get("/openapi.json")
    assert openapi_response.status_code == 200
    openapi = openapi_response.json()
    parameters = openapi["paths"]["/api/v1/core/object-templates"]["get"]["parameters"]
    parameter_names = {parameter["name"] for parameter in parameters}
    assert "parent_template_id" in parameter_names
    assert "parent_filter_set" not in parameter_names
    assert "parent_filter_set" not in json.dumps(openapi, sort_keys=True)


@pytest.mark.api
@pytest.mark.postgresql
async def test_m3_ver_14_invalid_parent_carriers_are_invalid_request(
    m3_s01_client: httpx.AsyncClient,
) -> None:
    for carrier in (
        "",
        "NULL",
        "None",
        "root",
        "ROOT",
        "not-a-uuid",
        " null",
        "null ",
    ):
        response = await m3_s01_client.get(
            "/api/v1/core/object-templates",
            params={"parent_template_id": carrier},
        )
        assert response.status_code == 400, (carrier, response.text)
        assert response.json()["code"] == "invalid_request"

    repeated = await m3_s01_client.get(
        "/api/v1/core/object-templates",
        params=[("parent_template_id", "null"), ("parent_template_id", "null")],
    )
    assert repeated.status_code == 400
    assert repeated.json()["code"] == "invalid_request"

    internal_name = await m3_s01_client.get(
        "/api/v1/core/object-templates", params={"parent_filter_set": "true"}
    )
    assert internal_name.status_code == 400
    assert internal_name.json()["code"] == "invalid_request"


@pytest.mark.api
@pytest.mark.postgresql
async def test_m3_ver_16_parent_cursor_identity_and_limit_compatibility(
    m3_s01_client: httpx.AsyncClient,
) -> None:
    parent_a = await _create_template(m3_s01_client, "root_a", publish=True)
    parent_b = await _create_template(m3_s01_client, "root_b")
    await _create_template(m3_s01_client, "root_c")
    await _create_template(m3_s01_client, "child_a_1", parent_template_id=parent_a)
    await _create_template(m3_s01_client, "child_a_2", parent_template_id=parent_a)

    omitted_page = await m3_s01_client.get(
        "/api/v1/core/object-templates",
        params={"namespace": "m3s01", "limit": 1},
    )
    root_page = await m3_s01_client.get(
        "/api/v1/core/object-templates",
        params={
            "namespace": "m3s01",
            "parent_template_id": "null",
            "limit": 1,
        },
    )
    exact_page = await m3_s01_client.get(
        "/api/v1/core/object-templates",
        params={
            "namespace": "m3s01",
            "parent_template_id": parent_a,
            "limit": 1,
        },
    )
    omitted_cursor = cast(str, omitted_page.json()["next_cursor"])
    root_cursor = cast(str, root_page.json()["next_cursor"])
    exact_cursor = cast(str, exact_page.json()["next_cursor"])
    assert omitted_cursor and root_cursor and exact_cursor

    root_continuation = await m3_s01_client.get(
        "/api/v1/core/object-templates",
        params={
            "namespace": "m3s01",
            "parent_template_id": "null",
            "cursor": root_cursor,
            "limit": 2,
        },
    )
    assert root_continuation.status_code == 200, root_continuation.text
    assert len(root_continuation.json()["items"]) == 2
    assert all(
        item["parent_template_id"] is None for item in root_continuation.json()["items"]
    )

    exact_continuation = await m3_s01_client.get(
        "/api/v1/core/object-templates",
        params={
            "namespace": "m3s01",
            "parent_template_id": parent_a,
            "cursor": exact_cursor,
            "limit": 2,
        },
    )
    assert exact_continuation.status_code == 200, exact_continuation.text

    incompatible_queries = (
        {"namespace": "m3s01", "parent_template_id": "null", "cursor": omitted_cursor},
        {"namespace": "m3s01", "cursor": root_cursor},
        {"namespace": "m3s01", "parent_template_id": parent_b, "cursor": exact_cursor},
        {"namespace": "m3s01", "parent_template_id": parent_a, "cursor": root_cursor},
        {"namespace": "m3s01", "parent_template_id": "null", "cursor": exact_cursor},
    )
    for params in incompatible_queries:
        response = await m3_s01_client.get(
            "/api/v1/core/object-templates", params=params
        )
        assert response.status_code == 400, response.text
        assert response.json()["code"] == "invalid_cursor"


def _mock(handler: Callable[[httpx.Request], httpx.Response]) -> httpx.MockTransport:
    return httpx.MockTransport(handler)


def _page(request: httpx.Request, *, with_parent: bool = False) -> httpx.Response:
    items: list[dict[str, object]] = []
    if with_parent:
        items.append(
            {
                "id": PARENT_ID,
                "namespace": "infra",
                "name": "parent",
                "description": None,
                "abstract": True,
                "parent_template_id": None,
                "default_version": 1,
            }
        )
    return httpx.Response(
        200,
        headers={"Content-Type": "application/json"},
        json={"items": items, "next_cursor": None},
        request=request,
    )


def _query_handler(
    expected_query: list[tuple[str, str]], requests: list[httpx.Request]
) -> Callable[[httpx.Request], httpx.Response]:
    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.url.path == "/api/v1/core/object-templates"
        assert request.url.params.multi_items() == expected_query
        return _page(request)

    return handler


def test_m3_ver_15_registry_and_parser_preserve_three_intent_states() -> None:
    key = CommandKey("object-template", "list")
    spec = COMMAND_REGISTRY[key]
    parent = next(
        parameter
        for parameter in spec.parameters
        if parameter.name == "parent_template_id"
    )
    assert parent.kind == "string"
    assert parent.location == "query"
    assert parent.selector_kind == "object-template"
    assert parent.nullable is True
    assert [
        (candidate.key, parameter.name)
        for candidate in COMMAND_REGISTRY.values()
        for parameter in candidate.parameters
        if parameter.selector_kind is not None and parameter.nullable
    ] == [(key, "parent_template_id")]
    assert all(
        parameter.name != "parent_filter_set"
        for candidate in COMMAND_REGISTRY.values()
        for parameter in candidate.parameters
    )

    _, omitted, _ = parse_process(
        ["-n", "http://example.test", "object-template", "list"]
    )
    _, explicit_null, _ = parse_process(
        [
            "-n",
            "http://example.test",
            "object-template",
            "list",
            "parent_template_id=null",
        ]
    )
    assert "parent_template_id" not in omitted.parameters
    assert explicit_null.parameters["parent_template_id"] is None
    assert explicit_null.as_json()["parameters"] == {"parent_template_id": None}

    with pytest.raises(ParseFailure) as caught:
        parse_process(
            [
                "-n",
                "http://example.test",
                "object",
                "list",
                "template_id=null",
            ]
        )
    assert caught.value.error.code == "cli_invalid_parameter"


@pytest.mark.asyncio
async def test_m3_ver_15_generic_nullable_direct_selector_rule() -> None:
    original = COMMAND_REGISTRY[CommandKey("object-template", "list")]
    parent = next(
        parameter
        for parameter in original.parameters
        if parameter.name == "parent_template_id"
    )
    nullable_spec = replace(
        original,
        parameters=(replace(parent, name="generic_nullable_selector"),),
    )
    nullable_command = ParsedCommand.create(
        original.key, None, {"generic_nullable_selector": None}
    )
    nonnullable_spec = replace(
        nullable_spec,
        parameters=(replace(nullable_spec.parameters[0], nullable=False),),
    )

    async with HttpTransport(
        "http://example.test",
        transport=_mock(lambda request: pytest.fail(f"unexpected request: {request}")),
    ) as transport:
        nullable = await resolve_selectors(transport, nullable_command, nullable_spec)
        nonnullable = await resolve_selectors(
            transport, nullable_command, nonnullable_spec
        )

    assert nullable.error is None
    assert nullable.parameters == {"generic_nullable_selector": None}
    assert nullable.exchanges == ()
    assert nonnullable.error is not None
    assert nonnullable.error.source == "local"
    assert nonnullable.error.code == "cli_invalid_parameter"
    assert nonnullable.exchanges == ()


@pytest.mark.asyncio
async def test_m3_ver_15_noninteractive_omitted_uuid_and_null_carriers() -> None:
    cases: tuple[tuple[list[str], list[tuple[str, str]]], ...] = (
        ([], []),
        ([f"parent_template_id={PARENT_ID}"], [("parent_template_id", PARENT_ID)]),
        (["parent_template_id=null"], [("parent_template_id", "null")]),
    )
    for arguments, expected_query in cases:
        requests: list[httpx.Request] = []

        _, command, spec = parse_process(
            [
                "-n",
                "http://example.test",
                "object-template",
                "list",
                *arguments,
            ]
        )
        result = await execute(
            "http://example.test",
            command,
            spec,
            http_transport=_mock(_query_handler(expected_query, requests)),
        )
        assert result.status == "ok"
        assert len(requests) == 1
        assert len(result.exchanges) == 1
        assert result.exchanges[0].request.query == {
            key: (value,) for key, value in expected_query
        }


@pytest.mark.asyncio
async def test_m3_ver_15_human_selector_uses_one_bounded_discovery() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if len(requests) == 1:
            assert request.url.params.multi_items() == [
                ("namespace", "infra"),
                ("name", "parent"),
                ("limit", "2"),
            ]
            return _page(request, with_parent=True)
        assert request.url.params.multi_items() == [("parent_template_id", PARENT_ID)]
        return _page(request)

    _, command, spec = parse_process(
        [
            "-n",
            "http://example.test",
            "object-template",
            "list",
            "parent_template_id=infra.parent",
        ]
    )
    result = await execute(
        "http://example.test", command, spec, http_transport=_mock(handler)
    )
    assert result.status == "ok"
    assert len(requests) == 2
    assert len(result.exchanges) == 2
    assert result.exchanges[-1].request.query == {"parent_template_id": (PARENT_ID,)}


@pytest.mark.asyncio
async def test_m3_ver_15_nullable_body_and_path_none_are_location_aware() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == f"/api/v1/core/datatypes/{PARENT_ID}/set-description"
        assert json.loads(request.content) == {"description": None}
        return httpx.Response(
            200,
            headers={"Content-Type": "application/json"},
            json={
                "id": PARENT_ID,
                "namespace": "core",
                "name": "example",
                "description": None,
                "default_version": None,
            },
            request=request,
        )

    _, command, spec = parse_process(
        [
            "-n",
            "http://example.test",
            "datatype",
            "set-description",
            PARENT_ID,
            "description=null",
        ]
    )
    result = await execute(
        "http://example.test", command, spec, http_transport=_mock(handler)
    )
    assert result.status == "ok"
    assert result.exchanges[0].request.body == {"description": None}

    path_spec = COMMAND_REGISTRY[CommandKey("datatype", "get-version")]
    path_command = ParsedCommand.create(path_spec.key, PARENT_ID, {"version": None})
    path_result = await execute(
        "http://example.test",
        path_command,
        path_spec,
        http_transport=_mock(
            lambda request: pytest.fail(f"unexpected request: {request}")
        ),
    )
    assert path_result.error is not None
    assert path_result.error.code == "cli_invalid_parameter"
    assert path_result.exchanges == ()

    with pytest.raises(ValueError):
        # Frozen M3 evidence intentionally checks the module-private scalar boundary.
        cli_execution._wire_string(None)  # pyright: ignore[reportPrivateUsage]


@pytest.mark.asyncio
async def test_m3_ver_15_interactive_null_is_one_primary_exchange() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/health/core":
            return httpx.Response(
                200,
                headers={"Content-Type": "application/json"},
                json=READY,
                request=request,
            )
        assert request.url.path == "/api/v1/core/object-templates"
        assert request.url.params.multi_items() == [("parent_template_id", "null")]
        return _page(request)

    session = InteractiveSession(http_transport=_mock(handler))
    connected = await session.submit("/connect http://example.test")
    assert connected is not None and connected.result.status == "ok"
    requests.clear()

    outcome = await session.submit("object-template list parent_template_id=null")
    assert outcome is not None
    assert outcome.result.status == "ok"
    assert len(requests) == 1
    assert len(outcome.result.exchanges) == 1
    assert outcome.result.exchanges[0].request.query == {
        "parent_template_id": ("null",)
    }
    await session.close()
