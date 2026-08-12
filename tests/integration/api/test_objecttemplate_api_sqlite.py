from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx2
import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from netauto.api.app import create_app
from netauto.persistence.sqlalchemy.database import create_schema, create_sqlite_engine
from netauto.persistence.sqlalchemy.unit_of_work import (
    SqlAlchemyUnitOfWork,
    SqliteModelWriteUnitOfWork,
)
from support.http_server import serve_app


@asynccontextmanager
async def _client(tmp_path: Path) -> AsyncIterator[httpx2.AsyncClient]:
    engine: Engine = create_sqlite_engine(f"sqlite:///{tmp_path / 'objecttemplate-api.sqlite3'}")
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)

    def uow_factory() -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(session_factory)

    try:
        async with serve_app(
            create_app(
                uow_factory,
                model_write_uow_factory=lambda: SqliteModelWriteUnitOfWork(session_factory),
                ownership_graph_uow_factory=uow_factory,
            )
        ) as client:
            yield client
    finally:
        engine.dispose()


@asynccontextmanager
async def _client_for_database(database_path: Path) -> AsyncIterator[httpx2.AsyncClient]:
    engine: Engine = create_sqlite_engine(f"sqlite:///{database_path}")
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)

    def uow_factory() -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(session_factory)

    try:
        async with serve_app(
            create_app(
                uow_factory,
                model_write_uow_factory=lambda: SqliteModelWriteUnitOfWork(session_factory),
                ownership_graph_uow_factory=uow_factory,
            )
        ) as client:
            yield client
    finally:
        engine.dispose()


async def _create_datatype(
    client: httpx2.AsyncClient,
    *,
    namespace: str,
    name: str,
) -> dict[str, object]:
    response = await client.post(
        "/api/v1/datatypes",
        json={
            "namespace": namespace,
            "name": name,
            "description": f"{name} datatype",
            "base_type": "core.string",
            "constraints": [],
        },
    )
    assert response.status_code == 201
    return response.json()


async def _publish_datatype_v1(client: httpx2.AsyncClient, datatype_id: str) -> dict[str, object]:
    response = await client.post(f"/api/v1/datatypes/{datatype_id}/versions/1/publish")
    assert response.status_code == 200
    return response.json()


async def _create_object_template(
    client: httpx2.AsyncClient,
    payload: dict[str, object],
) -> dict[str, object]:
    response = await client.post("/api/v1/object-templates", json=payload)
    assert response.status_code == 201
    return response.json()


async def _publish_object_template_version(
    client: httpx2.AsyncClient,
    template_id: str,
    version: int,
) -> dict[str, object]:
    response = await client.post(
        f"/api/v1/object-templates/{template_id}/versions/{version}/publish"
    )
    assert response.status_code == 200
    return response.json()


async def _create_next_object_template_version(
    client: httpx2.AsyncClient,
    template_id: str,
    source_version: int,
) -> dict[str, object]:
    response = await client.post(
        f"/api/v1/object-templates/{template_id}/versions",
        json={"source_version": source_version},
    )
    assert response.status_code == 201
    return response.json()


async def _deprecate_object_template_version(
    client: httpx2.AsyncClient,
    template_id: str,
    version: int,
) -> dict[str, object]:
    response = await client.post(
        f"/api/v1/object-templates/{template_id}/versions/{version}/deprecate"
    )
    assert response.status_code == 200
    return response.json()


def _string_field(payload: dict[str, object], *path: str) -> str:
    current: object = payload
    for key in path:
        if not isinstance(current, dict):
            raise AssertionError(f"Expected object at {'.'.join(path)}")
        current = current[key]
    if not isinstance(current, str):
        raise AssertionError(f"Expected string at {'.'.join(path)}")
    return current


def _object_field(payload: dict[str, object], *path: str) -> dict[str, object]:
    current: object = payload
    for key in path:
        if not isinstance(current, dict):
            raise AssertionError(f"Expected object at {'.'.join(path)}")
        current = current[key]
    if not isinstance(current, dict):
        raise AssertionError(f"Expected object at {'.'.join(path)}")
    return current


pytestmark = pytest.mark.anyio


