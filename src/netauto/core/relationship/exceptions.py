"""Domain exceptions for relationship definitions and semantics."""


class InvalidRelationshipDefinition(Exception):
    """Raised when a relationship definition has invalid local state."""


class InvalidRelationshipIdentifier(Exception):
    """Raised when a relationship semantic identifier is invalid."""
