"""Strict operational HTTP adapter for Core readiness."""

from typing import cast

from fastapi import APIRouter, Request, Response

from netauto.application.health import CoreHealthService
from netauto.entrypoints.api.common import NoBody, validate_query
from netauto.transport.http.health import ComponentHealthDTO, CoreHealthDTO

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "/core",
    response_model=CoreHealthDTO,
    response_model_exclude_none=True,
    responses={
        503: {
            "model": CoreHealthDTO,
            "description": "Core is not ready",
        }
    },
)
async def get_core_health(
    request: Request,
    response: Response,
    _no_body: NoBody,
) -> CoreHealthDTO:
    validate_query(request, ())
    service = cast(CoreHealthService, request.app.state.core_health_service)
    result = await service.check()
    response.status_code = 200 if result.is_ready else 503
    response.headers["Cache-Control"] = "no-store"
    return CoreHealthDTO(
        app_status=ComponentHealthDTO(
            status=result.app_status.status,
            message=result.app_status.message,
        ),
        db_status=ComponentHealthDTO(
            status=result.db_status.status,
            message=result.db_status.message,
        ),
        execution_time_ms=result.execution_time_ms,
    )
