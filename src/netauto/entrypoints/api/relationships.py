"""Strict public HTTP adapter for factual Relationship capabilities."""

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Query, Request, Response, status

from netauto.application.cursors import Page
from netauto.application.relationships import (
    RelationshipProjection,
    RelationshipService,
)
from netauto.domain.objects import DataChangeKind, DataChangeOperation
from netauto.domain.relationships import ObjectRelationshipView, RelationshipView
from netauto.entrypoints.api.common import (
    NoBody,
    PageLimit,
    validate_query,
)
from netauto.persistence.engine import RuntimeContext
from netauto.transport.http.relationships import (
    ObjectRelationshipPageDto,
    ObjectRelationshipViewDto,
    RelationshipCreateBody,
    RelationshipDataChangeBody,
    RelationshipDto,
    RelationshipSchemaChangeBody,
    RelationshipSetOperationBody,
    RelationshipViewDto,
)

router = APIRouter(prefix="/api/v1/core", tags=["relationships"])


RelationshipNameQuery = Annotated[str, Query(pattern=r"^[a-z][a-z0-9_]{0,63}$")]


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
