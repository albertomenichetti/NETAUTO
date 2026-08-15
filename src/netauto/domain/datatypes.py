"""Plain-Python DataType state and input validation."""

import re
from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from netauto.domain.primitives import JsonValue, PrimitiveType

_IDENTIFIER = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")
_NAMESPACE = re.compile(r"[a-z][a-z0-9_]{0,63}(?:\.[a-z][a-z0-9_]{0,63})*\Z")


class VersionStatus(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    DEPRECATED = "DEPRECATED"


@dataclass(frozen=True, slots=True)
class DataType:
    id: UUID
    namespace: str
    name: str
    description: str | None
    default_version: int | None


@dataclass(frozen=True, slots=True)
class DataTypeVersion:
    datatype_id: UUID
    version: int
    revision: int
    status: VersionStatus
    base_type: PrimitiveType
    constraints: dict[str, JsonValue]


@dataclass(frozen=True, slots=True)
class DataTypeVersionSummary:
    datatype_id: UUID
    version: int
    revision: int
    status: VersionStatus
    base_type: PrimitiveType


@dataclass(frozen=True, slots=True)
class CreateDataTypeResult:
    datatype: DataType
    version: DataTypeVersion


def validate_qualified_name(namespace: str, name: str, *, public: bool) -> None:
    if (
        len(namespace) > 255
        or _NAMESPACE.fullmatch(namespace) is None
        or _IDENTIFIER.fullmatch(name) is None
    ):
        raise ValueError("invalid_qualified_name")
    if public and (namespace == "core" or namespace.startswith("core.")):
        raise ValueError("reserved_namespace")
