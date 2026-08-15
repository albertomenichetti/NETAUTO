"""Plain-Python ObjectTemplate aggregate and effective-schema semantics."""

import re
from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from netauto.domain.datatypes import VersionStatus
from netauto.domain.primitives import JsonValue

_IDENTIFIER = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")


class ValueMode(StrEnum):
    SCALAR = "SCALAR"
    LIST = "LIST"


@dataclass(frozen=True, slots=True)
class ObjectTemplate:
    id: UUID
    namespace: str
    name: str
    description: str | None
    abstract: bool
    parent_template_id: UUID | None
    default_version: int | None


@dataclass(frozen=True, slots=True)
class LocalProperty:
    name: str
    position: int
    datatype_id: UUID
    datatype_version: int
    value_mode: ValueMode
    required: bool
    migration_default: JsonValue | None


@dataclass(frozen=True, slots=True)
class LocalComponent:
    name: str
    position: int
    target_template_id: UUID


@dataclass(frozen=True, slots=True)
class ObjectTemplateVersion:
    template_id: UUID
    version: int
    revision: int
    status: VersionStatus
    parent_template_id: UUID | None
    parent_version: int | None
    properties: tuple[LocalProperty, ...]
    components: tuple[LocalComponent, ...]


@dataclass(frozen=True, slots=True)
class ObjectTemplateVersionSummary:
    template_id: UUID
    version: int
    revision: int
    status: VersionStatus
    parent_template_id: UUID | None
    parent_version: int | None


@dataclass(frozen=True, slots=True)
class EffectiveProperty:
    declaring_template_id: UUID
    declaration: LocalProperty


@dataclass(frozen=True, slots=True)
class EffectiveComponent:
    declaring_template_id: UUID
    declaration: LocalComponent


@dataclass(frozen=True, slots=True)
class EffectiveSchema:
    template_id: UUID
    version: int
    properties: tuple[EffectiveProperty, ...]
    components: tuple[EffectiveComponent, ...]


@dataclass(frozen=True, slots=True)
class CreateObjectTemplateResult:
    object_template: ObjectTemplate
    version: ObjectTemplateVersion


class ObjectTemplateValidationError(ValueError):
    def __init__(self, path: str, rule: str) -> None:
        self.path = path
        self.rule = rule
        super().__init__(f"{path}: {rule}")


def validate_member_name(name: str, path: str) -> None:
    if _IDENTIFIER.fullmatch(name) is None:
        raise ObjectTemplateValidationError(path, "invalid_identifier")


def validate_local_declarations(
    properties: tuple[LocalProperty, ...], components: tuple[LocalComponent, ...]
) -> None:
    property_names: set[str] = set()
    property_positions: set[int] = set()
    for item in properties:
        validate_member_name(item.name, f"properties.{item.name}.name")
        if item.position <= 0 or item.position in property_positions:
            raise ObjectTemplateValidationError(
                f"properties.{item.name}.position", "duplicate_or_invalid_position"
            )
        if item.name in property_names:
            raise ObjectTemplateValidationError(
                f"properties.{item.name}.name", "duplicate_member_name"
            )
        property_names.add(item.name)
        property_positions.add(item.position)

    component_names: set[str] = set()
    component_positions: set[int] = set()
    for item in components:
        validate_member_name(item.name, f"components.{item.name}.name")
        if item.position <= 0 or item.position in component_positions:
            raise ObjectTemplateValidationError(
                f"components.{item.name}.position", "duplicate_or_invalid_position"
            )
        if item.name in component_names or item.name in property_names:
            raise ObjectTemplateValidationError(
                f"components.{item.name}.name", "duplicate_member_name"
            )
        component_names.add(item.name)
        component_positions.add(item.position)


def resolve_effective_schema(
    template_id: UUID,
    version: int,
    root_to_leaf: tuple[ObjectTemplateVersion, ...],
) -> EffectiveSchema:
    seen_templates: set[UUID] = set()
    seen_members: set[str] = set()
    properties: list[EffectiveProperty] = []
    components: list[EffectiveComponent] = []
    for snapshot in root_to_leaf:
        if snapshot.template_id in seen_templates:
            raise ObjectTemplateValidationError("inheritance", "inheritance_cycle")
        seen_templates.add(snapshot.template_id)
        validate_local_declarations(snapshot.properties, snapshot.components)
        for item in sorted(snapshot.properties, key=lambda value: value.position):
            if item.name in seen_members:
                raise ObjectTemplateValidationError(
                    f"properties.{item.name}", "inherited_member_collision"
                )
            seen_members.add(item.name)
            properties.append(EffectiveProperty(snapshot.template_id, item))
        for item in sorted(snapshot.components, key=lambda value: value.position):
            if item.name in seen_members:
                raise ObjectTemplateValidationError(
                    f"components.{item.name}", "inherited_member_collision"
                )
            seen_members.add(item.name)
            components.append(EffectiveComponent(snapshot.template_id, item))
    return EffectiveSchema(template_id, version, tuple(properties), tuple(components))
