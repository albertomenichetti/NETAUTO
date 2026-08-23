"""Permanent regression evidence for the bounded M2-S06 review findings."""

import json
from collections.abc import Callable

import httpx
import pytest

from netauto.cli.repl import ConnectionState, InteractiveSession, render_interactive

DT = "11111111-1111-1111-1111-111111111111"
WRONG_DT = "11111111-1111-1111-1111-111111111112"
OT = "22222222-2222-2222-2222-222222222222"
WRONG_OT = "22222222-2222-2222-2222-222222222223"
PARENT = "33333333-3333-3333-3333-333333333333"
TARGET = "44444444-4444-4444-4444-444444444444"
OBJ = "55555555-5555-5555-5555-555555555555"
WRONG_OBJ = "55555555-5555-5555-5555-555555555556"
CHILD = "66666666-6666-6666-6666-666666666666"

READY = {
    "app_status": {"status": "ok"},
    "db_status": {"status": "ok"},
    "execution_time_ms": 1,
}


def _response(
    request: httpx.Request, payload: object, *, status: int = 200
) -> httpx.Response:
    return httpx.Response(
        status,
        headers={"Content-Type": "application/json"},
        json=payload,
        request=request,
    )


def _datatype(datatype_id: str = DT) -> dict[str, object]:
    return {
        "id": datatype_id,
        "namespace": "core",
        "name": "string",
        "description": None,
        "default_version": 1,
    }


def _datatype_version() -> dict[str, object]:
    return {
        "datatype_id": DT,
        "version": 1,
        "revision": 1,
        "status": "PUBLISHED",
        "base_type": "core.string",
        "constraints": {},
    }


def _template(
    template_id: str,
    *,
    parent_template_id: str | None = None,
) -> dict[str, object]:
    names = {
        OT: "server",
        WRONG_OT: "wrong",
        PARENT: "asset",
        TARGET: "root",
    }
    return {
        "id": template_id,
        "namespace": "infra",
        "name": names[template_id],
        "description": None,
        "abstract": False,
        "parent_template_id": parent_template_id,
        "default_version": 1,
    }


def _template_version(
    template_id: str,
    version: int,
    *,
    parent_template_id: str | None = None,
    parent_version: int | None = None,
    properties: list[dict[str, object]] | None = None,
    components: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "template_id": template_id,
        "version": version,
        "revision": 1,
        "status": "PUBLISHED",
        "parent_template_id": parent_template_id,
        "parent_version": parent_version,
        "properties": [] if properties is None else properties,
        "components": [] if components is None else components,
    }


def _object(object_id: str = OBJ, *, template_id: str = OT) -> dict[str, object]:
    return {
        "id": object_id,
        "canonical_name": "server01",
        "template_id": template_id,
        "template_version": 1,
        "properties": {},
    }


def _datatype_page() -> dict[str, object]:
    return {"items": [_datatype()], "next_cursor": None}


def _object_page(object_id: str, canonical_name: str) -> dict[str, object]:
    return {
        "items": [
            {
                "id": object_id,
                "canonical_name": canonical_name,
                "template_id": OT,
                "template_version": 1,
            }
        ],
        "next_cursor": None,
    }


async def _connected_session(
    handler: Callable[[httpx.Request], httpx.Response],
) -> InteractiveSession:
    session = InteractiveSession(http_transport=httpx.MockTransport(handler))
    connected = await session.submit("/connect http://example.test")
    assert connected is not None and connected.result.status == "ok"
    return session


def _assert_protocol_failure(
    session: InteractiveSession,
    outcome: object,
    paths: list[str],
    expected_paths: list[str],
) -> None:
    from netauto.cli.repl import InteractiveOutcome

    assert isinstance(outcome, InteractiveOutcome)
    assert outcome.result.error is not None
    assert outcome.result.error.source == "protocol"
    assert outcome.result.error.code == "cli_protocol_error"
    assert outcome.presentation is None
    assert paths == expected_paths
    assert len(outcome.result.exchanges) == len(expected_paths)
    assert session.connection is ConnectionState.CONNECTED
    assert session.transport is not None and not session.transport.is_closed
    rendered = render_interactive(session, outcome)
    assert "status: error" in rendered
    assert "qualified_name" not in rendered


