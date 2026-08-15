"""Pure tests for the single authoritative PrimitiveType semantics path."""

from collections.abc import Callable

import pytest
from hypothesis import given
from hypothesis import strategies as st

from netauto.domain.primitives import (
    PrimitiveType,
    PrimitiveValidationError,
    canonicalize_constraints,
    canonicalize_value,
    validate_value,
)


@pytest.mark.parametrize(
    ("primitive", "candidate", "canonical"),
    [
        (PrimitiveType.STRING, " untouched ", " untouched "),
        (PrimitiveType.INTEGER, 42, 42),
        (PrimitiveType.NUMBER, "-0.000", "0"),
        (PrimitiveType.NUMBER, "12.3400", "12.34"),
        (PrimitiveType.BOOLEAN, True, True),
        (PrimitiveType.DATE, "2024-02-29", "2024-02-29"),
        (
            PrimitiveType.DATETIME,
            "2024-01-02T03:04:05.120000000+02:30",
            "2024-01-02T00:34:05.12Z",
        ),
        (PrimitiveType.IP, "2001:0db8::1", "2001:db8::1"),
        (PrimitiveType.IP_PREFIX, "192.0.2.0/24", "192.0.2.0/24"),
        (PrimitiveType.BYTE_SIZE, "1.5 KiB", 1536),
        (
            PrimitiveType.BYTE_SIZE,
            "123456789012345678901234567890 EB",
            123456789012345678901234567890000000000000000000,
        ),
        (PrimitiveType.BYTE_SIZE, 0, 0),
    ],
)
def test_canonical_primitive_values(
    primitive: PrimitiveType, candidate: object, canonical: object
) -> None:
    assert canonicalize_value(primitive, candidate) == canonical


@pytest.mark.parametrize(
    ("primitive", "candidate"),
    [
        (PrimitiveType.INTEGER, True),
        (PrimitiveType.NUMBER, 1),
        (PrimitiveType.NUMBER, "+1"),
        (PrimitiveType.NUMBER, "1e2"),
        (PrimitiveType.DATE, "2023-02-29"),
        (PrimitiveType.DATETIME, "2024-01-01T00:00:00"),
        (PrimitiveType.DATETIME, "2024-01-01T00:00:00.0000001Z"),
        (PrimitiveType.IP, "192.0.2.1/24"),
        (PrimitiveType.IP_PREFIX, "192.0.2.1/24"),
        (PrimitiveType.BYTE_SIZE, "0.1 B"),
        (PrimitiveType.BYTE_SIZE, -1),
    ],
)
def test_invalid_primitive_values(primitive: PrimitiveType, candidate: object) -> None:
    with pytest.raises(PrimitiveValidationError):
        canonicalize_value(primitive, candidate)


def test_constraints_are_canonical_and_enum_is_an_unordered_set() -> None:
    first = canonicalize_constraints(
        PrimitiveType.NUMBER,
        {"maximum": "10.00", "minimum": "-0.0", "enum": ["10.0", "0.00"]},
    )
    second = canonicalize_constraints(
        PrimitiveType.NUMBER,
        {"enum": ["0", "10"], "minimum": "0", "maximum": "10"},
    )
    assert (
        first
        == second
        == {
            "minimum": "0",
            "maximum": "10",
            "enum": ["0", "10"],
        }
    )


@pytest.mark.parametrize(
    "operation",
    [
        lambda: canonicalize_constraints(PrimitiveType.STRING, {"minimum": 1}),
        lambda: canonicalize_constraints(
            PrimitiveType.INTEGER, {"minimum": 2, "maximum": 1}
        ),
        lambda: canonicalize_constraints(
            PrimitiveType.STRING, {"min_length": 2, "enum": ["x"]}
        ),
        lambda: canonicalize_constraints(
            PrimitiveType.IP, {"enum": ["192.0.2.1"], "ip_version": 6}
        ),
        lambda: canonicalize_constraints(
            PrimitiveType.IP, {"enum": ["2001:0db8::1", "2001:db8::1"]}
        ),
        lambda: canonicalize_constraints(PrimitiveType.STRING, {"pattern": "["}),
    ],
)
def test_invalid_constraint_candidates(
    operation: Callable[[], dict[str, object]],
) -> None:
    with pytest.raises(PrimitiveValidationError):
        operation()


def test_value_validation_reuses_canonical_constraint_authority() -> None:
    constraints = canonicalize_constraints(
        PrimitiveType.STRING,
        {"min_length": 2, "max_length": 4, "pattern": "[a-z]+"},
    )
    assert validate_value(PrimitiveType.STRING, "abc", constraints) == "abc"
    with pytest.raises(PrimitiveValidationError):
        validate_value(PrimitiveType.STRING, "A", constraints)


@pytest.mark.property
@given(
    integer=st.integers(min_value=-(10**30), max_value=10**30),
    scale=st.integers(min_value=0, max_value=12),
)
def test_number_canonicalization_is_idempotent(integer: int, scale: int) -> None:
    sign = "-" if integer < 0 else ""
    digits = str(abs(integer)).zfill(scale + 1)
    candidate = (
        f"{sign}{digits[:-scale]}.{digits[-scale:]}" if scale else f"{sign}{digits}"
    )
    canonical = canonicalize_value(PrimitiveType.NUMBER, candidate)
    assert canonicalize_value(PrimitiveType.NUMBER, canonical) == canonical