async def test_objecttemplate_components_workflow_over_http_and_sqlite(tmp_path: Path) -> None:
    database_path = tmp_path / "objecttemplate-components.sqlite3"

    async with _client_for_database(database_path) as client:
        network_interface = await _create_object_template(
            client,
            {
                "namespace": "network",
                "name": "network_interface",
                "description": "Network interface template",
                "abstract": True,
                "parent": None,
                "properties": [],
                "components": [],
            },
        )
        network_interface_id = _string_field(network_interface, "object_template", "id")
        assert _object_field(network_interface, "object_template")["abstract"] is True

        published_interface_v1 = await _publish_object_template_version(
            client,
            network_interface_id,
            1,
        )
        assert published_interface_v1["status"] == "published"

        interface_v2 = await _create_next_object_template_version(client, network_interface_id, 1)
        assert interface_v2["version"] == 2
        published_interface_v2 = await _publish_object_template_version(
            client,
            network_interface_id,
            2,
        )
        assert published_interface_v2["status"] == "published"

        interface_v3 = await _create_next_object_template_version(client, network_interface_id, 2)
        assert interface_v3["version"] == 3
        assert interface_v3["status"] == "draft"

        network_device = await _create_object_template(
            client,
            {
                "namespace": "network",
                "name": "network_device",
                "description": "Network device template",
                "abstract": True,
                "parent": None,
                "properties": [],
                "components": [{"name": "interfaces", "template_id": network_interface_id}],
            },
        )
        network_device_id = _string_field(network_device, "object_template", "id")
        assert _object_field(network_device, "version")["components"] == [
            {
                "name": "interfaces",
                "template_id": network_interface_id,
            }
        ]
        published_device_v1 = await _publish_object_template_version(client, network_device_id, 1)
        assert published_device_v1["status"] == "published"

        router = await _create_object_template(
            client,
            {
                "namespace": "network",
                "name": "router",
                "description": "Router template",
                "abstract": False,
                "parent": {"template_id": network_device_id, "version": 1},
                "properties": [],
                "components": [],
            },
        )
        router_id = _string_field(router, "object_template", "id")
        assert _object_field(router, "version")["components"] == []
        published_router_v1 = await _publish_object_template_version(client, router_id, 1)
        assert published_router_v1["status"] == "published"

        published_interface_v3 = await _publish_object_template_version(
            client,
            network_interface_id,
            3,
        )
        assert published_interface_v3["status"] == "published"

        network_device_v2 = await _create_next_object_template_version(client, network_device_id, 1)
        assert network_device_v2 == {
            "template_id": network_device_id,
            "version": 2,
            "status": "draft",
            "parent": None,
            "properties": [],
            "components": [
                {
                    "name": "interfaces",
                    "template_id": network_interface_id,
                }
            ],
        }

        deprecated_interface_v2 = await _deprecate_object_template_version(
            client,
            network_interface_id,
            2,
        )
        assert deprecated_interface_v2["status"] == "deprecated"

        publish_device_v2 = await client.post(
            f"/api/v1/object-templates/{network_device_id}/versions/2/publish"
        )
        assert publish_device_v2.status_code == 200
        assert publish_device_v2.json()["status"] == "published"

        loaded_device_v2 = await client.get(
            f"/api/v1/object-templates/{network_device_id}/versions/2"
        )
        assert loaded_device_v2.status_code == 200
        assert loaded_device_v2.json() == {
            "template_id": network_device_id,
            "version": 2,
            "status": "published",
            "parent": None,
            "properties": [],
            "components": [
                {
                    "name": "interfaces",
                    "template_id": network_interface_id,
                }
            ],
        }

        loaded_device_v1 = await client.get(
            f"/api/v1/object-templates/{network_device_id}/versions/1"
        )
        assert loaded_device_v1.status_code == 200
        assert loaded_device_v1.json() == {
            "template_id": network_device_id,
            "version": 1,
            "status": "published",
            "parent": None,
            "properties": [],
            "components": [
                {
                    "name": "interfaces",
                    "template_id": network_interface_id,
                }
            ],
        }

        loaded_router_v1 = await client.get(f"/api/v1/object-templates/{router_id}/versions/1")
        assert loaded_router_v1.status_code == 200
        assert loaded_router_v1.json() == {
            "template_id": router_id,
            "version": 1,
            "status": "published",
            "parent": {"template_id": network_device_id, "version": 1},
            "properties": [],
            "components": [],
        }

        router_after_deprecation = await _create_object_template(
            client,
            {
                "namespace": "network",
                "name": "router_after_deprecation",
                "description": "Router after deprecation",
                "abstract": False,
                "parent": {"template_id": network_device_id, "version": 1},
                "properties": [],
                "components": [],
            },
        )
        router_after_deprecation_id = _string_field(
            router_after_deprecation,
            "object_template",
            "id",
        )
        assert _object_field(router_after_deprecation, "version")["status"] == "draft"
        assert _object_field(router_after_deprecation, "version")["components"] == []

        publish_router_after_deprecation = await client.post(
            f"/api/v1/object-templates/{router_after_deprecation_id}/versions/1/publish"
        )
        assert publish_router_after_deprecation.status_code == 200
        assert publish_router_after_deprecation.json()["status"] == "published"

        loaded_router_after_deprecation = await client.get(
            f"/api/v1/object-templates/{router_after_deprecation_id}/versions/1"
        )
        assert loaded_router_after_deprecation.status_code == 200
        assert loaded_router_after_deprecation.json() == {
            "template_id": router_after_deprecation_id,
            "version": 1,
            "status": "published",
            "parent": {"template_id": network_device_id, "version": 1},
            "properties": [],
            "components": [],
        }

    async with _client_for_database(database_path) as client:
        loaded_after_restart = await client.get(
            f"/api/v1/object-templates/{network_device_id}/versions/1"
        )

    assert loaded_after_restart.status_code == 200
    assert loaded_after_restart.json() == {
        "template_id": network_device_id,
        "version": 1,
        "status": "published",
        "parent": None,
        "properties": [],
        "components": [
            {
                "name": "interfaces",
                "template_id": network_interface_id,
            }
        ],
    }


