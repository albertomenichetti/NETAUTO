"""Constraint vocabulary for datatype versions."""

from dataclasses import dataclass
from enum import StrEnum


class ConstraintName(StrEnum):
    """Supported datatype constraint names."""

    MIN_LENGTH = "min_length"
    MAX_LENGTH = "max_length"
    PATTERN = "pattern"
    MINIMUM = "minimum"
    MAXIMUM = "maximum"
    ENUM = "enum"


@dataclass(frozen=True, slots=True)
class Constraint:
    """A single immutable datatype constraint."""

    name: ConstraintName
    value: object

    def __post_init__(self) -> None:
        if self.name is ConstraintName.ENUM and isinstance(self.value, list | tuple):
            object.__setattr__(self, "value", tuple(self.value))
