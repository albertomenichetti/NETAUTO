"""Read-only registry for built-in primitive types."""

from types import MappingProxyType

from netauto.core.datatype.exceptions import PrimitiveTypeNotFound
from netauto.core.datatype.primitives import PrimitiveType

_PRIMITIVE_TYPES = {
    "core.string": PrimitiveType(name="core.string", json_schema_type="string"),
    "core.integer": PrimitiveType(name="core.integer", json_schema_type="integer"),
    "core.number": PrimitiveType(name="core.number", json_schema_type="number"),
    "core.boolean": PrimitiveType(name="core.boolean", json_schema_type="boolean"),
    "core.date": PrimitiveType(
        name="core.date",
        json_schema_type="string",
        json_schema_format="date",
    ),
    "core.datetime": PrimitiveType(
        name="core.datetime",
        json_schema_type="string",
        json_schema_format="date-time",
    ),
}


class PrimitiveTypeRegistry:
    """Expose the built-in primitive types without mutation operations."""

    def __init__(self) -> None:
        self._primitive_types = MappingProxyType(_PRIMITIVE_TYPES)

    def get(self, name: str) -> PrimitiveType:
        """Return a built-in primitive type by name."""
        primitive_type = self._primitive_types.get(name)
        if primitive_type is None:
            raise PrimitiveTypeNotFound(f"Primitive type '{name}' was not found.")
        return primitive_type

    def exists(self, name: str) -> bool:
        """Return whether a built-in primitive type exists."""
        return name in self._primitive_types

    def all(self) -> tuple[PrimitiveType, ...]:
        """Return all built-in primitive types."""
        return tuple(self._primitive_types.values())
