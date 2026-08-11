"""Domain exceptions for object models, validation, persistence, and workflows."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from netauto.core.object.validation import ObjectValidationResult


class InvalidObject(Exception):
    """Raised when an object has invalid local state."""


class InvalidObjectChange(Exception):
    """Raised when an object change or change snapshot has invalid local state."""


class InvalidComponentMembership(Exception):
    """Raised when a component membership has invalid local state."""


class ObjectAlreadyExists(Exception):
    """Raised when an object UUID already exists in persistence."""


class ObjectChangeAlreadyExists(Exception):
    """Raised when an object change UUID already exists in persistence."""


class ObjectNotFound(Exception):
    """Raised when a required object does not exist in persistence."""


class ObjectConcurrentModification(Exception):
    """Raised when an Object snapshot is stale at conditional write time."""


class ComponentMembershipAlreadyExists(Exception):
    """Raised when a child object already has a stored ownership edge."""


class ComponentMembershipNotFound(Exception):
    """Raised when a required ownership edge does not exist in persistence."""


class ObjectDataTypeVersionNotFound(Exception):
    """Raised when a referenced datatype version cannot be found during validation."""


class ObjectPersistenceError(Exception):
    """Raised when persisted object or membership state cannot be mapped safely."""


class ObjectTemplateVersionNotPublished(Exception):
    """Raised when a new object targets a non-published template version."""


class AbstractObjectTemplateInstantiation(Exception):
    """Raised when direct instantiation of an abstract template is attempted."""


class ObjectValidationFailed(Exception):
    """Raised when object properties fail semantic validation."""

    def __init__(self, result: ObjectValidationResult) -> None:
        self.result = result
        super().__init__("Object validation failed.")


class InvalidObjectPatch(Exception):
    """Raised when an object patch request is internally inconsistent."""


class ObjectComponentSlotNotFound(Exception):
    """Raised when a requested component slot is not declared by the parent template."""


class ObjectComponentTemplateIncompatible(Exception):
    """Raised when a child object's pinned template is incompatible with a slot target."""


class ComponentOwnershipCycle(Exception):
    """Raised when a structural ownership change would create an ownership cycle."""


class ObjectMigrationTargetVersionNotPublished(Exception):
    """Raised when automatic migration targets a non-published template version."""


class ObjectMigrationTargetVersionNotNewer(Exception):
    """Raised when automatic migration does not target a newer template version."""


class ObjectMigrationBlocked(Exception):
    """Raised when structural migration analysis contains blocking changes."""


class MissingObjectMigrationPropertyValue(Exception):
    """Raised when a new required target property lacks a migration-supplied value."""


class UnexpectedObjectMigrationPropertyValue(Exception):
    """Raised when migration supplies a value for a property outside the additive delta."""
