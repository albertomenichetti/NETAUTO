"""API error mapping and handlers."""

from http import HTTPStatus
from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from netauto.api.schemas.datatypes import ErrorBody, ErrorDetail, ErrorResponse
from netauto.core.datatype import (
    ConflictingConstraints,
    DataTypeAlreadyExists,
    DataTypeNotFound,
    DataTypePersistenceError,
    DataTypeVersionAlreadyExists,
    DataTypeVersionNotFound,
    DuplicateConstraint,
    InvalidConstraintValue,
    InvalidDataTypeIdentifier,
    InvalidDataTypeVersion,
    InvalidDataTypeVersionTransition,
    PrimitiveTypeNotFound,
    ReservedDataTypeNamespace,
    SchemaCompilationError,
    UnsupportedConstraint,
)
from netauto.core.objecttemplate import (
    DuplicateObjectTemplateProperty,
    InheritedObjectTemplatePropertyConflict,
    InvalidObjectTemplate,
    InvalidObjectTemplateIdentifier,
    InvalidObjectTemplateProperty,
    InvalidObjectTemplateVersion,
    InvalidObjectTemplateVersionTransition,
    MismatchedObjectTemplateVersion,
    ObjectTemplateAlreadyExists,
    ObjectTemplateDataTypeVersionNotFound,
    ObjectTemplateDataTypeVersionNotPublished,
    ObjectTemplateInheritanceCycle,
    ObjectTemplateNotFound,
    ObjectTemplateParentNotFound,
    ObjectTemplateParentNotPublished,
    ObjectTemplatePersistenceError,
    ObjectTemplateSelfInheritance,
    ObjectTemplateVersionAlreadyExists,
    ObjectTemplateVersionNotFound,
)


def _response(
    status_code: int,
    *,
    code: str,
    message: str,
    details: list[ErrorDetail] | None = None,
) -> JSONResponse:
    payload = ErrorResponse(
        error=ErrorBody(code=code, message=message, details=details or []),
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))


def _normalize_path(location: tuple[object, ...]) -> str:
    return "/" + "/".join(str(component) for component in location)


