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
