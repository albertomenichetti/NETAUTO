"""Real-PostgreSQL API and persistence coverage for factual Relationships."""

from collections.abc import AsyncIterator
from typing import cast
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import Engine, insert, select
from sqlalchemy.exc import IntegrityError

from netauto.entrypoints.http import build_app
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
    return cast(dict[str, object], created.json())


def _resolution(definition: dict[str, object], from_template_id: str) -> dict[str, str]:
    resolutions = cast(list[dict[str, str]], definition["resolutions"])
    return next(
        item for item in resolutions if item["from_template_id"] == from_template_id
    )


@pytest.mark.api
@pytest.mark.postgresql
async def test_create_converge_read_navigate_lifecycle_delete_and_definition_unblock(
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
    assert converged.status_code == 200, converged.text
    assert "location" not in converged.headers
    assert converged.json() == value

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
                "object_id": first_object,
                "destination_object_id": second_object,
                "name": "hosts",
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
        }
        for item in events
    )

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

    deleted = await client.delete(f"/api/v1/core/relationships/{relationship_id}")
    assert deleted.status_code == 204
    repeated = await client.delete(f"/api/v1/core/relationships/{relationship_id}")
    assert repeated.status_code == 204
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
    unblocked = await client.delete(
        f"/api/v1/core/relationship-definitions/{definition['id']}"
    )
    assert unblocked.status_code == 204


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
    resolution_id = definition.json()["resolutions"][0]["resolution_id"]

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
    resolution_id = definition.json()["resolutions"][0]["resolution_id"]
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
    resolution_id = definition.json()["resolutions"][0]["resolution_id"]
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
    definition_id = UUID(definition.json()["id"])
    resolution_id = UUID(definition.json()["resolutions"][0]["resolution_id"])
    relationship_id = uuid4()
    with migrated_database_engine.begin() as connection:
        connection.execute(
            insert(relationships).values(
                id=relationship_id, relationship_definition_id=definition_id
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
    created = await client.post(
        "/api/v1/core/relationships",
        json={
            "resolution_id": definition.json()["resolutions"][0]["resolution_id"],
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
