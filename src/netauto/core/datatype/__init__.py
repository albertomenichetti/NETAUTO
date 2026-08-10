"""Built-in datatype primitives."""

from netauto.core.datatype.compiler import SchemaCompiler
from netauto.core.datatype.constraints import Constraint, ConstraintName
from netauto.core.datatype.exceptions import (
    ConflictingConstraints,
    DataTypeAlreadyExists,
    DataTypeConstraintError,
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
    MismatchedDataTypeVersion,
    PrimitiveTypeNotFound,
    ReservedDataTypeNamespace,
    SchemaCompilationError,
    UnsupportedConstraint,
    ValidationEngineError,
)
from netauto.core.datatype.factory import DataTypeFactory
from netauto.core.datatype.models import DataType, DataTypeVersion, DataTypeVersionStatus
from netauto.core.datatype.primitives import PrimitiveType
from netauto.core.datatype.registry import PrimitiveTypeRegistry
from netauto.core.datatype.repository import DataTypeRepository
from netauto.core.datatype.validation import ValidationEngine, ValidationIssue, ValidationResult
from netauto.core.datatype.versioning import DataTypeVersioningService

__all__ = [
    "ConflictingConstraints",
    "Constraint",
    "ConstraintName",
    "DataType",
    "DataTypeFactory",
    "DataTypeAlreadyExists",
    "DataTypeInUse",
    "DataTypeConstraintError",
    "DataTypeNotFound",
    "DataTypePersistenceError",
    "DataTypeRepository",
    "DataTypeVersion",
    "DataTypeVersionAlreadyExists",
    "DataTypeVersionNotFound",
    "DataTypeVersionStatus",
    "DuplicateConstraint",
    "InvalidConstraintValue",
    "InvalidDataTypeIdentifier",
    "InvalidDataTypeVersion",
    "InvalidDataTypeVersionTransition",
    "MismatchedDataTypeVersion",
    "PrimitiveType",
    "PrimitiveTypeNotFound",
    "PrimitiveTypeRegistry",
    "ReservedDataTypeNamespace",
    "SchemaCompilationError",
    "SchemaCompiler",
    "UnsupportedConstraint",
    "ValidationEngine",
    "ValidationEngineError",
    "ValidationIssue",
    "ValidationResult",
    "DataTypeVersioningService",
]
