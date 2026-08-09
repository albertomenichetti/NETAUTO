"""Object domain models."""

from netauto.core.object.exceptions import (
    AbstractObjectTemplateInstantiation,
    ComponentMembershipAlreadyExists,
    ComponentMembershipNotFound,
    InvalidComponentMembership,
    InvalidObject,
    InvalidObjectPatch,
    ObjectAlreadyExists,
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
    "ComponentMembershipAlreadyExists",
    "ComponentMembershipNotFound",
    "DataTypeVersionLookup",
    "InvalidObjectPatch",
    "InvalidComponentMembership",
    "InvalidObject",
    "Object",
    "ObjectAlreadyExists",
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