async def test_full_objecttemplate_workflow_over_http_and_sqlite(tmp_path: Path) -> None:
    async with _client(tmp_path) as client:
        hostname_datatype = await _create_datatype(
            client,
            namespace="network",
            name="hostname",
        )
        serial_datatype = await _create_datatype(
            client,
            namespace="network",
            name="serial",
        )
        hostname_id = _string_field(hostname_datatype, "datatype", "id")
        serial_id = _string_field(serial_datatype, "datatype", "id")

        hostname_published = await client.post(
            f"/api/v1/datatypes/{hostname_id}/versions/1/publish"
        )
        serial_published = await client.post(f"/api/v1/datatypes/{serial_id}/versions/1/publish")
        assert hostname_published.status_code == 200
        assert serial_published.status_code == 200

        parent_created = await _create_object_template(
            client,
            {
                "namespace": "network",
                "name": "device",
                "description": "Device template",
                "abstract": True,
                "parent": None,
                "properties": [
                    {
                        "name": "hostname",
                        "datatype_id": hostname_id,
                        "required": True,
                    }
                ],
            },
        )
        parent_id = _string_field(parent_created, "object_template", "id")
        parent_version = _object_field(parent_created, "version")
        parent_identity = _object_field(parent_created, "object_template")
        assert parent_version["version"] == 1
        assert parent_version["status"] == "draft"
        assert parent_identity["abstract"] is True
        assert parent_version["properties"] == [
            {
                "name": "hostname",
                "datatype_id": hostname_id,
                "datatype_version": 1,
                "required": True,
            }
        ]

        parent_published = await client.post(
            f"/api/v1/object-templates/{parent_id}/versions/1/publish"
        )
        assert parent_published.status_code == 200
        assert parent_published.json()["status"] == "published"

        child_created = await _create_object_template(
            client,
            {
                "namespace": "network",
                "name": "router",
                "description": "Router template",
                "abstract": False,
                "parent": {"template_id": parent_id, "version": 1},
                "properties": [
                    {
                        "name": "serial",
                        "datatype_id": serial_id,
                        "required": False,
                    }
                ],
            },
        )
        child_id = _string_field(child_created, "object_template", "id")
        child_version = _object_field(child_created, "version")
        assert child_version["parent"] == {"template_id": parent_id, "version": 1}
        assert child_version["properties"] == [
            {
                "name": "serial",
                "datatype_id": serial_id,
                "datatype_version": 1,
                "required": False,
            }
        ]

        child_published = await client.post(
            f"/api/v1/object-templates/{child_id}/versions/1/publish"
        )
        assert child_published.status_code == 200
        assert child_published.json()["status"] == "published"

        parent_by_id = await client.get(f"/api/v1/object-templates/{parent_id}")
        parent_v1 = await client.get(f"/api/v1/object-templates/{parent_id}/versions/1")
        child_by_id = await client.get(f"/api/v1/object-templates/{child_id}")
        child_v1 = await client.get(f"/api/v1/object-templates/{child_id}/versions/1")
        child_versions = await client.get(f"/api/v1/object-templates/{child_id}/versions")
        child_by_name = await client.get("/api/v1/object-templates/by-name/network/router")

        assert parent_by_id.status_code == 200
        assert parent_by_id.json() == {
            "id": parent_id,
            "namespace": "network",
            "name": "device",
            "qualified_name": "network.device",
            "description": "Device template",
            "abstract": True,
        }
        assert parent_v1.status_code == 200
        assert parent_v1.json() == {
            "template_id": parent_id,
            "version": 1,
            "status": "published",
            "parent": None,
            "properties": [
                {
                    "name": "hostname",
                    "datatype_id": hostname_id,
                    "datatype_version": 1,
                    "required": True,
                }
            ],
            "components": [],
        }
        assert child_by_id.status_code == 200
        assert child_by_id.json()["id"] == child_id
        assert child_by_id.json()["abstract"] is False
        assert child_v1.status_code == 200
        assert child_v1.json() == {
            "template_id": child_id,
            "version": 1,
            "status": "published",
            "parent": {"template_id": parent_id, "version": 1},
            "properties": [
                {
                    "name": "serial",
                    "datatype_id": serial_id,
                    "datatype_version": 1,
                    "required": False,
                }
            ],
            "components": [],
        }
        assert child_versions.status_code == 200
        assert child_versions.json() == [child_v1.json()]
        assert child_by_name.status_code == 200
        assert child_by_name.json()["id"] == child_id

        child_v2 = await client.post(
            f"/api/v1/object-templates/{child_id}/versions",
            json={"source_version": 1},
        )
        assert child_v2.status_code == 201
        assert child_v2.json() == {
            "template_id": child_id,
            "version": 2,
            "status": "draft",
            "parent": {"template_id": parent_id, "version": 1},
            "properties": [
                {
                    "name": "serial",
                    "datatype_id": serial_id,
                    "datatype_version": 1,
                    "required": False,
                }
            ],
            "components": [],
        }

        revised_v2 = await client.put(
            f"/api/v1/object-templates/{child_id}/versions/2",
            json={
                "parent": {"template_id": parent_id, "version": 1},
                "properties": [
                    {
                        "name": "serial",
                        "datatype_id": serial_id,
                        "datatype_version": 1,
                        "required": True,
                    }
                ],
            },
        )
        assert revised_v2.status_code == 200
        assert revised_v2.json()["status"] == "draft"
        assert revised_v2.json()["properties"][0]["required"] is True

        published_v2 = await client.post(f"/api/v1/object-templates/{child_id}/versions/2/publish")
        assert published_v2.status_code == 200
        assert published_v2.json()["status"] == "published"

        child_v1_again = await client.get(f"/api/v1/object-templates/{child_id}/versions/1")
        child_v2_again = await client.get(f"/api/v1/object-templates/{child_id}/versions/2")
        assert child_v1_again.status_code == 200
        assert child_v1_again.json() == {
            "template_id": child_id,
            "version": 1,
            "status": "published",
            "parent": {"template_id": parent_id, "version": 1},
            "properties": [
                {
                    "name": "serial",
                    "datatype_id": serial_id,
                    "datatype_version": 1,
                    "required": False,
                }
            ],
            "components": [],
        }
        assert child_v2_again.status_code == 200
        assert child_v2_again.json() == {
            "template_id": child_id,
            "version": 2,
            "status": "published",
            "parent": {"template_id": parent_id, "version": 1},
            "properties": [
                {
                    "name": "serial",
                    "datatype_id": serial_id,
                    "datatype_version": 1,
                    "required": True,
                }
            ],
            "components": [],
        }

        deprecated_v1 = await client.post(
            f"/api/v1/object-templates/{child_id}/versions/1/deprecate"
        )
        assert deprecated_v1.status_code == 200
        assert deprecated_v1.json()["status"] == "deprecated"

        child_versions_after = await client.get(f"/api/v1/object-templates/{child_id}/versions")
        assert child_versions_after.status_code == 200
        assert child_versions_after.json() == [
            {
                "template_id": child_id,
                "version": 1,
                "status": "deprecated",
                "parent": {"template_id": parent_id, "version": 1},
                "properties": [
                    {
                        "name": "serial",
                        "datatype_id": serial_id,
                        "datatype_version": 1,
                        "required": False,
                    }
                ],
                "components": [],
            },
            {
                "template_id": child_id,
                "version": 2,
                "status": "published",
                "parent": {"template_id": parent_id, "version": 1},
                "properties": [
                    {
                        "name": "serial",
                        "datatype_id": serial_id,
                        "datatype_version": 1,
                        "required": True,
                    }
                ],
                "components": [],
            },
        ]