@pytest.mark.asyncio
async def test_rf01_human_selector_204_exposes_exact_target_without_hidden_get() -> (
    None
):
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        if request.url.path == "/health/core":
            return _response(request, READY)
        if request.url.path == "/api/v1/core/datatypes":
            return _response(request, _datatype_page())
        if request.url.path == f"/api/v1/core/datatypes/{DT}/versions/2":
            assert request.url.params["expected_revision"] == "4"
            return httpx.Response(204, request=request)
        raise AssertionError(request.url)

    session = await _connected_session(handler)
    paths.clear()
    outcome = await session.submit(
        "datatype delete-draft core.string version=2 expected_revision=4"
    )
    assert outcome is not None and outcome.result.status == "ok"
    assert paths == [
        "/api/v1/core/datatypes",
        f"/api/v1/core/datatypes/{DT}/versions/2",
    ]
    assert [exchange.request.method for exchange in outcome.result.exchanges] == [
        "GET",
        "DELETE",
    ]
    rendered = render_interactive(session, outcome)
    assert "target: core.string" in rendered
    assert '"datatype_id": "' + DT + '"' in rendered
    assert '"version": 2' in rendered
    assert outcome.result.result is None
    await session.close()


@pytest.mark.asyncio
async def test_rf01_nullable_owner_exposes_selected_object_without_recovery_get() -> (
    None
):
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        if request.url.path == "/health/core":
            return _response(request, READY)
        if request.url.path == "/api/v1/core/objects":
            return _response(request, _object_page(CHILD, "child01"))
        if request.url.path == f"/api/v1/core/objects/{CHILD}/owner":
            return httpx.Response(
                200,
                headers={"Content-Type": "application/json"},
                content=b"null",
                request=request,
            )
        raise AssertionError(request.url)

    session = await _connected_session(handler)
    paths.clear()
    outcome = await session.submit("object get-owner child01")
    assert outcome is not None and outcome.result.status == "ok"
    assert paths == ["/api/v1/core/objects", f"/api/v1/core/objects/{CHILD}/owner"]
    assert outcome.result.as_json()["result"] is None
    rendered = render_interactive(session, outcome)
    assert "selector: child01" in rendered
    assert '"child_object_id": "' + CHILD + '"' in rendered
    await session.close()


@pytest.mark.asyncio
async def test_rf01_projection_exposes_resolved_path_and_body_identities() -> None:
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        if request.url.path == "/health/core":
            return _response(request, READY)
        if request.url.path == "/api/v1/core/objects":
            name = request.url.params["canonical_name"]
            if name == "server01":
                return _response(request, _object_page(OBJ, name))
            if name == "child01":
                return _response(request, _object_page(CHILD, name))
        if request.url.path == f"/api/v1/core/objects/{OBJ}/attach":
            return _response(
                request,
                {
                    "slot_declaring_template_id": OT,
                    "slot_name": "member",
                    "child_object_id": CHILD,
                },
            )
        raise AssertionError(request.url)

    session = await _connected_session(handler)
    paths.clear()
    outcome = await session.submit(
        "object attach server01 slot_name=member child_object_id=child01"
    )
    assert outcome is not None and outcome.result.status == "ok"
    assert paths == [
        "/api/v1/core/objects",
        "/api/v1/core/objects",
        f"/api/v1/core/objects/{OBJ}/attach",
    ]
    rendered = render_interactive(session, outcome)
    assert "selector: server01" in rendered
    assert '"parent_object_id": "' + OBJ + '"' in rendered
    assert '"child_object_id": "' + CHILD + '"' in rendered
    assert "slot_declaring_template_id" in rendered
    assert all(path != f"/api/v1/core/objects/{OBJ}" for path in paths)
    await session.close()


@pytest.mark.asyncio
async def test_rf01_exact_uuid_target_is_visible_once_without_lookup_ambiguity() -> (
    None
):
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        if request.url.path == "/health/core":
            return _response(request, READY)
        if request.url.path == f"/api/v1/core/objects/{OBJ}":
            return httpx.Response(204, request=request)
        raise AssertionError(request.url)

    session = await _connected_session(handler)
    paths.clear()
    outcome = await session.submit(f"object delete {OBJ}")
    assert outcome is not None and outcome.result.status == "ok"
    assert paths == [f"/api/v1/core/objects/{OBJ}"]
    rendered = render_interactive(session, outcome)
    assert '"object_id": "' + OBJ + '"' in rendered
    assert rendered.count(OBJ) == 1
    await session.close()


@pytest.mark.asyncio
async def test_rf01_json_contract_remains_primary_only_and_target_metadata_absent() -> (
    None
):
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        if request.url.path == "/health/core":
            return _response(request, READY)
        if request.url.path == "/api/v1/core/datatypes":
            return _response(request, _datatype_page())
        if request.url.path == f"/api/v1/core/datatypes/{DT}":
            return httpx.Response(204, request=request)
        raise AssertionError(request.url)

    session = await _connected_session(handler)
    await session.submit("/output JSON")
    paths.clear()
    outcome = await session.submit("datatype delete core.string")
    assert outcome is not None and outcome.result.status == "ok"
    rendered = render_interactive(session, outcome)
    payload = json.loads(rendered)
    assert set(payload) == {"status", "command", "exchanges", "result", "error"}
    assert payload["command"] == {
        "resource": "datatype",
        "operation": "delete",
        "selector": "core.string",
        "parameters": {},
    }
    assert payload["result"] is None
    assert len(payload["exchanges"]) == 2
    assert "resolved_target" not in rendered
    await session.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["datatype", "object-template", "object"])
