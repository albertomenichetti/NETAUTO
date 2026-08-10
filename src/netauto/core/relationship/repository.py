"""Persistence-neutral repository contract for relationship definitions."""

from typing import Protocol
from uuid import UUID

from netauto.core.relationship.models import RelationshipDefinition


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
