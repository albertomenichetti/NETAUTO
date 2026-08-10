from dataclasses import FrozenInstanceError
from math import inf, nan
from uuid import uuid4

import pytest

from netauto.core.datatype import (
    ConflictingConstraints,
    Constraint,
    ConstraintName,
    DataType,
    DataTypeVersion,
    DataTypeVersionStatus,
    DuplicateConstraint,
    InvalidConstraintValue,
    PrimitiveTypeRegistry,
    UnsupportedConstraint,
)


def _base_type(name: str):
    return PrimitiveTypeRegistry().get(name)


def test_datatype_version_with_no_constraints_is_valid() -> None:
    version = DataTypeVersion(
        datatype_id=uuid4(),
        version=1,
        status=DataTypeVersionStatus.DRAFT,
        base_type=_base_type("core.string"),
    )

    assert version.constraints == ()


@pytest.mark.parametrize("primitive_name", ["core.date", "core.datetime"])
def test_temporal_datatype_version_with_no_constraints_is_valid(primitive_name: str) -> None:
    version = DataTypeVersion(
        datatype_id=uuid4(),
        version=1,
        status=DataTypeVersionStatus.DRAFT,
        base_type=_base_type(primitive_name),
    )

    assert version.constraints == ()


def test_constraint_objects_are_immutable() -> None:
    constraint = Constraint(name=ConstraintName.MIN_LENGTH, value=1)

    with pytest.raises(FrozenInstanceError):
        constraint.value = 2  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        constraint.name = ConstraintName.MAX_LENGTH  # type: ignore[misc]


def test_enum_constraint_stores_values_as_tuple() -> None:
    constraint = Constraint(name=ConstraintName.ENUM, value=["active", "planned"])

    assert constraint.value == ("active", "planned")
    assert isinstance(constraint.value, tuple)


def test_enum_constraint_isolated_from_caller_owned_list_mutation() -> None:
    values = ["active", "planned"]

    constraint = Constraint(name=ConstraintName.ENUM, value=values)
    values.append("retired")

    assert constraint.value == ("active", "planned")


def test_constraint_collection_is_tuple() -> None:
    version = DataTypeVersion(
        datatype_id=uuid4(),
        version=1,
        status=DataTypeVersionStatus.DRAFT,
        base_type=_base_type("core.string"),
        constraints=(Constraint(name=ConstraintName.MIN_LENGTH, value=1),),
    )

    assert isinstance(version.constraints, tuple)


def test_valid_min_length() -> None:
    version = DataTypeVersion(
        datatype_id=uuid4(),
        version=1,
        status=DataTypeVersionStatus.DRAFT,
        base_type=_base_type("core.string"),
        constraints=(Constraint(name=ConstraintName.MIN_LENGTH, value=1),),
    )

    assert version.constraints[0].value == 1


def test_valid_max_length() -> None:
    version = DataTypeVersion(
        datatype_id=uuid4(),
        version=1,
        status=DataTypeVersionStatus.DRAFT,
        base_type=_base_type("core.string"),
        constraints=(Constraint(name=ConstraintName.MAX_LENGTH, value=253),),
    )

    assert version.constraints[0].value == 253


def test_valid_pattern() -> None:
    version = DataTypeVersion(
        datatype_id=uuid4(),
        version=1,
        status=DataTypeVersionStatus.DRAFT,
        base_type=_base_type("core.string"),
        constraints=(Constraint(name=ConstraintName.PATTERN, value="^[a-z]+$"),),
    )

    assert version.constraints[0].value == "^[a-z]+$"


def test_valid_string_enum() -> None:
    version = DataTypeVersion(
        datatype_id=uuid4(),
        version=1,
        status=DataTypeVersionStatus.DRAFT,
        base_type=_base_type("core.string"),
        constraints=(Constraint(name=ConstraintName.ENUM, value=("active", "planned")),),
    )

    assert version.constraints[0].value == ("active", "planned")


def test_min_length_zero_is_valid() -> None:
    version = DataTypeVersion(
        datatype_id=uuid4(),
        version=1,
        status=DataTypeVersionStatus.DRAFT,
        base_type=_base_type("core.string"),
        constraints=(Constraint(name=ConstraintName.MIN_LENGTH, value=0),),
    )

    assert version.constraints[0].value == 0


@pytest.mark.parametrize(
    ("name", "value"),
    [
        (ConstraintName.MIN_LENGTH, -1),
        (ConstraintName.MAX_LENGTH, -1),
    ],
)
def test_negative_string_length_constraints_rejected(name: ConstraintName, value: int) -> None:
    with pytest.raises(InvalidConstraintValue):
        DataTypeVersion(
            datatype_id=uuid4(),
            version=1,
            status=DataTypeVersionStatus.DRAFT,
            base_type=_base_type("core.string"),
            constraints=(Constraint(name=name, value=value),),
        )


