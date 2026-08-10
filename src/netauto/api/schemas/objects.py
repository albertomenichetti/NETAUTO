"""Pydantic DTOs for object REST endpoints."""

from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictInt

PositiveStrictInt = Annotated[StrictInt, Field(ge=1)]


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateObjectRequest(ApiModel):
    template_id: UUID
    template_version: PositiveStrictInt
    properties: dict[str, object] = Field(default_factory=dict)


class UpdateObjectRequest(ApiModel):
    properties: dict[str, object] | None = None
    remove_properties: list[str] = Field(default_factory=list)


class ObjectResponse(ApiModel):
    id: UUID
    template_id: UUID
    template_version: int
    properties: dict[str, object]
