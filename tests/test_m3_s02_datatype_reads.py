"""M3-S02 DataType trusted one-statement read evidence."""

import ast
import inspect
import textwrap
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from typing import cast
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import Engine, event
from sqlalchemy.ext.asyncio import AsyncEngine

from netauto.application.cursors import encode_cursor
from netauto.application.datatypes import DataTypeService
from netauto.domain.datatypes import VersionStatus
from netauto.domain.primitives import PrimitiveType
from netauto.entrypoints.http import build_app
from netauto.persistence.engine import RuntimeContext
from netauto.persistence.metadata import datatype_versions, datatypes
from netauto.settings import Settings


@dataclass(frozen=True, slots=True)
class M3S02Runtime:
    client: httpx.AsyncClient
    engine: AsyncEngine


@pytest.fixture
async def m3_s02_runtime(
    migrated_database_engine: Engine, test_database_url: str
) -> AsyncIterator[M3S02Runtime]:
    del migrated_database_engine
    app = build_app(Settings(database_url=test_database_url))
    async with app.router.lifespan_context(app):
        runtime = cast(RuntimeContext, app.state.runtime)
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            yield M3S02Runtime(client, runtime.engine)


async def _create_datatype(
    client: httpx.AsyncClient,
    name: str,
    *,
    namespace: str = "m3s02",
) -> str:
    response = await client.post(
        "/api/v1/core/datatypes",
        json={
            "namespace": namespace,
            "name": name,
            "base_type": "core.integer",
        },
    )
    assert response.status_code == 201, response.text
    return cast(str, response.json()["datatype"]["id"])


@pytest.mark.api
@pytest.mark.postgresql
async def test_m3_s02_trusted_reads_preserve_persisted_surprises_and_writes_reject(
    m3_s02_runtime: M3S02Runtime,
) -> None:
    client = m3_s02_runtime.client
    datatype_id = await _create_datatype(client, "trusted")
    persisted_constraints = {"unsupported_constraint": True}
    async with m3_s02_runtime.engine.begin() as connection:
        await connection.execute(
            datatypes.update()
            .where(datatypes.c.id == datatype_id)
            .values(default_version=1)
        )
        await connection.execute(
            datatype_versions.update()
            .where(
                datatype_versions.c.datatype_id == datatype_id,
                datatype_versions.c.version == 1,
            )
            .values(constraints=persisted_constraints)
        )

    exact_lineage = await client.get(f"/api/v1/core/datatypes/{datatype_id}")
    lineage_page = await client.get(
        "/api/v1/core/datatypes",
        params={"namespace": "m3s02", "name": "trusted"},
    )
    exact_version = await client.get(f"/api/v1/core/datatypes/{datatype_id}/versions/1")

    assert exact_lineage.status_code == 200, exact_lineage.text
    assert exact_lineage.json()["default_version"] == 1
    assert lineage_page.status_code == 200, lineage_page.text
    assert lineage_page.json()["items"][0]["default_version"] == 1
    assert exact_version.status_code == 200, exact_version.text
    assert exact_version.json()["constraints"] == persisted_constraints

    draft_default = await client.post(
        f"/api/v1/core/datatypes/{datatype_id}/set-default",
        json={"version": 1},
    )
    invalid_revision = await client.post(
        f"/api/v1/core/datatypes/{datatype_id}/versions/1/revise",
        params={"expected_revision": 1},
        json={"constraints": persisted_constraints},
    )
    assert draft_default.status_code == 409
    assert draft_default.json()["code"] == "dependency_not_admissible"
    assert invalid_revision.status_code == 422
    assert invalid_revision.json()["code"] == "semantic_validation_failed"


