"""Domain exceptions for relationship definitions and runtime relationships."""


class InvalidRelationshipDefinition(Exception):
    """Raised when a relationship definition has invalid local state."""


class InvalidRelationshipIdentifier(Exception):
    """Raised when a relationship semantic identifier is invalid."""


class RelationshipDefinitionAlreadyExists(Exception):
    """Raised when a relationship definition UUID already exists in persistence."""


class RelationshipDefinitionNotFound(Exception):
    """Raised when a required relationship definition does not exist."""


class RelationshipDefinitionTemplateNotFound(Exception):
    """Raised when a referenced endpoint object template identity does not exist."""


class RelationshipDefinitionTemplateNotPublished(Exception):
    """Raised when a referenced endpoint object template has no published version."""


class RelationshipDefinitionSemanticConflict(Exception):
    """Raised when a relationship definition conflicts semantically with an existing one."""


class RelationshipDefinitionPersistenceError(Exception):
    """Raised when persisted relationship definition state cannot be mapped safely."""


class RelationshipDefinitionInUse(Exception):
    """Raised when a relationship definition is still referenced by runtime relationships."""


class InvalidRelationship(Exception):
    """Raised when a runtime relationship has invalid local state."""


class RelationshipAlreadyExists(Exception):
    """Raised when a runtime relationship UUID or canonical edge already exists."""


class RelationshipNotFound(Exception):
    """Raised when a required runtime relationship does not exist."""


class RelationshipObjectNotFound(Exception):
    """Raised when a referenced endpoint object does not exist."""


class RelationshipEndpointIncompatible(Exception):
    """Raised when an object does not satisfy a relationship definition endpoint."""


class RelationshipPersistenceError(Exception):
    """Raised when persisted runtime relationship state cannot be mapped safely."""