async def test_publish_revalidates_deprecated_datatype_over_real_persistence(
    tmp_path: Path,
) -> None:
    async with _client(tmp_path) as client:
        datatype = await _create_datatype(client, namespace="network", name="hostname")
        datatype_id = _string_field(datatype, "datatype", "id")
        datatype_published = await client.post(
            f"/api/v1/datatypes/{datatype_id}/versions/1/publish"
        )
        assert datatype_published.status_code == 200

        template = await _create_object_template(
            client,
            {
                "namespace": "network",
                "name": "device",
                "description": "Device template",
                "abstract": False,
                "parent": None,
                "properties": [
                    {
                        "name": "hostname",
                        "datatype_id": datatype_id,
                        "datatype_version": 1,
                        "required": True,
                    }
                ],
            },
        )
        template_id = _string_field(template, "object_template", "id")

        deprecated = await client.post(f"/api/v1/datatypes/{datatype_id}/versions/1/deprecate")
        assert deprecated.status_code == 200
        assert deprecated.json()["status"] == "deprecated"

        publish = await client.post(f"/api/v1/object-templates/{template_id}/versions/1/publish")
        assert publish.status_code == 409
        assert publish.json()["error"]["code"] == "object_template_datatype_version_not_published"

        loaded = await client.get(f"/api/v1/object-templates/{template_id}/versions/1")
        assert loaded.status_code == 200
        assert loaded.json()["status"] == "draft"