@pytest.mark.api
@pytest.mark.postgresql
async def test_m3_s02_request_and_path_target_failures_preserve_rp03_empty_page(
    m3_s02_runtime: M3S02Runtime,
) -> None:
    client = m3_s02_runtime.client
    datatype_id = await _create_datatype(client, "failure_boundary")
    missing_id = uuid4()

    repeated = await client.get(
        "/api/v1/core/datatypes", params=[("limit", "1"), ("limit", "2")]
    )
    unknown = await client.get(
        f"/api/v1/core/datatypes/{datatype_id}", params={"expand": "versions"}
    )
    malformed_uuid = await client.get("/api/v1/core/datatypes/not-a-uuid")
    malformed_version = await client.get(
        f"/api/v1/core/datatypes/{datatype_id}/versions/not-an-integer"
    )
    malformed_status = await client.get(
        f"/api/v1/core/datatypes/{datatype_id}/versions",
        params={"status": "UNKNOWN"},
    )
    missing_lineage = await client.get(f"/api/v1/core/datatypes/{missing_id}")
    missing_version = await client.get(
        f"/api/v1/core/datatypes/{datatype_id}/versions/99"
    )
    missing_parent_page = await client.get(
        f"/api/v1/core/datatypes/{missing_id}/versions"
    )
    existing_empty_page = await client.get(
        f"/api/v1/core/datatypes/{datatype_id}/versions",
        params={"status": "PUBLISHED"},
    )

    for response in (
        repeated,
        unknown,
        malformed_uuid,
        malformed_version,
        malformed_status,
    ):
        assert response.status_code == 400, response.text
        assert response.json()["code"] == "invalid_request"
    for response in (missing_lineage, missing_version, missing_parent_page):
        assert response.status_code == 404, response.text
        assert response.json()["code"] == "resource_not_found"
    assert existing_empty_page.status_code == 200, existing_empty_page.text
    assert existing_empty_page.json() == {"items": [], "next_cursor": None}


@pytest.mark.api
@pytest.mark.postgresql
async def test_m3_s02_datatype_cursors_traverse_and_bind_semantic_identity(
    m3_s02_runtime: M3S02Runtime,
) -> None:
    client = m3_s02_runtime.client
    identifiers = {
        name: await _create_datatype(client, name)
        for name in ("third", "first", "second")
    }

    first_lineage_page = await client.get("/api/v1/core/datatypes", params={"limit": 1})
    lineage_cursor = cast(str, first_lineage_page.json()["next_cursor"])
    second_lineage_page = await client.get(
        "/api/v1/core/datatypes", params={"cursor": lineage_cursor, "limit": 2}
    )
    lineage_names = [
        item["name"]
        for response in (first_lineage_page, second_lineage_page)
        for item in response.json()["items"]
    ]
    assert lineage_names == ["first", "second", "third"]
    assert len(lineage_names) == len(set(lineage_names))
    assert second_lineage_page.json()["next_cursor"] is None

    changed_filter = await client.get(
        "/api/v1/core/datatypes",
        params={"cursor": lineage_cursor, "namespace": "m3s02"},
    )
    malformed_lineage_key = encode_cursor(
        "datatypes", {"namespace": None, "name": None}, ["only-one-key-part"]
    )
    wrong_lineage_key = await client.get(
        "/api/v1/core/datatypes", params={"cursor": malformed_lineage_key}
    )
    for response in (changed_filter, wrong_lineage_key):
        assert response.status_code == 400
        assert response.json()["code"] == "invalid_cursor"

    first_id = identifiers["first"]
    published = await client.post(
        f"/api/v1/core/datatypes/{first_id}/versions/1/publish",
        params={"expected_revision": 1},
    )
    assert published.status_code == 200, published.text
    for _ in range(2):
        created = await client.post(
            f"/api/v1/core/datatypes/{first_id}/create-next",
            json={"source_version": 1},
        )
        assert created.status_code == 201, created.text

    first_version_page = await client.get(
        f"/api/v1/core/datatypes/{first_id}/versions", params={"limit": 1}
    )
    version_cursor = cast(str, first_version_page.json()["next_cursor"])
    second_version_page = await client.get(
        f"/api/v1/core/datatypes/{first_id}/versions",
        params={"cursor": version_cursor, "limit": 2},
    )
    versions = [
        item["version"]
        for response in (first_version_page, second_version_page)
        for item in response.json()["items"]
    ]
    assert versions == [1, 2, 3]
    assert len(versions) == len(set(versions))
    assert second_version_page.json()["next_cursor"] is None

    changed_status = await client.get(
        f"/api/v1/core/datatypes/{first_id}/versions",
        params={"cursor": version_cursor, "status": "DRAFT"},
    )
    changed_parent = await client.get(
        f"/api/v1/core/datatypes/{identifiers['second']}/versions",
        params={"cursor": version_cursor},
    )
    malformed_version_key = encode_cursor(
        "datatype_versions",
        {"datatype_id": first_id, "status": None},
        ["not-an-integer"],
    )
    wrong_version_key = await client.get(
        f"/api/v1/core/datatypes/{first_id}/versions",
        params={"cursor": malformed_version_key},
    )
    for response in (changed_status, changed_parent, wrong_version_key):
        assert response.status_code == 400
        assert response.json()["code"] == "invalid_cursor"