async def request_validation_exception_handler(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    details = [
        ErrorDetail(
            path=_normalize_path(tuple(error["loc"])),
            code=str(error["type"]),
            message=str(error["msg"]),
        )
        for error in exc.errors()
    ]
    details.sort(key=lambda item: (item.path, item.code, item.message))
    return _response(
        HTTPStatus.UNPROCESSABLE_ENTITY,
        code="request_validation_failed",
        message="Request validation failed",
        details=details,
    )


_EXCEPTION_MAP: tuple[tuple[type[Exception], int, str, str], ...] = (
    (DataTypeNotFound, HTTPStatus.NOT_FOUND, "datatype_not_found", "Datatype not found"),
    (
        DataTypeVersionNotFound,
        HTTPStatus.NOT_FOUND,
        "datatype_version_not_found",
        "Datatype version not found",
    ),
    (
        DataTypeAlreadyExists,
        HTTPStatus.CONFLICT,
        "datatype_already_exists",
        "Datatype already exists",
    ),
    (
        DataTypeVersionAlreadyExists,
        HTTPStatus.CONFLICT,
        "datatype_version_already_exists",
        "Datatype version already exists",
    ),
    (
        InvalidDataTypeVersionTransition,
        HTTPStatus.CONFLICT,
        "invalid_datatype_version_transition",
        "Datatype version transition is invalid",
    ),
    (
        InvalidDataTypeIdentifier,
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "invalid_datatype_identifier",
        "Datatype identifier is invalid",
    ),
    (
        ReservedDataTypeNamespace,
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "reserved_datatype_namespace",
        "The namespace is reserved",
    ),
    (
        PrimitiveTypeNotFound,
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "primitive_type_not_found",
        "Primitive type not found",
    ),
    (
        UnsupportedConstraint,
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "unsupported_constraint",
        "Constraint is not supported",
    ),
    (
        InvalidConstraintValue,
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "invalid_constraint_value",
        "Constraint value is invalid",
    ),
    (
        DuplicateConstraint,
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "duplicate_constraint",
        "Constraint names must be unique",
    ),
    (
        ConflictingConstraints,
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "conflicting_constraints",
        "Constraints conflict",
    ),
    (
        SchemaCompilationError,
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "schema_compilation_failed",
        "Schema compilation failed",
    ),
    (
        InvalidDataTypeVersion,
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "invalid_datatype_version",
        "Datatype version is invalid",
    ),
    (
        DataTypePersistenceError,
        HTTPStatus.INTERNAL_SERVER_ERROR,
        "persistence_error",
        "Persistence operation failed",
    ),
    (
        ObjectTemplateNotFound,
        HTTPStatus.NOT_FOUND,
        "object_template_not_found",
        "Object template not found",
    ),
    (
        ObjectTemplateVersionNotFound,
        HTTPStatus.NOT_FOUND,
        "object_template_version_not_found",
        "Object template version not found",
    ),
    (
        ObjectTemplateParentNotFound,
        HTTPStatus.NOT_FOUND,
        "object_template_parent_not_found",
        "Object template parent not found",
    ),
    (
        ObjectTemplateDataTypeVersionNotFound,
        HTTPStatus.NOT_FOUND,
        "object_template_datatype_version_not_found",
        "Object template datatype version not found",
    ),
    (
        ObjectTemplateAlreadyExists,
        HTTPStatus.CONFLICT,
        "object_template_already_exists",
        "Object template already exists",
    ),
    (
        ObjectTemplateVersionAlreadyExists,
        HTTPStatus.CONFLICT,
        "object_template_version_already_exists",
        "Object template version already exists",
    ),
    (
        InvalidObjectTemplateVersionTransition,
        HTTPStatus.CONFLICT,
        "invalid_object_template_version_transition",
        "Object template version transition is invalid",
    ),
    (
        ObjectTemplateParentNotPublished,
        HTTPStatus.CONFLICT,
        "object_template_parent_not_published",
        "Object template parent must be published",
    ),
    (
        ObjectTemplateDataTypeVersionNotPublished,
        HTTPStatus.CONFLICT,
        "object_template_datatype_version_not_published",
        "Object template datatype version must be published",
    ),
    (
        ObjectTemplateInheritanceCycle,
        HTTPStatus.CONFLICT,
        "object_template_inheritance_cycle",
        "Object template inheritance cycle detected",
    ),
    (
        ObjectTemplateSelfInheritance,
        HTTPStatus.CONFLICT,
        "object_template_self_inheritance",
        "Object template self inheritance is not allowed",
    ),
    (
        InheritedObjectTemplatePropertyConflict,
        HTTPStatus.CONFLICT,
        "inherited_object_template_property_conflict",
        "Object template property conflicts with inherited property",
    ),
    (
        MismatchedObjectTemplateVersion,
        HTTPStatus.CONFLICT,
        "mismatched_object_template_version",
        "Object template version set is inconsistent",
    ),
    (
        InvalidObjectTemplate,
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "invalid_object_template",
        "Object template is invalid",
    ),
    (
        InvalidObjectTemplateIdentifier,
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "invalid_object_template_identifier",
        "Object template identifier is invalid",
    ),
    (
        InvalidObjectTemplateVersion,
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "invalid_object_template_version",
        "Object template version is invalid",
    ),
    (
        InvalidObjectTemplateProperty,
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "invalid_object_template_property",
        "Object template property is invalid",
    ),
    (
        DuplicateObjectTemplateProperty,
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "duplicate_object_template_property",
        "Object template property names must be unique",
    ),
    (
        ObjectTemplatePersistenceError,
        HTTPStatus.INTERNAL_SERVER_ERROR,
        "persistence_error",
        "Persistence operation failed",
    ),
)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(
        RequestValidationError,
        cast("Any", request_validation_exception_handler),
    )

    for exception_type, status_code, code, message in _EXCEPTION_MAP:
        async def _handler(
            _request: Request,
            _exc: Exception,
            *,
            _status_code: int = status_code,
            _code: str = code,
            _message: str = message,
        ) -> JSONResponse:
            return _response(_status_code, code=_code, message=_message)

        app.add_exception_handler(exception_type, _handler)


ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    404: {"model": ErrorResponse, "description": "Not found"},
    409: {"model": ErrorResponse, "description": "Conflict"},
    422: {"model": ErrorResponse, "description": "Validation error"},
    500: {"model": ErrorResponse, "description": "Persistence error"},
}
