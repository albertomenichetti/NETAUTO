"""M3-S04 Object trusted projection and cursor-repair evidence."""

import ast
import inspect
import textwrap
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from typing import cast
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import Engine, event, select
from sqlalchemy.ext.asyncio import AsyncEngine

from netauto.application.cursors import encode_cursor
from netauto.application.objects import ObjectService
from netauto.application.relationships import RelationshipService
from netauto.domain.primitives import JsonValue
from netauto.entrypoints.http import build_app
from netauto.persistence.engine import RuntimeContext
from netauto.persistence.lifecycle import LifecycleStore, decode_lifecycle_event
from netauto.persistence.metadata import (
    object_lifecycle_events,
    object_template_components,
    objects,
    relationships,
)
from netauto.persistence.objects import ObjectStore
from netauto.persistence.relationships import RuntimeRelationshipStore
from netauto.settings import Settings


@dataclass(frozen=True, slots=True)
class M3S04Runtime:
    client: httpx.AsyncClient
    engine: AsyncEngine
    database_engine: Engine


@pytest.fixture
async def m3_s04_runtime(
    migrated_database_engine: Engine, test_database_url: str
) -> AsyncIterator[M3S04Runtime]:
    app = build_app(Settings(database_url=test_database_url))
    async with app.router.lifespan_context(app):
        runtime = cast(RuntimeContext, app.state.runtime)
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            yield M3S04Runtime(client, runtime.engine, migrated_database_engine)


async def _template(
    client: httpx.AsyncClient,
    name: str,
    *,
    components: list[dict[str, object]] | None = None,
) -> str:
    created = await client.post(
        "/api/v1/core/object-templates",
        json={
            "namespace": "m3s04",
            "name": name,
            "abstract": False,
            "components": components or [],
        },
    )
    assert created.status_code == 201, created.text
    template_id = cast(str, created.json()["object_template"]["id"])
    published = await client.post(
        f"/api/v1/core/object-templates/{template_id}/versions/1/publish",
        params={"expected_revision": 1},
    )
    assert published.status_code == 200, published.text
    return template_id


async def _object(
    client: httpx.AsyncClient, template_id: str, canonical_name: str
) -> str:
    created = await client.post(
        "/api/v1/core/objects",
        json={"template_id": template_id, "canonical_name": canonical_name},
    )
    assert created.status_code == 201, created.text
    return cast(str, created.json()["id"])


async def _attach(client: httpx.AsyncClient, parent_id: str, child_id: str) -> None:
    attached = await client.post(
        f"/api/v1/core/objects/{parent_id}/attach",
        json={"slot_name": "children", "child_object_id": child_id},
    )
    assert attached.status_code == 200, attached.text


async def _definition(
    client: httpx.AsyncClient, template_id: str, name: str
) -> tuple[str, str]:
    created = await client.post(
        "/api/v1/core/relationship-definitions",
        json={
            "symmetric": True,
            "endpoint_template_ids": [template_id, template_id],
            "name": name,
        },
    )
    assert created.status_code == 201, created.text
    definition_id = cast(str, created.json()["relationship_definition"]["id"])
    published = await client.post(
        f"/api/v1/core/relationship-definitions/{definition_id}/versions/1/publish",
        params={"expected_revision": 1},
    )
    assert published.status_code == 200, published.text
    current = await client.get(f"/api/v1/core/relationship-definitions/{definition_id}")
    assert current.status_code == 200, current.text
    resolution_id = cast(str, current.json()["resolutions"][0]["resolution_id"])
    return definition_id, resolution_id


async def _relationship(
    client: httpx.AsyncClient,
    resolution_id: str,
    from_object_id: str,
    to_object_id: str,
) -> str:
    created = await client.post(
        "/api/v1/core/relationships",
        json={
            "resolution_id": resolution_id,
            "from_object_id": from_object_id,
            "to_object_id": to_object_id,
        },
    )
    assert created.status_code == 201, created.text
    return cast(str, created.json()["id"])


