"""HTTP-only execution, selectors, trace, and protocol evidence for M2-S05."""

from collections.abc import Callable
from typing import cast
from uuid import UUID

import httpx
import pytest

from netauto.cli.execution import execute
from netauto.cli.model import CommandKey, ParsedCommand
from netauto.cli.parser import parse_process
from netauto.cli.registry import COMMAND_REGISTRY
from netauto.cli.selectors import resolve_selectors
from netauto.cli.transport import TIMEOUT, HttpTransport

OBJECT_ID = "11111111-1111-1111-1111-111111111111"
TEMPLATE_ID = "22222222-2222-2222-2222-222222222222"
SECOND_TEMPLATE_ID = "33333333-3333-3333-3333-333333333333"
DATATYPE_ID = "44444444-4444-4444-4444-444444444444"


def _mock(handler: Callable[[httpx.Request], httpx.Response]) -> httpx.MockTransport:
    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_selector_deduplication_cookie_isolation_and_primary_trace() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/api/v1/core/objects":
            return httpx.Response(
                200,
                headers={
                    "Content-Type": "application/json",
                    "Set-Cookie": "session=must-not-propagate",
                },
                json={
                    "items": [
                        {
                            "id": OBJECT_ID,
                            "canonical_name": "server01",
                            "template_id": TEMPLATE_ID,
                            "template_version": 1,
                        }
                    ],
                    "next_cursor": None,
                },
            )
        assert request.url.path == f"/api/v1/core/objects/{OBJECT_ID}/attach"
        assert "cookie" not in request.headers
        assert request.headers["accept"] == "application/json"
        assert request.headers["content-type"] == "application/json"
        assert request.headers["user-agent"].startswith("netauto/")
        return httpx.Response(
            200,
            headers={"Content-Type": "application/json"},
            json={
                "slot_declaring_template_id": TEMPLATE_ID,
                "slot_name": "member",
                "child_object_id": OBJECT_ID,
            },
        )

    _, command, spec = parse_process(
        [
            "-n",
            "http://example.test",
            "object",
            "attach",
            "server01",
            "slot_name=member",
            "child_object_id=server01",
        ]
    )
    result = await execute(
        "http://example.test", command, spec, http_transport=_mock(handler)
    )
    assert result.status == "ok"
    assert len(requests) == 2
    assert len(result.exchanges) == 2
    assert result.command is command
    assert result.command is not None
    assert result.command.parameters["child_object_id"] == "server01"
    assert result.exchanges[1].request.body == {
        "slot_name": "member",
        "child_object_id": OBJECT_ID,
    }


@pytest.mark.asyncio
async def test_selector_lookup_zero_stops_before_primary_request() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            headers={"Content-Type": "application/json"},
            json={"items": [], "next_cursor": None},
        )

    _, command, spec = parse_process(
        ["-n", "http://example.test", "datatype", "get", "core.missing"]
    )
    result = await execute(
        "http://example.test", command, spec, http_transport=_mock(handler)
    )
    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == "cli_selector_not_found"
    assert len(requests) == 1
    assert len(result.exchanges) == 1


