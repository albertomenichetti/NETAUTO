"""Bounded GET-only presentation enrichment for formatted single reads."""

from dataclasses import dataclass
from typing import cast

from netauto.cli.model import (
    CliError,
    ErrorSource,
    JsonValue,
    ParsedCommand,
    RequestPlan,
)
from netauto.cli.protocol import interpret_response
from netauto.cli.transport import HttpTransport, TransportFailure
from netauto.transport.http.datatypes import DataTypeDto
from netauto.transport.http.objects import ObjectDto
from netauto.transport.http.objecttemplates import (
    ObjectTemplateDto,
    ObjectTemplateVersionDto,
)


@dataclass(frozen=True, slots=True)
class EnrichmentOutcome:
    presentation: JsonValue | None
    error: CliError | None


def _protocol_error(http_status: int | None = None) -> CliError:
    return CliError.create(
        ErrorSource.PROTOCOL,
        "cli_protocol_error",
        "The server response violates the same-release HTTP contract.",
        http_status=http_status,
    )


class _Context:
    def __init__(self, transport: HttpTransport) -> None:
        self.transport = transport
        self.cache: dict[tuple[str, str], dict[str, JsonValue]] = {}

    async def get(
        self,
        kind: str,
        identity: str,
        path: str,
        annotation: object,
    ) -> tuple[dict[str, JsonValue] | None, CliError | None]:
        key = (kind, identity)
        cached = self.cache.get(key)
        if cached is not None:
            return cached, None
        try:
            response, exchange = await self.transport.exchange(
                RequestPlan.create("GET", path, (), None)
            )
        except TransportFailure:
            return (
                None,
                CliError.create(
                    ErrorSource.TRANSPORT,
                    "cli_transport_error",
                    "The HTTP request could not be completed.",
                ),
            )
        outcome = interpret_response(
            response,
            exchange,
            expected_status=200,
            response_annotation=annotation,
        )
        if outcome.error is not None:
            return None, _protocol_error(response.status_code)
        if not isinstance(outcome.result, dict):
            return None, _protocol_error(response.status_code)
        value = cast(dict[str, JsonValue], outcome.result)
        self.cache[key] = value
        return value, None

    async def datatype(
        self, datatype_id: str
    ) -> tuple[dict[str, JsonValue] | None, CliError | None]:
        return await self.get(
            "datatype",
            datatype_id,
            f"/api/v1/core/datatypes/{datatype_id}",
            DataTypeDto,
        )

    async def template(
        self, template_id: str
    ) -> tuple[dict[str, JsonValue] | None, CliError | None]:
        return await self.get(
            "object-template",
            template_id,
            f"/api/v1/core/object-templates/{template_id}",
            ObjectTemplateDto,
        )

    async def template_version(
        self, template_id: str, version: int
    ) -> tuple[dict[str, JsonValue] | None, CliError | None]:
        return await self.get(
            "object-template-version",
            f"{template_id}:{version}",
            f"/api/v1/core/object-templates/{template_id}/versions/{version}",
            ObjectTemplateVersionDto,
        )

    async def object(
        self, object_id: str
    ) -> tuple[dict[str, JsonValue] | None, CliError | None]:
        return await self.get(
            "object",
            object_id,
            f"/api/v1/core/objects/{object_id}",
            ObjectDto,
        )


def _qualified_name(value: dict[str, JsonValue]) -> str | None:
    namespace = value.get("namespace")
    name = value.get("name")
    if isinstance(namespace, str) and isinstance(name, str):
        return f"{namespace}.{name}"
    return None


async def _template_name(
    context: _Context, template_id: str
) -> tuple[str | None, CliError | None]:
    value, error = await context.template(template_id)
    if error is not None or value is None:
        return None, error
    name = _qualified_name(value)
    return (name, None) if name is not None else (None, _protocol_error())


async def _datatype_name(
    context: _Context, datatype_id: str
) -> tuple[str | None, CliError | None]:
    value, error = await context.datatype(datatype_id)
    if error is not None or value is None:
        return None, error
    name = _qualified_name(value)
    return (name, None) if name is not None else (None, _protocol_error())


