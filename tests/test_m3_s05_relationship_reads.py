"""M3-S05 RelationshipDefinition, Relationship, and lifecycle read evidence."""

import ast
import inspect
import textwrap
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import Engine, event
from sqlalchemy.ext.asyncio import AsyncEngine

from netauto.application.cursors import encode_cursor
from netauto.application.objects import ObjectService
from netauto.application.relationshipdefinitions import RelationshipDefinitionService
from netauto.application.relationships import RelationshipService
from netauto.domain.primitives import JsonValue
from netauto.entrypoints.http import build_app
from netauto.persistence.engine import RuntimeContext
from netauto.persistence.lifecycle import LifecycleStore, decode_lifecycle_event
from netauto.persistence.metadata import (
    object_lifecycle_events,
    relationship_definition_properties,
    relationship_definitions,
    relationships,
    runtime_relationship_resolutions,
)
from netauto.persistence.relationships import (
    RelationshipDefinitionStore,
    RelationshipDefinitionVersionStore,
    RuntimeRelationshipStore,
)
from netauto.settings import Settings


@dataclass(frozen=True, slots=True)
class M3S05Runtime:
    client: httpx.AsyncClient
    engine: AsyncEngine
    database_engine: Engine


@pytest.fixture
async def m3_s05_runtime(
    migrated_database_engine: Engine, test_database_url: str
) -> AsyncIterator[M3S05Runtime]:
    app = build_app(Settings(database_url=test_database_url))
    async with app.router.lifespan_context(app):
        runtime = cast(RuntimeContext, app.state.runtime)
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            yield M3S05Runtime(client, runtime.engine, migrated_database_engine)


async def _template(client: httpx.AsyncClient, name: str) -> str:
    created = await client.post(
        "/api/v1/core/object-templates",
        json={"namespace": "m3s05", "name": name, "abstract": False},
    )
    assert created.status_code == 201, created.text
    template_id = cast(str, created.json()["object_template"]["id"])
    published = await client.post(
        f"/api/v1/core/object-templates/{template_id}/versions/1/publish",
        params={"expected_revision": 1},
    )
    assert published.status_code == 200, published.text
    return template_id


async def _datatype(client: httpx.AsyncClient, name: str) -> str:
    created = await client.post(
        "/api/v1/core/datatypes",
        json={
            "namespace": "m3s05",
            "name": name,
            "base_type": "core.integer",
        },
    )
    assert created.status_code == 201, created.text
    datatype_id = cast(str, created.json()["datatype"]["id"])
    published = await client.post(
        f"/api/v1/core/datatypes/{datatype_id}/versions/1/publish",
        params={"expected_revision": 1},
    )
    assert published.status_code == 200, published.text
    return datatype_id


async def _definition(
    client: httpx.AsyncClient,
    first_template_id: str,
    second_template_id: str,
    name: str,
    *,
    symmetric: bool,
    properties: list[dict[str, object]] | None = None,
    publish: bool = False,
) -> dict[str, object]:
    if symmetric:
        body: dict[str, object] = {
            "symmetric": True,
            "endpoint_template_ids": [first_template_id, second_template_id],
            "name": name,
            "properties": properties or [],
        }
    else:
        body = {
            "symmetric": False,
            "perspectives": [
                {"template_id": first_template_id, "name": f"{name}_from"},
                {"template_id": second_template_id, "name": f"{name}_to"},
            ],
            "properties": properties or [],
        }
    created = await client.post("/api/v1/core/relationship-definitions", json=body)
    assert created.status_code == 201, created.text
    value = cast(dict[str, object], created.json()["relationship_definition"])
    if publish:
        published = await client.post(
            f"/api/v1/core/relationship-definitions/{value['id']}/versions/1/publish",
            params={"expected_revision": 1},
        )
        assert published.status_code == 200, published.text
        current = await client.get(
            f"/api/v1/core/relationship-definitions/{value['id']}"
        )
        assert current.status_code == 200, current.text
        value = cast(dict[str, object], current.json())
    return value


