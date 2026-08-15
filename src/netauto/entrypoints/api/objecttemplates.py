"""Strict public HTTP adapter for the M1 ObjectTemplate capability."""

from typing import Annotated, Self, cast
from uuid import UUID

from fastapi import APIRouter, Query, Request, Response, status
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from netauto.application.cursors import Page
from netauto.application.objecttemplates import (
    MISSING,
    ComponentCandidate,
    ObjectTemplateService,
    PropertyCandidate,
)
from netauto.application.relationshipdefinitions import RelationshipDefinitionService
from netauto.domain.datatypes import VersionStatus
from netauto.domain.objecttemplates import (
    CreateObjectTemplateResult,
    EffectiveComponent,
    EffectiveProperty,
    EffectiveSchema,
    LocalComponent,
    LocalProperty,
    ObjectTemplate,
    ObjectTemplateVersion,
    ObjectTemplateVersionSummary,
    ValueMode,
)
from netauto.domain.primitives import JsonValue
from netauto.domain.relationships import RelationshipCapability
from netauto.entrypoints.api.common import (
    NoBody,
    PageLimit,
    PathPositiveInteger,
    PositiveInteger,
    QueryPositiveInteger,
    StrictBody,
    validate_query,
)
from netauto.persistence.engine import RuntimeContext

router = APIRouter(prefix="/api/v1/core", tags=["object-templates"])


def _strict_boolean(value: object) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    if isinstance(value, bool):
        return value
    raise ValueError("boolean_required")


QueryBoolean = Annotated[bool, BeforeValidator(_strict_boolean), Query()]


def _uuid_carrier(value: object) -> UUID:
    if isinstance(value, UUID):
        return value
    if not isinstance(value, str):
        raise ValueError("uuid_required")
    return UUID(value)


def _value_mode_carrier(value: object) -> ValueMode:
    if isinstance(value, ValueMode):
        return value
    if not isinstance(value, str):
        raise ValueError("value_mode_required")
    return ValueMode(value)


BodyUUID = Annotated[UUID, BeforeValidator(_uuid_carrier)]
BodyValueMode = Annotated[ValueMode, BeforeValidator(_value_mode_carrier)]


class PropertyBody(StrictBody):
    name: str
    position: PositiveInteger
    datatype_id: BodyUUID
    datatype_version: PositiveInteger | None = None
    value_mode: BodyValueMode
    required: bool
    migration_default: JsonValue | None = None

    @model_validator(mode="before")
    @classmethod
    def preserve_omission(cls, value: object) -> object:
        if isinstance(value, dict):
            raw = cast(dict[object, object], value)
            if "datatype_version" in raw and raw["datatype_version"] is None:
                raise ValueError("datatype_version_null_forbidden")
            required = raw.get("required")
            has_default = "migration_default" in raw
            if required is True and (
                not has_default or raw.get("migration_default") is None
            ):
                raise ValueError("required_migration_default")
            if required is False and has_default:
                raise ValueError("optional_default_must_be_absent")
            return raw
        return value


class ComponentBody(StrictBody):
    name: str
    position: PositiveInteger
    target_template_id: BodyUUID


class ObjectTemplateCreateBody(StrictBody):
    namespace: str
    name: str
    abstract: bool
    description: str | None = None
    parent_template_id: BodyUUID | None = None
    parent_version: PositiveInteger | None = None
    properties: list[PropertyBody] = Field(default_factory=lambda: list[PropertyBody]())
    components: list[ComponentBody] = Field(
        default_factory=lambda: list[ComponentBody]()
    )

    @model_validator(mode="before")
    @classmethod
    def parent_selector_shape(cls, value: object) -> object:
        if isinstance(value, dict):
            raw = cast(dict[object, object], value)
            if "parent_template_id" in raw and raw["parent_template_id"] is None:
                raise ValueError("parent_template_id_null_forbidden")
            if "parent_version" in raw and raw["parent_version"] is None:
                raise ValueError("parent_version_null_forbidden")
            if "parent_version" in raw and "parent_template_id" not in raw:
                raise ValueError("parent_template_id_required")
            return raw
        return value


class CreateNextBody(StrictBody):
    source_version: PositiveInteger


class ReviseBody(StrictBody):
    parent_version: PositiveInteger | None = None
    properties: list[PropertyBody]
    components: list[ComponentBody]

    @model_validator(mode="before")
    @classmethod
    def parent_version_not_null(cls, value: object) -> object:
        if isinstance(value, dict):
            raw = cast(dict[object, object], value)
            if "parent_version" in raw and raw["parent_version"] is None:
                raise ValueError("parent_version_null_forbidden")
            return raw
        return value


