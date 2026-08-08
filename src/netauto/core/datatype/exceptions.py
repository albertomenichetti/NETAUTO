"""Domain exceptions for datatype domain models."""


class PrimitiveTypeNotFound(Exception):
    """Raised when a built-in primitive type cannot be found."""


class InvalidDataTypeIdentifier(Exception):
    """Raised when a datatype namespace or name is invalid."""


class InvalidDataTypeVersion(Exception):
    """Raised when a datatype version number is invalid."""


class DataTypeConstraintError(Exception):
    """Base exception for datatype constraint validation errors."""


class UnsupportedConstraint(DataTypeConstraintError):
    """Raised when a constraint is not supported for a primitive type."""


class InvalidConstraintValue(DataTypeConstraintError):
    """Raised when a constraint value is invalid."""


class DuplicateConstraint(DataTypeConstraintError):
    """Raised when a datatype version contains duplicate constraints."""


class ConflictingConstraints(DataTypeConstraintError):
    """Raised when a datatype version contains conflicting constraints."""


class SchemaCompilationError(Exception):
    """Raised when schema compilation fails."""


class ValidationEngineError(Exception):
    """Raised when datatype validation machinery fails."""


class ReservedDataTypeNamespace(Exception):
    """Raised when a custom datatype uses a reserved namespace."""


class InvalidDataTypeVersionTransition(Exception):
    """Raised when a datatype version lifecycle transition is invalid."""


class MismatchedDataTypeVersion(Exception):
    """Raised when versions from different datatypes are mixed."""


class DataTypeAlreadyExists(Exception):
    """Raised when a datatype identity or logical name already exists."""


class DataTypeVersionAlreadyExists(Exception):
    """Raised when a datatype version identity already exists."""


class DataTypeNotFound(Exception):
    """Raised when a required datatype does not exist."""


class DataTypeVersionNotFound(Exception):
    """Raised when a required datatype version does not exist."""


class DataTypePersistenceError(Exception):
    """Raised when persisted datatype state cannot be mapped safely."""
