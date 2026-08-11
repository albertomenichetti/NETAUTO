"""Domain models for runtime objects, change history, and structural membership."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType
from uuid import UUID

from netauto.core.object.exceptions import (
    InvalidComponentMembership,
    InvalidObject,
    InvalidObjectChange,
)


def _validate_plain_positive_int(value: object, message: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise InvalidObject(message)
    return value


def _validate_plain_positive_int_for_change(value: object, message: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise InvalidObjectChange(message)
    return value


def _snapshot_properties(
    properties: Mapping[str, object],
    *,
    error_factory: type[InvalidObject] | type[InvalidObjectChange],
    mapping_message: str,
    key_message: str,
) -> Mapping[str, object]:
    if not isinstance(properties, Mapping):
        raise error_factory(mapping_message)

    snapshot: dict[str, object] = {}
    for key, value in properties.items():
        if not isinstance(key, str):
            raise error_factory(key_message)
        snapshot[key] = value

    return MappingProxyType(snapshot)


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
        object.__setattr__(
            self,
            "properties",
            _snapshot_properties(
                self.properties,
                error_factory=InvalidObject,
                mapping_message="Object properties must be a mapping.",
                key_message="Object property names must be strings.",
            ),
        )


class ObjectChangeKind(StrEnum):
    """Kinds of append-only runtime object history entries."""

    CREATED = "created"
    UPDATED = "updated"
    MIGRATED = "migrated"
    DELETED = "deleted"


@dataclass(frozen=True, slots=True)
class ObjectChangeSnapshot:
    """Immutable runtime object snapshot embedded in history."""

    template_id: UUID
    template_version: int
    properties: Mapping[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "template_version",
            _validate_plain_positive_int_for_change(
                self.template_version,
                (
                    f"Invalid template_version '{self.template_version}'. "
                    "Object change snapshot template_version must be >= 1."
                ),
            ),
        )
        object.__setattr__(
            self,
            "properties",
            _snapshot_properties(
                self.properties,
                error_factory=InvalidObjectChange,
                mapping_message="Object change snapshot properties must be a mapping.",
                key_message="Object change snapshot property names must be strings.",
            ),
        )


@dataclass(frozen=True, slots=True)
class ObjectChange:
    """Immutable append-only runtime object history entry."""

    id: UUID
    object_id: UUID
    occurred_at: datetime
    kind: ObjectChangeKind
    before: ObjectChangeSnapshot | None
    after: ObjectChangeSnapshot | None

    def __post_init__(self) -> None:
        if (
            self.occurred_at.tzinfo is None
            or self.occurred_at.tzinfo.utcoffset(self.occurred_at) is None
        ):
            raise InvalidObjectChange("Object change occurred_at must be timezone-aware.")

        if self.kind is ObjectChangeKind.CREATED:
            if self.before is not None or self.after is None:
                raise InvalidObjectChange(
                    "Created object changes must have before=None and after set."
                )
        elif self.kind in (ObjectChangeKind.UPDATED, ObjectChangeKind.MIGRATED):
            if self.before is None or self.after is None:
                raise InvalidObjectChange(
                    "Updated and migrated object changes must have both before and after."
                )
        elif self.kind is ObjectChangeKind.DELETED:
            if self.before is None or self.after is not None:
                raise InvalidObjectChange(
                    "Deleted object changes must have before set and after=None."
                )
        else:
            raise InvalidObjectChange("Object change kind is invalid.")


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
