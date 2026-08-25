"""M3-VER-01..03 evidence for official CLI Location correctness."""

import ast
import inspect
from dataclasses import dataclass

import httpx
import pytest

import netauto.cli.protocol as protocol_module
from netauto.cli.execution import execute
from netauto.cli.main import run
from netauto.cli.model import (
    CommandKey,
    HttpExchangeTrace,
    HttpRequestTrace,
    HttpResponseTrace,
    JsonValue,
    ParsedCommand,
    freeze_json,
)
from netauto.cli.protocol import (
    ProtocolOutcome,
    interpret_response,
    location_template_tokens,
    materialize_location,
)
from netauto.cli.registry import COMMAND_REGISTRY
from netauto.cli.repl import InteractiveSession, render_interactive
from netauto.transport.http.objects import ObjectDto

DATATYPE_ID = "11111111-1111-1111-1111-111111111111"
TEMPLATE_ID = "22222222-2222-2222-2222-222222222222"
OBJECT_ID = "33333333-3333-3333-3333-333333333333"
DEFINITION_ID = "44444444-4444-4444-4444-444444444444"
RELATIONSHIP_ID = "55555555-5555-5555-5555-555555555555"
RESOLUTION_ID = "66666666-6666-6666-6666-666666666666"
SECOND_TEMPLATE_ID = "77777777-7777-7777-7777-777777777777"
SECOND_RESOLUTION_ID = "88888888-8888-8888-8888-888888888888"
SECOND_OBJECT_ID = "99999999-9999-9999-9999-999999999999"

M3_CLI_201_CENSUS = frozenset(
    {
        CommandKey("datatype", "create"),
        CommandKey("datatype", "create-next"),
        CommandKey("object-template", "create"),
        CommandKey("object-template", "create-next"),
        CommandKey("object", "create"),
        CommandKey("relationship-definition", "create"),
        CommandKey("relationship-definition", "create-next"),
        CommandKey("relationship", "create"),
    }
)

M3_NESTED_201_CENSUS = frozenset(
    {
        CommandKey("datatype", "create"),
        CommandKey("object-template", "create"),
        CommandKey("relationship-definition", "create"),
    }
)


def _datatype_version(version: int) -> dict[str, JsonValue]:
    return {
        "datatype_id": DATATYPE_ID,
        "version": version,
        "revision": 1,
        "status": "DRAFT",
        "base_type": "core.string",
        "constraints": {},
    }


def _template_version(version: int) -> dict[str, JsonValue]:
    return {
        "template_id": TEMPLATE_ID,
        "version": version,
        "revision": 1,
        "status": "DRAFT",
        "parent_template_id": None,
        "parent_version": None,
        "properties": [],
        "components": [],
    }


def _definition_version(version: int) -> dict[str, JsonValue]:
    return {
        "relationship_definition_id": DEFINITION_ID,
        "version": version,
        "revision": 1,
        "status": "DRAFT",
        "properties": [],
    }


def _object_body() -> dict[str, JsonValue]:
    return {
        "id": OBJECT_ID,
        "canonical_name": "server01",
        "template_id": TEMPLATE_ID,
        "template_version": 1,
        "properties": {},
    }


def _datatype_create_body() -> dict[str, JsonValue]:
    return {
        "datatype": {
            "id": DATATYPE_ID,
            "namespace": "core",
            "name": "string",
            "description": None,
            "default_version": 1,
        },
        "version": _datatype_version(1),
    }


@dataclass(frozen=True, slots=True)
class CreateCase:
    key: CommandKey
    selector: str | None
    parameters: dict[str, JsonValue]
    response_body: dict[str, JsonValue]
    request_path: str
    location: str


