"""Strict HTTP adapter for RelationshipDefinition and exact RDV capabilities."""

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Query, Request, Response, status

from netauto.application.cursors import Page
from netauto.application.relationshipdefinitions import RelationshipDefinitionService
from netauto.domain.datatypes import VersionStatus
from netauto.domain.relationships import (
    CreateRelationshipDefinitionResult,
    RelationshipDefinition,
    RelationshipDefinitionProperty,
    RelationshipDefinitionVersion,
    RelationshipDefinitionVersionSummary,
    RelationshipPerspective,
    RelationshipPropertyCandidate,
    ResolutionRename,
)
from netauto.entrypoints.api.common import (
    NoBody,
    PageLimit,
    PathPositiveInteger,
    QueryPositiveInteger,
    validate_query,
)
from netauto.persistence.engine import RuntimeContext
from netauto.transport.http.relationshipdefinitions import (
    CreateNextBody,
    CreateRelationshipDefinitionDto,
    NonSymmetricCreateBody,
    NonSymmetricRenameBody,
    RelationshipDefinitionCreateBody,
    RelationshipDefinitionDto,
    RelationshipDefinitionPageDto,
    RelationshipDefinitionPropertyDto,
    RelationshipDefinitionRenameBody,
    RelationshipDefinitionVersionDto,
    RelationshipDefinitionVersionPageDto,
    RelationshipDefinitionVersionSummaryDto,
    RelationshipPropertyBody,
    RelationshipResolutionDto,
    ReviseBody,
    SetDefaultBody,
)

router = APIRouter(prefix="/api/v1/core", tags=["relationship-definitions"])


def _service(request: Request) -> RelationshipDefinitionService:
    runtime = cast(RuntimeContext, request.app.state.runtime)
    return RelationshipDefinitionService(runtime.uow_factory)


def _definition(value: RelationshipDefinition) -> RelationshipDefinitionDto:
    return RelationshipDefinitionDto(
        id=value.id,
        symmetric=value.symmetric,
        default_version=value.default_version,
        resolutions=[
            RelationshipResolutionDto(
                resolution_id=item.id,
                name=item.name,
                from_template_id=item.from_template_id,
                to_template_id=item.to_template_id,
            )
            for item in sorted(value.resolutions, key=lambda item: item.id)
        ],
    )


def _property_candidate(
    value: RelationshipPropertyBody,
) -> RelationshipPropertyCandidate:
    return RelationshipPropertyCandidate(
        value.name,
        value.position,
        value.datatype_id,
        value.datatype_version,
        value.value_mode,
    )


def _version_property(
    value: RelationshipDefinitionProperty,
) -> RelationshipDefinitionPropertyDto:
    return RelationshipDefinitionPropertyDto.model_validate(value)


def _version(
    value: RelationshipDefinitionVersion,
) -> RelationshipDefinitionVersionDto:
    return RelationshipDefinitionVersionDto(
        relationship_definition_id=value.relationship_definition_id,
        version=value.version,
        revision=value.revision,
        status=value.status,
        properties=[_version_property(item) for item in value.properties],
    )


def _created(
    value: CreateRelationshipDefinitionResult,
) -> CreateRelationshipDefinitionDto:
    return CreateRelationshipDefinitionDto(
        relationship_definition=_definition(value.relationship_definition),
        version=_version(value.version),
    )


def _page(
    value: Page[RelationshipDefinition],
) -> RelationshipDefinitionPageDto:
    return RelationshipDefinitionPageDto(
        items=[_definition(item) for item in value.items],
        next_cursor=value.next_cursor,
    )


def _version_page(
    value: Page[RelationshipDefinitionVersionSummary],
) -> RelationshipDefinitionVersionPageDto:
    return RelationshipDefinitionVersionPageDto(
        items=[
            RelationshipDefinitionVersionSummaryDto.model_validate(item)
            for item in value.items
        ],
        next_cursor=value.next_cursor,
    )


@router.post(
    "/relationship-definitions",
    response_model=CreateRelationshipDefinitionDto,
    status_code=status.HTTP_201_CREATED,
)
async def create_relationship_definition(
    body: RelationshipDefinitionCreateBody,
    request: Request,
    response: Response,
) -> CreateRelationshipDefinitionDto:
    validate_query(request, ())
    service = _service(request)
    if isinstance(body, NonSymmetricCreateBody):
        first, second = body.perspectives
        created = await service.create_non_symmetric(
            (
                RelationshipPerspective(first.template_id, first.name),
                RelationshipPerspective(second.template_id, second.name),
            ),
            tuple(_property_candidate(item) for item in body.properties),
        )
    else:
        first, second = body.endpoint_template_ids
        created = await service.create_symmetric(
            (first, second),
            body.name,
            tuple(_property_candidate(item) for item in body.properties),
        )
    response.headers["Location"] = (
        f"/api/v1/core/relationship-definitions/{created.relationship_definition.id}"
    )
    return _created(created)


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


