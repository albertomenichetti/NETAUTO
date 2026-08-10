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
            lines.append(f"  - {_require_string(item, 'name')}: {rendered_value}")
    return "\n".join(lines)


def render_datatype_delete_result(datatype_id: str, mode: OutputMode) -> str:
    if mode is OutputMode.JSON:
        return render_json({"deleted_datatype_id": datatype_id})
    return f"Deleted datatype {datatype_id}"


def render_object_template_list(payload: JSONArray, mode: OutputMode) -> str:
    if mode is OutputMode.JSON:
        return render_json(payload)
    rows = []
    for item in payload:
        template = _require_object(item)
        rows.append(
            (
                _require_string(template, "qualified_name"),
                _require_string(template, "id"),
                _format_bool(_require_bool(template, "abstract")),
                _optional_string(template, "description"),
            )
        )
    return _table(("QUALIFIED NAME", "ID", "ABSTRACT", "DESCRIPTION"), rows)


def render_object_template(payload: JSONObject, mode: OutputMode) -> str:
    if mode is OutputMode.JSON:
        return render_json(payload)
    return "\n".join(
        [
            f"Qualified Name: {_require_string(payload, 'qualified_name')}",
            f"ID: {_require_string(payload, 'id')}",
            f"Namespace: {_require_string(payload, 'namespace')}",
            f"Name: {_require_string(payload, 'name')}",
            f"Abstract: {_format_bool(_require_bool(payload, 'abstract'))}",
            f"Description: {_optional_string(payload, 'description')}",
        ]
    )


def render_object_template_create_result(payload: JSONObject, mode: OutputMode) -> str:
    if mode is OutputMode.JSON:
        return render_json(payload)
    template = _require_object(payload.get("object_template"))
    version = _require_object(payload.get("version"))
    return "\n".join(
        [
            f"Created {_require_string(template, 'qualified_name')}",
            f"ID: {_require_string(template, 'id')}",
            f"Version: {_require_int(version, 'version')}",
            f"Status: {_require_string(version, 'status')}",
            f"Abstract: {_format_bool(_require_bool(template, 'abstract'))}",
        ]
    )


def render_object_template_version_list(payload: JSONArray, mode: OutputMode) -> str:
    if mode is OutputMode.JSON:
        return render_json(payload)
    rows = []
    for item in payload:
        version = _require_object(item)
        rows.append(
            (
                str(_require_int(version, "version")),
                _require_string(version, "status"),
                _render_parent(version.get("parent")),
                str(len(_require_array(version, "properties"))),
                str(len(_require_array(version, "components"))),
            )
        )
    return _table(("VERSION", "STATUS", "PARENT", "PROPERTIES", "COMPONENTS"), rows)


def render_object_template_version(
    payload: JSONObject,
    mode: OutputMode,
    *,
    prefix: str | None = None,
) -> str:
    if mode is OutputMode.JSON:
        return render_json(payload)
    properties = _require_array(payload, "properties")
    components = _require_array(payload, "components")
    lines = []
    if prefix is not None:
        lines.append(prefix)
    lines.extend(
        [
            f"ObjectTemplate ID: {_require_string(payload, 'template_id')}",
            f"Version: {_require_int(payload, 'version')}",
            f"Status: {_require_string(payload, 'status')}",
            f"Parent: {_render_parent(payload.get('parent'))}",
            "Properties:",
        ]
    )
    if not properties:
        lines.append("  (none)")
    else:
        for item in properties:
            prop = _require_object(item)
            lines.append(
                "  - "
                f"{_require_string(prop, 'name')}: "
                f"{_require_string(prop, 'datatype_id')}@{_require_int(prop, 'datatype_version')} "
                f"({'required' if _require_bool(prop, 'required') else 'optional'})"
            )
    lines.append("Components:")
    if not components:
        lines.append("  (none)")
    else:
        for item in components:
            component = _require_object(item)
            lines.append(
                "  - "
                f"{_require_string(component, 'name')}: "
                f"{_require_string(component, 'template_id')}"
            )
    return "\n".join(lines)


def render_object_list(payload: JSONArray, mode: OutputMode) -> str:
    if mode is OutputMode.JSON:
        return render_json(payload)
    rows = []
    for item in payload:
        object_value = _require_object(item)
        properties = _require_object(object_value.get("properties"))
        rows.append(
            (
                _require_string(object_value, "id"),
                _require_string(object_value, "template_id"),
                str(_require_int(object_value, "template_version")),
                str(len(properties)),
            )
        )
    return _table(("ID", "TEMPLATE ID", "TEMPLATE VERSION", "PROPERTIES"), rows)


