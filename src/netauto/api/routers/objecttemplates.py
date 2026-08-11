"""Object template REST routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, status

from netauto.api.dependencies import get_object_service, get_object_template_service
from netauto.api.errors import ERROR_RESPONSES
from netauto.api.schemas.objecttemplates import (
    CreateNextObjectTemplateVersionRequest,
    CreateObjectTemplateRequest,
    CreateObjectTemplateResponse,
    MigrateObjectsRequest,
    MigrateObjectsResponse,
    ObjectTemplateComponentRequest,
    ObjectTemplateComponentResponse,
    ObjectTemplateMigrationAddedComponentResponse,
    ObjectTemplateMigrationAddedPropertyResponse,
    ObjectTemplateMigrationAnalysisResponse,
    ObjectTemplateMigrationBlockingChangeResponse,
    ObjectTemplatePropertyRequest,
    ObjectTemplatePropertyResponse,
    ObjectTemplateResponse,
    ObjectTemplateVersionRefRequest,
    ObjectTemplateVersionRefResponse,
    ObjectTemplateVersionResponse,
    ReviseObjectTemplateVersionRequest,
)
from netauto.application.object import ObjectApplicationService
from netauto.application.objecttemplate import (
    ObjectTemplateApplicationService,
    ObjectTemplateComponentSpec,
    ObjectTemplatePropertySpec,
)
from netauto.core.object import (
    ObjectMigrationResult,
    ObjectTemplateMigrationAddedComponent,
    ObjectTemplateMigrationAddedProperty,
    ObjectTemplateMigrationAnalysis,
    ObjectTemplateMigrationBlockingChange,
)
from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateComponent,
    ObjectTemplateProperty,
    ObjectTemplateVersion,
    ObjectTemplateVersionRef,
)

router = APIRouter(prefix="/object-templates", tags=["object-templates"])

PositiveVersion = Annotated[int, Path(ge=1)]
PositiveVersionQuery = Annotated[int, Query(ge=1)]


def _to_parent_ref(
    parent: ObjectTemplateVersionRefRequest | None,
) -> ObjectTemplateVersionRef | None:
    if parent is None:
        return None
    return ObjectTemplateVersionRef(template_id=parent.template_id, version=parent.version)


def _to_property_spec(
    property_request: ObjectTemplatePropertyRequest,
) -> ObjectTemplatePropertySpec:
    return ObjectTemplatePropertySpec(
        name=property_request.name,
        datatype_id=property_request.datatype_id,
        datatype_version=property_request.datatype_version,
        required=property_request.required,
    )


def _to_component_spec(
    component_request: ObjectTemplateComponentRequest,
) -> ObjectTemplateComponentSpec:
    return ObjectTemplateComponentSpec(
        name=component_request.name,
        template_id=component_request.template_id,
    )


def _to_object_template_response(template: ObjectTemplate) -> ObjectTemplateResponse:
    return ObjectTemplateResponse(
        id=template.id,
        namespace=template.namespace,
        name=template.name,
        qualified_name=template.qualified_name,
        description=template.description,
        abstract=template.abstract,
    )


def _to_property_response(property_value: ObjectTemplateProperty) -> ObjectTemplatePropertyResponse:
    return ObjectTemplatePropertyResponse(
        name=property_value.name,
        datatype_id=property_value.datatype_id,
        datatype_version=property_value.datatype_version,
        required=property_value.required,
    )


def _to_component_response(
    component_value: ObjectTemplateComponent,
) -> ObjectTemplateComponentResponse:
    return ObjectTemplateComponentResponse(
        name=component_value.name,
        template_id=component_value.template_id,
    )


def _to_parent_response(
    parent: ObjectTemplateVersionRef | None,
) -> ObjectTemplateVersionRefResponse | None:
    if parent is None:
        return None
    return ObjectTemplateVersionRefResponse(
        template_id=parent.template_id,
        version=parent.version,
    )


def _to_version_response(version: ObjectTemplateVersion) -> ObjectTemplateVersionResponse:
    return ObjectTemplateVersionResponse(
        template_id=version.template_id,
        version=version.version,
        status=version.status,
        parent=_to_parent_response(version.parent),
        properties=[_to_property_response(prop) for prop in version.properties],
        components=[_to_component_response(component) for component in version.components],
    )


def _to_migration_added_property_response(
    property_value: ObjectTemplateMigrationAddedProperty,
) -> ObjectTemplateMigrationAddedPropertyResponse:
    return ObjectTemplateMigrationAddedPropertyResponse(
        name=property_value.name,
        required=property_value.required,
    )


def _to_migration_added_component_response(
    component_value: ObjectTemplateMigrationAddedComponent,
) -> ObjectTemplateMigrationAddedComponentResponse:
    return ObjectTemplateMigrationAddedComponentResponse(
        name=component_value.name,
        template_id=component_value.template_id,
    )


def _to_migration_blocking_change_response(
    change: ObjectTemplateMigrationBlockingChange,
) -> ObjectTemplateMigrationBlockingChangeResponse:
    return ObjectTemplateMigrationBlockingChangeResponse(
        kind=change.kind,
        name=change.name,
    )


def _to_migration_analysis_response(
    analysis: ObjectTemplateMigrationAnalysis,
) -> ObjectTemplateMigrationAnalysisResponse:
    return ObjectTemplateMigrationAnalysisResponse(
        template_id=analysis.template_id,
        source_version=analysis.source_version,
        target_version=analysis.target_version,
        automatic=analysis.automatic,
        added_properties=[
            _to_migration_added_property_response(property_value)
            for property_value in analysis.added_properties
        ],
        added_components=[
            _to_migration_added_component_response(component_value)
            for component_value in analysis.added_components
        ],
        blocking_changes=[
            _to_migration_blocking_change_response(change)
            for change in analysis.blocking_changes
        ],
    )


def _to_migrate_objects_response(result: ObjectMigrationResult) -> MigrateObjectsResponse:
    return MigrateObjectsResponse(
        template_id=result.template_id,
        source_version=result.source_version,
        target_version=result.target_version,
        migrated_count=result.migrated_count,
    )


@router.post(
    "",
    response_model=CreateObjectTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    responses=ERROR_RESPONSES,
)
def create_object_template(
    request: CreateObjectTemplateRequest,
    service: Annotated[ObjectTemplateApplicationService, Depends(get_object_template_service)],
) -> CreateObjectTemplateResponse:
    template, version = service.create_object_template(
        namespace=request.namespace,
        name=request.name,
        description=request.description,
        abstract=request.abstract,
        parent=_to_parent_ref(request.parent),
        properties=tuple(_to_property_spec(prop) for prop in request.properties),
        components=tuple(_to_component_spec(component) for component in request.components),
    )
    return CreateObjectTemplateResponse(
        object_template=_to_object_template_response(template),
        version=_to_version_response(version),
    )


@router.get("", response_model=list[ObjectTemplateResponse], responses=ERROR_RESPONSES)
def list_object_templates(
    service: Annotated[ObjectTemplateApplicationService, Depends(get_object_template_service)],
) -> list[ObjectTemplateResponse]:
    return [
        _to_object_template_response(template)
        for template in service.list_object_templates()
    ]


@router.get(
    "/by-name/{namespace}/{name}",
    response_model=ObjectTemplateResponse,
    responses=ERROR_RESPONSES,
)
def get_object_template_by_name(
    namespace: str,
    name: str,
    service: Annotated[ObjectTemplateApplicationService, Depends(get_object_template_service)],
) -> ObjectTemplateResponse:
    return _to_object_template_response(service.get_object_template_by_name(namespace, name))


@router.get(
    "/{template_id}",
    response_model=ObjectTemplateResponse,
    responses=ERROR_RESPONSES,
)
def get_object_template(
    template_id: UUID,
    service: Annotated[ObjectTemplateApplicationService, Depends(get_object_template_service)],
) -> ObjectTemplateResponse:
    return _to_object_template_response(service.get_object_template(template_id))


@router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=ERROR_RESPONSES,
)
def delete_object_template(
    template_id: UUID,
    service: Annotated[ObjectTemplateApplicationService, Depends(get_object_template_service)],
) -> None:
    service.delete_object_template(template_id)


@router.get(
    "/{template_id}/versions",
    response_model=list[ObjectTemplateVersionResponse],
    responses=ERROR_RESPONSES,
)
def list_versions(
    template_id: UUID,
    service: Annotated[ObjectTemplateApplicationService, Depends(get_object_template_service)],
) -> list[ObjectTemplateVersionResponse]:
    return [_to_version_response(version) for version in service.list_versions(template_id)]


@router.get(
    "/{template_id}/versions/{version}",
    response_model=ObjectTemplateVersionResponse,
    responses=ERROR_RESPONSES,
)
def get_version(
    template_id: UUID,
    version: PositiveVersion,
    service: Annotated[ObjectTemplateApplicationService, Depends(get_object_template_service)],
) -> ObjectTemplateVersionResponse:
    return _to_version_response(service.get_version(template_id, version))


@router.get(
    "/{template_id}/versions/{version}/migration-analysis",
    response_model=ObjectTemplateMigrationAnalysisResponse,
    responses=ERROR_RESPONSES,
)
def analyze_object_migration(
    template_id: UUID,
    version: PositiveVersion,
    target_version: PositiveVersionQuery,
    service: Annotated[ObjectApplicationService, Depends(get_object_service)],
) -> ObjectTemplateMigrationAnalysisResponse:
    analysis = service.analyze_object_migration(
        template_id=template_id,
        source_version=version,
        target_version=target_version,
    )
    return _to_migration_analysis_response(analysis)


@router.post(
    "/{template_id}/versions/{version}/migrate-objects",
    response_model=MigrateObjectsResponse,
    responses=ERROR_RESPONSES,
)
def migrate_objects(
    template_id: UUID,
    version: PositiveVersion,
    request: MigrateObjectsRequest,
    service: Annotated[ObjectApplicationService, Depends(get_object_service)],
) -> MigrateObjectsResponse:
    result = service.migrate_objects(
        template_id=template_id,
        source_version=version,
        target_version=request.target_version,
        property_values=request.property_values,
    )
    return _to_migrate_objects_response(result)


@router.put(
    "/{template_id}/versions/{version}",
    response_model=ObjectTemplateVersionResponse,
    responses=ERROR_RESPONSES,
)
def revise_version(
    template_id: UUID,
    version: PositiveVersion,
    request: ReviseObjectTemplateVersionRequest,
    service: Annotated[ObjectTemplateApplicationService, Depends(get_object_template_service)],
) -> ObjectTemplateVersionResponse:
    revised = service.revise_version(
        template_id=template_id,
        version=version,
        parent=_to_parent_ref(request.parent),
        properties=tuple(_to_property_spec(prop) for prop in request.properties),
        components=tuple(_to_component_spec(component) for component in request.components),
    )
    return _to_version_response(revised)


@router.post(
    "/{template_id}/versions",
    response_model=ObjectTemplateVersionResponse,
    status_code=status.HTTP_201_CREATED,
    responses=ERROR_RESPONSES,
)
def create_next_version(
    template_id: UUID,
    request: CreateNextObjectTemplateVersionRequest,
    service: Annotated[ObjectTemplateApplicationService, Depends(get_object_template_service)],
) -> ObjectTemplateVersionResponse:
    version = service.create_next_version(
        template_id=template_id,
        source_version=request.source_version,
    )
    return _to_version_response(version)


@router.post(
    "/{template_id}/versions/{version}/publish",
    response_model=ObjectTemplateVersionResponse,
    responses=ERROR_RESPONSES,
)
def publish_version(
    template_id: UUID,
    version: PositiveVersion,
    service: Annotated[ObjectTemplateApplicationService, Depends(get_object_template_service)],
) -> ObjectTemplateVersionResponse:
    return _to_version_response(service.publish_version(template_id=template_id, version=version))


@router.post(
    "/{template_id}/versions/{version}/deprecate",
    response_model=ObjectTemplateVersionResponse,
    responses=ERROR_RESPONSES,
)
def deprecate_version(
    template_id: UUID,
    version: PositiveVersion,
    service: Annotated[ObjectTemplateApplicationService, Depends(get_object_template_service)],
) -> ObjectTemplateVersionResponse:
    return _to_version_response(
        service.deprecate_version(template_id=template_id, version=version)
    )
