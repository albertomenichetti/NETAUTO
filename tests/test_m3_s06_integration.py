"""M3-S06 integrated HTTP, cursor, statement, and snapshot evidence."""

import asyncio
import threading
from collections.abc import AsyncIterator, Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import cast
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import Engine, event
from sqlalchemy.ext.asyncio import AsyncEngine

from netauto.application.cursors import encode_cursor
from netauto.domain.primitives import JsonValue
from netauto.domain.relationships import RelationshipDefinition
from netauto.entrypoints.http import build_app
from netauto.persistence.engine import RuntimeContext
from netauto.persistence.metadata import (
    relationship_definitions,
    relationship_resolutions,
)
from netauto.persistence.relationships import RelationshipDefinitionStore
from netauto.settings import Settings
from tests.support.m3_evidence import (
    M3_CURSOR_ROUTE_CENSUS,
    M3_GET_ROUTE_CENSUS,
)


@dataclass(frozen=True, slots=True)
class M3S06Runtime:
    client: httpx.AsyncClient
    engine: AsyncEngine
    database_engine: Engine


@dataclass(frozen=True, slots=True)
class M3S06Seed:
    datatype_ids: tuple[str, str, str]
    template_ids: tuple[str, str, str]
    subject_template_id: str
    child_template_id: str
    object_ids: tuple[str, str, str, str, str]
    child_ids: tuple[str, str, str, str]
    definition_ids: tuple[str, str, str]
    resolution_ids: tuple[str, str, str]
    relationship_ids: tuple[str, str, str]


@dataclass(frozen=True, slots=True)
class RequestTarget:
    path: str
    params: dict[str, str | int]


PageKey = tuple[str | int, ...]


@dataclass(frozen=True, slots=True)
class CursorCase:
    route_id: str
    path: str
    params: dict[str, str]
    filters: dict[str, JsonValue]
    item_key: Callable[[dict[str, object]], PageKey]
    malformed_key: list[JsonValue]
    changed_filter: dict[str, str] | None = None
    alternate_path: str | None = None


@pytest.fixture
async def m3_s06_runtime(
    migrated_database_engine: Engine, test_database_url: str
) -> AsyncIterator[M3S06Runtime]:
    app = build_app(Settings(database_url=test_database_url))
    async with app.router.lifespan_context(app):
        runtime = cast(RuntimeContext, app.state.runtime)
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            yield M3S06Runtime(client, runtime.engine, migrated_database_engine)


async def _datatype(client: httpx.AsyncClient, name: str) -> str:
    response = await client.post(
        "/api/v1/core/datatypes",
        json={
            "namespace": "m3s06",
            "name": name,
            "base_type": "core.integer",
        },
    )
    assert response.status_code == 201, response.text
    return cast(str, response.json()["datatype"]["id"])


async def _template(
    client: httpx.AsyncClient,
    name: str,
    *,
    components: list[dict[str, object]] | None = None,
) -> str:
    response = await client.post(
        "/api/v1/core/object-templates",
        json={
            "namespace": "m3s06",
            "name": name,
            "abstract": False,
            "components": components or [],
        },
    )
    assert response.status_code == 201, response.text
    return cast(str, response.json()["object_template"]["id"])


async def _publish_template(client: httpx.AsyncClient, template_id: str) -> None:
    response = await client.post(
        f"/api/v1/core/object-templates/{template_id}/versions/1/publish",
        params={"expected_revision": 1},
    )
    assert response.status_code == 200, response.text


async def _object(client: httpx.AsyncClient, template_id: str, name: str) -> str:
    response = await client.post(
        "/api/v1/core/objects",
        json={"template_id": template_id, "canonical_name": name},
    )
    assert response.status_code == 201, response.text
    return cast(str, response.json()["id"])


async def _definition(
    client: httpx.AsyncClient, template_id: str, name: str
) -> tuple[str, str]:
    response = await client.post(
        "/api/v1/core/relationship-definitions",
        json={
            "symmetric": True,
            "endpoint_template_ids": [template_id, template_id],
            "name": name,
        },
    )
    assert response.status_code == 201, response.text
    definition_id = cast(str, response.json()["relationship_definition"]["id"])
    published = await client.post(
        f"/api/v1/core/relationship-definitions/{definition_id}/versions/1/publish",
        params={"expected_revision": 1},
    )
    assert published.status_code == 200, published.text
    current = await client.get(f"/api/v1/core/relationship-definitions/{definition_id}")
    assert current.status_code == 200, current.text
    resolution_id = cast(str, current.json()["resolutions"][0]["resolution_id"])
    return definition_id, resolution_id