async def test_rf02_stable_get_identity_mismatch_fails_before_cache_or_use(
    kind: str,
) -> None:
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        paths.append(path)
        if path == "/health/core":
            return _response(request, READY)
        if kind == "datatype":
            if path == f"/api/v1/core/datatypes/{DT}/versions/1":
                return _response(request, _datatype_version())
            if path == f"/api/v1/core/datatypes/{DT}":
                return _response(request, _datatype(WRONG_DT))
        elif kind == "object-template":
            if path == f"/api/v1/core/objects/{OBJ}":
                return _response(request, _object())
            if path == f"/api/v1/core/object-templates/{OT}":
                return _response(request, _template(WRONG_OT))
        else:
            if path == f"/api/v1/core/objects/{CHILD}/owner":
                return _response(
                    request,
                    {
                        "parent_object_id": OBJ,
                        "slot_declaring_template_id": OT,
                        "slot_name": "member",
                    },
                )
            if path == f"/api/v1/core/objects/{OBJ}":
                return _response(request, _object(WRONG_OBJ))
        raise AssertionError(request.url)

    command, expected_paths = {
        "datatype": (
            f"datatype get-version {DT} version=1",
            [
                f"/api/v1/core/datatypes/{DT}/versions/1",
                f"/api/v1/core/datatypes/{DT}",
            ],
        ),
        "object-template": (
            f"object get {OBJ}",
            [
                f"/api/v1/core/objects/{OBJ}",
                f"/api/v1/core/object-templates/{OT}",
            ],
        ),
        "object": (
            f"object get-owner {CHILD}",
            [
                f"/api/v1/core/objects/{CHILD}/owner",
                f"/api/v1/core/objects/{OBJ}",
            ],
        ),
    }[kind]
    session = await _connected_session(handler)
    paths.clear()
    outcome = await session.submit(command)
    _assert_protocol_failure(session, outcome, paths, expected_paths)
    await session.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("returned_template_id", "returned_version"),
    [(WRONG_OT, 1), (PARENT, 2)],
)
async def test_rf02_exact_version_identity_mismatch_fails_before_cache_or_use(
    returned_template_id: str,
    returned_version: int,
) -> None:
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        paths.append(path)
        if path == "/health/core":
            return _response(request, READY)
        if path == f"/api/v1/core/object-templates/{OT}/versions/2":
            return _response(
                request,
                _template_version(OT, 2, parent_template_id=PARENT, parent_version=1),
            )
        if path == f"/api/v1/core/object-templates/{OT}":
            return _response(request, _template(OT, parent_template_id=PARENT))
        if path == f"/api/v1/core/object-templates/{PARENT}":
            return _response(request, _template(PARENT))
        if path == f"/api/v1/core/object-templates/{PARENT}/versions/1":
            return _response(
                request,
                _template_version(returned_template_id, returned_version),
            )
        raise AssertionError(request.url)

    session = await _connected_session(handler)
    paths.clear()
    outcome = await session.submit(f"object-template get-version {OT} version=2")
    _assert_protocol_failure(
        session,
        outcome,
        paths,
        [
            f"/api/v1/core/object-templates/{OT}/versions/2",
            f"/api/v1/core/object-templates/{OT}",
            f"/api/v1/core/object-templates/{PARENT}",
            f"/api/v1/core/object-templates/{PARENT}/versions/1",
        ],
    )
    await session.close()


@pytest.mark.asyncio
async def test_rf02_same_lineage_different_version_cycle_stops_immediately() -> None:
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        paths.append(path)
        if path == "/health/core":
            return _response(request, READY)
        if path == f"/api/v1/core/object-templates/{OT}/versions/2":
            return _response(
                request,
                _template_version(OT, 2, parent_template_id=OT, parent_version=1),
            )
        if path == f"/api/v1/core/object-templates/{OT}":
            return _response(request, _template(OT, parent_template_id=OT))
        if path == f"/api/v1/core/object-templates/{OT}/versions/1":
            return _response(request, _template_version(OT, 1))
        raise AssertionError(request.url)

    session = await _connected_session(handler)
    paths.clear()
    outcome = await session.submit(f"object-template get-version {OT} version=2")
    _assert_protocol_failure(
        session,
        outcome,
        paths,
        [
            f"/api/v1/core/object-templates/{OT}/versions/2",
            f"/api/v1/core/object-templates/{OT}",
        ],
    )
    await session.close()


