"""Plain-Python intrinsic Object state and runtime-property semantics."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import cast
from uuid import UUID

from netauto.domain.objecttemplates import ValueMode
from netauto.domain.primitives import JsonValue, PrimitiveType, validate_value


@dataclass(frozen=True, slots=True)
class Object:
    id: UUID
    canonical_name: str
    template_id: UUID
    template_version: int
    properties: dict[str, JsonValue]


@dataclass(frozen=True, slots=True)
class ObjectSummary:
    id: UUID
    canonical_name: str
    template_id: UUID
    template_version: int


@dataclass(frozen=True, slots=True)
class RuntimePropertySpec:
    name: str
    value_mode: ValueMode
    required: bool
    base_type: PrimitiveType
    constraints: dict[str, JsonValue]


class DataChangeKind(StrEnum):
    SET = "SET"
    REMOVE = "REMOVE"


@dataclass(frozen=True, slots=True)
class DataChangeOperation:
    op: DataChangeKind
    property: str
    value: object = None


class ObjectValidationError(ValueError):
    def __init__(self, path: str, rule: str) -> None:
        self.path = path
        self.rule = rule
        super().__init__(f"{path}: {rule}")


def validate_canonical_name(value: str) -> str:
    if not 1 <= len(value) <= 255:
        raise ObjectValidationError("canonical_name", "length")
    return value


def canonicalize_properties(
    candidate: Mapping[str, object], specs: tuple[RuntimePropertySpec, ...]
) -> dict[str, JsonValue]:
    by_name = {spec.name: spec for spec in specs}
    unknown = set(candidate) - set(by_name)
    if unknown:
        name = sorted(unknown)[0]
        raise ObjectValidationError(f"properties.{name}", "unknown_property")

    canonical: dict[str, JsonValue] = {}
    for spec in specs:
        path = f"properties.{spec.name}"
        if spec.name not in candidate:
            if spec.required:
                raise ObjectValidationError(path, "required")
            continue
        raw = candidate[spec.name]
        if raw is None:
            raise ObjectValidationError(path, "null_forbidden")
        if spec.value_mode is ValueMode.SCALAR:
            if isinstance(raw, list):
                raise ObjectValidationError(path, "scalar_required")
            canonical[spec.name] = validate_value(
                spec.base_type, raw, spec.constraints, path
            )
            continue
        if not isinstance(raw, list):
            raise ObjectValidationError(path, "list_required")
        raw_items = cast(list[object], raw)
        if not raw_items:
            if spec.required:
                raise ObjectValidationError(path, "non_empty_list_required")
            continue
        canonical[spec.name] = [
            validate_value(spec.base_type, item, spec.constraints, f"{path}.{index}")
            for index, item in enumerate(raw_items)
        ]
    return canonical


def apply_data_change(
    current: dict[str, JsonValue],
    operations: tuple[DataChangeOperation, ...],
    specs: tuple[RuntimePropertySpec, ...],
) -> dict[str, JsonValue]:
    known = {spec.name for spec in specs}
    candidate: dict[str, object] = dict(current)
    for operation in operations:
        path = f"properties.{operation.property}"
        if operation.property not in known:
            raise ObjectValidationError(path, "unknown_property")
        if operation.op is DataChangeKind.SET:
            candidate[operation.property] = operation.value
        else:
            candidate.pop(operation.property, None)
    return canonicalize_properties(candidate, specs)