async def _seed(client: httpx.AsyncClient) -> M3S06Seed:
    datatype_ids = cast(
        tuple[str, str, str],
        tuple([await _datatype(client, name) for name in ("alpha", "beta", "gamma")]),
    )
    published_datatype = await client.post(
        f"/api/v1/core/datatypes/{datatype_ids[0]}/versions/1/publish",
        params={"expected_revision": 1},
    )
    assert published_datatype.status_code == 200, published_datatype.text
    for _ in range(2):
        created = await client.post(
            f"/api/v1/core/datatypes/{datatype_ids[0]}/create-next",
            json={"source_version": 1},
        )
        assert created.status_code == 201, created.text

    child_template_id = await _template(client, "child")
    alternate_template_id = await _template(client, "alternate")
    await _publish_template(client, child_template_id)
    await _publish_template(client, alternate_template_id)
    subject_template_id = await _template(
        client,
        "subject",
        components=[
            {
                "name": "children",
                "position": 1,
                "target_template_id": child_template_id,
            }
        ],
    )
    await _publish_template(client, subject_template_id)
    for _ in range(2):
        created = await client.post(
            f"/api/v1/core/object-templates/{subject_template_id}/create-next",
            json={"source_version": 1},
        )
        assert created.status_code == 201, created.text

    definitions = tuple(
        [
            await _definition(client, subject_template_id, name)
            for name in ("link_alpha", "link_beta", "link_gamma")
        ]
    )
    definition_ids = cast(tuple[str, str, str], tuple(item[0] for item in definitions))
    resolution_ids = cast(tuple[str, str, str], tuple(item[1] for item in definitions))
    for _ in range(2):
        created = await client.post(
            f"/api/v1/core/relationship-definitions/{definition_ids[0]}/create-next",
            json={"source_version": 1},
        )
        assert created.status_code == 201, created.text

    object_ids = cast(
        tuple[str, str, str, str, str],
        tuple(
            [
                await _object(client, subject_template_id, f"subject-{suffix}")
                for suffix in ("a", "b", "c", "d", "e")
            ]
        ),
    )
    child_ids = cast(
        tuple[str, str, str, str],
        tuple(
            [
                await _object(client, child_template_id, f"child-{suffix}")
                for suffix in ("a", "b", "c", "detached")
            ]
        ),
    )
    for child_id in child_ids[:3]:
        attached = await client.post(
            f"/api/v1/core/objects/{object_ids[0]}/attach",
            json={"slot_name": "children", "child_object_id": child_id},
        )
        assert attached.status_code == 200, attached.text

    relationship_ids: list[str] = []
    for resolution_id, destination_id in zip(
        resolution_ids, object_ids[1:4], strict=True
    ):
        created = await client.post(
            "/api/v1/core/relationships",
            json={
                "resolution_id": resolution_id,
                "from_object_id": object_ids[0],
                "to_object_id": destination_id,
            },
        )
        assert created.status_code == 201, created.text
        relationship_ids.append(cast(str, created.json()["id"]))

    for index in range(3):
        renamed = await client.post(
            f"/api/v1/core/objects/{object_ids[0]}/rename",
            json={"canonical_name": f"subject-a-renamed-{index}"},
        )
        assert renamed.status_code == 200, renamed.text

    return M3S06Seed(
        datatype_ids,
        (child_template_id, alternate_template_id, subject_template_id),
        subject_template_id,
        child_template_id,
        object_ids,
        child_ids,
        definition_ids,
        resolution_ids,
        cast(tuple[str, str, str], tuple(relationship_ids)),
    )


