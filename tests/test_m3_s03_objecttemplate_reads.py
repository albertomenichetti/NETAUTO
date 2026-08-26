"""M3-S03 ObjectTemplate trusted one-statement read evidence."""

import ast
import inspect
import textwrap
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from typing import cast
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import Engine, event
from sqlalchemy.ext.asyncio import AsyncEngine

from netauto.application.cursors import encode_cursor
from netauto.application.objecttemplates import ObjectTemplateService
from netauto.application.relationshipdefinitions import RelationshipDefinitionService
from netauto.domain.datatypes import VersionStatus
from netauto.domain.objecttemplates import ValueMode
from netauto.entrypoints.http import build_app
from netauto.persistence.engine import RuntimeContext
from netauto.persistence.metadata import (
    object_template_components,
    object_template_properties,
    object_template_versions,
    object_templates,
    relationship_definition_versions,
    relationship_definitions,
)
from netauto.persistence.objecttemplates import ObjectTemplateStore
from netauto.persistence.relationships import RelationshipDefinitionStore
from netauto.settings import Settings
from netauto.transport.http.objecttemplates import PropertyDto


@dataclass(frozen=True, slots=True)
class M3S03Runtime:
    client: httpx.AsyncClient
    engine: AsyncEngine
    database_engine: Engine


@pytest.fixture
async def m3_s03_runtime(
    migrated_database_engine: Engine, test_database_url: str
) -> AsyncIterator[M3S03Runtime]:
    app = build_app(Settings(database_url=test_database_url))
    async with app.router.lifespan_context(app):
        runtime = cast(RuntimeContext, app.state.runtime)
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            yield M3S03Runtime(client, runtime.engine, migrated_database_engine)