CREATE_CASES = (
    CreateCase(
        CommandKey("datatype", "create"),
        None,
        {"namespace": "core", "name": "string", "base_type": "core.string"},
        _datatype_create_body(),
        "/api/v1/core/datatypes",
        f"/api/v1/core/datatypes/{DATATYPE_ID}",
    ),
    CreateCase(
        CommandKey("datatype", "create-next"),
        DATATYPE_ID,
        {"source_version": 1},
        _datatype_version(2),
        f"/api/v1/core/datatypes/{DATATYPE_ID}/create-next",
        f"/api/v1/core/datatypes/{DATATYPE_ID}/versions/2",
    ),
    CreateCase(
        CommandKey("object-template", "create"),
        None,
        {"namespace": "infra", "name": "server", "abstract": False},
        {
            "object_template": {
                "id": TEMPLATE_ID,
                "namespace": "infra",
                "name": "server",
                "description": None,
                "abstract": False,
                "parent_template_id": None,
                "default_version": 1,
            },
            "version": _template_version(1),
        },
        "/api/v1/core/object-templates",
        f"/api/v1/core/object-templates/{TEMPLATE_ID}",
    ),
    CreateCase(
        CommandKey("object-template", "create-next"),
        TEMPLATE_ID,
        {"source_version": 1},
        _template_version(2),
        f"/api/v1/core/object-templates/{TEMPLATE_ID}/create-next",
        f"/api/v1/core/object-templates/{TEMPLATE_ID}/versions/2",
    ),
    CreateCase(
        CommandKey("object", "create"),
        None,
        {"template_id": TEMPLATE_ID},
        _object_body(),
        "/api/v1/core/objects",
        f"/api/v1/core/objects/{OBJECT_ID}",
    ),
    CreateCase(
        CommandKey("relationship-definition", "create"),
        None,
        {
            "symmetric": False,
            "perspectives": [
                {"template_id": TEMPLATE_ID, "name": "hosts"},
                {"template_id": SECOND_TEMPLATE_ID, "name": "hosted_by"},
            ],
        },
        {
            "relationship_definition": {
                "id": DEFINITION_ID,
                "symmetric": False,
                "default_version": 1,
                "resolutions": [
                    {
                        "resolution_id": RESOLUTION_ID,
                        "name": "hosts",
                        "from_template_id": TEMPLATE_ID,
                        "to_template_id": SECOND_TEMPLATE_ID,
                    },
                    {
                        "resolution_id": SECOND_RESOLUTION_ID,
                        "name": "hosted_by",
                        "from_template_id": SECOND_TEMPLATE_ID,
                        "to_template_id": TEMPLATE_ID,
                    },
                ],
            },
            "version": _definition_version(1),
        },
        "/api/v1/core/relationship-definitions",
        f"/api/v1/core/relationship-definitions/{DEFINITION_ID}",
    ),
    CreateCase(
        CommandKey("relationship-definition", "create-next"),
        DEFINITION_ID,
        {"source_version": 1},
        _definition_version(2),
        f"/api/v1/core/relationship-definitions/{DEFINITION_ID}/create-next",
        f"/api/v1/core/relationship-definitions/{DEFINITION_ID}/versions/2",
    ),
    CreateCase(
        CommandKey("relationship", "create"),
        None,
        {
            "resolution_id": RESOLUTION_ID,
            "from_object_id": OBJECT_ID,
            "to_object_id": SECOND_OBJECT_ID,
        },
        {
            "id": RELATIONSHIP_ID,
            "relationship_definition_id": DEFINITION_ID,
            "relationship_definition_version": 1,
            "properties": {},
            "views": [],
        },
        "/api/v1/core/relationships",
        f"/api/v1/core/relationships/{RELATIONSHIP_ID}",
    ),
)


def _request_values(case: CreateCase) -> dict[str, JsonValue]:
    values = dict(case.parameters)
    spec = COMMAND_REGISTRY[case.key]
    if spec.selector_parameter is not None and case.selector is not None:
        values[spec.selector_parameter] = case.selector
    return values


def _case_ids() -> list[str]:
    return [f"{case.key.resource}-{case.key.operation}" for case in CREATE_CASES]


def _protocol_outcome(
    template: str,
    *,
    locations: tuple[str, ...],
    request_values: dict[str, JsonValue] | None = None,
) -> ProtocolOutcome:
    body = _object_body()
    response_headers = [("Content-Type", "application/json")]
    response_headers.extend(("Location", value) for value in locations)
    response = httpx.Response(201, headers=response_headers, json=body)
    trace_headers: dict[str, tuple[str, ...]] = {"content-type": ("application/json",)}
    if locations:
        trace_headers["location"] = locations
    exchange = HttpExchangeTrace(
        HttpRequestTrace(
            "POST", "http://example.test/api/v1/core/objects", {}, {}, None
        ),
        HttpResponseTrace(201, trace_headers, "json", freeze_json(body)),
        0,
    )
    return interpret_response(
        response,
        exchange,
        expected_status=201,
        response_annotation=ObjectDto,
        location_template=template,
        request_values={} if request_values is None else request_values,
    )


