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
    return ObjectTemplateComponent(name=name, template_id=uuid4())


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


def test_is_same_or_descendant_returns_true_for_exact_same_version() -> None:
    template_id = uuid4()
    candidate = _version(template_id, 1)

    result = ObjectTemplateInheritanceResolver().is_same_or_descendant(
        candidate,
        required=ObjectTemplateVersionRef(template_id=template_id, version=1),
        parent_lookup=lambda _: pytest.fail("parent_lookup should not be called"),
    )

    assert result is True


def test_is_same_or_descendant_returns_true_for_direct_descendant() -> None:
    parent_id = uuid4()
    parent = _version(parent_id, 1)
    child = _version(
        uuid4(),
        3,
        parent=ObjectTemplateVersionRef(template_id=parent_id, version=1),
    )
    lookups: list[tuple[UUID, int]] = []
    versions = {(parent_id, 1): parent}

    result = ObjectTemplateInheritanceResolver().is_same_or_descendant(
        child,
        required=ObjectTemplateVersionRef(template_id=parent_id, version=1),
        parent_lookup=lambda ref: lookups.append((ref.template_id, ref.version))
        or versions.get((ref.template_id, ref.version)),
    )

    assert result is True
    assert lookups == [(parent_id, 1)]


def test_is_same_or_descendant_returns_true_for_multi_level_descendant() -> None:
    base_id = uuid4()
    parent_id = uuid4()
    base = _version(base_id, 1)
    parent = _version(
        parent_id,
        2,
        parent=ObjectTemplateVersionRef(template_id=base_id, version=1),
    )
    child = _version(
        uuid4(),
        3,
        parent=ObjectTemplateVersionRef(template_id=parent_id, version=2),
    )
    versions = {
        (base_id, 1): base,
        (parent_id, 2): parent,
    }

    result = ObjectTemplateInheritanceResolver().is_same_or_descendant(
        child,
        required=ObjectTemplateVersionRef(template_id=base_id, version=1),
        parent_lookup=lambda ref: versions.get((ref.template_id, ref.version)),
    )

    assert result is True


def test_is_same_or_descendant_returns_false_for_unrelated_candidate() -> None:
    candidate = _version(uuid4(), 1)
    required = ObjectTemplateVersionRef(template_id=uuid4(), version=1)

    result = ObjectTemplateInheritanceResolver().is_same_or_descendant(
        candidate,
        required=required,
        parent_lookup=lambda _: None,
    )

    assert result is False


def test_is_same_or_descendant_returns_false_for_same_template_id_different_version() -> None:
    template_id = uuid4()
    candidate = _version(template_id, 2)

    result = ObjectTemplateInheritanceResolver().is_same_or_descendant(
        candidate,
        required=ObjectTemplateVersionRef(template_id=template_id, version=1),
        parent_lookup=lambda _: pytest.fail("parent_lookup should not be called"),
    )

    assert result is False


def test_descendant_of_version_two_is_not_compatible_with_requirement_pinned_to_version_one(
) -> None:
    template_v2_id = uuid4()
    candidate = _version(
        uuid4(),
        1,
        parent=ObjectTemplateVersionRef(template_id=template_v2_id, version=2),
    )
    parent_v2 = _version(template_v2_id, 2)

    result = ObjectTemplateInheritanceResolver().is_same_or_descendant(
        candidate,
        required=ObjectTemplateVersionRef(template_id=template_v2_id, version=1),
        parent_lookup=lambda ref: (
            parent_v2
            if (ref.template_id, ref.version) == (template_v2_id, 2)
            else None
        ),
    )

    assert result is False


def test_is_same_or_descendant_uses_exact_parent_refs_not_template_names() -> None:
    required_id = uuid4()
    parent = _version(required_id, 7)
    child = _version(
        uuid4(),
        1,
        parent=ObjectTemplateVersionRef(template_id=required_id, version=7),
    )

    result = ObjectTemplateInheritanceResolver().is_same_or_descendant(
        child,
        required=ObjectTemplateVersionRef(template_id=required_id, version=7),
        parent_lookup=lambda ref: (
            parent if (ref.template_id, ref.version) == (required_id, 7) else None
        ),
    )

    assert result is True


def test_is_same_or_descendant_missing_parent_raises_object_template_parent_not_found() -> None:
    candidate = _version(
        uuid4(),
        1,
        parent=ObjectTemplateVersionRef(template_id=uuid4(), version=1),
    )

    with pytest.raises(ObjectTemplateParentNotFound):
        ObjectTemplateInheritanceResolver().is_same_or_descendant(
            candidate,
            required=ObjectTemplateVersionRef(template_id=uuid4(), version=1),
            parent_lookup=lambda _: None,
        )


def test_is_same_or_descendant_preserves_self_inheritance_detection() -> None:
    template_id = uuid4()
    candidate = _version(
        template_id,
        2,
        parent=ObjectTemplateVersionRef(template_id=template_id, version=1),
    )

    with pytest.raises(ObjectTemplateSelfInheritance):
        ObjectTemplateInheritanceResolver().is_same_or_descendant(
            candidate,
            required=ObjectTemplateVersionRef(template_id=uuid4(), version=1),
            parent_lookup=lambda _: pytest.fail("parent_lookup should not be called"),
        )


def test_is_same_or_descendant_preserves_cycle_detection() -> None:
    first_id = uuid4()
    second_id = uuid4()
    first = _version(
        first_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=second_id, version=1),
    )
    second = _version(
        second_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=first_id, version=1),
    )
    versions = {
        (first_id, 1): first,
        (second_id, 1): second,
    }

    with pytest.raises(ObjectTemplateInheritanceCycle):
        ObjectTemplateInheritanceResolver().is_same_or_descendant(
            first,
            required=ObjectTemplateVersionRef(template_id=uuid4(), version=1),
            parent_lookup=lambda ref: versions.get((ref.template_id, ref.version)),
        )


def test_is_same_or_descendant_ignores_status() -> None:
    required_id = uuid4()
    required_version = ObjectTemplateVersion(
        template_id=required_id,
        version=1,
        status=ObjectTemplateVersionStatus.DEPRECATED,
    )
    candidate = _version(
        uuid4(),
        1,
        parent=ObjectTemplateVersionRef(template_id=required_id, version=1),
    )

    result = ObjectTemplateInheritanceResolver().is_same_or_descendant(
        candidate,
        required=ObjectTemplateVersionRef(template_id=required_id, version=1),
        parent_lookup=lambda ref: required_version
        if (ref.template_id, ref.version) == (required_id, 1)
        else None,
    )

    assert result is True


def test_is_same_or_descendant_has_no_latest_or_fallback_behavior() -> None:
    template_id = uuid4()
    candidate = _version(
        uuid4(),
        1,
        parent=ObjectTemplateVersionRef(template_id=template_id, version=2),
    )
    only_existing_parent = _version(template_id, 2)

    result = ObjectTemplateInheritanceResolver().is_same_or_descendant(
        candidate,
        required=ObjectTemplateVersionRef(template_id=template_id, version=1),
        parent_lookup=lambda ref: only_existing_parent
        if (ref.template_id, ref.version) == (template_id, 2)
        else None,
    )

    assert result is False


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
