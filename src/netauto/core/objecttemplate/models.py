"""Domain models for object templates and their versions."""

import re
from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from netauto.core.objecttemplate.exceptions import (
    DuplicateObjectTemplateComponent,
    DuplicateObjectTemplateProperty,
    InvalidObjectTemplate,
    InvalidObjectTemplateIdentifier,
    InvalidObjectTemplateProperty,
    InvalidObjectTemplateVersion,
)

_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def _validate_identifier(value: str, field_name: str) -> str:
    if not _IDENTIFIER_PATTERN.fullmatch(value):
        raise InvalidObjectTemplateIdentifier(f"Invalid {field_name}: '{value}'.")
    return value


def _validate_plain_positive_int(value: object, message: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise InvalidObjectTemplateVersion(message)
    return value


class ObjectTemplateVersionStatus(StrEnum):
    """Lifecycle status for an object template version."""

    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"


@dataclass(frozen=True, slots=True)
class ObjectTemplate:
    """Stable identity and qualified name for an object template."""

    id: UUID
    namespace: str
    name: str
    description: str | None = None
    abstract: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "namespace", _validate_identifier(self.namespace, "namespace"))
        object.__setattr__(self, "name", _validate_identifier(self.name, "name"))
        if not isinstance(self.abstract, bool):
            raise InvalidObjectTemplate("ObjectTemplate abstract must be a bool.")

    @property
    def qualified_name(self) -> str:
        """Return the human-readable qualified name."""
        return f"{self.namespace}.{self.name}"


@dataclass(frozen=True, slots=True)
class ObjectTemplateVersionRef:
    """Pinned reference to a specific object template version."""

    template_id: UUID
    version: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "version",
            _validate_plain_positive_int(
                self.version,
                f"Invalid version '{self.version}'. ObjectTemplateVersionRef must be >= 1.",
            ),
        )


@dataclass(frozen=True, slots=True)
class ObjectTemplateProperty:
    """Local property declaration for an object template version."""

    name: str
    datatype_id: UUID
    datatype_version: int
    required: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _validate_identifier(self.name, "property name"))
        if not isinstance(self.required, bool):
            raise InvalidObjectTemplateProperty("ObjectTemplateProperty required must be a bool.")
        if isinstance(self.datatype_version, bool) or not isinstance(self.datatype_version, int):
            raise InvalidObjectTemplateProperty(
                "ObjectTemplateProperty datatype_version must be an integer >= 1."
            )
        if self.datatype_version < 1:
            raise InvalidObjectTemplateProperty(
                f"Invalid datatype_version '{self.datatype_version}'. "
                "ObjectTemplateProperty datatype_version must be >= 1."
            )


@dataclass(frozen=True, slots=True)
class ObjectTemplateComponent:
    """Local structural component slot declaration for an object template version."""

    name: str
    template_id: UUID

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _validate_identifier(self.name, "component name"))


@dataclass(frozen=True, slots=True)
class ObjectTemplateVersion:
    """Versioned object template schema metadata."""

    template_id: UUID
    version: int
    status: ObjectTemplateVersionStatus
    parent: ObjectTemplateVersionRef | None = None
    properties: tuple[ObjectTemplateProperty, ...] = ()
    components: tuple[ObjectTemplateComponent, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "version",
            _validate_plain_positive_int(
                self.version,
                f"Invalid version '{self.version}'. ObjectTemplateVersion must be >= 1.",
            ),
        )
        normalized_properties = tuple(self.properties)
        seen_names: set[str] = set()
        for prop in normalized_properties:
            if prop.name in seen_names:
                raise DuplicateObjectTemplateProperty(
                    f"Duplicate property '{prop.name}' is not allowed."
                )
            seen_names.add(prop.name)
        object.__setattr__(self, "properties", normalized_properties)

        normalized_components = tuple(self.components)
        seen_component_names: set[str] = set()
        for component in normalized_components:
            if component.name in seen_component_names:
                raise DuplicateObjectTemplateComponent(
                    f"Duplicate component '{component.name}' is not allowed."
                )
            seen_component_names.add(component.name)
        object.__setattr__(self, "components", normalized_components)
