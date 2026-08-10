"""FastAPI app factory."""

from fastapi import FastAPI

from netauto.api.errors import register_exception_handlers
from netauto.api.routers.datatypes import router as datatype_router
from netauto.api.routers.objects import router as object_router
from netauto.api.routers.objecttemplates import router as object_template_router
from netauto.api.routers.relationships import router as relationship_router
from netauto.application.datatype import DataTypeApplicationService
from netauto.application.object import ObjectApplicationService
from netauto.application.objecttemplate import ObjectTemplateApplicationService
from netauto.application.relationship import (
    RelationshipApplicationService,
    RelationshipDefinitionApplicationService,
)
from netauto.application.unit_of_work import ObjectUnitOfWorkFactory


def create_app(uow_factory: ObjectUnitOfWorkFactory) -> FastAPI:
    app = FastAPI()
    app.state.datatype_service = DataTypeApplicationService(uow_factory)
    app.state.object_template_service = ObjectTemplateApplicationService(uow_factory)
    app.state.object_service = ObjectApplicationService(uow_factory)
    app.state.relationship_definition_service = RelationshipDefinitionApplicationService(
        uow_factory
    )
    app.state.relationship_service = RelationshipApplicationService(uow_factory)
    register_exception_handlers(app)
    app.include_router(datatype_router, prefix="/api/v1")
    app.include_router(object_router, prefix="/api/v1")
    app.include_router(object_template_router, prefix="/api/v1")
    app.include_router(relationship_router, prefix="/api/v1")
    return app