async def _published_datatype(client: httpx.AsyncClient, name: str) -> str:
    created = await client.post(
        "/api/v1/core/datatypes",
        json={
            "namespace": "m3s03",
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


async def _template(
    client: httpx.AsyncClient,
    name: str,
    *,
    namespace: str = "m3s03",
    abstract: bool = False,
    parent_template_id: str | None = None,
    parent_version: int | None = None,
    properties: list[dict[str, object]] | None = None,
    components: list[dict[str, object]] | None = None,
) -> str:
    body: dict[str, object] = {
        "namespace": namespace,
        "name": name,
        "abstract": abstract,
    }
    if parent_template_id is not None:
        body["parent_template_id"] = parent_template_id
    if parent_version is not None:
        body["parent_version"] = parent_version
    if properties is not None:
        body["properties"] = properties
    if components is not None:
        body["components"] = components
    created = await client.post("/api/v1/core/object-templates", json=body)
    assert created.status_code == 201, created.text
    return cast(str, created.json()["object_template"]["id"])


async def _publish_template(client: httpx.AsyncClient, template_id: str) -> None:
    published = await client.post(
        f"/api/v1/core/object-templates/{template_id}/versions/1/publish",
        params={"expected_revision": 1},
    )
    assert published.status_code == 200, published.text


async def _published_symmetric_definition(
    client: httpx.AsyncClient, template_id: str, name: str
) -> str:
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
    return definition_id


@pytest.mark.api
@pytest.mark.postgresql
async def test_m3_s03_direct_reads_and_parent_page_trust_persisted_default(
    m3_s03_runtime: M3S03Runtime,
) -> None:
    client = m3_s03_runtime.client
    template_id = await _template(client, "trusted_default")
    with m3_s03_runtime.database_engine.begin() as connection:
        connection.execute(
            object_templates.update()
            .where(object_templates.c.id == UUID(template_id))
            .values(default_version=1)
        )

    exact = await client.get(f"/api/v1/core/object-templates/{template_id}")
    page = await client.get(
        "/api/v1/core/object-templates",
        params={"namespace": "m3s03", "name": "trusted_default"},
    )
    assert exact.status_code == 200, exact.text
    assert exact.json()["default_version"] == 1
    assert page.status_code == 200, page.text
    assert page.json()["items"][0]["default_version"] == 1

    empty_exact = await client.get(
        f"/api/v1/core/object-templates/{template_id}/versions/1"
    )
    empty_effective = await client.get(
        f"/api/v1/core/object-templates/{template_id}/versions/1/effective-schema"
    )
    empty_capabilities = await client.get(
        f"/api/v1/core/object-templates/{template_id}/relationship-capabilities"
    )
    assert empty_exact.status_code == 200, empty_exact.text
    assert empty_exact.json()["properties"] == []
    assert empty_exact.json()["components"] == []
    assert empty_effective.status_code == 200, empty_effective.text
    assert empty_effective.json()["properties"] == []
    assert empty_effective.json()["components"] == []
    assert empty_capabilities.status_code == 200, empty_capabilities.text
    assert empty_capabilities.json() == {"items": [], "next_cursor": None}

    rejected_default = await client.post(
        f"/api/v1/core/object-templates/{template_id}/set-default",
        json={"version": 1},
    )
    assert rejected_default.status_code == 409
    assert rejected_default.json()["code"] == "dependency_not_admissible"

    missing_id = uuid4()
    existing_empty = await client.get(
        f"/api/v1/core/object-templates/{template_id}/versions",
        params={"status": "PUBLISHED"},
    )
    missing_requests = (
        f"/api/v1/core/object-templates/{missing_id}",
        f"/api/v1/core/object-templates/{missing_id}/versions",
        f"/api/v1/core/object-templates/{template_id}/versions/99",
        f"/api/v1/core/object-templates/{template_id}/versions/99/effective-schema",
        f"/api/v1/core/object-templates/{missing_id}/relationship-capabilities",
    )
    assert existing_empty.status_code == 200, existing_empty.text
    assert existing_empty.json() == {"items": [], "next_cursor": None}
    for path in missing_requests:
        response = await client.get(path)
        assert response.status_code == 404, (path, response.text)
        assert response.json()["code"] == "resource_not_found"

    invalid_requests = (
        await client.get(
            "/api/v1/core/object-templates",
            params=[("limit", "1"), ("limit", "2")],
        ),
        await client.get(
            f"/api/v1/core/object-templates/{template_id}",
            params={"expand": "versions"},
        ),
        await client.get("/api/v1/core/object-templates/not-a-uuid"),
        await client.get(
            f"/api/v1/core/object-templates/{template_id}/versions/not-an-integer"
        ),
        await client.get(
            f"/api/v1/core/object-templates/{template_id}/versions",
            params={"status": "UNKNOWN"},
        ),
    )
    for response in invalid_requests:
        assert response.status_code == 400, response.text
        assert response.json()["code"] == "invalid_request"


@pytest.mark.api
@pytest.mark.postgresql
async def test_m3_s03_exact_aggregate_keeps_independent_ordered_child_sets(
    m3_s03_runtime: M3S03Runtime,
) -> None:
    client = m3_s03_runtime.client
    datatype_id = await _published_datatype(client, "aggregate_value")
    first_target = await _template(client, "aggregate_target_a")
    second_target = await _template(client, "aggregate_target_b")
    template_id = await _template(
        client,
        "aggregate",
        properties=[
            {
                "name": "second_property",
                "position": 2,
                "datatype_id": datatype_id,
                "datatype_version": 1,
                "value_mode": "SCALAR",
                "required": False,
            },
            {
                "name": "first_property",
                "position": 1,
                "datatype_id": datatype_id,
                "datatype_version": 1,
                "value_mode": "SCALAR",
                "required": False,
            },
        ],
        components=[
            {
                "name": "second_component",
                "position": 2,
                "target_template_id": second_target,
            },
            {
                "name": "first_component",
                "position": 1,
                "target_template_id": first_target,
            },
        ],
    )

    response = await client.get(
        f"/api/v1/core/object-templates/{template_id}/versions/1"
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert [item["name"] for item in payload["properties"]] == [
        "first_property",
        "second_property",
    ]
    assert [item["name"] for item in payload["components"]] == [
        "first_component",
        "second_component",
    ]
    assert len(payload["properties"]) == 2
    assert len(payload["components"]) == 2


@pytest.mark.api
@pytest.mark.postgresql
async def test_m3_s03_exact_pin_and_stable_ancestry_are_distinct_and_writes_stay_strong(
    m3_s03_runtime: M3S03Runtime,
) -> None:
    client = m3_s03_runtime.client
    datatype_id = await _published_datatype(client, "ancestry_value")
    stable_parent = await _template(
        client,
        "stable_parent",
        abstract=True,
        properties=[
            {
                "name": "stable_member",
                "position": 1,
                "datatype_id": datatype_id,
                "datatype_version": 1,
                "value_mode": "SCALAR",
                "required": False,
            }
        ],
    )
    exact_parent = await _template(
        client,
        "exact_parent",
        abstract=True,
        properties=[
            {
                "name": "exact_member",
                "position": 1,
                "datatype_id": datatype_id,
                "datatype_version": 1,
                "value_mode": "SCALAR",
                "required": False,
            }
        ],
    )
    await _publish_template(client, stable_parent)
    await _publish_template(client, exact_parent)
    child_id = await _template(
        client,
        "ancestry_child",
        parent_template_id=stable_parent,
        parent_version=1,
    )

    with m3_s03_runtime.database_engine.begin() as connection:
        connection.execute(
            object_template_versions.update()
            .where(
                object_template_versions.c.template_id == UUID(child_id),
                object_template_versions.c.version == 1,
            )
            .values(parent_template_id=UUID(exact_parent), parent_version=1)
        )

    stable_definition = await _published_symmetric_definition(
        client, stable_parent, "stable_capability"
    )
    exact_definition = await _published_symmetric_definition(
        client, exact_parent, "exact_capability"
    )
    effective = await client.get(
        f"/api/v1/core/object-templates/{child_id}/versions/1/effective-schema"
    )
    capabilities = await client.get(
        f"/api/v1/core/object-templates/{child_id}/relationship-capabilities"
    )
    assert effective.status_code == 200, effective.text
    assert [item["name"] for item in effective.json()["properties"]] == ["exact_member"]
    assert capabilities.status_code == 200, capabilities.text
    capability_definition_ids = {
        item["relationship_definition_id"] for item in capabilities.json()["items"]
    }
    assert stable_definition in capability_definition_ids
    assert exact_definition not in capability_definition_ids

    inherited_collision = await client.post(
        f"/api/v1/core/object-templates/{child_id}/versions/1/revise",
        params={"expected_revision": 1},
        json={
            "parent_version": 1,
            "properties": [
                {
                    "name": "stable_member",
                    "position": 1,
                    "datatype_id": datatype_id,
                    "datatype_version": 1,
                    "value_mode": "SCALAR",
                    "required": False,
                }
            ],
            "components": [],
        },
    )
    assert inherited_collision.status_code == 422, inherited_collision.text
    assert inherited_collision.json()["code"] == "semantic_validation_failed"

    missing_component_target = await client.post(
        "/api/v1/core/object-templates",
        json={
            "namespace": "m3s03",
            "name": "missing_component_target",
            "abstract": False,
            "components": [
                {
                    "name": "missing",
                    "position": 1,
                    "target_template_id": str(uuid4()),
                }
            ],
        },
    )
    assert missing_component_target.status_code == 422
    assert missing_component_target.json()["code"] == "referenced_resource_not_found"

    draft_parent = await _template(client, "draft_parent")
    inadmissible_parent = await client.post(
        "/api/v1/core/object-templates",
        json={
            "namespace": "m3s03",
            "name": "inadmissible_parent",
            "abstract": False,
            "parent_template_id": draft_parent,
            "parent_version": 1,
        },
    )
    assert inadmissible_parent.status_code == 409
    assert inadmissible_parent.json()["code"] == "dependency_not_admissible"


@pytest.mark.api
@pytest.mark.postgresql
async def test_m3_s03_exact_chain_keeps_repeated_stable_id_at_distinct_versions(
    m3_s03_runtime: M3S03Runtime,
) -> None:
    client = m3_s03_runtime.client
    datatype_id = await _published_datatype(client, "exact_pair_value")
    template_a = await _template(
        client,
        "exact_pair_a",
        abstract=True,
        properties=[
            {
                "name": "a1_member",
                "position": 1,
                "datatype_id": datatype_id,
                "datatype_version": 1,
                "value_mode": "SCALAR",
                "required": False,
            }
        ],
    )
    await _publish_template(client, template_a)
    template_b = await _template(
        client,
        "exact_pair_b",
        abstract=True,
        parent_template_id=template_a,
        parent_version=1,
        properties=[
            {
                "name": "b1_member",
                "position": 1,
                "datatype_id": datatype_id,
                "datatype_version": 1,
                "value_mode": "SCALAR",
                "required": False,
            }
        ],
    )
    created_next = await client.post(
        f"/api/v1/core/object-templates/{template_a}/create-next",
        json={"source_version": 1},
    )
    assert created_next.status_code == 201, created_next.text

    with m3_s03_runtime.database_engine.begin() as connection:
        connection.execute(
            object_template_versions.update()
            .where(
                object_template_versions.c.template_id == UUID(template_a),
                object_template_versions.c.version == 2,
            )
            .values(parent_template_id=UUID(template_b), parent_version=1)
        )
        connection.execute(
            object_template_properties.update()
            .where(
                object_template_properties.c.template_id == UUID(template_a),
                object_template_properties.c.template_version == 2,
                object_template_properties.c.name == "a1_member",
            )
            .values(name="a2_member")
        )

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

    event.listen(
        m3_s03_runtime.engine.sync_engine,
        "before_cursor_execute",
        observe_statement,
    )
    try:
        response = await client.get(
            f"/api/v1/core/object-templates/{template_a}/versions/2/effective-schema"
        )
    finally:
        event.remove(
            m3_s03_runtime.engine.sync_engine,
            "before_cursor_execute",
            observe_statement,
        )

    assert response.status_code == 200, response.text
    assert len(statements) == 1, statements
    properties = response.json()["properties"]
    assert [item["name"] for item in properties] == [
        "a1_member",
        "b1_member",
        "a2_member",
    ]
    assert [item["declaring_template_id"] for item in properties] == [
        template_a,
        template_b,
        template_a,
    ]


@pytest.mark.api
@pytest.mark.postgresql
async def test_m3_s03_capabilities_keep_published_membership_without_default_recheck(
    m3_s03_runtime: M3S03Runtime,
) -> None:
    client = m3_s03_runtime.client
    root_id = await _template(client, "capability_root", abstract=True)
    await _publish_template(client, root_id)
    child_id = await _template(
        client, "capability_child", parent_template_id=root_id, parent_version=1
    )
    definition_id = await _published_symmetric_definition(
        client, root_id, "trusted_capability"
    )
    created_next = await client.post(
        f"/api/v1/core/relationship-definitions/{definition_id}/create-next",
        json={"source_version": 1},
    )
    assert created_next.status_code == 201, created_next.text
    with m3_s03_runtime.database_engine.begin() as connection:
        connection.execute(
            relationship_definitions.update()
            .where(relationship_definitions.c.id == UUID(definition_id))
            .values(default_version=2)
        )

    response = await client.get(
        f"/api/v1/core/object-templates/{child_id}/relationship-capabilities",
        params={"name": "trusted_capability"},
    )
    assert response.status_code == 200, response.text
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["default_version"] == 2

    rejected_default = await client.post(
        f"/api/v1/core/relationship-definitions/{definition_id}/set-default",
        json={"version": 2},
    )
    assert rejected_default.status_code == 409
    assert rejected_default.json()["code"] == "dependency_not_admissible"

    with m3_s03_runtime.database_engine.begin() as connection:
        connection.execute(
            relationship_definition_versions.update()
            .where(
                relationship_definition_versions.c.relationship_definition_id
                == UUID(definition_id),
                relationship_definition_versions.c.version == 1,
            )
            .values(status="DEPRECATED")
        )
    no_published_members = await client.get(
        f"/api/v1/core/object-templates/{child_id}/relationship-capabilities",
        params={"name": "trusted_capability"},
    )
    assert no_published_members.status_code == 200, no_published_members.text
    assert no_published_members.json() == {"items": [], "next_cursor": None}


@pytest.mark.api
@pytest.mark.postgresql
async def test_m3_s03_three_cursor_routes_traverse_and_bind_query_identity(
    m3_s03_runtime: M3S03Runtime,
) -> None:
    client = m3_s03_runtime.client
    lineage_ids = {
        name: await _template(client, name, namespace="m3s03cursor")
        for name in ("third", "first", "second")
    }
    lineage_first = await client.get(
        "/api/v1/core/object-templates",
        params={"namespace": "m3s03cursor", "limit": 1},
    )
    lineage_cursor = cast(str, lineage_first.json()["next_cursor"])
    lineage_second = await client.get(
        "/api/v1/core/object-templates",
        params={
            "namespace": "m3s03cursor",
            "cursor": lineage_cursor,
            "limit": 2,
        },
    )
    assert [
        item["name"]
        for page in (lineage_first, lineage_second)
        for item in page.json()["items"]
    ] == ["first", "second", "third"]
    changed_lineage_filter = await client.get(
        "/api/v1/core/object-templates",
        params={"namespace": "other", "cursor": lineage_cursor},
    )
    malformed_lineage_key = encode_cursor(
        "object_templates",
        {
            "namespace": "m3s03cursor",
            "name": None,
            "abstract": None,
            "parent_template_id": None,
            "parent_filter_set": False,
        },
        ["only-one-part"],
    )
    wrong_lineage_key = await client.get(
        "/api/v1/core/object-templates",
        params={
            "namespace": "m3s03cursor",
            "cursor": malformed_lineage_key,
        },
    )

    version_template = lineage_ids["first"]
    await _publish_template(client, version_template)
    for _ in range(2):
        created = await client.post(
            f"/api/v1/core/object-templates/{version_template}/create-next",
            json={"source_version": 1},
        )
        assert created.status_code == 201, created.text
    version_first = await client.get(
        f"/api/v1/core/object-templates/{version_template}/versions",
        params={"limit": 1},
    )
    version_cursor = cast(str, version_first.json()["next_cursor"])
    version_second = await client.get(
        f"/api/v1/core/object-templates/{version_template}/versions",
        params={"cursor": version_cursor, "limit": 2},
    )
    assert [
        item["version"]
        for page in (version_first, version_second)
        for item in page.json()["items"]
    ] == [1, 2, 3]
    changed_status = await client.get(
        f"/api/v1/core/object-templates/{version_template}/versions",
        params={"cursor": version_cursor, "status": "DRAFT"},
    )
    changed_version_parent = await client.get(
        f"/api/v1/core/object-templates/{lineage_ids['second']}/versions",
        params={"cursor": version_cursor},
    )
    malformed_version_key = encode_cursor(
        "object_template_versions",
        {"template_id": version_template, "status": None},
        ["not-an-integer"],
    )
    wrong_version_key = await client.get(
        f"/api/v1/core/object-templates/{version_template}/versions",
        params={"cursor": malformed_version_key},
    )

    capability_template = lineage_ids["second"]
    await _publish_template(client, capability_template)
    for name in ("capability_a", "capability_b", "capability_c"):
        await _published_symmetric_definition(client, capability_template, name)
    capability_first = await client.get(
        f"/api/v1/core/object-templates/{capability_template}/relationship-capabilities",
        params={"limit": 1},
    )
    capability_cursor = cast(str, capability_first.json()["next_cursor"])
    capability_second = await client.get(
        f"/api/v1/core/object-templates/{capability_template}/relationship-capabilities",
        params={"cursor": capability_cursor, "limit": 2},
    )
    capability_ids = [
        item["resolution_id"]
        for page in (capability_first, capability_second)
        for item in page.json()["items"]
    ]
    assert len(capability_ids) == 3
    assert len(capability_ids) == len(set(capability_ids))
    changed_name = await client.get(
        f"/api/v1/core/object-templates/{capability_template}/relationship-capabilities",
        params={"cursor": capability_cursor, "name": "capability_a"},
    )
    changed_capability_target = await client.get(
        f"/api/v1/core/object-templates/{lineage_ids['third']}/relationship-capabilities",
        params={"cursor": capability_cursor},
    )
    malformed_capability_key = encode_cursor(
        "relationship_capabilities",
        {"template_id": capability_template, "name": None},
        [1],
    )
    wrong_capability_key = await client.get(
        f"/api/v1/core/object-templates/{capability_template}/relationship-capabilities",
        params={"cursor": malformed_capability_key},
    )

    for response in (
        changed_lineage_filter,
        wrong_lineage_key,
        changed_status,
        changed_version_parent,
        wrong_version_key,
        changed_name,
        changed_capability_target,
        wrong_capability_key,
    ):
        assert response.status_code == 400, response.text
        assert response.json()["code"] == "invalid_cursor"


@pytest.mark.api
@pytest.mark.postgresql
async def test_m3_s03_required_property_without_default_remains_readable(
    m3_s03_runtime: M3S03Runtime,
) -> None:
    client = m3_s03_runtime.client
    datatype_id = await _published_datatype(client, "nullable_default_value")
    template_id = await _template(client, "nullable_default_template")
    with m3_s03_runtime.database_engine.begin() as connection:
        connection.execute(
            object_template_properties.insert().values(
                template_id=UUID(template_id),
                template_version=1,
                name="missing_default",
                position=1,
                datatype_id=UUID(datatype_id),
                datatype_version=1,
                value_mode="SCALAR",
                required=True,
                migration_default=None,
            )
        )

    exact = await client.get(f"/api/v1/core/object-templates/{template_id}/versions/1")
    effective = await client.get(
        f"/api/v1/core/object-templates/{template_id}/versions/1/effective-schema"
    )
    for response in (exact, effective):
        assert response.status_code == 200, response.text
        properties = response.json()["properties"]
        assert len(properties) == 1
        assert properties[0]["name"] == "missing_default"
        assert properties[0]["required"] is True
        assert "migration_default" not in properties[0]

    invalid_property: dict[str, object] = {
        "name": "required_value",
        "position": 1,
        "datatype_id": datatype_id,
        "datatype_version": 1,
        "value_mode": "SCALAR",
        "required": True,
    }
    missing_default = await client.post(
        "/api/v1/core/object-templates",
        json={
            "namespace": "m3s03",
            "name": "missing_required_default",
            "abstract": False,
            "properties": [invalid_property],
        },
    )
    null_default = await client.post(
        "/api/v1/core/object-templates",
        json={
            "namespace": "m3s03",
            "name": "null_required_default",
            "abstract": False,
            "properties": [{**invalid_property, "migration_default": None}],
        },
    )
    for response in (missing_default, null_default):
        assert response.status_code == 400, response.text
        assert response.json()["code"] == "invalid_request"


def test_m3_s03_objecttemplate_ver_07_target_is_not_applicable() -> None:
    column_types = {
        table.name: {
            column.name: type(column.type).__name__ for column in table.columns
        }
        for table in (
            object_templates,
            object_template_versions,
            object_template_properties,
            object_template_components,
        )
    }
    nullable_columns = {
        table.name: {column.name for column in table.columns if column.nullable}
        for table in (
            object_templates,
            object_template_versions,
            object_template_properties,
            object_template_components,
        )
    }
    constraint_names = {
        constraint.name
        for table in (
            object_templates,
            object_template_versions,
            object_template_properties,
            object_template_components,
        )
        for constraint in table.constraints
    }

    assert column_types == {
        "object_templates": {
            "id": "UUID",
            "namespace": "Text",
            "name": "Text",
            "description": "Text",
            "abstract": "Boolean",
            "default_version": "Integer",
            "parent_template_id": "UUID",
        },
        "object_template_versions": {
            "template_id": "UUID",
            "version": "Integer",
            "revision": "Integer",
            "status": "Text",
            "parent_template_id": "UUID",
            "parent_version": "Integer",
        },
        "object_template_properties": {
            "template_id": "UUID",
            "template_version": "Integer",
            "name": "Text",
            "position": "Integer",
            "datatype_id": "UUID",
            "datatype_version": "Integer",
            "value_mode": "Text",
            "required": "Boolean",
            "migration_default": "JSONB",
        },
        "object_template_components": {
            "template_id": "UUID",
            "template_version": "Integer",
            "name": "Text",
            "position": "Integer",
            "target_template_id": "UUID",
        },
    }
    assert nullable_columns == {
        "object_templates": {
            "description",
            "default_version",
            "parent_template_id",
        },
        "object_template_versions": {"parent_template_id", "parent_version"},
        "object_template_properties": {"migration_default"},
        "object_template_components": set(),
    }
    assert {
        "ck_object_template_versions_status",
        "ck_object_template_versions_parent_pair",
        "ck_object_template_properties_value_mode",
        "ck_object_template_properties_optional_default",
        "fk_object_template_properties_datatype_version",
        "fk_object_template_components_target",
    } <= constraint_names
    assert {item.value for item in VersionStatus} == {
        "DRAFT",
        "PUBLISHED",
        "DEPRECATED",
    }
    assert {item.value for item in ValueMode} == {"SCALAR", "LIST"}
    assert object_template_properties.c.migration_default.nullable
    migration_default = PropertyDto.model_fields["migration_default"]
    assert not migration_default.is_required()
    assert migration_default.default is None
    assert set(PropertyDto.model_fields) == {
        "name",
        "position",
        "datatype_id",
        "datatype_version",
        "value_mode",
        "required",
        "migration_default",
    }
    projected = PropertyDto(
        name="required_value",
        position=1,
        datatype_id=uuid4(),
        datatype_version=1,
        value_mode=ValueMode.SCALAR,
        required=True,
        migration_default=None,
    ).model_dump(mode="json")
    assert "migration_default" not in projected


@pytest.mark.api
@pytest.mark.postgresql
async def test_m3_s03_six_gets_each_execute_one_business_statement(
    m3_s03_runtime: M3S03Runtime,
) -> None:
    client = m3_s03_runtime.client
    datatype_id = await _published_datatype(client, "statement_value")
    target_id = await _template(client, "statement_target")
    template_id = await _template(
        client,
        "statement_subject",
        properties=[
            {
                "name": "value",
                "position": 1,
                "datatype_id": datatype_id,
                "datatype_version": 1,
                "value_mode": "SCALAR",
                "required": False,
            }
        ],
        components=[
            {
                "name": "member",
                "position": 1,
                "target_template_id": target_id,
            }
        ],
    )
    await _publish_template(client, template_id)
    await _published_symmetric_definition(client, template_id, "statement_capability")

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
        "OT-GET-01": "/api/v1/core/object-templates?namespace=m3s03&limit=1",
        "OT-GET-02": f"/api/v1/core/object-templates/{template_id}",
        "OT-GET-03": (f"/api/v1/core/object-templates/{template_id}/versions?limit=1"),
        "OT-GET-04": f"/api/v1/core/object-templates/{template_id}/versions/1",
        "OT-GET-05": (
            f"/api/v1/core/object-templates/{template_id}/versions/1/effective-schema"
        ),
        "OT-GET-06": (
            f"/api/v1/core/object-templates/{template_id}/relationship-capabilities"
            "?limit=1"
        ),
    }
    counts: dict[str, int] = {}
    event.listen(
        m3_s03_runtime.engine.sync_engine,
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
            m3_s03_runtime.engine.sync_engine,
            "before_cursor_execute",
            observe_statement,
        )
    assert counts == {
        "OT-GET-01": 1,
        "OT-GET-02": 1,
        "OT-GET-03": 1,
        "OT-GET-04": 1,
        "OT-GET-05": 1,
        "OT-GET-06": 1,
    }


def test_m3_s03_get_paths_have_no_read_certification_dependencies() -> None:
    forbidden_calls = {
        "_validate_default_pointers",
        "coherent_read",
        "get_version",
        "load_exact_effective_chain",
        "resolve_effective_schema",
        "resolve_exact_effective_schema",
        "validate_local_declarations",
    }
    methods: tuple[Callable[..., object], ...] = (
        ObjectTemplateService.list_lineages,
        ObjectTemplateService.get_lineage,
        ObjectTemplateService.list_versions,
        ObjectTemplateService.get_version,
        ObjectTemplateService.get_effective_schema,
        RelationshipDefinitionService.list_capabilities,
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

    exact_source = inspect.getsource(ObjectTemplateStore.project_effective_schema)
    stable_source = inspect.getsource(RelationshipDefinitionStore.list_capabilities)
    assert "exact_chain" in exact_source
    assert "object_template_versions" in exact_source
    assert "stable_ancestry" not in exact_source
    assert "visited_exact_nodes" in exact_source
    assert "exact.version::text" in exact_source
    assert "parent.version::text" in exact_source
    assert "stable_ancestry" in stable_source
    assert "object_templates" in stable_source
    assert "exact_chain" not in stable_source