@pytest.mark.api
@pytest.mark.postgresql
async def test_m3_s02_four_gets_each_execute_one_business_statement(
    m3_s02_runtime: M3S02Runtime,
) -> None:
    client = m3_s02_runtime.client
    datatype_id = await _create_datatype(client, "statement_count")
    published = await client.post(
        f"/api/v1/core/datatypes/{datatype_id}/versions/1/publish",
        params={"expected_revision": 1},
    )
    assert published.status_code == 200, published.text
    created_next = await client.post(
        f"/api/v1/core/datatypes/{datatype_id}/create-next",
        json={"source_version": 1},
    )
    assert created_next.status_code == 201, created_next.text

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
        "DT-GET-01": "/api/v1/core/datatypes?limit=1",
        "DT-GET-02": f"/api/v1/core/datatypes/{datatype_id}",
        "DT-GET-03": f"/api/v1/core/datatypes/{datatype_id}/versions?limit=1",
        "DT-GET-04": f"/api/v1/core/datatypes/{datatype_id}/versions/1",
    }
    counts: dict[str, int] = {}
    event.listen(
        m3_s02_runtime.engine.sync_engine,
        "before_cursor_execute",
        observe_statement,
    )
    try:
        for route_id, path in routes.items():
            statements.clear()
            response = await client.get(path)
            assert response.status_code == 200, response.text
            counts[route_id] = len(statements)
            assert len(statements) == 1, (route_id, statements)
            assert statements[0].lstrip().upper().startswith("SELECT")
    finally:
        event.remove(
            m3_s02_runtime.engine.sync_engine,
            "before_cursor_execute",
            observe_statement,
        )
    assert counts == {
        "DT-GET-01": 1,
        "DT-GET-02": 1,
        "DT-GET-03": 1,
        "DT-GET-04": 1,
    }


def test_m3_s02_get_paths_have_no_read_certification_dependencies() -> None:
    forbidden_calls = {
        "canonicalize_constraints",
        "coherent_read",
        "validate_qualified_name",
        "_validate_default_pointers",
    }
    methods: tuple[Callable[..., object], ...] = (
        DataTypeService.list_lineages,
        DataTypeService.get_lineage,
        DataTypeService.list_versions,
        DataTypeService.get_version,
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


def test_m3_s02_ver_07_datatype_target_is_not_applicable_under_delivered_schema() -> (
    None
):
    lineage_types = {
        column.name: type(column.type).__name__
        for column in datatypes.c
        if column.name != "description"
    }
    version_types = {
        column.name: type(column.type).__name__ for column in datatype_versions.c
    }
    constraint_names = {
        constraint.name
        for table in (datatypes, datatype_versions)
        for constraint in table.constraints
    }

    assert lineage_types == {
        "id": "UUID",
        "namespace": "Text",
        "name": "Text",
        "default_version": "Integer",
    }
    assert version_types == {
        "datatype_id": "UUID",
        "version": "Integer",
        "revision": "Integer",
        "status": "Text",
        "base_type": "Text",
        "constraints": "JSONB",
    }
    assert all(
        not datatype_versions.c[name].nullable
        for name in (
            "datatype_id",
            "version",
            "revision",
            "status",
            "base_type",
            "constraints",
        )
    )
    assert {
        "ck_datatypes_namespace",
        "ck_datatypes_name",
        "ck_datatypes_default_version_positive",
        "fk_datatypes_default_version",
        "ck_datatype_versions_version_positive",
        "ck_datatype_versions_revision_positive",
        "ck_datatype_versions_status",
        "ck_datatype_versions_base_type",
        "ck_datatype_versions_constraints_object",
    } <= constraint_names
    assert {item.value for item in VersionStatus} == {
        "DRAFT",
        "PUBLISHED",
        "DEPRECATED",
    }
    assert {item.value for item in PrimitiveType} == {
        "core.string",
        "core.integer",
        "core.number",
        "core.boolean",
        "core.date",
        "core.datetime",
        "core.ip",
        "core.ip_prefix",
        "core.byte_size",
    }