async def _ownership_seed(
    client: httpx.AsyncClient, prefix: str
) -> tuple[str, str, str, list[str]]:
    child_template = await _template(client, f"{prefix}_child")
    parent_template = await _template(
        client,
        f"{prefix}_parent",
        components=[
            {
                "name": "children",
                "position": 1,
                "target_template_id": child_template,
            }
        ],
    )
    parent_a = await _object(client, parent_template, f"{prefix}-parent-a")
    parent_b = await _object(client, parent_template, f"{prefix}-parent-b")
    children = [
        await _object(client, child_template, f"{prefix}-child-{index}")
        for index in range(5)
    ]
    return child_template, parent_template, parent_a, [parent_b, *children]


@pytest.mark.api
@pytest.mark.postgresql
async def test_m3_s04_object_list_and_exact_reads_trust_representable_state(
    m3_s04_runtime: M3S04Runtime,
) -> None:
    client = m3_s04_runtime.client
    template_id = await _template(client, "trusted_object")
    object_ids = [
        await _object(client, template_id, f"trusted-object-{index}")
        for index in range(3)
    ]
    persisted_surprise = {
        "Bad-Key": None,
        "nested": {"empty": [], "mixed": [1, True, {"deep": None}]},
    }
    with m3_s04_runtime.database_engine.begin() as connection:
        connection.execute(
            objects.update()
            .where(objects.c.id == UUID(object_ids[0]))
            .values(properties=persisted_surprise)
        )

    exact = await client.get(f"/api/v1/core/objects/{object_ids[0]}")
    assert exact.status_code == 200, exact.text
    assert exact.json()["properties"] == persisted_surprise

    first = await client.get(
        "/api/v1/core/objects",
        params={"template_id": template_id, "limit": 1},
    )
    cursor = cast(str, first.json()["next_cursor"])
    second = await client.get(
        "/api/v1/core/objects",
        params={"template_id": template_id, "cursor": cursor, "limit": 10},
    )
    traversed = [
        item["id"] for page in (first, second) for item in page.json()["items"]
    ]
    assert set(traversed) == set(object_ids)
    assert len(traversed) == len(set(traversed))

    wrong_filter = await client.get(
        "/api/v1/core/objects",
        params={"canonical_name": "different", "cursor": cursor},
    )
    missing = await client.get(f"/api/v1/core/objects/{uuid4()}")
    invalid_dependency = await client.get(
        "/api/v1/core/objects", params={"template_version": 1}
    )
    for response in (wrong_filter, invalid_dependency):
        assert response.status_code == 400, response.text
    assert missing.status_code == 404

    rejected_mutation = await client.post(
        f"/api/v1/core/objects/{object_ids[1]}/data-change",
        json={"operations": [{"op": "SET", "property": "unknown", "value": 1}]},
    )
    assert rejected_mutation.status_code == 422, rejected_mutation.text
    assert rejected_mutation.json()["code"] == "semantic_validation_failed"


