from dataclasses import FrozenInstanceError

import pytest

from netauto.core.datatype import PrimitiveTypeNotFound, PrimitiveTypeRegistry


def test_all_four_built_in_primitives_exist() -> None:
    registry = PrimitiveTypeRegistry()

    assert registry.exists("core.string")
    assert registry.exists("core.integer")
    assert registry.exists("core.number")
    assert registry.exists("core.boolean")


@pytest.mark.parametrize(
    ("name", "json_schema_type"),
    [
        ("core.string", "string"),
        ("core.integer", "integer"),
        ("core.number", "number"),
        ("core.boolean", "boolean"),
    ],
)
def test_each_primitive_has_expected_json_schema_type(
    name: str, json_schema_type: str
) -> None:
    registry = PrimitiveTypeRegistry()

    primitive_type = registry.get(name)

    assert primitive_type.json_schema_type == json_schema_type


def test_unknown_primitive_lookup_raises_specific_exception() -> None:
    registry = PrimitiveTypeRegistry()

    with pytest.raises(PrimitiveTypeNotFound):
        registry.get("core.unknown")


def test_registry_contains_exactly_expected_primitive_names() -> None:
    registry = PrimitiveTypeRegistry()

    assert {primitive_type.name for primitive_type in registry.all()} == {
        "core.string",
        "core.integer",
        "core.number",
        "core.boolean",
    }


def test_primitive_objects_are_immutable() -> None:
    registry = PrimitiveTypeRegistry()
    primitive_type = registry.get("core.string")

    with pytest.raises(FrozenInstanceError):
        primitive_type.name = "core.changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("core.string", True),
        ("core.integer", True),
        ("core.number", True),
        ("core.boolean", True),
        ("core.unknown", False),
    ],
)
def test_exists_returns_correct_results(name: str, expected: bool) -> None:
    registry = PrimitiveTypeRegistry()

    assert registry.exists(name) is expected