class SetDefaultBody(StrictBody):
    version: PositiveInteger


class SetDescriptionBody(StrictBody):
    description: str | None


class ObjectTemplateDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    namespace: str
    name: str
    description: str | None
    abstract: bool
    parent_template_id: UUID | None
    default_version: int | None


class PropertyDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    position: int
    datatype_id: UUID
    datatype_version: int
    value_mode: ValueMode
    required: bool
    migration_default: JsonValue | None = Field(
        default=None, exclude_if=lambda value: value is None
    )


class ComponentDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    position: int
    target_template_id: UUID


class ObjectTemplateVersionDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    template_id: UUID
    version: int
    revision: int
    status: VersionStatus
    parent_template_id: UUID | None
    parent_version: int | None
    properties: list[PropertyDto]
    components: list[ComponentDto]


class ObjectTemplateVersionSummaryDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    template_id: UUID
    version: int
    revision: int
    status: VersionStatus
    parent_template_id: UUID | None
    parent_version: int | None


class EffectivePropertyDto(PropertyDto):
    declaring_template_id: UUID

    @classmethod
    def from_domain(cls, value: EffectiveProperty) -> Self:
        declaration = value.declaration
        return cls(
            declaring_template_id=value.declaring_template_id,
            name=declaration.name,
            position=declaration.position,
            datatype_id=declaration.datatype_id,
            datatype_version=declaration.datatype_version,
            value_mode=declaration.value_mode,
            required=declaration.required,
            migration_default=declaration.migration_default,
        )


class EffectiveComponentDto(ComponentDto):
    declaring_template_id: UUID

    @classmethod
    def from_domain(cls, value: EffectiveComponent) -> Self:
        declaration = value.declaration
        return cls(
            declaring_template_id=value.declaring_template_id,
            name=declaration.name,
            position=declaration.position,
            target_template_id=declaration.target_template_id,
        )


class EffectiveSchemaDto(BaseModel):
    template_id: UUID
    version: int
    properties: list[EffectivePropertyDto]
    components: list[EffectiveComponentDto]


class ObjectTemplateCreateResultDto(BaseModel):
    object_template: ObjectTemplateDto
    version: ObjectTemplateVersionDto


class ObjectTemplatePageDto(BaseModel):
    items: list[ObjectTemplateDto]
    next_cursor: str | None


class ObjectTemplateVersionPageDto(BaseModel):
    items: list[ObjectTemplateVersionSummaryDto]
    next_cursor: str | None


class RelationshipCapabilityDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resolution_id: UUID
    relationship_definition_id: UUID
    name: str
    from_template_id: UUID
    to_template_id: UUID


class RelationshipCapabilityPageDto(BaseModel):
    items: list[RelationshipCapabilityDto]
    next_cursor: str | None


def _service(request: Request) -> ObjectTemplateService:
    runtime = cast(RuntimeContext, request.app.state.runtime)
    return ObjectTemplateService(runtime.uow_factory)


def _relationship_service(request: Request) -> RelationshipDefinitionService:
    runtime = cast(RuntimeContext, request.app.state.runtime)
    return RelationshipDefinitionService(runtime.uow_factory)


def _property_candidate(value: PropertyBody) -> PropertyCandidate:
    return PropertyCandidate(
        value.name,
        value.position,
        value.datatype_id,
        value.datatype_version,
        value.value_mode,
        value.required,
        value.migration_default if value.required else MISSING,
    )


def _component_candidate(value: ComponentBody) -> ComponentCandidate:
    return ComponentCandidate(value.name, value.position, value.target_template_id)


def _lineage(value: ObjectTemplate) -> ObjectTemplateDto:
    return ObjectTemplateDto.model_validate(value)


def _property(value: LocalProperty) -> PropertyDto:
    return PropertyDto.model_validate(value)


def _component(value: LocalComponent) -> ComponentDto:
    return ComponentDto.model_validate(value)


def _version(value: ObjectTemplateVersion) -> ObjectTemplateVersionDto:
    return ObjectTemplateVersionDto(
        template_id=value.template_id,
        version=value.version,
        revision=value.revision,
        status=value.status,
        parent_template_id=value.parent_template_id,
        parent_version=value.parent_version,
        properties=[_property(item) for item in value.properties],
        components=[_component(item) for item in value.components],
    )


