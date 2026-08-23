"""FastAPI composition entrypoint."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from netauto.application.health import CoreHealthService
from netauto.entrypoints.api.datatypes import router as datatype_router
from netauto.entrypoints.api.errors import install_error_handlers
from netauto.entrypoints.api.health import router as health_router
from netauto.entrypoints.api.objects import router as object_router
from netauto.entrypoints.api.objecttemplates import router as object_template_router
from netauto.entrypoints.api.relationshipdefinitions import (
    router as relationship_definition_router,
)
from netauto.entrypoints.api.relationships import router as relationship_router
from netauto.logging import configure_logging
from netauto.persistence.engine import build_runtime_context
from netauto.persistence.health import PostgreSQLHealthProbe
from netauto.runtime.schema_guard import require_exact_schema_revision
from netauto.settings import Settings, load_settings

logger = logging.getLogger(__name__)


def build_app(settings: Settings) -> FastAPI:
    """Build the ASGI application from already validated process settings."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        configure_logging(settings.log_level)
        runtime = build_runtime_context(settings)
        try:
            await require_exact_schema_revision(runtime.engine)
            health_service = CoreHealthService(PostgreSQLHealthProbe(runtime.engine))
            app.state.runtime = runtime
            app.state.core_health_service = health_service
            logger.info("NETAUTO process starting")
            yield
        finally:
            await runtime.engine.dispose()
            logger.info("NETAUTO process stopping")

    app = FastAPI(title="NETAUTO", lifespan=lifespan)
    app.state.settings = settings
    app.include_router(datatype_router)
    app.include_router(object_template_router)
    app.include_router(object_router)
    app.include_router(relationship_definition_router)
    app.include_router(relationship_router)
    app.include_router(health_router)
    install_error_handlers(app)
    return app


def create_app() -> FastAPI:
    """Load process settings and build an app for Uvicorn factory loading."""
    return build_app(load_settings())
