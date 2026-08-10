"""HTTP client for the NETAUTO REST API."""

from __future__ import annotations

from collections.abc import Mapping
from json import JSONDecodeError
from typing import TypeAlias
from urllib.parse import urlsplit, urlunsplit

import httpx

from netauto.cli.errors import ApiError, InputError, ProtocolError, TransportError

JSONValue: TypeAlias = object
JSONObject: TypeAlias = dict[str, object]
JSONArray: TypeAlias = list[object]


class NetautoApiClient:
    """Synchronous HTTP client for the NETAUTO API."""

    def __init__(
        self,
        api_url: str,
        *,
        transport: httpx.BaseTransport | None = None,
        timeout: float | httpx.Timeout = 5.0,
    ) -> None:
        self._base_url = _normalize_api_url(api_url)
        try:
            self._client = httpx.Client(
                base_url=self._base_url,
                follow_redirects=False,
                timeout=timeout,
                transport=transport,
            )
        except httpx.InvalidURL as error:
            raise InputError("API URL is invalid.") from error

    def __enter__(self) -> NetautoApiClient:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def list_datatypes(self) -> JSONArray:
        return self._request_array("GET", "/datatypes")

    def get_datatype(self, datatype_id: str) -> JSONObject:
        return self._request_object("GET", f"/datatypes/{datatype_id}")

    def get_datatype_by_name(self, namespace: str, name: str) -> JSONObject:
        return self._request_object("GET", f"/datatypes/by-name/{namespace}/{name}")

    def create_datatype(self, payload: JSONObject) -> JSONObject:
        return self._request_object("POST", "/datatypes", json_body=payload)

    def list_versions(self, datatype_id: str) -> JSONArray:
        return self._request_array("GET", f"/datatypes/{datatype_id}/versions")

    def get_version(self, datatype_id: str, version: int) -> JSONObject:
        return self._request_object("GET", f"/datatypes/{datatype_id}/versions/{version}")

    def revise_version(self, datatype_id: str, version: int, payload: JSONObject) -> JSONObject:
        return self._request_object(
            "PUT",
            f"/datatypes/{datatype_id}/versions/{version}",
            json_body=payload,
        )

    def create_version(self, datatype_id: str, source_version: int) -> JSONObject:
        return self._request_object(
            "POST",
            f"/datatypes/{datatype_id}/versions",
            json_body={"source_version": source_version},
        )

    def publish_version(self, datatype_id: str, version: int) -> JSONObject:
        return self._request_object(
            "POST",
            f"/datatypes/{datatype_id}/versions/{version}/publish",
        )

    def deprecate_version(self, datatype_id: str, version: int) -> JSONObject:
        return self._request_object(
            "POST",
            f"/datatypes/{datatype_id}/versions/{version}/deprecate",
        )

    def list_object_templates(self) -> JSONArray:
        return self._request_array("GET", "/object-templates")

    def get_object_template(self, template_id: str) -> JSONObject:
        return self._request_object("GET", f"/object-templates/{template_id}")

    def get_object_template_by_name(self, namespace: str, name: str) -> JSONObject:
        return self._request_object(
            "GET",
            f"/object-templates/by-name/{namespace}/{name}",
        )

    def create_object_template(self, payload: JSONObject) -> JSONObject:
        return self._request_object("POST", "/object-templates", json_body=payload)

    def list_object_template_versions(self, template_id: str) -> JSONArray:
        return self._request_array("GET", f"/object-templates/{template_id}/versions")

    def get_object_template_version(self, template_id: str, version: int) -> JSONObject:
        return self._request_object(
            "GET",
            f"/object-templates/{template_id}/versions/{version}",
        )

    def revise_object_template_version(
        self,
        template_id: str,
        version: int,
        payload: JSONObject,
    ) -> JSONObject:
        return self._request_object(
            "PUT",
            f"/object-templates/{template_id}/versions/{version}",
            json_body=payload,
        )

    def create_object_template_version(self, template_id: str, source_version: int) -> JSONObject:
        return self._request_object(
            "POST",
            f"/object-templates/{template_id}/versions",
            json_body={"source_version": source_version},
        )

    def publish_object_template_version(self, template_id: str, version: int) -> JSONObject:
        return self._request_object(
            "POST",
            f"/object-templates/{template_id}/versions/{version}/publish",
        )

    def deprecate_object_template_version(self, template_id: str, version: int) -> JSONObject:
        return self._request_object(
            "POST",
            f"/object-templates/{template_id}/versions/{version}/deprecate",
        )

    def get_object_migration_analysis(
        self,
        template_id: str,
        source_version: int,
        target_version: int,
    ) -> JSONObject:
        return self._request_object(
            "GET",
            (
                f"/object-templates/{template_id}/versions/{source_version}/migration-analysis"
                f"?target_version={target_version}"
            ),
        )

    def migrate_objects(
        self,
        template_id: str,
        source_version: int,
        payload: JSONObject,
    ) -> JSONObject:
        return self._request_object(
            "POST",
            f"/object-templates/{template_id}/versions/{source_version}/migrate-objects",
            json_body=payload,
        )

    def list_objects(self) -> JSONArray:
        return self._request_array("GET", "/objects")

    def get_object(self, object_id: str) -> JSONObject:
        return self._request_object("GET", f"/objects/{object_id}")

    def create_object(self, payload: JSONObject) -> JSONObject:
        return self._request_object("POST", "/objects", json_body=payload)

    def update_object(self, object_id: str, payload: JSONObject) -> JSONObject:
        return self._request_object("PATCH", f"/objects/{object_id}", json_body=payload)

    def delete_object(self, object_id: str) -> None:
        self._request_empty("DELETE", f"/objects/{object_id}")

    def list_effective_relationship_definitions(self, object_id: str) -> JSONArray:
        return self._request_array(
            "GET",
            f"/objects/{object_id}/relationship-definitions/effective",
        )

    def list_outgoing_relationships(self, object_id: str) -> JSONArray:
        return self._request_array("GET", f"/objects/{object_id}/relationships/outgoing")

    def list_incoming_relationships(self, object_id: str) -> JSONArray:
        return self._request_array("GET", f"/objects/{object_id}/relationships/incoming")

    def list_neighbor_relationships(self, object_id: str) -> JSONArray:
        return self._request_array("GET", f"/objects/{object_id}/relationships/neighbors")

    def list_object_components(self, object_id: str) -> JSONArray:
        return self._request_array("GET", f"/objects/{object_id}/components")

    def attach_object_component(self, object_id: str, payload: JSONObject) -> JSONObject:
        return self._request_object("POST", f"/objects/{object_id}/components", json_body=payload)

    def detach_object_component(self, component_object_id: str) -> JSONObject:
        return self._request_object("DELETE", f"/objects/components/{component_object_id}")

    def list_relationship_definitions(self) -> JSONArray:
        return self._request_array("GET", "/relationship-definitions")

    def get_relationship_definition(self, definition_id: str) -> JSONObject:
        return self._request_object("GET", f"/relationship-definitions/{definition_id}")

    def create_relationship_definition(self, payload: JSONObject) -> JSONObject:
        return self._request_object("POST", "/relationship-definitions", json_body=payload)

    def delete_relationship_definition(self, definition_id: str) -> None:
        self._request_empty("DELETE", f"/relationship-definitions/{definition_id}")

    def list_relationships(self) -> JSONArray:
        return self._request_array("GET", "/relationships")

    def get_relationship(self, relationship_id: str) -> JSONObject:
        return self._request_object("GET", f"/relationships/{relationship_id}")

    def create_relationship(self, payload: JSONObject) -> JSONObject:
        return self._request_object("POST", "/relationships", json_body=payload)

    def delete_relationship(self, relationship_id: str) -> None:
        self._request_empty("DELETE", f"/relationships/{relationship_id}")

    def _request_object(
        self,
        method: str,
        path: str,
        *,
        json_body: JSONObject | None = None,
    ) -> JSONObject:
        payload = self._request_json(method, path, json_body=json_body)
        if not isinstance(payload, dict):
            raise ProtocolError("Server returned an incompatible response.")
        return payload

    def _request_array(
        self,
        method: str,
        path: str,
        *,
        json_body: JSONObject | None = None,
    ) -> JSONArray:
        payload = self._request_json(method, path, json_body=json_body)
        if not isinstance(payload, list):
            raise ProtocolError("Server returned an incompatible response.")
        return payload

    def _request_empty(
        self,
        method: str,
        path: str,
        *,
        json_body: JSONObject | None = None,
    ) -> None:
        try:
            response = self._client.request(method, path, json=json_body)
        except httpx.InvalidURL as error:
            raise InputError("API URL is invalid.") from error
        except httpx.RequestError as error:
            raise TransportError("Could not connect to NETAUTO API.") from error

        if 200 <= response.status_code < 300:
            return

        payload = _decode_json(response)
        if not isinstance(payload, dict):
            raise ProtocolError("Server returned an incompatible response.")
        raise _parse_error_envelope(payload, response.status_code)

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        json_body: JSONObject | None = None,
    ) -> JSONValue:
        try:
            response = self._client.request(method, path, json=json_body)
        except httpx.InvalidURL as error:
            raise InputError("API URL is invalid.") from error
        except httpx.RequestError as error:
            raise TransportError("Could not connect to NETAUTO API.") from error

        payload = _decode_json(response)
        if 200 <= response.status_code < 300:
            return payload

        if not isinstance(payload, dict):
            raise ProtocolError("Server returned an incompatible response.")
        error_payload = _parse_error_envelope(payload, response.status_code)
        raise error_payload


