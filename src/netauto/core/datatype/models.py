"""Domain models for user-defined datatypes and their versions."""

import math
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import cast
from uuid import UUID

from netauto.core.datatype.constraints import Constraint, ConstraintName
from netauto.core.datatype.exceptions import (
    ConflictingConstraints,
    DuplicateConstraint,
    InvalidConstraintValue,
    InvalidDataTypeIdentifier,
    InvalidDataTypeVersion,
    UnsupportedConstraint,
)
from netauto.core.datatype.primitives import PrimitiveType

_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
_SUPPORTED_CONSTRAINTS_BY_PRIMITIVE = {
    "core.string": frozenset(
        {
            ConstraintName.MIN_LENGTH,
            ConstraintName.MAX_LENGTH,
            ConstraintName.PATTERN,
            ConstraintName.ENUM,
        }
    ),
    "core.integer": frozenset(
        {
            ConstraintName.MINIMUM,
            ConstraintName.MAXIMUM,
            ConstraintName.ENUM,
        }
    ),
    "core.number": frozenset(
        {
            ConstraintName.MINIMUM,
            ConstraintName.MAXIMUM,
            ConstraintName.ENUM,
        }
    ),
    "core.boolean": frozenset({ConstraintName.ENUM}),
}


def _validate_identifier(value: str, field_name: str) -> str:
    if not _IDENTIFIER_PATTERN.fullmatch(value):
        raise InvalidDataTypeIdentifier(f"Invalid {field_name}: '{value}'.")
    return value


def _is_plain_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_finite_number(value: object) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    return False


def _validate_non_negative_integer(value: object, constraint_name: ConstraintName) -> int:
    if not _is_plain_int(value):
        raise InvalidConstraintValue(f"Constraint '{constraint_name.value}' requires an integer.")
    validated_value = cast("int", value)
    if validated_value < 0:
        raise InvalidConstraintValue(
            f"Constraint '{constraint_name.value}' requires a value >= 0."
        )
    return validated_value


def _validate_pattern(value: object) -> str:
    if not isinstance(value, str):
        raise InvalidConstraintValue("Constraint 'pattern' requires a string.")
    return value


def _validate_integer_bound(value: object, constraint_name: ConstraintName) -> int:
    if not _is_plain_int(value):
        raise InvalidConstraintValue(f"Constraint '{constraint_name.value}' requires an integer.")
    return cast("int", value)


def _validate_number_bound(value: object, constraint_name: ConstraintName) -> int | float:
    if not _is_finite_number(value):
        raise InvalidConstraintValue(
            f"Constraint '{constraint_name.value}' requires a finite number."
        )
    return cast("int | float", value)


def _validate_enum_collection(value: object) -> tuple[object, ...]:
    if isinstance(value, tuple):
        enum_values = value
    elif isinstance(value, list):
        enum_values = tuple(value)
    else:
        raise InvalidConstraintValue("Constraint 'enum' requires a tuple of values.")
    if not enum_values:
        raise InvalidConstraintValue("Constraint 'enum' must contain at least one value.")
    return enum_values


def _validate_enum_value_for_primitive(value: object, primitive_name: str) -> None:
    if primitive_name == "core.string":
        if not isinstance(value, str):
            raise InvalidConstraintValue(
                "Constraint 'enum' values for core.string must be strings."
            )
        return
    if primitive_name == "core.integer":
        if not _is_plain_int(value):
            raise InvalidConstraintValue(
                "Constraint 'enum' values for core.integer must be integers."
            )
        return
    if primitive_name == "core.number":
        if not _is_finite_number(value):
            raise InvalidConstraintValue(
                "Constraint 'enum' values for core.number must be finite numbers."
            )
        return
    if primitive_name == "core.boolean" and not isinstance(value, bool):
        raise InvalidConstraintValue("Constraint 'enum' values for core.boolean must be bool.")


