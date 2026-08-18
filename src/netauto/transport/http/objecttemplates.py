"""ObjectTemplate HTTP wire DTOs."""

from typing import cast
from uuid import UUID

from pydantic import ConfigDict, Field, model_validator

from netauto.domain.datatypes import VersionStatus
from netauto.domain.objecttemplates import ValueMode
from netauto.domain.primitives import JsonValue
from netauto.transport.http.common import (
    BodyUUID,
    BodyValueMode,
    PositiveInteger,
    StrictBody,
    WireDTO,
)


class PropertyBody(StrictBody):
    name: str
    position: PositiveInteger
    datatype_id: BodyUUID
    datatype_version: PositiveInteger | None = None
    value_mode: BodyValueMode
    required: bool
    migration_default: JsonValue | None = None

    @model_validator(mode="before")
    @classmethod
    def preserve_omission(cls, value: object) -> object:
        if isinstance(value, dict):
            raw = cast(dict[object, object], value)
            if "datatype_version" in raw and raw["datatype_version"] is None:
                raise ValueError("datatype_version_null_forbidden")
            required = raw.get("required")
            has_default = "migration_default" in raw
            if required is True and (
                not has_default or raw.get("migration_default") is None
            ):
                raise ValueError("required_migration_default")
            if required is False and has_default:
                raise ValueError("optional_default_must_be_absent")
            return cast(object, raw)
        return value


class ComponentBody(StrictBody):
    name: str
    position: PositiveInteger
    target_template_id: BodyUUID


class ObjectTemplateCreateBody(StrictBody):
    namespace: str
    name: str
    abstract: bool
    description: str | None = None
    parent_template_id: BodyUUID | None = None
    parent_version: PositiveInteger | None = None
    properties: list[PropertyBody] = Field(default_factory=lambda: list[PropertyBody]())
    components: list[ComponentBody] = Field(
        default_factory=lambda: list[ComponentBody]()
    )

    @model_validator(mode="before")
    @classmethod
    def parent_selector_shape(cls, value: object) -> object:
        if isinstance(value, dict):
            raw = cast(dict[object, object], value)
            if "parent_template_id" in raw and raw["parent_template_id"] is None:
                raise ValueError("parent_template_id_null_forbidden")
            if "parent_version" in raw and raw["parent_version"] is None:
                raise ValueError("parent_version_null_forbidden")
            if "parent_version" in raw and "parent_template_id" not in raw:
                raise ValueError("parent_template_id_required")
            return cast(object, raw)
        return value


class CreateNextBody(StrictBody):
    source_version: PositiveInteger


class ReviseBody(StrictBody):
    parent_version: PositiveInteger | None = None
    properties: list[PropertyBody]
    components: list[ComponentBody]

    @model_validator(mode="before")
    @classmethod
    def parent_version_not_null(cls, value: object) -> object:
        if isinstance(value, dict):
            raw = cast(dict[object, object], value)
            if "parent_version" in raw and raw["parent_version"] is None:
                raise ValueError("parent_version_null_forbidden")
            return cast(object, raw)
        return value


class SetDefaultBody(StrictBody):
    version: PositiveInteger


class SetDescriptionBody(StrictBody):
    description: str | None


class ObjectTemplateDto(WireDTO):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    namespace: str
    name: str
    description: str | None
    abstract: bool
    parent_template_id: UUID | None
    default_version: int | None


class PropertyDto(WireDTO):
    model_config = ConfigDict(from_attributes=True)

    name: str
    position: int
    datatype_id: UUID
    datatype_version: int
    value_mode: ValueMode
    required: bool
    migration_default: JsonValue | None = Field(
        default=None, exclude_if=lambda value: value is None
    )


class ComponentDto(WireDTO):
    model_config = ConfigDict(from_attributes=True)

    name: str
    position: int
    target_template_id: UUID


class ObjectTemplateVersionDto(WireDTO):
    model_config = ConfigDict(from_attributes=True)

    template_id: UUID
    version: int
    revision: int
    status: VersionStatus
    parent_template_id: UUID | None
    parent_version: int | None
    properties: list[PropertyDto]
    components: list[ComponentDto]


class ObjectTemplateVersionSummaryDto(WireDTO):
    model_config = ConfigDict(from_attributes=True)

    template_id: UUID
    version: int
    revision: int
    status: VersionStatus
    parent_template_id: UUID | None
    parent_version: int | None


class EffectivePropertyDto(PropertyDto):
    declaring_template_id: UUID


class EffectiveComponentDto(ComponentDto):
    declaring_template_id: UUID


class EffectiveSchemaDto(WireDTO):
    template_id: UUID
    version: int
    properties: list[EffectivePropertyDto]
    components: list[EffectiveComponentDto]


class ObjectTemplateCreateResultDto(WireDTO):
    object_template: ObjectTemplateDto
    version: ObjectTemplateVersionDto


class ObjectTemplatePageDto(WireDTO):
    items: list[ObjectTemplateDto]
    next_cursor: str | None


class ObjectTemplateVersionPageDto(WireDTO):
    items: list[ObjectTemplateVersionSummaryDto]
    next_cursor: str | None


class RelationshipCapabilityDto(WireDTO):
    model_config = ConfigDict(from_attributes=True)

    resolution_id: UUID
    relationship_definition_id: UUID
    name: str
    from_template_id: UUID
    to_template_id: UUID
    default_version: int | None


class RelationshipCapabilityPageDto(WireDTO):
    items: list[RelationshipCapabilityDto]
    next_cursor: str | None
