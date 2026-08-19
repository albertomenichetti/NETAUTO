"""Immutable, static registry for all 63 business HTTP operations."""

from types import MappingProxyType
from typing import Final

from netauto.cli.model import (
    CommandKey,
    CommandSpec,
    NestedSelector,
    ParameterKind,
    ParameterLocation,
    ParameterSpec,
    SelectorKind,
)
from netauto.transport.http import datatypes as dt
from netauto.transport.http import objects as obj
from netauto.transport.http import objecttemplates as ot
from netauto.transport.http import relationshipdefinitions as rd
from netauto.transport.http import relationships as rel

P = ParameterLocation.PATH
Q = ParameterLocation.QUERY
B = ParameterLocation.BODY

VERSION_STATUSES: Final = frozenset({"DRAFT", "PUBLISHED", "DEPRECATED"})
PRIMITIVE_TYPES: Final = frozenset(
    {
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
)
EVENT_KINDS: Final = frozenset(
    {
        "CREATED",
        "RENAME",
        "DATA_CHANGE",
        "SCHEMA_CHANGE",
        "ATTACH_TO",
        "DETACH_FROM",
        "RELATIONSHIP_CREATED",
        "RELATIONSHIP_DATA_CHANGE",
        "RELATIONSHIP_SCHEMA_CHANGE",
        "RELATIONSHIP_DELETED",
        "DELETED",
    }
)

_EXAMPLE_UUID: Final = "11111111-1111-1111-1111-111111111111"
_SECOND_EXAMPLE_UUID: Final = "22222222-2222-2222-2222-222222222222"
_RESOURCE_LABELS: Final = {
    "datatype": "DataType",
    "object-template": "ObjectTemplate",
    "object": "Object",
    "relationship-definition": "RelationshipDefinition",
    "relationship": "factual Relationship",
    "lifecycle-event": "lifecycle event",
}
_DESCRIPTION_TEMPLATES: Final = {
    "create": "Create a new {label} from a complete caller-supplied candidate.",
    "create-next": "Create the next draft {label} version from one exact source.",
    "revise": "Replace one exact draft {label} candidate at the expected revision.",
    "publish": "Publish one exact draft {label} version at the expected revision.",
    "set-default": "Select one exact published {label} version as the default.",
    "clear-default": "Clear the current default version from the selected {label}.",
    "deprecate": "Deprecate one exact published {label} version.",
    "delete-draft": "Delete one exact draft {label} version at the expected revision.",
    "delete": "Delete the selected {label} through its exact public operation.",
    "set-description": "Replace the nullable description of the selected {label}.",
    "list": "List {label} resources with the supported filters and keyset cursor.",
    "get": "Read the canonical public projection of one selected {label}.",
    "list-versions": "List exact {label} versions in canonical version order.",
    "get-version": "Read one exact selected {label} version and its full projection.",
    "get-effective-schema": (
        "Read one exact ObjectTemplate effective-schema projection."
    ),
    "list-relationship-capabilities": (
        "List Relationship capabilities applicable to one ObjectTemplate lineage."
    ),
    "rename": "Rename the selected {label} using one complete accepted shape.",
    "data-change": "Apply one non-empty typed data-change set to the selected {label}.",
    "schema-change": "Move the selected {label} to one explicit exact target version.",
    "attach": (
        "Attach one child Object in a declared slot of the selected parent Object."
    ),
    "detach": (
        "Detach one child Object from a declared slot of the selected parent Object."
    ),
    "list-components": "List the direct component children of one selected Object.",
    "get-owner": "Read the nullable owner projection of one selected Object.",
    "list-relationships": (
        "List factual Relationship views involving one selected Object."
    ),
    "list-lifecycle-events": "List lifecycle events involving one selected Object.",
}


def _description(resource: str, operation: str) -> str:
    return _DESCRIPTION_TEMPLATES[operation].format(label=_RESOURCE_LABELS[resource])


def _example_selector(kind: SelectorKind) -> str:
    if kind is SelectorKind.DATATYPE:
        return "core.string"
    if kind is SelectorKind.OBJECT_TEMPLATE:
        return "infra.server"
    if kind is SelectorKind.OBJECT:
        return "server01"
    return _EXAMPLE_UUID


def _example_parameter(parameter: ParameterSpec) -> str:
    if parameter.selector_kind is not None:
        value = _example_selector(parameter.selector_kind)
    elif parameter.kind is ParameterKind.POSITIVE_INTEGER:
        value = "1"
    elif parameter.kind is ParameterKind.BOOLEAN:
        value = "true"
    elif parameter.kind is ParameterKind.ENUM:
        value = sorted(parameter.choices)[0]
    elif parameter.kind is ParameterKind.UUID:
        value = _EXAMPLE_UUID
    elif parameter.kind is ParameterKind.JSON_OBJECT:
        value = "{}"
    elif parameter.kind is ParameterKind.JSON_ARRAY:
        value = (
            '[{"op":"REMOVE","property":"comment"}]'
            if parameter.name == "operations"
            else "[]"
        )
    elif parameter.kind is ParameterKind.JSON_VALUE:
        value = '"example"'
    elif parameter.kind is ParameterKind.DATETIME:
        value = "2026-08-19T00:00:00Z"
    else:
        value = {
            "namespace": "example",
            "name": "sample",
            "canonical_name": "server01",
            "slot_name": "member",
        }.get(parameter.name, "example")
    return f"{parameter.name}={value}"


def _examples(
    resource: str,
    operation: str,
    selector: SelectorKind | None,
    parameters: tuple[ParameterSpec, ...],
) -> tuple[tuple[str, ...], ...]:
    prefix = [resource, operation]
    if selector is not None:
        prefix.append(_example_selector(selector))
    if resource == "relationship-definition" and operation == "create":
        return (
            (
                *prefix,
                "symmetric=false",
                (
                    'perspectives=[{"template_id":"infra.server","name":"hosts"},'
                    '{"template_id":"infra.rack","name":"hosted_by"}]'
                ),
            ),
            (
                *prefix,
                "symmetric=true",
                'endpoint_template_ids=["infra.server","infra.peer"]',
                "name=peers",
            ),
        )
    if resource == "relationship-definition" and operation == "rename":
        return (
            (
                *prefix,
                (
                    'resolutions=[{"resolution_id":"'
                    f"{_EXAMPLE_UUID}"
                    '","name":"hosts"},{"resolution_id":"'
                    f"{_SECOND_EXAMPLE_UUID}"
                    '","name":"hosted_by"}]'
                ),
            ),
            (*prefix, "name=peers"),
        )
    required = tuple(
        _example_parameter(parameter) for parameter in parameters if parameter.required
    )
    return ((*prefix, *required),)


def _renderer_key(resource: str, operation: str, status: int) -> str:
    if status == 204:
        return "no-content"
    special = {
        "get-effective-schema": "object-template.effective-schema",
        "list-relationship-capabilities": "object-template.capability-page",
        "list-components": "object.component-page",
        "get-owner": "object.owner",
        "list-relationships": "object.relationship-page",
        "list-lifecycle-events": "lifecycle-event.page",
    }
    if operation in special:
        return special[operation]
    if operation == "list":
        return f"{resource}.page"
    if operation == "list-versions":
        return f"{resource}.version-page"
    if operation in {"get-version", "create-next", "revise", "publish", "deprecate"}:
        return f"{resource}.version"
    if operation == "create":
        return f"{resource}.created"
    return f"{resource}.resource"


def _p(
    name: str,
    kind: ParameterKind,
    location: ParameterLocation,
    *,
    required: bool = False,
    nullable: bool = False,
    choices: frozenset[str] = frozenset(),
    selector: SelectorKind | None = None,
    nested: tuple[NestedSelector, ...] = (),
) -> ParameterSpec:
    return ParameterSpec(
        name,
        kind,
        location,
        required,
        nullable,
        choices,
        selector,
        nested,
    )


def _s(
    resource: str,
    operation: str,
    method: str,
    path: str,
    response: object | None,
    *,
    selector: SelectorKind | None = None,
    selector_parameter: str | None = None,
    parameters: tuple[ParameterSpec, ...] = (),
    status: int = 200,
    request: object | None = None,
    location: str | None = None,
) -> CommandSpec:
    examples = _examples(resource, operation, selector, parameters)
    return CommandSpec(
        CommandKey(resource, operation),
        method,
        path,
        selector,
        selector_parameter,
        parameters,
        status,
        response,
        request,
        location,
        _description(resource, operation),
        examples,
        _renderer_key(resource, operation, status),
    )


S = SelectorKind
K = ParameterKind
N = NestedSelector

_SPECS = (
    # DataType (14)
    _s(
        "datatype",
        "create",
        "POST",
        "/api/v1/core/datatypes",
        dt.DataTypeCreateResultDto,
        parameters=(
            _p("namespace", K.STRING, B, required=True),
            _p("name", K.STRING, B, required=True),
            _p("base_type", K.ENUM, B, required=True, choices=PRIMITIVE_TYPES),
            _p("description", K.NULLABLE_STRING, B, nullable=True),
            _p("constraints", K.JSON_OBJECT, B),
        ),
        status=201,
        request=dt.DataTypeCreateBody,
        location="/api/v1/core/datatypes/{datatype.id}",
    ),
    _s(
        "datatype",
        "create-next",
        "POST",
        "/api/v1/core/datatypes/{datatype_id}/create-next",
        dt.DataTypeVersionDto,
        selector=S.DATATYPE,
        selector_parameter="datatype_id",
        parameters=(_p("source_version", K.POSITIVE_INTEGER, B, required=True),),
        status=201,
        request=dt.CreateNextBody,
        location=("/api/v1/core/datatypes/{datatype_id}/versions/{version}"),
    ),
    _s(
        "datatype",
        "revise",
        "POST",
        "/api/v1/core/datatypes/{datatype_id}/versions/{version}/revise",
        dt.DataTypeVersionDto,
        selector=S.DATATYPE,
        selector_parameter="datatype_id",
        parameters=(
            _p("version", K.POSITIVE_INTEGER, P, required=True),
            _p("expected_revision", K.POSITIVE_INTEGER, Q, required=True),
            _p("constraints", K.JSON_OBJECT, B, required=True),
        ),
        request=dt.ReviseBody,
    ),
    _s(
        "datatype",
        "publish",
        "POST",
        "/api/v1/core/datatypes/{datatype_id}/versions/{version}/publish",
        dt.DataTypeVersionDto,
        selector=S.DATATYPE,
        selector_parameter="datatype_id",
        parameters=(
            _p("version", K.POSITIVE_INTEGER, P, required=True),
            _p("expected_revision", K.POSITIVE_INTEGER, Q, required=True),
        ),
    ),
    _s(
        "datatype",
        "set-default",
        "POST",
        "/api/v1/core/datatypes/{datatype_id}/set-default",
        dt.DataTypeDto,
        selector=S.DATATYPE,
        selector_parameter="datatype_id",
        parameters=(_p("version", K.POSITIVE_INTEGER, B, required=True),),
        request=dt.SetDefaultBody,
    ),
    _s(
        "datatype",
        "clear-default",
        "POST",
        "/api/v1/core/datatypes/{datatype_id}/clear-default",
        dt.DataTypeDto,
        selector=S.DATATYPE,
        selector_parameter="datatype_id",
    ),
    _s(
        "datatype",
        "deprecate",
        "POST",
        "/api/v1/core/datatypes/{datatype_id}/versions/{version}/deprecate",
        dt.DataTypeVersionDto,
        selector=S.DATATYPE,
        selector_parameter="datatype_id",
        parameters=(_p("version", K.POSITIVE_INTEGER, P, required=True),),
    ),
    _s(
        "datatype",
        "delete-draft",
        "DELETE",
        "/api/v1/core/datatypes/{datatype_id}/versions/{version}",
        None,
        selector=S.DATATYPE,
        selector_parameter="datatype_id",
        parameters=(
            _p("version", K.POSITIVE_INTEGER, P, required=True),
            _p("expected_revision", K.POSITIVE_INTEGER, Q, required=True),
        ),
        status=204,
    ),
    _s(
        "datatype",
        "delete",
        "DELETE",
        "/api/v1/core/datatypes/{datatype_id}",
        None,
        selector=S.DATATYPE,
        selector_parameter="datatype_id",
        status=204,
    ),
    _s(
        "datatype",
        "set-description",
        "POST",
        "/api/v1/core/datatypes/{datatype_id}/set-description",
        dt.DataTypeDto,
        selector=S.DATATYPE,
        selector_parameter="datatype_id",
        parameters=(
            _p(
                "description",
                K.NULLABLE_STRING,
                B,
                required=True,
                nullable=True,
            ),
        ),
        request=dt.SetDescriptionBody,
    ),
    _s(
        "datatype",
        "list",
        "GET",
        "/api/v1/core/datatypes",
        dt.DataTypePageDto,
        parameters=(
            _p("namespace", K.STRING, Q),
            _p("name", K.STRING, Q),
            _p("cursor", K.STRING, Q),
            _p("limit", K.POSITIVE_INTEGER, Q),
        ),
    ),
    _s(
        "datatype",
        "get",
        "GET",
        "/api/v1/core/datatypes/{datatype_id}",
        dt.DataTypeDto,
        selector=S.DATATYPE,
        selector_parameter="datatype_id",
    ),
    _s(
        "datatype",
        "list-versions",
        "GET",
        "/api/v1/core/datatypes/{datatype_id}/versions",
        dt.DataTypeVersionPageDto,
        selector=S.DATATYPE,
        selector_parameter="datatype_id",
        parameters=(
            _p("status", K.ENUM, Q, choices=VERSION_STATUSES),
            _p("cursor", K.STRING, Q),
            _p("limit", K.POSITIVE_INTEGER, Q),
        ),
    ),
    _s(
        "datatype",
        "get-version",
        "GET",
        "/api/v1/core/datatypes/{datatype_id}/versions/{version}",
        dt.DataTypeVersionDto,
        selector=S.DATATYPE,
        selector_parameter="datatype_id",
        parameters=(_p("version", K.POSITIVE_INTEGER, P, required=True),),
    ),
    # ObjectTemplate (16)
    _s(
        "object-template",
        "create",
        "POST",
        "/api/v1/core/object-templates",
        ot.ObjectTemplateCreateResultDto,
        parameters=(
            _p("namespace", K.STRING, B, required=True),
            _p("name", K.STRING, B, required=True),
            _p("abstract", K.BOOLEAN, B, required=True),
            _p("description", K.NULLABLE_STRING, B, nullable=True),
            _p("parent_template_id", K.STRING, B, selector=S.OBJECT_TEMPLATE),
            _p("parent_version", K.POSITIVE_INTEGER, B),
            _p(
                "properties",
                K.JSON_ARRAY,
                B,
                nested=(N(("*", "datatype_id"), S.DATATYPE),),
            ),
            _p(
                "components",
                K.JSON_ARRAY,
                B,
                nested=(N(("*", "target_template_id"), S.OBJECT_TEMPLATE),),
            ),
        ),
        status=201,
        request=ot.ObjectTemplateCreateBody,
        location="/api/v1/core/object-templates/{object_template.id}",
    ),
    _s(
        "object-template",
        "create-next",
        "POST",
        "/api/v1/core/object-templates/{template_id}/create-next",
        ot.ObjectTemplateVersionDto,
        selector=S.OBJECT_TEMPLATE,
        selector_parameter="template_id",
        parameters=(_p("source_version", K.POSITIVE_INTEGER, B, required=True),),
        status=201,
        request=ot.CreateNextBody,
        location=("/api/v1/core/object-templates/{template_id}/versions/{version}"),
    ),
    _s(
        "object-template",
        "revise",
        "POST",
        "/api/v1/core/object-templates/{template_id}/versions/{version}/revise",
        ot.ObjectTemplateVersionDto,
        selector=S.OBJECT_TEMPLATE,
        selector_parameter="template_id",
        parameters=(
            _p("version", K.POSITIVE_INTEGER, P, required=True),
            _p("expected_revision", K.POSITIVE_INTEGER, Q, required=True),
            _p("parent_version", K.POSITIVE_INTEGER, B),
            _p(
                "properties",
                K.JSON_ARRAY,
                B,
                required=True,
                nested=(N(("*", "datatype_id"), S.DATATYPE),),
            ),
            _p(
                "components",
                K.JSON_ARRAY,
                B,
                required=True,
                nested=(N(("*", "target_template_id"), S.OBJECT_TEMPLATE),),
            ),
        ),
        request=ot.ReviseBody,
    ),
    _s(
        "object-template",
        "publish",
        "POST",
        "/api/v1/core/object-templates/{template_id}/versions/{version}/publish",
        ot.ObjectTemplateVersionDto,
        selector=S.OBJECT_TEMPLATE,
        selector_parameter="template_id",
        parameters=(
            _p("version", K.POSITIVE_INTEGER, P, required=True),
            _p("expected_revision", K.POSITIVE_INTEGER, Q, required=True),
        ),
    ),
    _s(
        "object-template",
        "set-default",
        "POST",
        "/api/v1/core/object-templates/{template_id}/set-default",
        ot.ObjectTemplateDto,
        selector=S.OBJECT_TEMPLATE,
        selector_parameter="template_id",
        parameters=(_p("version", K.POSITIVE_INTEGER, B, required=True),),
        request=ot.SetDefaultBody,
    ),
    _s(
        "object-template",
        "clear-default",
        "POST",
        "/api/v1/core/object-templates/{template_id}/clear-default",
        ot.ObjectTemplateDto,
        selector=S.OBJECT_TEMPLATE,
        selector_parameter="template_id",
    ),
    _s(
        "object-template",
        "deprecate",
        "POST",
        "/api/v1/core/object-templates/{template_id}/versions/{version}/deprecate",
        ot.ObjectTemplateVersionDto,
        selector=S.OBJECT_TEMPLATE,
        selector_parameter="template_id",
        parameters=(_p("version", K.POSITIVE_INTEGER, P, required=True),),
    ),
    _s(
        "object-template",
        "delete-draft",
        "DELETE",
        "/api/v1/core/object-templates/{template_id}/versions/{version}",
        None,
        selector=S.OBJECT_TEMPLATE,
        selector_parameter="template_id",
        parameters=(
            _p("version", K.POSITIVE_INTEGER, P, required=True),
            _p("expected_revision", K.POSITIVE_INTEGER, Q, required=True),
        ),
        status=204,
    ),
    _s(
        "object-template",
        "delete",
        "DELETE",
        "/api/v1/core/object-templates/{template_id}",
        None,
        selector=S.OBJECT_TEMPLATE,
        selector_parameter="template_id",
        status=204,
    ),
    _s(
        "object-template",
        "set-description",
        "POST",
        "/api/v1/core/object-templates/{template_id}/set-description",
        ot.ObjectTemplateDto,
        selector=S.OBJECT_TEMPLATE,
        selector_parameter="template_id",
        parameters=(
            _p(
                "description",
                K.NULLABLE_STRING,
                B,
                required=True,
                nullable=True,
            ),
        ),
        request=ot.SetDescriptionBody,
    ),
    _s(
        "object-template",
        "list",
        "GET",
        "/api/v1/core/object-templates",
        ot.ObjectTemplatePageDto,
        parameters=(
            _p("namespace", K.STRING, Q),
            _p("name", K.STRING, Q),
            _p("abstract", K.BOOLEAN, Q),
            _p("parent_template_id", K.STRING, Q, selector=S.OBJECT_TEMPLATE),
            _p("cursor", K.STRING, Q),
            _p("limit", K.POSITIVE_INTEGER, Q),
        ),
    ),
    _s(
        "object-template",
        "get",
        "GET",
        "/api/v1/core/object-templates/{template_id}",
        ot.ObjectTemplateDto,
        selector=S.OBJECT_TEMPLATE,
        selector_parameter="template_id",
    ),
    _s(
        "object-template",
        "list-versions",
        "GET",
        "/api/v1/core/object-templates/{template_id}/versions",
        ot.ObjectTemplateVersionPageDto,
        selector=S.OBJECT_TEMPLATE,
        selector_parameter="template_id",
        parameters=(
            _p("status", K.ENUM, Q, choices=VERSION_STATUSES),
            _p("cursor", K.STRING, Q),
            _p("limit", K.POSITIVE_INTEGER, Q),
        ),
    ),
    _s(
        "object-template",
        "get-version",
        "GET",
        "/api/v1/core/object-templates/{template_id}/versions/{version}",
        ot.ObjectTemplateVersionDto,
        selector=S.OBJECT_TEMPLATE,
        selector_parameter="template_id",
        parameters=(_p("version", K.POSITIVE_INTEGER, P, required=True),),
    ),
    _s(
        "object-template",
        "get-effective-schema",
        "GET",
        "/api/v1/core/object-templates/{template_id}/versions/{version}/effective-schema",
        ot.EffectiveSchemaDto,
        selector=S.OBJECT_TEMPLATE,
        selector_parameter="template_id",
        parameters=(_p("version", K.POSITIVE_INTEGER, P, required=True),),
    ),
    _s(
        "object-template",
        "list-relationship-capabilities",
        "GET",
        "/api/v1/core/object-templates/{template_id}/relationship-capabilities",
        ot.RelationshipCapabilityPageDto,
        selector=S.OBJECT_TEMPLATE,
        selector_parameter="template_id",
        parameters=(
            _p("name", K.STRING, Q),
            _p("cursor", K.STRING, Q),
            _p("limit", K.POSITIVE_INTEGER, Q),
        ),
    ),
    # Object (13)
    _s(
        "object",
        "create",
        "POST",
        "/api/v1/core/objects",
        obj.ObjectDto,
        parameters=(
            _p(
                "template_id",
                K.STRING,
                B,
                required=True,
                selector=S.OBJECT_TEMPLATE,
            ),
            _p("template_version", K.POSITIVE_INTEGER, B),
            _p("canonical_name", K.STRING, B),
            _p("properties", K.JSON_OBJECT, B),
        ),
        status=201,
        request=obj.ObjectCreateBody,
        location="/api/v1/core/objects/{id}",
    ),
    _s(
        "object",
        "rename",
        "POST",
        "/api/v1/core/objects/{object_id}/rename",
        obj.ObjectDto,
        selector=S.OBJECT,
        selector_parameter="object_id",
        parameters=(_p("canonical_name", K.STRING, B, required=True),),
        request=obj.RenameBody,
    ),
    _s(
        "object",
        "data-change",
        "POST",
        "/api/v1/core/objects/{object_id}/data-change",
        obj.ObjectDto,
        selector=S.OBJECT,
        selector_parameter="object_id",
        parameters=(_p("operations", K.JSON_ARRAY, B, required=True),),
        request=obj.DataChangeBody,
    ),
    _s(
        "object",
        "schema-change",
        "POST",
        "/api/v1/core/objects/{object_id}/schema-change",
        obj.ObjectDto,
        selector=S.OBJECT,
        selector_parameter="object_id",
        parameters=(_p("target_version", K.POSITIVE_INTEGER, B, required=True),),
        request=obj.SchemaChangeBody,
    ),
    _s(
        "object",
        "attach",
        "POST",
        "/api/v1/core/objects/{parent_object_id}/attach",
        obj.ComponentProjectionDto,
        selector=S.OBJECT,
        selector_parameter="parent_object_id",
        parameters=(
            _p("slot_name", K.STRING, B, required=True),
            _p("child_object_id", K.STRING, B, required=True, selector=S.OBJECT),
        ),
        request=obj.OwnershipBody,
    ),
    _s(
        "object",
        "detach",
        "POST",
        "/api/v1/core/objects/{parent_object_id}/detach",
        None,
        selector=S.OBJECT,
        selector_parameter="parent_object_id",
        parameters=(
            _p("slot_name", K.STRING, B, required=True),
            _p("child_object_id", K.STRING, B, required=True, selector=S.OBJECT),
        ),
        status=204,
        request=obj.OwnershipBody,
    ),
    _s(
        "object",
        "delete",
        "DELETE",
        "/api/v1/core/objects/{object_id}",
        None,
        selector=S.OBJECT,
        selector_parameter="object_id",
        status=204,
    ),
    _s(
        "object",
        "list",
        "GET",
        "/api/v1/core/objects",
        obj.ObjectPageDto,
        parameters=(
            _p("template_id", K.STRING, Q, selector=S.OBJECT_TEMPLATE),
            _p("template_version", K.POSITIVE_INTEGER, Q),
            _p("canonical_name", K.STRING, Q),
            _p("cursor", K.STRING, Q),
            _p("limit", K.POSITIVE_INTEGER, Q),
        ),
    ),
    _s(
        "object",
        "get",
        "GET",
        "/api/v1/core/objects/{object_id}",
        obj.ObjectDto,
        selector=S.OBJECT,
        selector_parameter="object_id",
    ),
    _s(
        "object",
        "list-components",
        "GET",
        "/api/v1/core/objects/{parent_object_id}/components",
        obj.ComponentPageDto,
        selector=S.OBJECT,
        selector_parameter="parent_object_id",
        parameters=(
            _p("slot_name", K.STRING, Q),
            _p("cursor", K.STRING, Q),
            _p("limit", K.POSITIVE_INTEGER, Q),
        ),
    ),
    _s(
        "object",
        "get-owner",
        "GET",
        "/api/v1/core/objects/{child_object_id}/owner",
        obj.OwnerProjectionDto | None,
        selector=S.OBJECT,
        selector_parameter="child_object_id",
    ),
    _s(
        "object",
        "list-relationships",
        "GET",
        "/api/v1/core/objects/{object_id}/relationships",
        rel.ObjectRelationshipPageDto,
        selector=S.OBJECT,
        selector_parameter="object_id",
        parameters=(
            _p(
                "relationship_definition_id",
                K.UUID,
                Q,
                selector=S.RELATIONSHIP_DEFINITION,
            ),
            _p("name", K.STRING, Q),
            _p("cursor", K.STRING, Q),
            _p("limit", K.POSITIVE_INTEGER, Q),
        ),
    ),
    _s(
        "object",
        "list-lifecycle-events",
        "GET",
        "/api/v1/core/objects/{object_id}/lifecycle-events",
        obj.LifecyclePageDto,
        selector=S.OBJECT,
        selector_parameter="object_id",
        parameters=(
            _p("kind", K.ENUM, Q, choices=EVENT_KINDS),
            _p("destination_object_id", K.STRING, Q, selector=S.OBJECT),
            _p("relationship_id", K.UUID, Q, selector=S.RELATIONSHIP),
            _p(
                "relationship_definition_id",
                K.UUID,
                Q,
                selector=S.RELATIONSHIP_DEFINITION,
            ),
            _p("relationship_name", K.STRING, Q),
            _p("occurred_from", K.DATETIME, Q),
            _p("occurred_to", K.DATETIME, Q),
            _p("cursor", K.STRING, Q),
            _p("limit", K.POSITIVE_INTEGER, Q),
        ),
    ),
    # RelationshipDefinition (14)
    _s(
        "relationship-definition",
        "create",
        "POST",
        "/api/v1/core/relationship-definitions",
        rd.CreateRelationshipDefinitionDto,
        parameters=(
            _p("symmetric", K.BOOLEAN, B, required=True),
            _p(
                "perspectives",
                K.JSON_ARRAY,
                B,
                nested=(N(("*", "template_id"), S.OBJECT_TEMPLATE),),
            ),
            _p(
                "endpoint_template_ids",
                K.JSON_ARRAY,
                B,
                nested=(N(("*",), S.OBJECT_TEMPLATE),),
            ),
            _p("name", K.STRING, B),
            _p(
                "properties",
                K.JSON_ARRAY,
                B,
                nested=(N(("*", "datatype_id"), S.DATATYPE),),
            ),
        ),
        status=201,
        request=rd.RelationshipDefinitionCreateBody,
        location=("/api/v1/core/relationship-definitions/{relationship_definition.id}"),
    ),
    _s(
        "relationship-definition",
        "rename",
        "POST",
        "/api/v1/core/relationship-definitions/{relationship_definition_id}/rename",
        rd.RelationshipDefinitionDto,
        selector=S.RELATIONSHIP_DEFINITION,
        selector_parameter="relationship_definition_id",
        parameters=(
            _p(
                "resolutions",
                K.JSON_ARRAY,
                B,
                nested=(N(("*", "resolution_id"), S.RESOLUTION),),
            ),
            _p("name", K.STRING, B),
        ),
        request=rd.RelationshipDefinitionRenameBody,
    ),
    _s(
        "relationship-definition",
        "create-next",
        "POST",
        "/api/v1/core/relationship-definitions/{relationship_definition_id}/create-next",
        rd.RelationshipDefinitionVersionDto,
        selector=S.RELATIONSHIP_DEFINITION,
        selector_parameter="relationship_definition_id",
        parameters=(_p("source_version", K.POSITIVE_INTEGER, B, required=True),),
        status=201,
        request=rd.CreateNextBody,
        location=(
            "/api/v1/core/relationship-definitions/"
            "{relationship_definition_id}/versions/{version}"
        ),
    ),
    _s(
        "relationship-definition",
        "set-default",
        "POST",
        "/api/v1/core/relationship-definitions/{relationship_definition_id}/set-default",
        rd.RelationshipDefinitionDto,
        selector=S.RELATIONSHIP_DEFINITION,
        selector_parameter="relationship_definition_id",
        parameters=(_p("version", K.POSITIVE_INTEGER, B, required=True),),
        request=rd.SetDefaultBody,
    ),
    _s(
        "relationship-definition",
        "clear-default",
        "POST",
        "/api/v1/core/relationship-definitions/{relationship_definition_id}/clear-default",
        rd.RelationshipDefinitionDto,
        selector=S.RELATIONSHIP_DEFINITION,
        selector_parameter="relationship_definition_id",
    ),
    _s(
        "relationship-definition",
        "revise",
        "POST",
        "/api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}/revise",
        rd.RelationshipDefinitionVersionDto,
        selector=S.RELATIONSHIP_DEFINITION,
        selector_parameter="relationship_definition_id",
        parameters=(
            _p("version", K.POSITIVE_INTEGER, P, required=True),
            _p("expected_revision", K.POSITIVE_INTEGER, Q, required=True),
            _p(
                "properties",
                K.JSON_ARRAY,
                B,
                required=True,
                nested=(N(("*", "datatype_id"), S.DATATYPE),),
            ),
        ),
        request=rd.ReviseBody,
    ),
    _s(
        "relationship-definition",
        "publish",
        "POST",
        "/api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}/publish",
        rd.RelationshipDefinitionVersionDto,
        selector=S.RELATIONSHIP_DEFINITION,
        selector_parameter="relationship_definition_id",
        parameters=(
            _p("version", K.POSITIVE_INTEGER, P, required=True),
            _p("expected_revision", K.POSITIVE_INTEGER, Q, required=True),
        ),
    ),
    _s(
        "relationship-definition",
        "deprecate",
        "POST",
        "/api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}/deprecate",
        rd.RelationshipDefinitionVersionDto,
        selector=S.RELATIONSHIP_DEFINITION,
        selector_parameter="relationship_definition_id",
        parameters=(_p("version", K.POSITIVE_INTEGER, P, required=True),),
    ),
    _s(
        "relationship-definition",
        "delete-draft",
        "DELETE",
        "/api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}",
        None,
        selector=S.RELATIONSHIP_DEFINITION,
        selector_parameter="relationship_definition_id",
        parameters=(
            _p("version", K.POSITIVE_INTEGER, P, required=True),
            _p("expected_revision", K.POSITIVE_INTEGER, Q, required=True),
        ),
        status=204,
    ),
    _s(
        "relationship-definition",
        "delete",
        "DELETE",
        "/api/v1/core/relationship-definitions/{relationship_definition_id}",
        None,
        selector=S.RELATIONSHIP_DEFINITION,
        selector_parameter="relationship_definition_id",
        status=204,
    ),
    _s(
        "relationship-definition",
        "list",
        "GET",
        "/api/v1/core/relationship-definitions",
        rd.RelationshipDefinitionPageDto,
        parameters=(
            _p("cursor", K.STRING, Q),
            _p("limit", K.POSITIVE_INTEGER, Q),
        ),
    ),
    _s(
        "relationship-definition",
        "get",
        "GET",
        "/api/v1/core/relationship-definitions/{relationship_definition_id}",
        rd.RelationshipDefinitionDto,
        selector=S.RELATIONSHIP_DEFINITION,
        selector_parameter="relationship_definition_id",
    ),
    _s(
        "relationship-definition",
        "list-versions",
        "GET",
        "/api/v1/core/relationship-definitions/{relationship_definition_id}/versions",
        rd.RelationshipDefinitionVersionPageDto,
        selector=S.RELATIONSHIP_DEFINITION,
        selector_parameter="relationship_definition_id",
        parameters=(
            _p("status", K.ENUM, Q, choices=VERSION_STATUSES),
            _p("cursor", K.STRING, Q),
            _p("limit", K.POSITIVE_INTEGER, Q),
        ),
    ),
    _s(
        "relationship-definition",
        "get-version",
        "GET",
        "/api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}",
        rd.RelationshipDefinitionVersionDto,
        selector=S.RELATIONSHIP_DEFINITION,
        selector_parameter="relationship_definition_id",
        parameters=(_p("version", K.POSITIVE_INTEGER, P, required=True),),
    ),
    # Factual Relationship (5)
    _s(
        "relationship",
        "create",
        "POST",
        "/api/v1/core/relationships",
        rel.RelationshipDto,
        parameters=(
            _p("resolution_id", K.UUID, B, required=True, selector=S.RESOLUTION),
            _p("from_object_id", K.STRING, B, required=True, selector=S.OBJECT),
            _p("to_object_id", K.STRING, B, required=True, selector=S.OBJECT),
            _p("relationship_definition_version", K.POSITIVE_INTEGER, B),
            _p("properties", K.JSON_OBJECT, B),
        ),
        status=201,
        request=rel.RelationshipCreateBody,
        location="/api/v1/core/relationships/{id}",
    ),
    _s(
        "relationship",
        "data-change",
        "POST",
        "/api/v1/core/relationships/{relationship_id}/data-change",
        rel.RelationshipDto,
        selector=S.RELATIONSHIP,
        selector_parameter="relationship_id",
        parameters=(_p("operations", K.JSON_ARRAY, B, required=True),),
        request=rel.RelationshipDataChangeBody,
    ),
    _s(
        "relationship",
        "schema-change",
        "POST",
        "/api/v1/core/relationships/{relationship_id}/schema-change",
        rel.RelationshipDto,
        selector=S.RELATIONSHIP,
        selector_parameter="relationship_id",
        parameters=(_p("target_version", K.POSITIVE_INTEGER, B, required=True),),
        request=rel.RelationshipSchemaChangeBody,
    ),
    _s(
        "relationship",
        "delete",
        "DELETE",
        "/api/v1/core/relationships/{relationship_id}",
        None,
        selector=S.RELATIONSHIP,
        selector_parameter="relationship_id",
        status=204,
    ),
    _s(
        "relationship",
        "get",
        "GET",
        "/api/v1/core/relationships/{relationship_id}",
        rel.RelationshipDto,
        selector=S.RELATIONSHIP,
        selector_parameter="relationship_id",
    ),
    # LifecycleEvent (1)
    _s(
        "lifecycle-event",
        "list",
        "GET",
        "/api/v1/core/lifecycle-events",
        obj.LifecyclePageDto,
        parameters=(
            _p("kind", K.ENUM, Q, choices=EVENT_KINDS),
            _p("object_id", K.STRING, Q, selector=S.OBJECT),
            _p("destination_object_id", K.STRING, Q, selector=S.OBJECT),
            _p("relationship_id", K.UUID, Q, selector=S.RELATIONSHIP),
            _p(
                "relationship_definition_id",
                K.UUID,
                Q,
                selector=S.RELATIONSHIP_DEFINITION,
            ),
            _p("relationship_name", K.STRING, Q),
            _p("occurred_from", K.DATETIME, Q),
            _p("occurred_to", K.DATETIME, Q),
            _p("cursor", K.STRING, Q),
            _p("limit", K.POSITIVE_INTEGER, Q),
        ),
    ),
)

if len(_SPECS) != 63 or len({spec.key for spec in _SPECS}) != 63:
    raise RuntimeError("the CLI registry must contain exactly 63 unique commands")

COMMAND_REGISTRY = MappingProxyType({spec.key: spec for spec in _SPECS})
BUSINESS_OPERATION_SET = frozenset((spec.method, spec.path_template) for spec in _SPECS)