def _targets(seed: M3S06Seed) -> dict[str, RequestTarget]:
    datatype_id = seed.datatype_ids[0]
    template_id = seed.subject_template_id
    object_id = seed.object_ids[0]
    definition_id = seed.definition_ids[0]
    return {
        "DT-GET-01": RequestTarget(
            "/api/v1/core/datatypes", {"namespace": "m3s06", "limit": 2}
        ),
        "DT-GET-02": RequestTarget(f"/api/v1/core/datatypes/{datatype_id}", {}),
        "DT-GET-03": RequestTarget(
            f"/api/v1/core/datatypes/{datatype_id}/versions", {"limit": 2}
        ),
        "DT-GET-04": RequestTarget(
            f"/api/v1/core/datatypes/{datatype_id}/versions/1", {}
        ),
        "OT-GET-01": RequestTarget(
            "/api/v1/core/object-templates", {"namespace": "m3s06", "limit": 2}
        ),
        "OT-GET-02": RequestTarget(f"/api/v1/core/object-templates/{template_id}", {}),
        "OT-GET-03": RequestTarget(
            f"/api/v1/core/object-templates/{template_id}/versions", {"limit": 2}
        ),
        "OT-GET-04": RequestTarget(
            f"/api/v1/core/object-templates/{template_id}/versions/1", {}
        ),
        "OT-GET-05": RequestTarget(
            f"/api/v1/core/object-templates/{template_id}/versions/1/effective-schema",
            {},
        ),
        "OT-GET-06": RequestTarget(
            f"/api/v1/core/object-templates/{template_id}/relationship-capabilities",
            {"limit": 2},
        ),
        "OBJ-GET-01": RequestTarget(
            "/api/v1/core/objects", {"template_id": template_id, "limit": 2}
        ),
        "OBJ-GET-02": RequestTarget(f"/api/v1/core/objects/{object_id}", {}),
        "OBJ-GET-03": RequestTarget(
            f"/api/v1/core/objects/{object_id}/components",
            {"slot_name": "children", "limit": 2},
        ),
        "OBJ-GET-04": RequestTarget(
            f"/api/v1/core/objects/{seed.child_ids[0]}/owner", {}
        ),
        "OBJ-GET-05": RequestTarget(
            f"/api/v1/core/objects/{object_id}/lifecycle-events", {"limit": 2}
        ),
        "OBJ-GET-06": RequestTarget(
            f"/api/v1/core/objects/{object_id}/relationships", {"limit": 2}
        ),
        "RD-GET-01": RequestTarget(
            "/api/v1/core/relationship-definitions", {"limit": 2}
        ),
        "RD-GET-02": RequestTarget(
            f"/api/v1/core/relationship-definitions/{definition_id}", {}
        ),
        "RD-GET-03": RequestTarget(
            f"/api/v1/core/relationship-definitions/{definition_id}/versions",
            {"limit": 2},
        ),
        "RD-GET-04": RequestTarget(
            f"/api/v1/core/relationship-definitions/{definition_id}/versions/1",
            {},
        ),
        "REL-GET-01": RequestTarget(
            f"/api/v1/core/relationships/{seed.relationship_ids[0]}", {}
        ),
        "LC-GET-01": RequestTarget(
            "/api/v1/core/lifecycle-events",
            {"object_id": object_id, "limit": 2},
        ),
    }


