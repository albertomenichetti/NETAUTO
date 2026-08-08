import json
from uuid import uuid4

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from netauto.core.datatype import (
    Constraint,
    ConstraintName,
    DataTypeVersion,
    DataTypeVersionStatus,
    PrimitiveTypeRegistry,
    SchemaCompilationError,
    SchemaCompiler,
)


def _base_type(name: str):
    return PrimitiveTypeRegistry().get(name)


def _compile(
    primitive_name: str,
    *,
    constraints: tuple[Constraint, ...] = (),
    status: DataTypeVersionStatus = DataTypeVersionStatus.DRAFT,
) -> dict[str, object]:
    compiler = SchemaCompiler()
    datatype_version = DataTypeVersion(
        datatype_id=uuid4(),
        version=1,
        status=status,
        base_type=_base_type(primitive_name),
        constraints=constraints,
    )
    return compiler.compile_datatype(datatype_version)


@pytest.mark.parametrize(
    ("primitive_name", "expected"),
    [
        ("core.string", {"type": "string"}),
        ("core.integer", {"type": "integer"}),
        ("core.number", {"type": "number"}),
        ("core.boolean", {"type": "boolean"}),
    ],
)
def test_unconstrained_primitive_compilation(
    primitive_name: str, expected: dict[str, object]
) -> None:
    assert _compile(primitive_name) == expected


def test_string_constraints_compile_to_expected_fragment() -> None:
    schema = _compile(
        "core.string",
        constraints=(
            Constraint(name=ConstraintName.MIN_LENGTH, value=1),
            Constraint(name=ConstraintName.MAX_LENGTH, value=253),
        ),
    )

    assert schema == {
        "type": "string",
        "minLength": 1,
        "maxLength": 253,
    }


def test_pattern_text_is_preserved_unchanged() -> None:
    pattern = r"^(?:[a-z0-9](?:[a-z0-9-]{0,251}[a-z0-9])?)$"

    schema = _compile(
        "core.string",
        constraints=(Constraint(name=ConstraintName.PATTERN, value=pattern),),
    )

    assert schema == {"type": "string", "pattern": pattern}


def test_integer_constraints_compile_to_expected_fragment() -> None:
    schema = _compile(
        "core.integer",
        constraints=(
            Constraint(name=ConstraintName.MINIMUM, value=1),
            Constraint(name=ConstraintName.MAXIMUM, value=4094),
        ),
    )

    assert schema == {
        "type": "integer",
        "minimum": 1,
        "maximum": 4094,
    }


def test_number_constraints_compile_to_expected_fragment() -> None:
    schema = _compile(
        "core.number",
        constraints=(
            Constraint(name=ConstraintName.MINIMUM, value=-10.5),
            Constraint(name=ConstraintName.MAXIMUM, value=100.25),
        ),
    )

    assert schema == {
        "type": "number",
        "minimum": -10.5,
        "maximum": 100.25,
    }


def test_string_enum_compiles_to_json_array_with_preserved_order() -> None:
    schema = _compile(
        "core.string",
        constraints=(
            Constraint(
                name=ConstraintName.ENUM,
                value=("active", "planned", "retired"),
            ),
        ),
    )

    assert schema == {
        "type": "string",
        "enum": ["active", "planned", "retired"],
    }


@pytest.mark.parametrize(
    ("primitive_name", "enum_values"),
    [
        ("core.integer", (1, 2, 3)),
        ("core.number", (1, 2.5, 3)),
        ("core.boolean", (True, False)),
    ],
)
def test_non_string_enums_compile_to_json_array(
    primitive_name: str, enum_values: tuple[object, ...]
) -> None:
    schema = _compile(
        primitive_name,
        constraints=(Constraint(name=ConstraintName.ENUM, value=enum_values),),
    )

    assert schema["enum"] == list(enum_values)


