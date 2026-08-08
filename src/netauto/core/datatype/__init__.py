"""Built-in datatype primitives."""

from netauto.core.datatype.compiler import SchemaCompiler
from netauto.core.datatype.constraints import Constraint, ConstraintName
from netauto.core.datatype.exceptions import (
    ConflictingConstraints,
    DataTypeConstraintError,
    DuplicateConstraint,
    InvalidConstraintValue,
    InvalidDataTypeIdentifier,
    InvalidDataTypeVersion,
    PrimitiveTypeNotFound,
    SchemaCompilationError,
    UnsupportedConstraint,
)
from netauto.core.datatype.models import DataType, DataTypeVersion, DataTypeVersionStatus
from netauto.core.datatype.primitives import PrimitiveType
from netauto.core.datatype.registry import PrimitiveTypeRegistry

__all__ = [
    "ConflictingConstraints",
    "Constraint",
    "ConstraintName",
    "DataType",
    "DataTypeConstraintError",
    "DataTypeVersion",
    "DataTypeVersionStatus",
    "DuplicateConstraint",
    "InvalidConstraintValue",
    "InvalidDataTypeIdentifier",
    "InvalidDataTypeVersion",
    "PrimitiveType",
    "PrimitiveTypeNotFound",
    "PrimitiveTypeRegistry",
    "SchemaCompilationError",
    "SchemaCompiler",
    "UnsupportedConstraint",
]
