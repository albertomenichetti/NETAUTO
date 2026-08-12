from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from uuid import UUID, uuid4

import httpx2
import pytest
from sqlalchemy import Engine, event
from sqlalchemy.orm import Session

from netauto.composition import create_sqlalchemy_app
from netauto.core.object import Object, ObjectChangeKind
from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateVersion,
    ObjectTemplateVersionStatus,
)
from netauto.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from support.http_server import serve_app

pytestmark = [pytest.mark.postgresql, pytest.mark.anyio]


def _guard_key(statement: str, parameters: object) -> int | None:
    if "pg_try_advisory_xact_lock" not in statement:
        return None
    if isinstance(parameters, dict):
        guard_key = parameters.get("guard_key")
        if isinstance(guard_key, int):
            return guard_key
        return None
    if isinstance(parameters, tuple) and len(parameters) >= 2 and isinstance(parameters[1], int):
        return parameters[1]
    return None


def _seed_object(
    session_factory: Callable[[], Session],
    *,
    template_id: UUID | None = None,
    object_id: UUID | None = None,
) -> UUID:
    template = ObjectTemplate(
        id=template_id or uuid4(),
        namespace="network",
        name=f"seed_template_{uuid4().hex[:8]}",
        description=None,
        abstract=False,
    )
    version = ObjectTemplateVersion(
        template_id=template.id,
        version=1,
        status=ObjectTemplateVersionStatus.DRAFT,
    )
    object_value = Object(
        id=object_id or uuid4(),
        template_id=template.id,
        template_version=1,
        properties={},
    )

    with SqlAlchemyUnitOfWork(session_factory) as uow:
        uow.object_templates.add(template)
        uow.object_templates.add_version(version)
        uow.objects.add(object_value)
        uow.commit()

    return object_value.id


@asynccontextmanager
async def _client(
    session_factory: Callable[[], Session],
    *,
    database_url: str,
) -> AsyncIterator[httpx2.AsyncClient]:
    composition = create_sqlalchemy_app(
        session_factory,
        database_url=database_url,
    )
    async with serve_app(composition.app) as client:
        yield client


async def test_postgresql_application_composition_wires_model_and_ownership_guards(
    postgresql_engine: Engine,
    postgresql_repository_session_factory: Callable[[], Session],
    postgresql_test_database_url: str,
) -> None:
    statements: list[tuple[str, object]] = []

    def capture_sql(_conn, _cursor, statement, parameters, _context, _executemany) -> None:
        statements.append((statement, parameters))

    event.listen(postgresql_engine, "before_cursor_execute", capture_sql)
    try:
        async with _client(
            postgresql_repository_session_factory,
            database_url=postgresql_test_database_url,
        ) as client:
            create_response = await client.post(
                "/api/v1/datatypes",
                json={
                    "namespace": "network",
                    "name": f"composed_type_{uuid4().hex[:8]}",
                    "description": "Composed PostgreSQL datatype",
                    "base_type": "core.string",
                    "constraints": [],
                },
            )
            assert create_response.status_code == 201
            datatype_id = create_response.json()["datatype"]["id"]

            create_guard_index = next(
                index
                for index, (statement, parameters) in enumerate(statements)
                if _guard_key(statement, parameters) == 1
            )
            create_insert_index = next(
                index
                for index, (statement, _parameters) in enumerate(statements)
                if statement.lstrip().upper().startswith("INSERT")
                and "INTO datatypes" in statement
            )
            assert create_guard_index < create_insert_index

            statements.clear()
            get_response = await client.get(f"/api/v1/datatypes/{datatype_id}")
            assert get_response.status_code == 200
            assert get_response.json()["id"] == datatype_id
            assert all(
                _guard_key(statement, parameters) is None
                for statement, parameters in statements
            )

            object_id = _seed_object(postgresql_repository_session_factory)

            statements.clear()
            delete_response = await client.delete(f"/api/v1/objects/{object_id}")
            assert delete_response.status_code == 204

            delete_guard_index = next(
                index
                for index, (statement, parameters) in enumerate(statements)
                if _guard_key(statement, parameters) == 2
            )
            delete_select_index = next(
                index
                for index, (statement, _parameters) in enumerate(statements)
                if statement.lstrip().upper().startswith("SELECT")
                and (
                    "FROM objects" in statement
                    or "FROM object_components" in statement
                )
            )
            assert delete_guard_index < delete_select_index
    finally:
        event.remove(postgresql_engine, "before_cursor_execute", capture_sql)

    with SqlAlchemyUnitOfWork(postgresql_repository_session_factory) as verifier:
        assert verifier.objects.get(object_id) is None
        history = verifier.object_changes.list_by_object(object_id)
        assert history
        assert history[-1].kind is ObjectChangeKind.DELETED