@pytest.mark.asyncio
async def test_rf02_multi_lineage_different_version_cycle_stops_before_repeat() -> None:
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        paths.append(path)
        if path == "/health/core":
            return _response(request, READY)
        if path == f"/api/v1/core/object-templates/{OT}/versions/2":
            return _response(
                request,
                _template_version(OT, 2, parent_template_id=PARENT, parent_version=3),
            )
        if path == f"/api/v1/core/object-templates/{OT}":
            return _response(request, _template(OT, parent_template_id=PARENT))
        if path == f"/api/v1/core/object-templates/{PARENT}":
            return _response(request, _template(PARENT, parent_template_id=TARGET))
        if path == f"/api/v1/core/object-templates/{PARENT}/versions/3":
            return _response(
                request,
                _template_version(
                    PARENT, 3, parent_template_id=TARGET, parent_version=1
                ),
            )
        if path == f"/api/v1/core/object-templates/{TARGET}":
            return _response(request, _template(TARGET, parent_template_id=PARENT))
        if path == f"/api/v1/core/object-templates/{TARGET}/versions/1":
            return _response(
                request,
                _template_version(
                    TARGET, 1, parent_template_id=PARENT, parent_version=1
                ),
            )
        if path == f"/api/v1/core/object-templates/{PARENT}/versions/1":
            return _response(request, _template_version(PARENT, 1))
        raise AssertionError(request.url)

    session = await _connected_session(handler)
    paths.clear()
    outcome = await session.submit(f"object-template get-version {OT} version=2")
    _assert_protocol_failure(
        session,
        outcome,
        paths,
        [
            f"/api/v1/core/object-templates/{OT}/versions/2",
            f"/api/v1/core/object-templates/{OT}",
            f"/api/v1/core/object-templates/{PARENT}",
            f"/api/v1/core/object-templates/{PARENT}/versions/3",
            f"/api/v1/core/object-templates/{TARGET}",
            f"/api/v1/core/object-templates/{TARGET}/versions/1",
        ],
    )
    await session.close()


@pytest.mark.asyncio
async def test_rf02_valid_root_lineage_and_repeated_ids_are_memoized_once() -> None:
    paths: list[str] = []
    properties: list[dict[str, object]] = [
        {
            "name": name,
            "position": position,
            "datatype_id": DT,
            "datatype_version": 1,
            "value_mode": "SCALAR",
            "required": False,
        }
        for position, name in enumerate(("hostname", "alias"), start=1)
    ]
    components: list[dict[str, object]] = [
        {"name": name, "position": position, "target_template_id": TARGET}
        for position, name in enumerate(("disk", "backup"), start=1)
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        paths.append(path)
        if path == "/health/core":
            return _response(request, READY)
        if path == f"/api/v1/core/object-templates/{OT}/versions/2":
            return _response(
                request,
                _template_version(
                    OT,
                    2,
                    parent_template_id=PARENT,
                    parent_version=1,
                    properties=properties,
                    components=components,
                ),
            )
        if path == f"/api/v1/core/object-templates/{OT}":
            return _response(request, _template(OT, parent_template_id=PARENT))
        if path == f"/api/v1/core/object-templates/{PARENT}":
            return _response(request, _template(PARENT))
        if path == f"/api/v1/core/object-templates/{PARENT}/versions/1":
            return _response(request, _template_version(PARENT, 1))
        if path == f"/api/v1/core/datatypes/{DT}":
            return _response(request, _datatype())
        if path == f"/api/v1/core/object-templates/{TARGET}":
            return _response(request, _template(TARGET))
        raise AssertionError(request.url)

    session = await _connected_session(handler)
    paths.clear()
    outcome = await session.submit(f"object-template get-version {OT} version=2")
    assert outcome is not None and outcome.result.status == "ok"
    assert paths == [
        f"/api/v1/core/object-templates/{OT}/versions/2",
        f"/api/v1/core/object-templates/{OT}",
        f"/api/v1/core/object-templates/{PARENT}",
        f"/api/v1/core/object-templates/{PARENT}/versions/1",
        f"/api/v1/core/datatypes/{DT}",
        f"/api/v1/core/object-templates/{TARGET}",
    ]
    assert len(outcome.result.exchanges) == len(paths)
    assert session.connection is ConnectionState.CONNECTED
    rendered = render_interactive(session, outcome)
    assert rendered.count("core.string") == 2
    assert rendered.count("infra.root") == 2
    await session.close()
