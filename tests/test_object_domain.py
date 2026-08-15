"""Pure intrinsic Object runtime-state semantics."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from netauto.domain.objects import (
    DataChangeKind,
    DataChangeOperation,
    ObjectValidationError,
    RuntimePropertySpec,
    apply_data_change,
    canonicalize_properties,
    validate_canonical_name,
)
from netauto.domain.objecttemplates import ValueMode
from netauto.domain.primitives import JsonValue, PrimitiveType, PrimitiveValidationError


def _spec(
    name: str,
    primitive: PrimitiveType,
    *,
    mode: ValueMode = ValueMode.SCALAR,
    required: bool = False,
    constraints: dict[str, JsonValue] | None = None,
) -> RuntimePropertySpec:
    return RuntimePropertySpec(name, mode, required, primitive, constraints or {})


def test_canonical_name_preserves_exact_value_and_rejects_bad_length() -> None:
    assert validate_canonical_name("  Router A  ") == "  Router A  "
    with pytest.raises(ObjectValidationError):
        validate_canonical_name("")
    with pytest.raises(ObjectValidationError):
        validate_canonical_name("x" * 256)


def test_scalar_list_required_optional_and_duplicate_semantics() -> None:
    specs = (
        _spec("name", PrimitiveType.STRING, required=True),
        _spec("ports", PrimitiveType.INTEGER, mode=ValueMode.LIST),
        _spec(
            "required_ports",
            PrimitiveType.INTEGER,
            mode=ValueMode.LIST,
            required=True,
        ),
    )
    assert canonicalize_properties(
        {"name": "r1", "ports": [], "required_ports": [1, 1]}, specs
    ) == {"name": "r1", "required_ports": [1, 1]}
    with pytest.raises(ObjectValidationError, match="required"):
        canonicalize_properties({"required_ports": [1]}, specs)
    with pytest.raises(ObjectValidationError, match="non_empty_list_required"):
        canonicalize_properties({"name": "r1", "required_ports": []}, specs)
    with pytest.raises(ObjectValidationError, match="scalar_required"):
        canonicalize_properties({"name": ["r1"], "required_ports": [1]}, specs)


def test_unknown_null_and_list_carrier_are_rejected() -> None:
    specs = (_spec("value", PrimitiveType.INTEGER),)
    with pytest.raises(ObjectValidationError, match="unknown_property"):
        canonicalize_properties({"unknown": 1}, specs)
    with pytest.raises(ObjectValidationError, match="null_forbidden"):
        canonicalize_properties({"value": None}, specs)
    with pytest.raises(ObjectValidationError, match="list_required"):
        canonicalize_properties(
            {"value": 1},
            (_spec("value", PrimitiveType.INTEGER, mode=ValueMode.LIST),),
        )


def test_primitive_canonicalization_and_exact_constraints_are_reused() -> None:
    specs = (
        _spec(
            "number",
            PrimitiveType.NUMBER,
            constraints={"minimum": "1.5", "enum": ["1.5", "2"]},
        ),
        _spec("when", PrimitiveType.DATETIME),
        _spec("ip", PrimitiveType.IP),
        _spec("prefix", PrimitiveType.IP_PREFIX),
        _spec("size", PrimitiveType.BYTE_SIZE),
    )
    assert canonicalize_properties(
        {
            "number": "2.0",
            "when": "2026-08-15T02:00:00+02:00",
            "ip": "2001:0db8::1",
            "prefix": "10.0.0.0/24",
            "size": "1.5 KiB",
        },
        specs,
    ) == {
        "number": "2",
        "when": "2026-08-15T00:00:00Z",
        "ip": "2001:db8::1",
        "prefix": "10.0.0.0/24",
        "size": 1536,
    }
    with pytest.raises(PrimitiveValidationError, match="enum"):
        canonicalize_properties({"number": "3"}, (specs[0],))


def test_data_change_validates_complete_final_state_and_detects_noop() -> None:
    specs = (
        _spec("required", PrimitiveType.INTEGER, required=True),
        _spec("optional", PrimitiveType.INTEGER, mode=ValueMode.LIST),
    )
    current: dict[str, JsonValue] = {"required": 1, "optional": [2]}
    assert apply_data_change(
        current,
        (DataChangeOperation(DataChangeKind.SET, "optional", []),),
        specs,
    ) == {"required": 1}
    assert (
        apply_data_change(
            current,
            (DataChangeOperation(DataChangeKind.SET, "required", 1),),
            specs,
        )
        == current
    )
    with pytest.raises(ObjectValidationError, match="required"):
        apply_data_change(
            current,
            (DataChangeOperation(DataChangeKind.REMOVE, "required"),),
            specs,
        )


@pytest.mark.property
@given(st.lists(st.integers(), max_size=20))
def test_list_canonicalization_is_idempotent(values: list[int]) -> None:
    specs = (_spec("values", PrimitiveType.INTEGER, mode=ValueMode.LIST),)
    once = canonicalize_properties({"values": values}, specs)
    assert canonicalize_properties(once, specs) == once