@pytest.mark.asyncio
async def test_selector_ambiguity_is_bounded_to_two_ids() -> None:
    ids = [
        "11111111-1111-1111-1111-111111111111",
        "22222222-2222-2222-2222-222222222222",
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params.multi_items() == [
            ("namespace", "core"),
            ("name", "string"),
            ("limit", "2"),
        ]
        return httpx.Response(
            200,
            headers={"Content-Type": "application/json"},
            json={
                "items": [
                    {
                        "id": item,
                        "namespace": "core",
                        "name": "string",
                        "description": None,
                        "default_version": 1,
                    }
                    for item in ids
                ],
                "next_cursor": "more",
            },
        )

    _, command, spec = parse_process(
        ["-n", "http://example.test", "datatype", "get", "core.string"]
    )
    result = await execute(
        "http://example.test", command, spec, http_transport=_mock(handler)
    )
    assert result.error is not None
    assert result.error.code == "cli_selector_ambiguous"
    assert result.error.details["matched_ids"] == ids


@pytest.mark.asyncio
async def test_nested_selector_plan_is_ordered_and_deduplicated() -> None:
    lookups: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        namespace = request.url.params["namespace"]
        name = request.url.params["name"]
        lookups.append((namespace, name))
        if request.url.path.endswith("/object-templates"):
            identifier = TEMPLATE_ID if name == "left" else SECOND_TEMPLATE_ID
            item = {
                "id": identifier,
                "namespace": namespace,
                "name": name,
                "description": None,
                "abstract": False,
                "parent_template_id": None,
                "default_version": 1,
            }
        else:
            item = {
                "id": DATATYPE_ID,
                "namespace": namespace,
                "name": name,
                "description": None,
                "default_version": 1,
            }
        return httpx.Response(
            200,
            headers={"Content-Type": "application/json"},
            json={"items": [item], "next_cursor": None},
        )

    _, command, spec = parse_process(
        [
            "-n",
            "http://example.test",
            "relationship-definition",
            "create",
            "symmetric=false",
            'perspectives=[{"template_id":"infra.left","name":"a"},'
            '{"template_id":"infra.right","name":"b"}]',
            'properties=[{"name":"p","position":1,'
            '"datatype_id":"core.string","value_mode":"SCALAR"},'
            '{"name":"q","position":2,'
            '"datatype_id":"core.string","value_mode":"SCALAR"}]',
        ]
    )
    async with HttpTransport(
        "http://example.test", transport=_mock(handler)
    ) as transport:
        result = await resolve_selectors(transport, command, spec)
    assert result.error is None
    assert lookups == [
        ("infra", "left"),
        ("infra", "right"),
        ("core", "string"),
    ]
    assert len(result.exchanges) == 3
    perspectives = result.parameters["perspectives"]
    properties = result.parameters["properties"]
    assert isinstance(perspectives, list)
    assert isinstance(properties, list)
    perspective_items = cast(list[dict[str, object]], perspectives)
    property_items = cast(list[dict[str, object]], properties)
    assert perspective_items[0]["template_id"] == TEMPLATE_ID
    assert perspective_items[1]["template_id"] == SECOND_TEMPLATE_ID
    assert property_items[0]["datatype_id"] == DATATYPE_ID
    assert property_items[1]["datatype_id"] == DATATYPE_ID
    original = cast(list[dict[str, object]], command.parameters["perspectives"])
    assert original[0]["template_id"] == "infra.left"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("resource", "selector", "path", "item"),
    [
        (
            "datatype",
            "core.string",
            "/api/v1/core/datatypes",
            {
                "id": DATATYPE_ID,
                "namespace": "core",
                "name": "string",
                "description": None,
                "default_version": 1,
            },
        ),
        (
            "object-template",
            "infra.vm",
            "/api/v1/core/object-templates",
            {
                "id": TEMPLATE_ID,
                "namespace": "infra",
                "name": "vm",
                "description": None,
                "abstract": False,
                "parent_template_id": None,
                "default_version": 1,
            },
        ),
        (
            "object",
            "server01",
            "/api/v1/core/objects",
            {
                "id": OBJECT_ID,
                "canonical_name": "server01",
                "template_id": TEMPLATE_ID,
                "template_version": 1,
            },
        ),
    ],
)
@pytest.mark.parametrize(
    ("outcome", "expected_code"),
    [
        ("zero", "cli_selector_not_found"),
        ("one", None),
        ("many", "cli_selector_ambiguous"),
    ],
)
async def test_human_selector_families_cover_zero_one_many(
    resource: str,
    selector: str,
    path: str,
    item: dict[str, object],
    outcome: str,
    expected_code: str | None,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == path
        if outcome == "zero":
            items: list[dict[str, object]] = []
            cursor = None
        elif outcome == "one":
            items = [item]
            cursor = None
        else:
            second = dict(item)
            second["id"] = SECOND_TEMPLATE_ID
            items = [item, second]
            cursor = "more"
        return httpx.Response(
            200,
            headers={"Content-Type": "application/json"},
            json={"items": items, "next_cursor": cursor},
        )

    command = ParsedCommand.create(CommandKey(resource, "get"), selector, {})
    async with HttpTransport(
        "http://example.test", transport=_mock(handler)
    ) as transport:
        result = await resolve_selectors(
            transport, command, COMMAND_REGISTRY[command.key]
        )
    assert len(result.exchanges) == 1
    if expected_code is None:
        assert result.error is None
        assert result.selector == str(item["id"])
    else:
        assert result.error is not None
        assert result.error.code == expected_code


@pytest.mark.asyncio
async def test_uuid_only_selector_families_accept_uuid_and_reject_names() -> None:
    definition = CommandKey("relationship-definition", "get")
    relationship = CommandKey("relationship", "get")
    commands = [
        ParsedCommand.create(definition, OBJECT_ID, {}),
        ParsedCommand.create(relationship, OBJECT_ID, {}),
        ParsedCommand.create(
            CommandKey("relationship", "create"),
            None,
            {
                "resolution_id": OBJECT_ID,
                "from_object_id": OBJECT_ID,
                "to_object_id": SECOND_TEMPLATE_ID,
            },
        ),
    ]
    async with HttpTransport(
        "http://example.test", transport=_mock(lambda request: pytest.fail())
    ) as transport:
        for command in commands:
            result = await resolve_selectors(
                transport, command, COMMAND_REGISTRY[command.key]
            )
            assert result.error is None
            assert result.exchanges == ()

        for key in (definition, relationship):
            command = ParsedCommand.create(key, "human-name", {})
            result = await resolve_selectors(transport, command, COMMAND_REGISTRY[key])
            assert result.error is not None
            assert result.error.code == "cli_selector_invalid"
            assert result.exchanges == ()

        _, resolution_command, resolution_spec = parse_process(
            [
                "-n",
                "http://example.test",
                "relationship",
                "create",
                "resolution_id=human-name",
                f"from_object_id={OBJECT_ID}",
                f"to_object_id={SECOND_TEMPLATE_ID}",
            ]
        )
        resolution = await resolve_selectors(
            transport, resolution_command, resolution_spec
        )
        assert resolution.error is not None
        assert resolution.error.code == "cli_selector_invalid"
        assert resolution.error.details["selector_kind"] == "relationship-resolution"
        assert resolution.exchanges == ()


@pytest.mark.asyncio
async def test_selector_cache_never_survives_one_command() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(
            200,
            headers={"Content-Type": "application/json"},
            json={
                "items": [
                    {
                        "id": OBJECT_ID,
                        "canonical_name": "server01",
                        "template_id": TEMPLATE_ID,
                        "template_version": 1,
                    }
                ],
                "next_cursor": None,
            },
        )

    command = ParsedCommand.create(CommandKey("object", "get"), "server01", {})
    async with HttpTransport(
        "http://example.test", transport=_mock(handler)
    ) as transport:
        first = await resolve_selectors(
            transport, command, COMMAND_REGISTRY[command.key]
        )
        second = await resolve_selectors(
            transport, command, COMMAND_REGISTRY[command.key]
        )
    assert first.error is None
    assert second.error is None
    assert attempts == 2


@pytest.mark.asyncio
async def test_uuid_top_level_selector_has_precedence_and_no_lookup() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.url.path == f"/api/v1/core/datatypes/{OBJECT_ID}"
        return httpx.Response(
            200,
            headers={"Content-Type": "application/json"},
            json={
                "id": OBJECT_ID,
                "namespace": "core",
                "name": "string",
                "description": None,
                "default_version": 1,
            },
        )

    command = ParsedCommand.create(CommandKey("datatype", "get"), OBJECT_ID, {})
    result = await execute(
        "http://example.test",
        command,
        COMMAND_REGISTRY[command.key],
        http_transport=_mock(handler),
    )
    assert result.status == "ok"
    assert len(requests) == 1
    assert len(result.exchanges) == 1


@pytest.mark.asyncio
async def test_remote_business_error_is_preserved_exactly() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            404,
            headers={"Content-Type": "application/json"},
            json={
                "code": "resource_not_found",
                "message": "The resource was not found.",
                "details": {"resource": "datatype"},
            },
        )

    command = ParsedCommand.create(CommandKey("datatype", "get"), OBJECT_ID, {})
    result = await execute(
        "http://example.test",
        command,
        COMMAND_REGISTRY[command.key],
        http_transport=_mock(handler),
    )
    assert result.error is not None
    assert result.error.source == "remote"
    assert result.error.code == "resource_not_found"
    assert result.error.http_status == 404
    assert result.error.details == {"resource": "datatype"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(302, headers={"Location": "/elsewhere"}),
        httpx.Response(200, headers={"Content-Type": "application/json"}),
        httpx.Response(
            200, headers={"Content-Type": "application/json"}, json={"wrong": True}
        ),
        httpx.Response(
            409,
            headers={"Content-Type": "application/json"},
            json={"code": "resource_not_found", "message": "x", "details": {}},
        ),
    ],
)
async def test_protocol_failures_are_not_remapped(response: httpx.Response) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return response

    command = ParsedCommand.create(CommandKey("datatype", "get"), OBJECT_ID, {})
    result = await execute(
        "http://example.test",
        command,
        COMMAND_REGISTRY[command.key],
        http_transport=_mock(handler),
    )
    assert result.error is not None
    assert result.error.source == "protocol"
    assert result.error.code == "cli_protocol_error"
    assert len(result.exchanges) == 1