def _cursor_cases(seed: M3S06Seed) -> tuple[CursorCase, ...]:
    object_id = seed.object_ids[0]
    other_object_id = seed.object_ids[1]
    datatype_id = seed.datatype_ids[0]
    template_id = seed.subject_template_id
    definition_id = seed.definition_ids[0]
    lifecycle_global_filters: dict[str, JsonValue] = {
        "kind": None,
        "object_id": object_id,
        "destination_object_id": None,
        "relationship_id": None,
        "relationship_definition_id": None,
        "relationship_name": None,
        "occurred_from": None,
        "occurred_to": None,
        "involving_object_id": None,
    }
    lifecycle_object_filters = dict(lifecycle_global_filters)
    lifecycle_object_filters["object_id"] = None
    lifecycle_object_filters["involving_object_id"] = object_id
    return (
        CursorCase(
            "DT-GET-01",
            "/api/v1/core/datatypes",
            {"namespace": "m3s06"},
            {"namespace": "m3s06", "name": None},
            lambda item: (cast(str, item["namespace"]), cast(str, item["name"])),
            ["only-one-part"],
            {"namespace": "other"},
        ),
        CursorCase(
            "DT-GET-03",
            f"/api/v1/core/datatypes/{datatype_id}/versions",
            {},
            {"datatype_id": datatype_id, "status": None},
            lambda item: (cast(int, item["version"]),),
            ["not-an-integer"],
            {"status": "DRAFT"},
            f"/api/v1/core/datatypes/{seed.datatype_ids[1]}/versions",
        ),
        CursorCase(
            "OT-GET-01",
            "/api/v1/core/object-templates",
            {"namespace": "m3s06"},
            {
                "namespace": "m3s06",
                "name": None,
                "abstract": None,
                "parent_template_id": None,
                "parent_filter_set": False,
            },
            lambda item: (cast(str, item["namespace"]), cast(str, item["name"])),
            ["only-one-part"],
            {"namespace": "other"},
        ),
        CursorCase(
            "OT-GET-03",
            f"/api/v1/core/object-templates/{template_id}/versions",
            {},
            {"template_id": template_id, "status": None},
            lambda item: (cast(int, item["version"]),),
            ["not-an-integer"],
            {"status": "DRAFT"},
            f"/api/v1/core/object-templates/{seed.template_ids[0]}/versions",
        ),
        CursorCase(
            "OT-GET-06",
            f"/api/v1/core/object-templates/{template_id}/relationship-capabilities",
            {},
            {"template_id": template_id, "name": None},
            lambda item: (cast(str, item["resolution_id"]),),
            ["not-a-uuid"],
            {"name": "other"},
            (
                f"/api/v1/core/object-templates/{seed.template_ids[0]}"
                "/relationship-capabilities"
            ),
        ),
        CursorCase(
            "OBJ-GET-01",
            "/api/v1/core/objects",
            {"template_id": template_id},
            {
                "template_id": template_id,
                "template_version": None,
                "canonical_name": None,
            },
            lambda item: (cast(str, item["id"]),),
            ["not-a-uuid"],
            {"canonical_name": "other"},
        ),
        CursorCase(
            "OBJ-GET-03",
            f"/api/v1/core/objects/{object_id}/components",
            {"slot_name": "children"},
            {"parent_object_id": object_id, "slot_name": "children"},
            lambda item: (cast(str, item["child_object_id"]),),
            ["not-a-uuid"],
            {"slot_name": "other"},
            f"/api/v1/core/objects/{other_object_id}/components",
        ),
        CursorCase(
            "OBJ-GET-06",
            f"/api/v1/core/objects/{object_id}/relationships",
            {},
            {
                "object_id": object_id,
                "relationship_definition_id": None,
                "name": None,
            },
            lambda item: (
                cast(str, item["relationship_id"]),
                cast(str, item["destination_object_id"]),
                cast(str, item["name"]),
            ),
            ["not-a-complete-key"],
            {"relationship_definition_id": seed.definition_ids[0]},
            f"/api/v1/core/objects/{other_object_id}/relationships",
        ),
        CursorCase(
            "OBJ-GET-05",
            f"/api/v1/core/objects/{object_id}/lifecycle-events",
            {},
            lifecycle_object_filters,
            lambda item: (cast(str, item["occurred_at"]), cast(str, item["id"])),
            [1, "not-a-uuid"],
            {"kind": "RENAME"},
            f"/api/v1/core/objects/{other_object_id}/lifecycle-events",
        ),
        CursorCase(
            "RD-GET-01",
            "/api/v1/core/relationship-definitions",
            {},
            {},
            lambda item: (cast(str, item["id"]),),
            ["not-a-uuid"],
        ),
        CursorCase(
            "RD-GET-03",
            f"/api/v1/core/relationship-definitions/{definition_id}/versions",
            {},
            {"definition_id": definition_id, "status": None},
            lambda item: (cast(int, item["version"]),),
            ["not-an-integer"],
            {"status": "DRAFT"},
            (
                "/api/v1/core/relationship-definitions/"
                f"{seed.definition_ids[1]}/versions"
            ),
        ),
        CursorCase(
            "LC-GET-01",
            "/api/v1/core/lifecycle-events",
            {"object_id": object_id},
            lifecycle_global_filters,
            lambda item: (cast(str, item["occurred_at"]), cast(str, item["id"])),
            [1, "not-a-uuid"],
            {"object_id": other_object_id},
        ),
    )


