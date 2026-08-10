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
    EffectiveRelationshipDefinitionResponse,
    RelationshipDefinitionResponse,
    RelationshipNavigationResponse,
    RelationshipResponse,
)
from netauto.application.relationship import (
    RelationshipApplicationService,
    RelationshipDefinitionApplicationService,
)
from netauto.core.relationship import (
    EffectiveRelationshipDefinition,
    Relationship,
    RelationshipDefinition,
    RelationshipNavigationView,
)

router = APIRouter()
relationship_definition_router = APIRouter(
    prefix="/relationship-definitions",
    tags=["relationship-definitions"],
)
relationship_router = APIRouter(prefix="/relationships", tags=["relationships"])
object_relationship_router = APIRouter(prefix="/objects", tags=["relationships"])


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


def _to_effective_relationship_definition_response(
    definition: EffectiveRelationshipDefinition,
) -> EffectiveRelationshipDefinitionResponse:
    return EffectiveRelationshipDefinitionResponse(
        relationship_definition_id=definition.relationship_definition_id,
        direction=definition.direction.value,
        name=definition.name,
        related_template_id=definition.related_template_id,
    )


def _to_relationship_navigation_response(
    view: RelationshipNavigationView,
) -> RelationshipNavigationResponse:
    return RelationshipNavigationResponse(
        relationship_id=view.relationship_id,
        relationship_definition_id=view.relationship_definition_id,
        source_object_id=view.source_object_id,
        target_object_id=view.target_object_id,
        direction=view.direction.value,
        name=view.name,
        related_object_id=view.related_object_id,
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


@object_relationship_router.get(
    "/{object_id}/relationship-definitions/effective",
    response_model=list[EffectiveRelationshipDefinitionResponse],
    responses=ERROR_RESPONSES,
)
def list_effective_relationship_definitions(
    object_id: UUID,
    service: Annotated[
        RelationshipApplicationService,
        Depends(get_relationship_service),
    ],
) -> list[EffectiveRelationshipDefinitionResponse]:
    return [
        _to_effective_relationship_definition_response(definition)
        for definition in service.list_effective_relationship_definitions(object_id)
    ]


@object_relationship_router.get(
    "/{object_id}/relationships/outgoing",
    response_model=list[RelationshipNavigationResponse],
    responses=ERROR_RESPONSES,
)
def list_outgoing_relationships(
    object_id: UUID,
    service: Annotated[
        RelationshipApplicationService,
        Depends(get_relationship_service),
    ],
) -> list[RelationshipNavigationResponse]:
    return [
        _to_relationship_navigation_response(view)
        for view in service.list_outgoing_relationships(object_id)
    ]


@object_relationship_router.get(
    "/{object_id}/relationships/incoming",
    response_model=list[RelationshipNavigationResponse],
    responses=ERROR_RESPONSES,
)
def list_incoming_relationships(
    object_id: UUID,
    service: Annotated[
        RelationshipApplicationService,
        Depends(get_relationship_service),
    ],
) -> list[RelationshipNavigationResponse]:
    return [
        _to_relationship_navigation_response(view)
        for view in service.list_incoming_relationships(object_id)
    ]


@object_relationship_router.get(
    "/{object_id}/relationships/neighbors",
    response_model=list[RelationshipNavigationResponse],
    responses=ERROR_RESPONSES,
)
def list_neighbor_relationships(
    object_id: UUID,
    service: Annotated[
        RelationshipApplicationService,
        Depends(get_relationship_service),
    ],
) -> list[RelationshipNavigationResponse]:
    return [
        _to_relationship_navigation_response(view)
        for view in service.list_neighbor_relationships(object_id)
    ]


router.include_router(relationship_definition_router)
router.include_router(relationship_router)
router.include_router(object_relationship_router)
