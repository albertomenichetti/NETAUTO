"""Relationship definition and runtime relationship REST routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from netauto.api.dependencies import (
    get_relationship_definition_service,
    get_relationship_service,
)
from netauto.api.errors import ERROR_RESPONSES
from netauto.api.schemas.relationships import (
    CreateRelationshipDefinitionRequest,
    CreateRelationshipRequest,
    RelationshipDefinitionResponse,
    RelationshipResponse,
)
from netauto.application.relationship import (
    RelationshipApplicationService,
    RelationshipDefinitionApplicationService,
)
from netauto.core.relationship import Relationship, RelationshipDefinition

router = APIRouter()
relationship_definition_router = APIRouter(
    prefix="/relationship-definitions",
    tags=["relationship-definitions"],
)
relationship_router = APIRouter(prefix="/relationships", tags=["relationships"])


def _to_relationship_definition_response(
    definition: RelationshipDefinition,
) -> RelationshipDefinitionResponse:
    return RelationshipDefinitionResponse(
        id=definition.id,
        source_template_id=definition.source_template_id,
        target_template_id=definition.target_template_id,
        forward_name=definition.forward_name,
        reverse_name=definition.reverse_name,
    )


def _to_relationship_response(relationship: Relationship) -> RelationshipResponse:
    return RelationshipResponse(
        id=relationship.id,
        relationship_definition_id=relationship.relationship_definition_id,
        source_object_id=relationship.source_object_id,
        target_object_id=relationship.target_object_id,
    )


@relationship_definition_router.get(
    "",
    response_model=list[RelationshipDefinitionResponse],
    responses=ERROR_RESPONSES,
)
def list_relationship_definitions(
    service: Annotated[
        RelationshipDefinitionApplicationService,
        Depends(get_relationship_definition_service),
    ],
) -> list[RelationshipDefinitionResponse]:
    return [
        _to_relationship_definition_response(definition)
        for definition in service.list_relationship_definitions()
    ]


@relationship_definition_router.get(
    "/{definition_id}",
    response_model=RelationshipDefinitionResponse,
    responses=ERROR_RESPONSES,
)
def get_relationship_definition(
    definition_id: UUID,
    service: Annotated[
        RelationshipDefinitionApplicationService,
        Depends(get_relationship_definition_service),
    ],
) -> RelationshipDefinitionResponse:
    return _to_relationship_definition_response(
        service.get_relationship_definition(definition_id)
    )


@relationship_definition_router.post(
    "",
    response_model=RelationshipDefinitionResponse,
    status_code=status.HTTP_201_CREATED,
    responses=ERROR_RESPONSES,
)
def create_relationship_definition(
    request: CreateRelationshipDefinitionRequest,
    service: Annotated[
        RelationshipDefinitionApplicationService,
        Depends(get_relationship_definition_service),
    ],
) -> RelationshipDefinitionResponse:
    return _to_relationship_definition_response(
        service.create_relationship_definition(
            source_template_id=request.source_template_id,
            target_template_id=request.target_template_id,
            forward_name=request.forward_name,
            reverse_name=request.reverse_name,
        )
    )


@relationship_definition_router.delete(
    "/{definition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=ERROR_RESPONSES,
)
def delete_relationship_definition(
    definition_id: UUID,
    service: Annotated[
        RelationshipDefinitionApplicationService,
        Depends(get_relationship_definition_service),
    ],
) -> Response:
    service.delete_relationship_definition(definition_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@relationship_router.get(
    "",
    response_model=list[RelationshipResponse],
    responses=ERROR_RESPONSES,
)
def list_relationships(
    service: Annotated[
        RelationshipApplicationService,
        Depends(get_relationship_service),
    ],
) -> list[RelationshipResponse]:
    return [
        _to_relationship_response(relationship)
        for relationship in service.list_relationships()
    ]


@relationship_router.get(
    "/{relationship_id}",
    response_model=RelationshipResponse,
    responses=ERROR_RESPONSES,
)
def get_relationship(
    relationship_id: UUID,
    service: Annotated[
        RelationshipApplicationService,
        Depends(get_relationship_service),
    ],
) -> RelationshipResponse:
    return _to_relationship_response(service.get_relationship(relationship_id))


@relationship_router.post(
    "",
    response_model=RelationshipResponse,
    status_code=status.HTTP_201_CREATED,
    responses=ERROR_RESPONSES,
)
def create_relationship(
    request: CreateRelationshipRequest,
    service: Annotated[
        RelationshipApplicationService,
        Depends(get_relationship_service),
    ],
) -> RelationshipResponse:
    return _to_relationship_response(
        service.create_relationship(
            relationship_definition_id=request.relationship_definition_id,
            source_object_id=request.source_object_id,
            target_object_id=request.target_object_id,
        )
    )


@relationship_router.delete(
    "/{relationship_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=ERROR_RESPONSES,
)
def delete_relationship(
    relationship_id: UUID,
    service: Annotated[
        RelationshipApplicationService,
        Depends(get_relationship_service),
    ],
) -> Response:
    service.delete_relationship(relationship_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


router.include_router(relationship_definition_router)
router.include_router(relationship_router)
