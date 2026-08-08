"""Datatype REST routes."""

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Path, status

from netauto.api.dependencies import get_datatype_service
from netauto.api.errors import ERROR_RESPONSES
from netauto.api.schemas.datatypes import (
    ConstraintRequest,
    ConstraintResponse,
    ConstraintValue,
    CreateDataTypeRequest,
    CreateDataTypeResponse,
    CreateNextVersionRequest,
    DataTypeResponse,
    DataTypeVersionResponse,
    ReviseDataTypeVersionRequest,
)
from netauto.application.datatype import DataTypeApplicationService
from netauto.core.datatype import Constraint, DataType, DataTypeVersion

router = APIRouter(prefix="/datatypes", tags=["datatypes"])

PositiveVersion = Annotated[int, Path(ge=1)]


def _to_constraint(constraint: ConstraintRequest) -> Constraint:
    return Constraint(name=constraint.name, value=constraint.value)


def _to_constraint_response(constraint: Constraint) -> ConstraintResponse:
    value = constraint.value
    if isinstance(value, tuple):
        value = list(value)
    return ConstraintResponse(name=constraint.name, value=cast("ConstraintValue", value))


def _to_datatype_response(datatype: DataType) -> DataTypeResponse:
    return DataTypeResponse(
        id=datatype.id,
        namespace=datatype.namespace,
        name=datatype.name,
        qualified_name=datatype.qualified_name,
        description=datatype.description,
    )


def _to_version_response(version: DataTypeVersion) -> DataTypeVersionResponse:
    return DataTypeVersionResponse(
        datatype_id=version.datatype_id,
        version=version.version,
        status=version.status,
        base_type=version.base_type.name,
        constraints=[_to_constraint_response(constraint) for constraint in version.constraints],
    )


@router.post(
    "",
    response_model=CreateDataTypeResponse,
    status_code=status.HTTP_201_CREATED,
    responses=ERROR_RESPONSES,
)
def create_datatype(
    request: CreateDataTypeRequest,
    service: Annotated[DataTypeApplicationService, Depends(get_datatype_service)],
) -> CreateDataTypeResponse:
    datatype, version = service.create_datatype(
        namespace=request.namespace,
        name=request.name,
        description=request.description,
        base_type=request.base_type,
        constraints=tuple(_to_constraint(constraint) for constraint in request.constraints),
    )
    return CreateDataTypeResponse(
        datatype=_to_datatype_response(datatype),
        version=_to_version_response(version),
    )


@router.get("", response_model=list[DataTypeResponse], responses=ERROR_RESPONSES)
def list_datatypes(
    service: Annotated[DataTypeApplicationService, Depends(get_datatype_service)],
) -> list[DataTypeResponse]:
    return [_to_datatype_response(datatype) for datatype in service.list_datatypes()]


@router.get(
    "/by-name/{namespace}/{name}",
    response_model=DataTypeResponse,
    responses=ERROR_RESPONSES,
)
def get_datatype_by_name(
    namespace: str,
    name: str,
    service: Annotated[DataTypeApplicationService, Depends(get_datatype_service)],
) -> DataTypeResponse:
    return _to_datatype_response(service.get_datatype_by_name(namespace, name))


@router.get("/{datatype_id}", response_model=DataTypeResponse, responses=ERROR_RESPONSES)
def get_datatype(
    datatype_id: UUID,
    service: Annotated[DataTypeApplicationService, Depends(get_datatype_service)],
) -> DataTypeResponse:
    return _to_datatype_response(service.get_datatype(datatype_id))


@router.get(
    "/{datatype_id}/versions",
    response_model=list[DataTypeVersionResponse],
    responses=ERROR_RESPONSES,
)
def list_versions(
    datatype_id: UUID,
    service: Annotated[DataTypeApplicationService, Depends(get_datatype_service)],
) -> list[DataTypeVersionResponse]:
    return [_to_version_response(version) for version in service.list_versions(datatype_id)]


@router.get(
    "/{datatype_id}/versions/{version}",
    response_model=DataTypeVersionResponse,
    responses=ERROR_RESPONSES,
)
def get_version(
    datatype_id: UUID,
    version: PositiveVersion,
    service: Annotated[DataTypeApplicationService, Depends(get_datatype_service)],
) -> DataTypeVersionResponse:
    return _to_version_response(service.get_version(datatype_id, version))


@router.put(
    "/{datatype_id}/versions/{version}",
    response_model=DataTypeVersionResponse,
    responses=ERROR_RESPONSES,
)
def revise_version(
    datatype_id: UUID,
    version: PositiveVersion,
    request: ReviseDataTypeVersionRequest,
    service: Annotated[DataTypeApplicationService, Depends(get_datatype_service)],
) -> DataTypeVersionResponse:
    revised = service.revise_version(
        datatype_id=datatype_id,
        version=version,
        base_type=request.base_type,
        constraints=tuple(_to_constraint(constraint) for constraint in request.constraints),
    )
    return _to_version_response(revised)


@router.post(
    "/{datatype_id}/versions",
    response_model=DataTypeVersionResponse,
    status_code=status.HTTP_201_CREATED,
    responses=ERROR_RESPONSES,
)
def create_next_version(
    datatype_id: UUID,
    request: CreateNextVersionRequest,
    service: Annotated[DataTypeApplicationService, Depends(get_datatype_service)],
) -> DataTypeVersionResponse:
    version = service.create_next_version(
        datatype_id=datatype_id,
        source_version=request.source_version,
    )
    return _to_version_response(version)


@router.post(
    "/{datatype_id}/versions/{version}/publish",
    response_model=DataTypeVersionResponse,
    responses=ERROR_RESPONSES,
)
def publish_version(
    datatype_id: UUID,
    version: PositiveVersion,
    service: Annotated[DataTypeApplicationService, Depends(get_datatype_service)],
) -> DataTypeVersionResponse:
    return _to_version_response(service.publish_version(datatype_id=datatype_id, version=version))


@router.post(
    "/{datatype_id}/versions/{version}/deprecate",
    response_model=DataTypeVersionResponse,
    responses=ERROR_RESPONSES,
)
def deprecate_version(
    datatype_id: UUID,
    version: PositiveVersion,
    service: Annotated[DataTypeApplicationService, Depends(get_datatype_service)],
) -> DataTypeVersionResponse:
    return _to_version_response(
        service.deprecate_version(datatype_id=datatype_id, version=version)
    )