@pytest.mark.parametrize(
    ("name", "value"),
    [
        (ConstraintName.MIN_LENGTH, True),
        (ConstraintName.MAX_LENGTH, False),
        (ConstraintName.MIN_LENGTH, 1.5),
        (ConstraintName.MAX_LENGTH, "10"),
    ],
)
def test_bool_and_invalid_types_rejected_for_string_lengths(
    name: ConstraintName, value: object
) -> None:
    with pytest.raises(InvalidConstraintValue):
        DataTypeVersion(
            datatype_id=uuid4(),
            version=1,
            status=DataTypeVersionStatus.DRAFT,
            base_type=_base_type("core.string"),
            constraints=(Constraint(name=name, value=value),),
        )


def test_min_length_greater_than_max_length_rejected() -> None:
    with pytest.raises(ConflictingConstraints):
        DataTypeVersion(
            datatype_id=uuid4(),
            version=1,
            status=DataTypeVersionStatus.DRAFT,
            base_type=_base_type("core.string"),
            constraints=(
                Constraint(name=ConstraintName.MIN_LENGTH, value=10),
                Constraint(name=ConstraintName.MAX_LENGTH, value=5),
            ),
        )


def test_valid_integer_minimum() -> None:
    version = DataTypeVersion(
        datatype_id=uuid4(),
        version=1,
        status=DataTypeVersionStatus.DRAFT,
        base_type=_base_type("core.integer"),
        constraints=(Constraint(name=ConstraintName.MINIMUM, value=1),),
    )

    assert version.constraints[0].value == 1


def test_valid_integer_maximum() -> None:
    version = DataTypeVersion(
        datatype_id=uuid4(),
        version=1,
        status=DataTypeVersionStatus.DRAFT,
        base_type=_base_type("core.integer"),
        constraints=(Constraint(name=ConstraintName.MAXIMUM, value=4094),),
    )

    assert version.constraints[0].value == 4094


def test_negative_integer_bounds_valid() -> None:
    version = DataTypeVersion(
        datatype_id=uuid4(),
        version=1,
        status=DataTypeVersionStatus.DRAFT,
        base_type=_base_type("core.integer"),
        constraints=(Constraint(name=ConstraintName.MINIMUM, value=-10),),
    )

    assert version.constraints[0].value == -10


@pytest.mark.parametrize(
    ("name", "value"),
    [
        (ConstraintName.MINIMUM, True),
        (ConstraintName.MAXIMUM, False),
        (ConstraintName.MINIMUM, 1.5),
        (ConstraintName.MAXIMUM, "10"),
    ],
)
def test_invalid_integer_bounds_rejected(name: ConstraintName, value: object) -> None:
    with pytest.raises(InvalidConstraintValue):
        DataTypeVersion(
            datatype_id=uuid4(),
            version=1,
            status=DataTypeVersionStatus.DRAFT,
            base_type=_base_type("core.integer"),
            constraints=(Constraint(name=name, value=value),),
        )


def test_integer_enum_works() -> None:
    version = DataTypeVersion(
        datatype_id=uuid4(),
        version=1,
        status=DataTypeVersionStatus.DRAFT,
        base_type=_base_type("core.integer"),
        constraints=(Constraint(name=ConstraintName.ENUM, value=(1, 2, 3)),),
    )

    assert version.constraints[0].value == (1, 2, 3)


def test_bool_rejected_inside_integer_enum() -> None:
    with pytest.raises(InvalidConstraintValue):
        DataTypeVersion(
            datatype_id=uuid4(),
            version=1,
            status=DataTypeVersionStatus.DRAFT,
            base_type=_base_type("core.integer"),
            constraints=(Constraint(name=ConstraintName.ENUM, value=(1, True)),),
        )


def test_int_minimum_for_number_is_valid() -> None:
    version = DataTypeVersion(
        datatype_id=uuid4(),
        version=1,
        status=DataTypeVersionStatus.DRAFT,
        base_type=_base_type("core.number"),
        constraints=(Constraint(name=ConstraintName.MINIMUM, value=1),),
    )

    assert version.constraints[0].value == 1


def test_very_large_integer_minimum_for_number_is_valid() -> None:
    large_integer = 10**1000

    version = DataTypeVersion(
        datatype_id=uuid4(),
        version=1,
        status=DataTypeVersionStatus.DRAFT,
        base_type=_base_type("core.number"),
        constraints=(Constraint(name=ConstraintName.MINIMUM, value=large_integer),),
    )

    assert version.constraints[0].value == large_integer


