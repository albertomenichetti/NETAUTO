"""Domain exceptions for object template domain models."""


class InvalidObjectTemplate(Exception):
    """Raised when an object template has invalid local state."""


class InvalidObjectTemplateIdentifier(Exception):
    """Raised when an object template namespace, name, or property name is invalid."""


class InvalidObjectTemplateVersion(Exception):
    """Raised when an object template version number is invalid."""


class InvalidObjectTemplateProperty(Exception):
    """Raised when an object template property has invalid local state."""


class DuplicateObjectTemplateProperty(Exception):
    """Raised when a template version contains duplicate local property names."""


class ObjectTemplateParentNotFound(Exception):
    """Raised when a referenced parent template version cannot be found."""


class ObjectTemplateInheritanceCycle(Exception):
    """Raised when object template inheritance contains a cycle."""


class InheritedObjectTemplatePropertyConflict(Exception):
    """Raised when a local property conflicts with an inherited property name."""
