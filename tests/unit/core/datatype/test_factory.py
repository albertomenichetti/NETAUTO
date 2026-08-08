from uuid import UUID

import pytest

from netauto.core.datatype import (
    Constraint,
    ConstraintName,
    DataTypeFactory,
    DataTypeVersionStatus,
    InvalidConstraintValue,
    InvalidDataTypeIdentifier,
    PrimitiveTypeNotFound,
    ReservedDataTypeNamespace,
    SchemaCompiler,
    UnsupportedConstraint,
    ValidationEngine,
    ValidationIssue,
)


def test_basic_creation() -> None:
    datatype, version = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description="Network hostname",
        base_type="core.string",
        constraints=(
            Constraint(name=ConstraintName.MIN_LENGTH, value=1),
            Constraint(name=ConstraintName.MAX_LENGTH, value=253),
        ),
    )

    assert isinstance(datatype.id, UUID)
    assert datatype.namespace == "network"
    assert datatype.name == "hostname"
    assert datatype.qualified_name == "network.hostname"
    assert datatype.description == "Network hostname"
    assert version.datatype_id == datatype.id
    assert version.version == 1
    assert version.status is DataTypeVersionStatus.DRAFT
    assert version.base_type.name == "core.string"
    assert version.constraints == (
        Constraint(name=ConstraintName.MIN_LENGTH, value=1),
        Constraint(name=ConstraintName.MAX_LENGTH, value=253),
    )


def test_uuid_generation_differs_between_creations() -> None:
    first_datatype, _ = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description=None,
        base_type="core.string",
    )
    second_datatype, _ = DataTypeFactory().create(
        namespace="asset",
        name="status",
        description=None,
        base_type="core.string",
    )

    assert first_datatype.id != second_datatype.id


def test_same_logical_name_does_not_enforce_global_uniqueness() -> None:
    first_datatype, _ = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description=None,
        base_type="core.string",
    )
    second_datatype, _ = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description=None,
        base_type="core.string",
    )

    assert first_datatype.qualified_name == second_datatype.qualified_name
    assert first_datatype.id != second_datatype.id


@pytest.mark.parametrize(
    "primitive_name",
    ["core.string", "core.integer", "core.number", "core.boolean"],
)
def test_all_current_primitives_can_be_used(primitive_name: str) -> None:
    _, version = DataTypeFactory().create(
        namespace="network",
        name="value",
        description=None,
        base_type=primitive_name,
    )

    assert version.base_type.name == primitive_name


def test_unknown_primitive_raises_primitive_type_not_found() -> None:
    with pytest.raises(PrimitiveTypeNotFound):
        DataTypeFactory().create(
            namespace="network",
            name="hostname",
            description=None,
            base_type="core.unknown",
        )


def test_custom_on_custom_base_type_is_not_supported() -> None:
    with pytest.raises(PrimitiveTypeNotFound):
        DataTypeFactory().create(
            namespace="network",
            name="hostname_v2",
            description=None,
            base_type="network.hostname",
        )


def test_reserved_core_namespace_is_rejected() -> None:
    with pytest.raises(ReservedDataTypeNamespace):
        DataTypeFactory().create(
            namespace="core",
            name="hostname",
            description=None,
            base_type="core.string",
        )


@pytest.mark.parametrize("namespace", ["network", "asset", "infrastructure"])
def test_normal_namespaces_are_allowed(namespace: str) -> None:
    datatype, _ = DataTypeFactory().create(
        namespace=namespace,
        name="hostname",
        description=None,
        base_type="core.string",
    )

    assert datatype.namespace == namespace


@pytest.mark.parametrize(
    ("namespace", "name"),
    [("Network", "hostname"), ("network", "HostName"), ("1network", "hostname")],
)
def test_identifier_validation_is_preserved(namespace: str, name: str) -> None:
    with pytest.raises(InvalidDataTypeIdentifier):
        DataTypeFactory().create(
            namespace=namespace,
            name=name,
            description=None,
            base_type="core.string",
        )


def test_constraints_are_attached_to_created_version() -> None:
    _, version = DataTypeFactory().create(
        namespace="network",
        name="vlan_id",
        description="VLAN identifier",
        base_type="core.integer",
        constraints=(
            Constraint(name=ConstraintName.MINIMUM, value=1),
            Constraint(name=ConstraintName.MAXIMUM, value=4094),
        ),
    )

    assert version.constraints == (
        Constraint(name=ConstraintName.MINIMUM, value=1),
        Constraint(name=ConstraintName.MAXIMUM, value=4094),
    )