def _assert_failure(response: httpx.Response, status: int, code: str) -> None:
    assert response.status_code == status, response.text
    assert response.json()["code"] == code


@pytest.mark.api
@pytest.mark.postgresql
async def test_m3_ver_04_05_integrated_success_and_failure_matrix(
    m3_s06_runtime: M3S06Runtime,
) -> None:
    client = m3_s06_runtime.client
    seed = await _seed(client)
    targets = _targets(seed)
    assert set(targets) == set(M3_GET_ROUTE_CENSUS)
    for route_id, target in targets.items():
        response = await client.get(target.path, params=target.params)
        assert response.status_code == 200, (route_id, response.text)
        assert set(response.json()) == M3_GET_ROUTE_CENSUS[route_id].fields

    unknown_queries = (
        f"/api/v1/core/datatypes/{seed.datatype_ids[0]}",
        f"/api/v1/core/object-templates/{seed.subject_template_id}",
        f"/api/v1/core/objects/{seed.object_ids[0]}",
        f"/api/v1/core/relationship-definitions/{seed.definition_ids[0]}",
        f"/api/v1/core/relationships/{seed.relationship_ids[0]}",
    )
    for path in unknown_queries:
        _assert_failure(
            await client.get(path, params={"expand": "anything"}),
            400,
            "invalid_request",
        )

    repeated_queries = (
        "/api/v1/core/datatypes",
        "/api/v1/core/object-templates",
        "/api/v1/core/objects",
        "/api/v1/core/relationship-definitions",
        "/api/v1/core/lifecycle-events",
    )
    for path in repeated_queries:
        _assert_failure(
            await client.get(path, params=[("limit", "1"), ("limit", "2")]),
            400,
            "invalid_request",
        )

    malformed_carriers = (
        "/api/v1/core/datatypes/not-a-uuid",
        "/api/v1/core/object-templates/not-a-uuid",
        "/api/v1/core/objects/not-a-uuid",
        "/api/v1/core/relationship-definitions/not-a-uuid",
        "/api/v1/core/relationships/not-a-uuid",
        "/api/v1/core/lifecycle-events?object_id=not-a-uuid",
    )
    for path in malformed_carriers:
        _assert_failure(await client.get(path), 400, "invalid_request")

    missing_id = uuid4()
    missing_paths = (
        f"/api/v1/core/datatypes/{missing_id}",
        f"/api/v1/core/object-templates/{missing_id}",
        f"/api/v1/core/objects/{missing_id}",
        f"/api/v1/core/relationship-definitions/{missing_id}",
        f"/api/v1/core/relationships/{missing_id}",
    )
    for path in missing_paths:
        _assert_failure(await client.get(path), 404, "resource_not_found")

    nested_parent_or_child_missing = (
        f"/api/v1/core/datatypes/{missing_id}/versions",
        f"/api/v1/core/datatypes/{seed.datatype_ids[0]}/versions/999",
        f"/api/v1/core/object-templates/{missing_id}/versions",
        f"/api/v1/core/object-templates/{seed.subject_template_id}/versions/999",
        f"/api/v1/core/relationship-definitions/{missing_id}/versions",
        (
            "/api/v1/core/relationship-definitions/"
            f"{seed.definition_ids[0]}/versions/999"
        ),
    )
    for path in nested_parent_or_child_missing:
        _assert_failure(await client.get(path), 404, "resource_not_found")

    empty_pages = (
        await client.get(
            f"/api/v1/core/datatypes/{seed.datatype_ids[1]}/versions",
            params={"status": "PUBLISHED"},
        ),
        await client.get("/api/v1/core/objects", params={"canonical_name": "absent"}),
        await client.get(
            f"/api/v1/core/objects/{seed.object_ids[1]}/components",
            params={"slot_name": "children"},
        ),
    )
    for response in empty_pages:
        assert response.status_code == 200, response.text
        assert response.json() == {"items": [], "next_cursor": None}

    detached = await client.get(f"/api/v1/core/objects/{seed.child_ids[3]}/owner")
    missing_owner = await client.get(f"/api/v1/core/objects/{missing_id}/owner")
    assert detached.status_code == 200 and detached.json() is None
    _assert_failure(missing_owner, 404, "resource_not_found")


