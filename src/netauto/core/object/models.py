"""Domain models for runtime objects."""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from uuid import UUID

from netauto.core.object.exceptions import InvalidObject


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
