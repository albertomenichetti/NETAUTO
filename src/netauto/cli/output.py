"""CLI rendering helpers."""

from __future__ import annotations

import json
from enum import StrEnum
from typing import Any

from netauto.cli.client import JSONArray, JSONObject
from netauto.cli.errors import ApiError, CliError, InputError, ProtocolError, TransportError


class OutputMode(StrEnum):
    HUMAN = "human"
    JSON = "json"


def render_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def render_error(error: CliError, mode: OutputMode) -> str:
    if mode is OutputMode.JSON:
        return render_json(_error_payload(error))
    return _render_human_error(error)


def render_datatype_list(payload: JSONArray, mode: OutputMode) -> str:
    if mode is OutputMode.JSON:
        return render_json(payload)
    rows = []
    for item in payload:
        datatype = _require_object(item)
        rows.append(
            (
                _require_string(datatype, "qualified_name"),
                _require_string(datatype, "id"),
                _optional_string(datatype, "description"),
            )
        )
    return _table(
        ("QUALIFIED NAME", "ID", "DESCRIPTION"),
        rows,
    )


def render_datatype(payload: JSONObject, mode: OutputMode) -> str:
    if mode is OutputMode.JSON:
        return render_json(payload)
    return "\n".join(
        [
            f"Qualified Name: {_require_string(payload, 'qualified_name')}",
            f"ID: {_require_string(payload, 'id')}",
            f"Namespace: {_require_string(payload, 'namespace')}",
            f"Name: {_require_string(payload, 'name')}",
            f"Description: {_optional_string(payload, 'description')}",
        ]
    )


def render_create_result(payload: JSONObject, mode: OutputMode) -> str:
    if mode is OutputMode.JSON:
        return render_json(payload)
    datatype = _require_object(payload.get("datatype"))
    version = _require_object(payload.get("version"))
    return "\n".join(
        [
            f"Created {_require_string(datatype, 'qualified_name')}",
            f"ID: {_require_string(datatype, 'id')}",
            f"Version: {_require_int(version, 'version')}",
            f"Status: {_require_string(version, 'status')}",
        ]
    )


def render_version_list(payload: JSONArray, mode: OutputMode) -> str:
    if mode is OutputMode.JSON:
        return render_json(payload)
    rows = []
    for item in payload:
        version = _require_object(item)
        constraints = version.get("constraints")
        if not isinstance(constraints, list):
            raise ProtocolError("Server returned an incompatible response.")
        rows.append(
            (
                str(_require_int(version, "version")),
                _require_string(version, "status"),
                _require_string(version, "base_type"),
                str(len(constraints)),
            )
        )
    return _table(("VERSION", "STATUS", "BASE TYPE", "CONSTRAINTS"), rows)


def render_version(payload: JSONObject, mode: OutputMode, *, prefix: str | None = None) -> str:
    if mode is OutputMode.JSON:
        return render_json(payload)
    constraints = payload.get("constraints")
    if not isinstance(constraints, list):
        raise ProtocolError("Server returned an incompatible response.")
    lines = []
    if prefix is not None:
        lines.append(prefix)
    lines.extend(
        [
            f"DataType ID: {_require_string(payload, 'datatype_id')}",
            f"Version: {_require_int(payload, 'version')}",
            f"Status: {_require_string(payload, 'status')}",
            f"Base Type: {_require_string(payload, 'base_type')}",
            "Constraints:",
        ]
    )
    if not constraints:
        lines.append("  (none)")
    else:
        for constraint in constraints:
            item = _require_object(constraint)
            rendered_value = json.dumps(item.get("value"), ensure_ascii=False)
            lines.append(
                f"  - {_require_string(item, 'name')}: {rendered_value}"
            )
    return "\n".join(lines)


def _error_payload(error: CliError) -> JSONObject:
    if isinstance(error, ApiError):
        return {
            "error": {
                "code": error.code,
                "message": error.message,
                "details": error.details,
            }
        }
    if isinstance(error, TransportError):
        return {
            "error": {
                "code": "cli_transport_error",
                "message": "Could not connect to NETAUTO API",
                "details": [],
            }
        }
    if isinstance(error, ProtocolError):
        return {
            "error": {
                "code": "cli_protocol_error",
                "message": "Server returned an incompatible response",
                "details": [],
            }
        }
    if isinstance(error, InputError):
        return {
            "error": {
                "code": "cli_input_error",
                "message": str(error),
                "details": [],
            }
        }
    return {
        "error": {
            "code": "cli_error",
            "message": str(error),
            "details": [],
        }
    }


def _render_human_error(error: CliError) -> str:
    if isinstance(error, ApiError):
        lines = [f"Error [{error.code}]: {error.message}"]
        for detail in error.details:
            path = detail.get("path", "?")
            message = detail.get("message", "?")
            code = detail.get("code", "?")
            lines.append(f"  {path}: {message} [{code}]")
        return "\n".join(lines)
    if isinstance(error, TransportError):
        return "Error [cli_transport_error]: Could not connect to NETAUTO API"
    if isinstance(error, ProtocolError):
        return "Error [cli_protocol_error]: Server returned an incompatible response"
    if isinstance(error, InputError):
        return f"Error [cli_input_error]: {error}"
    return f"Error [cli_error]: {error}"


def _table(headers: tuple[str, ...], rows: list[tuple[str, ...]]) -> str:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))
    header_line = "  ".join(header.ljust(widths[index]) for index, header in enumerate(headers))
    body = [
        "  ".join(value.ljust(widths[index]) for index, value in enumerate(row))
        for row in rows
    ]
    return "\n".join([header_line, *body]) if body else header_line


def _require_object(value: object) -> JSONObject:
    if not isinstance(value, dict):
        raise ProtocolError("Server returned an incompatible response.")
    return value


def _require_string(payload: JSONObject, key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise ProtocolError("Server returned an incompatible response.")
    return value


def _optional_string(payload: JSONObject, key: str) -> str:
    value = payload.get(key)
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ProtocolError("Server returned an incompatible response.")
    return value


def _require_int(payload: JSONObject, key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ProtocolError("Server returned an incompatible response.")
    return value
