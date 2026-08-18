"""Strict public HTTP adapter for factual Relationship capabilities."""

from typing import Annotated, Literal, cast
from uuid import UUID

from fastapi import APIRouter, Query, Request, Response, status
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from netauto.application.cursors import Page
from netauto.application.relationships import (
    RelationshipProjection,
    RelationshipService,
)
from netauto.domain.objects import DataChangeKind, DataChangeOperation
from netauto.domain.primitives import JsonValue
from netauto.domain.relationships import ObjectRelationshipView, RelationshipView
from netauto.entrypoints.api.common import (
    NoBody,
    PageLimit,
    PositiveInteger,
    StrictBody,
    validate_query,
)
from netauto.persistence.engine import RuntimeContext

router = APIRouter(prefix="/api/v1/core", tags=["relationships"])


def _uuid_carrier(value: object) -> UUID:
    if isinstance(value, UUID):
        return value
    if not isinstance(value, str):
        raise ValueError("uuid_required")
    return UUID(value)


BodyUUID = Annotated[UUID, BeforeValidator(_uuid_carrier)]
RelationshipNameQuery = Annotated[str, Query(pattern=r"^[a-z][a-z0-9_]{0,63}$")]


class RelationshipCreateBody(StrictBody):
    resolution_id: BodyUUID
    from_object_id: BodyUUID
    to_object_id: BodyUUID
    relationship_definition_version: PositiveInteger | None = None
    properties: dict[str, JsonValue] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def preserve_omission(cls, value: object) -> object:
        if isinstance(value, dict):
            raw = cast(dict[object, object], value)
            if (
                "relationship_definition_version" in raw
                and raw["relationship_definition_version"] is None
            ):
                raise ValueError("relationship_definition_version_null_forbidden")
            if "properties" in raw and raw["properties"] is None:
                raise ValueError("properties_null_forbidden")
            return cast(object, raw)
        return value


class RelationshipSetOperationBody(StrictBody):
    op: Literal["SET"]
    property: str = Field(pattern=r"^[a-z][a-z0-9_]{0,63}$")
    value: JsonValue


class RelationshipRemoveOperationBody(StrictBody):
    op: Literal["REMOVE"]
    property: str = Field(pattern=r"^[a-z][a-z0-9_]{0,63}$")


RelationshipDataChangeOperationBody = Annotated[
    RelationshipSetOperationBody | RelationshipRemoveOperationBody,
    Field(discriminator="op"),
]


class RelationshipDataChangeBody(StrictBody):
    operations: list[RelationshipDataChangeOperationBody] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_properties(self) -> RelationshipDataChangeBody:
        names = [operation.property for operation in self.operations]
        if len(names) != len(set(names)):
            raise ValueError("duplicate_relationship_property_operation")
        return self


class RelationshipSchemaChangeBody(StrictBody):
    target_version: PositiveInteger


class RelationshipViewDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    object_id: UUID
    destination_object_id: UUID
    name: str


class RelationshipDto(BaseModel):
    id: UUID
    relationship_definition_id: UUID
    relationship_definition_version: int
    properties: dict[str, JsonValue]
    views: list[RelationshipViewDto]


class ObjectRelationshipViewDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    relationship_id: UUID
    relationship_definition_id: UUID
    relationship_definition_version: int
    object_id: UUID
    destination_object_id: UUID
    name: str
    properties: dict[str, JsonValue]


class ObjectRelationshipPageDto(BaseModel):
    items: list[ObjectRelationshipViewDto]
    next_cursor: str | None


def _service(request: Request) -> RelationshipService:
    runtime = cast(RuntimeContext, request.app.state.runtime)
    return RelationshipService(runtime.uow_factory)


def _view(value: RelationshipView) -> RelationshipViewDto:
    return RelationshipViewDto.model_validate(value)


def _relationship(value: RelationshipProjection) -> RelationshipDto:
    return RelationshipDto(
        id=value.id,
        relationship_definition_id=value.relationship_definition_id,
        relationship_definition_version=value.relationship_definition_version,
        properties=value.properties,
        views=[_view(item) for item in value.views],
    )


def _object_view(value: ObjectRelationshipView) -> ObjectRelationshipViewDto:
    return ObjectRelationshipViewDto.model_validate(value)


def _page(value: Page[ObjectRelationshipView]) -> ObjectRelationshipPageDto:
    return ObjectRelationshipPageDto(
        items=[_object_view(item) for item in value.items],
        next_cursor=value.next_cursor,
    )


@router.post(
    "/relationships",
    response_model=RelationshipDto,
    status_code=status.HTTP_201_CREATED,
)
async def create_relationship(
    body: RelationshipCreateBody,
    request: Request,
    response: Response,
) -> RelationshipDto:
    validate_query(request, ())
    result = await _service(request).create(
        body.resolution_id,
        body.from_object_id,
        body.to_object_id,
        body.relationship_definition_version,
        body.properties,
    )
    response.headers["Location"] = (
        f"/api/v1/core/relationships/{result.relationship.id}"
    )
    return _relationship(result.relationship)


@router.get("/relationships/{relationship_id}", response_model=RelationshipDto)
async def get_relationship(relationship_id: UUID, request: Request) -> RelationshipDto:
    validate_query(request, ())
    return _relationship(await _service(request).get(relationship_id))


@router.post(
    "/relationships/{relationship_id}/data-change",
    response_model=RelationshipDto,
)
async def data_change_relationship(
    relationship_id: UUID,
    body: RelationshipDataChangeBody,
    request: Request,
) -> RelationshipDto:
    validate_query(request, ())
    operations = tuple(
        DataChangeOperation(
            DataChangeKind(operation.op),
            operation.property,
            operation.value
            if isinstance(operation, RelationshipSetOperationBody)
            else None,
        )
        for operation in body.operations
    )
    return _relationship(
        await _service(request).data_change(relationship_id, operations)
    )


@router.post(
    "/relationships/{relationship_id}/schema-change",
    response_model=RelationshipDto,
)
async def schema_change_relationship(
    relationship_id: UUID,
    body: RelationshipSchemaChangeBody,
    request: Request,
) -> RelationshipDto:
    validate_query(request, ())
    return _relationship(
        await _service(request).schema_change(relationship_id, body.target_version)
    )


@router.delete(
    "/relationships/{relationship_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_relationship(
    relationship_id: UUID, request: Request, _: NoBody
) -> None:
    validate_query(request, ())
    await _service(request).delete(relationship_id)


@router.get(
    "/objects/{object_id}/relationships",
    response_model=ObjectRelationshipPageDto,
)
async def list_object_relationships(
    object_id: UUID,
    request: Request,
    relationship_definition_id: UUID | None = None,
    name: RelationshipNameQuery | None = None,
    cursor: str | None = None,
    limit: PageLimit = 100,
) -> ObjectRelationshipPageDto:
    validate_query(
        request,
        ("relationship_definition_id", "name", "cursor", "limit"),
    )
    return _page(
        await _service(request).list_for_object(
            object_id,
            relationship_definition_id=relationship_definition_id,
            name=name,
            cursor=cursor,
            limit=limit,
        )
    )