def test_m3_ver_01_registry_and_location_dsl_census_is_exact() -> None:
    registered = frozenset(
        key for key, spec in COMMAND_REGISTRY.items() if spec.expected_status == 201
    )
    assert registered == M3_CLI_201_CENSUS
    assert len(registered) == 8
    assert len(COMMAND_REGISTRY) == 63

    nested: set[CommandKey] = set()
    for key in M3_CLI_201_CENSUS:
        template = COMMAND_REGISTRY[key].location_template
        assert template is not None
        tokens = location_template_tokens(template)
        assert tokens is not None and tokens
        if any("." in token for token in tokens):
            nested.add(key)
    assert frozenset(nested) == M3_NESTED_201_CENSUS
    assert M3_CLI_201_CENSUS - nested == frozenset(
        {
            CommandKey("datatype", "create-next"),
            CommandKey("object-template", "create-next"),
            CommandKey("object", "create"),
            CommandKey("relationship-definition", "create-next"),
            CommandKey("relationship", "create"),
        }
    )


def test_m3_ver_01_all_canonical_carriers_materialize_exact_locations() -> None:
    assert len(CREATE_CASES) == 8
    assert frozenset(case.key for case in CREATE_CASES) == M3_CLI_201_CENSUS
    for case in CREATE_CASES:
        template = COMMAND_REGISTRY[case.key].location_template
        assert template is not None
        assert (
            materialize_location(template, case.response_body, _request_values(case))
            == case.location
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CREATE_CASES, ids=_case_ids())
async def test_m3_ver_01_all_canonical_201_responses_are_successes(
    case: CreateCase,
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.url.path == case.request_path
        return httpx.Response(
            201,
            headers={
                "Content-Type": "application/json",
                "Location": case.location,
            },
            json=case.response_body,
        )

    command = ParsedCommand.create(case.key, case.selector, case.parameters)
    result = await execute(
        "http://example.test",
        command,
        COMMAND_REGISTRY[case.key],
        http_transport=httpx.MockTransport(handler),
    )
    assert result.status == "ok"
    assert result.error is None
    assert result.result == case.response_body
    assert len(requests) == 1
    assert len(result.exchanges) == 1
    assert result.exchanges[0].response is not None
    assert result.exchanges[0].response.headers["location"] == (case.location,)


@pytest.mark.parametrize(
    "template",
    [
        "{}",
        "{a..b}",
        "{a[0]}",
        "{a!r}",
        "{a:b}",
        "{{a}}",
        "{a.}",
        "{.a}",
        "{a",
        "a}",
        "{A}",
        "{a-b}",
        "{a.*}",
    ],
)
def test_m3_ver_02_closed_location_dsl_rejects_malformed_classes(
    template: str,
) -> None:
    assert location_template_tokens(template) is None
    assert materialize_location(template, {}, {}) is None


@pytest.mark.parametrize(
    ("template", "tokens"),
    [
        ("/static", ()),
        ("/{id}", ("id",)),
        ("/{version}", ("version",)),
        ("/{datatype_id}", ("datatype_id",)),
        ("/{datatype.id}", ("datatype.id",)),
        ("/{object_template.id}", ("object_template.id",)),
        (
            "/{relationship_definition.id}",
            ("relationship_definition.id",),
        ),
    ],
)
def test_m3_ver_02_closed_location_dsl_accepts_only_frozen_examples(
    template: str,
    tokens: tuple[str, ...],
) -> None:
    assert location_template_tokens(template) == tokens


def test_m3_ver_02_request_presence_precedes_response_fallback() -> None:
    result: dict[str, JsonValue] = {
        "id": "response",
        "datatype": {"id": "nested-response"},
    }
    assert materialize_location("/{id}", result, {"id": "request"}) == "/request"
    assert materialize_location("/{id}", result, {}) == "/response"
    assert (
        materialize_location(
            "/{datatype.id}", result, {"datatype.id": "exact-request-key"}
        )
        == "/exact-request-key"
    )


@pytest.mark.parametrize(
    "value",
    [None, True, 1.5, ["value"], {"value": "nested"}],
)
def test_m3_ver_02_nonmaterializable_request_value_never_falls_back(
    value: JsonValue,
) -> None:
    expected = f"/api/v1/core/objects/{OBJECT_ID}"
    outcome = _protocol_outcome(
        "/api/v1/core/objects/{id}",
        locations=(expected,),
        request_values={"id": value},
    )
    assert outcome.result is None
    assert outcome.error is not None
    assert outcome.error.code == "cli_protocol_error"


@pytest.mark.parametrize(
    "value",
    [None, True, 1.5, ["value"], {"value": "nested"}],
)
def test_m3_ver_02_nonmaterializable_response_values_return_no_location(
    value: JsonValue,
) -> None:
    assert materialize_location("/{token}", {"token": value}, {}) is None


@pytest.mark.parametrize(
    "template",
    ["/{missing}", "/{properties}", "/{properties.id}", "/{id.value}"],
)
def test_m3_ver_02_unresolvable_or_nonscalar_response_token_is_protocol_error(
    template: str,
) -> None:
    outcome = _protocol_outcome(template, locations=("/anything",))
    assert outcome.result is None
    assert outcome.error is not None
    assert outcome.error.code == "cli_protocol_error"


def test_m3_ver_02_dotted_tokens_are_literal_json_paths_not_python_format() -> None:
    result: dict[str, JsonValue] = {"datatype": {"id": DATATYPE_ID}}
    assert (
        materialize_location("/datatypes/{datatype.id}", result, {})
        == f"/datatypes/{DATATYPE_ID}"
    )
    assert (
        materialize_location("/{datatype.id}/{datatype.id}", result, {})
        == f"/{DATATYPE_ID}/{DATATYPE_ID}"
    )

    tree = ast.parse(inspect.getsource(protocol_module.materialize_location))
    formatter_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"format", "format_map"}
    ]
    assert formatter_calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "locations",
    [
        (),
        (f"/api/v1/core/objects/{OBJECT_ID}",) * 2,
        ("/api/v1/core/objects/not-the-response-id",),
    ],
    ids=["missing", "repeated", "mismatching"],
)
async def test_m3_ver_02_actual_location_failures_are_protocol_errors(
    locations: tuple[str, ...],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        headers = [("Content-Type", "application/json")]
        headers.extend(("Location", location) for location in locations)
        return httpx.Response(201, headers=headers, json=_object_body())

    key = CommandKey("object", "create")
    command = ParsedCommand.create(key, None, {"template_id": TEMPLATE_ID})
    result = await execute(
        "http://example.test",
        command,
        COMMAND_REGISTRY[key],
        http_transport=httpx.MockTransport(handler),
    )
    assert result.status == "error"
    assert result.error is not None
    assert result.error.source == "protocol"
    assert result.error.code == "cli_protocol_error"
    assert len(result.exchanges) == 1


def test_m3_ver_03_noninteractive_nested_create_is_truthful_and_primary_only() -> None:
    paths: list[str] = []
    location = f"/api/v1/core/datatypes/{DATATYPE_ID}"

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        return httpx.Response(
            201,
            headers={"Content-Type": "application/json", "Location": location},
            json=_datatype_create_body(),
        )

    result, exit_code = run(
        [
            "-n",
            "http://example.test",
            "datatype",
            "create",
            "namespace=core",
            "name=string",
            "base_type=core.string",
        ],
        http_transport=httpx.MockTransport(handler),
    )
    assert exit_code == 0
    assert result.status == "ok"
    assert result.error is None
    assert paths == ["/api/v1/core/datatypes"]
    assert len(result.exchanges) == 1
    assert result.exchanges[0].response is not None
    assert result.exchanges[0].response.headers["location"] == (location,)


@pytest.mark.asyncio
async def test_m3_ver_03_interactive_nested_create_is_truthful_and_primary_only() -> (
    None
):
    paths: list[str] = []
    location = f"/api/v1/core/datatypes/{DATATYPE_ID}"

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        if request.url.path == "/health/core":
            return httpx.Response(
                200,
                headers={"Content-Type": "application/json"},
                json={
                    "app_status": {"status": "ok"},
                    "db_status": {"status": "ok"},
                    "execution_time_ms": 1,
                },
            )
        return httpx.Response(
            201,
            headers={"Content-Type": "application/json", "Location": location},
            json=_datatype_create_body(),
        )

    session = InteractiveSession(http_transport=httpx.MockTransport(handler))
    connected = await session.submit("/connect http://example.test")
    assert connected is not None and connected.result.status == "ok"
    paths.clear()
    outcome = await session.submit(
        "datatype create namespace=core name=string base_type=core.string"
    )
    assert outcome is not None
    assert outcome.result.status == "ok"
    assert outcome.result.error is None
    assert paths == ["/api/v1/core/datatypes"]
    assert len(outcome.result.exchanges) == 1
    assert outcome.result.exchanges[0].response is not None
    assert outcome.result.exchanges[0].response.headers["location"] == (location,)
    rendered = render_interactive(session, outcome)
    assert "status: ok" in rendered
    assert f"location: {location}" in rendered
    assert paths == ["/api/v1/core/datatypes"]
    await session.close()
