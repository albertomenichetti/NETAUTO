"""Domain models for runtime objects and structural membership."""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from uuid import UUID

from netauto.core.object.exceptions import InvalidComponentMembership, InvalidObject


def _validate_plain_positive_int(value: object, message: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise InvalidObject(message)
    return value


@dataclass(frozen=True, slots=True)
class Object:
    """Runtime object snapshot pinned to an exact object template version."""

    id: UUID
    template_id: UUID
    template_version: int
    properties: Mapping[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "template_version",
            _validate_plain_positive_int(
                self.template_version,
                (
                    f"Invalid template_version '{self.template_version}'. "
                    "Object template_version must be >= 1."
                ),
            ),
        )
        if not isinstance(self.properties, Mapping):
            raise InvalidObject("Object properties must be a mapping.")

        snapshot: dict[str, object] = {}
        for key, value in self.properties.items():
            if not isinstance(key, str):
                raise InvalidObject("Object property names must be strings.")
            snapshot[key] = value

        object.__setattr__(self, "properties", MappingProxyType(snapshot))


@dataclass(frozen=True, slots=True)
class ComponentMembership:
    """Authoritative structural ownership edge between two objects."""

    parent_object_id: UUID
    slot_name: str
    child_object_id: UUID

    def __post_init__(self) -> None:
        if not isinstance(self.slot_name, str):
            raise InvalidComponentMembership("ComponentMembership slot_name must be a string.")
        if self.slot_name == "":
            raise InvalidComponentMembership("ComponentMembership slot_name must not be empty.")
        if self.parent_object_id == self.child_object_id:
            raise InvalidComponentMembership(
                "ComponentMembership parent_object_id and child_object_id must differ."
            )
