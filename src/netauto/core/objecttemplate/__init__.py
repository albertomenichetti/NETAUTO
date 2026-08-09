"""Object template domain models."""

from netauto.core.objecttemplate.exceptions import (
    DuplicateObjectTemplateProperty,
    InheritedObjectTemplatePropertyConflict,
    InvalidObjectTemplate,
    InvalidObjectTemplateIdentifier,
    InvalidObjectTemplateProperty,
    InvalidObjectTemplateVersion,
    InvalidObjectTemplateVersionTransition,
    MismatchedObjectTemplateVersion,
    ObjectTemplateAlreadyExists,
    ObjectTemplateDataTypeVersionNotFound,
    ObjectTemplateDataTypeVersionNotPublished,
    ObjectTemplateInheritanceCycle,
    ObjectTemplateNotFound,
    ObjectTemplateParentNotFound,
    ObjectTemplateParentNotPublished,
    ObjectTemplateSelfInheritance,
    ObjectTemplateVersionAlreadyExists,
    ObjectTemplateVersionNotFound,
)
from netauto.core.objecttemplate.models import (
    ObjectTemplate,
    ObjectTemplateProperty,
    ObjectTemplateVersion,
    ObjectTemplateVersionRef,
    ObjectTemplateVersionStatus,
)
from netauto.core.objecttemplate.repository import ObjectTemplateRepository
from netauto.core.objecttemplate.resolver import (
    ObjectTemplateInheritanceResolver,
    ObjectTemplateVersionLookup,
)
from netauto.core.objecttemplate.versioning import (
    DataTypeVersionLookup,
    ObjectTemplateVersioningService,
)

__all__ = [
    "DuplicateObjectTemplateProperty",
    "InheritedObjectTemplatePropertyConflict",
    "InvalidObjectTemplate",
    "InvalidObjectTemplateIdentifier",
    "InvalidObjectTemplateProperty",
    "InvalidObjectTemplateVersion",
    "InvalidObjectTemplateVersionTransition",
    "MismatchedObjectTemplateVersion",
    "ObjectTemplateAlreadyExists",
    "ObjectTemplate",
    "ObjectTemplateDataTypeVersionNotFound",
    "ObjectTemplateDataTypeVersionNotPublished",
    "ObjectTemplateInheritanceCycle",
    "ObjectTemplateInheritanceResolver",
    "ObjectTemplateNotFound",
    "ObjectTemplateParentNotFound",
    "ObjectTemplateParentNotPublished",
    "ObjectTemplateRepository",
    "ObjectTemplateSelfInheritance",
    "ObjectTemplateProperty",
    "ObjectTemplateVersion",
    "ObjectTemplateVersionAlreadyExists",
    "ObjectTemplateVersionLookup",
    "ObjectTemplateVersionNotFound",
    "ObjectTemplateVersionRef",
    "ObjectTemplateVersionStatus",
    "ObjectTemplateVersioningService",
    "DataTypeVersionLookup",
]
