"""Object template domain models."""

from netauto.core.objecttemplate.exceptions import (
    DuplicateObjectTemplateProperty,
    InheritedObjectTemplatePropertyConflict,
    InvalidObjectTemplate,
    InvalidObjectTemplateIdentifier,
    InvalidObjectTemplateProperty,
    InvalidObjectTemplateVersion,
    ObjectTemplateInheritanceCycle,
    ObjectTemplateParentNotFound,
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

__all__ = [
    "DuplicateObjectTemplateProperty",
    "InheritedObjectTemplatePropertyConflict",
    "InvalidObjectTemplate",
    "InvalidObjectTemplateIdentifier",
    "InvalidObjectTemplateProperty",
    "InvalidObjectTemplateVersion",
    "ObjectTemplate",
    "ObjectTemplateInheritanceCycle",
    "ObjectTemplateInheritanceResolver",
    "ObjectTemplateParentNotFound",
    "ObjectTemplateProperty",
    "ObjectTemplateVersion",
    "ObjectTemplateVersionLookup",
    "ObjectTemplateVersionRef",
    "ObjectTemplateVersionStatus",
]
