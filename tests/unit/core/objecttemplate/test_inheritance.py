from uuid import UUID, uuid4

import pytest

from netauto.core.objecttemplate import (
    InheritedObjectTemplateComponentConflict,
    InheritedObjectTemplatePropertyConflict,
    ObjectTemplateComponent,
    ObjectTemplateInheritanceCycle,
    ObjectTemplateInheritanceResolver,
    ObjectTemplateParentNotFound,
    ObjectTemplateProperty,
    ObjectTemplateSelfInheritance,
    ObjectTemplateVersion,
    ObjectTemplateVersionRef,
    ObjectTemplateVersionStatus,
)


def _property(name: str) -> ObjectTemplateProperty:
    return ObjectTemplateProperty(name=name, datatype_id=uuid4(), datatype_version=1)


def _component(name: str) -> ObjectTemplateComponent:
    return ObjectTemplateComponent(name=name, template_id=uuid4(), template_version=1)


def _version(
    template_id: UUID,
    version: int,
    *,
    parent: ObjectTemplateVersionRef | None = None,
    properties: tuple[ObjectTemplateProperty, ...] = (),
    components: tuple[ObjectTemplateComponent, ...] = (),
) -> ObjectTemplateVersion:
    return ObjectTemplateVersion(
        template_id=template_id,
        version=version,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=parent,
        properties=properties,
        components=components,
    )


def test_resolve_effective_properties_without_parent() -> None:
    version = _version(uuid4(), 1, properties=(_property("hostname"), _property("serial")))

    result = ObjectTemplateInheritanceResolver().resolve_effective_properties(
        version,
        parent_lookup=lambda _: None,
    )

    assert tuple(prop.name for prop in result) == ("hostname", "serial")


def test_resolve_effective_properties_with_one_parent() -> None:
    parent_id = uuid4()
    parent = _version(parent_id, 1, properties=(_property("hostname"), _property("serial")))
    child = _version(
        uuid4(),
        1,
        parent=ObjectTemplateVersionRef(template_id=parent_id, version=1),
        properties=(_property("routing_id"),),
    )

    versions = {(parent_id, 1): parent}

    result = ObjectTemplateInheritanceResolver().resolve_effective_properties(
        child,
        parent_lookup=lambda ref: versions.get((ref.template_id, ref.version)),
    )

    assert tuple(prop.name for prop in result) == ("hostname", "serial", "routing_id")


def test_resolve_effective_properties_with_multiple_levels() -> None:
    base_id = uuid4()
    router_id = uuid4()
    edge_id = uuid4()
    base = _version(base_id, 1, properties=(_property("hostname"), _property("serial")))
    router = _version(
        router_id,
        2,
        parent=ObjectTemplateVersionRef(template_id=base_id, version=1),
        properties=(_property("routing_id"),),
    )
    edge = _version(
        edge_id,
        3,
        parent=ObjectTemplateVersionRef(template_id=router_id, version=2),
        properties=(_property("uplink_name"), _property("asn")),
    )
    versions = {
        (base_id, 1): base,
        (router_id, 2): router,
    }

    result = ObjectTemplateInheritanceResolver().resolve_effective_properties(
        edge,
        parent_lookup=lambda ref: versions.get((ref.template_id, ref.version)),
    )

    assert tuple(prop.name for prop in result) == (
        "hostname",
        "serial",
        "routing_id",
        "uplink_name",
        "asn",
    )


def test_effective_property_order_is_ancestor_first_and_preserves_local_order() -> None:
    grandparent_id = uuid4()
    parent_id = uuid4()
    grandparent = _version(
        grandparent_id,
        1,
        properties=(_property("hostname"), _property("serial")),
    )
    parent = _version(
        parent_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=grandparent_id, version=1),
        properties=(_property("site"), _property("role")),
    )
    child = _version(
        uuid4(),
        1,
        parent=ObjectTemplateVersionRef(template_id=parent_id, version=1),
        properties=(_property("mgmt_ip"), _property("loopback_ip")),
    )
    versions = {
        (grandparent_id, 1): grandparent,
        (parent_id, 1): parent,
    }

    result = ObjectTemplateInheritanceResolver().resolve_effective_properties(
        child,
        parent_lookup=lambda ref: versions.get((ref.template_id, ref.version)),
    )

    assert tuple(prop.name for prop in result) == (
        "hostname",
        "serial",
        "site",
        "role",
        "mgmt_ip",
        "loopback_ip",
    )


def test_missing_parent_raises_focused_error() -> None:
    child = _version(
        uuid4(),
        1,
        parent=ObjectTemplateVersionRef(template_id=uuid4(), version=1),
        properties=(_property("hostname"),),
    )

    with pytest.raises(ObjectTemplateParentNotFound):
        ObjectTemplateInheritanceResolver().resolve_effective_properties(
            child,
            parent_lookup=lambda _: None,
        )


