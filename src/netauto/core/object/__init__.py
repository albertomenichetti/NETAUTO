"""Object domain models."""

from netauto.core.object.exceptions import (
    AbstractObjectTemplateInstantiation,
    ComponentMembershipAlreadyExists,
    ComponentMembershipNotFound,
    ComponentOwnershipCycle,
    InvalidComponentMembership,
    InvalidObject,
    InvalidObjectPatch,
    ObjectAlreadyExists,
    ObjectComponentSlotNotFound,
    ObjectComponentTemplateIncompatible,
    ObjectDataTypeVersionNotFound,
    ObjectNotFound,
    ObjectPersistenceError,
    ObjectTemplateVersionNotPublished,
    ObjectValidationFailed,
)
from netauto.core.object.models import ComponentMembership, Object
from netauto.core.object.repository import ObjectRepository
from netauto.core.object.validation import (
    DataTypeVersionLookup,
    ObjectValidationEngine,
    ObjectValidationIssue,
    ObjectValidationResult,
)

__all__ = [
    "AbstractObjectTemplateInstantiation",
    "ComponentMembership",
    "ComponentOwnershipCycle",
    "ComponentMembershipAlreadyExists",
    "ComponentMembershipNotFound",
    "DataTypeVersionLookup",
    "InvalidObjectPatch",
    "InvalidComponentMembership",
    "InvalidObject",
    "Object",
    "ObjectAlreadyExists",
    "ObjectComponentSlotNotFound",
    "ObjectComponentTemplateIncompatible",
    "ObjectDataTypeVersionNotFound",
    "ObjectNotFound",
    "ObjectPersistenceError",
    "ObjectRepository",
    "ObjectTemplateVersionNotPublished",
    "ObjectValidationEngine",
    "ObjectValidationFailed",
    "ObjectValidationIssue",
    "ObjectValidationResult",
]
