"""Domain exceptions for object template domain models."""


class InvalidObjectTemplate(Exception):
    """Raised when an object template has invalid local state."""


class InvalidObjectTemplateIdentifier(Exception):
    """Raised when an object template namespace, name, or property name is invalid."""


class InvalidObjectTemplateVersion(Exception):
    """Raised when an object template version number is invalid."""


class InvalidObjectTemplateProperty(Exception):
    """Raised when an object template property has invalid local state."""


class InvalidObjectTemplateComponent(Exception):
    """Raised when an object template component has invalid local state."""


class DuplicateObjectTemplateProperty(Exception):
    """Raised when a template version contains duplicate local property names."""


class DuplicateObjectTemplateComponent(Exception):
    """Raised when a template version contains duplicate local component names."""


class ObjectTemplateParentNotFound(Exception):
    """Raised when a referenced parent template version cannot be found."""


class ObjectTemplateInheritanceCycle(Exception):
    """Raised when object template inheritance contains a cycle."""


class ObjectTemplateSelfInheritance(Exception):
    """Raised when a template version declares a parent from the same template identity."""


class InheritedObjectTemplatePropertyConflict(Exception):
    """Raised when a local property conflicts with an inherited property name."""


class InheritedObjectTemplateComponentConflict(Exception):
    """Raised when a local component conflicts with an inherited component name."""


class InvalidObjectTemplateVersionTransition(Exception):
    """Raised when an object template version lifecycle transition is invalid."""


class MismatchedObjectTemplateVersion(Exception):
    """Raised when versions from different object templates are mixed."""


class ObjectTemplateDataTypeVersionNotFound(Exception):
    """Raised when a referenced datatype version cannot be found."""


class ObjectTemplateDataTypeVersionNotPublished(Exception):
    """Raised when a referenced datatype version is not published."""


class ObjectTemplateDataTypeVersionDowngrade(Exception):
    """Raised when a property is revised to an older version of the same datatype."""


class ObjectTemplateComponentVersionNotFound(Exception):
    """Raised when a referenced component target template cannot be found."""


class ObjectTemplateComponentVersionNotPublished(Exception):
    """Raised when a referenced component target template has no published version."""


class ObjectTemplateParentNotPublished(Exception):
    """Raised when a referenced parent object template version is not published."""


class ObjectTemplateAlreadyExists(Exception):
    """Raised when an object template identity or logical name already exists."""


class ObjectTemplateNotFound(Exception):
    """Raised when a required object template does not exist."""


class ObjectTemplateInUse(Exception):
    """Raised when an object template identity is still referenced."""


class ObjectTemplateVersionAlreadyExists(Exception):
    """Raised when an object template version identity already exists."""


class ObjectTemplateVersionNotFound(Exception):
    """Raised when a required object template version does not exist."""


class ObjectTemplatePersistenceError(Exception):
    """Raised when persisted object template state cannot be mapped safely."""