@pytest.mark.api
@pytest.mark.postgresql
async def test_m3_s04_components_and_owner_context_cursor_and_failure_boundaries(
    m3_s04_runtime: M3S04Runtime,
) -> None:
    client = m3_s04_runtime.client
    _, parent_template, parent_a, remaining = await _ownership_seed(client, "ownership")
    parent_b, child_a1, child_a2, child_b1, child_b2, detached = remaining
    for parent_id, child_id in (
        (parent_a, child_a1),
        (parent_a, child_a2),
        (parent_b, child_b1),
        (parent_b, child_b2),
    ):
        await _attach(client, parent_id, child_id)

    empty = await client.get(
        f"/api/v1/core/objects/{parent_a}/components",
        params={"slot_name": "other"},
    )
    missing = await client.get(f"/api/v1/core/objects/{uuid4()}/components")
    assert empty.status_code == 200 and empty.json()["items"] == []
    assert missing.status_code == 404

    first = await client.get(
        f"/api/v1/core/objects/{parent_a}/components",
        params={"slot_name": "children", "limit": 1},
    )
    assert first.status_code == 200, first.text
    cursor = cast(str, first.json()["next_cursor"])
    continued = await client.get(
        f"/api/v1/core/objects/{parent_a}/components",
        params={"slot_name": "children", "cursor": cursor, "limit": 5},
    )
    crossed = await client.get(
        f"/api/v1/core/objects/{parent_b}/components",
        params={"slot_name": "children", "cursor": cursor},
    )
    traversed = [
        item["child_object_id"]
        for page in (first, continued)
        for item in page.json()["items"]
    ]
    assert set(traversed) == {child_a1, child_a2}
    assert len(traversed) == len(set(traversed))
    assert crossed.status_code == 400
    assert crossed.json()["code"] == "invalid_cursor"

    malformed = encode_cursor(
        "object_components",
        {"parent_object_id": parent_a, "slot_name": "children"},
        [123],
    )
    malformed_response = await client.get(
        f"/api/v1/core/objects/{parent_a}/components",
        params={"slot_name": "children", "cursor": malformed},
    )
    assert malformed_response.status_code == 400
    assert malformed_response.json()["code"] == "invalid_cursor"

    detached_owner = await client.get(f"/api/v1/core/objects/{detached}/owner")
    attached_owner = await client.get(f"/api/v1/core/objects/{child_a1}/owner")
    missing_owner = await client.get(f"/api/v1/core/objects/{uuid4()}/owner")
    assert detached_owner.status_code == 200 and detached_owner.json() is None
    assert attached_owner.status_code == 200, attached_owner.text
    assert attached_owner.json() == {
        "parent_object_id": parent_a,
        "slot_declaring_template_id": parent_template,
        "slot_name": "children",
    }
    assert missing_owner.status_code == 404

    with m3_s04_runtime.database_engine.begin() as connection:
        connection.execute(
            object_template_components.delete().where(
                object_template_components.c.template_id == UUID(parent_template),
                object_template_components.c.template_version == 1,
                object_template_components.c.name == "children",
            )
        )
    incomplete_components = await client.get(
        f"/api/v1/core/objects/{parent_a}/components"
    )
    incomplete_owner = await client.get(f"/api/v1/core/objects/{child_a1}/owner")
    for response in (incomplete_components, incomplete_owner):
        assert response.status_code == 500, response.text
        assert response.json()["code"] == "internal_error"


@pytest.mark.api
@pytest.mark.postgresql
async def test_m3_s04_object_lifecycle_trusted_decoder_and_cursor_scope(
    m3_s04_runtime: M3S04Runtime,
) -> None:
    client = m3_s04_runtime.client
    template_id = await _template(client, "lifecycle")
    object_a = await _object(client, template_id, "lifecycle-a")
    object_b = await _object(client, template_id, "lifecycle-b")
    for name in ("lifecycle-a-one", "lifecycle-a-two"):
        renamed = await client.post(
            f"/api/v1/core/objects/{object_a}/rename",
            json={"canonical_name": name},
        )
        assert renamed.status_code == 200, renamed.text

    empty = await client.get(
        f"/api/v1/core/objects/{object_a}/lifecycle-events",
        params={"kind": "ATTACH_TO"},
    )
    missing = await client.get(f"/api/v1/core/objects/{uuid4()}/lifecycle-events")
    assert empty.status_code == 200 and empty.json()["items"] == []
    assert missing.status_code == 404

    first = await client.get(
        f"/api/v1/core/objects/{object_a}/lifecycle-events", params={"limit": 1}
    )
    cursor = cast(str, first.json()["next_cursor"])
    continued = await client.get(
        f"/api/v1/core/objects/{object_a}/lifecycle-events",
        params={"cursor": cursor, "limit": 10},
    )
    crossed = await client.get(
        f"/api/v1/core/objects/{object_b}/lifecycle-events",
        params={"cursor": cursor},
    )
    event_ids = [
        item["id"] for page in (first, continued) for item in page.json()["items"]
    ]
    assert len(event_ids) == 3
    assert len(event_ids) == len(set(event_ids))
    assert crossed.status_code == 400
    assert crossed.json()["code"] == "invalid_cursor"

    historical_surprise: dict[str, JsonValue] = {
        "id": str(uuid4()),
        "canonical_name": "",
        "template_id": template_id,
        "template_version": 0,
        "properties": {
            "Bad-Key": None,
            "nested": [1, True, [], {"deep": None}],
        },
        "extra": "ignored",
    }
    with m3_s04_runtime.database_engine.begin() as connection:
        created_event_id = connection.scalar(
            select(object_lifecycle_events.c.id).where(
                object_lifecycle_events.c.object_id == UUID(object_a),
                object_lifecycle_events.c.kind == "CREATED",
            )
        )
        assert created_event_id is not None
        connection.execute(
            object_lifecycle_events.update()
            .where(object_lifecycle_events.c.id == created_event_id)
            .values(after_state=historical_surprise)
        )
    trusted = await client.get(
        f"/api/v1/core/objects/{object_a}/lifecycle-events",
        params={"kind": "CREATED"},
    )
    assert trusted.status_code == 200, trusted.text
    assert trusted.json()["items"][0]["after"] == {
        key: historical_surprise[key]
        for key in (
            "id",
            "canonical_name",
            "template_id",
            "template_version",
            "properties",
        )
    }

    with m3_s04_runtime.database_engine.begin() as connection:
        connection.execute(
            object_lifecycle_events.update()
            .where(object_lifecycle_events.c.id == created_event_id)
            .values(after_state={"canonical_name": "missing-required-fields"})
        )
    undecodable = await client.get(
        f"/api/v1/core/objects/{object_a}/lifecycle-events",
        params={"kind": "CREATED"},
    )
    assert undecodable.status_code == 500
    assert undecodable.json()["code"] == "internal_error"


