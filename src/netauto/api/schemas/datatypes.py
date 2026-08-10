"""Pydantic DTOs for datatype REST endpoints."""

from typing import Annotated, TypeAlias
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictFloat, StrictInt, StrictStr

from netauto.core.datatype import ConstraintName, DataTypeVersionStatus

StrictScalar: TypeAlias = StrictStr | StrictInt | StrictFloat | StrictBool
ConstraintValue: TypeAlias = StrictScalar | list[StrictScalar]
PositiveStrictInt = Annotated[StrictInt, Field(ge=1)]


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ConstraintRequest(ApiModel):
    name: ConstraintName
    value: ConstraintValue


class ConstraintResponse(ApiModel):
    name: ConstraintName
    value: ConstraintValue


class CreateDataTypeRequest(ApiModel):
    namespace: StrictStr
    name: StrictStr
    description: StrictStr | None
    base_type: StrictStr
    constraints: list[ConstraintRequest] = Field(default_factory=list)


class ReviseDataTypeVersionRequest(ApiModel):
    constraints: list[ConstraintRequest]


class CreateNextVersionRequest(ApiModel):
    source_version: PositiveStrictInt


class DataTypeResponse(ApiModel):
    id: UUID
    namespace: str
    name: str
    qualified_name: str
    description: str | None


class DataTypeVersionResponse(ApiModel):
    datatype_id: UUID
    version: int
    status: DataTypeVersionStatus
    base_type: str
    constraints: list[ConstraintResponse]


class CreateDataTypeResponse(ApiModel):
    datatype: DataTypeResponse
    version: DataTypeVersionResponse


class ErrorDetail(ApiModel):
    path: str
    code: str
    message: str


class ErrorBody(ApiModel):
    code: str
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)


class ErrorResponse(ApiModel):
    error: ErrorBody
