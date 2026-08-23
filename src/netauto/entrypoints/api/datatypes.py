"""Strict public HTTP adapter for the M1 DataType capability."""

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Query, Request, Response, status

from netauto.application.cursors import Page
from netauto.application.datatypes import DataTypeService
from netauto.domain.datatypes import (
    CreateDataTypeResult,
    DataType,
    DataTypeVersion,
    DataTypeVersionSummary,
    VersionStatus,
)
from netauto.entrypoints.api.common import (
    NoBody,
    PageLimit,
    PathPositiveInteger,
    QueryPositiveInteger,
    validate_query,
)
from netauto.persistence.engine import RuntimeContext
from netauto.transport.http.datatypes import (
    CreateNextBody,
    DataTypeCreateBody,
    DataTypeCreateResultDto,
    DataTypeDto,
    DataTypePageDto,
    DataTypeVersionDto,
    DataTypeVersionPageDto,
    DataTypeVersionSummaryDto,
    ReviseBody,
    SetDefaultBody,
    SetDescriptionBody,
)

router = APIRouter(prefix="/api/v1/core", tags=["datatypes"])


def _service(request: Request) -> DataTypeService:
    runtime = cast(RuntimeContext, request.app.state.runtime)
    return DataTypeService(runtime.uow_factory)


def _lineage(value: DataType) -> DataTypeDto:
    return DataTypeDto.model_validate(value)


def _version(value: DataTypeVersion) -> DataTypeVersionDto:
    return DataTypeVersionDto.model_validate(value)


def _summary(value: DataTypeVersionSummary) -> DataTypeVersionSummaryDto:
    return DataTypeVersionSummaryDto.model_validate(value)


def _created(value: CreateDataTypeResult) -> DataTypeCreateResultDto:
    return DataTypeCreateResultDto(
        datatype=_lineage(value.datatype), version=_version(value.version)
    )


def _lineage_page(value: Page[DataType]) -> DataTypePageDto:
    return DataTypePageDto(
        items=[_lineage(item) for item in value.items],
        next_cursor=value.next_cursor,
    )


def _version_page(
    value: Page[DataTypeVersionSummary],
) -> DataTypeVersionPageDto:
    return DataTypeVersionPageDto(
        items=[_summary(item) for item in value.items],
        next_cursor=value.next_cursor,
    )


@router.post(
    "/datatypes",
    response_model=DataTypeCreateResultDto,
    status_code=status.HTTP_201_CREATED,
)
async def create_datatype(
    body: DataTypeCreateBody, request: Request, response: Response
) -> DataTypeCreateResultDto:
    validate_query(request, ())
    created = await _service(request).create(
        body.namespace,
        body.name,
        body.base_type,
        body.description,
        body.constraints,
    )
    response.headers["Location"] = f"/api/v1/core/datatypes/{created.datatype.id}"
    return _created(created)


@router.get("/datatypes", response_model=DataTypePageDto)
async def list_datatypes(
    request: Request,
    namespace: str | None = None,
    name: str | None = None,
    cursor: str | None = None,
    limit: PageLimit = 100,
) -> DataTypePageDto:
    validate_query(request, ("namespace", "name", "cursor", "limit"))
    page = await _service(request).list_lineages(
        namespace=namespace, name=name, cursor=cursor, limit=limit
    )
    return _lineage_page(page)


@router.post(
    "/datatypes/{datatype_id}/create-next",
    response_model=DataTypeVersionDto,
    status_code=status.HTTP_201_CREATED,
)
async def create_next_datatype_version(
    datatype_id: UUID,
    body: CreateNextBody,
    request: Request,
    response: Response,
) -> DataTypeVersionDto:
    validate_query(request, ())
    created = await _service(request).create_next(datatype_id, body.source_version)
    response.headers["Location"] = (
        f"/api/v1/core/datatypes/{datatype_id}/versions/{created.version}"
    )
    return _version(created)


