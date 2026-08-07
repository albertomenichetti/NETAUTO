"""Domain value objects for built-in primitive types."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PrimitiveType:
    """Immutable built-in primitive type."""

    name: str
    json_schema_type: str
