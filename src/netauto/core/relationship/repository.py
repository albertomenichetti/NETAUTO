"""Persistence-neutral repository contracts for relationships."""

from typing import Protocol
from uuid import UUID

from netauto.core.relationship.models import Relationship, RelationshipDefinition


class RelationshipDefinitionRepository(Protocol):
    """Repository contract for relationship definition persistence."""

    def list(self) -> tuple[RelationshipDefinition, ...]:
        """Return all relationship definitions ordered deterministically."""
        ...

    def add(self, definition: RelationshipDefinition) -> None:
        """Persist a new relationship definition."""
        ...

    def get(self, definition_id: UUID) -> RelationshipDefinition | None:
        """Return a relationship definition by UUID or None."""
        ...

    def delete(self, definition_id: UUID) -> None:
        """Delete a relationship definition by UUID."""
        ...


class RelationshipRepository(Protocol):
    """Repository contract for runtime relationship persistence."""

    def list(self) -> tuple[Relationship, ...]:
        """Return all runtime relationships ordered deterministically."""
        ...

    def get(self, relationship_id: UUID) -> Relationship | None:
        """Return a runtime relationship by UUID or None."""
        ...

    def get_by_endpoints(
        self,
        relationship_definition_id: UUID,
        source_object_id: UUID,
        target_object_id: UUID,
    ) -> Relationship | None:
        """Return a runtime relationship by canonical definition/source/target triple."""
        ...

    def add(self, relationship: Relationship) -> None:
        """Persist a new runtime relationship."""
        ...

    def delete(self, relationship_id: UUID) -> None:
        """Delete a runtime relationship by UUID."""
        ...
