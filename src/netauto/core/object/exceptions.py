"""Domain exceptions for object domain models and validation."""


class InvalidObject(Exception):
    """Raised when an object has invalid local state."""


class InvalidComponentMembership(Exception):
    """Raised when a component membership has invalid local state."""


class ObjectDataTypeVersionNotFound(Exception):
    """Raised when a referenced datatype version cannot be found during validation."""
