"""Real-PostgreSQL API and persistence coverage for factual Relationships."""

from collections.abc import AsyncIterator
from typing import cast
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import Engine, insert, select
from sqlalchemy.exc import IntegrityError

from netauto.domain.primitives import JsonValue
from netauto.entrypoints.http import build_app
from netauto.persistence.lifecycle import EventKind
from netauto.persistence.metadata import (
    object_lifecycle_events,
    objects,
    relationships,
    runtime_relationship_resolutions,
)
from netauto.settings import Settings


@pytest.fixture
async def relationship_client(
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


async def _template(client: httpx.AsyncClient, name: str) -> str:
    created = await client.post(
        "/api/v1/core/object-templates",
        json={"namespace": "relationship_runtime", "name": name, "abstract": False},
    )
    assert created.status_code == 201, created.text
    template_id = cast(str, created.json()["object_template"]["id"])
    published = await client.post(
        f"/api/v1/core/object-templates/{template_id}/versions/1/publish",
        params={"expected_revision": 1},
    )
    assert published.status_code == 200, published.text
    return template_id


async def _object(client: httpx.AsyncClient, template_id: str, name: str) -> str:
    created = await client.post(
        "/api/v1/core/objects",
        json={"template_id": template_id, "canonical_name": name},
    )
    assert created.status_code == 201, created.text
    return cast(str, created.json()["id"])


async def _definition(
    client: httpx.AsyncClient, first_template: str, second_template: str
) -> dict[str, object]:
    created = await client.post(
        "/api/v1/core/relationship-definitions",
        json={
            "symmetric": False,
            "perspectives": [
                {"template_id": first_template, "name": "hosts"},
                {"template_id": second_template, "name": "hosted_by"},
            ],
        },
    )
    assert created.status_code == 201, created.text
    return await _publish_created_definition(client, created)


async def _publish_created_definition(
    client: httpx.AsyncClient, created: httpx.Response
) -> dict[str, object]:
    payload = cast(dict[str, object], created.json())
    definition = cast(dict[str, object], payload["relationship_definition"])
    definition_id = cast(str, definition["id"])
    published = await client.post(
        f"/api/v1/core/relationship-definitions/{definition_id}/versions/1/publish",
        params={"expected_revision": 1},
    )
    assert published.status_code == 200, published.text
    current = await client.get(f"/api/v1/core/relationship-definitions/{definition_id}")
    assert current.status_code == 200, current.text
    return cast(dict[str, object], current.json())


def _resolution(definition: dict[str, object], from_template_id: str) -> dict[str, str]:
    resolutions = cast(list[dict[str, str]], definition["resolutions"])
    return next(
        item for item in resolutions if item["from_template_id"] == from_template_id
    )


@pytest.mark.api
@pytest.mark.postgresql
async def test_create_conflict_read_navigate_lifecycle_delete_and_definition_unblock(
    relationship_client: httpx.AsyncClient,
) -> None:
    client = relationship_client
    first_template = await _template(client, "runtime_a")
    second_template = await _template(client, "runtime_b")
    first_object = await _object(client, first_template, "endpoint-a")
    second_object = await _object(client, second_template, "endpoint-b")
    definition = await _definition(client, first_template, second_template)
    first_resolution = _resolution(definition, first_template)
    second_resolution = _resolution(definition, second_template)

    created = await client.post(
        "/api/v1/core/relationships",
        json={
            "resolution_id": first_resolution["resolution_id"],
            "from_object_id": first_object,
            "to_object_id": second_object,
        },
    )
    assert created.status_code == 201, created.text
    value = created.json()
    relationship_id = value["id"]
    assert created.headers["location"].endswith(relationship_id)
    assert value["relationship_definition_id"] == definition["id"]
    assert value["relationship_definition_version"] == 1
    assert value["properties"] == {}
    assert {
        (item["object_id"], item["destination_object_id"], item["name"])
        for item in value["views"]
    } == {
        (first_object, second_object, first_resolution["name"]),
        (second_object, first_object, second_resolution["name"]),
    }

    converged = await client.post(
        "/api/v1/core/relationships",
        json={
            "resolution_id": second_resolution["resolution_id"],
            "from_object_id": second_object,
            "to_object_id": first_object,
        },
    )
    assert converged.status_code == 409, converged.text
    assert "location" not in converged.headers
    assert converged.json()["code"] == "relationship_fact_conflict"
    assert converged.json()["details"] == {"relationship_id": relationship_id}

    exact = await client.get(f"/api/v1/core/relationships/{relationship_id}")
    assert exact.status_code == 200
    assert exact.json() == value

    relative = await client.get(
        f"/api/v1/core/objects/{first_object}/relationships",
        params={
            "relationship_definition_id": cast(str, definition["id"]),
            "name": "hosts",
        },
    )
    assert relative.status_code == 200, relative.text
    assert relative.json() == {
        "items": [
            {
                "relationship_id": relationship_id,
                "relationship_definition_id": definition["id"],
                "relationship_definition_version": 1,
                "object_id": first_object,
                "destination_object_id": second_object,
                "name": "hosts",
                "properties": {},
            }
        ],
        "next_cursor": None,
    }

    created_events = await client.get(
        "/api/v1/core/lifecycle-events",
        params={"relationship_id": relationship_id, "kind": "RELATIONSHIP_CREATED"},
    )
    assert created_events.status_code == 200, created_events.text
    events = created_events.json()["items"]
    assert len(events) == 2
    assert all(
        set(item)
        == {
            "id",
            "occurred_at",
            "kind",
            "object_id",
            "canonical_name",
            "destination_object_id",
            "destination_canonical_name",
            "relationship_id",
            "relationship_definition_id",
            "relationship_name",
            "before",
            "after",
        }
        for item in events
    )
    assert all(item["before"] is None for item in events)
    assert all(
        item["after"] == {"relationship_definition_version": 1, "properties": {}}
        for item in events
    )

    destination_events = await client.get(
        "/api/v1/core/lifecycle-events",
        params={"destination_object_id": second_object},
    )
    assert destination_events.status_code == 200
    assert {
        item["destination_object_id"] for item in destination_events.json()["items"]
    } == {second_object}
    destination_mismatch = await client.get(
        "/api/v1/core/lifecycle-events",
        params={"destination_object_id": str(uuid4())},
    )
    assert destination_mismatch.json()["items"] == []

    event_timestamp = events[0]["occurred_at"]
    for key in ("occurred_from", "occurred_to"):
        inclusive = await client.get(
            "/api/v1/core/lifecycle-events", params={key: event_timestamp}
        )
        assert inclusive.status_code == 200, inclusive.text
        assert any(
            item["relationship_id"] == relationship_id
            for item in inclusive.json()["items"]
            if "relationship_id" in item
        )
    too_late = await client.get(
        "/api/v1/core/lifecycle-events",
        params={"occurred_from": "2999-01-01T00:00:00.000000Z"},
    )
    assert too_late.json()["items"] == []
    too_early = await client.get(
        "/api/v1/core/lifecycle-events",
        params={"occurred_to": "1970-01-01T00:00:00.000000Z"},
    )
    assert too_early.json()["items"] == []

    relationship_id_mismatch = await client.get(
        "/api/v1/core/lifecycle-events",
        params={"relationship_id": str(uuid4())},
    )
    assert relationship_id_mismatch.status_code == 200
    assert relationship_id_mismatch.json()["items"] == []

    definition_events = await client.get(
        "/api/v1/core/lifecycle-events",
        params={
            "relationship_definition_id": cast(str, definition["id"]),
            "kind": "RELATIONSHIP_CREATED",
        },
    )
    assert definition_events.status_code == 200
    assert len(definition_events.json()["items"]) == 2
    definition_mismatch = await client.get(
        "/api/v1/core/lifecycle-events",
        params={"relationship_definition_id": str(uuid4())},
    )
    assert definition_mismatch.status_code == 200
    assert definition_mismatch.json()["items"] == []

    name_events = await client.get(
        "/api/v1/core/lifecycle-events",
        params={"relationship_name": first_resolution["name"]},
    )
    assert name_events.status_code == 200
    assert [item["relationship_name"] for item in name_events.json()["items"]] == [
        first_resolution["name"]
    ]
    name_mismatch = await client.get(
        "/api/v1/core/lifecycle-events",
        params={"relationship_name": "relationship_name_mismatch"},
    )
    assert name_mismatch.status_code == 200
    assert name_mismatch.json()["items"] == []

    for endpoint_id in (first_object, second_object):
        endpoint_timeline = await client.get(
            f"/api/v1/core/objects/{endpoint_id}/lifecycle-events",
            params={
                "relationship_id": relationship_id,
                "kind": "RELATIONSHIP_CREATED",
            },
        )
        assert endpoint_timeline.status_code == 200
        timeline_items = endpoint_timeline.json()["items"]
        assert len(timeline_items) == 2
        assert all(
            endpoint_id in {item["object_id"], item["destination_object_id"]}
            for item in timeline_items
        )
        assert {item["object_id"] for item in timeline_items} == {
            first_object,
            second_object,
        }

    blocked = await client.delete(
        f"/api/v1/core/relationship-definitions/{definition['id']}"
    )
    assert blocked.status_code == 409
    assert blocked.json()["code"] == "delete_blocked"
    assert blocked.json()["details"]["blockers"] == [
        {"type": "relationship", "count": 1}
    ]

    blocked_endpoint = await client.delete(f"/api/v1/core/objects/{first_object}")
    assert blocked_endpoint.status_code == 409
    assert blocked_endpoint.json() == {
        "code": "delete_blocked",
        "message": "Current references prevent Object deletion.",
        "details": {
            "resource_type": "object",
            "id": first_object,
            "blockers": [{"type": "relationship", "count": 1}],
        },
    }

    deleted = await client.delete(f"/api/v1/core/relationships/{relationship_id}")
    assert deleted.status_code == 204
    repeated = await client.delete(f"/api/v1/core/relationships/{relationship_id}")
    assert repeated.status_code == 404
    missing = await client.get(f"/api/v1/core/relationships/{relationship_id}")
    assert missing.status_code == 404

    history = await client.get(
        "/api/v1/core/lifecycle-events",
        params={"relationship_id": relationship_id},
    )
    assert history.status_code == 200
    assert len(history.json()["items"]) == 4
    assert {item["kind"] for item in history.json()["items"]} == {
        "RELATIONSHIP_CREATED",
        "RELATIONSHIP_DELETED",
    }
    deleted_endpoint = await client.delete(f"/api/v1/core/objects/{first_object}")
    assert deleted_endpoint.status_code == 204
    assert (await client.get(f"/api/v1/core/objects/{first_object}")).status_code == 404
    assert (
        await client.get(f"/api/v1/core/objects/{first_object}/lifecycle-events")
    ).status_code == 404
    endpoint_history = await client.get(
        "/api/v1/core/lifecycle-events", params={"object_id": first_object}
    )
    assert endpoint_history.status_code == 200
    assert "DELETED" in {item["kind"] for item in endpoint_history.json()["items"]}
    unblocked = await client.delete(
        f"/api/v1/core/relationship-definitions/{definition['id']}"
    )
    assert unblocked.status_code == 204
    assert (
        await client.delete(f"/api/v1/core/objects/{second_object}")
    ).status_code == 204
    historical = await client.get(
        "/api/v1/core/lifecycle-events", params={"relationship_id": relationship_id}
    )
    assert historical.status_code == 200
    assert len(historical.json()["items"]) == 4


@pytest.mark.api
@pytest.mark.postgresql
async def test_strict_operands_missing_resources_incompatibility_and_self_loop(
    relationship_client: httpx.AsyncClient,
) -> None:
    client = relationship_client
    template_id = await _template(client, "self_endpoint")
    other_template_id = await _template(client, "other_endpoint")
    object_id = await _object(client, template_id, "self")
    other_object_id = await _object(client, other_template_id, "other")
    definition = await client.post(
        "/api/v1/core/relationship-definitions",
        json={
            "symmetric": True,
            "endpoint_template_ids": [template_id, template_id],
            "name": "peers",
        },
    )
    assert definition.status_code == 201
    definition_value = await _publish_created_definition(client, definition)
    resolution_id = cast(list[dict[str, str]], definition_value["resolutions"])[0][
        "resolution_id"
    ]

    unknown = await client.post(
        "/api/v1/core/relationships",
        json={
            "resolution_id": resolution_id,
            "from_object_id": object_id,
            "to_object_id": object_id,
            "relationship_id": str(uuid4()),
        },
    )
    assert unknown.status_code == 400
    assert unknown.json()["code"] == "invalid_request"
    for invalid_body in (
        {
            "resolution_id": None,
            "from_object_id": object_id,
            "to_object_id": object_id,
        },
        {
            "resolution_id": 7,
            "from_object_id": object_id,
            "to_object_id": object_id,
        },
    ):
        invalid_carrier = await client.post(
            "/api/v1/core/relationships", json=invalid_body
        )
        assert invalid_carrier.status_code == 400
        assert invalid_carrier.json()["code"] == "invalid_request"
    missing_resolution = await client.post(
        "/api/v1/core/relationships",
        json={
            "resolution_id": str(uuid4()),
            "from_object_id": object_id,
            "to_object_id": object_id,
        },
    )
    assert missing_resolution.status_code == 422
    assert missing_resolution.json()["details"]["resource_type"] == (
        "relationship_resolution"
    )
    missing_object_id = str(uuid4())
    missing_object = await client.post(
        "/api/v1/core/relationships",
        json={
            "resolution_id": resolution_id,
            "from_object_id": object_id,
            "to_object_id": missing_object_id,
        },
    )
    assert missing_object.status_code == 422
    assert missing_object.json()["details"] == {
        "resource_type": "object",
        "id": missing_object_id,
    }
    incompatible = await client.post(
        "/api/v1/core/relationships",
        json={
            "resolution_id": resolution_id,
            "from_object_id": other_object_id,
            "to_object_id": object_id,
        },
    )
    assert incompatible.status_code == 422
    assert incompatible.json()["code"] == "semantic_validation_failed"
    assert incompatible.json()["details"]["violations"][0]["path"] == ("from_object_id")

    self_loop = await client.post(
        "/api/v1/core/relationships",
        json={
            "resolution_id": resolution_id,
            "from_object_id": object_id,
            "to_object_id": object_id,
        },
    )
    assert self_loop.status_code == 201, self_loop.text
    assert len(self_loop.json()["views"]) == 1
    events = await client.get(
        "/api/v1/core/lifecycle-events",
        params={"relationship_id": self_loop.json()["id"]},
    )
    assert len(events.json()["items"]) == 1


@pytest.mark.api
@pytest.mark.postgresql
async def test_object_relative_keyset_cursor_and_filter_identity(
    relationship_client: httpx.AsyncClient,
) -> None:
    client = relationship_client
    template_id = await _template(client, "page_endpoint")
    first = await _object(client, template_id, "page-first")
    second = await _object(client, template_id, "page-second")
    third = await _object(client, template_id, "page-third")
    definition = await client.post(
        "/api/v1/core/relationship-definitions",
        json={
            "symmetric": True,
            "endpoint_template_ids": [template_id, template_id],
            "name": "linked",
        },
    )
    assert definition.status_code == 201
    definition_value = await _publish_created_definition(client, definition)
    resolution_id = cast(list[dict[str, str]], definition_value["resolutions"])[0][
        "resolution_id"
    ]
    for destination in (second, third):
        created = await client.post(
            "/api/v1/core/relationships",
            json={
                "resolution_id": resolution_id,
                "from_object_id": first,
                "to_object_id": destination,
            },
        )
        assert created.status_code == 201

    first_page = await client.get(
        f"/api/v1/core/objects/{first}/relationships", params={"limit": 1}
    )
    assert first_page.status_code == 200
    assert len(first_page.json()["items"]) == 1
    cursor = first_page.json()["next_cursor"]
    assert cursor is not None
    second_page = await client.get(
        f"/api/v1/core/objects/{first}/relationships",
        params={"cursor": cursor, "limit": 2},
    )
    assert second_page.status_code == 200
    assert len(second_page.json()["items"]) == 1
    invalid = await client.get(
        f"/api/v1/core/objects/{first}/relationships",
        params={"cursor": cursor, "name": "linked"},
    )
    assert invalid.status_code == 400
    assert invalid.json()["code"] == "invalid_cursor"


@pytest.mark.postgresql
async def test_runtime_object_foreign_keys_restrict_and_rollback(
    relationship_client: httpx.AsyncClient,
    migrated_database_engine: Engine,
) -> None:
    client = relationship_client
    template_id = await _template(client, "fk_endpoint")
    first = await _object(client, template_id, "fk-first")
    second = await _object(client, template_id, "fk-second")
    definition = await client.post(
        "/api/v1/core/relationship-definitions",
        json={
            "symmetric": True,
            "endpoint_template_ids": [template_id, template_id],
            "name": "fk_link",
        },
    )
    assert definition.status_code == 201
    definition_value = await _publish_created_definition(client, definition)
    resolution_id = cast(list[dict[str, str]], definition_value["resolutions"])[0][
        "resolution_id"
    ]
    created = await client.post(
        "/api/v1/core/relationships",
        json={
            "resolution_id": resolution_id,
            "from_object_id": first,
            "to_object_id": second,
        },
    )
    relationship_id = created.json()["id"]

    with pytest.raises(IntegrityError):
        with migrated_database_engine.begin() as connection:
            connection.execute(objects.delete().where(objects.c.id == UUID(first)))
    with migrated_database_engine.connect() as connection:
        assert connection.scalar(
            select(relationships.c.id).where(
                relationships.c.id == UUID(relationship_id)
            )
        ) == UUID(relationship_id)
        assert connection.scalar(
            select(objects.c.id).where(objects.c.id == UUID(first))
        ) == UUID(first)


@pytest.mark.api
@pytest.mark.postgresql
async def test_db_valid_incomplete_runtime_aggregate_maps_to_internal_error(
    relationship_client: httpx.AsyncClient,
    migrated_database_engine: Engine,
) -> None:
    client = relationship_client
    template_id = await _template(client, "corrupt_endpoint")
    first = await _object(client, template_id, "corrupt-first")
    second = await _object(client, template_id, "corrupt-second")
    definition = await client.post(
        "/api/v1/core/relationship-definitions",
        json={
            "symmetric": True,
            "endpoint_template_ids": [template_id, template_id],
            "name": "corrupt_link",
        },
    )
    assert definition.status_code == 201
    definition_value = await _publish_created_definition(client, definition)
    definition_id = UUID(cast(str, definition_value["id"]))
    resolution_id = UUID(
        cast(list[dict[str, str]], definition_value["resolutions"])[0]["resolution_id"]
    )
    relationship_id = uuid4()
    with migrated_database_engine.begin() as connection:
        connection.execute(
            insert(relationships).values(
                id=relationship_id,
                relationship_definition_id=definition_id,
                relationship_definition_version=1,
                properties={},
            )
        )
        connection.execute(
            insert(runtime_relationship_resolutions).values(
                relationship_id=relationship_id,
                relationship_definition_id=definition_id,
                resolution_id=resolution_id,
                from_object_id=UUID(first),
                to_object_id=UUID(second),
            )
        )

    response = await client.get(f"/api/v1/core/relationships/{relationship_id}")
    assert response.status_code == 500
    assert response.json() == {
        "code": "internal_error",
        "message": "The persisted factual Relationship aggregate is invalid.",
        "details": {},
    }
    relative = await client.get(f"/api/v1/core/objects/{first}/relationships")
    assert relative.status_code == 500


@pytest.mark.postgresql
async def test_relationship_event_rows_use_database_identity_and_timestamp_defaults(
    relationship_client: httpx.AsyncClient,
    migrated_database_engine: Engine,
) -> None:
    client = relationship_client
    template_id = await _template(client, "event_default_endpoint")
    first = await _object(client, template_id, "event-default-first")
    second = await _object(client, template_id, "event-default-second")
    definition = await client.post(
        "/api/v1/core/relationship-definitions",
        json={
            "symmetric": True,
            "endpoint_template_ids": [template_id, template_id],
            "name": "event_default_link",
        },
    )
    assert definition.status_code == 201
    definition_value = await _publish_created_definition(client, definition)
    created = await client.post(
        "/api/v1/core/relationships",
        json={
            "resolution_id": cast(
                list[dict[str, str]], definition_value["resolutions"]
            )[0]["resolution_id"],
            "from_object_id": first,
            "to_object_id": second,
        },
    )
    relationship_id = UUID(created.json()["id"])
    with migrated_database_engine.connect() as connection:
        rows = connection.execute(
            select(
                object_lifecycle_events.c.id,
                object_lifecycle_events.c.occurred_at,
            ).where(object_lifecycle_events.c.relationship_id == relationship_id)
        ).all()
    assert len(rows) == 2
    assert all(row.id is not None and row.occurred_at is not None for row in rows)
    assert len({row.occurred_at for row in rows}) == 1


async def _published_relationship_datatype(client: httpx.AsyncClient, name: str) -> str:
    created = await client.post(
        "/api/v1/core/datatypes",
        json={
            "namespace": "relationship_runtime",
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


@pytest.mark.api
@pytest.mark.postgresql
async def test_m2_s02_data_schema_change_lifecycle_and_strict_contract(
    relationship_client: httpx.AsyncClient,
) -> None:
    client = relationship_client
    datatype_id = await _published_relationship_datatype(client, "s02_metric")
    first_template = await _template(client, "s02_endpoint_a")
    second_template = await _template(client, "s02_endpoint_b")
    first_object = await _object(client, first_template, "s02-a")
    second_object = await _object(client, second_template, "s02-b")
    scalar_property = {
        "name": "metric",
        "position": 1,
        "datatype_id": datatype_id,
        "value_mode": "SCALAR",
    }
    created_definition = await client.post(
        "/api/v1/core/relationship-definitions",
        json={
            "symmetric": False,
            "perspectives": [
                {"template_id": first_template, "name": "measures"},
                {"template_id": second_template, "name": "measured_by"},
            ],
            "properties": [scalar_property],
        },
    )
    assert created_definition.status_code == 201, created_definition.text
    definition = created_definition.json()["relationship_definition"]
    definition_id = cast(str, definition["id"])
    publish_v1 = await client.post(
        f"/api/v1/core/relationship-definitions/{definition_id}/versions/1/publish",
        params={"expected_revision": 1},
    )
    assert publish_v1.status_code == 200, publish_v1.text

    create_v2 = await client.post(
        f"/api/v1/core/relationship-definitions/{definition_id}/create-next",
        json={"source_version": 1},
    )
    assert create_v2.status_code == 201, create_v2.text
    list_property = {**scalar_property, "value_mode": "LIST"}
    revise_v2 = await client.post(
        f"/api/v1/core/relationship-definitions/{definition_id}/versions/2/revise",
        params={"expected_revision": 1},
        json={"properties": [list_property]},
    )
    assert revise_v2.status_code == 200, revise_v2.text
    publish_v2 = await client.post(
        f"/api/v1/core/relationship-definitions/{definition_id}/versions/2/publish",
        params={"expected_revision": 2},
    )
    assert publish_v2.status_code == 200, publish_v2.text

    create_v3 = await client.post(
        f"/api/v1/core/relationship-definitions/{definition_id}/create-next",
        json={"source_version": 2},
    )
    assert create_v3.status_code == 201, create_v3.text
    publish_v3 = await client.post(
        f"/api/v1/core/relationship-definitions/{definition_id}/versions/3/publish",
        params={"expected_revision": 1},
    )
    assert publish_v3.status_code == 200, publish_v3.text

    create_datatype_v2 = await client.post(
        f"/api/v1/core/datatypes/{datatype_id}/create-next",
        json={"source_version": 1},
    )
    assert create_datatype_v2.status_code == 201, create_datatype_v2.text
    revise_datatype_v2 = await client.post(
        f"/api/v1/core/datatypes/{datatype_id}/versions/2/revise",
        params={"expected_revision": 1},
        json={"constraints": {"maximum": 10}},
    )
    assert revise_datatype_v2.status_code == 200, revise_datatype_v2.text
    publish_datatype_v2 = await client.post(
        f"/api/v1/core/datatypes/{datatype_id}/versions/2/publish",
        params={"expected_revision": 2},
    )
    assert publish_datatype_v2.status_code == 200, publish_datatype_v2.text
    create_v4 = await client.post(
        f"/api/v1/core/relationship-definitions/{definition_id}/create-next",
        json={"source_version": 3},
    )
    assert create_v4.status_code == 201, create_v4.text
    constrained_property = {**list_property, "datatype_version": 2}
    revise_v4 = await client.post(
        f"/api/v1/core/relationship-definitions/{definition_id}/versions/4/revise",
        params={"expected_revision": 1},
        json={"properties": [constrained_property]},
    )
    assert revise_v4.status_code == 200, revise_v4.text
    publish_v4 = await client.post(
        f"/api/v1/core/relationship-definitions/{definition_id}/versions/4/publish",
        params={"expected_revision": 2},
    )
    assert publish_v4.status_code == 200, publish_v4.text

    resolution = _resolution(definition, first_template)
    created = await client.post(
        "/api/v1/core/relationships",
        json={
            "resolution_id": resolution["resolution_id"],
            "from_object_id": first_object,
            "to_object_id": second_object,
            "relationship_definition_version": 1,
            "properties": {"metric": 1},
        },
    )
    assert created.status_code == 201, created.text
    relationship_id = cast(str, created.json()["id"])

    changed = await client.post(
        f"/api/v1/core/relationships/{relationship_id}/data-change",
        json={"operations": [{"op": "SET", "property": "metric", "value": 99}]},
    )
    assert changed.status_code == 200, changed.text
    assert changed.json()["properties"] == {"metric": 99}
    no_op = await client.post(
        f"/api/v1/core/relationships/{relationship_id}/data-change",
        json={"operations": [{"op": "SET", "property": "metric", "value": 99}]},
    )
    assert no_op.status_code == 200
    assert no_op.json() == changed.json()
    data_events = await client.get(
        "/api/v1/core/lifecycle-events",
        params={
            "relationship_id": relationship_id,
            "kind": "RELATIONSHIP_DATA_CHANGE",
        },
    )
    assert len(data_events.json()["items"]) == 2
    assert all(
        item["before"]
        == {"relationship_definition_version": 1, "properties": {"metric": 1}}
        and item["after"]
        == {"relationship_definition_version": 1, "properties": {"metric": 99}}
        for item in data_events.json()["items"]
    )

    schema_v2 = await client.post(
        f"/api/v1/core/relationships/{relationship_id}/schema-change",
        json={"target_version": 2},
    )
    assert schema_v2.status_code == 200, schema_v2.text
    assert schema_v2.json()["properties"] == {"metric": [99]}
    schema_v3 = await client.post(
        f"/api/v1/core/relationships/{relationship_id}/schema-change",
        json={"target_version": 3},
    )
    assert schema_v3.status_code == 200, schema_v3.text
    assert schema_v3.json()["properties"] == {"metric": [99]}
    blocked = await client.post(
        f"/api/v1/core/relationships/{relationship_id}/schema-change",
        json={"target_version": 4},
    )
    assert blocked.status_code == 409, blocked.text
    assert blocked.json()["code"] == "schema_change_blocked"
    assert blocked.json()["details"] == {
        "relationship_id": relationship_id,
        "target_version": 4,
        "blocker_type": "property",
        "member_name": "metric",
    }
    exact = await client.get(f"/api/v1/core/relationships/{relationship_id}")
    assert exact.status_code == 200
    assert exact.json()["relationship_definition_version"] == 3
    assert exact.json()["properties"] == {"metric": [99]}
    schema_events = await client.get(
        "/api/v1/core/lifecycle-events",
        params={
            "relationship_id": relationship_id,
            "kind": "RELATIONSHIP_SCHEMA_CHANGE",
        },
    )
    assert len(schema_events.json()["items"]) == 4
    assert {
        (
            item["before"]["relationship_definition_version"],
            item["after"]["relationship_definition_version"],
        )
        for item in schema_events.json()["items"]
    } == {(1, 2), (2, 3)}

    removed = await client.post(
        f"/api/v1/core/relationships/{relationship_id}/data-change",
        json={"operations": [{"op": "REMOVE", "property": "metric"}]},
    )
    assert removed.status_code == 200, removed.text
    assert removed.json()["properties"] == {}
    remove_noop = await client.post(
        f"/api/v1/core/relationships/{relationship_id}/data-change",
        json={"operations": [{"op": "REMOVE", "property": "metric"}]},
    )
    assert remove_noop.status_code == 200
    assert remove_noop.json() == removed.json()

    invalid_bodies: tuple[dict[str, object], ...] = (
        {"operations": []},
        {
            "operations": [
                {"op": "REMOVE", "property": "metric"},
                {"op": "REMOVE", "property": "metric"},
            ]
        },
        {"operations": [{"op": "REMOVE", "property": "metric", "value": 1}]},
        {"operations": [{"op": "SET", "property": "metric"}]},
        {"operations": [{"op": "UPSERT", "property": "metric", "value": 1}]},
        {"operations": [{"op": "SET", "property": "metric", "value": 1}], "x": 1},
    )
    for body in invalid_bodies:
        response = await client.post(
            f"/api/v1/core/relationships/{relationship_id}/data-change", json=body
        )
        assert response.status_code == 400, response.text
        assert response.json()["code"] == "invalid_request"
    null_value = await client.post(
        f"/api/v1/core/relationships/{relationship_id}/data-change",
        json={"operations": [{"op": "SET", "property": "metric", "value": None}]},
    )
    assert null_value.status_code == 422
    assert null_value.json()["code"] == "semantic_validation_failed"
    repeated_query = await client.post(
        f"/api/v1/core/relationships/{relationship_id}/schema-change?x=1&x=2",
        json={"target_version": 4},
    )
    assert repeated_query.status_code == 400
    nonforward = await client.post(
        f"/api/v1/core/relationships/{relationship_id}/schema-change",
        json={"target_version": 3},
    )
    assert nonforward.status_code == 422
    missing_target = await client.post(
        f"/api/v1/core/relationships/{relationship_id}/schema-change",
        json={"target_version": 999},
    )
    assert missing_target.status_code == 422
    assert missing_target.json()["details"] == {
        "resource_type": "relationship_definition_version",
        "id": definition_id,
        "version": 999,
    }
    draft_v5 = await client.post(
        f"/api/v1/core/relationship-definitions/{definition_id}/create-next",
        json={"source_version": 3},
    )
    assert draft_v5.status_code == 201, draft_v5.text
    nonpublished = await client.post(
        f"/api/v1/core/relationships/{relationship_id}/schema-change",
        json={"target_version": 5},
    )
    assert nonpublished.status_code == 409
    assert nonpublished.json()["code"] == "dependency_not_admissible"
    for invalid_target_body in (
        {"target_version": True},
        {"target_version": 0},
        {"target_version": -1},
        {"target_version": 4, "extra": 1},
        {},
    ):
        invalid_target = await client.post(
            f"/api/v1/core/relationships/{relationship_id}/schema-change",
            json=invalid_target_body,
        )
        assert invalid_target.status_code == 400
        assert invalid_target.json()["code"] == "invalid_request"
    malformed_path = await client.post(
        "/api/v1/core/relationships/not-a-uuid/schema-change",
        json={"target_version": 4},
    )
    assert malformed_path.status_code == 400
    unknown_query = await client.post(
        f"/api/v1/core/relationships/{relationship_id}/data-change?unknown=1",
        json={"operations": [{"op": "REMOVE", "property": "metric"}]},
    )
    assert unknown_query.status_code == 400
    missing_relationship_id = str(uuid4())
    missing_data = await client.post(
        f"/api/v1/core/relationships/{missing_relationship_id}/data-change",
        json={"operations": [{"op": "REMOVE", "property": "metric"}]},
    )
    missing_schema = await client.post(
        f"/api/v1/core/relationships/{missing_relationship_id}/schema-change",
        json={"target_version": 4},
    )
    assert missing_data.status_code == missing_schema.status_code == 404
    assert missing_data.json()["details"] == {
        "resource_type": "relationship",
        "id": missing_relationship_id,
    }

    deleted_relationship = await client.delete(
        f"/api/v1/core/relationships/{relationship_id}"
    )
    assert deleted_relationship.status_code == 204
    deleted_definition = await client.delete(
        f"/api/v1/core/relationship-definitions/{definition_id}"
    )
    assert deleted_definition.status_code == 204, deleted_definition.text
    for object_id in (first_object, second_object):
        deleted_object = await client.delete(f"/api/v1/core/objects/{object_id}")
        assert deleted_object.status_code == 204, deleted_object.text
    deleted_datatype = await client.delete(f"/api/v1/core/datatypes/{datatype_id}")
    assert deleted_datatype.status_code == 204, deleted_datatype.text
    assert (
        await client.get(f"/api/v1/core/relationship-definitions/{definition_id}")
    ).status_code == 404
    assert (
        await client.get(f"/api/v1/core/datatypes/{datatype_id}")
    ).status_code == 404
    for object_id in (first_object, second_object):
        assert (
            await client.get(f"/api/v1/core/objects/{object_id}")
        ).status_code == 404
    historical = await client.get(
        "/api/v1/core/lifecycle-events",
        params={"relationship_id": relationship_id},
    )
    assert historical.status_code == 200, historical.text
    historical_items = historical.json()["items"]
    assert len(historical_items) == 12
    expected_transitions: tuple[
        tuple[str, dict[str, JsonValue] | None, dict[str, JsonValue] | None], ...
    ] = (
        (
            EventKind.RELATIONSHIP_CREATED.value,
            None,
            {"relationship_definition_version": 1, "properties": {"metric": 1}},
        ),
        (
            EventKind.RELATIONSHIP_DATA_CHANGE.value,
            {"relationship_definition_version": 1, "properties": {"metric": 1}},
            {"relationship_definition_version": 1, "properties": {"metric": 99}},
        ),
        (
            EventKind.RELATIONSHIP_SCHEMA_CHANGE.value,
            {"relationship_definition_version": 1, "properties": {"metric": 99}},
            {
                "relationship_definition_version": 2,
                "properties": {"metric": [99]},
            },
        ),
        (
            EventKind.RELATIONSHIP_SCHEMA_CHANGE.value,
            {
                "relationship_definition_version": 2,
                "properties": {"metric": [99]},
            },
            {
                "relationship_definition_version": 3,
                "properties": {"metric": [99]},
            },
        ),
        (
            EventKind.RELATIONSHIP_DATA_CHANGE.value,
            {
                "relationship_definition_version": 3,
                "properties": {"metric": [99]},
            },
            {"relationship_definition_version": 3, "properties": {}},
        ),
        (
            EventKind.RELATIONSHIP_DELETED.value,
            {"relationship_definition_version": 3, "properties": {}},
            None,
        ),
    )
    for kind, before, after in expected_transitions:
        assert (
            sum(
                item["kind"] == kind
                and item["before"] == before
                and item["after"] == after
                for item in historical_items
            )
            == 2
        )
    assert {item["relationship_id"] for item in historical_items} == {relationship_id}
    assert {item["relationship_definition_id"] for item in historical_items} == {
        definition_id
    }
    assert {item["object_id"] for item in historical_items} == {
        first_object,
        second_object,
    }
    assert {item["destination_object_id"] for item in historical_items} == {
        first_object,
        second_object,
    }
    assert {item["relationship_name"] for item in historical_items} == {
        "measures",
        "measured_by",
    }
    assert (
        await client.get(f"/api/v1/core/objects/{first_object}/lifecycle-events")
    ).status_code == 404


@pytest.mark.api
@pytest.mark.postgresql
async def test_m2_s02_corrupt_relationship_transition_fails_complete_page(
    relationship_client: httpx.AsyncClient,
    migrated_database_engine: Engine,
) -> None:
    client = relationship_client
    template_id = await _template(client, "s02_corrupt_event")
    first = await _object(client, template_id, "s02-corrupt-first")
    second = await _object(client, template_id, "s02-corrupt-second")
    created_definition = await client.post(
        "/api/v1/core/relationship-definitions",
        json={
            "symmetric": True,
            "endpoint_template_ids": [template_id, template_id],
            "name": "s02_corrupt_link",
        },
    )
    definition = await _publish_created_definition(client, created_definition)
    resolution_id = cast(list[dict[str, str]], definition["resolutions"])[0][
        "resolution_id"
    ]
    created = await client.post(
        "/api/v1/core/relationships",
        json={
            "resolution_id": resolution_id,
            "from_object_id": first,
            "to_object_id": second,
        },
    )
    assert created.status_code == 201, created.text
    relationship_id = UUID(created.json()["id"])
    invalid_state: dict[str, JsonValue] = {
        "relationship_definition_version": 1,
        "properties": {},
    }
    with migrated_database_engine.begin() as connection:
        event_id = connection.scalar(
            select(object_lifecycle_events.c.id)
            .where(object_lifecycle_events.c.relationship_id == relationship_id)
            .limit(1)
        )
        assert event_id is not None
        connection.execute(
            object_lifecycle_events.update()
            .where(object_lifecycle_events.c.id == event_id)
            .values(
                kind="RELATIONSHIP_DATA_CHANGE",
                before_state=invalid_state,
                after_state=invalid_state,
            )
        )
    response = await client.get(
        "/api/v1/core/lifecycle-events",
        params={"relationship_id": str(relationship_id)},
    )
    assert response.status_code == 500
    assert response.json() == {
        "code": "internal_error",
        "message": "The persisted lifecycle event state is invalid.",
        "details": {},
    }