@pytest.mark.api
@pytest.mark.postgresql
async def test_m3_ver_09_12_complete_cursor_matrix(
    m3_s06_runtime: M3S06Runtime,
) -> None:
    client = m3_s06_runtime.client
    seed = await _seed(client)
    cases = _cursor_cases(seed)
    assert {case.route_id for case in cases} == set(M3_CURSOR_ROUTE_CENSUS)
    assert len(cases) == 12

    cursors: dict[str, str] = {}
    baselines: dict[str, list[PageKey]] = {}
    first_keys: dict[str, list[PageKey]] = {}
    for case in cases:
        baseline = await client.get(case.path, params={**case.params, "limit": "100"})
        assert baseline.status_code == 200, (case.route_id, baseline.text)
        baseline_keys = [case.item_key(item) for item in baseline.json()["items"]]
        assert len(baseline_keys) >= 3, case.route_id
        expected_reverse = M3_CURSOR_ROUTE_CENSUS[case.route_id].order == "DESC"
        assert baseline_keys == sorted(baseline_keys, reverse=expected_reverse)
        baselines[case.route_id] = baseline_keys

        first = await client.get(case.path, params={**case.params, "limit": "1"})
        assert first.status_code == 200, (case.route_id, first.text)
        first_keys[case.route_id] = [
            case.item_key(item) for item in first.json()["items"]
        ]
        cursors[case.route_id] = cast(str, first.json()["next_cursor"])
        assert cursors[case.route_id]

    for index, case in enumerate(cases):
        traversed = list(first_keys[case.route_id])
        cursor: str | None = cursors[case.route_id]
        while cursor is not None:
            continued = await client.get(
                case.path,
                params={**case.params, "cursor": cursor, "limit": "2"},
            )
            assert continued.status_code == 200, (case.route_id, continued.text)
            traversed.extend(case.item_key(item) for item in continued.json()["items"])
            cursor = cast(str | None, continued.json()["next_cursor"])
        assert traversed == baselines[case.route_id]
        assert len(traversed) == len(set(traversed))

        if case.changed_filter is not None:
            changed = await client.get(
                case.path,
                params={
                    **case.params,
                    **case.changed_filter,
                    "cursor": cursors[case.route_id],
                },
            )
            _assert_failure(changed, 400, "invalid_cursor")
        if case.alternate_path is not None:
            changed_path = await client.get(
                case.alternate_path,
                params={**case.params, "cursor": cursors[case.route_id]},
            )
            _assert_failure(changed_path, 400, "invalid_cursor")

        incompatible_case = cases[(index + 1) % len(cases)]
        incompatible = await client.get(
            case.path,
            params={
                **case.params,
                "cursor": cursors[incompatible_case.route_id],
            },
        )
        _assert_failure(incompatible, 400, "invalid_cursor")
        _assert_failure(
            await client.get(case.path, params={**case.params, "cursor": "***"}),
            400,
            "invalid_cursor",
        )
        wrong_key = encode_cursor(
            M3_CURSOR_ROUTE_CENSUS[case.route_id].codec_route,
            case.filters,
            case.malformed_key,
        )
        malformed = await client.get(
            case.path, params={**case.params, "cursor": wrong_key}
        )
        _assert_failure(malformed, 400, "invalid_cursor")


@pytest.mark.api
@pytest.mark.postgresql
async def test_m3_ver_19_all_gets_execute_one_business_statement(
    m3_s06_runtime: M3S06Runtime,
) -> None:
    client = m3_s06_runtime.client
    seed = await _seed(client)
    targets = _targets(seed)
    statements: list[str] = []

    def observe_statement(
        connection: object,
        cursor: object,
        statement: str,
        parameters: object,
        context: object,
        executemany: bool,
    ) -> None:
        del connection, cursor, parameters, context, executemany
        statements.append(statement)

    counts: dict[str, int] = {}
    event.listen(
        m3_s06_runtime.engine.sync_engine,
        "before_cursor_execute",
        observe_statement,
    )
    try:
        for route_id, target in targets.items():
            statements.clear()
            response = await client.get(target.path, params=target.params)
            assert response.status_code == 200, (route_id, response.text)
            assert set(response.json()) == M3_GET_ROUTE_CENSUS[route_id].fields
            counts[route_id] = len(statements)
            assert len(statements) == 1, (route_id, statements)
            assert statements[0].lstrip().upper().startswith(("SELECT", "WITH"))
    finally:
        event.remove(
            m3_s06_runtime.engine.sync_engine,
            "before_cursor_execute",
            observe_statement,
        )
    assert counts == {route_id: 1 for route_id in M3_GET_ROUTE_CENSUS}


