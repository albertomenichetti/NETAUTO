from dataclasses import FrozenInstanceError
from types import MappingProxyType
from uuid import uuid4

import pytest

from netauto.core.object import InvalidObject, Object


def test_valid_object_with_empty_properties() -> None:
    object_value = Object(
        id=uuid4(),
        template_id=uuid4(),
        template_version=1,
        properties={},
    )

    assert object_value.template_version == 1
    assert object_value.properties == {}


def test_valid_object_with_primitive_properties_preserves_exact_pin() -> None:
    object_id = uuid4()
    template_id = uuid4()
    object_value = Object(
        id=object_id,
        template_id=template_id,
        template_version=3,
        properties={
            "hostname": "router-01",
            "serial": "ABC123",
            "enabled": True,
            "vlan": 100,
        },
    )

    assert object_value.id == object_id
    assert object_value.template_id == template_id
    assert object_value.template_version == 3
    assert object_value.properties["hostname"] == "router-01"
    assert object_value.properties["enabled"] is True


@pytest.mark.parametrize("value", [True, False, 0, -1, 1.0, "1", None])
def test_object_requires_plain_positive_template_version(value: object) -> None:
    with pytest.raises(InvalidObject):
        Object(
            id=uuid4(),
            template_id=uuid4(),
            template_version=value,  # type: ignore[arg-type]
            properties={},
        )


@pytest.mark.parametrize("value", [None, [], (), "hostname"])
def test_object_rejects_non_mapping_properties(value: object) -> None:
    with pytest.raises(InvalidObject):
        Object(
            id=uuid4(),
            template_id=uuid4(),
            template_version=1,
            properties=value,  # type: ignore[arg-type]
        )


def test_object_rejects_non_string_property_key() -> None:
    with pytest.raises(InvalidObject):
        Object(
            id=uuid4(),
            template_id=uuid4(),
            template_version=1,
            properties={1: "router-01"},  # type: ignore[dict-item]
        )


def test_object_is_immutable() -> None:
    object_value = Object(
        id=uuid4(),
        template_id=uuid4(),
        template_version=1,
        properties={},
    )

    with pytest.raises(FrozenInstanceError):
        object_value.template_version = 2  # type: ignore[misc]


def test_object_properties_are_read_only() -> None:
    object_value = Object(
        id=uuid4(),
        template_id=uuid4(),
        template_version=1,
        properties={"hostname": "router-01"},
    )

    assert isinstance(object_value.properties, MappingProxyType)
    with pytest.raises(TypeError):
        object_value.properties["hostname"] = "router-02"  # type: ignore[index]


def test_object_copies_original_property_mapping() -> None:
    source = {"hostname": "router-01"}
    object_value = Object(
        id=uuid4(),
        template_id=uuid4(),
        template_version=1,
        properties=source,
    )

    source["hostname"] = "router-02"
    source["serial"] = "ABC123"

    assert object_value.properties == {"hostname": "router-01"}