async def _object(client: httpx.AsyncClient, template_id: str, name: str) -> str:
    created = await client.post(
        "/api/v1/core/objects",
        json={"template_id": template_id, "canonical_name": name},
    )
    assert created.status_code == 201, created.text
    return cast(str, created.json()["id"])


def _resolution(definition: dict[str, object], from_template_id: str) -> dict[str, str]:
    values = cast(list[dict[str, str]], definition["resolutions"])
    return next(item for item in values if item["from_template_id"] == from_template_id)


@pytest.mark.api
@pytest.mark.postgresql
async def test_m3_s05_definition_root_pages_and_exact_reads_trust_aggregates(
    m3_s05_runtime: M3S05Runtime,
) -> None:
    client = m3_s05_runtime.client
    templates = [await _template(client, f"aggregate_{index}") for index in range(4)]
    definitions = [
        await _definition(
            client,
            templates[0],
            templates[1],
            "aggregate_first",
            symmetric=False,
        ),
        await _definition(
            client,
            templates[2],
            templates[3],
            "aggregate_second",
            symmetric=False,
        ),
    ]
    definition_ids = {cast(str, value["id"]) for value in definitions}

    first_page = await client.get(
        "/api/v1/core/relationship-definitions", params={"limit": 1}
    )
    assert first_page.status_code == 200, first_page.text
    assert len(first_page.json()["items"]) == 1
    assert len(first_page.json()["items"][0]["resolutions"]) == 2
    cursor = cast(str, first_page.json()["next_cursor"])
    second_page = await client.get(
        "/api/v1/core/relationship-definitions",
        params={"cursor": cursor, "limit": 10},
    )
    assert second_page.status_code == 200, second_page.text
    traversed = [
        item["id"]
        for page in (first_page, second_page)
        for item in page.json()["items"]
    ]
    assert set(traversed) == definition_ids
    assert len(traversed) == len(set(traversed))
    assert all(
        len(item["resolutions"]) == 2
        for page in (first_page, second_page)
        for item in page.json()["items"]
    )

    malformed = encode_cursor("relationship_definitions", {}, [1])
    malformed_response = await client.get(
        "/api/v1/core/relationship-definitions", params={"cursor": malformed}
    )
    assert malformed_response.status_code == 400
    assert malformed_response.json()["code"] == "invalid_cursor"

    trusted_id = UUID(cast(str, definitions[0]["id"]))
    with m3_s05_runtime.database_engine.begin() as connection:
        connection.execute(
            relationship_definitions.update()
            .where(relationship_definitions.c.id == trusted_id)
            .values(default_version=1)
        )
    exact = await client.get(f"/api/v1/core/relationship-definitions/{trusted_id}")
    listed = await client.get("/api/v1/core/relationship-definitions")
    assert exact.status_code == 200 and exact.json()["default_version"] == 1
    assert (
        next(item for item in listed.json()["items"] if item["id"] == str(trusted_id))[
            "default_version"
        ]
        == 1
    )

    rejected_default = await client.post(
        f"/api/v1/core/relationship-definitions/{trusted_id}/set-default",
        json={"version": 1},
    )
    assert rejected_default.status_code == 409, rejected_default.text
    assert rejected_default.json()["code"] == "dependency_not_admissible"

    zero_resolution_id = uuid4()
    with m3_s05_runtime.database_engine.begin() as connection:
        connection.execute(
            relationship_definitions.insert().values(
                id=zero_resolution_id, symmetric=False
            )
        )
    zero = await client.get(
        f"/api/v1/core/relationship-definitions/{zero_resolution_id}"
    )
    missing = await client.get(f"/api/v1/core/relationship-definitions/{uuid4()}")
    assert zero.status_code == 200
    assert zero.json()["resolutions"] == []
    assert missing.status_code == 404


