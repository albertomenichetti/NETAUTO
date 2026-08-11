"""Pydantic DTOs for object REST endpoints."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr

from netauto.core.object import ObjectChangeKind

PositiveStrictInt = Annotated[StrictInt, Field(ge=1)]


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateObjectRequest(ApiModel):
    template_id: UUID
    template_version: PositiveStrictInt | None = None
    properties: dict[str, object] = Field(default_factory=dict)


class UpdateObjectRequest(ApiModel):
    properties: dict[str, object] | None = None
    remove_properties: list[StrictStr] = Field(default_factory=list)


class AttachObjectComponentRequest(ApiModel):
    slot_name: StrictStr
    component_object_id: UUID


class ComponentMembershipResponse(ApiModel):
    parent_object_id: UUID
    slot_name: str
    component_object_id: UUID


class ObjectResponse(ApiModel):
    id: UUID
    template_id: UUID
    template_version: int
    properties: dict[str, object]


class ObjectChangeSnapshotResponse(ApiModel):
    template_id: UUID
    template_version: int
    properties: dict[str, object]


class ObjectChangeResponse(ApiModel):
    id: UUID
    object_id: UUID
    occurred_at: datetime
    kind: ObjectChangeKind
    before: ObjectChangeSnapshotResponse | None
    after: ObjectChangeSnapshotResponse | None
