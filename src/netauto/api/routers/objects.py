"""Object REST routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from netauto.api.dependencies import get_object_service
from netauto.api.errors import ERROR_RESPONSES
from netauto.api.schemas.objects import CreateObjectRequest, ObjectResponse, UpdateObjectRequest
from netauto.application.object import ObjectApplicationService
from netauto.core.object import Object

router = APIRouter(prefix="/objects", tags=["objects"])


def _to_object_response(object_value: Object) -> ObjectResponse:
    return ObjectResponse(
        id=object_value.id,
        template_id=object_value.template_id,
        template_version=object_value.template_version,
        properties=dict(object_value.properties),
    )


@router.post(
    "",
    response_model=ObjectResponse,
    status_code=status.HTTP_201_CREATED,
    responses=ERROR_RESPONSES,
)
def create_object(
    request: CreateObjectRequest,
    service: Annotated[ObjectApplicationService, Depends(get_object_service)],
) -> ObjectResponse:
    created = service.create_object(
        template_id=request.template_id,
        template_version=request.template_version,
        properties=request.properties,
    )
    return _to_object_response(created)


@router.get("", response_model=list[ObjectResponse], responses=ERROR_RESPONSES)
def list_objects(
    service: Annotated[ObjectApplicationService, Depends(get_object_service)],
) -> list[ObjectResponse]:
    return [_to_object_response(object_value) for object_value in service.list_objects()]


@router.get("/{object_id}", response_model=ObjectResponse, responses=ERROR_RESPONSES)
def get_object(
    object_id: UUID,
    service: Annotated[ObjectApplicationService, Depends(get_object_service)],
) -> ObjectResponse:
    return _to_object_response(service.get_object(object_id))


@router.patch("/{object_id}", response_model=ObjectResponse, responses=ERROR_RESPONSES)
def update_object(
    object_id: UUID,
    request: UpdateObjectRequest,
    service: Annotated[ObjectApplicationService, Depends(get_object_service)],
) -> ObjectResponse:
    updated = service.update_object(
        object_id=object_id,
        properties=request.properties,
        remove_properties=tuple(request.remove_properties),
    )
    return _to_object_response(updated)


@router.delete("/{object_id}", status_code=status.HTTP_204_NO_CONTENT, responses=ERROR_RESPONSES)
def delete_object(
    object_id: UUID,
    service: Annotated[ObjectApplicationService, Depends(get_object_service)],
) -> Response:
    service.delete_object(object_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
