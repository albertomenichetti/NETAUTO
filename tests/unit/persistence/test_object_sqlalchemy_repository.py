from dataclasses import replace
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from netauto.core.object import (
    ComponentMembership,
    ComponentMembershipAlreadyExists,
    ComponentMembershipNotFound,
    Object,
    ObjectAlreadyExists,
    ObjectNotFound,
    ObjectPersistenceError,
)
from netauto.persistence.sqlalchemy.database import create_schema, create_sqlite_engine
from netauto.persistence.sqlalchemy.models import ObjectComponentRow, ObjectRow
from netauto.persistence.sqlalchemy.object_repository import SqlAlchemyObjectRepository


def _repo(
    tmp_path: Path,
    filename: str,
) -> tuple[SqlAlchemyObjectRepository, Session, Engine]:
    engine = create_sqlite_engine(f"sqlite:///{tmp_path / filename}")
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    session = session_factory()
    return SqlAlchemyObjectRepository(session), session, engine


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


def test_schema_encodes_object_and_membership_invariants(tmp_path: Path) -> None:
    _repo_obj, session, engine = _repo(tmp_path, "schema.sqlite3")
    session.close()
    try:
        inspector = inspect(engine)

        object_pk = inspector.get_pk_constraint("objects")
        component_pk = inspector.get_pk_constraint("object_components")
        object_fks = inspector.get_foreign_keys("objects")
        component_fks = inspector.get_foreign_keys("object_components")
        component_columns = {
            column["name"] for column in inspector.get_columns("object_components")
        }

        assert object_pk["constrained_columns"] == ["id"]
        assert component_pk["constrained_columns"] == ["child_object_id"]
        assert object_fks == []
        assert component_columns == {"parent_object_id", "slot_name", "child_object_id"}
        assert len(component_fks) == 2

        parent_fk = next(
            fk for fk in component_fks if fk["constrained_columns"] == ["parent_object_id"]
        )
        child_fk = next(
            fk for fk in component_fks if fk["constrained_columns"] == ["child_object_id"]
        )
        assert parent_fk["referred_table"] == "objects"
        assert parent_fk["referred_columns"] == ["id"]
        assert child_fk["referred_table"] == "objects"
        assert child_fk["referred_columns"] == ["id"]
        assert parent_fk.get("options", {}).get("ondelete") == "CASCADE"
        assert child_fk.get("options", {}).get("ondelete") == "CASCADE"
    finally:
        engine.dispose()


def test_empty_list(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "empty.sqlite3")
    try:
        assert repo.list() == ()
    finally:
        session.close()
        engine.dispose()


def test_add_get_round_trip_with_exact_pin_and_empty_properties(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "round_trip.sqlite3")
    object_value = _object()
    try:
        repo.add(object_value)
        assert repo.get(object_value.id) == object_value
    finally:
        session.close()
        engine.dispose()


def test_representative_primitive_property_values_round_trip(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "primitive_properties.sqlite3")
    object_value = _object(
        properties={
            "hostname": "router-01",
            "vlan": 100,
            "metric": 1.5,
            "enabled": True,
            "note": None,
        }
    )
    try:
        repo.add(object_value)
        assert repo.get(object_value.id) == object_value
    finally:
        session.close()
        engine.dispose()