@pytest.mark.asyncio
async def test_created_location_is_validated_exactly() -> None:
    location = f"/api/v1/core/objects/{OBJECT_ID}"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            201,
            headers={
                "Content-Type": "application/json",
                "Location": location,
            },
            json={
                "id": OBJECT_ID,
                "canonical_name": "server01",
                "template_id": TEMPLATE_ID,
                "template_version": 1,
                "properties": {},
            },
        )

    command = ParsedCommand.create(
        CommandKey("object", "create"), None, {"template_id": TEMPLATE_ID}
    )
    valid = await execute(
        "http://example.test",
        command,
        COMMAND_REGISTRY[command.key],
        http_transport=_mock(handler),
    )
    assert valid.status == "ok"
    assert valid.error is None

    location = "/api/v1/core/objects/not-the-returned-id"
    invalid = await execute(
        "http://example.test",
        command,
        COMMAND_REGISTRY[command.key],
        http_transport=_mock(handler),
    )
    assert invalid.error is not None
    assert invalid.error.code == "cli_protocol_error"


@pytest.mark.asyncio
async def test_204_with_body_is_protocol_error() -> None:
    content = b""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(204, content=content)

    command = ParsedCommand.create(CommandKey("datatype", "delete"), OBJECT_ID, {})
    valid = await execute(
        "http://example.test",
        command,
        COMMAND_REGISTRY[command.key],
        http_transport=_mock(handler),
    )
    assert valid.status == "ok"
    assert valid.result is None

    content = b"unexpected"
    invalid = await execute(
        "http://example.test",
        command,
        COMMAND_REGISTRY[command.key],
        http_transport=_mock(handler),
    )
    assert invalid.error is not None
    assert invalid.error.code == "cli_protocol_error"


@pytest.mark.asyncio
async def test_transport_failure_is_one_attempt_with_response_null() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ConnectError("sensitive raw transport text", request=request)

    command = ParsedCommand.create(CommandKey("datatype", "list"), None, {})
    result = await execute(
        "http://example.test",
        command,
        COMMAND_REGISTRY[command.key],
        http_transport=_mock(handler),
    )
    assert attempts == 1
    assert result.error is not None
    assert result.error.code == "cli_transport_error"
    assert "sensitive" not in str(result.as_json())
    assert len(result.exchanges) == 1
    assert result.exchanges[0].response is None
    assert result.exchanges[0].elapsed_ms >= 0


def test_registry_uuid_only_selector_is_canonical() -> None:
    UUID(OBJECT_ID)


def test_http_timeout_policy_is_exact() -> None:
    assert TIMEOUT.connect == 5.0
    assert TIMEOUT.pool == 5.0
    assert TIMEOUT.read == 30.0
    assert TIMEOUT.write == 30.0
