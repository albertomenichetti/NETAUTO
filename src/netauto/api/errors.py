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
    DataTypeInUse,
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
from netauto.core.object import (
    AbstractObjectTemplateInstantiation,
    ComponentMembershipAlreadyExists,
    ComponentMembershipNotFound,
    ComponentOwnershipCycle,
    InvalidComponentMembership,
    InvalidObject,
    InvalidObjectPatch,
    MissingObjectMigrationPropertyValue,
    ObjectAlreadyExists,
    ObjectComponentSlotNotFound,
    ObjectComponentTemplateIncompatible,
    ObjectDataTypeVersionNotFound,
    ObjectMigrationBlocked,
    ObjectMigrationTargetVersionNotNewer,
    ObjectMigrationTargetVersionNotPublished,
    ObjectNotFound,
    ObjectPersistenceError,
    ObjectTemplateVersionNotPublished,
    ObjectValidationFailed,
    UnexpectedObjectMigrationPropertyValue,
)
from netauto.core.objecttemplate import (
    DuplicateObjectTemplateComponent,
    DuplicateObjectTemplateProperty,
    InheritedObjectTemplateComponentConflict,
    InheritedObjectTemplatePropertyConflict,
    InvalidObjectTemplate,
    InvalidObjectTemplateComponent,
    InvalidObjectTemplateIdentifier,
    InvalidObjectTemplateProperty,
    InvalidObjectTemplateVersion,
    InvalidObjectTemplateVersionTransition,
    MismatchedObjectTemplateVersion,
    ObjectTemplateAlreadyExists,
    ObjectTemplateComponentVersionNotFound,
    ObjectTemplateComponentVersionNotPublished,
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
from netauto.core.relationship import (
    InvalidRelationship,
    InvalidRelationshipDefinition,
    InvalidRelationshipIdentifier,
    RelationshipAlreadyExists,
    RelationshipDefinitionAlreadyExists,
    RelationshipDefinitionInUse,
    RelationshipDefinitionNotFound,
    RelationshipDefinitionPersistenceError,
    RelationshipDefinitionSemanticConflict,
    RelationshipDefinitionTemplateNotFound,
    RelationshipDefinitionTemplateNotPublished,
    RelationshipEndpointIncompatible,
    RelationshipNotFound,
    RelationshipObjectNotFound,
    RelationshipPersistenceError,
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


async def object_validation_failed_exception_handler(
    _request: Request,
    exc: ObjectValidationFailed,
) -> JSONResponse:
    details = [
        ErrorDetail(
            path=_normalize_path(issue.path),
            code=issue.code,
            message=issue.message,
        )
        for issue in exc.result.errors
    ]
    details.sort(key=lambda item: (item.path, item.code, item.message))
    return _response(
        HTTPStatus.UNPROCESSABLE_ENTITY,
        code="object_validation_failed",
        message="Object validation failed",
        details=details,
    )


_EXCEPTION_MAP: tuple[tuple[type[Exception], int, str, str], ...] = (
    (ObjectNotFound, HTTPStatus.NOT_FOUND, "object_not_found", "Object not found"),
    (
        ComponentMembershipNotFound,
        HTTPStatus.NOT_FOUND,
        "component_membership_not_found",
        "Component membership not found",
    ),
    (DataTypeNotFound, HTTPStatus.NOT_FOUND, "datatype_not_found", "Datatype not found"),
    (
        DataTypeVersionNotFound,
        HTTPStatus.NOT_FOUND,
        "datatype_version_not_found",
        "Datatype version not found",
    ),
    (
        ObjectAlreadyExists,
        HTTPStatus.CONFLICT,
        "object_already_exists",
        "Object already exists",
    ),
    (
        ComponentMembershipAlreadyExists,
        HTTPStatus.CONFLICT,
        "component_membership_already_exists",
        "Component membership already exists",
    ),
    (
        ObjectTemplateVersionNotPublished,
        HTTPStatus.CONFLICT,
        "object_template_version_not_published",
        "Object template version must be published",
    ),
    (
        AbstractObjectTemplateInstantiation,
        HTTPStatus.CONFLICT,
        "abstract_object_template_instantiation",
        "Abstract object template cannot be instantiated",
    ),
    (
        ObjectComponentTemplateIncompatible,
        HTTPStatus.CONFLICT,
        "object_component_template_incompatible",
        "Object component template is incompatible",
    ),
    (
        ComponentOwnershipCycle,
        HTTPStatus.CONFLICT,
        "component_ownership_cycle",
        "Component ownership cycle detected",
    ),
    (
        ObjectMigrationTargetVersionNotNewer,
        HTTPStatus.CONFLICT,
        "object_migration_target_version_not_newer",
        "Object migration target version must be newer than the source version",
    ),
    (
        ObjectMigrationTargetVersionNotPublished,
        HTTPStatus.CONFLICT,
        "object_migration_target_version_not_published",
        "Object migration target version must be published",
    ),
    (
        ObjectMigrationBlocked,
        HTTPStatus.CONFLICT,
        "object_migration_blocked",
        "Object migration contains blocking schema changes",
    ),
    (
        DataTypeAlreadyExists,
        HTTPStatus.CONFLICT,
        "datatype_already_exists",
        "Datatype already exists",
    ),
    (
        DataTypeInUse,
        HTTPStatus.CONFLICT,
        "datatype_in_use",
        "Datatype is still referenced by an object template",
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
        InvalidObject,
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "invalid_object",
        "Object is invalid",
    ),
    (
        InvalidComponentMembership,
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "invalid_component_membership",
        "Component membership is invalid",
    ),
    (
        InvalidObjectPatch,
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "invalid_object_patch",
        "Object patch is invalid",
    ),
    (
        InvalidRelationship,
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "invalid_relationship",
        "Relationship is invalid",
    ),
    (
        MissingObjectMigrationPropertyValue,
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "missing_object_migration_property_value",
        "Object migration requires values for newly added required properties",
    ),
    (
        UnexpectedObjectMigrationPropertyValue,
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "unexpected_object_migration_property_value",
        "Object migration supplied values may only target newly added properties",
    ),
    (
        ObjectComponentSlotNotFound,
        HTTPStatus.NOT_FOUND,
        "object_component_slot_not_found",
        "Object component slot not found",
    ),
    (
        InvalidDataTypeVersion,
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "invalid_datatype_version",
        "Datatype version is invalid",
    ),
    (
        ObjectDataTypeVersionNotFound,
        HTTPStatus.INTERNAL_SERVER_ERROR,
        "object_datatype_version_not_found",
        "Object datatype version not found",
    ),
    (
        ObjectPersistenceError,
        HTTPStatus.INTERNAL_SERVER_ERROR,
        "persistence_error",
        "Persistence operation failed",
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
        ObjectTemplateComponentVersionNotFound,
        HTTPStatus.NOT_FOUND,
        "object_template_component_version_not_found",
        "Object template component target template not found",
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
        RelationshipNotFound,
        HTTPStatus.NOT_FOUND,
        "relationship_not_found",
        "Relationship not found",
    ),
    (
        RelationshipObjectNotFound,
        HTTPStatus.NOT_FOUND,
        "relationship_object_not_found",
        "Relationship endpoint object not found",
    ),
    (
        RelationshipDefinitionNotFound,
        HTTPStatus.NOT_FOUND,
        "relationship_definition_not_found",
        "Relationship definition not found",
    ),
    (
        RelationshipDefinitionTemplateNotFound,
        HTTPStatus.NOT_FOUND,
        "relationship_definition_template_not_found",
        "Relationship definition template not found",
    ),
    (
        RelationshipAlreadyExists,
        HTTPStatus.CONFLICT,
        "relationship_already_exists",
        "Relationship already exists",
    ),
    (
        RelationshipEndpointIncompatible,
        HTTPStatus.CONFLICT,
        "relationship_endpoint_incompatible",
        "Relationship endpoint is incompatible",
    ),
    (
        RelationshipDefinitionAlreadyExists,
        HTTPStatus.CONFLICT,
        "relationship_definition_already_exists",
        "Relationship definition already exists",
    ),
    (
        RelationshipDefinitionInUse,
        HTTPStatus.CONFLICT,
        "relationship_definition_in_use",
        "Relationship definition is in use",
    ),
    (
        RelationshipDefinitionSemanticConflict,
        HTTPStatus.CONFLICT,
        "relationship_definition_semantic_conflict",
        "Relationship definition conflicts semantically with an existing definition",
    ),
    (
        RelationshipDefinitionTemplateNotPublished,
        HTTPStatus.CONFLICT,
        "relationship_definition_template_not_published",
        "Relationship definition template must have a published version",
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
        ObjectTemplateComponentVersionNotPublished,
        HTTPStatus.CONFLICT,
        "object_template_component_version_not_published",
        "Object template component target template must have a published version",
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
        InheritedObjectTemplateComponentConflict,
        HTTPStatus.CONFLICT,
        "inherited_object_template_component_conflict",
        "Object template component conflicts with inherited component",
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
        InvalidObjectTemplateComponent,
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "invalid_object_template_component",
        "Object template component is invalid",
    ),
    (
        DuplicateObjectTemplateProperty,
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "duplicate_object_template_property",
        "Object template property names must be unique",
    ),
    (
        DuplicateObjectTemplateComponent,
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "duplicate_object_template_component",
        "Object template component names must be unique",
    ),
    (
        InvalidRelationshipDefinition,
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "invalid_relationship_definition",
        "Relationship definition is invalid",
    ),
    (
        InvalidRelationshipIdentifier,
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "invalid_relationship_identifier",
        "Relationship identifier is invalid",
    ),
    (
        RelationshipDefinitionPersistenceError,
        HTTPStatus.INTERNAL_SERVER_ERROR,
        "persistence_error",
        "Persistence operation failed",
    ),
    (
        RelationshipPersistenceError,
        HTTPStatus.INTERNAL_SERVER_ERROR,
        "persistence_error",
        "Persistence operation failed",
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
    app.add_exception_handler(
        ObjectValidationFailed,
        cast("Any", object_validation_failed_exception_handler),
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
