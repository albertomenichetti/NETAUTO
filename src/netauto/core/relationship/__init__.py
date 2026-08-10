"""Relationship definition domain models."""

from netauto.core.relationship.exceptions import (
    InvalidRelationshipDefinition,
    InvalidRelationshipIdentifier,
    RelationshipDefinitionAlreadyExists,
    RelationshipDefinitionNotFound,
    RelationshipDefinitionPersistenceError,
    RelationshipDefinitionSemanticConflict,
    RelationshipDefinitionTemplateNotFound,
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
    "RelationshipDefinitionNotFound",
    "RelationshipDefinitionPersistenceError",
    "RelationshipDefinitionRepository",
    "RelationshipDefinitionSemanticConflict",
    "RelationshipDefinitionTemplateNotFound",
    "relationship_definition_applies",
    "relationship_definitions_are_semantically_equivalent",
]
