from dataclasses import FrozenInstanceError

import pytest

from netauto.core.datatype import PrimitiveTypeNotFound, PrimitiveTypeRegistry


def test_all_six_built_in_primitives_exist() -> None:
    registry = PrimitiveTypeRegistry()

    assert registry.exists("core.string")
    assert registry.exists("core.integer")
    assert registry.exists("core.number")
    assert registry.exists("core.boolean")
    assert registry.exists("core.date")
    assert registry.exists("core.datetime")


@pytest.mark.parametrize(
    ("name", "json_schema_type", "json_schema_format"),
    [
        ("core.string", "string", None),
        ("core.integer", "integer", None),
        ("core.number", "number", None),
        ("core.boolean", "boolean", None),
        ("core.date", "string", "date"),
        ("core.datetime", "string", "date-time"),
    ],
)
def test_each_primitive_has_expected_json_schema_type(
    name: str, json_schema_type: str, json_schema_format: str | None
) -> None:
    registry = PrimitiveTypeRegistry()

    primitive_type = registry.get(name)

    assert primitive_type.json_schema_type == json_schema_type
    assert primitive_type.json_schema_format == json_schema_format


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
        "core.date",
        "core.datetime",
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
        ("core.date", True),
        ("core.datetime", True),
        ("core.unknown", False),
    ],
)
def test_exists_returns_correct_results(name: str, expected: bool) -> None:
    registry = PrimitiveTypeRegistry()

    assert registry.exists(name) is expected