def render_object(payload: JSONObject, mode: OutputMode, *, prefix: str | None = None) -> str:
    if mode is OutputMode.JSON:
        return render_json(payload)
    properties = _require_object(payload.get("properties"))
    lines = []
    if prefix is not None:
        lines.append(prefix)
    lines.extend(
        [
            f"ID: {_require_string(payload, 'id')}",
            f"Template ID: {_require_string(payload, 'template_id')}",
            f"Template Version: {_require_int(payload, 'template_version')}",
            "Properties:",
        ]
    )
    if not properties:
        lines.append("  (none)")
    else:
        for name, value in properties.items():
            if not isinstance(name, str):
                raise ProtocolError("Server returned an incompatible response.")
            lines.append(f"  - {name}: {json.dumps(value, ensure_ascii=False)}")
    return "\n".join(lines)


def render_component_membership_list(payload: JSONArray, mode: OutputMode) -> str:
    if mode is OutputMode.JSON:
        return render_json(payload)
    rows = []
    for item in payload:
        membership = _require_object(item)
        rows.append(
            (
                _require_string(membership, "parent_object_id"),
                _require_string(membership, "slot_name"),
                _require_string(membership, "component_object_id"),
            )
        )
    return _table(("PARENT OBJECT ID", "SLOT", "COMPONENT OBJECT ID"), rows)


def render_component_membership(
    payload: JSONObject,
    mode: OutputMode,
    *,
    prefix: str | None = None,
) -> str:
    if mode is OutputMode.JSON:
        return render_json(payload)
    lines = []
    if prefix is not None:
        lines.append(prefix)
    lines.extend(
        [
            f"Parent Object ID: {_require_string(payload, 'parent_object_id')}",
            f"Slot Name: {_require_string(payload, 'slot_name')}",
            f"Component Object ID: {_require_string(payload, 'component_object_id')}",
        ]
    )
    return "\n".join(lines)


def render_relationship_definition_list(payload: JSONArray, mode: OutputMode) -> str:
    if mode is OutputMode.JSON:
        return render_json(payload)
    rows = []
    for item in payload:
        definition = _require_object(item)
        rows.append(
            (
                _require_string(definition, "id"),
                _require_string(definition, "source_template_id"),
                _require_string(definition, "target_template_id"),
                _require_string(definition, "forward_name"),
                _require_string(definition, "reverse_name"),
            )
        )
    return _table(
        ("ID", "SOURCE TEMPLATE ID", "TARGET TEMPLATE ID", "FORWARD", "REVERSE"),
        rows,
    )


def render_relationship_definition(
    payload: JSONObject,
    mode: OutputMode,
    *,
    prefix: str | None = None,
) -> str:
    if mode is OutputMode.JSON:
        return render_json(payload)
    lines = []
    if prefix is not None:
        lines.append(prefix)
    lines.extend(
        [
            f"ID: {_require_string(payload, 'id')}",
            f"Source Template ID: {_require_string(payload, 'source_template_id')}",
            f"Target Template ID: {_require_string(payload, 'target_template_id')}",
            f"Forward Name: {_require_string(payload, 'forward_name')}",
            f"Reverse Name: {_require_string(payload, 'reverse_name')}",
        ]
    )
    return "\n".join(lines)


def render_relationship_definition_delete_result(
    _payload: object,
    mode: OutputMode,
    *,
    definition_id: str,
) -> str:
    if mode is OutputMode.JSON:
        return render_json(None)
    return f"Deleted relationship definition {definition_id}"


def render_relationship_list(payload: JSONArray, mode: OutputMode) -> str:
    if mode is OutputMode.JSON:
        return render_json(payload)
    rows = []
    for item in payload:
        relationship = _require_object(item)
        rows.append(
            (
                _require_string(relationship, "id"),
                _require_string(relationship, "relationship_definition_id"),
                _require_string(relationship, "source_object_id"),
                _require_string(relationship, "target_object_id"),
            )
        )
    return _table(
        ("ID", "RELATIONSHIP DEFINITION ID", "SOURCE OBJECT ID", "TARGET OBJECT ID"),
        rows,
    )


def render_relationship(
    payload: JSONObject,
    mode: OutputMode,
    *,
    prefix: str | None = None,
) -> str:
    if mode is OutputMode.JSON:
        return render_json(payload)
    lines = []
    if prefix is not None:
        lines.append(prefix)
    lines.extend(
        [
            f"ID: {_require_string(payload, 'id')}",
            "Relationship Definition ID: "
            f"{_require_string(payload, 'relationship_definition_id')}",
            f"Source Object ID: {_require_string(payload, 'source_object_id')}",
            f"Target Object ID: {_require_string(payload, 'target_object_id')}",
        ]
    )
    return "\n".join(lines)