@pytest.mark.api
@pytest.mark.postgresql
async def test_m3_s05_definition_version_parent_cursor_and_trusted_history(
    m3_s05_runtime: M3S05Runtime,
) -> None:
    client = m3_s05_runtime.client
    template_id = await _template(client, "version_endpoint")
    first_datatype = await _datatype(client, "version_first")
    second_datatype = await _datatype(client, "version_second")
    properties: list[dict[str, object]] = [
        {
            "name": "later",
            "position": 2,
            "datatype_id": first_datatype,
            "datatype_version": 1,
            "value_mode": "SCALAR",
        },
        {
            "name": "earlier",
            "position": 1,
            "datatype_id": first_datatype,
            "datatype_version": 1,
            "value_mode": "SCALAR",
        },
    ]
    definition = await _definition(
        client,
        template_id,
        template_id,
        "versioned",
        symmetric=True,
        properties=properties,
    )
    definition_id = cast(str, definition["id"])

    populated = await client.get(
        f"/api/v1/core/relationship-definitions/{definition_id}/versions/1"
    )
    assert populated.status_code == 200, populated.text
    assert [item["position"] for item in populated.json()["properties"]] == [1, 2]

    filtered_empty = await client.get(
        f"/api/v1/core/relationship-definitions/{definition_id}/versions",
        params={"status": "DEPRECATED"},
    )
    missing_parent_id = str(uuid4())
    missing_parent_page = await client.get(
        f"/api/v1/core/relationship-definitions/{missing_parent_id}/versions"
    )
    missing_parent_exact = await client.get(
        f"/api/v1/core/relationship-definitions/{missing_parent_id}/versions/1"
    )
    missing_version = await client.get(
        f"/api/v1/core/relationship-definitions/{definition_id}/versions/999"
    )
    assert filtered_empty.status_code == 200
    assert filtered_empty.json()["items"] == []
    assert missing_parent_page.status_code == 404
    assert missing_parent_exact.status_code == 404
    assert missing_parent_exact.json()["details"]["resource_type"] == (
        "relationship_definition"
    )
    assert missing_version.status_code == 404
    assert missing_version.json()["details"]["resource_type"] == (
        "relationship_definition_version"
    )

    zero_definition = await _definition(
        client,
        template_id,
        template_id,
        "zero_properties",
        symmetric=True,
    )
    zero_definition_id = cast(str, zero_definition["id"])
    zero = await client.get(
        f"/api/v1/core/relationship-definitions/{zero_definition_id}/versions/1"
    )
    assert zero.status_code == 200 and zero.json()["properties"] == []

    published = await client.post(
        f"/api/v1/core/relationship-definitions/{definition_id}/versions/1/publish",
        params={"expected_revision": 1},
    )
    assert published.status_code == 200, published.text
    created_next = await client.post(
        f"/api/v1/core/relationship-definitions/{definition_id}/create-next",
        json={"source_version": 1},
    )
    assert created_next.status_code == 201, created_next.text

    first_page = await client.get(
        f"/api/v1/core/relationship-definitions/{definition_id}/versions",
        params={"limit": 1},
    )
    cursor = cast(str, first_page.json()["next_cursor"])
    continued = await client.get(
        f"/api/v1/core/relationship-definitions/{definition_id}/versions",
        params={"cursor": cursor, "limit": 10},
    )
    assert [item["version"] for item in first_page.json()["items"]] == [1]
    assert [item["version"] for item in continued.json()["items"]] == [2]

    wrong_filter = await client.get(
        f"/api/v1/core/relationship-definitions/{definition_id}/versions",
        params={"status": "DRAFT", "cursor": cursor},
    )
    wrong_target = await client.get(
        f"/api/v1/core/relationship-definitions/{zero_definition_id}/versions",
        params={"cursor": cursor},
    )
    malformed = encode_cursor(
        "relationship_definition_versions",
        {"definition_id": definition_id, "status": None},
        ["1"],
    )
    malformed_response = await client.get(
        f"/api/v1/core/relationship-definitions/{definition_id}/versions",
        params={"cursor": malformed},
    )
    for response in (wrong_filter, wrong_target, malformed_response):
        assert response.status_code == 400, response.text
        assert response.json()["code"] == "invalid_cursor"

    with m3_s05_runtime.database_engine.begin() as connection:
        connection.execute(
            relationship_definition_properties.update()
            .where(
                relationship_definition_properties.c.relationship_definition_id
                == UUID(definition_id),
                relationship_definition_properties.c.relationship_definition_version
                == 2,
                relationship_definition_properties.c.name == "later",
            )
            .values(datatype_id=UUID(second_datatype), datatype_version=1)
        )
    trusted = await client.get(
        f"/api/v1/core/relationship-definitions/{definition_id}/versions/2"
    )
    assert trusted.status_code == 200, trusted.text
    changed = next(
        item for item in trusted.json()["properties"] if item["name"] == "later"
    )
    assert changed["datatype_id"] == second_datatype

    rejected_history = await client.post(
        f"/api/v1/core/relationship-definitions/{definition_id}/versions/2/publish",
        params={"expected_revision": 1},
    )
    assert rejected_history.status_code == 422, rejected_history.text
    assert rejected_history.json()["code"] == "semantic_validation_failed"


