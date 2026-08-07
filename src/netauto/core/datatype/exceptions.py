"""Domain exceptions for datatype domain models."""


class PrimitiveTypeNotFound(Exception):
    """Raised when a built-in primitive type cannot be found."""


class InvalidDataTypeIdentifier(Exception):
    """Raised when a datatype namespace or name is invalid."""


class InvalidDataTypeVersion(Exception):
    """Raised when a datatype version number is invalid."""
