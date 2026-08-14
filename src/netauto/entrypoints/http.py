"""FastAPI composition entrypoint."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from netauto.logging import configure_logging
from netauto.settings import Settings

logger = logging.getLogger(__name__)


def build_app(settings: Settings) -> FastAPI:
    """Build the ASGI application from already validated process settings."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        del app
        configure_logging(settings.log_level)
        logger.info("NETAUTO process starting")
        try:
            yield
        finally:
            logger.info("NETAUTO process stopping")

    app = FastAPI(title="NETAUTO", lifespan=lifespan)
    app.state.settings = settings
    return app


def create_app() -> FastAPI:
    """Load process settings and build an app for Uvicorn factory loading."""
    # BaseSettings obtains the required value from NETAUTO_DATABASE_URL here.
    settings = Settings()  # pyright: ignore[reportCallIssue]
    return build_app(settings)
