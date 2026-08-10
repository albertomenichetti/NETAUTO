"""Relationship definition domain models."""

from netauto.core.relationship.conflicts import (
    RelationshipDefinitionConflictSnapshot,
    ensure_relationship_definition_does_not_conflict,
    ensure_relationship_definition_set_has_no_conflicts,
    relationship_definitions_conflict,
)
from netauto.core.relationship.exceptions import (
    InvalidRelationshipDefinition,
    InvalidRelationshipIdentifier,
    RelationshipDefinitionAlreadyExists,
    RelationshipDefinitionNotFound,
    RelationshipDefinitionPersistenceError,
    RelationshipDefinitionSemanticConflict,
    RelationshipDefinitionTemplateNotFound,
    RelationshipDefinitionTemplateNotPublished,
)
from netauto.core.relationship.models import RelationshipDefinition
from netauto.core.relationship.repository import RelationshipDefinitionRepository
from netauto.core.relationship.semantics import (
    relationship_definition_applies,
    relationship_definitions_are_semantically_equivalent,
)

__all__ = [
    "InvalidRelationshipDefinition",
    "InvalidRelationshipIdentifier",
    "RelationshipDefinition",
    "RelationshipDefinitionAlreadyExists",
    "RelationshipDefinitionConflictSnapshot",
    "RelationshipDefinitionNotFound",
    "RelationshipDefinitionPersistenceError",
    "RelationshipDefinitionRepository",
    "RelationshipDefinitionSemanticConflict",
    "RelationshipDefinitionTemplateNotPublished",
    "RelationshipDefinitionTemplateNotFound",
    "ensure_relationship_definition_does_not_conflict",
    "ensure_relationship_definition_set_has_no_conflicts",
    "relationship_definition_applies",
    "relationship_definitions_conflict",
    "relationship_definitions_are_semantically_equivalent",
]