def test_compile_datatype_does_not_mutate_datatype_version_or_constraint() -> None:
    enum_constraint = Constraint(name=ConstraintName.ENUM, value=("active", "planned"))
    datatype_version = DataTypeVersion(
        datatype_id=uuid4(),
        version=1,
        status=DataTypeVersionStatus.DRAFT,
        base_type=_base_type("core.string"),
        constraints=(enum_constraint,),
    )

    schema = SchemaCompiler().compile_datatype(datatype_version)

    assert datatype_version.constraints == (enum_constraint,)
    assert enum_constraint.value == ("active", "planned")
    assert schema["enum"] == ["active", "planned"]


def test_mutating_returned_enum_list_does_not_mutate_domain_constraint() -> None:
    enum_constraint = Constraint(name=ConstraintName.ENUM, value=("active", "planned"))
    datatype_version = DataTypeVersion(
        datatype_id=uuid4(),
        version=1,
        status=DataTypeVersionStatus.DRAFT,
        base_type=_base_type("core.string"),
        constraints=(enum_constraint,),
    )

    schema = SchemaCompiler().compile_datatype(datatype_version)
    enum_values = schema["enum"]
    assert isinstance(enum_values, list)
    enum_values.append("retired")

    assert enum_constraint.value == ("active", "planned")


def test_two_compilation_calls_return_equal_but_independent_schemas() -> None:
    datatype_version = DataTypeVersion(
        datatype_id=uuid4(),
        version=1,
        status=DataTypeVersionStatus.DRAFT,
        base_type=_base_type("core.string"),
        constraints=(Constraint(name=ConstraintName.ENUM, value=("active", "planned")),),
    )
    compiler = SchemaCompiler()

    first = compiler.compile_datatype(datatype_version)
    second = compiler.compile_datatype(datatype_version)

    assert first == second
    assert first is not second
    first_enum = first["enum"]
    assert isinstance(first_enum, list)
    first_enum.append("retired")
    assert second == {"type": "string", "enum": ["active", "planned"]}


def test_constraint_order_does_not_affect_semantic_result() -> None:
    compiler = SchemaCompiler()
    first = compiler.compile_datatype(
        DataTypeVersion(
            datatype_id=uuid4(),
            version=1,
            status=DataTypeVersionStatus.DRAFT,
            base_type=_base_type("core.string"),
            constraints=(
                Constraint(name=ConstraintName.MIN_LENGTH, value=1),
                Constraint(name=ConstraintName.MAX_LENGTH, value=253),
            ),
        )
    )
    second = compiler.compile_datatype(
        DataTypeVersion(
            datatype_id=uuid4(),
            version=1,
            status=DataTypeVersionStatus.DRAFT,
            base_type=_base_type("core.string"),
            constraints=(
                Constraint(name=ConstraintName.MAX_LENGTH, value=253),
                Constraint(name=ConstraintName.MIN_LENGTH, value=1),
            ),
        )
    )

    assert first == second


@pytest.mark.parametrize(
    "status",
    [
        DataTypeVersionStatus.DRAFT,
        DataTypeVersionStatus.PUBLISHED,
        DataTypeVersionStatus.DEPRECATED,
    ],
)
def test_all_lifecycle_statuses_can_be_compiled(status: DataTypeVersionStatus) -> None:
    schema = _compile("core.string", status=status)

    assert schema == {"type": "string"}


def test_compiled_schema_is_valid_draft_2020_12() -> None:
    schema = _compile(
        "core.integer",
        constraints=(
            Constraint(name=ConstraintName.MINIMUM, value=1),
            Constraint(name=ConstraintName.MAXIMUM, value=4094),
        ),
    )

    Draft202012Validator.check_schema(schema)


def test_compiled_schema_is_json_serializable() -> None:
    schema = _compile(
        "core.string",
        constraints=(Constraint(name=ConstraintName.ENUM, value=("active", "planned")),),
    )

    assert json.dumps(schema) == '{"type": "string", "enum": ["active", "planned"]}'


def test_schema_compilation_error_wraps_schema_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_check_schema(_schema: object) -> None:
        raise SchemaError("invalid")

    monkeypatch.setattr(Draft202012Validator, "check_schema", fake_check_schema)

    with pytest.raises(SchemaCompilationError) as error_info:
        _compile("core.string")

    assert isinstance(error_info.value.__cause__, SchemaError)
