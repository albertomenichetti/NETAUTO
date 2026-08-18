"""RelationshipDefinition HTTP wire DTOs."""

from typing import Annotated, Literal, Self, cast
from uuid import UUID

from pydantic import ConfigDict, Field, model_validator

from netauto.domain.datatypes import VersionStatus
from netauto.domain.objecttemplates import ValueMode
from netauto.transport.http.common import (
    BodyUUID,
    BodyValueMode,
    PositiveInteger,
    StrictBody,
    WireDTO,
)


class RelationshipPropertyBody(StrictBody):
    name: str
    position: PositiveInteger
    datatype_id: BodyUUID
    datatype_version: PositiveInteger | None = None
    value_mode: BodyValueMode

    @model_validator(mode="before")
    @classmethod
    def null_is_not_omission(cls, value: object) -> object:
        if isinstance(value, dict):
            raw = cast(dict[object, object], value)
            if "datatype_version" in raw and raw["datatype_version"] is None:
                raise ValueError("datatype_version_null_forbidden")
            return cast(object, raw)
        return value


class PerspectiveBody(StrictBody):
    template_id: BodyUUID
    name: str


class NonSymmetricCreateBody(StrictBody):
    symmetric: Literal[False]
    perspectives: list[PerspectiveBody] = Field(min_length=2, max_length=2)
    properties: list[RelationshipPropertyBody] = Field(
        default_factory=lambda: list[RelationshipPropertyBody]()
    )

    @model_validator(mode="before")
    @classmethod
    def symmetric_is_strict_boolean(cls, value: object) -> object:
        if isinstance(value, dict):
            raw = cast(dict[object, object], value)
            if not isinstance(raw.get("symmetric"), bool):
                raise ValueError("boolean_required")
            if "properties" in raw and raw["properties"] is None:
                raise ValueError("properties_null_forbidden")
        return cast(object, value)


class SymmetricCreateBody(StrictBody):
    symmetric: Literal[True]
    endpoint_template_ids: list[BodyUUID] = Field(min_length=2, max_length=2)
    name: str
    properties: list[RelationshipPropertyBody] = Field(
        default_factory=lambda: list[RelationshipPropertyBody]()
    )

    @model_validator(mode="before")
    @classmethod
    def symmetric_is_strict_boolean(cls, value: object) -> object:
        if isinstance(value, dict):
            raw = cast(dict[object, object], value)
            if not isinstance(raw.get("symmetric"), bool):
                raise ValueError("boolean_required")
            if "properties" in raw and raw["properties"] is None:
                raise ValueError("properties_null_forbidden")
        return cast(object, value)


RelationshipDefinitionCreateBody = Annotated[
    NonSymmetricCreateBody | SymmetricCreateBody, Field(discriminator="symmetric")
]


class ResolutionRenameBody(StrictBody):
    resolution_id: BodyUUID
    name: str


class NonSymmetricRenameBody(StrictBody):
    resolutions: list[ResolutionRenameBody] = Field(min_length=2, max_length=2)

    @model_validator(mode="after")
    def resolution_ids_are_unique(self) -> Self:
        if len({item.resolution_id for item in self.resolutions}) != 2:
            raise ValueError("duplicate_resolution_id")
        return self


class SymmetricRenameBody(StrictBody):
    name: str


RelationshipDefinitionRenameBody = NonSymmetricRenameBody | SymmetricRenameBody


class CreateNextBody(StrictBody):
    source_version: PositiveInteger


class ReviseBody(StrictBody):
    properties: list[RelationshipPropertyBody]

    @model_validator(mode="before")
    @classmethod
    def properties_are_required_and_non_null(cls, value: object) -> object:
        if isinstance(value, dict):
            raw = cast(dict[object, object], value)
            if "properties" not in raw or raw["properties"] is None:
                raise ValueError("properties_required")
            return cast(object, raw)
        return value


class SetDefaultBody(StrictBody):
    version: PositiveInteger


class RelationshipResolutionDto(WireDTO):
    model_config = ConfigDict(from_attributes=True)

    resolution_id: UUID
    name: str
    from_template_id: UUID
    to_template_id: UUID


class RelationshipDefinitionDto(WireDTO):
    id: UUID
    symmetric: bool
    default_version: int | None
    resolutions: list[RelationshipResolutionDto]


class RelationshipDefinitionPropertyDto(WireDTO):
    model_config = ConfigDict(from_attributes=True)

    name: str
    position: int
    datatype_id: UUID
    datatype_version: int
    value_mode: ValueMode


class RelationshipDefinitionVersionDto(WireDTO):
    relationship_definition_id: UUID
    version: int
    revision: int
    status: VersionStatus
    properties: list[RelationshipDefinitionPropertyDto]


class RelationshipDefinitionVersionSummaryDto(WireDTO):
    model_config = ConfigDict(from_attributes=True)

    relationship_definition_id: UUID
    version: int
    revision: int
    status: VersionStatus


class CreateRelationshipDefinitionDto(WireDTO):
    relationship_definition: RelationshipDefinitionDto
    version: RelationshipDefinitionVersionDto


class RelationshipDefinitionPageDto(WireDTO):
    items: list[RelationshipDefinitionDto]
    next_cursor: str | None


class RelationshipDefinitionVersionPageDto(WireDTO):
    items: list[RelationshipDefinitionVersionSummaryDto]
    next_cursor: str | None
