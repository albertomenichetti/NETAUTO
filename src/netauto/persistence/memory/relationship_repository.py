"""In-memory relationship definition repository implementation."""

from uuid import UUID

from netauto.core.relationship import (
    RelationshipDefinition,
    RelationshipDefinitionAlreadyExists,
    RelationshipDefinitionNotFound,
    RelationshipDefinitionRepository,
)


class InMemoryRelationshipDefinitionRepository(RelationshipDefinitionRepository):
    """Reference in-memory relationship definition repository."""

    def __init__(self) -> None:
        self._definitions: dict[UUID, RelationshipDefinition] = {}

    def list(self) -> tuple[RelationshipDefinition, ...]:
        definitions = list(self._definitions.values())
        definitions.sort(key=lambda item: str(item.id))
        return tuple(definitions)

    def add(self, definition: RelationshipDefinition) -> None:
        if definition.id in self._definitions:
            raise RelationshipDefinitionAlreadyExists(
                "RelationshipDefinition UUID already exists."
            )
        self._definitions[definition.id] = definition

    def get(self, definition_id: UUID) -> RelationshipDefinition | None:
        return self._definitions.get(definition_id)

    def delete(self, definition_id: UUID) -> None:
        if definition_id not in self._definitions:
            raise RelationshipDefinitionNotFound("RelationshipDefinition does not exist.")
        del self._definitions[definition_id]
