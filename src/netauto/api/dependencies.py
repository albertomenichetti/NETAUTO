"""FastAPI dependencies."""

from fastapi import Request

from netauto.application.datatype import DataTypeApplicationService
from netauto.application.object import ObjectApplicationService
from netauto.application.objecttemplate import ObjectTemplateApplicationService
from netauto.application.relationship import (
    RelationshipApplicationService,
    RelationshipDefinitionApplicationService,
)


def get_datatype_service(request: Request) -> DataTypeApplicationService:
    return request.app.state.datatype_service


def get_object_template_service(request: Request) -> ObjectTemplateApplicationService:
    return request.app.state.object_template_service


def get_object_service(request: Request) -> ObjectApplicationService:
    return request.app.state.object_service


def get_relationship_definition_service(
    request: Request,
) -> RelationshipDefinitionApplicationService:
    return request.app.state.relationship_definition_service


def get_relationship_service(request: Request) -> RelationshipApplicationService:
    return request.app.state.relationship_service
