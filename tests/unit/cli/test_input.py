from __future__ import annotations

import pytest

from netauto.cli.errors import InputError
from netauto.cli.input import parse_constraint, parse_constraints


def test_constraint_parsing_preserves_scalar_and_array_types() -> None:
    assert parse_constraint("minimum=1") == {"name": "minimum", "value": 1}
    assert parse_constraint("minimum=1.5") == {"name": "minimum", "value": 1.5}
    assert parse_constraint('enum=[true,false]') == {
        "name": "enum",
        "value": [True, False],
    }
    assert parse_constraint('enum=["active","planned"]') == {
        "name": "enum",
        "value": ["active", "planned"],
    }
    assert parse_constraint(r'pattern="^[a-z]+$"') == {
        "name": "pattern",
        "value": "^[a-z]+$",
    }


def test_constraint_parsing_allows_json_object_values_for_server_validation() -> None:
    assert parse_constraint('foo={"nested":"object"}') == {
        "name": "foo",
        "value": {"nested": "object"},
    }


def test_constraint_parsing_rejects_bad_syntax() -> None:
    with pytest.raises(InputError):
        parse_constraint("minimum")
    with pytest.raises(InputError):
        parse_constraint("=1")
    with pytest.raises(InputError):
        parse_constraint("minimum=not-json")


def test_huge_integer_preserved_exactly() -> None:
    huge = 10**1000
    parsed = parse_constraints((f"minimum={huge}",))
    assert parsed[0]["value"] == huge
    assert type(parsed[0]["value"]) is int