async def test_publish_rejects_unpublished_parent_over_real_persistence(tmp_path: Path) -> None:
    async with _client(tmp_path) as client:
        datatype = await _create_datatype(client, namespace="network", name="hostname")
        datatype_id = _string_field(datatype, "datatype", "id")
        datatype_published = await client.post(
            f"/api/v1/datatypes/{datatype_id}/versions/1/publish"
        )
        assert datatype_published.status_code == 200

        parent = await _create_object_template(
            client,
            {
                "namespace": "network",
                "name": "device",
                "description": "Device template",
                "abstract": True,
                "parent": None,
                "properties": [
                    {
                        "name": "hostname",
                        "datatype_id": datatype_id,
                        "required": True,
                    }
                ],
            },
        )
        parent_id = _string_field(parent, "object_template", "id")

        child = await _create_object_template(
            client,
            {
                "namespace": "network",
                "name": "router",
                "description": "Router template",
                "abstract": False,
                "parent": {"template_id": parent_id, "version": 1},
                "properties": [],
            },
        )
        child_id = _string_field(child, "object_template", "id")

        publish = await client.post(f"/api/v1/object-templates/{child_id}/versions/1/publish")
        assert publish.status_code == 409
        assert publish.json()["error"]["code"] == "object_template_parent_not_published"

        loaded = await client.get(f"/api/v1/object-templates/{child_id}/versions/1")
        assert loaded.status_code == 200
        assert loaded.json()["status"] == "draft"


async def test_objecttemplate_state_survives_app_reconstruction(tmp_path: Path) -> None:
    database_path = tmp_path / "objecttemplate-restart.sqlite3"

    async with _client_for_database(database_path) as client:
        datatype = await _create_datatype(client, namespace="network", name="hostname")
        datatype_id = _string_field(datatype, "datatype", "id")
        datatype_published = await client.post(
            f"/api/v1/datatypes/{datatype_id}/versions/1/publish"
        )
        assert datatype_published.status_code == 200

        template = await _create_object_template(
            client,
            {
                "namespace": "network",
                "name": "device",
                "description": "Device template",
                "abstract": True,
                "parent": None,
                "properties": [
                    {
                        "name": "hostname",
                        "datatype_id": datatype_id,
                        "required": True,
                    }
                ],
            },
        )
        template_id = _string_field(template, "object_template", "id")
        publish = await client.post(f"/api/v1/object-templates/{template_id}/versions/1/publish")
        assert publish.status_code == 200

    async with _client_for_database(database_path) as client:
        loaded = await client.get(f"/api/v1/object-templates/{template_id}")
        version = await client.get(f"/api/v1/object-templates/{template_id}/versions/1")

    assert loaded.status_code == 200
    assert loaded.json() == {
        "id": template_id,
        "namespace": "network",
        "name": "device",
        "qualified_name": "network.device",
        "description": "Device template",
        "abstract": True,
    }
    assert version.status_code == 200
    assert version.json() == {
        "template_id": template_id,
        "version": 1,
        "status": "published",
        "parent": None,
        "properties": [
            {
                "name": "hostname",
                "datatype_id": datatype_id,
                "datatype_version": 1,
                "required": True,
            }
        ],
        "components": [],
    }
