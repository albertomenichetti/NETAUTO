"""Domain exceptions for relationship definitions and semantics."""


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