@pytest.mark.api
@pytest.mark.postgresql
async def test_m3_s05_relationship_exact_trusts_facts_and_deduplicates_views(
    m3_s05_runtime: M3S05Runtime,
) -> None:
    client = m3_s05_runtime.client
    first_template = await _template(client, "relationship_first")
    second_template = await _template(client, "relationship_second")
    definition = await _definition(
        client,
        first_template,
        second_template,
        "related",
        symmetric=True,
        publish=True,
    )
    definition_id = cast(str, definition["id"])
    first_object = await _object(client, first_template, "relationship-first")
    second_object = await _object(client, second_template, "relationship-second")
    selected = _resolution(definition, first_template)
    reciprocal = _resolution(definition, second_template)

    created = await client.post(
        "/api/v1/core/relationships",
        json={
            "resolution_id": selected["resolution_id"],
            "from_object_id": first_object,
            "to_object_id": second_object,
        },
    )
    assert created.status_code == 201, created.text
    relationship_id = cast(str, created.json()["id"])

    duplicate_mutation = await client.post(
        "/api/v1/core/relationships",
        json={
            "resolution_id": selected["resolution_id"],
            "from_object_id": first_object,
            "to_object_id": second_object,
        },
    )
    assert duplicate_mutation.status_code == 409, duplicate_mutation.text
    assert duplicate_mutation.json()["code"] == "relationship_fact_conflict"

    third_object = await _object(client, first_template, "relationship-third")
    fourth_object = await _object(client, second_template, "relationship-fourth")
    invalid_properties = await client.post(
        "/api/v1/core/relationships",
        json={
            "resolution_id": selected["resolution_id"],
            "from_object_id": third_object,
            "to_object_id": fourth_object,
            "properties": {"unknown": 1},
        },
    )
    assert invalid_properties.status_code == 422, invalid_properties.text
    assert invalid_properties.json()["code"] == "semantic_validation_failed"

    surprise = {"Bad-Key": None, "nested": [1, True, {"deep": None}]}
    with m3_s05_runtime.database_engine.begin() as connection:
        connection.execute(
            relationships.update()
            .where(relationships.c.id == UUID(relationship_id))
            .values(properties=surprise)
        )
        connection.execute(
            runtime_relationship_resolutions.insert().values(
                relationship_id=UUID(relationship_id),
                relationship_definition_id=UUID(definition_id),
                resolution_id=UUID(reciprocal["resolution_id"]),
                from_object_id=UUID(first_object),
                to_object_id=UUID(second_object),
            )
        )

    exact = await client.get(f"/api/v1/core/relationships/{relationship_id}")
    assert exact.status_code == 200, exact.text
    assert exact.json()["properties"] == surprise
    views = {
        (item["object_id"], item["destination_object_id"], item["name"])
        for item in exact.json()["views"]
    }
    assert views == {
        (first_object, second_object, "related"),
        (second_object, first_object, "related"),
    }
    assert len(exact.json()["views"]) == 2

    zero_view_id = uuid4()
    with m3_s05_runtime.database_engine.begin() as connection:
        connection.execute(
            relationships.insert().values(
                id=zero_view_id,
                relationship_definition_id=UUID(definition_id),
                relationship_definition_version=1,
                properties={},
            )
        )
    zero = await client.get(f"/api/v1/core/relationships/{zero_view_id}")
    missing = await client.get(f"/api/v1/core/relationships/{uuid4()}")
    assert zero.status_code == 200 and zero.json()["views"] == []
    assert missing.status_code == 404