def test_float_maximum_for_number_is_valid() -> None:
    version = DataTypeVersion(
        datatype_id=uuid4(),
        version=1,
        status=DataTypeVersionStatus.DRAFT,
        base_type=_base_type("core.number"),
        constraints=(Constraint(name=ConstraintName.MAXIMUM, value=10.5),),
    )

    assert version.constraints[0].value == 10.5


def test_very_large_integer_maximum_for_number_is_valid() -> None:
    large_integer = 10**1000

    version = DataTypeVersion(
        datatype_id=uuid4(),
        version=1,
        status=DataTypeVersionStatus.DRAFT,
        base_type=_base_type("core.number"),
        constraints=(Constraint(name=ConstraintName.MAXIMUM, value=large_integer),),
    )

    assert version.constraints[0].value == large_integer


@pytest.mark.parametrize("value", [True, nan, inf, -inf])
def test_invalid_number_bounds_rejected(value: object) -> None:
    with pytest.raises(InvalidConstraintValue):
        DataTypeVersion(
            datatype_id=uuid4(),
            version=1,
            status=DataTypeVersionStatus.DRAFT,
            base_type=_base_type("core.number"),
            constraints=(Constraint(name=ConstraintName.MINIMUM, value=value),),
        )


def test_numeric_enum_supports_finite_ints_and_floats() -> None:
    version = DataTypeVersion(
        datatype_id=uuid4(),
        version=1,
        status=DataTypeVersionStatus.DRAFT,
        base_type=_base_type("core.number"),
        constraints=(Constraint(name=ConstraintName.ENUM, value=(1, 2.5, -3)),),
    )

    assert version.constraints[0].value == (1, 2.5, -3)


@pytest.mark.parametrize("enum_values", [("1", "2"), (1, nan), (1, inf), (1, True)])
def test_invalid_non_numeric_number_enum_values_rejected(enum_values: tuple[object, ...]) -> None:
    with pytest.raises(InvalidConstraintValue):
        DataTypeVersion(
            datatype_id=uuid4(),
            version=1,
            status=DataTypeVersionStatus.DRAFT,
            base_type=_base_type("core.number"),
            constraints=(Constraint(name=ConstraintName.ENUM, value=enum_values),),
        )


def test_boolean_enum_works() -> None:
    version = DataTypeVersion(
        datatype_id=uuid4(),
        version=1,
        status=DataTypeVersionStatus.DRAFT,
        base_type=_base_type("core.boolean"),
        constraints=(Constraint(name=ConstraintName.ENUM, value=(True, False)),),
    )

    assert version.constraints[0].value == (True, False)


def test_integer_values_rejected_as_boolean_enum_values() -> None:
    with pytest.raises(InvalidConstraintValue):
        DataTypeVersion(
            datatype_id=uuid4(),
            version=1,
            status=DataTypeVersionStatus.DRAFT,
            base_type=_base_type("core.boolean"),
            constraints=(Constraint(name=ConstraintName.ENUM, value=(0, 1)),),
        )


@pytest.mark.parametrize(
    ("primitive_name", "constraint"),
    [
        ("core.integer", Constraint(name=ConstraintName.MIN_LENGTH, value=1)),
        ("core.boolean", Constraint(name=ConstraintName.PATTERN, value="yes|no")),
        ("core.string", Constraint(name=ConstraintName.MINIMUM, value=1)),
        ("core.number", Constraint(name=ConstraintName.MAX_LENGTH, value=5)),
        ("core.boolean", Constraint(name=ConstraintName.MAXIMUM, value=1)),
    ],
)
def test_unsupported_constraint_combinations_fail(
    primitive_name: str, constraint: Constraint
) -> None:
    with pytest.raises(UnsupportedConstraint):
        DataTypeVersion(
            datatype_id=uuid4(),
            version=1,
            status=DataTypeVersionStatus.DRAFT,
            base_type=_base_type(primitive_name),
            constraints=(constraint,),
        )


def test_duplicate_constraint_name_rejected() -> None:
    with pytest.raises(DuplicateConstraint):
        DataTypeVersion(
            datatype_id=uuid4(),
            version=1,
            status=DataTypeVersionStatus.DRAFT,
            base_type=_base_type("core.integer"),
            constraints=(
                Constraint(name=ConstraintName.MINIMUM, value=1),
                Constraint(name=ConstraintName.MINIMUM, value=10),
            ),
        )


def test_empty_enum_rejected() -> None:
    with pytest.raises(InvalidConstraintValue):
        DataTypeVersion(
            datatype_id=uuid4(),
            version=1,
            status=DataTypeVersionStatus.DRAFT,
            base_type=_base_type("core.string"),
            constraints=(Constraint(name=ConstraintName.ENUM, value=()),),
        )


def test_duplicate_enum_values_rejected() -> None:
    with pytest.raises(InvalidConstraintValue):
        DataTypeVersion(
            datatype_id=uuid4(),
            version=1,
            status=DataTypeVersionStatus.DRAFT,
            base_type=_base_type("core.string"),
            constraints=(Constraint(name=ConstraintName.ENUM, value=("active", "active")),),
        )


