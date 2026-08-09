from dataclasses import replace
from uuid import UUID, uuid4

import pytest

from netauto.core.object import (
    ComponentMembership,
    ComponentMembershipAlreadyExists,
    ComponentMembershipNotFound,
    Object,
    ObjectAlreadyExists,
    ObjectNotFound,
)
from netauto.persistence.memory.object_repository import InMemoryObjectRepository


def _object(
    *,
    object_id: UUID | None = None,
    template_id: UUID | None = None,
    template_version: int = 1,
    properties: dict[str, object] | None = None,
) -> Object:
    return Object(
        id=object_id or uuid4(),
        template_id=template_id or uuid4(),
        template_version=template_version,
        properties=properties or {},
    )


def _membership(
    *,
    parent_object_id: UUID,
    child_object_id: UUID,
    slot_name: str = "interfaces",
) -> ComponentMembership:
    return ComponentMembership(
        parent_object_id=parent_object_id,
        slot_name=slot_name,
        child_object_id=child_object_id,
    )


def test_list_empty_repository() -> None:
    repo = InMemoryObjectRepository()

    assert repo.list() == ()


def test_add_and_get_round_trip() -> None:
    repo = InMemoryObjectRepository()
    object_value = _object(properties={"hostname": "router-01"})

    repo.add(object_value)

    assert repo.get(object_value.id) == object_value