def _normalize_api_url(api_url: str) -> str:
    if not api_url.strip():
        raise InputError("API URL is invalid.")
    try:
        parts = urlsplit(api_url)
    except ValueError as error:
        raise InputError("API URL is invalid.") from error
    if not parts.scheme or not parts.netloc:
        raise InputError("API URL is invalid.")

    path = parts.path.rstrip("/")
    if path.endswith("/api/v1"):
        path = path[: -len("/api/v1")]
    base_path = f"{path}/api/v1" if path else "/api/v1"
    return urlunsplit((parts.scheme, parts.netloc, base_path, "", ""))


def _decode_json(response: httpx.Response) -> JSONValue:
    try:
        return response.json()
    except (JSONDecodeError, ValueError) as error:
        raise ProtocolError("Server returned an incompatible response.") from error


def _parse_error_envelope(payload: Mapping[str, object], status_code: int) -> ApiError:
    error_object = payload.get("error")
    if not isinstance(error_object, Mapping):
        raise ProtocolError("Server returned an incompatible response.")

    code = error_object.get("code")
    message = error_object.get("message")
    details = error_object.get("details", [])
    if not isinstance(code, str) or not isinstance(message, str) or not isinstance(details, list):
        raise ProtocolError("Server returned an incompatible response.")

    normalized_details: list[dict[str, object]] = []
    for detail in details:
        if isinstance(detail, Mapping):
            normalized_details.append(dict(detail))
        else:
            raise ProtocolError("Server returned an incompatible response.")

    return ApiError(
        status_code=status_code,
        code=code,
        message=message,
        details=normalized_details,
    )
