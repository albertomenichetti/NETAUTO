"""DataType HTTP wire DTOs."""

from uuid import UUID

from pydantic import ConfigDict, Field

from netauto.domain.datatypes import VersionStatus
from netauto.domain.primitives import JsonValue, PrimitiveType
from netauto.transport.http.common import PositiveInteger, StrictBody, WireDTO


class DataTypeCreateBody(StrictBody):
    namespace: str
    name: str
    base_type: str
    description: str | None = None
    constraints: dict[str, JsonValue] = Field(default_factory=dict)


class CreateNextBody(StrictBody):
    source_version: PositiveInteger


class ReviseBody(StrictBody):
    constraints: dict[str, JsonValue]


class SetDefaultBody(StrictBody):
    version: PositiveInteger


class SetDescriptionBody(StrictBody):
    description: str | None


class DataTypeDto(WireDTO):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    namespace: str
    name: str
    description: str | None
    default_version: int | None


class DataTypeVersionDto(WireDTO):
    model_config = ConfigDict(from_attributes=True)

    datatype_id: UUID
    version: int
    revision: int
    status: VersionStatus
    base_type: PrimitiveType
    constraints: dict[str, JsonValue]


class DataTypeVersionSummaryDto(WireDTO):
    model_config = ConfigDict(from_attributes=True)

    datatype_id: UUID
    version: int
    revision: int
    status: VersionStatus
    base_type: PrimitiveType


class DataTypeCreateResultDto(WireDTO):
    datatype: DataTypeDto
    version: DataTypeVersionDto


class DataTypePageDto(WireDTO):
    items: list[DataTypeDto]
    next_cursor: str | None


class DataTypeVersionPageDto(WireDTO):
    items: list[DataTypeVersionSummaryDto]
    next_cursor: str | None
