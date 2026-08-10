from dataclasses import FrozenInstanceError
from decimal import Decimal
from fractions import Fraction
from math import inf, nan
from uuid import uuid4

import pytest

from netauto.core.datatype import (
    Constraint,
    ConstraintName,
    DataTypeVersion,
    DataTypeVersionStatus,
    PrimitiveTypeRegistry,
    SchemaCompilationError,
    ValidationEngine,
    ValidationEngineError,
    ValidationIssue,
    ValidationResult,
)


def _base_type(name: str):
    return PrimitiveTypeRegistry().get(name)


def _datatype_version(
    primitive_name: str,
    *,
    constraints: tuple[Constraint, ...] = (),
    status: DataTypeVersionStatus = DataTypeVersionStatus.DRAFT,
) -> DataTypeVersion:
    return DataTypeVersion(
        datatype_id=uuid4(),
        version=1,
        status=status,
        base_type=_base_type(primitive_name),
        constraints=constraints,
    )


def test_empty_errors_means_valid() -> None:
    result = ValidationResult()

    assert result.errors == ()
    assert result.is_valid is True


def test_one_or_more_errors_means_invalid() -> None:
    result = ValidationResult(
        errors=(ValidationIssue(path=(), code="type", message="Value is not of the expected type"),)
    )

    assert result.is_valid is False


def test_validation_issue_is_immutable() -> None:
    issue = ValidationIssue(path=(), code="type", message="Value is not of the expected type")

    with pytest.raises(FrozenInstanceError):
        issue.code = "enum"  # type: ignore[misc]


def test_validation_result_is_immutable_and_errors_are_tuple() -> None:
    result = ValidationResult(
        errors=(
            ValidationIssue(path=(), code="type", message="Value is not of the expected type"),
        )
    )

    assert isinstance(result.errors, tuple)
    with pytest.raises(FrozenInstanceError):
        result.errors = ()  # type: ignore[misc]


@pytest.mark.parametrize("value", ["router01"])
def test_string_value_accepted(value: object) -> None:
    result = ValidationEngine().validate_datatype(_datatype_version("core.string"), value)

    assert result.is_valid is True


@pytest.mark.parametrize("value", [123, True, None])
def test_string_non_string_values_rejected(value: object) -> None:
    result = ValidationEngine().validate_datatype(_datatype_version("core.string"), value)

    assert result.errors == (
        ValidationIssue(path=(), code="type", message="Value is not of the expected type"),
    )


@pytest.mark.parametrize("value", [1, 0, -1])
def test_integer_values_accepted(value: object) -> None:
    result = ValidationEngine().validate_datatype(_datatype_version("core.integer"), value)

    assert result.is_valid is True


@pytest.mark.parametrize("value", [1.0, 1.5, True, False, "1", None])
def test_integer_values_rejected_with_strict_runtime_semantics(value: object) -> None:
    result = ValidationEngine().validate_datatype(_datatype_version("core.integer"), value)

    assert result.errors == (
        ValidationIssue(path=(), code="type", message="Value is not of the expected type"),
    )


@pytest.mark.parametrize("value", [1, 1.0, 1.5, -2.75])
def test_number_values_accepted(value: object) -> None:
    result = ValidationEngine().validate_datatype(_datatype_version("core.number"), value)

    assert result.is_valid is True


def test_very_large_integer_is_accepted_for_core_number() -> None:
    large_integer = 10**1000

    result = ValidationEngine().validate_datatype(_datatype_version("core.number"), large_integer)

    assert result.is_valid is True


def test_very_large_integer_is_accepted_for_core_integer() -> None:
    large_integer = 10**1000

    result = ValidationEngine().validate_datatype(_datatype_version("core.integer"), large_integer)

    assert result.is_valid is True


@pytest.mark.parametrize(
    "value",
    [True, False, "1", nan, inf, -inf, None, Decimal("1.5"), Fraction(3, 2), 1 + 2j],
)
def test_number_values_rejected_with_json_native_semantics(value: object) -> None:
    result = ValidationEngine().validate_datatype(_datatype_version("core.number"), value)

    assert result.errors == (
        ValidationIssue(path=(), code="type", message="Value is not of the expected type"),
    )


@pytest.mark.parametrize("value", [True, False])
def test_boolean_values_accepted(value: object) -> None:
    result = ValidationEngine().validate_datatype(_datatype_version("core.boolean"), value)

    assert result.is_valid is True


@pytest.mark.parametrize("value", [0, 1, "true", None])
def test_boolean_values_rejected(value: object) -> None:
    result = ValidationEngine().validate_datatype(_datatype_version("core.boolean"), value)

    assert result.errors == (
        ValidationIssue(path=(), code="type", message="Value is not of the expected type"),
    )


