from uuid import UUID, uuid4

import pytest

from netauto.core.objecttemplate import (
    InheritedObjectTemplatePropertyConflict,
    ObjectTemplateInheritanceCycle,
    ObjectTemplateInheritanceResolver,
    ObjectTemplateParentNotFound,
    ObjectTemplateProperty,
    ObjectTemplateVersion,
    ObjectTemplateVersionRef,
    ObjectTemplateVersionStatus,
)


def _property(name: str) -> ObjectTemplateProperty:
    return ObjectTemplateProperty(name=name, datatype_id=uuid4(), datatype_version=1)


def _version(
    template_id: UUID,
    version: int,
    *,
    parent: ObjectTemplateVersionRef | None = None,
    properties: tuple[ObjectTemplateProperty, ...] = (),
) -> ObjectTemplateVersion:
    return ObjectTemplateVersion(
        template_id=template_id,
        version=version,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=parent,
        properties=properties,
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


def test_direct_self_cycle_is_rejected() -> None:
    template_id = uuid4()
    version = _version(
        template_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=template_id, version=1),
    )
    versions = {(template_id, 1): version}

    with pytest.raises(ObjectTemplateInheritanceCycle):
        ObjectTemplateInheritanceResolver().resolve_effective_properties(
            version,
            parent_lookup=lambda ref: versions.get((ref.template_id, ref.version)),
        )


def test_indirect_cycle_is_rejected() -> None:
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
