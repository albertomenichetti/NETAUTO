from dataclasses import FrozenInstanceError
from typing import cast
from uuid import uuid4

import pytest

from netauto.core.objecttemplate import (
    DuplicateObjectTemplateComponent,
    DuplicateObjectTemplateProperty,
    InvalidObjectTemplate,
    InvalidObjectTemplateIdentifier,
    InvalidObjectTemplateProperty,
    InvalidObjectTemplateVersion,
    ObjectTemplate,
    ObjectTemplateComponent,
    ObjectTemplateProperty,
    ObjectTemplateVersion,
    ObjectTemplateVersionRef,
    ObjectTemplateVersionStatus,
)


def test_valid_object_template_construction() -> None:
    template = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="device",
        description="Network device template",
        abstract=True,
    )

    assert template.namespace == "network"
    assert template.name == "device"
    assert template.description == "Network device template"
    assert template.abstract is True
    assert template.qualified_name == "network.device"


def test_object_template_is_immutable() -> None:
    template = ObjectTemplate(id=uuid4(), namespace="network", name="device")

    with pytest.raises(FrozenInstanceError):
        template.name = "server"  # type: ignore[misc]


@pytest.mark.parametrize("field_name", ["namespace", "name"])
@pytest.mark.parametrize("value", ["", "Network", "device-name", "1device"])
def test_object_template_rejects_invalid_identifiers(field_name: str, value: str) -> None:
    kwargs = {
        "id": uuid4(),
        "namespace": "network",
        "name": "device",
    }
    kwargs[field_name] = value

    with pytest.raises(InvalidObjectTemplateIdentifier):
        ObjectTemplate(**kwargs)


@pytest.mark.parametrize("value", [1, "true", None])
def test_object_template_requires_abstract_bool(value: object) -> None:
    with pytest.raises(InvalidObjectTemplate):
        ObjectTemplate(
            id=uuid4(),
            namespace="network",
            name="device",
            abstract=cast("bool", value),
        )


def test_object_template_version_ref_requires_plain_positive_int() -> None:
    assert ObjectTemplateVersionRef(template_id=uuid4(), version=1).version == 1

    for invalid_value in (0, -1, True, 1.0):
        with pytest.raises(InvalidObjectTemplateVersion):
            ObjectTemplateVersionRef(template_id=uuid4(), version=invalid_value)  # type: ignore[arg-type]


def test_object_template_property_valid_construction() -> None:
    property_definition = ObjectTemplateProperty(
        name="hostname",
        datatype_id=uuid4(),
        datatype_version=2,
        required=True,
    )

    assert property_definition.name == "hostname"
    assert property_definition.datatype_version == 2
    assert property_definition.required is True


def test_object_template_property_is_immutable() -> None:
    property_definition = ObjectTemplateProperty(
        name="hostname",
        datatype_id=uuid4(),
        datatype_version=1,
    )

    with pytest.raises(FrozenInstanceError):
        property_definition.required = True  # type: ignore[misc]


@pytest.mark.parametrize("value", ["", "host-name", "HostName", "1name"])
def test_object_template_property_rejects_invalid_name(value: str) -> None:
    with pytest.raises(InvalidObjectTemplateIdentifier):
        ObjectTemplateProperty(name=value, datatype_id=uuid4(), datatype_version=1)