def test_same_template_same_version_parent_is_rejected() -> None:
    template_id = uuid4()
    version = _version(
        template_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=template_id, version=1),
    )

    with pytest.raises(ObjectTemplateSelfInheritance):
        ObjectTemplateInheritanceResolver().resolve_effective_properties(
            version,
            parent_lookup=lambda _: pytest.fail("parent_lookup should not be called"),
        )


def test_same_template_different_version_parent_is_rejected() -> None:
    template_id = uuid4()
    version = _version(
        template_id,
        2,
        parent=ObjectTemplateVersionRef(template_id=template_id, version=1),
    )

    with pytest.raises(ObjectTemplateSelfInheritance):
        ObjectTemplateInheritanceResolver().resolve_effective_properties(
            version,
            parent_lookup=lambda _: pytest.fail("parent_lookup should not be called"),
        )


def test_indirect_cycle_between_different_templates_is_rejected() -> None:
    first_id = uuid4()
    second_id = uuid4()
    first = _version(
        first_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=second_id, version=1),
        properties=(_property("hostname"),),
    )
    second = _version(
        second_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=first_id, version=1),
        properties=(_property("serial"),),
    )
    versions = {
        (first_id, 1): first,
        (second_id, 1): second,
    }

    with pytest.raises(ObjectTemplateInheritanceCycle):
        ObjectTemplateInheritanceResolver().resolve_effective_properties(
            first,
            parent_lookup=lambda ref: versions.get((ref.template_id, ref.version)),
        )


def test_local_property_name_conflicting_with_inherited_name_is_rejected() -> None:
    parent_id = uuid4()
    parent = _version(parent_id, 1, properties=(_property("hostname"), _property("serial")))
    child = _version(
        uuid4(),
        1,
        parent=ObjectTemplateVersionRef(template_id=parent_id, version=1),
        properties=(_property("hostname"),),
    )
    versions = {(parent_id, 1): parent}

    with pytest.raises(InheritedObjectTemplatePropertyConflict):
        ObjectTemplateInheritanceResolver().resolve_effective_properties(
            child,
            parent_lookup=lambda ref: versions.get((ref.template_id, ref.version)),
        )


def test_sibling_and_local_non_conflicting_properties_are_resolved() -> None:
    parent_id = uuid4()
    parent = _version(parent_id, 1, properties=(_property("hostname"), _property("serial")))
    child = _version(
        uuid4(),
        1,
        parent=ObjectTemplateVersionRef(template_id=parent_id, version=1),
        properties=(_property("routing_id"), _property("asn")),
    )
    versions = {(parent_id, 1): parent}

    result = ObjectTemplateInheritanceResolver().resolve_effective_properties(
        child,
        parent_lookup=lambda ref: versions.get((ref.template_id, ref.version)),
    )

    assert tuple(prop.name for prop in result) == ("hostname", "serial", "routing_id", "asn")


def test_resolve_effective_components_without_parent() -> None:
    version = _version(uuid4(), 1, components=(_component("interfaces"), _component("fans")))

    result = ObjectTemplateInheritanceResolver().resolve_effective_components(
        version,
        parent_lookup=lambda _: None,
    )

    assert tuple(component.name for component in result) == ("interfaces", "fans")


def test_resolve_effective_components_with_one_parent() -> None:
    parent_id = uuid4()
    parent = _version(parent_id, 1, components=(_component("interfaces"), _component("psus")))
    child = _version(
        uuid4(),
        1,
        parent=ObjectTemplateVersionRef(template_id=parent_id, version=1),
        components=(_component("routing_engines"),),
    )
    versions = {(parent_id, 1): parent}

    result = ObjectTemplateInheritanceResolver().resolve_effective_components(
        child,
        parent_lookup=lambda ref: versions.get((ref.template_id, ref.version)),
    )

    assert tuple(component.name for component in result) == (
        "interfaces",
        "psus",
        "routing_engines",
    )


def test_resolve_effective_components_with_multiple_levels() -> None:
    base_id = uuid4()
    router_id = uuid4()
    edge_id = uuid4()
    base = _version(base_id, 1, components=(_component("interfaces"),))
    router = _version(
        router_id,
        2,
        parent=ObjectTemplateVersionRef(template_id=base_id, version=1),
        components=(_component("routing_engines"),),
    )
    edge = _version(
        edge_id,
        3,
        parent=ObjectTemplateVersionRef(template_id=router_id, version=2),
        components=(_component("linecards"), _component("supervisors")),
    )
    versions = {
        (base_id, 1): base,
        (router_id, 2): router,
    }

    result = ObjectTemplateInheritanceResolver().resolve_effective_components(
        edge,
        parent_lookup=lambda ref: versions.get((ref.template_id, ref.version)),
    )

    assert tuple(component.name for component in result) == (
        "interfaces",
        "routing_engines",
        "linecards",
        "supervisors",
    )