def test_constraint_exceptions_propagate_unchanged() -> None:
    with pytest.raises(UnsupportedConstraint):
        DataTypeFactory().create(
            namespace="network",
            name="invalid_boolean",
            description=None,
            base_type="core.boolean",
            constraints=(Constraint(name=ConstraintName.MINIMUM, value=1),),
        )


def test_constraint_value_exceptions_propagate_unchanged() -> None:
    with pytest.raises(InvalidConstraintValue):
        DataTypeFactory().create(
            namespace="network",
            name="bad_hostname",
            description=None,
            base_type="core.string",
            constraints=(Constraint(name=ConstraintName.MIN_LENGTH, value=-1),),
        )


def test_caller_collection_independence() -> None:
    constraints = [Constraint(name=ConstraintName.MIN_LENGTH, value=1)]

    _, version = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description=None,
        base_type="core.string",
        constraints=constraints,
    )
    constraints.append(Constraint(name=ConstraintName.MAX_LENGTH, value=253))

    assert version.constraints == (Constraint(name=ConstraintName.MIN_LENGTH, value=1),)


def test_compiler_integration_for_network_hostname() -> None:
    _, version = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description="Network hostname",
        base_type="core.string",
        constraints=(
            Constraint(name=ConstraintName.MIN_LENGTH, value=1),
            Constraint(name=ConstraintName.MAX_LENGTH, value=253),
        ),
    )

    schema = SchemaCompiler().compile_datatype(version)

    assert schema == {
        "type": "string",
        "minLength": 1,
        "maxLength": 253,
    }


def test_compiler_integration_for_network_vlan_id() -> None:
    _, version = DataTypeFactory().create(
        namespace="network",
        name="vlan_id",
        description="VLAN identifier",
        base_type="core.integer",
        constraints=(
            Constraint(name=ConstraintName.MINIMUM, value=1),
            Constraint(name=ConstraintName.MAXIMUM, value=4094),
        ),
    )

    schema = SchemaCompiler().compile_datatype(version)

    assert schema == {
        "type": "integer",
        "minimum": 1,
        "maximum": 4094,
    }


def test_validation_integration_for_network_hostname() -> None:
    _, version = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description="Network hostname",
        base_type="core.string",
        constraints=(
            Constraint(name=ConstraintName.MIN_LENGTH, value=1),
            Constraint(name=ConstraintName.MAX_LENGTH, value=253),
        ),
    )
    engine = ValidationEngine()

    assert engine.validate_datatype(version, "router01").is_valid is True
    assert engine.validate_datatype(version, "").errors == (
        ValidationIssue(
            path=(),
            code="min_length",
            message="Value is shorter than the minimum allowed length",
        ),
    )
    assert engine.validate_datatype(version, 123).errors == (
        ValidationIssue(path=(), code="type", message="Value is not of the expected type"),
    )


def test_validation_integration_for_network_vlan_id() -> None:
    _, version = DataTypeFactory().create(
        namespace="network",
        name="vlan_id",
        description="VLAN identifier",
        base_type="core.integer",
        constraints=(
            Constraint(name=ConstraintName.MINIMUM, value=1),
            Constraint(name=ConstraintName.MAXIMUM, value=4094),
        ),
    )
    engine = ValidationEngine()

    assert engine.validate_datatype(version, 1).is_valid is True
    assert engine.validate_datatype(version, 4094).is_valid is True
    assert engine.validate_datatype(version, 0).errors == (
        ValidationIssue(
            path=(),
            code="minimum",
            message="Value is below the minimum allowed value",
        ),
    )
    assert engine.validate_datatype(version, 4095).errors == (
        ValidationIssue(
            path=(),
            code="maximum",
            message="Value exceeds the maximum allowed value",
        ),
    )
    assert engine.validate_datatype(version, 1.0).errors == (
        ValidationIssue(path=(), code="type", message="Value is not of the expected type"),
    )
    assert engine.validate_datatype(version, True).errors == (
        ValidationIssue(path=(), code="type", message="Value is not of the expected type"),
    )


def test_validation_integration_for_network_device_status() -> None:
    _, version = DataTypeFactory().create(
        namespace="network",
        name="device_status",
        description="Device status",
        base_type="core.string",
        constraints=(
            Constraint(
                name=ConstraintName.ENUM,
                value=("active", "planned", "retired"),
            ),
        ),
    )
    engine = ValidationEngine()

    assert engine.validate_datatype(version, "active").is_valid is True
    assert engine.validate_datatype(version, "banana").errors == (
        ValidationIssue(path=(), code="enum", message="Value is not one of the allowed values"),
    )


def test_every_created_custom_datatype_begins_as_v1_draft() -> None:
    _, version = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description=None,
        base_type="core.string",
    )

    assert version.version == 1
    assert version.status is DataTypeVersionStatus.DRAFT