def test_list_is_deterministic_by_uuid_string(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "ordering.sqlite3")
    low = _object(object_id=UUID("00000000-0000-0000-0000-000000000001"))
    high = _object(object_id=UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"))
    mid = _object(object_id=UUID("11111111-1111-1111-1111-111111111111"))
    try:
        repo.add(high)
        repo.add(mid)
        repo.add(low)
        assert tuple(object_value.id for object_value in repo.list()) == (low.id, mid.id, high.id)
    finally:
        session.close()
        engine.dispose()


def test_duplicate_uuid_rejected(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "dup_uuid.sqlite3")
    object_value = _object(object_id=uuid4())
    duplicate = _object(object_id=object_value.id)
    try:
        repo.add(object_value)
        with pytest.raises(ObjectAlreadyExists):
            repo.add(duplicate)
    finally:
        session.close()
        engine.dispose()


def test_get_missing_returns_none(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "missing_get.sqlite3")
    try:
        assert repo.get(uuid4()) is None
    finally:
        session.close()
        engine.dispose()


def test_replace_complete_snapshot(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "replace.sqlite3")
    original = _object(properties={"hostname": "router-01"})
    updated = replace(
        original,
        template_id=uuid4(),
        template_version=3,
        properties={"serial": "ABC123"},
    )
    try:
        repo.add(original)
        repo.replace(updated)
        assert repo.get(original.id) == updated
    finally:
        session.close()
        engine.dispose()


def test_replace_serialization_failure_does_not_partially_mutate_persisted_row(
    tmp_path: Path,
) -> None:
    repo, session, engine = _repo(tmp_path, "replace_atomicity.sqlite3")
    original = _object(properties={"hostname": "router-01"})
    replacement = replace(
        original,
        template_id=uuid4(),
        template_version=2,
        properties={"bad": object()},
    )
    try:
        repo.add(original)
        session.commit()

        with pytest.raises(ObjectPersistenceError):
            repo.replace(replacement)

        session.commit()

        fresh_session = sessionmaker(engine, expire_on_commit=False)()
        try:
            fresh_repo = SqlAlchemyObjectRepository(fresh_session)
            loaded = fresh_repo.get(original.id)
            assert loaded == original
            assert loaded is not None
            assert loaded.template_id == original.template_id
            assert loaded.template_version == original.template_version
            assert loaded.properties == original.properties
        finally:
            fresh_session.close()
    finally:
        session.close()
        engine.dispose()


def test_replace_missing_raises_object_not_found(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "replace_missing.sqlite3")
    try:
        with pytest.raises(ObjectNotFound):
            repo.replace(_object())
    finally:
        session.close()
        engine.dispose()


def test_delete_existing_and_delete_missing(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "delete.sqlite3")
    object_value = _object()
    try:
        repo.add(object_value)
        repo.delete(object_value.id)
        assert repo.get(object_value.id) is None
        with pytest.raises(ObjectNotFound):
            repo.delete(object_value.id)
    finally:
        session.close()
        engine.dispose()


def test_persisted_properties_json_is_deterministic(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "deterministic_json.sqlite3")
    object_value = _object(properties={"z": 1, "a": 2})
    try:
        repo.add(object_value)
        row = session.get(ObjectRow, str(object_value.id))
        assert row is not None
        assert row.properties_json == '{"a":2,"z":1}'
    finally:
        session.close()
        engine.dispose()


@pytest.mark.parametrize("value", [{"bad": object()}, {"bad": float("nan")}, {"bad": float("inf")}])
def test_non_json_serializable_or_non_finite_runtime_value_raises_object_persistence_error(
    tmp_path: Path,
    value: dict[str, object],
) -> None:
    repo, session, engine = _repo(tmp_path, "bad_json.sqlite3")
    try:
        with pytest.raises(ObjectPersistenceError):
            repo.add(_object(properties=value))
    finally:
        session.close()
        engine.dispose()


def test_malformed_stored_object_uuid_raises_object_persistence_error(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "bad_object_uuid.sqlite3")
    session.add(
        ObjectRow(
            id="not-a-uuid",
            template_id=str(uuid4()),
            template_version=1,
            properties_json="{}",
        )
    )
    session.commit()
    try:
        with pytest.raises(ObjectPersistenceError):
            repo.list()
    finally:
        session.close()
        engine.dispose()


def test_malformed_stored_template_uuid_raises_object_persistence_error(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "bad_template_uuid.sqlite3")
    object_id = uuid4()
    session.add(
        ObjectRow(
            id=str(object_id),
            template_id="not-a-uuid",
            template_version=1,
            properties_json="{}",
        )
    )
    session.commit()
    try:
        with pytest.raises(ObjectPersistenceError):
            repo.get(object_id)
    finally:
        session.close()
        engine.dispose()


def test_malformed_properties_json_raises_object_persistence_error(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "bad_properties_json.sqlite3")
    object_id = uuid4()
    session.add(
        ObjectRow(
            id=str(object_id),
            template_id=str(uuid4()),
            template_version=1,
            properties_json="{bad json",
        )
    )
    session.commit()
    try:
        with pytest.raises(ObjectPersistenceError):
            repo.get(object_id)
    finally:
        session.close()
        engine.dispose()


def test_top_level_properties_json_that_is_not_object_raises_object_persistence_error(
    tmp_path: Path,
) -> None:
    repo, session, engine = _repo(tmp_path, "bad_top_level_json.sqlite3")
    object_id = uuid4()
    session.add(
        ObjectRow(
            id=str(object_id),
            template_id=str(uuid4()),
            template_version=1,
            properties_json="[]",
        )
    )
    session.commit()
    try:
        with pytest.raises(ObjectPersistenceError):
            repo.get(object_id)
    finally:
        session.close()
        engine.dispose()


def test_invalid_stored_template_version_raises_object_persistence_error(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "bad_template_version.sqlite3")
    object_id = uuid4()
    session.add(
        ObjectRow(
            id=str(object_id),
            template_id=str(uuid4()),
            template_version=0,
            properties_json="{}",
        )
    )
    session.commit()
    try:
        with pytest.raises(ObjectPersistenceError):
            repo.get(object_id)
    finally:
        session.close()
        engine.dispose()


def test_add_membership_and_get_owner_round_trip(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "membership_round_trip.sqlite3")
    parent = _object()
    child = _object()
    membership = _membership(parent_object_id=parent.id, child_object_id=child.id)
    try:
        repo.add(parent)
        repo.add(child)
        repo.add_membership(membership)
        assert repo.get_owner(child.id) == membership
    finally:
        session.close()
        engine.dispose()


def test_add_membership_parent_missing_or_child_missing_raises_object_not_found(
    tmp_path: Path,
) -> None:
    repo, session, engine = _repo(tmp_path, "membership_missing_object.sqlite3")
    parent = _object()
    child = _object()
    try:
        with pytest.raises(ObjectNotFound):
            repo.add_membership(_membership(parent_object_id=parent.id, child_object_id=child.id))
        repo.add(parent)
        with pytest.raises(ObjectNotFound):
            repo.add_membership(_membership(parent_object_id=parent.id, child_object_id=child.id))
    finally:
        session.close()
        engine.dispose()


def test_identical_duplicate_membership_is_rejected(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "duplicate_membership_identical.sqlite3")
    parent_one = _object()
    child = _object()
    identical = _membership(parent_object_id=parent_one.id, child_object_id=child.id)
    try:
        for object_value in (parent_one, child):
            repo.add(object_value)
        repo.add_membership(identical)

        with pytest.raises(ComponentMembershipAlreadyExists):
            repo.add_membership(identical)
    finally:
        session.close()
        engine.dispose()


def test_same_child_cannot_have_two_different_owners(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "duplicate_membership_different_owner.sqlite3")
    parent_one = _object()
    parent_two = _object()
    child = _object()
    try:
        for object_value in (parent_one, parent_two, child):
            repo.add(object_value)
        repo.add_membership(_membership(parent_object_id=parent_one.id, child_object_id=child.id))

        with pytest.raises(ComponentMembershipAlreadyExists):
            repo.add_membership(
                _membership(parent_object_id=parent_two.id, child_object_id=child.id)
            )
    finally:
        session.close()
        engine.dispose()


def test_database_physically_enforces_unique_child_ownership(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "unique_child.sqlite3")
    parent_one = _object()
    parent_two = _object()
    child = _object()
    try:
        for object_value in (parent_one, parent_two, child):
            repo.add(object_value)
        session.add(
            ObjectComponentRow(
                parent_object_id=str(parent_one.id),
                slot_name="interfaces",
                child_object_id=str(child.id),
            )
        )
        session.flush()
        session.add(
            ObjectComponentRow(
                parent_object_id=str(parent_two.id),
                slot_name="modules",
                child_object_id=str(child.id),
            )
        )
        with pytest.raises(IntegrityError):
            session.flush()
    finally:
        session.rollback()
        session.close()
        engine.dispose()


def test_multiple_children_same_parent_slot_and_multiple_slots_work(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "multiple_memberships.sqlite3")
    parent = _object()
    child_one = _object()
    child_two = _object()
    module_child = _object()
    try:
        for object_value in (parent, child_one, child_two, module_child):
            repo.add(object_value)
        membership_one = _membership(parent_object_id=parent.id, child_object_id=child_one.id)
        membership_two = _membership(parent_object_id=parent.id, child_object_id=child_two.id)
        module_membership = _membership(
            parent_object_id=parent.id,
            child_object_id=module_child.id,
            slot_name="modules",
        )
        repo.add_membership(membership_one)
        repo.add_membership(membership_two)
        repo.add_membership(module_membership)
        assert repo.list_components(parent.id) == (
            membership_one,
            membership_two,
            module_membership,
        ) or repo.list_components(parent.id) == (
            membership_two,
            membership_one,
            module_membership,
        )
    finally:
        session.close()
        engine.dispose()


def test_list_components_direct_only_slot_filter_and_ordering(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "list_components.sqlite3")
    parent = _object()
    child_a = _object(object_id=UUID("00000000-0000-0000-0000-000000000010"))
    child_b = _object(object_id=UUID("00000000-0000-0000-0000-000000000020"))
    child_c = _object(object_id=UUID("00000000-0000-0000-0000-000000000005"))
    grandchild = _object()
    try:
        for object_value in (parent, child_a, child_b, child_c, grandchild):
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
        grandchild_membership = _membership(
            parent_object_id=child_a.id,
            child_object_id=grandchild.id,
            slot_name="subinterfaces",
        )
        repo.add_membership(membership_a)
        repo.add_membership(membership_b)
        repo.add_membership(membership_c)
        repo.add_membership(grandchild_membership)

        assert repo.list_components(parent.id) == (membership_c, membership_b, membership_a)
        assert repo.list_components(parent.id, slot_name="interfaces") == (
            membership_c,
            membership_b,
        )
        assert repo.list_components(uuid4()) == ()
    finally:
        session.close()
        engine.dispose()


def test_unowned_returns_none_remove_membership_detaches_and_preserves_objects_and_subtree(
    tmp_path: Path,
) -> None:
    repo, session, engine = _repo(tmp_path, "detach.sqlite3")
    parent = _object()
    child = _object(properties={"hostname": "router-01"})
    grandchild = _object()
    try:
        for object_value in (parent, child, grandchild):
            repo.add(object_value)
        parent_membership = _membership(parent_object_id=parent.id, child_object_id=child.id)
        child_membership = _membership(
            parent_object_id=child.id,
            child_object_id=grandchild.id,
            slot_name="subinterfaces",
        )
        repo.add_membership(parent_membership)
        repo.add_membership(child_membership)
        before = repo.get(child.id)

        repo.remove_membership(child.id)

        assert repo.get_owner(uuid4()) is None
        assert repo.get_owner(child.id) is None
        assert repo.get_owner(grandchild.id) == child_membership
        assert repo.list_components(child.id) == (child_membership,)
        assert repo.get(parent.id) == parent
        assert repo.get(child.id) == before
    finally:
        session.close()
        engine.dispose()


def test_remove_missing_membership_raises_component_membership_not_found(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "remove_missing_membership.sqlite3")
    try:
        with pytest.raises(ComponentMembershipNotFound):
            repo.remove_membership(uuid4())
    finally:
        session.close()
        engine.dispose()


def test_deleting_child_removes_incoming_membership_only(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "delete_child.sqlite3")
    parent = _object()
    child = _object()
    try:
        repo.add(parent)
        repo.add(child)
        repo.add_membership(_membership(parent_object_id=parent.id, child_object_id=child.id))
        repo.delete(child.id)

        assert repo.get(parent.id) == parent
        assert repo.get(child.id) is None
        assert repo.list_components(parent.id) == ()
    finally:
        session.close()
        engine.dispose()


def test_deleting_parent_removes_outgoing_memberships_but_not_child_objects(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "delete_parent.sqlite3")
    parent = _object()
    child = _object()
    try:
        repo.add(parent)
        repo.add(child)
        repo.add_membership(_membership(parent_object_id=parent.id, child_object_id=child.id))
        repo.delete(parent.id)

        assert repo.get(parent.id) is None
        assert repo.get(child.id) == child
        assert repo.get_owner(child.id) is None
    finally:
        session.close()
        engine.dispose()


def test_deleting_middle_node_in_chain_removes_both_incident_edges_but_leaves_objects(
    tmp_path: Path,
) -> None:
    repo, session, engine = _repo(tmp_path, "delete_middle.sqlite3")
    root = _object()
    middle = _object()
    leaf = _object()
    try:
        for object_value in (root, middle, leaf):
            repo.add(object_value)
        repo.add_membership(_membership(parent_object_id=root.id, child_object_id=middle.id))
        leaf_membership = _membership(
            parent_object_id=middle.id,
            child_object_id=leaf.id,
        )
        repo.add_membership(leaf_membership)

        repo.delete(middle.id)

        assert repo.get(root.id) == root
        assert repo.get(middle.id) is None
        assert repo.get(leaf.id) == leaf
        assert repo.list_components(root.id) == ()
        assert repo.get_owner(leaf.id) is None
    finally:
        session.close()
        engine.dispose()
