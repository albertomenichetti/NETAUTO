"""Domain exceptions for object models, validation, and persistence."""


class InvalidObject(Exception):
    """Raised when an object has invalid local state."""


class InvalidComponentMembership(Exception):
    """Raised when a component membership has invalid local state."""


class ObjectAlreadyExists(Exception):
    """Raised when an object UUID already exists in persistence."""


class ObjectNotFound(Exception):
    """Raised when a required object does not exist in persistence."""


class ComponentMembershipAlreadyExists(Exception):
    """Raised when a child object already has a stored ownership edge."""


class ComponentMembershipNotFound(Exception):
    """Raised when a required ownership edge does not exist in persistence."""


class ObjectDataTypeVersionNotFound(Exception):
    """Raised when a referenced datatype version cannot be found during validation."""


class ObjectPersistenceError(Exception):
    """Raised when persisted object or membership state cannot be mapped safely."""
