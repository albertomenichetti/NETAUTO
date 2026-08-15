"""Real-PostgreSQL public API coverage for the intrinsic Object slice."""

from collections.abc import AsyncIterator, Awaitable, Callable
from typing import cast
from uuid import UUID

import httpx
import pytest
from sqlalchemy import Engine, select

from netauto.entrypoints.http import build_app
from netauto.persistence.metadata import (
    object_components,
    object_lifecycle_events,
    objects,
)
from netauto.persistence.objects import EventKind, ObjectStore
from netauto.settings import Settings


@pytest.fixture
async def object_client(
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


async def _datatype(
    client: httpx.AsyncClient,
    name: str,
    *,
    base_type: str = "core.integer",
    constraints: dict[str, object] | None = None,
) -> str:
    created = await client.post(
        "/api/v1/core/datatypes",
        json={
            "namespace": "objects",
            "name": name,
            "base_type": base_type,
            "constraints": constraints or {},
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


async def _template(
    client: httpx.AsyncClient,
    name: str,
    *,
    abstract: bool = False,
    parent_template_id: str | None = None,
    properties: list[dict[str, object]] | None = None,
    components: list[dict[str, object]] | None = None,
    publish: bool = True,
) -> str:
    body: dict[str, object] = {
        "namespace": "objects",
        "name": name,
        "abstract": abstract,
        "properties": properties or [],
        "components": components or [],
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


async def _runtime_schema(client: httpx.AsyncClient) -> tuple[str, str]:
    datatype_id = await _datatype(
        client, "metric", constraints={"minimum": 1, "maximum": 10}
    )
    root_id = await _template(
        client,
        "base",
        abstract=True,
        properties=[
            {
                "name": "required_value",
                "position": 1,
                "datatype_id": datatype_id,
                "value_mode": "SCALAR",
                "required": True,
                "migration_default": 1,
            },
            {
                "name": "values",
                "position": 2,
                "datatype_id": datatype_id,
                "value_mode": "LIST",
                "required": False,
            },
        ],
    )
    child_id = await _template(client, "concrete", parent_template_id=root_id)
    return root_id, child_id


@pytest.mark.api
@pytest.mark.postgresql
async def test_object_create_mutations_reads_lists_and_lifecycle(
    object_client: httpx.AsyncClient,
) -> None:
    _, template_id = await _runtime_schema(object_client)
    created = await object_client.post(
        "/api/v1/core/objects",
        json={
            "template_id": template_id,
            "properties": {"required_value": 2, "values": [2, 2]},
        },
    )
    assert created.status_code == 201, created.text
    value = created.json()
    object_id = value["id"]
    assert value["canonical_name"] == object_id
    assert value["template_version"] == 1
    assert value["properties"] == {"required_value": 2, "values": [2, 2]}
    assert created.headers["location"] == f"/api/v1/core/objects/{object_id}"

    renamed = await object_client.post(
        f"/api/v1/core/objects/{object_id}/rename",
        json={"canonical_name": "  Router 01  "},
    )
    assert renamed.status_code == 200, renamed.text
    assert renamed.json()["canonical_name"] == "  Router 01  "

    changed_body: dict[str, object] = {
        "operations": [
            {"op": "SET", "property": "required_value", "value": 3},
            {"op": "SET", "property": "values", "value": []},
        ]
    }
    changed = await object_client.post(
        f"/api/v1/core/objects/{object_id}/data-change",
        json=changed_body,
    )
    assert changed.status_code == 200, changed.text
    assert changed.json()["properties"] == {"required_value": 3}

    no_op = await object_client.post(
        f"/api/v1/core/objects/{object_id}/data-change",
        json={"operations": [{"op": "SET", "property": "required_value", "value": 3}]},
    )
    assert no_op.status_code == 200

    fetched = await object_client.get(f"/api/v1/core/objects/{object_id}")
    assert fetched.status_code == 200
    assert fetched.json() == changed.json()

    listed = await object_client.get(
        "/api/v1/core/objects",
        params={"template_id": template_id, "canonical_name": "  Router 01  "},
    )
    assert listed.status_code == 200
    assert listed.json()["items"] == [
        {
            "id": object_id,
            "canonical_name": "  Router 01  ",
            "template_id": template_id,
            "template_version": 1,
        }
    ]
    assert "properties" not in listed.json()["items"][0]

    another = await object_client.post(
        "/api/v1/core/objects",
        json={
            "template_id": template_id,
            "canonical_name": "other",
            "properties": {"required_value": 1},
        },
    )
    assert another.status_code == 201
    object_page = await object_client.get("/api/v1/core/objects", params={"limit": 1})
    object_cursor = object_page.json()["next_cursor"]
    assert object_cursor is not None
    continuation = await object_client.get(
        "/api/v1/core/objects", params={"cursor": object_cursor, "limit": 1}
    )
    assert continuation.status_code == 200
    assert continuation.json()["items"]
    object_mismatch = await object_client.get(
        "/api/v1/core/objects",
        params={"cursor": object_cursor, "canonical_name": "other"},
    )
    assert object_mismatch.status_code == 400
    assert object_mismatch.json()["code"] == "invalid_cursor"

    lifecycle = await object_client.get(
        f"/api/v1/core/objects/{object_id}/lifecycle-events"
    )
    assert lifecycle.status_code == 200, lifecycle.text
    events = lifecycle.json()["items"]
    assert [item["kind"] for item in events] == [
        "DATA_CHANGE",
        "RENAME",
        "CREATED",
    ]
    expected_event_fields = {
        "id",
        "occurred_at",
        "kind",
        "object_id",
        "canonical_name",
        "before",
        "after",
    }
    assert all(set(item) == expected_event_fields for item in events)
    assert events[-1]["before"] is None
    assert events[-1]["after"]["id"] == object_id
    assert events[1]["before"]["canonical_name"] == object_id
    assert events[1]["after"]["canonical_name"] == "  Router 01  "
    assert events[0]["before"]["properties"]["values"] == [2, 2]
    assert events[0]["after"]["properties"] == {"required_value": 3}
    assert all(item["id"] and item["occurred_at"].endswith("Z") for item in events)

    structural_kind = await object_client.get(
        "/api/v1/core/lifecycle-events", params={"kind": "ATTACH_TO"}
    )
    assert structural_kind.status_code == 200, structural_kind.text
    assert structural_kind.json() == {"items": [], "next_cursor": None}

    first_page = await object_client.get(
        "/api/v1/core/lifecycle-events", params={"limit": 1}
    )
    assert first_page.status_code == 200
    cursor = first_page.json()["next_cursor"]
    assert cursor is not None
    second_page = await object_client.get(
        "/api/v1/core/lifecycle-events", params={"limit": 2, "cursor": cursor}
    )
    assert second_page.status_code == 200
    mismatch = await object_client.get(
        "/api/v1/core/lifecycle-events",
        params={"cursor": cursor, "kind": "CREATED"},
    )
    assert mismatch.status_code == 400
    assert mismatch.json()["code"] == "invalid_cursor"


@pytest.mark.api
@pytest.mark.postgresql
async def test_object_admission_runtime_failures_and_strict_transport(
    object_client: httpx.AsyncClient,
) -> None:
    root_id, template_id = await _runtime_schema(object_client)
    missing_required = await object_client.post(
        "/api/v1/core/objects", json={"template_id": template_id}
    )
    assert missing_required.status_code == 422
    assert missing_required.json()["code"] == "semantic_validation_failed"

    abstract = await object_client.post(
        "/api/v1/core/objects",
        json={"template_id": root_id, "properties": {"required_value": 1}},
    )
    assert abstract.status_code == 422

    draft_id = await _template(object_client, "draft", publish=False)
    draft = await object_client.post(
        "/api/v1/core/objects",
        json={"template_id": draft_id, "template_version": 1},
    )
    assert draft.status_code == 409
    assert draft.json()["code"] == "dependency_not_admissible"
    no_default = await object_client.post(
        "/api/v1/core/objects", json={"template_id": draft_id}
    )
    assert no_default.status_code == 409
    assert no_default.json()["code"] == "default_version_unavailable"

    missing = await object_client.post(
        "/api/v1/core/objects",
        json={"template_id": "00000000-0000-0000-0000-000000000001"},
    )
    assert missing.status_code == 422
    assert missing.json()["code"] == "referenced_resource_not_found"

    for body in (
        {"template_id": template_id, "template_version": None},
        {"template_id": template_id, "canonical_name": None},
        {"template_id": template_id, "properties": None},
        {"template_id": template_id, "unknown": True},
    ):
        response = await object_client.post("/api/v1/core/objects", json=body)
        assert response.status_code == 400
        assert response.json()["code"] == "invalid_request"

    created = await object_client.post(
        "/api/v1/core/objects",
        json={"template_id": template_id, "properties": {"required_value": 2}},
    )
    object_id = created.json()["id"]
    invalid_changes: tuple[dict[str, object], ...] = (
        {"operations": []},
        {
            "operations": [
                {"op": "SET", "property": "required_value", "value": 2},
                {"op": "REMOVE", "property": "required_value"},
            ]
        },
        {"operations": [{"op": "REMOVE", "property": "required_value", "value": 2}]},
    )
    for body in invalid_changes:
        response = await object_client.post(
            f"/api/v1/core/objects/{object_id}/data-change", json=body
        )
        assert response.status_code == 400

    null_set = await object_client.post(
        f"/api/v1/core/objects/{object_id}/data-change",
        json={
            "operations": [{"op": "SET", "property": "required_value", "value": None}]
        },
    )
    assert null_set.status_code == 422
    dependent = await object_client.get(
        "/api/v1/core/objects", params={"template_version": 1}
    )
    assert dependent.status_code == 400
    missing_schema = await object_client.post(
        f"/api/v1/core/objects/{object_id}/schema-change",
        json={"target_version": 2},
    )
    assert missing_schema.status_code == 422
    assert missing_schema.json()["code"] == "referenced_resource_not_found"
    assert (
        await object_client.delete(f"/api/v1/core/objects/{object_id}")
    ).status_code == 405


@pytest.mark.api
@pytest.mark.postgresql
async def test_s05_ownership_schema_change_reads_and_lifecycle(
    object_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    datatype_id = await _datatype(object_client, "schema_metric")
    target_root = await _template(object_client, "component_base", abstract=True)
    target_child = await _template(
        object_client, "component_leaf", parent_template_id=target_root
    )
    property_v1: dict[str, object] = {
        "name": "metric",
        "position": 1,
        "datatype_id": datatype_id,
        "datatype_version": 1,
        "value_mode": "SCALAR",
        "required": True,
        "migration_default": 1,
    }
    component: dict[str, object] = {
        "name": "parts",
        "position": 1,
        "target_template_id": target_root,
    }
    parent_template = await _template(
        object_client,
        "component_owner",
        properties=[property_v1],
        components=[component],
    )

    next_version = await object_client.post(
        f"/api/v1/core/object-templates/{parent_template}/create-next",
        json={"source_version": 1},
    )
    assert next_version.status_code == 201, next_version.text
    property_v2 = dict(property_v1)
    property_v2["value_mode"] = "LIST"
    property_v2["migration_default"] = [1]
    property_v2_new: dict[str, object] = {
        "name": "added",
        "position": 2,
        "datatype_id": datatype_id,
        "datatype_version": 1,
        "value_mode": "SCALAR",
        "required": True,
        "migration_default": 7,
    }
    revised_v2 = await object_client.post(
        f"/api/v1/core/object-templates/{parent_template}/versions/2/revise",
        params={"expected_revision": 1},
        json={
            "properties": [property_v2, property_v2_new],
            "components": [component],
        },
    )
    assert revised_v2.status_code == 200, revised_v2.text
    published_v2 = await object_client.post(
        f"/api/v1/core/object-templates/{parent_template}/versions/2/publish",
        params={"expected_revision": 2},
    )
    assert published_v2.status_code == 200, published_v2.text

    assert (
        await object_client.post(
            f"/api/v1/core/object-templates/{parent_template}/create-next",
            json={"source_version": 2},
        )
    ).status_code == 201
    revised_v3 = await object_client.post(
        f"/api/v1/core/object-templates/{parent_template}/versions/3/revise",
        params={"expected_revision": 1},
        json={"properties": [property_v2, property_v2_new], "components": []},
    )
    assert revised_v3.status_code == 200, revised_v3.text
    assert (
        await object_client.post(
            f"/api/v1/core/object-templates/{parent_template}/versions/3/publish",
            params={"expected_revision": 2},
        )
    ).status_code == 200

    parent = await object_client.post(
        "/api/v1/core/objects",
        json={"template_id": parent_template, "properties": {"metric": 2}},
    )
    other_parent = await object_client.post(
        "/api/v1/core/objects",
        json={"template_id": parent_template, "properties": {"metric": 3}},
    )
    child = await object_client.post(
        "/api/v1/core/objects", json={"template_id": target_child}
    )
    assert parent.status_code == other_parent.status_code == child.status_code == 201
    parent_id = parent.json()["id"]
    other_parent_id = other_parent.json()["id"]
    child_id = child.json()["id"]
    body = {"slot_name": "parts", "child_object_id": child_id}

    attached = await object_client.post(
        f"/api/v1/core/objects/{parent_id}/attach", json=body
    )
    assert attached.status_code == 200, attached.text
    assert attached.json() == {
        "slot_declaring_template_id": parent_template,
        "slot_name": "parts",
        "child_object_id": child_id,
    }
    assert (
        await object_client.post(f"/api/v1/core/objects/{parent_id}/attach", json=body)
    ).json() == attached.json()
    conflict = await object_client.post(
        f"/api/v1/core/objects/{other_parent_id}/attach", json=body
    )
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "ownership_conflict"

    components = await object_client.get(
        f"/api/v1/core/objects/{parent_id}/components",
        params={"slot_name": "parts"},
    )
    assert components.json() == {"items": [attached.json()], "next_cursor": None}
    owner = await object_client.get(f"/api/v1/core/objects/{child_id}/owner")
    assert owner.json() == {
        "parent_object_id": parent_id,
        "slot_declaring_template_id": parent_template,
        "slot_name": "parts",
    }

    migrated = await object_client.post(
        f"/api/v1/core/objects/{parent_id}/schema-change",
        json={"target_version": 2},
    )
    assert migrated.status_code == 200, migrated.text
    assert migrated.json()["template_version"] == 2
    assert migrated.json()["properties"] == {"metric": [2], "added": 7}
    blocked = await object_client.post(
        f"/api/v1/core/objects/{parent_id}/schema-change",
        json={"target_version": 3},
    )
    assert blocked.status_code == 409
    assert blocked.json()["code"] == "schema_change_blocked"

    child_timeline = await object_client.get(
        f"/api/v1/core/objects/{child_id}/lifecycle-events"
    )
    attach_events = [
        item for item in child_timeline.json()["items"] if item["kind"] == "ATTACH_TO"
    ]
    assert len(attach_events) == 1
    assert set(attach_events[0]) == {
        "id",
        "occurred_at",
        "kind",
        "object_id",
        "canonical_name",
        "destination_object_id",
        "destination_canonical_name",
        "slot_declaring_template_id",
        "slot_name",
    }
    parent_timeline = await object_client.get(
        f"/api/v1/core/objects/{parent_id}/lifecycle-events"
    )
    assert any(item["kind"] == "ATTACH_TO" for item in parent_timeline.json()["items"])

    detached = await object_client.post(
        f"/api/v1/core/objects/{parent_id}/detach", json=body
    )
    assert detached.status_code == 204 and detached.content == b""
    assert (
        await object_client.post(f"/api/v1/core/objects/{parent_id}/detach", json=body)
    ).status_code == 204
    assert (
        await object_client.get(f"/api/v1/core/objects/{child_id}/owner")
    ).json() is None
    original_event = ObjectStore.insert_intrinsic_event

    async def fail_schema_event(
        store: ObjectStore, kind: EventKind, *args: object
    ) -> object:
        if kind is EventKind.SCHEMA_CHANGE:
            raise RuntimeError("forced schema-change event failure")
        return await cast(Callable[..., Awaitable[object]], original_event)(
            store, kind, *args
        )

    with monkeypatch.context() as context:
        context.setattr(ObjectStore, "insert_intrinsic_event", fail_schema_event)
        failed_schema = await object_client.post(
            f"/api/v1/core/objects/{parent_id}/schema-change",
            json={"target_version": 3},
        )
    assert failed_schema.status_code == 500
    still_v2 = await object_client.get(f"/api/v1/core/objects/{parent_id}")
    assert still_v2.json()["template_version"] == 2
    final = await object_client.post(
        f"/api/v1/core/objects/{parent_id}/schema-change",
        json={"target_version": 3},
    )
    assert final.status_code == 200, final.text


@pytest.mark.api
@pytest.mark.postgresql
async def test_s05_ownership_failures_cycle_and_atomic_event(
    object_client: httpx.AsyncClient,
    migrated_database_engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    template_id = await _template(object_client, "cycle_node")
    assert (
        await object_client.post(
            f"/api/v1/core/object-templates/{template_id}/create-next",
            json={"source_version": 1},
        )
    ).status_code == 201
    component = {
        "name": "children",
        "position": 1,
        "target_template_id": template_id,
    }
    revised = await object_client.post(
        f"/api/v1/core/object-templates/{template_id}/versions/2/revise",
        params={"expected_revision": 1},
        json={"properties": [], "components": [component]},
    )
    assert revised.status_code == 200, revised.text
    assert (
        await object_client.post(
            f"/api/v1/core/object-templates/{template_id}/versions/2/publish",
            params={"expected_revision": 2},
        )
    ).status_code == 200

    nodes: list[str] = []
    for name in ("a", "b", "c"):
        created = await object_client.post(
            "/api/v1/core/objects",
            json={
                "template_id": template_id,
                "template_version": 2,
                "canonical_name": name,
            },
        )
        assert created.status_code == 201, created.text
        nodes.append(cast(str, created.json()["id"]))
    a, b, c = nodes

    missing_parent = await object_client.post(
        "/api/v1/core/objects/00000000-0000-0000-0000-000000000001/attach",
        json={"slot_name": "children", "child_object_id": a},
    )
    assert missing_parent.status_code == 404
    missing_child = await object_client.post(
        f"/api/v1/core/objects/{a}/attach",
        json={
            "slot_name": "children",
            "child_object_id": "00000000-0000-0000-0000-000000000001",
        },
    )
    assert missing_child.status_code == 422
    assert missing_child.json()["code"] == "referenced_resource_not_found"
    unavailable = await object_client.post(
        f"/api/v1/core/objects/{a}/attach",
        json={"slot_name": "missing", "child_object_id": b},
    )
    assert unavailable.status_code == 409
    assert unavailable.json()["code"] == "ownership_slot_unavailable"
    self_attach = await object_client.post(
        f"/api/v1/core/objects/{a}/attach",
        json={"slot_name": "children", "child_object_id": a},
    )
    assert self_attach.status_code == 422

    assert (
        await object_client.post(
            f"/api/v1/core/objects/{a}/attach",
            json={"slot_name": "children", "child_object_id": b},
        )
    ).status_code == 200
    assert (
        await object_client.post(
            f"/api/v1/core/objects/{b}/attach",
            json={"slot_name": "children", "child_object_id": c},
        )
    ).status_code == 200
    cycle = await object_client.post(
        f"/api/v1/core/objects/{c}/attach",
        json={"slot_name": "children", "child_object_id": a},
    )
    assert cycle.status_code == 409
    assert cycle.json()["code"] == "ownership_cycle"
    mismatch = await object_client.post(
        f"/api/v1/core/objects/{c}/detach",
        json={"slot_name": "children", "child_object_id": b},
    )
    assert mismatch.status_code == 409
    assert mismatch.json()["code"] == "ownership_mismatch"

    async def fail_event(store: ObjectStore, *args: object, **kwargs: object) -> object:
        del store, args, kwargs
        raise RuntimeError("forced ownership event failure")

    with monkeypatch.context() as context:
        context.setattr(ObjectStore, "insert_ownership_event", fail_event)
        failed = await object_client.post(
            f"/api/v1/core/objects/{a}/attach",
            json={"slot_name": "children", "child_object_id": c},
        )
    assert failed.status_code == 409  # C is still owned; no event hook is reached.

    await object_client.post(
        f"/api/v1/core/objects/{b}/detach",
        json={"slot_name": "children", "child_object_id": c},
    )
    with monkeypatch.context() as context:
        context.setattr(ObjectStore, "insert_ownership_event", fail_event)
        failed = await object_client.post(
            f"/api/v1/core/objects/{a}/attach",
            json={"slot_name": "children", "child_object_id": c},
        )
    assert failed.status_code == 500
    with migrated_database_engine.connect() as connection:
        assert (
            connection.scalar(
                select(object_components.c.parent_object_id).where(
                    object_components.c.child_object_id == UUID(c)
                )
            )
            is None
        )
    retry = await object_client.post(
        f"/api/v1/core/objects/{a}/attach",
        json={"slot_name": "children", "child_object_id": c},
    )
    assert retry.status_code == 200, retry.text
    assert (
        await object_client.post(
            f"/api/v1/core/objects/{a}/detach",
            json={"slot_name": "children", "child_object_id": c},
        )
    ).status_code == 204

    with migrated_database_engine.begin() as connection:
        connection.execute(
            object_components.update()
            .where(object_components.c.child_object_id == UUID(b))
            .values(slot_name="ghost")
        )
    for response in (
        await object_client.get(f"/api/v1/core/objects/{a}/components"),
        await object_client.get(f"/api/v1/core/objects/{b}/owner"),
        await object_client.post(
            f"/api/v1/core/objects/{a}/detach",
            json={"slot_name": "ghost", "child_object_id": b},
        ),
    ):
        assert response.status_code == 500
        assert response.json()["code"] == "internal_error"


@pytest.mark.api
@pytest.mark.postgresql
async def test_existing_object_on_deprecated_schema_remains_mutable(
    object_client: httpx.AsyncClient,
) -> None:
    _, template_id = await _runtime_schema(object_client)
    created = await object_client.post(
        "/api/v1/core/objects",
        json={"template_id": template_id, "properties": {"required_value": 2}},
    )
    object_id = created.json()["id"]
    assert (
        await object_client.post(
            f"/api/v1/core/object-templates/{template_id}/clear-default"
        )
    ).status_code == 200
    deprecated = await object_client.post(
        f"/api/v1/core/object-templates/{template_id}/versions/1/deprecate"
    )
    assert deprecated.status_code == 200, deprecated.text
    assert (
        await object_client.post(
            f"/api/v1/core/objects/{object_id}/rename",
            json={"canonical_name": "legacy"},
        )
    ).status_code == 200
    changed = await object_client.post(
        f"/api/v1/core/objects/{object_id}/data-change",
        json={"operations": [{"op": "SET", "property": "required_value", "value": 4}]},
    )
    assert changed.status_code == 200
    assert changed.json()["properties"] == {"required_value": 4}


@pytest.mark.api
@pytest.mark.postgresql
async def test_intrinsic_state_event_atomic_rollback(
    object_client: httpx.AsyncClient,
    migrated_database_engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    _, template_id = await _runtime_schema(object_client)
    original = ObjectStore.insert_intrinsic_event

    async def fail_create(store: ObjectStore, kind: EventKind, *args: object) -> object:
        if kind is EventKind.CREATED:
            raise RuntimeError("forced created-event failure")
        return await cast(Callable[..., Awaitable[object]], original)(
            store, kind, *args
        )

    with monkeypatch.context() as context:
        context.setattr(ObjectStore, "insert_intrinsic_event", fail_create)
        failed_create = await object_client.post(
            "/api/v1/core/objects",
            json={
                "template_id": template_id,
                "canonical_name": "must-not-exist",
                "properties": {"required_value": 2},
            },
        )
    assert failed_create.status_code == 500
    absent = await object_client.get(
        "/api/v1/core/objects", params={"canonical_name": "must-not-exist"}
    )
    assert absent.json()["items"] == []

    created = await object_client.post(
        "/api/v1/core/objects",
        json={"template_id": template_id, "properties": {"required_value": 2}},
    )
    object_id = created.json()["id"]

    async def fail_rename(store: ObjectStore, kind: EventKind, *args: object) -> object:
        if kind is EventKind.RENAME:
            raise RuntimeError("forced event failure")
        return await cast(Callable[..., Awaitable[object]], original)(
            store, kind, *args
        )

    monkeypatch.setattr(ObjectStore, "insert_intrinsic_event", fail_rename)
    failed = await object_client.post(
        f"/api/v1/core/objects/{object_id}/rename",
        json={"canonical_name": "must-rollback"},
    )
    assert failed.status_code == 500
    current = await object_client.get(f"/api/v1/core/objects/{object_id}")
    assert current.json()["canonical_name"] == object_id
    lifecycle = await object_client.get(
        f"/api/v1/core/objects/{object_id}/lifecycle-events"
    )
    assert [item["kind"] for item in lifecycle.json()["items"]] == ["CREATED"]


@pytest.mark.api
@pytest.mark.postgresql
async def test_persisted_intrinsic_event_corruption_maps_internal_error(
    object_client: httpx.AsyncClient, migrated_database_engine: Engine
) -> None:
    _, template_id = await _runtime_schema(object_client)
    created = await object_client.post(
        "/api/v1/core/objects",
        json={"template_id": template_id, "properties": {"required_value": 2}},
    )
    object_id = UUID(created.json()["id"])
    with migrated_database_engine.begin() as connection:
        connection.execute(
            objects.update().where(objects.c.id == object_id).values(properties={})
        )
    corrupt_object = await object_client.get(f"/api/v1/core/objects/{object_id}")
    assert corrupt_object.status_code == 500
    assert corrupt_object.json()["code"] == "internal_error"
    with migrated_database_engine.begin() as connection:
        connection.execute(
            objects.update()
            .where(objects.c.id == object_id)
            .values(properties={"required_value": 2})
        )
        event_id = connection.scalar(
            select(object_lifecycle_events.c.id).where(
                object_lifecycle_events.c.object_id == object_id
            )
        )
        connection.execute(
            object_lifecycle_events.update()
            .where(object_lifecycle_events.c.id == event_id)
            .values(after_state={"invalid": "snapshot"})
        )
        assert (
            connection.scalar(select(objects.c.id).where(objects.c.id == object_id))
            == object_id
        )
    response = await object_client.get(
        f"/api/v1/core/objects/{object_id}/lifecycle-events"
    )
    assert response.status_code == 500
    assert response.json() == {
        "code": "internal_error",
        "message": "The persisted lifecycle event state is invalid.",
        "details": {},
    }