def _validate_constraint_value(constraint: Constraint, primitive_name: str) -> Constraint:
    if constraint.name in {ConstraintName.MIN_LENGTH, ConstraintName.MAX_LENGTH}:
        validated_value = _validate_non_negative_integer(constraint.value, constraint.name)
        return Constraint(name=constraint.name, value=validated_value)
    if constraint.name is ConstraintName.PATTERN:
        return Constraint(name=constraint.name, value=_validate_pattern(constraint.value))
    if constraint.name in {ConstraintName.MINIMUM, ConstraintName.MAXIMUM}:
        if primitive_name == "core.integer":
            validated_value = _validate_integer_bound(constraint.value, constraint.name)
        else:
            validated_value = _validate_number_bound(constraint.value, constraint.name)
        return Constraint(name=constraint.name, value=validated_value)
    if constraint.name is ConstraintName.ENUM:
        enum_values = _validate_enum_collection(constraint.value)
        for enum_value in enum_values:
            _validate_enum_value_for_primitive(enum_value, primitive_name)
        if len(set(enum_values)) != len(enum_values):
            raise InvalidConstraintValue("Constraint 'enum' values must be unique.")
        return Constraint(name=constraint.name, value=enum_values)
    raise UnsupportedConstraint(
        f"Constraint '{constraint.name.value}' is not supported for primitive '{primitive_name}'."
    )


def _validate_constraints(
    primitive_type: PrimitiveType, constraints: tuple[Constraint, ...]
) -> tuple[Constraint, ...]:
    supported_constraints = _SUPPORTED_CONSTRAINTS_BY_PRIMITIVE[primitive_type.name]
    validated_constraints: list[Constraint] = []
    seen_constraints: set[ConstraintName] = set()

    for constraint in constraints:
        if constraint.name in seen_constraints:
            raise DuplicateConstraint(
                f"Duplicate constraint '{constraint.name.value}' is not allowed."
            )
        if constraint.name not in supported_constraints:
            raise UnsupportedConstraint(
                f"Constraint '{constraint.name.value}' is not supported for primitive "
                f"'{primitive_type.name}'."
            )
        validated_constraints.append(_validate_constraint_value(constraint, primitive_type.name))
        seen_constraints.add(constraint.name)

    by_name = {constraint.name: constraint for constraint in validated_constraints}
    min_length = by_name.get(ConstraintName.MIN_LENGTH)
    max_length = by_name.get(ConstraintName.MAX_LENGTH)
    if min_length is not None and max_length is not None:
        min_length_value = cast("int", min_length.value)
        max_length_value = cast("int", max_length.value)
        if min_length_value > max_length_value:
            raise ConflictingConstraints("Constraint 'min_length' must be <= 'max_length'.")

    minimum = by_name.get(ConstraintName.MINIMUM)
    maximum = by_name.get(ConstraintName.MAXIMUM)
    if minimum is not None and maximum is not None:
        minimum_value = cast("int | float", minimum.value)
        maximum_value = cast("int | float", maximum.value)
        if minimum_value > maximum_value:
            raise ConflictingConstraints("Constraint 'minimum' must be <= 'maximum'.")

    return tuple(validated_constraints)


class DataTypeVersionStatus(StrEnum):
    """Lifecycle status for a datatype version."""

    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"


@dataclass(frozen=True, slots=True)
class DataType:
    """Stable identity and human-readable name for a user-defined datatype."""

    id: UUID
    namespace: str
    name: str
    description: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "namespace", _validate_identifier(self.namespace, "namespace"))
        object.__setattr__(self, "name", _validate_identifier(self.name, "name"))

    @property
    def qualified_name(self) -> str:
        """Return the human-readable qualified name."""
        return f"{self.namespace}.{self.name}"


@dataclass(frozen=True, slots=True)
class DataTypeVersion:
    """Versioned schema metadata for a datatype."""

    datatype_id: UUID
    version: int
    status: DataTypeVersionStatus
    base_type: PrimitiveType
    constraints: tuple[Constraint, ...] = ()

    def __post_init__(self) -> None:
        if self.version < 1:
            raise InvalidDataTypeVersion(
                f"Invalid version '{self.version}'. DataTypeVersion must be >= 1."
            )
        object.__setattr__(
            self,
            "constraints",
            _validate_constraints(self.base_type, tuple(self.constraints)),
        )
