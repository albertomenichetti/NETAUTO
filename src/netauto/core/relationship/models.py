"""Domain models for relationship definitions and runtime relationships."""

import re
from dataclasses import dataclass
from uuid import UUID

from netauto.core.relationship.exceptions import (
    InvalidRelationship,
    InvalidRelationshipDefinition,
    InvalidRelationshipIdentifier,
)

_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def _validate_identifier(value: str, field_name: str) -> str:
    if not _IDENTIFIER_PATTERN.fullmatch(value):
        raise InvalidRelationshipIdentifier(f"Invalid {field_name}: '{value}'.")
    return value


@dataclass(frozen=True, slots=True)
class RelationshipDefinition:
    """Canonical semantic relationship definition between two template identities."""

    id: UUID
    source_template_id: UUID
    target_template_id: UUID
    forward_name: str
    reverse_name: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "forward_name",
            _validate_identifier(self.forward_name, "relationship forward_name"),
        )
        object.__setattr__(
            self,
            "reverse_name",
            _validate_identifier(self.reverse_name, "relationship reverse_name"),
        )
        for field_name in ("source_template_id", "target_template_id"):
            if not isinstance(getattr(self, field_name), UUID):
                raise InvalidRelationshipDefinition(
                    f"RelationshipDefinition {field_name} must be a UUID."
                )


@dataclass(frozen=True, slots=True)
class Relationship:
    """Canonical immutable runtime relationship edge."""

    id: UUID
    relationship_definition_id: UUID
    source_object_id: UUID
    target_object_id: UUID

    def __post_init__(self) -> None:
        for field_name in (
            "id",
            "relationship_definition_id",
            "source_object_id",
            "target_object_id",
        ):
            if not isinstance(getattr(self, field_name), UUID):
                raise InvalidRelationship(f"Relationship {field_name} must be a UUID.")
