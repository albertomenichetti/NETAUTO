"""Factual Relationship HTTP wire DTOs."""

from typing import Annotated, Literal, Self, cast
from uuid import UUID

from pydantic import ConfigDict, Field, model_validator

from netauto.domain.primitives import JsonValue
from netauto.transport.http.common import BodyUUID, PositiveInteger, StrictBody, WireDTO


class RelationshipCreateBody(StrictBody):
    resolution_id: BodyUUID
    from_object_id: BodyUUID
    to_object_id: BodyUUID
    relationship_definition_version: PositiveInteger | None = None
    properties: dict[str, JsonValue] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def preserve_omission(cls, value: object) -> object:
        if isinstance(value, dict):
            raw = cast(dict[object, object], value)
            if (
                "relationship_definition_version" in raw
                and raw["relationship_definition_version"] is None
            ):
                raise ValueError("relationship_definition_version_null_forbidden")
            if "properties" in raw and raw["properties"] is None:
                raise ValueError("properties_null_forbidden")
            return cast(object, raw)
        return value


class RelationshipSetOperationBody(StrictBody):
    op: Literal["SET"]
    property: str = Field(pattern=r"^[a-z][a-z0-9_]{0,63}$")
    value: JsonValue


class RelationshipRemoveOperationBody(StrictBody):
    op: Literal["REMOVE"]
    property: str = Field(pattern=r"^[a-z][a-z0-9_]{0,63}$")


RelationshipDataChangeOperationBody = Annotated[
    RelationshipSetOperationBody | RelationshipRemoveOperationBody,
    Field(discriminator="op"),
]


class RelationshipDataChangeBody(StrictBody):
    operations: list[RelationshipDataChangeOperationBody] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_properties(self) -> Self:
        names = [operation.property for operation in self.operations]
        if len(names) != len(set(names)):
            raise ValueError("duplicate_relationship_property_operation")
        return self


class RelationshipSchemaChangeBody(StrictBody):
    target_version: PositiveInteger


class RelationshipViewDto(WireDTO):
    model_config = ConfigDict(from_attributes=True)

    object_id: UUID
    destination_object_id: UUID
    name: str


class RelationshipDto(WireDTO):
    id: UUID
    relationship_definition_id: UUID
    relationship_definition_version: int
    properties: dict[str, JsonValue]
    views: list[RelationshipViewDto]


class ObjectRelationshipViewDto(WireDTO):
    model_config = ConfigDict(from_attributes=True)

    relationship_id: UUID
    relationship_definition_id: UUID
    relationship_definition_version: int
    object_id: UUID
    destination_object_id: UUID
    name: str
    properties: dict[str, JsonValue]


class ObjectRelationshipPageDto(WireDTO):
    items: list[ObjectRelationshipViewDto]
    next_cursor: str | None