def _object_value(value: JsonValue | None) -> dict[str, JsonValue] | None:
    return cast(dict[str, JsonValue], value) if isinstance(value, dict) else None


def _string(value: JsonValue | None) -> str | None:
    return value if isinstance(value, str) else None


def _integer(value: JsonValue | None) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


async def enrich_formatted(
    transport: HttpTransport,
    command: ParsedCommand,
    result: JsonValue | None,
) -> EnrichmentOutcome:
    """Build one complete enriched presentation for the exact frozen read set."""

    key = (command.key.resource, command.key.operation)
    if key not in {
        ("datatype", "get-version"),
        ("object-template", "get"),
        ("object-template", "get-version"),
        ("object-template", "get-effective-schema"),
        ("object", "get"),
        ("object", "get-owner"),
        ("relationship-definition", "get"),
        ("relationship-definition", "get-version"),
        ("relationship", "get"),
    }:
        return EnrichmentOutcome(result, None)
    if result is None and key == ("object", "get-owner"):
        return EnrichmentOutcome(None, None)
    primary = _object_value(result)
    if primary is None:
        return EnrichmentOutcome(None, _protocol_error())
    presentation = {**primary}
    context = _Context(transport)

    if key == ("datatype", "get-version"):
        datatype_id = _string(primary.get("datatype_id"))
        if datatype_id is None:
            return EnrichmentOutcome(None, _protocol_error())
        name, error = await _datatype_name(context, datatype_id)
        if error is not None or name is None:
            return EnrichmentOutcome(None, error or _protocol_error())
        presentation["datatype_qualified_name"] = name

    elif key == ("object-template", "get"):
        lineage: list[JsonValue] = []
        current_id = _string(primary.get("id"))
        parent_id = _string(primary.get("parent_template_id"))
        if current_id is None:
            return EnrichmentOutcome(None, _protocol_error())
        seen = {current_id}
        while parent_id is not None:
            if parent_id in seen:
                return EnrichmentOutcome(None, _protocol_error())
            seen.add(parent_id)
            parent, error = await context.template(parent_id)
            if error is not None or parent is None:
                return EnrichmentOutcome(None, error or _protocol_error())
            name = _qualified_name(parent)
            if name is None:
                return EnrichmentOutcome(None, _protocol_error())
            lineage.append({"id": parent_id, "qualified_name": name})
            raw_parent = parent.get("parent_template_id")
            if raw_parent is not None and not isinstance(raw_parent, str):
                return EnrichmentOutcome(None, _protocol_error())
            parent_id = raw_parent
        presentation["parent_lineage"] = lineage

    elif key == ("object-template", "get-version"):
        owner_id = _string(primary.get("template_id"))
        if owner_id is None:
            return EnrichmentOutcome(None, _protocol_error())
        owner_name, error = await _template_name(context, owner_id)
        if error is not None or owner_name is None:
            return EnrichmentOutcome(None, error or _protocol_error())
        presentation["template_qualified_name"] = owner_name
        parent_chain: list[JsonValue] = []
        parent_id = _string(primary.get("parent_template_id"))
        parent_version = _integer(primary.get("parent_version"))
        owner_version = _integer(primary.get("version"))
        if owner_version is None:
            return EnrichmentOutcome(None, _protocol_error())
        seen_versions: set[tuple[str, int]] = {(owner_id, owner_version)}
        while parent_id is not None or parent_version is not None:
            if parent_id is None or parent_version is None:
                return EnrichmentOutcome(None, _protocol_error())
            version_key = (parent_id, parent_version)
            if version_key in seen_versions:
                return EnrichmentOutcome(None, _protocol_error())
            seen_versions.add(version_key)
            parent_name, error = await _template_name(context, parent_id)
            if error is not None or parent_name is None:
                return EnrichmentOutcome(None, error or _protocol_error())
            parent, error = await context.template_version(parent_id, parent_version)
            if error is not None or parent is None:
                return EnrichmentOutcome(None, error or _protocol_error())
            parent_chain.append(
                {
                    "template_id": parent_id,
                    "version": parent_version,
                    "qualified_name": parent_name,
                }
            )
            parent_id = _string(parent.get("parent_template_id"))
            parent_version = _integer(parent.get("parent_version"))
        presentation["parent_version_lineage"] = parent_chain
        properties = primary.get("properties")
        components = primary.get("components")
        if not isinstance(properties, list) or not isinstance(components, list):
            return EnrichmentOutcome(None, _protocol_error())
        enriched_properties: list[JsonValue] = []
        for item in properties:
            if not isinstance(item, dict):
                return EnrichmentOutcome(None, _protocol_error())
            prop = cast(dict[str, JsonValue], item)
            datatype_id = _string(prop.get("datatype_id"))
            if datatype_id is None:
                return EnrichmentOutcome(None, _protocol_error())
            datatype_name, error = await _datatype_name(context, datatype_id)
            if error is not None or datatype_name is None:
                return EnrichmentOutcome(None, error or _protocol_error())
            enriched_properties.append(
                {
                    **prop,
                    "datatype_qualified_name": datatype_name,
                    "declaring_template_qualified_name": owner_name,
                }
            )
        enriched_components: list[JsonValue] = []
        for item in components:
            if not isinstance(item, dict):
                return EnrichmentOutcome(None, _protocol_error())
            component = cast(dict[str, JsonValue], item)
            target_id = _string(component.get("target_template_id"))
            if target_id is None:
                return EnrichmentOutcome(None, _protocol_error())
            target_name, error = await _template_name(context, target_id)
            if error is not None or target_name is None:
                return EnrichmentOutcome(None, error or _protocol_error())
            enriched_components.append(
                {
                    **component,
                    "target_template_qualified_name": target_name,
                    "declaring_template_qualified_name": owner_name,
                }
            )
        presentation["properties"] = enriched_properties
        presentation["components"] = enriched_components

    elif key == ("object-template", "get-effective-schema"):
        owner_id = _string(primary.get("template_id"))
        if owner_id is None:
            return EnrichmentOutcome(None, _protocol_error())
        owner_name, error = await _template_name(context, owner_id)
        if error is not None or owner_name is None:
            return EnrichmentOutcome(None, error or _protocol_error())
        presentation["template_qualified_name"] = owner_name
        for field, target_field in (
            ("properties", "datatype_id"),
            ("components", "target_template_id"),
        ):
            items = primary.get(field)
            if not isinstance(items, list):
                return EnrichmentOutcome(None, _protocol_error())
            enriched: list[JsonValue] = []
            for item in items:
                if not isinstance(item, dict):
                    return EnrichmentOutcome(None, _protocol_error())
                member = cast(dict[str, JsonValue], item)
                declaring_id = _string(member.get("declaring_template_id"))
                target_id = _string(member.get(target_field))
                if declaring_id is None or target_id is None:
                    return EnrichmentOutcome(None, _protocol_error())
                declaring_name, error = await _template_name(context, declaring_id)
                if error is not None or declaring_name is None:
                    return EnrichmentOutcome(None, error or _protocol_error())
                if field == "properties":
                    target_name, error = await _datatype_name(context, target_id)
                    label = "datatype_qualified_name"
                else:
                    target_name, error = await _template_name(context, target_id)
                    label = "target_template_qualified_name"
                if error is not None or target_name is None:
                    return EnrichmentOutcome(None, error or _protocol_error())
                enriched.append(
                    {
                        **member,
                        "declaring_template_qualified_name": declaring_name,
                        label: target_name,
                    }
                )
            presentation[field] = enriched

    elif key == ("object", "get"):
        template_id = _string(primary.get("template_id"))
        if template_id is None:
            return EnrichmentOutcome(None, _protocol_error())
        name, error = await _template_name(context, template_id)
        if error is not None or name is None:
            return EnrichmentOutcome(None, error or _protocol_error())
        presentation["template_qualified_name"] = name

    elif key == ("object", "get-owner"):
        parent_id = _string(primary.get("parent_object_id"))
        declaring_id = _string(primary.get("slot_declaring_template_id"))
        if parent_id is None or declaring_id is None:
            return EnrichmentOutcome(None, _protocol_error())
        parent, error = await context.object(parent_id)
        if error is not None or parent is None:
            return EnrichmentOutcome(None, error or _protocol_error())
        canonical_name = _string(parent.get("canonical_name"))
        declaring_name, error = await _template_name(context, declaring_id)
        if error is not None or declaring_name is None or canonical_name is None:
            return EnrichmentOutcome(None, error or _protocol_error())
        presentation["parent_canonical_name"] = canonical_name
        presentation["slot_declaring_template_qualified_name"] = declaring_name

    elif key == ("relationship-definition", "get"):
        resolutions = primary.get("resolutions")
        if not isinstance(resolutions, list):
            return EnrichmentOutcome(None, _protocol_error())
        enriched_resolutions: list[JsonValue] = []
        for item in resolutions:
            if not isinstance(item, dict):
                return EnrichmentOutcome(None, _protocol_error())
            resolution = cast(dict[str, JsonValue], item)
            from_id = _string(resolution.get("from_template_id"))
            to_id = _string(resolution.get("to_template_id"))
            if from_id is None or to_id is None:
                return EnrichmentOutcome(None, _protocol_error())
            from_name, error = await _template_name(context, from_id)
            if error is not None or from_name is None:
                return EnrichmentOutcome(None, error or _protocol_error())
            to_name, error = await _template_name(context, to_id)
            if error is not None or to_name is None:
                return EnrichmentOutcome(None, error or _protocol_error())
            enriched_resolutions.append(
                {
                    **resolution,
                    "from_template_qualified_name": from_name,
                    "to_template_qualified_name": to_name,
                }
            )
        presentation["resolutions"] = enriched_resolutions

    elif key == ("relationship-definition", "get-version"):
        properties = primary.get("properties")
        if not isinstance(properties, list):
            return EnrichmentOutcome(None, _protocol_error())
        enriched_properties = []
        for item in properties:
            if not isinstance(item, dict):
                return EnrichmentOutcome(None, _protocol_error())
            prop = cast(dict[str, JsonValue], item)
            datatype_id = _string(prop.get("datatype_id"))
            if datatype_id is None:
                return EnrichmentOutcome(None, _protocol_error())
            name, error = await _datatype_name(context, datatype_id)
            if error is not None or name is None:
                return EnrichmentOutcome(None, error or _protocol_error())
            enriched_properties.append({**prop, "datatype_qualified_name": name})
        presentation["properties"] = enriched_properties

    elif key == ("relationship", "get"):
        views = primary.get("views")
        if not isinstance(views, list):
            return EnrichmentOutcome(None, _protocol_error())
        enriched_views: list[JsonValue] = []
        for item in views:
            if not isinstance(item, dict):
                return EnrichmentOutcome(None, _protocol_error())
            view = cast(dict[str, JsonValue], item)
            object_id = _string(view.get("object_id"))
            destination_id = _string(view.get("destination_object_id"))
            if object_id is None or destination_id is None:
                return EnrichmentOutcome(None, _protocol_error())
            source, error = await context.object(object_id)
            if error is not None or source is None:
                return EnrichmentOutcome(None, error or _protocol_error())
            destination, error = await context.object(destination_id)
            if error is not None or destination is None:
                return EnrichmentOutcome(None, error or _protocol_error())
            source_name = _string(source.get("canonical_name"))
            destination_name = _string(destination.get("canonical_name"))
            if source_name is None or destination_name is None:
                return EnrichmentOutcome(None, _protocol_error())
            enriched_views.append(
                {
                    **view,
                    "object_canonical_name": source_name,
                    "destination_canonical_name": destination_name,
                }
            )
        presentation["views"] = enriched_views

    return EnrichmentOutcome(presentation, None)