@pytest.mark.api
@pytest.mark.postgresql
async def test_m3_ver_07_08_13_lifecycle_boundaries_and_cursor_scope(
    m3_s05_runtime: M3S05Runtime,
) -> None:
    client = m3_s05_runtime.client
    template_id = await _template(client, "lifecycle_template")
    first_object = await _object(client, template_id, "lifecycle-first")
    second_object = await _object(client, template_id, "lifecycle-second")
    occurred_at = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
    snapshot = {
        "id": first_object,
        "canonical_name": "lifecycle-first",
        "template_id": template_id,
        "template_version": 1,
        "properties": {"Bad-Key": None, "nested": [1, True, {"deep": None}]},
        "ignored": "extra",
    }
    intrinsic_ids = [UUID(int=value) for value in (301, 302, 303)]
    relationship_event_id = UUID(int=401)
    relationship_id = uuid4()
    relationship_definition_id = uuid4()
    factual_surprise: dict[str, JsonValue] = {
        "relationship_definition_version": 0,
        "properties": {"Bad-Key": None, "nested": [[], {"deep": True}]},
        "ignored": "extra",
    }
    with m3_s05_runtime.database_engine.begin() as connection:
        connection.execute(
            object_lifecycle_events.insert(),
            [
                {
                    "id": event_id,
                    "occurred_at": occurred_at,
                    "kind": "DATA_CHANGE",
                    "object_id": UUID(first_object),
                    "canonical_name": "lifecycle-first",
                    "before_state": snapshot,
                    "after_state": snapshot,
                }
                for event_id in intrinsic_ids
            ],
        )
        connection.execute(
            object_lifecycle_events.insert().values(
                id=relationship_event_id,
                occurred_at=occurred_at,
                kind="RELATIONSHIP_DATA_CHANGE",
                object_id=UUID(first_object),
                canonical_name="lifecycle-first",
                destination_object_id=UUID(second_object),
                destination_canonical_name="lifecycle-second",
                relationship_id=relationship_id,
                relationship_definition_id=relationship_definition_id,
                relationship_name="surprising_link",
                before_state=factual_surprise,
                after_state=factual_surprise,
            )
        )

    global_first = await client.get(
        "/api/v1/core/lifecycle-events",
        params={"kind": "DATA_CHANGE", "limit": 1},
    )
    assert global_first.status_code == 200, global_first.text
    global_cursor = cast(str, global_first.json()["next_cursor"])
    global_continued = await client.get(
        "/api/v1/core/lifecycle-events",
        params={"kind": "DATA_CHANGE", "cursor": global_cursor, "limit": 10},
    )
    ids = [
        item["id"]
        for page in (global_first, global_continued)
        for item in page.json()["items"]
    ]
    assert ids == [str(value) for value in reversed(intrinsic_ids)]
    assert len(ids) == len(set(ids))
    assert all(
        item["before"] == item["after"]
        for page in (global_first, global_continued)
        for item in page.json()["items"]
    )

    global_on_object = await client.get(
        f"/api/v1/core/objects/{first_object}/lifecycle-events",
        params={"kind": "DATA_CHANGE", "cursor": global_cursor},
    )
    changed_filter = await client.get(
        "/api/v1/core/lifecycle-events",
        params={"kind": "RENAME", "cursor": global_cursor},
    )
    malformed_filters: dict[str, JsonValue] = {
        "kind": "DATA_CHANGE",
        "object_id": None,
        "destination_object_id": None,
        "relationship_id": None,
        "relationship_definition_id": None,
        "relationship_name": None,
        "occurred_from": None,
        "occurred_to": None,
        "involving_object_id": None,
    }
    malformed = encode_cursor("lifecycle_events", malformed_filters, [1, str(uuid4())])
    malformed_response = await client.get(
        "/api/v1/core/lifecycle-events",
        params={"kind": "DATA_CHANGE", "cursor": malformed},
    )
    for response in (global_on_object, changed_filter, malformed_response):
        assert response.status_code == 400, response.text
        assert response.json()["code"] == "invalid_cursor"

    object_first = await client.get(
        f"/api/v1/core/objects/{first_object}/lifecycle-events",
        params={"kind": "DATA_CHANGE", "limit": 1},
    )
    object_cursor = cast(str, object_first.json()["next_cursor"])
    object_continued = await client.get(
        f"/api/v1/core/objects/{first_object}/lifecycle-events",
        params={"kind": "DATA_CHANGE", "cursor": object_cursor, "limit": 10},
    )
    other_object = await client.get(
        f"/api/v1/core/objects/{second_object}/lifecycle-events",
        params={"kind": "DATA_CHANGE", "cursor": object_cursor},
    )
    object_on_global = await client.get(
        "/api/v1/core/lifecycle-events",
        params={"kind": "DATA_CHANGE", "cursor": object_cursor},
    )
    assert object_continued.status_code == 200, object_continued.text
    assert len(object_continued.json()["items"]) == 2
    for response in (other_object, object_on_global):
        assert response.status_code == 400, response.text
        assert response.json()["code"] == "invalid_cursor"

    relationship_global = await client.get(
        "/api/v1/core/lifecycle-events",
        params={"relationship_id": str(relationship_id)},
    )
    relationship_object = await client.get(
        f"/api/v1/core/objects/{first_object}/lifecycle-events",
        params={"relationship_id": str(relationship_id)},
    )
    for response in (relationship_global, relationship_object):
        assert response.status_code == 200, response.text
        assert len(response.json()["items"]) == 1
        item = response.json()["items"][0]
        assert item["kind"] == "RELATIONSHIP_DATA_CHANGE"
        assert (
            item["before"]
            == item["after"]
            == {
                "relationship_definition_version": 0,
                "properties": factual_surprise["properties"],
            }
        )

    bad_intrinsic_id = UUID(int=501)
    bad_relationship_event_id = UUID(int=502)
    bad_relationship_id = uuid4()
    with m3_s05_runtime.database_engine.begin() as connection:
        connection.execute(
            object_lifecycle_events.insert().values(
                id=bad_intrinsic_id,
                occurred_at=occurred_at,
                kind="CREATED",
                object_id=UUID(first_object),
                canonical_name="lifecycle-first",
                after_state={
                    "id": first_object,
                    "canonical_name": "missing-template",
                    "template_version": 1,
                    "properties": {},
                },
            )
        )
        connection.execute(
            object_lifecycle_events.insert().values(
                id=bad_relationship_event_id,
                occurred_at=occurred_at,
                kind="RELATIONSHIP_CREATED",
                object_id=UUID(first_object),
                canonical_name="lifecycle-first",
                destination_object_id=UUID(second_object),
                destination_canonical_name="lifecycle-second",
                relationship_id=bad_relationship_id,
                relationship_definition_id=relationship_definition_id,
                relationship_name="bad_link",
                after_state={
                    "relationship_definition_version": "not-an-integer",
                    "properties": {},
                },
            )
        )

    intrinsic_global = await client.get(
        "/api/v1/core/lifecycle-events",
        params={"object_id": first_object, "kind": "CREATED"},
    )
    intrinsic_object = await client.get(
        f"/api/v1/core/objects/{first_object}/lifecycle-events",
        params={"kind": "CREATED"},
    )
    relationship_global_bad = await client.get(
        "/api/v1/core/lifecycle-events",
        params={"relationship_id": str(bad_relationship_id)},
    )
    relationship_object_bad = await client.get(
        f"/api/v1/core/objects/{first_object}/lifecycle-events",
        params={"relationship_id": str(bad_relationship_id)},
    )
    for response in (
        intrinsic_global,
        intrinsic_object,
        relationship_global_bad,
        relationship_object_bad,
    ):
        assert response.status_code == 500, response.text
        assert response.json()["code"] == "internal_error"


