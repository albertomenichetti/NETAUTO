"""FastAPI app factory."""

from fastapi import FastAPI

from netauto.api.errors import register_exception_handlers
from netauto.api.routers.datatypes import router as datatype_router
from netauto.application.datatype import DataTypeApplicationService
from netauto.application.unit_of_work import DataTypeUnitOfWorkFactory


def create_app(uow_factory: DataTypeUnitOfWorkFactory) -> FastAPI:
    app = FastAPI()
    app.state.datatype_service = DataTypeApplicationService(uow_factory)
    register_exception_handlers(app)
    app.include_router(datatype_router, prefix="/api/v1")
    return app