async def _snapshot_definition(
    client: httpx.AsyncClient, prefix: str
) -> tuple[str, tuple[str, str]]:
    first_template = await _template(client, f"{prefix}_first")
    second_template = await _template(client, f"{prefix}_second")
    response = await client.post(
        "/api/v1/core/relationship-definitions",
        json={
            "symmetric": True,
            "endpoint_template_ids": [first_template, second_template],
            "name": "before",
        },
    )
    assert response.status_code == 201, response.text
    definition = cast(dict[str, object], response.json()["relationship_definition"])
    resolutions = cast(list[dict[str, str]], definition["resolutions"])
    assert len(resolutions) == 2
    return cast(str, definition["id"]), (
        resolutions[0]["resolution_id"],
        resolutions[1]["resolution_id"],
    )


@pytest.mark.parametrize("interleaving", ["AFTER", "BEFORE"])
@pytest.mark.api
@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_m3_ver_19_snapshot_is_complete_before_or_after(
    m3_s06_runtime: M3S06Runtime,
    monkeypatch: pytest.MonkeyPatch,
    interleaving: str,
) -> None:
    client = m3_s06_runtime.client
    definition_id, resolution_ids = await _snapshot_definition(
        client, f"snapshot_{interleaving.lower()}"
    )
    reader_reached = threading.Event()
    writer_committed = threading.Event()

    def write_after() -> None:
        assert reader_reached.wait(timeout=10), "reader never reached snapshot cut"
        with m3_s06_runtime.database_engine.begin() as connection:
            connection.execute(
                relationship_definitions.update()
                .where(relationship_definitions.c.id == UUID(definition_id))
                .values(symmetric=False)
            )
            connection.execute(
                relationship_resolutions.update()
                .where(
                    relationship_resolutions.c.id.in_(
                        tuple(UUID(value) for value in resolution_ids)
                    )
                )
                .values(name="after")
            )
        writer_committed.set()

    observer: Callable[..., None] | None = None
    armed = False
    if interleaving == "AFTER":

        def before_execute(
            connection: object,
            cursor: object,
            statement: str,
            parameters: object,
            context: object,
            executemany: bool,
        ) -> None:
            del connection, cursor, parameters, context, executemany
            if armed and "relationship_definitions" in statement:
                reader_reached.set()
                assert writer_committed.wait(timeout=10), "writer did not commit"

        observer = before_execute
        event.listen(
            m3_s06_runtime.engine.sync_engine,
            "before_cursor_execute",
            observer,
        )
    else:
        original_get = RelationshipDefinitionStore.get

        async def pause_after_execute(
            store: RelationshipDefinitionStore, target_id: UUID
        ) -> RelationshipDefinition | None:
            value = await original_get(store, target_id)
            reader_reached.set()
            committed = await asyncio.to_thread(writer_committed.wait, 10)
            assert committed, "writer did not commit"
            return value

        monkeypatch.setattr(RelationshipDefinitionStore, "get", pause_after_execute)

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            writer = executor.submit(write_after)
            armed = True
            response = await client.get(
                f"/api/v1/core/relationship-definitions/{definition_id}"
            )
            writer.result(timeout=10)
    finally:
        if observer is not None:
            event.remove(
                m3_s06_runtime.engine.sync_engine,
                "before_cursor_execute",
                observer,
            )

    assert response.status_code == 200, response.text
    expected_symmetric = interleaving != "AFTER"
    expected_name = "before" if interleaving == "BEFORE" else "after"
    assert response.json()["symmetric"] is expected_symmetric
    assert {item["name"] for item in response.json()["resolutions"]} == {expected_name}
