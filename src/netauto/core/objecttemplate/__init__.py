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
    ObjectTemplateDataTypeVersionNotFound,
    ObjectTemplateDataTypeVersionNotPublished,
    ObjectTemplateInheritanceCycle,
    ObjectTemplateParentNotFound,
    ObjectTemplateParentNotPublished,
    ObjectTemplateSelfInheritance,
)
from netauto.core.objecttemplate.models import (
    ObjectTemplate,
    ObjectTemplateProperty,
    ObjectTemplateVersion,
    ObjectTemplateVersionRef,
    ObjectTemplateVersionStatus,
)
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
    "ObjectTemplate",
    "ObjectTemplateDataTypeVersionNotFound",
    "ObjectTemplateDataTypeVersionNotPublished",
    "ObjectTemplateInheritanceCycle",
    "ObjectTemplateInheritanceResolver",
    "ObjectTemplateParentNotFound",
    "ObjectTemplateParentNotPublished",
    "ObjectTemplateSelfInheritance",
    "ObjectTemplateProperty",
    "ObjectTemplateVersion",
    "ObjectTemplateVersionLookup",
    "ObjectTemplateVersionRef",
    "ObjectTemplateVersionStatus",
    "ObjectTemplateVersioningService",
    "DataTypeVersionLookup",
]
