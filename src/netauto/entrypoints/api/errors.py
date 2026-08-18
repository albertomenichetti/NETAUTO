"""Canonical mapping from application failures to the public error contract."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from netauto.failures import ApplicationFailure, FailureClass
from netauto.transport.http.errors import PUBLIC_STATUS_BY_CODE, BusinessErrorDTO

logger = logging.getLogger(__name__)

_STATUS_BY_CLASS = {
    FailureClass.INVALID_REQUEST: 400,
    FailureClass.NOT_FOUND: 404,
    FailureClass.SEMANTIC_VALIDATION: 422,
    FailureClass.STATE_CONFLICT: 409,
    FailureClass.INTERNAL_FAILURE: 500,
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
    content = BusinessErrorDTO(
        code=failure.code,
        message=failure.message,
        details=failure.details,
    )
    return JSONResponse(
        status_code=status_code, content=content.model_dump(mode="json")
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