def render_relationship_delete_result(
    _payload: object,
    mode: OutputMode,
    *,
    relationship_id: str,
) -> str:
    if mode is OutputMode.JSON:
        return render_json(None)
    return f"Deleted relationship {relationship_id}"


def render_effective_relationship_definition_list(payload: JSONArray, mode: OutputMode) -> str:
    if mode is OutputMode.JSON:
        return render_json(payload)
    rows = []
    for item in payload:
        definition = _require_object(item)
        rows.append(
            (
                _require_string(definition, "relationship_definition_id"),
                _require_string(definition, "direction"),
                _require_string(definition, "name"),
                _require_string(definition, "related_template_id"),
            )
        )
    return _table(
        ("RELATIONSHIP DEFINITION ID", "DIRECTION", "NAME", "RELATED TEMPLATE ID"),
        rows,
    )


def render_relationship_navigation_list(payload: JSONArray, mode: OutputMode) -> str:
    if mode is OutputMode.JSON:
        return render_json(payload)
    rows = []
    for item in payload:
        view = _require_object(item)
        rows.append(
            (
                _require_string(view, "relationship_id"),
                _require_string(view, "relationship_definition_id"),
                _require_string(view, "direction"),
                _require_string(view, "name"),
                _require_string(view, "related_object_id"),
                _require_string(view, "source_object_id"),
                _require_string(view, "target_object_id"),
            )
        )
    return _table(
        (
            "RELATIONSHIP ID",
            "RELATIONSHIP DEFINITION ID",
            "DIRECTION",
            "NAME",
            "RELATED OBJECT ID",
            "SOURCE OBJECT ID",
            "TARGET OBJECT ID",
        ),
        rows,
    )


def render_object_delete_result(
    _payload: object,
    mode: OutputMode,
    *,
    object_id: str,
) -> str:
    if mode is OutputMode.JSON:
        return render_json(None)
    return f"Deleted object {object_id}"


def render_object_migration_analysis(payload: JSONObject, mode: OutputMode) -> str:
    if mode is OutputMode.JSON:
        return render_json(payload)

    added_properties = _require_array(payload, "added_properties")
    added_components = _require_array(payload, "added_components")
    blocking_changes = _require_array(payload, "blocking_changes")
    lines = [
        f"Template ID: {_require_string(payload, 'template_id')}",
        f"Source Version: {_require_int(payload, 'source_version')}",
        f"Target Version: {_require_int(payload, 'target_version')}",
        f"Automatic: {_format_bool(_require_bool(payload, 'automatic'))}",
        "Added Properties:",
    ]
    if not added_properties:
        lines.append("  (none)")
    else:
        for item in added_properties:
            property_value = _require_object(item)
            lines.append(
                "  - "
                f"{_require_string(property_value, 'name')} "
                f"({'required' if _require_bool(property_value, 'required') else 'optional'})"
            )
    lines.append("Added Components:")
    if not added_components:
        lines.append("  (none)")
    else:
        for item in added_components:
            component = _require_object(item)
            lines.append(
                "  - "
                f"{_require_string(component, 'name')}: "
                f"{_require_string(component, 'template_id')}"
            )
    lines.append("Blocking Changes:")
    if not blocking_changes:
        lines.append("  (none)")
    else:
        for item in blocking_changes:
            change = _require_object(item)
            lines.append(
                "  - "
                f"{_require_string(change, 'kind')}: "
                f"{_require_string(change, 'name')}"
            )
    return "\n".join(lines)


def render_object_migration_result(payload: JSONObject, mode: OutputMode) -> str:
    if mode is OutputMode.JSON:
        return render_json(payload)
    return "\n".join(
        [
            "Migrated objects",
            f"Template ID: {_require_string(payload, 'template_id')}",
            f"Source Version: {_require_int(payload, 'source_version')}",
            f"Target Version: {_require_int(payload, 'target_version')}",
            f"Migrated Count: {_require_int(payload, 'migrated_count')}",
        ]
    )


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


def _require_bool(payload: JSONObject, key: str) -> bool:
    value = payload.get(key)
    if not isinstance(value, bool):
        raise ProtocolError("Server returned an incompatible response.")
    return value


def _require_array(payload: JSONObject, key: str) -> JSONArray:
    value = payload.get(key)
    if not isinstance(value, list):
        raise ProtocolError("Server returned an incompatible response.")
    return value


def _render_parent(value: object) -> str:
    if value is None:
        return "-"
    parent = _require_object(value)
    return f"{_require_string(parent, 'template_id')}@{_require_int(parent, 'version')}"


def _format_bool(value: bool) -> str:
    return "yes" if value else "no"