@pytest.mark.api
@pytest.mark.postgresql
async def test_m3_s04_object_relationship_page_deduplicates_and_binds_target(
    m3_s04_runtime: M3S04Runtime,
) -> None:
    client = m3_s04_runtime.client
    template_id = await _template(client, "relationship_object")
    object_ids = [
        await _object(client, template_id, f"relationship-object-{index}")
        for index in range(6)
    ]
    object_a, object_b, object_c, object_d, object_e, detached = object_ids
    definition_id, resolution_id = await _definition(client, template_id, "related_to")
    relationship_ids = [
        await _relationship(client, resolution_id, source, destination)
        for source, destination in (
            (object_a, object_c),
            (object_a, object_d),
            (object_a, object_e),
            (object_b, object_c),
            (object_b, object_d),
        )
    ]
    with m3_s04_runtime.database_engine.begin() as connection:
        connection.execute(
            relationships.update()
            .where(relationships.c.id == UUID(relationship_ids[0]))
            .values(properties={"historical-surprise": None})
        )

    empty = await client.get(f"/api/v1/core/objects/{detached}/relationships")
    missing = await client.get(f"/api/v1/core/objects/{uuid4()}/relationships")
    assert empty.status_code == 200 and empty.json()["items"] == []
    assert missing.status_code == 404

    first = await client.get(
        f"/api/v1/core/objects/{object_a}/relationships", params={"limit": 1}
    )
    assert first.status_code == 200, first.text
    cursor = cast(str, first.json()["next_cursor"])
    continued = await client.get(
        f"/api/v1/core/objects/{object_a}/relationships",
        params={"cursor": cursor, "limit": 10},
    )
    crossed = await client.get(
        f"/api/v1/core/objects/{object_b}/relationships",
        params={"cursor": cursor},
    )
    views = [
        (
            item["relationship_id"],
            item["destination_object_id"],
            item["name"],
        )
        for page in (first, continued)
        for item in page.json()["items"]
    ]
    assert len(views) == 3
    assert len(views) == len(set(views))
    assert {item[0] for item in views} == set(relationship_ids[:3])
    assert crossed.status_code == 400
    assert crossed.json()["code"] == "invalid_cursor"

    malformed = encode_cursor(
        "object_relationships",
        {
            "object_id": object_a,
            "relationship_definition_id": None,
            "name": None,
        },
        [1, 2, 3],
    )
    malformed_response = await client.get(
        f"/api/v1/core/objects/{object_a}/relationships",
        params={"cursor": malformed},
    )
    assert malformed_response.status_code == 400
    assert malformed_response.json()["code"] == "invalid_cursor"

    filtered = await client.get(
        f"/api/v1/core/objects/{object_a}/relationships",
        params={"relationship_definition_id": definition_id},
    )
    assert filtered.status_code == 200
    assert len(filtered.json()["items"]) == 3

    rejected_mutation = await client.post(
        "/api/v1/core/relationships",
        json={
            "resolution_id": resolution_id,
            "from_object_id": object_b,
            "to_object_id": object_e,
            "properties": {"unknown": 1},
        },
    )
    assert rejected_mutation.status_code == 422, rejected_mutation.text
    assert rejected_mutation.json()["code"] == "semantic_validation_failed"


