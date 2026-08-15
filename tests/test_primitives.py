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
        (PrimitiveType.DATE, "0001-01-01", "0001-01-01"),
        (PrimitiveType.DATE, "9999-12-31", "9999-12-31"),
        (
            PrimitiveType.DATETIME,
            "2024-01-02T03:04:05.120000000+02:30",
            "2024-01-02T00:34:05.12Z",
        ),
        (
            PrimitiveType.DATETIME,
            "2024-01-01T00:15:00+00:30",
            "2023-12-31T23:45:00Z",
        ),
        (
            PrimitiveType.DATETIME,
            "2023-12-31T23:45:00-00:30",
            "2024-01-01T00:15:00Z",
        ),
        (
            PrimitiveType.DATETIME,
            "2024-01-01T00:00:00.123456000000Z",
            "2024-01-01T00:00:00.123456Z",
        ),
        (PrimitiveType.IP, "192.0.2.1", "192.0.2.1"),
        (PrimitiveType.IP, "2001:0db8::1", "2001:db8::1"),
        (PrimitiveType.IP_PREFIX, "192.0.2.0/24", "192.0.2.0/24"),
        (PrimitiveType.IP_PREFIX, "2001:0db8::/32", "2001:db8::/32"),
        (PrimitiveType.BYTE_SIZE, "1.5 KiB", 1536),
        (PrimitiveType.BYTE_SIZE, "1kB", 1000),
        (PrimitiveType.BYTE_SIZE, "1 KiB", 1024),
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
        (PrimitiveType.NUMBER, "NaN"),
        (PrimitiveType.NUMBER, "Infinity"),
        (PrimitiveType.NUMBER, "-Infinity"),
        (PrimitiveType.DATE, "2023-02-29"),
        (PrimitiveType.DATE, "0000-01-01"),
        (PrimitiveType.DATE, "10000-01-01"),
        (PrimitiveType.DATETIME, "2024-01-01T00:00:00"),
        (PrimitiveType.DATETIME, "2024-01-01T00:00:60Z"),
        (PrimitiveType.DATETIME, "2024-01-01T00:00:00.0000001Z"),
        (PrimitiveType.IP, "192.0.2.1/24"),
        (PrimitiveType.IP_PREFIX, "192.0.2.1/24"),
        (PrimitiveType.IP_PREFIX, "192.0.2.0/255.255.255.0"),
        (PrimitiveType.BYTE_SIZE, "0.1 B"),
        (PrimitiveType.BYTE_SIZE, "1  kB"),
        (PrimitiveType.BYTE_SIZE, "1 KB"),
        (PrimitiveType.BYTE_SIZE, "1 kb"),
        (PrimitiveType.BYTE_SIZE, "+1 kB"),
        (PrimitiveType.BYTE_SIZE, "1e2 kB"),
        (PrimitiveType.BYTE_SIZE, "-1 kB"),
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


def test_string_pattern_uses_fullmatch_not_substring_search() -> None:
    constraints = canonicalize_constraints(PrimitiveType.STRING, {"pattern": "[0-9]+"})
    assert validate_value(PrimitiveType.STRING, "123", constraints) == "123"
    with pytest.raises(PrimitiveValidationError):
        validate_value(PrimitiveType.STRING, "prefix123suffix", constraints)


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


@pytest.mark.property
@given(
    whole=st.integers(min_value=0, max_value=10**18),
    tenth=st.integers(min_value=0, max_value=9),
    unit_and_factor=st.sampled_from(
        [
            ("kB", 1000),
            ("MB", 1000**2),
            ("GB", 1000**3),
            ("KiB", 1024),
            ("MiB", 1024**2),
            ("GiB", 1024**3),
        ]
    ),
)
def test_byte_size_fractional_exact_conversion_property(
    whole: int, tenth: int, unit_and_factor: tuple[str, int]
) -> None:
    unit, factor = unit_and_factor
    candidate = f"{whole}.{tenth} {unit}"
    expected, remainder = divmod(((whole * 10) + tenth) * factor, 10)
    if remainder:
        with pytest.raises(PrimitiveValidationError):
            canonicalize_value(PrimitiveType.BYTE_SIZE, candidate)
        return
    canonical = canonicalize_value(PrimitiveType.BYTE_SIZE, candidate)
    assert canonical == expected
    assert canonicalize_value(PrimitiveType.BYTE_SIZE, canonical) == canonical


@pytest.mark.property
@given(
    minimum=st.integers(min_value=-1000, max_value=1000),
    width=st.integers(min_value=0, max_value=1000),
    members=st.sets(st.integers(min_value=0, max_value=1000), max_size=20),
)
def test_integer_constraint_canonical_round_trip(
    minimum: int, width: int, members: set[int]
) -> None:
    maximum = minimum + width
    enum = sorted(member for member in members if minimum <= member <= maximum)
    candidate: dict[str, object] = {"minimum": minimum, "maximum": maximum}
    if enum:
        candidate["enum"] = enum
    canonical = canonicalize_constraints(PrimitiveType.INTEGER, candidate)
    assert canonicalize_constraints(PrimitiveType.INTEGER, canonical) == canonical
    for member in enum:
        assert validate_value(PrimitiveType.INTEGER, member, canonical) == member
