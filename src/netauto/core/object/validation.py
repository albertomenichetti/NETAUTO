"""Runtime property validation for objects."""

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from netauto.core.datatype import DataTypeVersion, ValidationEngine
from netauto.core.object.exceptions import ObjectDataTypeVersionNotFound
from netauto.core.objecttemplate import ObjectTemplateProperty

DataTypeVersionLookup = Callable[[UUID, int], DataTypeVersion | None]


@dataclass(frozen=True, slots=True)
class ObjectValidationIssue:
    """A normalized object validation issue."""

    path: tuple[str | int, ...]
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class ObjectValidationResult:
    """Collected validation issues for a single object property mapping."""

    errors: tuple[ObjectValidationIssue, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "errors", tuple(self.errors))

    @property
    def is_valid(self) -> bool:
        return not self.errors


def _normalize_path(path: Any) -> tuple[str | int, ...]:
    normalized: list[str | int] = []
    for component in path:
        if isinstance(component, str | int):
            normalized.append(component)
        else:
            normalized.append(str(component))
    return tuple(normalized)


def _path_sort_key(path: tuple[str | int, ...]) -> tuple[tuple[int, str], ...]:
    key: list[tuple[int, str]] = []
    for component in path:
        if isinstance(component, int):
            key.append((0, str(component)))
        else:
            key.append((1, component))
    return tuple(key)


class ObjectValidationEngine:
    """Validate runtime property values against effective template property declarations."""

    def __init__(self) -> None:
        self._datatype_validation = ValidationEngine()

    def validate_properties(
        self,
        *,
        properties: Mapping[str, object],
        effective_properties: Iterable[ObjectTemplateProperty],
        datatype_lookup: DataTypeVersionLookup,
    ) -> ObjectValidationResult:
        declared_properties = {prop.name: prop for prop in effective_properties}
        issues: list[ObjectValidationIssue] = []

        for property_name, property_definition in declared_properties.items():
            if property_definition.required and property_name not in properties:
                issues.append(
                    ObjectValidationIssue(
                        path=("properties", property_name),
                        code="required",
                        message="Required property is missing",
                    )
                )

        for property_name, value in properties.items():
            property_definition = declared_properties.get(property_name)
            if property_definition is None:
                issues.append(
                    ObjectValidationIssue(
                        path=("properties", property_name),
                        code="unknown_property",
                        message="Property is not defined in template",
                    )
                )
                continue

            datatype_version = datatype_lookup(
                property_definition.datatype_id,
                property_definition.datatype_version,
            )
            if datatype_version is None:
                raise ObjectDataTypeVersionNotFound("Referenced datatype version was not found.")

            datatype_result = self._datatype_validation.validate_datatype(datatype_version, value)
            for error in datatype_result.errors:
                issues.append(
                    ObjectValidationIssue(
                        path=("properties", property_name, *_normalize_path(error.path)),
                        code=error.code,
                        message=error.message,
                    )
                )

        ordered_issues = tuple(
            sorted(
                issues,
                key=lambda issue: (_path_sort_key(issue.path), issue.code, issue.message),
            )
        )
        return ObjectValidationResult(errors=ordered_issues)
