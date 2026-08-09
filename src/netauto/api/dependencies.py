"""FastAPI dependencies."""

from fastapi import Request

from netauto.application.datatype import DataTypeApplicationService
from netauto.application.objecttemplate import ObjectTemplateApplicationService


def get_datatype_service(request: Request) -> DataTypeApplicationService:
    return request.app.state.datatype_service


def get_object_template_service(request: Request) -> ObjectTemplateApplicationService:
    return request.app.state.object_template_service
