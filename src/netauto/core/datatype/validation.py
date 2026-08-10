"""Runtime value validation for datatype versions."""

import datetime as dt
import math
import re
from dataclasses import dataclass
from typing import Any, cast

from jsonschema import Draft202012Validator, FormatChecker, ValidationError, validators

from netauto.core.datatype.compiler import SchemaCompiler
from netauto.core.datatype.exceptions import ValidationEngineError
from netauto.core.datatype.models import DataTypeVersion

_ERROR_CODES = {
    "type": "type",
    "format": "format",
    "minLength": "min_length",
    "maxLength": "max_length",
    "pattern": "pattern",
    "minimum": "minimum",
    "maximum": "maximum",
    "enum": "enum",
}

_ERROR_MESSAGES = {
    "type": "Value is not of the expected type",
    "format": "Value does not match the required format",
    "min_length": "Value is shorter than the minimum allowed length",
    "max_length": "Value exceeds the maximum allowed length",
    "pattern": "Value does not match the required pattern",
    "minimum": "Value is below the minimum allowed value",
    "maximum": "Value exceeds the maximum allowed value",
    "enum": "Value is not one of the allowed values",
}

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DATETIME_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?"
    r"(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)$"
)


def _is_integer(_checker: Any, instance: object) -> bool:
    return isinstance(instance, int) and not isinstance(instance, bool)


def _is_number(_checker: Any, instance: object) -> bool:
    if isinstance(instance, bool):
        return False
    if isinstance(instance, int):
        return True
    if isinstance(instance, float):
        return math.isfinite(instance)
    return False


_TYPE_CHECKER = Draft202012Validator.TYPE_CHECKER.redefine_many(
    {
        "integer": _is_integer,
        "number": _is_number,
    }
)
_Validator = validators.extend(Draft202012Validator, type_checker=_TYPE_CHECKER)
_FORMAT_CHECKER = FormatChecker()


@_FORMAT_CHECKER.checks("date")
def _is_date(instance: object) -> bool:
    if not isinstance(instance, str):
        return True
    if _DATE_PATTERN.fullmatch(instance) is None:
        return False
    try:
        dt.date.fromisoformat(instance)
    except ValueError:
        return False
    return True


@_FORMAT_CHECKER.checks("date-time")
def _is_datetime(instance: object) -> bool:
    if not isinstance(instance, str):
        return True
    if _DATETIME_PATTERN.fullmatch(instance) is None:
        return False
    try:
        parsed = dt.datetime.fromisoformat(instance.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """A normalized datatype validation issue."""

    path: tuple[str | int, ...]
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Collected validation issues for a single datatype value."""

    errors: tuple[ValidationIssue, ...] = ()

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


def _normalize_error(error: ValidationError) -> ValidationIssue:
    keyword = cast("str", error.validator)
    code = _ERROR_CODES.get(keyword)
    if code is None:
        raise ValidationEngineError(f"Unsupported validation keyword '{keyword}'.")
    return ValidationIssue(
        path=_normalize_path(error.path),
        code=code,
        message=_ERROR_MESSAGES[code],
    )


class ValidationEngine:
    """Validate runtime values against datatype versions."""

    def __init__(self) -> None:
        self._compiler = SchemaCompiler()

    def validate_datatype(
        self, datatype_version: DataTypeVersion, value: object
    ) -> ValidationResult:
        schema = self._compiler.compile_datatype(datatype_version)
        validator = _Validator(schema, format_checker=_FORMAT_CHECKER)

        try:
            issues = [_normalize_error(error) for error in validator.iter_errors(value)]
        except ValidationEngineError:
            raise
        except Exception as error:
            raise ValidationEngineError("Datatype validation failed unexpectedly.") from error

        ordered_issues = tuple(
            sorted(
                issues,
                key=lambda issue: (_path_sort_key(issue.path), issue.code, issue.message),
            )
        )
        return ValidationResult(errors=ordered_issues)
