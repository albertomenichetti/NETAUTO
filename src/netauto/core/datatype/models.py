"""Domain models for user-defined datatypes and their versions."""

import re
from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from netauto.core.datatype.exceptions import (
    InvalidDataTypeIdentifier,
    InvalidDataTypeVersion,
)
from netauto.core.datatype.primitives import PrimitiveType

_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def _validate_identifier(value: str, field_name: str) -> str:
    if not _IDENTIFIER_PATTERN.fullmatch(value):
        raise InvalidDataTypeIdentifier(f"Invalid {field_name}: '{value}'.")
    return value


class DataTypeVersionStatus(StrEnum):
    """Lifecycle status for a datatype version."""

    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"


@dataclass(frozen=True, slots=True)
class DataType:
    """Stable identity and human-readable name for a user-defined datatype."""

    id: UUID
    namespace: str
    name: str
    description: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "namespace", _validate_identifier(self.namespace, "namespace"))
        object.__setattr__(self, "name", _validate_identifier(self.name, "name"))

    @property
    def qualified_name(self) -> str:
        """Return the human-readable qualified name."""
        return f"{self.namespace}.{self.name}"


@dataclass(slots=True)
class DataTypeVersion:
    """Versioned schema metadata for a datatype."""

    datatype_id: UUID
    version: int
    status: DataTypeVersionStatus
    base_type: PrimitiveType

    def __post_init__(self) -> None:
        if self.version < 1:
            raise InvalidDataTypeVersion(
                f"Invalid version '{self.version}'. DataTypeVersion must be >= 1."
            )
