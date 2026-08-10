"""Relationship definition REST routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from netauto.api.dependencies import get_relationship_definition_service
from netauto.api.errors import ERROR_RESPONSES
from netauto.api.schemas.relationships import (
    CreateRelationshipDefinitionRequest,
    RelationshipDefinitionResponse,
)
from netauto.application.relationship import RelationshipDefinitionApplicationService
from netauto.core.relationship import RelationshipDefinition

router = APIRouter(prefix="/relationship-definitions", tags=["relationship-definitions"])


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


@router.get(
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


@router.get(
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


@router.post(
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


@router.delete(
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
) -> None:
    service.delete_relationship_definition(definition_id)