def test_unhashable_invalid_enum_value_raises_invalid_constraint_value() -> None:
    with pytest.raises(InvalidConstraintValue):
        DataTypeVersion(
            datatype_id=uuid4(),
            version=1,
            status=DataTypeVersionStatus.DRAFT,
            base_type=_base_type("core.string"),
            constraints=(Constraint(name=ConstraintName.ENUM, value=(["invalid"],)),),
        )


@pytest.mark.parametrize(
    ("primitive_name", "enum_values"),
    [
        ("core.string", ("active", 1)),
        ("core.integer", ("1", "2")),
        ("core.boolean", (True, 1)),
    ],
)
def test_mixed_incompatible_enum_values_rejected(
    primitive_name: str, enum_values: tuple[object, ...]
) -> None:
    with pytest.raises(InvalidConstraintValue):
        DataTypeVersion(
            datatype_id=uuid4(),
            version=1,
            status=DataTypeVersionStatus.DRAFT,
            base_type=_base_type(primitive_name),
            constraints=(Constraint(name=ConstraintName.ENUM, value=enum_values),),
        )


def test_minimum_greater_than_maximum_rejected() -> None:
    with pytest.raises(ConflictingConstraints):
        DataTypeVersion(
            datatype_id=uuid4(),
            version=1,
            status=DataTypeVersionStatus.DRAFT,
            base_type=_base_type("core.integer"),
            constraints=(
                Constraint(name=ConstraintName.MINIMUM, value=100),
                Constraint(name=ConstraintName.MAXIMUM, value=10),
            ),
        )


def test_minimum_equal_maximum_accepted() -> None:
    version = DataTypeVersion(
        datatype_id=uuid4(),
        version=1,
        status=DataTypeVersionStatus.DRAFT,
        base_type=_base_type("core.number"),
        constraints=(
            Constraint(name=ConstraintName.MINIMUM, value=10),
            Constraint(name=ConstraintName.MAXIMUM, value=10),
        ),
    )

    assert len(version.constraints) == 2


def test_network_hostname_example() -> None:
    datatype = DataType(id=uuid4(), namespace="network", name="hostname")

    version = DataTypeVersion(
        datatype_id=datatype.id,
        version=1,
        status=DataTypeVersionStatus.DRAFT,
        base_type=_base_type("core.string"),
        constraints=(
            Constraint(name=ConstraintName.MIN_LENGTH, value=1),
            Constraint(name=ConstraintName.MAX_LENGTH, value=253),
        ),
    )

    assert datatype.qualified_name == "network.hostname"
    assert version.base_type.name == "core.string"


def test_network_vlan_id_example() -> None:
    datatype = DataType(id=uuid4(), namespace="network", name="vlan_id")

    version = DataTypeVersion(
        datatype_id=datatype.id,
        version=1,
        status=DataTypeVersionStatus.DRAFT,
        base_type=_base_type("core.integer"),
        constraints=(
            Constraint(name=ConstraintName.MINIMUM, value=1),
            Constraint(name=ConstraintName.MAXIMUM, value=4094),
        ),
    )

    assert datatype.qualified_name == "network.vlan_id"
    assert version.base_type.name == "core.integer"


def test_asset_status_enum_example() -> None:
    datatype = DataType(id=uuid4(), namespace="asset", name="status")

    version = DataTypeVersion(
        datatype_id=datatype.id,
        version=1,
        status=DataTypeVersionStatus.DRAFT,
        base_type=_base_type("core.string"),
        constraints=(
            Constraint(
                name=ConstraintName.ENUM,
                value=("active", "planned", "retired"),
            ),
        ),
    )

    assert datatype.qualified_name == "asset.status"
    assert version.constraints[0].value == ("active", "planned", "retired")


@pytest.mark.parametrize(
    ("primitive_name", "constraint"),
    [
        (
            "core.date",
            Constraint(name=ConstraintName.PATTERN, value=r"^\d{4}-\d{2}-\d{2}$"),
        ),
        (
            "core.datetime",
            Constraint(name=ConstraintName.MINIMUM, value=1),
        ),
        (
            "core.datetime",
            Constraint(name=ConstraintName.ENUM, value=("2026-08-10T15:14:00Z",)),
        ),
    ],
)
def test_temporal_primitives_reject_all_constraints(
    primitive_name: str, constraint: Constraint
) -> None:
    with pytest.raises(UnsupportedConstraint):
        DataTypeVersion(
            datatype_id=uuid4(),
            version=1,
            status=DataTypeVersionStatus.DRAFT,
            base_type=_base_type(primitive_name),
            constraints=(constraint,),
        )