def test_effective_component_order_is_ancestor_first_and_preserves_local_order() -> None:
    grandparent_id = uuid4()
    parent_id = uuid4()
    grandparent = _version(
        grandparent_id,
        1,
        components=(_component("interfaces"), _component("fans")),
    )
    parent = _version(
        parent_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=grandparent_id, version=1),
        components=(_component("psus"), _component("routing_engines")),
    )
    child = _version(
        uuid4(),
        1,
        parent=ObjectTemplateVersionRef(template_id=parent_id, version=1),
        components=(_component("linecards"), _component("supervisors")),
    )
    versions = {
        (grandparent_id, 1): grandparent,
        (parent_id, 1): parent,
    }

    result = ObjectTemplateInheritanceResolver().resolve_effective_components(
        child,
        parent_lookup=lambda ref: versions.get((ref.template_id, ref.version)),
    )

    assert tuple(component.name for component in result) == (
        "interfaces",
        "fans",
        "psus",
        "routing_engines",
        "linecards",
        "supervisors",
    )


def test_local_child_component_added_successfully() -> None:
    parent_id = uuid4()
    parent = _version(parent_id, 1, components=(_component("interfaces"),))
    child = _version(
        uuid4(),
        1,
        parent=ObjectTemplateVersionRef(template_id=parent_id, version=1),
        components=(_component("routing_engines"),),
    )
    versions = {(parent_id, 1): parent}

    result = ObjectTemplateInheritanceResolver().resolve_effective_components(
        child,
        parent_lookup=lambda ref: versions.get((ref.template_id, ref.version)),
    )

    assert tuple(component.name for component in result) == ("interfaces", "routing_engines")


def test_inherited_component_name_same_target_redeclaration_is_rejected() -> None:
    target_id = uuid4()
    parent_id = uuid4()
    parent = _version(
        parent_id,
        1,
        components=(
            ObjectTemplateComponent(
                name="interfaces",
                template_id=target_id,
                template_version=1,
            ),
        ),
    )
    child = _version(
        uuid4(),
        1,
        parent=ObjectTemplateVersionRef(template_id=parent_id, version=1),
        components=(
            ObjectTemplateComponent(
                name="interfaces",
                template_id=target_id,
                template_version=1,
            ),
        ),
    )
    versions = {(parent_id, 1): parent}

    with pytest.raises(InheritedObjectTemplateComponentConflict):
        ObjectTemplateInheritanceResolver().resolve_effective_components(
            child,
            parent_lookup=lambda ref: versions.get((ref.template_id, ref.version)),
        )


def test_inherited_component_name_different_target_redeclaration_is_rejected() -> None:
    parent_id = uuid4()
    parent = _version(parent_id, 1, components=(_component("interfaces"),))
    child = _version(
        uuid4(),
        1,
        parent=ObjectTemplateVersionRef(template_id=parent_id, version=1),
        components=(_component("interfaces"),),
    )
    versions = {(parent_id, 1): parent}

    with pytest.raises(InheritedObjectTemplateComponentConflict):
        ObjectTemplateInheritanceResolver().resolve_effective_components(
            child,
            parent_lookup=lambda ref: versions.get((ref.template_id, ref.version)),
        )


def test_resolve_effective_components_missing_parent_raises_focused_error() -> None:
    child = _version(
        uuid4(),
        1,
        parent=ObjectTemplateVersionRef(template_id=uuid4(), version=1),
        components=(_component("interfaces"),),
    )

    with pytest.raises(ObjectTemplateParentNotFound):
        ObjectTemplateInheritanceResolver().resolve_effective_components(
            child,
            parent_lookup=lambda _: None,
        )


def test_resolve_effective_components_self_inheritance_is_rejected() -> None:
    template_id = uuid4()
    version = _version(
        template_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=template_id, version=1),
        components=(_component("interfaces"),),
    )

    with pytest.raises(ObjectTemplateSelfInheritance):
        ObjectTemplateInheritanceResolver().resolve_effective_components(
            version,
            parent_lookup=lambda _: pytest.fail("parent_lookup should not be called"),
        )


def test_resolve_effective_components_cycle_detection_still_works() -> None:
    first_id = uuid4()
    second_id = uuid4()
    first = _version(
        first_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=second_id, version=1),
        components=(_component("interfaces"),),
    )
    second = _version(
        second_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=first_id, version=1),
        components=(_component("routing_engines"),),
    )
    versions = {
        (first_id, 1): first,
        (second_id, 1): second,
    }

    with pytest.raises(ObjectTemplateInheritanceCycle):
        ObjectTemplateInheritanceResolver().resolve_effective_components(
            first,
            parent_lookup=lambda ref: versions.get((ref.template_id, ref.version)),
        )
