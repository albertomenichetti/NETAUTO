"""M2-VER-28 formatted renderer and bounded enrichment evidence."""

from collections.abc import Callable

import httpx
import pytest

from netauto.cli.model import (
    CliError,
    CliResult,
    CommandKey,
    ErrorSource,
    ParsedCommand,
)
from netauto.cli.registry import COMMAND_REGISTRY
from netauto.cli.render import RENDERER_REGISTRY, render_formatted
from netauto.cli.repl import InteractiveSession, render_interactive

DT = "11111111-1111-1111-1111-111111111111"
OT = "22222222-2222-2222-2222-222222222222"
PARENT = "33333333-3333-3333-3333-333333333333"
TARGET = "44444444-4444-4444-4444-444444444444"
OBJ = "55555555-5555-5555-5555-555555555555"
CHILD = "66666666-6666-6666-6666-666666666666"
DEST = "77777777-7777-7777-7777-777777777777"
RD = "88888888-8888-8888-8888-888888888888"
RESOLUTION = "99999999-9999-9999-9999-999999999999"
REL = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"

READY = {
    "app_status": {"status": "ok"},
    "db_status": {"status": "ok"},
    "execution_time_ms": 1,
}


def _template(template_id: str) -> dict[str, object]:
    names = {OT: "server", PARENT: "asset", TARGET: "disk"}
    return {
        "id": template_id,
        "namespace": "infra",
        "name": names[template_id],
        "description": None,
        "abstract": False,
        "parent_template_id": PARENT if template_id == OT else None,
        "default_version": 1,
    }


def _object(object_id: str) -> dict[str, object]:
    names = {OBJ: "server01", CHILD: "child01", DEST: "server02"}
    return {
        "id": object_id,
        "canonical_name": names[object_id],
        "template_id": OT if object_id != DEST else TARGET,
        "template_version": 1,
        "properties": {},
    }


def _primary_payload(path: str) -> object:
    if path == f"/api/v1/core/datatypes/{DT}/versions/1":
        return {
            "datatype_id": DT,
            "version": 1,
            "revision": 1,
            "status": "PUBLISHED",
            "base_type": "core.string",
            "constraints": {},
        }
    if path == f"/api/v1/core/object-templates/{OT}":
        return _template(OT)
    if path == f"/api/v1/core/object-templates/{OT}/versions/2":
        return {
            "template_id": OT,
            "version": 2,
            "revision": 1,
            "status": "PUBLISHED",
            "parent_template_id": PARENT,
            "parent_version": 1,
            "properties": [
                {
                    "name": "hostname",
                    "position": 1,
                    "datatype_id": DT,
                    "datatype_version": 1,
                    "value_mode": "SCALAR",
                    "required": False,
                }
            ],
            "components": [
                {
                    "name": "disk",
                    "position": 1,
                    "target_template_id": TARGET,
                }
            ],
        }
    if path == f"/api/v1/core/object-templates/{OT}/versions/2/effective-schema":
        return {
            "template_id": OT,
            "version": 2,
            "properties": [
                {
                    "name": "hostname",
                    "position": 1,
                    "datatype_id": DT,
                    "datatype_version": 1,
                    "value_mode": "SCALAR",
                    "required": False,
                    "declaring_template_id": PARENT,
                }
            ],
            "components": [
                {
                    "name": "disk",
                    "position": 1,
                    "target_template_id": TARGET,
                    "declaring_template_id": OT,
                }
            ],
        }
    if path == f"/api/v1/core/objects/{OBJ}":
        return _object(OBJ)
    if path == f"/api/v1/core/objects/{CHILD}/owner":
        return {
            "parent_object_id": OBJ,
            "slot_declaring_template_id": PARENT,
            "slot_name": "member",
        }
    if path == f"/api/v1/core/relationship-definitions/{RD}":
        return {
            "id": RD,
            "symmetric": False,
            "default_version": 1,
            "resolutions": [
                {
                    "resolution_id": RESOLUTION,
                    "name": "hosts",
                    "from_template_id": OT,
                    "to_template_id": TARGET,
                }
            ],
        }
    if path == f"/api/v1/core/relationship-definitions/{RD}/versions/1":
        return {
            "relationship_definition_id": RD,
            "version": 1,
            "revision": 1,
            "status": "PUBLISHED",
            "properties": [
                {
                    "name": "label",
                    "position": 1,
                    "datatype_id": DT,
                    "datatype_version": 1,
                    "value_mode": "SCALAR",
                }
            ],
        }
    if path == f"/api/v1/core/relationships/{REL}":
        return {
            "id": REL,
            "relationship_definition_id": RD,
            "relationship_definition_version": 1,
            "properties": {},
            "views": [
                {
                    "object_id": OBJ,
                    "destination_object_id": DEST,
                    "name": "hosts",
                }
            ],
        }
    raise KeyError(path)