def _summary(value: ObjectTemplateVersionSummary) -> ObjectTemplateVersionSummaryDto:
    return ObjectTemplateVersionSummaryDto.model_validate(value)


def _effective(value: EffectiveSchema) -> EffectiveSchemaDto:
    return EffectiveSchemaDto(
        template_id=value.template_id,
        version=value.version,
        properties=[
            EffectivePropertyDto.from_domain(item) for item in value.properties
        ],
        components=[
            EffectiveComponentDto.from_domain(item) for item in value.components
        ],
    )


def _created(value: CreateObjectTemplateResult) -> ObjectTemplateCreateResultDto:
    return ObjectTemplateCreateResultDto(
        object_template=_lineage(value.object_template), version=_version(value.version)
    )


def _lineage_page(value: Page[ObjectTemplate]) -> ObjectTemplatePageDto:
    return ObjectTemplatePageDto(
        items=[_lineage(item) for item in value.items], next_cursor=value.next_cursor
    )


def _version_page(
    value: Page[ObjectTemplateVersionSummary],
) -> ObjectTemplateVersionPageDto:
    return ObjectTemplateVersionPageDto(
        items=[_summary(item) for item in value.items], next_cursor=value.next_cursor
    )


def _capability(value: RelationshipCapability) -> RelationshipCapabilityDto:
    return RelationshipCapabilityDto.model_validate(value)


def _capability_page(
    value: Page[RelationshipCapability],
) -> RelationshipCapabilityPageDto:
    return RelationshipCapabilityPageDto(
        items=[_capability(item) for item in value.items],
        next_cursor=value.next_cursor,
    )


@router.post(
    "/object-templates",
    response_model=ObjectTemplateCreateResultDto,
    status_code=status.HTTP_201_CREATED,
)
async def create_object_template(
    body: ObjectTemplateCreateBody, request: Request, response: Response
) -> ObjectTemplateCreateResultDto:
    validate_query(request, ())
    created = await _service(request).create(
        body.namespace,
        body.name,
        body.abstract,
        body.description,
        body.parent_template_id,
        body.parent_version,
        tuple(_property_candidate(item) for item in body.properties),
        tuple(_component_candidate(item) for item in body.components),
    )
    response.headers["Location"] = (
        f"/api/v1/core/object-templates/{created.object_template.id}"
    )
    return _created(created)


@router.get("/object-templates", response_model=ObjectTemplatePageDto)
async def list_object_templates(
    request: Request,
    namespace: str | None = None,
    name: str | None = None,
    abstract: QueryBoolean | None = None,
    parent_template_id: UUID | None = None,
    cursor: str | None = None,
    limit: PageLimit = 100,
) -> ObjectTemplatePageDto:
    validate_query(
        request,
        ("namespace", "name", "abstract", "parent_template_id", "cursor", "limit"),
    )
    return _lineage_page(
        await _service(request).list_lineages(
            namespace=namespace,
            name=name,
            abstract=abstract,
            parent_template_id=parent_template_id,
            parent_filter_set="parent_template_id" in request.query_params,
            cursor=cursor,
            limit=limit,
        )
    )


@router.post(
    "/object-templates/{template_id}/create-next",
    response_model=ObjectTemplateVersionDto,
    status_code=status.HTTP_201_CREATED,
)
async def create_next_object_template_version(
    template_id: UUID,
    body: CreateNextBody,
    request: Request,
    response: Response,
) -> ObjectTemplateVersionDto:
    validate_query(request, ())
    created = await _service(request).create_next(template_id, body.source_version)
    response.headers["Location"] = (
        f"/api/v1/core/object-templates/{template_id}/versions/{created.version}"
    )
    return _version(created)


@router.get("/object-templates/{template_id}", response_model=ObjectTemplateDto)
async def get_object_template(template_id: UUID, request: Request) -> ObjectTemplateDto:
    validate_query(request, ())
    return _lineage(await _service(request).get_lineage(template_id))


@router.get(
    "/object-templates/{template_id}/relationship-capabilities",
    response_model=RelationshipCapabilityPageDto,
)
async def list_relationship_capabilities(
    template_id: UUID,
    request: Request,
    name: str | None = None,
    cursor: str | None = None,
    limit: PageLimit = 100,
) -> RelationshipCapabilityPageDto:
    validate_query(request, ("name", "cursor", "limit"))
    return _capability_page(
        await _relationship_service(request).list_capabilities(
            template_id, name=name, cursor=cursor, limit=limit
        )
    )