@pytest.mark.parametrize(
    ("primitive_name", "value"),
    [
        ("core.integer", "100"),
        ("core.integer", 1.0),
        ("core.boolean", 1),
        ("core.string", 123),
    ],
)
def test_no_coercion_is_performed(primitive_name: str, value: object) -> None:
    result = ValidationEngine().validate_datatype(_datatype_version(primitive_name), value)

    assert result.is_valid is False
    assert result.errors[0].code == "type"


@pytest.mark.parametrize("value", ["2026-08-10", "2024-02-29"])
def test_date_values_accepted(value: object) -> None:
    result = ValidationEngine().validate_datatype(_datatype_version("core.date"), value)

    assert result.is_valid is True


@pytest.mark.parametrize(
    "value",
    [
        "2026-02-29",
        "2026-02-31",
        "2026-13-01",
        "2026-8-10",
        "20260810",
        "2026-08-10T00:00:00Z",
    ],
)
def test_malformed_date_strings_are_rejected_with_format_error(value: object) -> None:
    result = ValidationEngine().validate_datatype(_datatype_version("core.date"), value)

    assert result.errors == (
        ValidationIssue(
            path=(),
            code="format",
            message="Value does not match the required format",
        ),
    )


@pytest.mark.parametrize("value", [123, True, None])
def test_non_string_date_values_are_rejected_with_type_error(value: object) -> None:
    result = ValidationEngine().validate_datatype(_datatype_version("core.date"), value)

    assert result.errors == (
        ValidationIssue(path=(), code="type", message="Value is not of the expected type"),
    )


@pytest.mark.parametrize(
    "value",
    [
        "2026-08-10T15:14:00Z",
        "2026-08-10T17:14:00+02:00",
        "2026-08-10T17:14:00.123456+02:00",
        "2026-08-10T10:14:00-05:00",
    ],
)
def test_datetime_values_accepted(value: object) -> None:
    result = ValidationEngine().validate_datatype(_datatype_version("core.datetime"), value)

    assert result.is_valid is True


@pytest.mark.parametrize(
    "value",
    [
        "2026-08-10",
        "2026-08-10T17:14:00",
        "2026-02-31T17:14:00Z",
        "2026-08-10 17:14:00Z",
        "2026-08-10T25:14:00Z",
        "2026-08-10T17:60:00Z",
        "2026-08-10T17:14:00+02:60",
        "2026-08-10T17:14:00+00:99",
        "2026-08-10T17:14:00+24:00",
        "2026-08-10t17:14:00z",
    ],
)
def test_malformed_datetime_strings_are_rejected_with_format_error(value: object) -> None:
    result = ValidationEngine().validate_datatype(_datatype_version("core.datetime"), value)

    assert result.errors == (
        ValidationIssue(
            path=(),
            code="format",
            message="Value does not match the required format",
        ),
    )


@pytest.mark.parametrize("value", [123, True, None])
def test_non_string_datetime_values_are_rejected_with_type_error(value: object) -> None:
    result = ValidationEngine().validate_datatype(_datatype_version("core.datetime"), value)

    assert result.errors == (
        ValidationIssue(path=(), code="type", message="Value is not of the expected type"),
    )


@pytest.mark.parametrize(
    "value",
    [
        "192.168.1.1",
        "0.0.0.0",
        "255.255.255.255",
        "2001:db8::1",
        "2001:DB8::1",
        "::1",
        "::",
        "fe80::1",
        "::ffff:192.0.2.1",
    ],
)
def test_ip_values_accepted(value: object) -> None:
    result = ValidationEngine().validate_datatype(_datatype_version("core.ip"), value)

    assert result.is_valid is True


@pytest.mark.parametrize(
    "value",
    [
        "192.168.1.999",
        "192.168.001.001",
        "192.168.1",
        "256.0.0.1",
        "2001:db8::gg",
        "2001:db8:::1",
        "192.168.1.1/24",
        "2001:db8::1/64",
        "fe80::1%eth0",
        "fe80::1%3",
        "not-an-ip",
        "",
    ],
)
def test_malformed_ip_strings_are_rejected_with_format_error(value: object) -> None:
    result = ValidationEngine().validate_datatype(_datatype_version("core.ip"), value)

    assert result.errors == (
        ValidationIssue(
            path=(),
            code="format",
            message="Value does not match the required format",
        ),
    )


@pytest.mark.parametrize("value", [123, True, None, {}, []])
def test_non_string_ip_values_are_rejected_with_type_error(value: object) -> None:
    result = ValidationEngine().validate_datatype(_datatype_version("core.ip"), value)

    assert result.errors == (
        ValidationIssue(path=(), code="type", message="Value is not of the expected type"),
    )