@pytest.mark.api
@pytest.mark.postgresql
async def test_m3_s04_six_object_gets_each_execute_one_business_statement(
    m3_s04_runtime: M3S04Runtime,
) -> None:
    client = m3_s04_runtime.client
    child_template, parent_template, parent, remaining = await _ownership_seed(
        client, "statement"
    )
    other_parent, child, *_ = remaining
    await _attach(client, parent, child)
    _, resolution_id = await _definition(client, parent_template, "statement_link")
    await _relationship(client, resolution_id, parent, other_parent)
    assert child_template

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

    routes = {
        "OBJ-GET-01": "/api/v1/core/objects?limit=1",
        "OBJ-GET-02": f"/api/v1/core/objects/{parent}",
        "OBJ-GET-03": f"/api/v1/core/objects/{parent}/components?limit=1",
        "OBJ-GET-04": f"/api/v1/core/objects/{child}/owner",
        "OBJ-GET-05": f"/api/v1/core/objects/{parent}/lifecycle-events?limit=1",
        "OBJ-GET-06": f"/api/v1/core/objects/{parent}/relationships?limit=1",
    }
    counts: dict[str, int] = {}
    event.listen(
        m3_s04_runtime.engine.sync_engine,
        "before_cursor_execute",
        observe_statement,
    )
    try:
        for route_id, path in routes.items():
            statements.clear()
            response = await client.get(path)
            assert response.status_code == 200, (route_id, response.text)
            counts[route_id] = len(statements)
            assert len(statements) == 1, (route_id, statements)
            assert statements[0].lstrip().upper().startswith(("SELECT", "WITH"))
    finally:
        event.remove(
            m3_s04_runtime.engine.sync_engine,
            "before_cursor_execute",
            observe_statement,
        )
    assert counts == {route_id: 1 for route_id in routes}


def test_m3_s04_get_paths_have_no_read_certification_dependencies() -> None:
    forbidden_calls = {
        "_schema_specs",
        "_validate_persisted_object",
        "_validated_many",
        "coherent_read",
        "resolve_exact_effective_schema",
    }
    methods: tuple[Callable[..., object], ...] = (
        ObjectService.list_objects,
        ObjectService.get,
        ObjectService.list_components,
        ObjectService.get_owner,
        ObjectService.list_object_events,
        RelationshipService.list_for_object,
    )
    for method in methods:
        tree = ast.parse(textwrap.dedent(inspect.getsource(method)))
        called = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        } | {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        assert called.isdisjoint(forbidden_calls), method.__name__

    component_source = inspect.getsource(ObjectStore.list_component_projections)
    owner_source = inspect.getsource(ObjectStore.get_owner_projection)
    lifecycle_source = inspect.getsource(LifecycleStore.list_events_for_object)
    relationship_source = inspect.getsource(RuntimeRelationshipStore.list_object_views)
    decoder_source = inspect.getsource(decode_lifecycle_event)
    assert "exact_chain" in component_source and "component_page" in component_source
    assert "exact_chain" in owner_source
    assert "object_lifecycle_page" in lifecycle_source
    assert ".distinct()" in relationship_source
    assert "_validated_many" not in relationship_source
    assert "properties ==" not in decoder_source
    assert "template_version <=" not in decoder_source
