"""In-memory relationship repository implementations."""

from collections.abc import Collection
from uuid import UUID

from netauto.core.relationship import (
    Relationship,
    RelationshipAlreadyExists,
    RelationshipDefinition,
    RelationshipDefinitionAlreadyExists,
    RelationshipDefinitionNotFound,
    RelationshipDefinitionRepository,
    RelationshipNotFound,
    RelationshipRepository,
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


class InMemoryRelationshipRepository(RelationshipRepository):
    """Reference in-memory runtime relationship repository."""

    def __init__(self) -> None:
        self._relationships: dict[UUID, Relationship] = {}
        self._ids_by_endpoints: dict[tuple[UUID, UUID, UUID], UUID] = {}

    def list(self) -> tuple[Relationship, ...]:
        relationships = list(self._relationships.values())
        relationships.sort(key=lambda item: str(item.id))
        return tuple(relationships)

    def get(self, relationship_id: UUID) -> Relationship | None:
        return self._relationships.get(relationship_id)

    def get_by_endpoints(
        self,
        relationship_definition_id: UUID,
        source_object_id: UUID,
        target_object_id: UUID,
    ) -> Relationship | None:
        relationship_id = self._ids_by_endpoints.get(
            (relationship_definition_id, source_object_id, target_object_id)
        )
        if relationship_id is None:
            return None
        return self._relationships.get(relationship_id)

    def add(self, relationship: Relationship) -> None:
        endpoint_key = (
            relationship.relationship_definition_id,
            relationship.source_object_id,
            relationship.target_object_id,
        )
        if relationship.id in self._relationships or endpoint_key in self._ids_by_endpoints:
            raise RelationshipAlreadyExists("Relationship already exists.")
        self._relationships[relationship.id] = relationship
        self._ids_by_endpoints[endpoint_key] = relationship.id

    def list_by_definition(
        self,
        relationship_definition_id: UUID,
    ) -> tuple[Relationship, ...]:
        relationships = [
            relationship
            for relationship in self._relationships.values()
            if relationship.relationship_definition_id == relationship_definition_id
        ]
        relationships.sort(key=lambda item: str(item.id))
        return tuple(relationships)

    def list_incident_to_objects(
        self,
        object_ids: Collection[UUID],
    ) -> tuple[Relationship, ...]:
        object_id_set = set(object_ids)
        relationships = [
            relationship
            for relationship in self._relationships.values()
            if relationship.source_object_id in object_id_set
            or relationship.target_object_id in object_id_set
        ]
        relationships.sort(key=lambda item: str(item.id))
        return tuple(relationships)

    def delete(self, relationship_id: UUID) -> None:
        relationship = self._relationships.get(relationship_id)
        if relationship is None:
            raise RelationshipNotFound("Relationship does not exist.")
        endpoint_key = (
            relationship.relationship_definition_id,
            relationship.source_object_id,
            relationship.target_object_id,
        )
        del self._relationships[relationship_id]
        del self._ids_by_endpoints[endpoint_key]