@pytest.mark.api
@pytest.mark.postgresql
async def test_m3_s05_six_gets_each_execute_one_business_statement(
    m3_s05_runtime: M3S05Runtime,
) -> None:
    client = m3_s05_runtime.client
    template_id = await _template(client, "statement_template")
    definition = await _definition(
        client,
        template_id,
        template_id,
        "statement_link",
        symmetric=True,
        publish=True,
    )
    definition_id = cast(str, definition["id"])
    first_object = await _object(client, template_id, "statement-first")
    second_object = await _object(client, template_id, "statement-second")
    resolution = _resolution(definition, template_id)
    created = await client.post(
        "/api/v1/core/relationships",
        json={
            "resolution_id": resolution["resolution_id"],
            "from_object_id": first_object,
            "to_object_id": second_object,
        },
    )
    assert created.status_code == 201, created.text
    relationship_id = cast(str, created.json()["id"])

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
        "RD-GET-01": "/api/v1/core/relationship-definitions?limit=1",
        "RD-GET-02": f"/api/v1/core/relationship-definitions/{definition_id}",
        "RD-GET-03": (
            f"/api/v1/core/relationship-definitions/{definition_id}/versions?limit=1"
        ),
        "RD-GET-04": (
            f"/api/v1/core/relationship-definitions/{definition_id}/versions/1"
        ),
        "REL-GET-01": f"/api/v1/core/relationships/{relationship_id}",
        "LC-GET-01": "/api/v1/core/lifecycle-events?limit=1",
    }
    counts: dict[str, int] = {}
    event.listen(
        m3_s05_runtime.engine.sync_engine,
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
            m3_s05_runtime.engine.sync_engine,
            "before_cursor_execute",
            observe_statement,
        )
    assert counts == {route_id: 1 for route_id in routes}


