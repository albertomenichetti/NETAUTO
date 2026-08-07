from uuid import uuid4

import pytest

from netauto.core.datatype import (
    DataType,
    DataTypeVersion,
    DataTypeVersionStatus,
    InvalidDataTypeIdentifier,
    InvalidDataTypeVersion,
    PrimitiveTypeRegistry,
)


def test_valid_datatype_creation() -> None:
    datatype = DataType(
        id=uuid4(),
        namespace="network",
        name="vlan_id",
        description="A VLAN identifier.",
    )

    assert datatype.namespace == "network"
    assert datatype.name == "vlan_id"
    assert datatype.description == "A VLAN identifier."


def test_qualified_name() -> None:
    datatype = DataType(id=uuid4(), namespace="network", name="vlan_id")

    assert datatype.qualified_name == "network.vlan_id"


def test_optional_description() -> None:
    datatype = DataType(id=uuid4(), namespace="network", name="vlan_id")

    assert datatype.description is None


@pytest.mark.parametrize("namespace", ["", "Network", "network-core", "1network"])
def test_invalid_namespace(namespace: str) -> None:
    with pytest.raises(InvalidDataTypeIdentifier):
        DataType(id=uuid4(), namespace=namespace, name="vlan_id")


@pytest.mark.parametrize("name", ["", "VlanId", "vlan-id", "1vlan"])
def test_invalid_name(name: str) -> None:
    with pytest.raises(InvalidDataTypeIdentifier):
        DataType(id=uuid4(), namespace="network", name=name)


def test_version_numbers_start_at_1() -> None:
    primitive_type = PrimitiveTypeRegistry().get("core.integer")

    version = DataTypeVersion(
        datatype_id=uuid4(),
        version=1,
        status=DataTypeVersionStatus.DRAFT,
        base_type=primitive_type,
    )

    assert version.version == 1


@pytest.mark.parametrize("version", [0, -1, -10])
def test_version_zero_and_negative_versions_are_rejected(version: int) -> None:
    primitive_type = PrimitiveTypeRegistry().get("core.integer")

    with pytest.raises(InvalidDataTypeVersion):
        DataTypeVersion(
            datatype_id=uuid4(),
            version=version,
            status=DataTypeVersionStatus.DRAFT,
            base_type=primitive_type,
        )


def test_all_three_status_values() -> None:
    assert DataTypeVersionStatus.DRAFT == "draft"
    assert DataTypeVersionStatus.PUBLISHED == "published"
    assert DataTypeVersionStatus.DEPRECATED == "deprecated"


def test_datatype_version_holds_primitive_type_instance() -> None:
    primitive_type = PrimitiveTypeRegistry().get("core.integer")

    version = DataTypeVersion(
        datatype_id=uuid4(),
        version=1,
        status=DataTypeVersionStatus.DRAFT,
        base_type=primitive_type,
    )

    assert version.base_type is primitive_type


def test_network_vlan_id_core_integer_example() -> None:
    datatype = DataType(id=uuid4(), namespace="network", name="vlan_id")
    primitive_type = PrimitiveTypeRegistry().get("core.integer")

    version = DataTypeVersion(
        datatype_id=datatype.id,
        version=1,
        status=DataTypeVersionStatus.DRAFT,
        base_type=primitive_type,
    )

    assert datatype.qualified_name == "network.vlan_id"
    assert version.datatype_id == datatype.id
    assert version.base_type.name == "core.integer"