def _handler(paths: list[str]) -> Callable[[httpx.Request], httpx.Response]:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        paths.append(path)
        if path == "/health/core":
            payload: object = READY
        elif path == f"/api/v1/core/datatypes/{DT}":
            payload = {
                "id": DT,
                "namespace": "core",
                "name": "string",
                "description": None,
                "default_version": 1,
            }
        elif (
            path
            in {
                f"/api/v1/core/object-templates/{OT}",
                f"/api/v1/core/object-templates/{PARENT}",
                f"/api/v1/core/object-templates/{TARGET}",
            }
            and path != f"/api/v1/core/object-templates/{OT}"
        ):
            payload = _template(path.rsplit("/", 1)[1])
        elif path == f"/api/v1/core/object-templates/{PARENT}/versions/1":
            payload = {
                "template_id": PARENT,
                "version": 1,
                "revision": 1,
                "status": "PUBLISHED",
                "parent_template_id": None,
                "parent_version": None,
                "properties": [],
                "components": [],
            }
        elif (
            path
            in {
                f"/api/v1/core/objects/{OBJ}",
                f"/api/v1/core/objects/{DEST}",
            }
            and path != f"/api/v1/core/objects/{OBJ}"
        ):
            payload = _object(path.rsplit("/", 1)[1])
        else:
            payload = _primary_payload(path)
        return httpx.Response(
            200,
            headers={"Content-Type": "application/json"},
            json=payload,
            request=request,
        )

    return handler


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("command", "expected_paths", "visible_name"),
    [
        (
            f"datatype get-version {DT} version=1",
            [
                f"/api/v1/core/datatypes/{DT}/versions/1",
                f"/api/v1/core/datatypes/{DT}",
            ],
            "core.string",
        ),
        (
            f"object-template get {OT}",
            [
                f"/api/v1/core/object-templates/{OT}",
                f"/api/v1/core/object-templates/{PARENT}",
            ],
            "infra.asset",
        ),
        (
            f"object-template get-version {OT} version=2",
            [
                f"/api/v1/core/object-templates/{OT}/versions/2",
                f"/api/v1/core/object-templates/{OT}",
                f"/api/v1/core/object-templates/{PARENT}",
                f"/api/v1/core/object-templates/{PARENT}/versions/1",
                f"/api/v1/core/datatypes/{DT}",
                f"/api/v1/core/object-templates/{TARGET}",
            ],
            "infra.disk",
        ),
        (
            f"object-template get-effective-schema {OT} version=2",
            [
                f"/api/v1/core/object-templates/{OT}/versions/2/effective-schema",
                f"/api/v1/core/object-templates/{OT}",
                f"/api/v1/core/object-templates/{PARENT}",
                f"/api/v1/core/datatypes/{DT}",
                f"/api/v1/core/object-templates/{TARGET}",
            ],
            "infra.asset",
        ),
        (
            f"object get {OBJ}",
            [f"/api/v1/core/objects/{OBJ}", f"/api/v1/core/object-templates/{OT}"],
            "infra.server",
        ),
        (
            f"object get-owner {CHILD}",
            [
                f"/api/v1/core/objects/{CHILD}/owner",
                f"/api/v1/core/objects/{OBJ}",
                f"/api/v1/core/object-templates/{PARENT}",
            ],
            "server01",
        ),
        (
            f"relationship-definition get {RD}",
            [
                f"/api/v1/core/relationship-definitions/{RD}",
                f"/api/v1/core/object-templates/{OT}",
                f"/api/v1/core/object-templates/{TARGET}",
            ],
            "infra.disk",
        ),
        (
            f"relationship-definition get-version {RD} version=1",
            [
                f"/api/v1/core/relationship-definitions/{RD}/versions/1",
                f"/api/v1/core/datatypes/{DT}",
            ],
            "core.string",
        ),
        (
            f"relationship get {REL}",
            [
                f"/api/v1/core/relationships/{REL}",
                f"/api/v1/core/objects/{OBJ}",
                f"/api/v1/core/objects/{DEST}",
            ],
            "server02",
        ),
    ],
)
async def test_exact_nine_formatted_enrichments_are_ordered_get_only(
    command: str,
    expected_paths: list[str],
    visible_name: str,
) -> None:
    paths: list[str] = []
    session = InteractiveSession(http_transport=httpx.MockTransport(_handler(paths)))
    await session.submit("/connect http://example.test")
    paths.clear()
    outcome = await session.submit(command)
    assert outcome is not None and outcome.result.status == "ok"
    assert paths == expected_paths
    assert all(
        exchange.request.method == "GET" for exchange in outcome.result.exchanges
    )
    assert len(outcome.result.exchanges) == len(expected_paths)
    rendered = render_interactive(session, outcome)
    assert visible_name in rendered
    assert command.split()[2] in rendered
    await session.close()