def test_m3_s05_get_paths_have_no_read_certification_dependencies() -> None:
    forbidden_calls = {
        "_relationship_schema",
        "_relationship_specs",
        "_validate_default_pointers",
        "_validate_persisted",
        "_validated",
        "_validated_many",
        "canonicalize_properties",
        "coherent_read",
        "validate_definition",
        "validate_relationship",
        "validate_relationship_definition_version",
        "validate_relationship_property_history",
    }
    methods: tuple[Callable[..., object], ...] = (
        RelationshipDefinitionService.list_definitions,
        RelationshipDefinitionService.get,
        RelationshipDefinitionService.list_versions,
        RelationshipDefinitionService.get_version,
        RelationshipService.get,
        ObjectService.list_events,
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

    root_page_source = inspect.getsource(RelationshipDefinitionStore.list_definitions)
    exact_version_source = inspect.getsource(
        RelationshipDefinitionVersionStore.project_version
    )
    relationship_source = inspect.getsource(RuntimeRelationshipStore.project)
    lifecycle_source = inspect.getsource(LifecycleStore.list_events)
    decoder_source = inspect.getsource(decode_lifecycle_event)
    writer_source = inspect.getsource(LifecycleStore.insert_relationship_events)
    relationship_validator_source = inspect.getsource(
        RelationshipService._validated  # pyright: ignore[reportPrivateUsage]
    )

    assert "relationship_definition_page" in root_page_source
    assert "outerjoin" in exact_version_source
    assert "views.add" in relationship_source
    assert ".limit(limit)" in lifecycle_source
    assert "properties !=" not in decoder_source
    assert "relationship_definition_version" in writer_source
    assert "before.properties != after.properties" in writer_source
    assert "validate_relationship(" in relationship_validator_source