@router.post(
    "/relationship-definitions/{relationship_definition_id}/create-next",
    response_model=RelationshipDefinitionVersionDto,
    status_code=status.HTTP_201_CREATED,
)
async def create_next_relationship_definition_version(
    relationship_definition_id: UUID,
    body: CreateNextBody,
    request: Request,
    response: Response,
) -> RelationshipDefinitionVersionDto:
    validate_query(request, ())
    created = await _service(request).create_next(
        relationship_definition_id, body.source_version
    )
    response.headers["Location"] = (
        "/api/v1/core/relationship-definitions/"
        f"{relationship_definition_id}/versions/{created.version}"
    )
    return _version(created)


@router.post(
    "/relationship-definitions/{relationship_definition_id}/set-default",
    response_model=RelationshipDefinitionDto,
)
async def set_relationship_definition_default(
    relationship_definition_id: UUID,
    body: SetDefaultBody,
    request: Request,
) -> RelationshipDefinitionDto:
    validate_query(request, ())
    return _definition(
        await _service(request).set_default(relationship_definition_id, body.version)
    )


@router.post(
    "/relationship-definitions/{relationship_definition_id}/clear-default",
    response_model=RelationshipDefinitionDto,
)
async def clear_relationship_definition_default(
    relationship_definition_id: UUID, request: Request, _: NoBody
) -> RelationshipDefinitionDto:
    validate_query(request, ())
    return _definition(
        await _service(request).clear_default(relationship_definition_id)
    )


@router.get(
    "/relationship-definitions/{relationship_definition_id}/versions",
    response_model=RelationshipDefinitionVersionPageDto,
)
async def list_relationship_definition_versions(
    relationship_definition_id: UUID,
    request: Request,
    version_status: Annotated[VersionStatus | None, Query(alias="status")] = None,
    cursor: str | None = None,
    limit: PageLimit = 100,
) -> RelationshipDefinitionVersionPageDto:
    validate_query(request, ("status", "cursor", "limit"))
    return _version_page(
        await _service(request).list_versions(
            relationship_definition_id,
            status=version_status,
            cursor=cursor,
            limit=limit,
        )
    )


@router.get(
    "/relationship-definitions/{relationship_definition_id}/versions/{version}",
    response_model=RelationshipDefinitionVersionDto,
)
async def get_relationship_definition_version(
    relationship_definition_id: UUID,
    version: PathPositiveInteger,
    request: Request,
) -> RelationshipDefinitionVersionDto:
    validate_query(request, ())
    return _version(
        await _service(request).get_version(relationship_definition_id, version)
    )


@router.post(
    "/relationship-definitions/{relationship_definition_id}/versions/{version}/revise",
    response_model=RelationshipDefinitionVersionDto,
)
async def revise_relationship_definition_version(
    relationship_definition_id: UUID,
    version: PathPositiveInteger,
    body: ReviseBody,
    request: Request,
    expected_revision: QueryPositiveInteger,
) -> RelationshipDefinitionVersionDto:
    validate_query(request, ("expected_revision",))
    return _version(
        await _service(request).revise(
            relationship_definition_id,
            version,
            expected_revision,
            tuple(_property_candidate(item) for item in body.properties),
        )
    )


@router.post(
    "/relationship-definitions/{relationship_definition_id}/versions/{version}/publish",
    response_model=RelationshipDefinitionVersionDto,
)
async def publish_relationship_definition_version(
    relationship_definition_id: UUID,
    version: PathPositiveInteger,
    request: Request,
    _: NoBody,
    expected_revision: QueryPositiveInteger,
) -> RelationshipDefinitionVersionDto:
    validate_query(request, ("expected_revision",))
    return _version(
        await _service(request).publish(
            relationship_definition_id, version, expected_revision
        )
    )


@router.post(
    "/relationship-definitions/{relationship_definition_id}/versions/{version}/deprecate",
    response_model=RelationshipDefinitionVersionDto,
)
async def deprecate_relationship_definition_version(
    relationship_definition_id: UUID,
    version: PathPositiveInteger,
    request: Request,
    _: NoBody,
) -> RelationshipDefinitionVersionDto:
    validate_query(request, ())
    return _version(
        await _service(request).deprecate(relationship_definition_id, version)
    )


@router.delete(
    "/relationship-definitions/{relationship_definition_id}/versions/{version}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_relationship_definition_version(
    relationship_definition_id: UUID,
    version: PathPositiveInteger,
    request: Request,
    _: NoBody,
    expected_revision: QueryPositiveInteger,
) -> None:
    validate_query(request, ("expected_revision",))
    await _service(request).delete_draft(
        relationship_definition_id, version, expected_revision
    )


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