def test_list_is_deterministic_by_uuid_string() -> None:
    repo = InMemoryObjectRepository()
    low = _object(object_id=UUID("00000000-0000-0000-0000-000000000001"))
    high = _object(object_id=UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"))
    mid = _object(object_id=UUID("11111111-1111-1111-1111-111111111111"))

    repo.add(high)
    repo.add(mid)
    repo.add(low)

    assert tuple(object_value.id for object_value in repo.list()) == (low.id, mid.id, high.id)


def test_duplicate_uuid_rejected() -> None:
    repo = InMemoryObjectRepository()
    first = _object(object_id=uuid4())
    duplicate = _object(object_id=first.id)

    repo.add(first)

    with pytest.raises(ObjectAlreadyExists):
        repo.add(duplicate)


def test_get_missing_returns_none() -> None:
    repo = InMemoryObjectRepository()

    assert repo.get(uuid4()) is None


def test_replace_existing_snapshot() -> None:
    repo = InMemoryObjectRepository()
    original = _object(properties={"hostname": "router-01"})
    updated = replace(original, properties={"hostname": "router-02", "serial": "ABC123"})

    repo.add(original)
    repo.replace(updated)

    assert repo.get(original.id) == updated


def test_replace_preserves_uuid_but_replaces_properties() -> None:
    repo = InMemoryObjectRepository()
    original = _object(properties={"hostname": "router-01"})
    updated = replace(original, properties={"serial": "ABC123"})

    repo.add(original)
    repo.replace(updated)

    loaded = repo.get(original.id)
    assert loaded is not None
    assert loaded.id == original.id
    assert loaded.properties == {"serial": "ABC123"}


def test_replace_missing_raises_object_not_found() -> None:
    repo = InMemoryObjectRepository()

    with pytest.raises(ObjectNotFound):
        repo.replace(_object())


def test_delete_existing_object() -> None:
    repo = InMemoryObjectRepository()
    object_value = _object()
    repo.add(object_value)

    repo.delete(object_value.id)

    assert repo.get(object_value.id) is None
    assert repo.list() == ()


def test_delete_missing_raises_object_not_found() -> None:
    repo = InMemoryObjectRepository()

    with pytest.raises(ObjectNotFound):
        repo.delete(uuid4())


def test_add_membership_and_get_owner_round_trip() -> None:
    repo = InMemoryObjectRepository()
    parent = _object()
    child = _object()
    membership = _membership(parent_object_id=parent.id, child_object_id=child.id)

    repo.add(parent)
    repo.add(child)
    repo.add_membership(membership)

    assert repo.get_owner(child.id) == membership


def test_add_membership_requires_existing_parent_and_child_objects() -> None:
    repo = InMemoryObjectRepository()
    parent = _object()
    child = _object()

    with pytest.raises(ObjectNotFound):
        repo.add_membership(_membership(parent_object_id=parent.id, child_object_id=child.id))

    repo.add(parent)
    with pytest.raises(ObjectNotFound):
        repo.add_membership(_membership(parent_object_id=parent.id, child_object_id=child.id))


def test_same_child_cannot_receive_two_memberships() -> None:
    repo = InMemoryObjectRepository()
    parent_one = _object()
    parent_two = _object()
    child = _object()

    for object_value in (parent_one, parent_two, child):
        repo.add(object_value)

    repo.add_membership(_membership(parent_object_id=parent_one.id, child_object_id=child.id))

    with pytest.raises(ComponentMembershipAlreadyExists):
        repo.add_membership(_membership(parent_object_id=parent_two.id, child_object_id=child.id))


def test_duplicate_identical_membership_is_still_rejected() -> None:
    repo = InMemoryObjectRepository()
    parent = _object()
    child = _object()
    membership = _membership(parent_object_id=parent.id, child_object_id=child.id)

    repo.add(parent)
    repo.add(child)
    repo.add_membership(membership)

    with pytest.raises(ComponentMembershipAlreadyExists):
        repo.add_membership(membership)


def test_different_children_can_belong_to_same_parent_and_slot() -> None:
    repo = InMemoryObjectRepository()
    parent = _object()
    child_one = _object()
    child_two = _object()
    for object_value in (parent, child_one, child_two):
        repo.add(object_value)

    repo.add_membership(_membership(parent_object_id=parent.id, child_object_id=child_one.id))
    repo.add_membership(_membership(parent_object_id=parent.id, child_object_id=child_two.id))

    assert tuple(membership.child_object_id for membership in repo.list_components(parent.id)) == (
        min(child_one.id, child_two.id, key=str),
        max(child_one.id, child_two.id, key=str),
    )


def test_different_slots_on_same_parent_work() -> None:
    repo = InMemoryObjectRepository()
    parent = _object()
    interface_child = _object()
    module_child = _object()
    for object_value in (parent, interface_child, module_child):
        repo.add(object_value)

    repo.add_membership(
        _membership(
            parent_object_id=parent.id,
            child_object_id=interface_child.id,
            slot_name="interfaces",
        )
    )
    repo.add_membership(
        _membership(
            parent_object_id=parent.id,
            child_object_id=module_child.id,
            slot_name="modules",
        )
    )

    assert tuple(membership.slot_name for membership in repo.list_components(parent.id)) == (
        "interfaces",
        "modules",
    )


def test_list_components_returns_all_direct_memberships() -> None:
    repo = InMemoryObjectRepository()
    parent = _object()
    child_one = _object()
    child_two = _object()
    outsider = _object()
    outsider_child = _object()
    for object_value in (parent, child_one, child_two, outsider, outsider_child):
        repo.add(object_value)

    first = _membership(parent_object_id=parent.id, child_object_id=child_one.id, slot_name="b")
    second = _membership(parent_object_id=parent.id, child_object_id=child_two.id, slot_name="a")
    outsider_membership = _membership(
        parent_object_id=outsider.id,
        child_object_id=outsider_child.id,
        slot_name="a",
    )
    repo.add_membership(first)
    repo.add_membership(second)
    repo.add_membership(outsider_membership)

    assert repo.list_components(parent.id) == (second, first)


def test_slot_filter_works() -> None:
    repo = InMemoryObjectRepository()
    parent = _object()
    child_one = _object()
    child_two = _object()
    for object_value in (parent, child_one, child_two):
        repo.add(object_value)

    first = _membership(
        parent_object_id=parent.id,
        child_object_id=child_one.id,
        slot_name="interfaces",
    )
    second = _membership(
        parent_object_id=parent.id,
        child_object_id=child_two.id,
        slot_name="modules",
    )
    repo.add_membership(first)
    repo.add_membership(second)

    assert repo.list_components(parent.id, slot_name="interfaces") == (first,)
    assert repo.list_components(parent.id, slot_name="fans") == ()


def test_list_components_ordering_is_slot_then_child_uuid_string() -> None:
    repo = InMemoryObjectRepository()
    parent = _object()
    child_a = _object(object_id=UUID("00000000-0000-0000-0000-000000000010"))
    child_b = _object(object_id=UUID("00000000-0000-0000-0000-000000000020"))
    child_c = _object(object_id=UUID("00000000-0000-0000-0000-000000000005"))
    for object_value in (parent, child_a, child_b, child_c):
        repo.add(object_value)

    membership_a = _membership(
        parent_object_id=parent.id,
        child_object_id=child_a.id,
        slot_name="modules",
    )
    membership_b = _membership(
        parent_object_id=parent.id,
        child_object_id=child_b.id,
        slot_name="interfaces",
    )
    membership_c = _membership(
        parent_object_id=parent.id,
        child_object_id=child_c.id,
        slot_name="interfaces",
    )
    repo.add_membership(membership_a)
    repo.add_membership(membership_b)
    repo.add_membership(membership_c)

    assert repo.list_components(parent.id) == (membership_c, membership_b, membership_a)


def test_get_owner_for_unowned_child_returns_none() -> None:
    repo = InMemoryObjectRepository()

    assert repo.get_owner(uuid4()) is None


def test_remove_membership_makes_child_unowned() -> None:
    repo = InMemoryObjectRepository()
    parent = _object()
    child = _object()
    for object_value in (parent, child):
        repo.add(object_value)
    repo.add_membership(_membership(parent_object_id=parent.id, child_object_id=child.id))

    repo.remove_membership(child.id)

    assert repo.get_owner(child.id) is None


def test_remove_missing_membership_raises_component_membership_not_found() -> None:
    repo = InMemoryObjectRepository()

    with pytest.raises(ComponentMembershipNotFound):
        repo.remove_membership(uuid4())


def test_removing_membership_does_not_delete_parent_or_child() -> None:
    repo = InMemoryObjectRepository()
    parent = _object()
    child = _object()
    for object_value in (parent, child):
        repo.add(object_value)
    repo.add_membership(_membership(parent_object_id=parent.id, child_object_id=child.id))

    repo.remove_membership(child.id)

    assert repo.get(parent.id) == parent
    assert repo.get(child.id) == child


def test_removing_owner_membership_preserves_child_subtree_memberships() -> None:
    repo = InMemoryObjectRepository()
    parent = _object()
    child = _object()
    grandchild = _object()
    for object_value in (parent, child, grandchild):
        repo.add(object_value)
    parent_to_child = _membership(parent_object_id=parent.id, child_object_id=child.id)
    child_to_grandchild = _membership(
        parent_object_id=child.id,
        child_object_id=grandchild.id,
        slot_name="subinterfaces",
    )
    repo.add_membership(parent_to_child)
    repo.add_membership(child_to_grandchild)

    repo.remove_membership(child.id)

    assert repo.get_owner(child.id) is None
    assert repo.get_owner(grandchild.id) == child_to_grandchild
    assert repo.list_components(child.id) == (child_to_grandchild,)


def test_adding_membership_does_not_alter_stored_child_object() -> None:
    repo = InMemoryObjectRepository()
    parent = _object()
    child = _object(properties={"hostname": "router-01"})
    repo.add(parent)
    repo.add(child)
    before = repo.get(child.id)

    repo.add_membership(_membership(parent_object_id=parent.id, child_object_id=child.id))
    after = repo.get(child.id)

    assert after == before
    assert not hasattr(after, "owner_id")  # type: ignore[arg-type]


def test_removing_membership_does_not_alter_stored_child_object() -> None:
    repo = InMemoryObjectRepository()
    parent = _object()
    child = _object(properties={"hostname": "router-01"})
    repo.add(parent)
    repo.add(child)
    repo.add_membership(_membership(parent_object_id=parent.id, child_object_id=child.id))
    before = repo.get(child.id)

    repo.remove_membership(child.id)
    after = repo.get(child.id)

    assert after == before
    assert not hasattr(after, "parent_id")  # type: ignore[arg-type]
    assert not hasattr(after, "components")  # type: ignore[arg-type]


def test_delete_child_removes_its_owner_membership() -> None:
    repo = InMemoryObjectRepository()
    parent = _object()
    child = _object()
    repo.add(parent)
    repo.add(child)
    repo.add_membership(_membership(parent_object_id=parent.id, child_object_id=child.id))

    repo.delete(child.id)

    assert repo.get_owner(child.id) is None
    assert repo.list_components(parent.id) == ()


def test_delete_parent_removes_outgoing_memberships_but_not_child_objects() -> None:
    repo = InMemoryObjectRepository()
    parent = _object()
    child = _object()
    repo.add(parent)
    repo.add(child)
    repo.add_membership(_membership(parent_object_id=parent.id, child_object_id=child.id))

    repo.delete(parent.id)

    assert repo.get(parent.id) is None
    assert repo.get(child.id) == child
    assert repo.get_owner(child.id) is None


def test_delete_object_that_is_both_child_and_parent_cleans_incident_memberships_only() -> None:
    repo = InMemoryObjectRepository()
    root = _object()
    middle = _object()
    leaf = _object()
    unrelated = _object()
    for object_value in (root, middle, leaf, unrelated):
        repo.add(object_value)
    root_to_middle = _membership(
        parent_object_id=root.id,
        child_object_id=middle.id,
        slot_name="modules",
    )
    middle_to_leaf = _membership(
        parent_object_id=middle.id,
        child_object_id=leaf.id,
        slot_name="interfaces",
    )
    repo.add_membership(root_to_middle)
    repo.add_membership(middle_to_leaf)

    repo.delete(middle.id)

    assert repo.get(root.id) == root
    assert repo.get(leaf.id) == leaf
    assert repo.get(unrelated.id) == unrelated
    assert repo.get_owner(middle.id) is None
    assert repo.get_owner(leaf.id) is None
    assert repo.list_components(root.id) == ()