@pytest.mark.parametrize(
    "value",
    [
        "192.168.1.0/24",
        "10.0.0.0/8",
        "0.0.0.0/0",
        "192.168.1.1/32",
        "2001:db8::/32",
        "2001:db8:abcd:12::/64",
        "::/0",
        "2001:db8::1/128",
    ],
)
def test_ip_prefix_values_accepted(value: object) -> None:
    result = ValidationEngine().validate_datatype(_datatype_version("core.ip_prefix"), value)

    assert result.is_valid is True


@pytest.mark.parametrize(
    "value",
    [
        "192.168.1.12/24",
        "192.168.1.255/24",
        "192.168.1.0/33",
        "192.168.1.0/-1",
        "192.168.1.0",
        "192.168.1.0/255.255.255.0",
        "192.168.1.0/0.0.0.255",
        "2001:db8::1/32",
        "2001:db8::/129",
        "2001:db8::/-1",
        "2001:db8::",
        "fe80::%eth0/64",
        "not-a-prefix",
        "",
    ],
)
def test_malformed_ip_prefix_strings_are_rejected_with_format_error(value: object) -> None:
    result = ValidationEngine().validate_datatype(_datatype_version("core.ip_prefix"), value)

    assert result.errors == (
        ValidationIssue(
            path=(),
            code="format",
            message="Value does not match the required format",
        ),
    )


@pytest.mark.parametrize("value", [123, True, None, {}, []])
def test_non_string_ip_prefix_values_are_rejected_with_type_error(value: object) -> None:
    result = ValidationEngine().validate_datatype(_datatype_version("core.ip_prefix"), value)

    assert result.errors == (
        ValidationIssue(path=(), code="type", message="Value is not of the expected type"),
    )


def test_hostname_constraints_validate_string_values() -> None:
    datatype_version = _datatype_version(
        "core.string",
        constraints=(
            Constraint(name=ConstraintName.MIN_LENGTH, value=1),
            Constraint(name=ConstraintName.MAX_LENGTH, value=253),
            Constraint(name=ConstraintName.PATTERN, value=r"^[a-z0-9-]+$"),
        ),
    )
    engine = ValidationEngine()

    assert engine.validate_datatype(datatype_version, "router-01").is_valid is True
    assert engine.validate_datatype(datatype_version, "").errors == (
        ValidationIssue(
            path=(),
            code="min_length",
            message="Value is shorter than the minimum allowed length",
        ),
        ValidationIssue(
            path=(),
            code="pattern",
            message="Value does not match the required pattern",
        ),
    )
    oversized = "r" * 254
    assert engine.validate_datatype(datatype_version, oversized).errors == (
        ValidationIssue(
            path=(),
            code="max_length",
            message="Value exceeds the maximum allowed length",
        ),
    )


def test_vlan_id_constraints_validate_integer_values() -> None:
    datatype_version = _datatype_version(
        "core.integer",
        constraints=(
            Constraint(name=ConstraintName.MINIMUM, value=1),
            Constraint(name=ConstraintName.MAXIMUM, value=4094),
        ),
    )
    engine = ValidationEngine()

    assert engine.validate_datatype(datatype_version, 1).is_valid is True
    assert engine.validate_datatype(datatype_version, 4094).is_valid is True
    assert engine.validate_datatype(datatype_version, 0).errors == (
        ValidationIssue(
            path=(),
            code="minimum",
            message="Value is below the minimum allowed value",
        ),
    )
    assert engine.validate_datatype(datatype_version, 4095).errors == (
        ValidationIssue(
            path=(),
            code="maximum",
            message="Value exceeds the maximum allowed value",
        ),
    )
    for invalid_value in (1.0, True):
        assert engine.validate_datatype(datatype_version, invalid_value).errors == (
            ValidationIssue(path=(), code="type", message="Value is not of the expected type"),
        )


def test_string_enum_validation() -> None:
    datatype_version = _datatype_version(
        "core.string",
        constraints=(
            Constraint(name=ConstraintName.ENUM, value=("active", "planned", "retired")),
        ),
    )
    engine = ValidationEngine()

    assert engine.validate_datatype(datatype_version, "active").is_valid is True
    assert engine.validate_datatype(datatype_version, "disabled").errors == (
        ValidationIssue(path=(), code="enum", message="Value is not one of the allowed values"),
    )


def test_integer_enum_validation_rejects_integral_float() -> None:
    datatype_version = _datatype_version(
        "core.integer",
        constraints=(Constraint(name=ConstraintName.ENUM, value=(1, 2, 3)),),
    )

    result = ValidationEngine().validate_datatype(datatype_version, 1.0)

    assert result.errors == (
        ValidationIssue(path=(), code="type", message="Value is not of the expected type"),
    )


def test_boolean_enum_validation() -> None:
    datatype_version = _datatype_version(
        "core.boolean",
        constraints=(Constraint(name=ConstraintName.ENUM, value=(True, False)),),
    )
    engine = ValidationEngine()

    assert engine.validate_datatype(datatype_version, True).is_valid is True
    assert engine.validate_datatype(datatype_version, 1).errors == (
        ValidationIssue(path=(), code="enum", message="Value is not one of the allowed values"),
        ValidationIssue(path=(), code="type", message="Value is not of the expected type"),
    )