@pytest.mark.asyncio
async def test_json_mode_performs_primary_only_without_presentation_enrichment() -> (
    None
):
    paths: list[str] = []
    session = InteractiveSession(http_transport=httpx.MockTransport(_handler(paths)))
    await session.submit("/connect http://example.test")
    await session.submit("/output JSON")
    paths.clear()
    outcome = await session.submit(f"object get {OBJ}")
    assert outcome is not None and outcome.result.status == "ok"
    assert paths == [f"/api/v1/core/objects/{OBJ}"]
    assert len(outcome.result.exchanges) == 1
    assert outcome.presentation == outcome.result.as_json()["result"]
    await session.close()


@pytest.mark.asyncio
async def test_mutation_and_page_rendering_never_issue_hidden_enrichment() -> None:
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        if request.url.path == "/health/core":
            payload: object = READY
        elif request.url.path == f"/api/v1/core/objects/{OBJ}/rename":
            payload = {**_object(OBJ), "canonical_name": "renamed"}
        elif request.url.path == "/api/v1/core/objects":
            payload = {
                "items": [
                    {
                        "id": OBJ,
                        "canonical_name": "server01",
                        "template_id": OT,
                        "template_version": 1,
                    }
                ],
                "next_cursor": "opaque-next",
            }
        else:
            raise AssertionError(request.url)
        return httpx.Response(
            200,
            headers={"Content-Type": "application/json"},
            json=payload,
            request=request,
        )

    session = InteractiveSession(http_transport=httpx.MockTransport(handler))
    await session.submit("/connect http://example.test")
    paths.clear()
    mutation = await session.submit(f"object rename {OBJ} canonical_name=renamed")
    page = await session.submit("object list")
    assert mutation is not None and page is not None
    assert paths == [f"/api/v1/core/objects/{OBJ}/rename", "/api/v1/core/objects"]
    assert "opaque-next" in render_interactive(session, page)
    assert OBJ in render_interactive(session, mutation)
    await session.close()


@pytest.mark.asyncio
async def test_enrichment_cycle_fails_whole_result_without_partial_render() -> None:
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        if request.url.path == "/health/core":
            payload: object = READY
        else:
            payload = {**_template(OT), "parent_template_id": OT}
        return httpx.Response(
            200,
            headers={"Content-Type": "application/json"},
            json=payload,
            request=request,
        )

    session = InteractiveSession(http_transport=httpx.MockTransport(handler))
    await session.submit("/connect http://example.test")
    paths.clear()
    outcome = await session.submit(f"object-template get {OT}")
    assert outcome is not None and outcome.result.error is not None
    assert outcome.result.error.code == "cli_protocol_error"
    assert outcome.presentation is None
    rendered = render_interactive(session, outcome)
    assert "parent_lineage" not in rendered
    assert paths == [f"/api/v1/core/object-templates/{OT}"]
    await session.close()


@pytest.mark.asyncio
async def test_enrichment_transport_failure_disconnects_and_preserves_trace() -> None:
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        if request.url.path == "/health/core":
            return httpx.Response(200, json=READY, request=request)
        if request.url.path == f"/api/v1/core/objects/{OBJ}":
            return httpx.Response(200, json=_object(OBJ), request=request)
        raise httpx.ReadError("controlled")

    session = InteractiveSession(http_transport=httpx.MockTransport(handler))
    await session.submit("/connect http://example.test")
    outcome = await session.submit(f"object get {OBJ}")
    assert outcome is not None and outcome.result.error is not None
    assert outcome.result.error.source == "transport"
    assert len(outcome.result.exchanges) == 2
    assert outcome.result.exchanges[-1].response is None
    assert session.transport is None


def test_every_command_renderer_key_resolves_from_one_registry() -> None:
    assert set(RENDERER_REGISTRY) == {
        spec.renderer_key for spec in COMMAND_REGISTRY.values()
    }
    assert len(COMMAND_REGISTRY) == 63
    assert all(
        RENDERER_REGISTRY[spec.renderer_key] for spec in COMMAND_REGISTRY.values()
    )


def test_formatted_error_is_bounded_and_bodyless_success_names_target() -> None:
    command = ParsedCommand.create(CommandKey("object", "delete"), OBJ, {})
    failed = CliResult.failed(
        command,
        (),
        CliError.create(
            ErrorSource.LOCAL,
            "cli_not_connected",
            "The CLI is not connected to an endpoint.",
            {"id": OBJ},
        ),
    )
    failure_text = render_formatted(failed)
    assert "cli_not_connected" in failure_text
    assert OBJ in failure_text
    assert "Traceback" not in failure_text

    spec = COMMAND_REGISTRY[command.key]
    success = CliResult.ok(command, (), None)
    success_text = render_formatted(success, spec, None)
    assert "http_status: 204" in success_text
    assert f"target: {OBJ}" in success_text
