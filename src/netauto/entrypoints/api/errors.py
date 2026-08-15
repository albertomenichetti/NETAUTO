"""Canonical mapping from application failures to the public error contract."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from netauto.failures import ApplicationFailure, FailureClass

logger = logging.getLogger(__name__)

_STATUS_BY_CLASS = {
    FailureClass.INVALID_REQUEST: 400,
    FailureClass.NOT_FOUND: 404,
    FailureClass.SEMANTIC_VALIDATION: 422,
    FailureClass.STATE_CONFLICT: 409,
    FailureClass.INTERNAL_FAILURE: 500,
}

PUBLIC_STATUS_BY_CODE = {
    "invalid_request": 400,
    "invalid_cursor": 400,
    "resource_not_found": 404,
    "referenced_resource_not_found": 422,
    "semantic_validation_failed": 422,
    "stale_revision": 409,
    "lifecycle_state_conflict": 409,
    "version_source_conflict": 409,
    "default_version_unavailable": 409,
    "dependency_not_admissible": 409,
    "qualified_name_conflict": 409,
    "default_version_conflict": 409,
    "active_dependency_conflict": 409,
    "delete_blocked": 409,
    "ownership_slot_unavailable": 409,
    "ownership_conflict": 409,
    "ownership_mismatch": 409,
    "ownership_cycle": 409,
    "schema_change_blocked": 409,
    "relationship_definition_equivalent": 409,
    "relationship_definition_conflict": 409,
    "relationship_fact_conflict": 409,
    "internal_error": 500,
}


def _response(failure: ApplicationFailure) -> JSONResponse:
    status_code = PUBLIC_STATUS_BY_CODE.get(failure.code)
    if status_code is None or status_code != _STATUS_BY_CLASS[failure.failure_class]:
        logger.error("Application emitted an invalid public failure code/class pair")
        failure = ApplicationFailure(
            FailureClass.INTERNAL_FAILURE,
            "internal_error",
            "An unexpected internal failure occurred.",
        )
        status_code = 500
    return JSONResponse(
        status_code=status_code,
        content={
            "code": failure.code,
            "message": failure.message,
            "details": failure.details,
        },
    )


async def _application_failure_handler(
    request: Request, error: Exception
) -> JSONResponse:
    del request
    if not isinstance(error, ApplicationFailure):
        raise error
    return _response(error)


async def _request_validation_handler(
    request: Request, error: Exception
) -> JSONResponse:
    del request
    if not isinstance(error, RequestValidationError):
        raise error
    return _response(
        ApplicationFailure(
            FailureClass.INVALID_REQUEST,
            "invalid_request",
            "The request path, query, or body is malformed.",
        )
    )


async def _unexpected_failure_handler(
    request: Request, error: Exception
) -> JSONResponse:
    del request
    logger.exception("Unexpected HTTP request failure", exc_info=error)
    return _response(
        ApplicationFailure(
            FailureClass.INTERNAL_FAILURE,
            "internal_error",
            "An unexpected internal failure occurred.",
        )
    )


def install_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApplicationFailure, _application_failure_handler)
    app.add_exception_handler(RequestValidationError, _request_validation_handler)
    app.add_exception_handler(Exception, _unexpected_failure_handler)