def test_multiple_errors_are_collected_in_deterministic_order() -> None:
    engine = ValidationEngine()
    first = _datatype_version(
        "core.string",
        constraints=(
            Constraint(name=ConstraintName.MIN_LENGTH, value=5),
            Constraint(name=ConstraintName.ENUM, value=("router", "switch")),
        ),
    )
    second = _datatype_version(
        "core.string",
        constraints=(
            Constraint(name=ConstraintName.ENUM, value=("router", "switch")),
            Constraint(name=ConstraintName.MIN_LENGTH, value=5),
        ),
    )

    expected = (
        ValidationIssue(path=(), code="enum", message="Value is not one of the allowed values"),
        ValidationIssue(
            path=(),
            code="min_length",
            message="Value is shorter than the minimum allowed length",
        ),
    )

    assert engine.validate_datatype(first, "a").errors == expected
    assert engine.validate_datatype(second, "a").errors == expected


def test_error_normalization_uses_netauto_codes_and_messages() -> None:
    datatype_version = _datatype_version(
        "core.string",
        constraints=(
            Constraint(name=ConstraintName.MIN_LENGTH, value=2),
            Constraint(name=ConstraintName.MAX_LENGTH, value=3),
            Constraint(name=ConstraintName.PATTERN, value=r"^[a-z]+$"),
            Constraint(name=ConstraintName.ENUM, value=("ab", "cd")),
        ),
    )

    result = ValidationEngine().validate_datatype(datatype_version, "1")

    assert result.errors == (
        ValidationIssue(path=(), code="enum", message="Value is not one of the allowed values"),
        ValidationIssue(
            path=(),
            code="min_length",
            message="Value is shorter than the minimum allowed length",
        ),
        ValidationIssue(
            path=(),
            code="pattern",
            message="Value does not match the required pattern",
        ),
    )


def test_scalar_datatype_validation_uses_root_path() -> None:
    datatype_version = _datatype_version(
        "core.integer",
        constraints=(Constraint(name=ConstraintName.MINIMUM, value=1),),
    )

    result = ValidationEngine().validate_datatype(datatype_version, 0)

    assert result.errors[0].path == ()


@pytest.mark.parametrize(
    "status",
    [
        DataTypeVersionStatus.DRAFT,
        DataTypeVersionStatus.PUBLISHED,
        DataTypeVersionStatus.DEPRECATED,
    ],
)
def test_validation_is_independent_of_lifecycle_status(status: DataTypeVersionStatus) -> None:
    result = ValidationEngine().validate_datatype(
        _datatype_version("core.string", status=status),
        "x",
    )

    assert result.is_valid is True


def test_validation_does_not_mutate_domain_state() -> None:
    enum_constraint = Constraint(name=ConstraintName.ENUM, value=("active", "planned"))
    datatype_version = _datatype_version(
        "core.string",
        constraints=(enum_constraint,),
    )

    ValidationEngine().validate_datatype(datatype_version, "disabled")

    assert datatype_version.constraints == (enum_constraint,)
    assert enum_constraint.value == ("active", "planned")


def test_unexpected_validator_failure_becomes_validation_engine_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BrokenValidator:
        def __init__(self, _schema: object, **_kwargs: object) -> None:
            pass

        def iter_errors(self, _value: object):
            raise RuntimeError("boom")

    monkeypatch.setattr("netauto.core.datatype.validation._Validator", BrokenValidator)

    with pytest.raises(ValidationEngineError) as error_info:
        ValidationEngine().validate_datatype(_datatype_version("core.string"), "ok")

    assert isinstance(error_info.value.__cause__, RuntimeError)


def test_schema_compilation_error_propagates_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken_compile(_datatype_version: DataTypeVersion) -> dict[str, object]:
        raise SchemaCompilationError("broken schema")

    engine = ValidationEngine()
    monkeypatch.setattr(engine._compiler, "compile_datatype", broken_compile)

    with pytest.raises(SchemaCompilationError):
        engine.validate_datatype(_datatype_version("core.string"), "ok")


def test_unsupported_validation_keyword_becomes_validation_engine_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class UnknownKeywordValidator:
        def __init__(self, _schema: object, **_kwargs: object) -> None:
            pass

        def iter_errors(self, _value: object):
            yield type(
                "FakeError",
                (),
                {"validator": "unknown", "path": ()},
            )()

    monkeypatch.setattr("netauto.core.datatype.validation._Validator", UnknownKeywordValidator)

    with pytest.raises(ValidationEngineError):
        ValidationEngine().validate_datatype(_datatype_version("core.string"), "ok")
