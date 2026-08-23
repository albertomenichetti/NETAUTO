"""Object and lifecycle-event HTTP wire DTOs."""

from datetime import datetime
from typing import Annotated, Literal, Self, cast
from uuid import UUID

from pydantic import ConfigDict, Field, field_serializer, model_validator

from netauto.domain.primitives import JsonValue, PrimitiveType, validate_value
from netauto.transport.http.common import BodyUUID, PositiveInteger, StrictBody, WireDTO


class ObjectCreateBody(StrictBody):
    template_id: BodyUUID
    template_version: PositiveInteger | None = None
    canonical_name: str | None = Field(default=None, min_length=1, max_length=255)
    properties: dict[str, JsonValue] | None = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def omission_is_not_null(cls, value: object) -> object:
        if isinstance(value, dict):
            raw = cast(dict[object, object], value)
            for field in ("template_version", "canonical_name", "properties"):
                if field in raw and raw[field] is None:
                    raise ValueError(f"{field}_null_forbidden")
        return cast(object, value)


class RenameBody(StrictBody):
    canonical_name: str = Field(min_length=1, max_length=255)


class SetOperationBody(StrictBody):
    op: Literal["SET"]
    property: str
    value: JsonValue


class RemoveOperationBody(StrictBody):
    op: Literal["REMOVE"]
    property: str


OperationBody = Annotated[
    SetOperationBody | RemoveOperationBody, Field(discriminator="op")
]


class DataChangeBody(StrictBody):
    operations: list[OperationBody] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_properties(self) -> Self:
        names = [item.property for item in self.operations]
        if len(names) != len(set(names)):
            raise ValueError("duplicate_property_operation")
        return self


class SchemaChangeBody(StrictBody):
    target_version: PositiveInteger


class OwnershipBody(StrictBody):
    slot_name: str = Field(pattern=r"^[a-z][a-z0-9_]{0,63}$")
    child_object_id: BodyUUID


class ObjectDto(WireDTO):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    canonical_name: str
    template_id: UUID
    template_version: int
    properties: dict[str, JsonValue]


class ObjectSummaryDto(WireDTO):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    canonical_name: str
    template_id: UUID
    template_version: int


class ObjectPageDto(WireDTO):
    items: list[ObjectSummaryDto]
    next_cursor: str | None


class ComponentProjectionDto(WireDTO):
    model_config = ConfigDict(from_attributes=True)

    slot_declaring_template_id: UUID
    slot_name: str
    child_object_id: UUID


class ComponentPageDto(WireDTO):
    items: list[ComponentProjectionDto]
    next_cursor: str | None


class OwnerProjectionDto(WireDTO):
    model_config = ConfigDict(from_attributes=True)

    parent_object_id: UUID
    slot_declaring_template_id: UUID
    slot_name: str


class IntrinsicLifecycleEventBaseDto(WireDTO):
    id: UUID
    occurred_at: datetime
    object_id: UUID
    canonical_name: str

    @field_serializer("occurred_at")
    def serialize_occurred_at(self, value: datetime) -> str:
        return str(
            validate_value(
                PrimitiveType.DATETIME, value.isoformat(timespec="microseconds"), {}
            )
        )


class CreatedLifecycleEventDto(IntrinsicLifecycleEventBaseDto):
    kind: Literal["CREATED"]
    before: None
    after: ObjectDto


class ChangedLifecycleEventDto(IntrinsicLifecycleEventBaseDto):
    kind: Literal["RENAME", "DATA_CHANGE", "SCHEMA_CHANGE"]
    before: ObjectDto
    after: ObjectDto


class DeletedLifecycleEventDto(IntrinsicLifecycleEventBaseDto):
    kind: Literal["DELETED"]
    before: ObjectDto
    after: None


class OwnershipLifecycleEventDto(IntrinsicLifecycleEventBaseDto):
    kind: Literal["ATTACH_TO", "DETACH_FROM"]
    destination_object_id: UUID
    destination_canonical_name: str
    slot_declaring_template_id: UUID
    slot_name: str


class RelationshipFactualStateDto(WireDTO):
    model_config = ConfigDict(from_attributes=True)

    relationship_definition_version: int
    properties: dict[str, JsonValue]


class RelationshipLifecycleEventBaseDto(IntrinsicLifecycleEventBaseDto):
    destination_object_id: UUID
    destination_canonical_name: str
    relationship_id: UUID
    relationship_definition_id: UUID
    relationship_name: str


class RelationshipCreatedLifecycleEventDto(RelationshipLifecycleEventBaseDto):
    kind: Literal["RELATIONSHIP_CREATED"]
    before: None
    after: RelationshipFactualStateDto


class RelationshipChangedLifecycleEventDto(RelationshipLifecycleEventBaseDto):
    kind: Literal["RELATIONSHIP_DATA_CHANGE", "RELATIONSHIP_SCHEMA_CHANGE"]
    before: RelationshipFactualStateDto
    after: RelationshipFactualStateDto


class RelationshipDeletedLifecycleEventDto(RelationshipLifecycleEventBaseDto):
    kind: Literal["RELATIONSHIP_DELETED"]
    before: RelationshipFactualStateDto
    after: None


type LifecycleEventDto = Annotated[
    CreatedLifecycleEventDto
    | ChangedLifecycleEventDto
    | DeletedLifecycleEventDto
    | OwnershipLifecycleEventDto
    | RelationshipCreatedLifecycleEventDto
    | RelationshipChangedLifecycleEventDto
    | RelationshipDeletedLifecycleEventDto,
    Field(discriminator="kind"),
]


class LifecyclePageDto(WireDTO):
    items: list[LifecycleEventDto]
    next_cursor: str | None
