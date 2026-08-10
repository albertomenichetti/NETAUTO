from __future__ import annotations

import json

import httpx
import pytest

from netauto.cli.client import NetautoApiClient
from netauto.cli.errors import ApiError, InputError, ProtocolError, TransportError


def _response(status_code: int, payload: object) -> httpx.Response:
    return httpx.Response(status_code, json=payload)


def test_client_builds_correct_urls_and_bodies() -> None:
    seen: list[tuple[str, str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = request.read().decode()
        seen.append((request.method, str(request.url), json.loads(body) if body else None))
        if request.method == "GET":
            return _response(200, [])
        return _response(201, {"datatype": {}, "version": {}})

    with NetautoApiClient(
        "http://127.0.0.1:8000/",
        transport=httpx.MockTransport(handler),
    ) as client:
        client.list_datatypes()
        client.create_datatype(
            {
                "namespace": "network",
                "name": "hostname",
                "description": None,
                "base_type": "core.string",
                "constraints": [],
            }
        )

    assert seen == [
        ("GET", "http://127.0.0.1:8000/api/v1/datatypes", None),
        (
            "POST",
            "http://127.0.0.1:8000/api/v1/datatypes",
            {
                "namespace": "network",
                "name": "hostname",
                "description": None,
                "base_type": "core.string",
                "constraints": [],
            },
        ),
    ]


def test_client_normalizes_trailing_root_and_existing_api_prefix() -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return _response(200, [])

    with NetautoApiClient(
        "http://127.0.0.1:8000/api/v1/",
        transport=httpx.MockTransport(handler),
    ) as client:
        client.list_datatypes()

    assert seen == ["http://127.0.0.1:8000/api/v1/datatypes"]


def test_client_returns_arrays_and_objects() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/datatypes"):
            return _response(200, [{"id": "x"}])
        return _response(200, {"id": "x"})

    with NetautoApiClient(
        "http://127.0.0.1:8000",
        transport=httpx.MockTransport(handler),
    ) as client:
        assert client.list_datatypes() == [{"id": "x"}]
        assert client.get_datatype("abc") == {"id": "x"}


def test_object_template_client_builds_correct_urls_and_bodies() -> None:
    seen: list[tuple[str, str, object]] = []
    version_payload = {
        "template_id": "x",
        "version": 1,
        "status": "draft",
        "parent": None,
        "properties": [],
        "components": [],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        body = request.read().decode()
        seen.append((request.method, str(request.url), json.loads(body) if body else None))
        if request.method == "GET" and (
            request.url.path.endswith("/object-templates")
            or request.url.path.endswith("/versions")
        ):
            return _response(200, [])
        return _response(200, version_payload)

    with NetautoApiClient(
        "http://127.0.0.1:8000/",
        transport=httpx.MockTransport(handler),
    ) as client:
        client.list_object_templates()
        client.get_object_template("abc")
        client.get_object_template_by_name("network", "device")
        client.create_object_template(
            {
                "namespace": "network",
                "name": "device",
                "description": None,
                "abstract": False,
                "parent": None,
                "properties": [],
                "components": [
                    {
                        "name": "interfaces",
                        "template_id": "target",
                    }
                ],
            }
        )
        client.list_object_template_versions("abc")
        client.get_object_template_version("abc", 2)
        client.revise_object_template_version(
            "abc",
            2,
            {
                "parent": None,
                "properties": [],
                "components": [
                    {
                        "name": "interfaces",
                        "template_id": "target",
                    }
                ],
            },
        )
        client.create_object_template_version("abc", 2)
        client.publish_object_template_version("abc", 2)
        client.deprecate_object_template_version("abc", 2)
        client.get_object_migration_analysis("abc", 1, 2)
        client.migrate_objects(
            "abc",
            1,
            {
                "target_version": 2,
                "property_values": {"serialnumber": "UNKNOWN"},
            },
        )

    assert seen == [
        ("GET", "http://127.0.0.1:8000/api/v1/object-templates", None),
        ("GET", "http://127.0.0.1:8000/api/v1/object-templates/abc", None),
        ("GET", "http://127.0.0.1:8000/api/v1/object-templates/by-name/network/device", None),
        (
            "POST",
            "http://127.0.0.1:8000/api/v1/object-templates",
            {
                "namespace": "network",
                "name": "device",
                "description": None,
                "abstract": False,
                "parent": None,
                "properties": [],
                "components": [
                    {
                        "name": "interfaces",
                        "template_id": "target",
                    }
                ],
            },
        ),
        ("GET", "http://127.0.0.1:8000/api/v1/object-templates/abc/versions", None),
        ("GET", "http://127.0.0.1:8000/api/v1/object-templates/abc/versions/2", None),
        (
            "PUT",
            "http://127.0.0.1:8000/api/v1/object-templates/abc/versions/2",
            {
                "parent": None,
                "properties": [],
                "components": [
                    {
                        "name": "interfaces",
                        "template_id": "target",
                    }
                ],
            },
        ),
        (
            "POST",
            "http://127.0.0.1:8000/api/v1/object-templates/abc/versions",
            {"source_version": 2},
        ),
        ("POST", "http://127.0.0.1:8000/api/v1/object-templates/abc/versions/2/publish", None),
        ("POST", "http://127.0.0.1:8000/api/v1/object-templates/abc/versions/2/deprecate", None),
        (
            "GET",
            (
                "http://127.0.0.1:8000/api/v1/object-templates/abc/versions/1/"
                "migration-analysis?target_version=2"
            ),
            None,
        ),
        (
            "POST",
            "http://127.0.0.1:8000/api/v1/object-templates/abc/versions/1/migrate-objects",
            {
                "target_version": 2,
                "property_values": {"serialnumber": "UNKNOWN"},
            },
        ),
    ]


def test_object_template_client_returns_arrays_and_objects() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/object-templates"):
            return _response(200, [{"id": "x"}])
        return _response(200, {"id": "x"})

    with NetautoApiClient(
        "http://127.0.0.1:8000",
        transport=httpx.MockTransport(handler),
    ) as client:
        assert client.list_object_templates() == [{"id": "x"}]
        assert client.get_object_template("abc") == {"id": "x"}


def test_object_client_builds_correct_urls_and_bodies() -> None:
    seen: list[tuple[str, str, object]] = []
    object_payload = {
        "id": "object-1",
        "template_id": "template-1",
        "template_version": 2,
        "properties": {"hostname": "router-01"},
    }
    membership_payload = {
        "parent_object_id": "parent-1",
        "slot_name": "interfaces",
        "component_object_id": "child-1",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        body = request.read().decode()
        seen.append((request.method, str(request.url), json.loads(body) if body else None))
        if request.method == "GET" and (
            request.url.path.endswith("/objects")
            or request.url.path.endswith("/components")
        ):
            if request.url.path.endswith("/components"):
                return _response(200, [membership_payload])
            return _response(200, [object_payload])
        if request.method == "DELETE" and request.url.path.endswith("/objects/object-1"):
            return httpx.Response(204)
        if request.url.path.endswith("/components/child-1"):
            return _response(200, membership_payload)
        return _response(200, object_payload)

    with NetautoApiClient(
        "http://127.0.0.1:8000/",
        transport=httpx.MockTransport(handler),
    ) as client:
        client.list_objects()
        client.get_object("object-1")
        client.create_object(
            {
                "template_id": "template-1",
                "template_version": 2,
                "properties": {"hostname": "router-01", "enabled": True},
            }
        )
        client.update_object(
            "object-1",
            {
                "properties": {"hostname": "router-02"},
                "remove_properties": ["serial"],
            },
        )
        client.delete_object("object-1")
        client.list_object_components("parent-1")
        client.attach_object_component(
            "parent-1",
            {
                "slot_name": "interfaces",
                "component_object_id": "child-1",
            },
        )
        client.detach_object_component("child-1")

    assert seen == [
        ("GET", "http://127.0.0.1:8000/api/v1/objects", None),
        ("GET", "http://127.0.0.1:8000/api/v1/objects/object-1", None),
        (
            "POST",
            "http://127.0.0.1:8000/api/v1/objects",
            {
                "template_id": "template-1",
                "template_version": 2,
                "properties": {"hostname": "router-01", "enabled": True},
            },
        ),
        (
            "PATCH",
            "http://127.0.0.1:8000/api/v1/objects/object-1",
            {
                "properties": {"hostname": "router-02"},
                "remove_properties": ["serial"],
            },
        ),
        ("DELETE", "http://127.0.0.1:8000/api/v1/objects/object-1", None),
        ("GET", "http://127.0.0.1:8000/api/v1/objects/parent-1/components", None),
        (
            "POST",
            "http://127.0.0.1:8000/api/v1/objects/parent-1/components",
            {
                "slot_name": "interfaces",
                "component_object_id": "child-1",
            },
        ),
        ("DELETE", "http://127.0.0.1:8000/api/v1/objects/components/child-1", None),
    ]


def test_object_client_returns_objects_arrays_and_empty_delete() -> None:
    object_payload = {
        "id": "object-1",
        "template_id": "template-1",
        "template_version": 2,
        "properties": {},
    }
    membership_payload = {
        "parent_object_id": "parent-1",
        "slot_name": "interfaces",
        "component_object_id": "child-1",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/objects"):
            return _response(200, [object_payload])
        if path.endswith("/components"):
            return _response(200, [membership_payload])
        if path.endswith("/objects/object-1"):
            if request.method == "DELETE":
                return httpx.Response(204)
            return _response(200, object_payload)
        return _response(200, membership_payload)

    with NetautoApiClient(
        "http://127.0.0.1:8000",
        transport=httpx.MockTransport(handler),
    ) as client:
        assert client.list_objects() == [object_payload]
        assert client.get_object("object-1") == object_payload
        assert client.list_object_components("parent-1") == [membership_payload]
        assert client.detach_object_component("child-1") == membership_payload
        assert client.delete_object("object-1") is None


@pytest.mark.parametrize("status_code", [404, 409, 422, 500])
def test_client_raises_api_error_for_valid_netauto_error(status_code: int) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return _response(
            status_code,
            {
                "error": {
                    "code": "some_code",
                    "message": "Some message",
                    "details": [{"path": "/body/x", "code": "bad", "message": "Bad"}],
                }
            },
        )

    with NetautoApiClient(
        "http://127.0.0.1:8000",
        transport=httpx.MockTransport(handler),
    ) as client:
        with pytest.raises(ApiError) as error:
            client.get_datatype("abc")

    assert error.value.status_code == status_code
    assert error.value.code == "some_code"


def test_client_raises_protocol_error_for_malformed_error_envelope() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return _response(404, {"detail": "nope"})

    with NetautoApiClient(
        "http://127.0.0.1:8000",
        transport=httpx.MockTransport(handler),
    ) as client:
        with pytest.raises(ProtocolError):
            client.get_datatype("abc")


@pytest.mark.parametrize(
    ("payload", "operation"),
    [
        ({}, "list"),
        ([], "object"),
    ],
)
def test_client_raises_protocol_error_for_wrong_success_shape(
    payload: object,
    operation: str,
) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return _response(200, payload)

    with NetautoApiClient(
        "http://127.0.0.1:8000",
        transport=httpx.MockTransport(handler),
    ) as client:
        with pytest.raises(ProtocolError):
            if operation == "list":
                client.list_datatypes()
            else:
                client.get_datatype("abc")


def test_client_raises_protocol_error_for_malformed_json() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=b"{bad json",
            headers={"content-type": "application/json"},
        )

    with NetautoApiClient(
        "http://127.0.0.1:8000",
        transport=httpx.MockTransport(handler),
    ) as client:
        with pytest.raises(ProtocolError):
            client.list_datatypes()


def test_client_raises_transport_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    with NetautoApiClient(
        "http://127.0.0.1:8000",
        transport=httpx.MockTransport(handler),
    ) as client:
        with pytest.raises(TransportError):
            client.list_datatypes()


def test_client_rejects_invalid_url() -> None:
    with pytest.raises(InputError):
        NetautoApiClient("not-a-url")
