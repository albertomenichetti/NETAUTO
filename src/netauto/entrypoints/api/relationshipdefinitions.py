"""Strict HTTP adapter for the M1 RelationshipDefinition capability."""

from typing import Annotated, Literal, Self, cast
from uuid import UUID

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from netauto.application.cursors import Page
from netauto.application.relationshipdefinitions import RelationshipDefinitionService
from netauto.domain.relationships import (
    RelationshipDefinition,
    RelationshipPerspective,
    RelationshipResolution,
    ResolutionRename,
)
from netauto.entrypoints.api.common import NoBody, PageLimit, StrictBody, validate_query
from netauto.persistence.engine import RuntimeContext

router = APIRouter(prefix="/api/v1/core", tags=["relationship-definitions"])


def _uuid_carrier(value: object) -> UUID:
    if isinstance(value, UUID):
        return value
    if not isinstance(value, str):
        raise ValueError("uuid_required")
    return UUID(value)


BodyUUID = Annotated[UUID, BeforeValidator(_uuid_carrier)]


class PerspectiveBody(StrictBody):
    template_id: BodyUUID
    name: str


class NonSymmetricCreateBody(StrictBody):
    symmetric: Literal[False]
    perspectives: list[PerspectiveBody] = Field(min_length=2, max_length=2)

    @model_validator(mode="before")
    @classmethod
    def symmetric_is_strict_boolean(cls, value: object) -> object:
        if isinstance(value, dict):
            raw = cast(dict[object, object], value)
            if not isinstance(raw.get("symmetric"), bool):
                raise ValueError("boolean_required")
        return cast(object, value)


class SymmetricCreateBody(StrictBody):
    symmetric: Literal[True]
    endpoint_template_ids: list[BodyUUID] = Field(min_length=2, max_length=2)
    name: str

    @model_validator(mode="before")
    @classmethod
    def symmetric_is_strict_boolean(cls, value: object) -> object:
        if isinstance(value, dict):
            raw = cast(dict[object, object], value)
            if not isinstance(raw.get("symmetric"), bool):
                raise ValueError("boolean_required")
        return cast(object, value)


type RelationshipDefinitionCreateBody = Annotated[
    NonSymmetricCreateBody | SymmetricCreateBody, Field(discriminator="symmetric")
]


class ResolutionRenameBody(StrictBody):
    resolution_id: BodyUUID
    name: str


class NonSymmetricRenameBody(StrictBody):
    resolutions: list[ResolutionRenameBody] = Field(min_length=2, max_length=2)

    @model_validator(mode="after")
    def resolution_ids_are_unique(self) -> Self:
        if len({item.resolution_id for item in self.resolutions}) != 2:
            raise ValueError("duplicate_resolution_id")
        return self


class SymmetricRenameBody(StrictBody):
    name: str


type RelationshipDefinitionRenameBody = NonSymmetricRenameBody | SymmetricRenameBody


class RelationshipResolutionDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resolution_id: UUID
    name: str
    from_template_id: UUID
    to_template_id: UUID

    @classmethod
    def from_domain(cls, value: RelationshipResolution) -> Self:
        return cls(
            resolution_id=value.id,
            name=value.name,
            from_template_id=value.from_template_id,
            to_template_id=value.to_template_id,
        )


class RelationshipDefinitionDto(BaseModel):
    id: UUID
    symmetric: bool
    resolutions: list[RelationshipResolutionDto]


class RelationshipDefinitionPageDto(BaseModel):
    items: list[RelationshipDefinitionDto]
    next_cursor: str | None


def _service(request: Request) -> RelationshipDefinitionService:
    runtime = cast(RuntimeContext, request.app.state.runtime)
    return RelationshipDefinitionService(runtime.uow_factory)


def _definition(value: RelationshipDefinition) -> RelationshipDefinitionDto:
    return RelationshipDefinitionDto(
        id=value.id,
        symmetric=value.symmetric,
        resolutions=[
            RelationshipResolutionDto.from_domain(item)
            for item in sorted(value.resolutions, key=lambda item: item.id)
        ],
    )


def _page(
    value: Page[RelationshipDefinition],
) -> RelationshipDefinitionPageDto:
    return RelationshipDefinitionPageDto(
        items=[_definition(item) for item in value.items],
        next_cursor=value.next_cursor,
    )


@router.post(
    "/relationship-definitions",
    response_model=RelationshipDefinitionDto,
    status_code=status.HTTP_201_CREATED,
)
async def create_relationship_definition(
    body: RelationshipDefinitionCreateBody,
    request: Request,
    response: Response,
) -> RelationshipDefinitionDto:
    validate_query(request, ())
    service = _service(request)
    if isinstance(body, NonSymmetricCreateBody):
        first, second = body.perspectives
        created = await service.create_non_symmetric(
            (
                RelationshipPerspective(first.template_id, first.name),
                RelationshipPerspective(second.template_id, second.name),
            )
        )
    else:
        first, second = body.endpoint_template_ids
        created = await service.create_symmetric((first, second), body.name)
    response.headers["Location"] = f"/api/v1/core/relationship-definitions/{created.id}"
    return _definition(created)


@router.get("/relationship-definitions", response_model=RelationshipDefinitionPageDto)
async def list_relationship_definitions(
    request: Request,
    cursor: str | None = None,
    limit: PageLimit = 100,
) -> RelationshipDefinitionPageDto:
    validate_query(request, ("cursor", "limit"))
    return _page(await _service(request).list_definitions(cursor=cursor, limit=limit))


@router.get(
    "/relationship-definitions/{relationship_definition_id}",
    response_model=RelationshipDefinitionDto,
)
async def get_relationship_definition(
    relationship_definition_id: UUID, request: Request
) -> RelationshipDefinitionDto:
    validate_query(request, ())
    return _definition(await _service(request).get(relationship_definition_id))


@router.post(
    "/relationship-definitions/{relationship_definition_id}/rename",
    response_model=RelationshipDefinitionDto,
)
async def rename_relationship_definition(
    relationship_definition_id: UUID,
    body: RelationshipDefinitionRenameBody,
    request: Request,
) -> RelationshipDefinitionDto:
    validate_query(request, ())
    service = _service(request)
    if isinstance(body, NonSymmetricRenameBody):
        first, second = body.resolutions
        renamed = await service.rename_non_symmetric(
            relationship_definition_id,
            (
                ResolutionRename(first.resolution_id, first.name),
                ResolutionRename(second.resolution_id, second.name),
            ),
        )
    else:
        renamed = await service.rename_symmetric(relationship_definition_id, body.name)
    return _definition(renamed)


@router.delete(
    "/relationship-definitions/{relationship_definition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_relationship_definition(
    relationship_definition_id: UUID,
    request: Request,
    _: NoBody,
) -> None:
    validate_query(request, ())
    await _service(request).delete(relationship_definition_id)
