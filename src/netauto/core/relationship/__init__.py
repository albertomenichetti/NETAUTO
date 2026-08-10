"""Relationship definition and runtime relationship domain models."""

from netauto.core.relationship.conflicts import (
    RelationshipDefinitionConflictSnapshot,
    ensure_relationship_definition_does_not_conflict,
    ensure_relationship_definition_set_has_no_conflicts,
    relationship_definitions_conflict,
)
from netauto.core.relationship.exceptions import (
    InvalidRelationship,
    InvalidRelationshipDefinition,
    InvalidRelationshipIdentifier,
    RelationshipAlreadyExists,
    RelationshipDefinitionAlreadyExists,
    RelationshipDefinitionNotFound,
    RelationshipDefinitionPersistenceError,
    RelationshipDefinitionSemanticConflict,
    RelationshipDefinitionTemplateNotFound,
    RelationshipDefinitionTemplateNotPublished,
    RelationshipEndpointIncompatible,
    RelationshipNotFound,
    RelationshipObjectNotFound,
    RelationshipPersistenceError,
)
from netauto.core.relationship.models import Relationship, RelationshipDefinition
from netauto.core.relationship.repository import (
    RelationshipDefinitionRepository,
    RelationshipRepository,
)
from netauto.core.relationship.semantics import (
    relationship_definition_applies,
    relationship_definitions_are_semantically_equivalent,
)

__all__ = [
    "InvalidRelationship",
    "InvalidRelationshipDefinition",
    "InvalidRelationshipIdentifier",
    "Relationship",
    "RelationshipAlreadyExists",
    "RelationshipDefinition",
    "RelationshipDefinitionAlreadyExists",
    "RelationshipDefinitionConflictSnapshot",
    "RelationshipDefinitionNotFound",
    "RelationshipDefinitionPersistenceError",
    "RelationshipDefinitionRepository",
    "RelationshipDefinitionSemanticConflict",
    "RelationshipDefinitionTemplateNotPublished",
    "RelationshipDefinitionTemplateNotFound",
    "RelationshipEndpointIncompatible",
    "RelationshipNotFound",
    "RelationshipObjectNotFound",
    "RelationshipPersistenceError",
    "RelationshipRepository",
    "ensure_relationship_definition_does_not_conflict",
    "ensure_relationship_definition_set_has_no_conflicts",
    "relationship_definition_applies",
    "relationship_definitions_conflict",
    "relationship_definitions_are_semantically_equivalent",
]