@pytest.mark.parametrize("value", [0, -1, True, 1.0])
def test_object_template_property_requires_plain_positive_datatype_version(value: object) -> None:
    with pytest.raises(InvalidObjectTemplateProperty):
        ObjectTemplateProperty(
            name="hostname",
            datatype_id=uuid4(),
            datatype_version=value,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("value", [1, "true", None])
def test_object_template_property_requires_required_bool(value: object) -> None:
    with pytest.raises(InvalidObjectTemplateProperty):
        ObjectTemplateProperty(
            name="hostname",
            datatype_id=uuid4(),
            datatype_version=1,
            required=value,  # type: ignore[arg-type]
        )


def test_object_template_component_valid_construction() -> None:
    component = ObjectTemplateComponent(
        name="interfaces",
        template_id=uuid4(),
    )

    assert component.name == "interfaces"
    assert component.template_id


def test_object_template_component_is_immutable() -> None:
    component = ObjectTemplateComponent(
        name="interfaces",
        template_id=uuid4(),
    )

    with pytest.raises(FrozenInstanceError):
        component.template_id = uuid4()  # type: ignore[misc]


@pytest.mark.parametrize("value", ["", "interface-slots", "Interfaces", "1interfaces"])
def test_object_template_component_rejects_invalid_name(value: str) -> None:
    with pytest.raises(InvalidObjectTemplateIdentifier):
        ObjectTemplateComponent(name=value, template_id=uuid4())


def test_object_template_version_normalizes_properties_to_tuple() -> None:
    property_definition = ObjectTemplateProperty(
        name="hostname",
        datatype_id=uuid4(),
        datatype_version=1,
    )
    version = ObjectTemplateVersion(
        template_id=uuid4(),
        version=1,
        status=ObjectTemplateVersionStatus.DRAFT,
        properties=cast("tuple[ObjectTemplateProperty, ...]", [property_definition]),
    )

    assert version.properties == (property_definition,)
    assert isinstance(version.properties, tuple)


def test_object_template_version_normalizes_components_to_tuple() -> None:
    component = ObjectTemplateComponent(
        name="interfaces",
        template_id=uuid4(),
    )
    version = ObjectTemplateVersion(
        template_id=uuid4(),
        version=1,
        status=ObjectTemplateVersionStatus.DRAFT,
        components=cast("tuple[ObjectTemplateComponent, ...]", [component]),
    )

    assert version.components == (component,)
    assert isinstance(version.components, tuple)


def test_object_template_version_valid_construction_with_parent() -> None:
    template_id = uuid4()
    parent = ObjectTemplateVersionRef(template_id=uuid4(), version=2)
    property_definition = ObjectTemplateProperty(
        name="hostname",
        datatype_id=uuid4(),
        datatype_version=1,
        required=True,
    )

    version = ObjectTemplateVersion(
        template_id=template_id,
        version=3,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        parent=parent,
        properties=(property_definition,),
    )

    assert version.template_id == template_id
    assert version.version == 3
    assert version.status is ObjectTemplateVersionStatus.PUBLISHED
    assert version.parent == parent
    assert version.properties == (property_definition,)


def test_object_template_version_properties_and_components_can_coexist() -> None:
    property_definition = ObjectTemplateProperty(
        name="hostname",
        datatype_id=uuid4(),
        datatype_version=1,
    )
    component = ObjectTemplateComponent(
        name="interfaces",
        template_id=uuid4(),
    )

    version = ObjectTemplateVersion(
        template_id=uuid4(),
        version=1,
        status=ObjectTemplateVersionStatus.DRAFT,
        properties=(property_definition,),
        components=(component,),
    )

    assert version.properties == (property_definition,)
    assert version.components == (component,)


@pytest.mark.parametrize("value", [0, -1, True, 1.0])
def test_object_template_version_requires_plain_positive_version(value: object) -> None:
    with pytest.raises(InvalidObjectTemplateVersion):
        ObjectTemplateVersion(
            template_id=uuid4(),
            version=value,  # type: ignore[arg-type]
            status=ObjectTemplateVersionStatus.DRAFT,
        )


def test_object_template_version_rejects_duplicate_local_property_names() -> None:
    datatype_id = uuid4()
    property_a = ObjectTemplateProperty(
        name="hostname",
        datatype_id=datatype_id,
        datatype_version=1,
    )
    property_b = ObjectTemplateProperty(
        name="hostname",
        datatype_id=datatype_id,
        datatype_version=2,
    )

    with pytest.raises(DuplicateObjectTemplateProperty):
        ObjectTemplateVersion(
            template_id=uuid4(),
            version=1,
            status=ObjectTemplateVersionStatus.DRAFT,
            properties=(property_a, property_b),
        )


def test_object_template_version_rejects_duplicate_local_component_names() -> None:
    template_id = uuid4()
    component_a = ObjectTemplateComponent(
        name="interfaces",
        template_id=template_id,
    )
    component_b = ObjectTemplateComponent(
        name="interfaces",
        template_id=uuid4(),
    )

    with pytest.raises(DuplicateObjectTemplateComponent):
        ObjectTemplateVersion(
            template_id=uuid4(),
            version=1,
            status=ObjectTemplateVersionStatus.DRAFT,
            components=(component_a, component_b),
        )


def test_object_template_version_is_immutable() -> None:
    version = ObjectTemplateVersion(
        template_id=uuid4(),
        version=1,
        status=ObjectTemplateVersionStatus.DRAFT,
    )

    with pytest.raises(FrozenInstanceError):
        version.status = ObjectTemplateVersionStatus.PUBLISHED  # type: ignore[misc]


def test_object_template_version_status_values() -> None:
    assert ObjectTemplateVersionStatus.DRAFT.value == "draft"
    assert ObjectTemplateVersionStatus.PUBLISHED.value == "published"
    assert ObjectTemplateVersionStatus.DEPRECATED.value == "deprecated"
