"""Pydantic DTOs for object template REST endpoints."""

from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr

from netauto.core.objecttemplate import ObjectTemplateVersionStatus

PositiveStrictInt = Annotated[StrictInt, Field(ge=1)]


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ObjectTemplateVersionRefRequest(ApiModel):
    template_id: UUID
    version: PositiveStrictInt


class ObjectTemplateVersionRefResponse(ApiModel):
    template_id: UUID
    version: int


class ObjectTemplatePropertyRequest(ApiModel):
    name: StrictStr
    datatype_id: UUID
    datatype_version: PositiveStrictInt | None = None
    required: StrictBool = False


class ObjectTemplatePropertyResponse(ApiModel):
    name: str
    datatype_id: UUID
    datatype_version: int
    required: bool


class ObjectTemplateComponentRequest(ApiModel):
    name: StrictStr
    template_id: UUID


class ObjectTemplateComponentResponse(ApiModel):
    name: str
    template_id: UUID


class CreateObjectTemplateRequest(ApiModel):
    namespace: StrictStr
    name: StrictStr
    description: StrictStr | None
    abstract: StrictBool
    parent: ObjectTemplateVersionRefRequest | None = None
    properties: list[ObjectTemplatePropertyRequest] = Field(default_factory=list)
    components: list[ObjectTemplateComponentRequest] = Field(default_factory=list)


class ReviseObjectTemplateVersionRequest(ApiModel):
    parent: ObjectTemplateVersionRefRequest | None
    properties: list[ObjectTemplatePropertyRequest]
    components: list[ObjectTemplateComponentRequest] = Field(default_factory=list)


class CreateNextObjectTemplateVersionRequest(ApiModel):
    source_version: PositiveStrictInt


class ObjectTemplateResponse(ApiModel):
    id: UUID
    namespace: str
    name: str
    qualified_name: str
    description: str | None
    abstract: bool


class ObjectTemplateVersionResponse(ApiModel):
    template_id: UUID
    version: int
    status: ObjectTemplateVersionStatus
    parent: ObjectTemplateVersionRefResponse | None
    properties: list[ObjectTemplatePropertyResponse]
    components: list[ObjectTemplateComponentResponse]


class CreateObjectTemplateResponse(ApiModel):
    object_template: ObjectTemplateResponse
    version: ObjectTemplateVersionResponse