@router.delete(
    "/object-templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_object_template(
    template_id: UUID, request: Request, _: NoBody
) -> None:
    validate_query(request, ())
    await _service(request).delete_lineage(template_id)


@router.post(
    "/object-templates/{template_id}/set-default",
    response_model=ObjectTemplateDto,
)
async def set_object_template_default(
    template_id: UUID, body: SetDefaultBody, request: Request
) -> ObjectTemplateDto:
    validate_query(request, ())
    return _lineage(await _service(request).set_default(template_id, body.version))


@router.post(
    "/object-templates/{template_id}/clear-default",
    response_model=ObjectTemplateDto,
)
async def clear_object_template_default(
    template_id: UUID, request: Request, _: NoBody
) -> ObjectTemplateDto:
    validate_query(request, ())
    return _lineage(await _service(request).clear_default(template_id))


@router.post(
    "/object-templates/{template_id}/set-description",
    response_model=ObjectTemplateDto,
)
async def set_object_template_description(
    template_id: UUID, body: SetDescriptionBody, request: Request
) -> ObjectTemplateDto:
    validate_query(request, ())
    return _lineage(
        await _service(request).set_description(template_id, body.description)
    )


@router.get(
    "/object-templates/{template_id}/versions",
    response_model=ObjectTemplateVersionPageDto,
)
async def list_object_template_versions(
    template_id: UUID,
    request: Request,
    status_filter: Annotated[VersionStatus | None, Query(alias="status")] = None,
    cursor: str | None = None,
    limit: PageLimit = 100,
) -> ObjectTemplateVersionPageDto:
    validate_query(request, ("status", "cursor", "limit"))
    return _version_page(
        await _service(request).list_versions(
            template_id, status=status_filter, cursor=cursor, limit=limit
        )
    )


@router.get(
    "/object-templates/{template_id}/versions/{version}",
    response_model=ObjectTemplateVersionDto,
)
async def get_object_template_version(
    template_id: UUID, version: PathPositiveInteger, request: Request
) -> ObjectTemplateVersionDto:
    validate_query(request, ())
    return _version(await _service(request).get_version(template_id, version))


@router.get(
    "/object-templates/{template_id}/versions/{version}/effective-schema",
    response_model=EffectiveSchemaDto,
)
async def get_object_template_effective_schema(
    template_id: UUID, version: PathPositiveInteger, request: Request
) -> EffectiveSchemaDto:
    validate_query(request, ())
    return _effective(
        await _service(request).get_effective_schema(template_id, version)
    )


@router.post(
    "/object-templates/{template_id}/versions/{version}/revise",
    response_model=ObjectTemplateVersionDto,
)
async def revise_object_template_version(
    template_id: UUID,
    version: PathPositiveInteger,
    body: ReviseBody,
    request: Request,
    expected_revision: QueryPositiveInteger,
) -> ObjectTemplateVersionDto:
    validate_query(request, ("expected_revision",))
    return _version(
        await _service(request).revise(
            template_id,
            version,
            expected_revision,
            body.parent_version,
            tuple(_property_candidate(item) for item in body.properties),
            tuple(_component_candidate(item) for item in body.components),
        )
    )


@router.post(
    "/object-templates/{template_id}/versions/{version}/publish",
    response_model=ObjectTemplateVersionDto,
)
async def publish_object_template_version(
    template_id: UUID,
    version: PathPositiveInteger,
    request: Request,
    _: NoBody,
    expected_revision: QueryPositiveInteger,
) -> ObjectTemplateVersionDto:
    validate_query(request, ("expected_revision",))
    return _version(
        await _service(request).publish(template_id, version, expected_revision)
    )


@router.post(
    "/object-templates/{template_id}/versions/{version}/deprecate",
    response_model=ObjectTemplateVersionDto,
)
async def deprecate_object_template_version(
    template_id: UUID,
    version: PathPositiveInteger,
    request: Request,
    _: NoBody,
) -> ObjectTemplateVersionDto:
    validate_query(request, ())
    return _version(await _service(request).deprecate(template_id, version))


@router.delete(
    "/object-templates/{template_id}/versions/{version}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_object_template_draft(
    template_id: UUID,
    version: PathPositiveInteger,
    request: Request,
    _: NoBody,
    expected_revision: QueryPositiveInteger,
) -> None:
    validate_query(request, ("expected_revision",))
    await _service(request).delete_draft(template_id, version, expected_revision)