@router.get("/datatypes/{datatype_id}", response_model=DataTypeDto)
async def get_datatype(datatype_id: UUID, request: Request) -> DataTypeDto:
    validate_query(request, ())
    return _lineage(await _service(request).get_lineage(datatype_id))


@router.delete("/datatypes/{datatype_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_datatype(datatype_id: UUID, request: Request, _: NoBody) -> None:
    validate_query(request, ())
    await _service(request).delete_lineage(datatype_id)


@router.post("/datatypes/{datatype_id}/set-default", response_model=DataTypeDto)
async def set_datatype_default(
    datatype_id: UUID, body: SetDefaultBody, request: Request
) -> DataTypeDto:
    validate_query(request, ())
    return _lineage(await _service(request).set_default(datatype_id, body.version))


@router.post("/datatypes/{datatype_id}/clear-default", response_model=DataTypeDto)
async def clear_datatype_default(
    datatype_id: UUID, request: Request, _: NoBody
) -> DataTypeDto:
    validate_query(request, ())
    return _lineage(await _service(request).clear_default(datatype_id))


@router.post("/datatypes/{datatype_id}/set-description", response_model=DataTypeDto)
async def set_datatype_description(
    datatype_id: UUID, body: SetDescriptionBody, request: Request
) -> DataTypeDto:
    validate_query(request, ())
    return _lineage(
        await _service(request).set_description(datatype_id, body.description)
    )


@router.get("/datatypes/{datatype_id}/versions", response_model=DataTypeVersionPageDto)
async def list_datatype_versions(
    datatype_id: UUID,
    request: Request,
    version_status: Annotated[VersionStatus | None, Query(alias="status")] = None,
    cursor: str | None = None,
    limit: PageLimit = 100,
) -> DataTypeVersionPageDto:
    validate_query(request, ("status", "cursor", "limit"))
    page = await _service(request).list_versions(
        datatype_id, status=version_status, cursor=cursor, limit=limit
    )
    return _version_page(page)


@router.get(
    "/datatypes/{datatype_id}/versions/{version}",
    response_model=DataTypeVersionDto,
)
async def get_datatype_version(
    datatype_id: UUID, version: PathPositiveInteger, request: Request
) -> DataTypeVersionDto:
    validate_query(request, ())
    return _version(await _service(request).get_version(datatype_id, version))


@router.post(
    "/datatypes/{datatype_id}/versions/{version}/revise",
    response_model=DataTypeVersionDto,
)
async def revise_datatype_version(
    datatype_id: UUID,
    version: PathPositiveInteger,
    body: ReviseBody,
    request: Request,
    expected_revision: QueryPositiveInteger,
) -> DataTypeVersionDto:
    validate_query(request, ("expected_revision",))
    revised = await _service(request).revise(
        datatype_id, version, expected_revision, body.constraints
    )
    return _version(revised)


@router.post(
    "/datatypes/{datatype_id}/versions/{version}/publish",
    response_model=DataTypeVersionDto,
)
async def publish_datatype_version(
    datatype_id: UUID,
    version: PathPositiveInteger,
    request: Request,
    expected_revision: QueryPositiveInteger,
    _: NoBody,
) -> DataTypeVersionDto:
    validate_query(request, ("expected_revision",))
    published = await _service(request).publish(datatype_id, version, expected_revision)
    return _version(published)


@router.post(
    "/datatypes/{datatype_id}/versions/{version}/deprecate",
    response_model=DataTypeVersionDto,
)
async def deprecate_datatype_version(
    datatype_id: UUID,
    version: PathPositiveInteger,
    request: Request,
    _: NoBody,
) -> DataTypeVersionDto:
    validate_query(request, ())
    return _version(await _service(request).deprecate(datatype_id, version))


@router.delete(
    "/datatypes/{datatype_id}/versions/{version}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_datatype_version(
    datatype_id: UUID,
    version: PathPositiveInteger,
    request: Request,
    expected_revision: QueryPositiveInteger,
    _: NoBody,
) -> None:
    validate_query(request, ("expected_revision",))
    await _service(request).delete_draft(datatype_id, version, expected_revision)
