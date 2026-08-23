"""Transport-neutral validation helpers for public HTTP bodies."""

import re
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from netauto.domain.objecttemplates import ValueMode
from netauto.domain.primitives import PrimitiveType, validate_value

PositiveInteger = Annotated[int, Field(strict=True, gt=0)]


class WireDTO(BaseModel):
    """Base preserving the delivered response-model configuration."""


class StrictBody(WireDTO):
    model_config = ConfigDict(strict=True, extra="forbid")


def positive_decimal_integer(value: object) -> int:
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    if not isinstance(value, str) or re.fullmatch(r"[1-9][0-9]*", value) is None:
        raise ValueError("positive_decimal_integer_required")
    return int(value)


def uuid_carrier(value: object) -> UUID:
    if isinstance(value, UUID):
        return value
    if not isinstance(value, str):
        raise ValueError("uuid_required")
    return UUID(value)


def value_mode_carrier(value: object) -> ValueMode:
    if isinstance(value, ValueMode):
        return value
    if not isinstance(value, str):
        raise ValueError("value_mode_required")
    return ValueMode(value)


def datetime_carrier(value: object) -> datetime:
    canonical = validate_value(PrimitiveType.DATETIME, value, {}, "datetime")
    return datetime.fromisoformat(str(canonical).replace("Z", "+00:00"))


BodyUUID = Annotated[UUID, BeforeValidator(uuid_carrier)]
BodyValueMode = Annotated[ValueMode, BeforeValidator(value_mode_carrier)]
