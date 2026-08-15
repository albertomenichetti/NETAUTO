"""FastAPI composition entrypoint."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from netauto.entrypoints.api.datatypes import router as datatype_router
from netauto.entrypoints.api.errors import install_error_handlers
from netauto.entrypoints.api.objects import router as object_router
from netauto.entrypoints.api.objecttemplates import router as object_template_router
from netauto.entrypoints.api.relationshipdefinitions import (
    router as relationship_definition_router,
)
from netauto.entrypoints.api.relationships import router as relationship_router
from netauto.logging import configure_logging
from netauto.persistence.engine import build_runtime_context
from netauto.settings import Settings

logger = logging.getLogger(__name__)


def build_app(settings: Settings) -> FastAPI:
    """Build the ASGI application from already validated process settings."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        configure_logging(settings.log_level)
        runtime = build_runtime_context(settings.database_url)
        app.state.runtime = runtime
        logger.info("NETAUTO process starting")
        try:
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
    install_error_handlers(app)
    return app


def create_app() -> FastAPI:
    """Load process settings and build an app for Uvicorn factory loading."""
    # BaseSettings obtains the required value from NETAUTO_DATABASE_URL here.
    settings = Settings()  # pyright: ignore[reportCallIssue]
    return build_app(settings)
