from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import replace
from uuid import UUID, uuid4

import pytest
from sqlalchemy import event, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from netauto.core.object import (
    ComponentMembership,
    ComponentMembershipAlreadyExists,
    ComponentMembershipNotFound,
    InvalidObject,
    Object,
    ObjectAlreadyExists,
    ObjectConcurrentModification,
    ObjectNotFound,
    ObjectPersistenceError,
)
from netauto.core.objecttemplate import ObjectTemplateVersionStatus
from netauto.persistence.sqlalchemy.models import (
    ObjectComponentRow,
    ObjectRow,
    ObjectTemplateRow,
    ObjectTemplateVersionRow,
)
from netauto.persistence.sqlalchemy.object_repository import SqlAlchemyObjectRepository

pytestmark = pytest.mark.postgresql

DEFAULT_TEMPLATE_ID = UUID("00000000-0000-0000-0000-0000000000aa")


def _object(
    *,
    object_id: UUID | None = None,
    template_id: UUID | None = None,
    template_version: int = 1,
    properties: dict[str, object] | None = None,
) -> Object:
    return Object(
        id=object_id or uuid4(),
        template_id=template_id or DEFAULT_TEMPLATE_ID,
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


def _store_template_identity(
    session: Session,
    *,
    template_id: UUID,
    namespace: str | None = None,
    name: str | None = None,
) -> None:
    logical_suffix = template_id.hex[:8]
    session.add(
        ObjectTemplateRow(
            id=str(template_id),
            namespace=namespace or f"network_{logical_suffix}",
            name=name or f"template_{logical_suffix}",
            description=None,
            abstract=False,
        )
    )
    session.flush()


def _store_template_version(
    session: Session,
    *,
    template_id: UUID,
    version: int = 1,
    status: ObjectTemplateVersionStatus = ObjectTemplateVersionStatus.PUBLISHED,
) -> None:
    if session.get(ObjectTemplateRow, str(template_id)) is None:
        _store_template_identity(session, template_id=template_id)
    session.add(
        ObjectTemplateVersionRow(
            template_id=str(template_id),
            version=version,
            status=status.value,
            parent_template_id=None,
            parent_version=None,
        )
    )
    session.flush()


def _repo(
    session: Session,
) -> SqlAlchemyObjectRepository:
    _store_template_version(session, template_id=DEFAULT_TEMPLATE_ID)
    return SqlAlchemyObjectRepository(session)


def test_postgresql_object_list_add_get_round_trip_and_deterministic_json(
    postgresql_model_session: Session,
) -> None:
    repo = _repo(postgresql_model_session)
    low = _object(
        object_id=UUID("00000000-0000-0000-0000-000000000001"),
        properties={"z": 1, "a": 2},
    )
    high = _object(
        object_id=UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"),
        properties={
            "hostname": "router-01",
            "vlan": 100,
            "metric": 1.5,
            "enabled": True,
            "note": None,
            "tags": ["edge", 7],
            "nested": {"rack": "A1"},
        },
    )

    assert repo.list() == ()

    repo.add(high)
    repo.add(low)

    loaded = repo.get(high.id)
    listed = repo.list()
    stored = postgresql_model_session.get(ObjectRow, str(low.id))

    assert loaded == high
    assert loaded is not None
    assert isinstance(loaded.id, UUID)
    assert listed == (low, high)
    assert stored is not None
    assert stored.properties_json == '{"a":2,"z":1}'
    assert repo.get(uuid4()) is None


def test_postgresql_object_list_by_template_version_filters_exact_pin(
    postgresql_model_session: Session,
) -> None:
    repo = _repo(postgresql_model_session)
    template_id = uuid4()
    other_template_id = uuid4()
    _store_template_version(postgresql_model_session, template_id=template_id, version=1)
    _store_template_version(postgresql_model_session, template_id=template_id, version=2)
    _store_template_version(postgresql_model_session, template_id=other_template_id, version=1)

    low = _object(
        object_id=UUID("00000000-0000-0000-0000-000000000001"),
        template_id=template_id,
        template_version=1,
    )
    high = _object(
        object_id=UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"),
        template_id=template_id,
        template_version=1,
    )
    other_version = _object(template_id=template_id, template_version=2)
    other_template = _object(template_id=other_template_id, template_version=1)

    for object_value in (high, other_version, other_template, low):
        repo.add(object_value)

    assert repo.list_by_template_version(template_id, 1) == (low, high)


def test_postgresql_object_exact_template_version_fk_parity(
    postgresql_model_session: Session,
) -> None:
    repo = _repo(postgresql_model_session)
    valid_template_id = uuid4()
    hole_template_id = uuid4()
    draft_template_id = uuid4()
    _store_template_version(postgresql_model_session, template_id=valid_template_id, version=1)
    _store_template_version(postgresql_model_session, template_id=hole_template_id, version=1)
    _store_template_version(postgresql_model_session, template_id=hole_template_id, version=3)
    _store_template_version(
        postgresql_model_session,
        template_id=draft_template_id,
        version=1,
        status=ObjectTemplateVersionStatus.DRAFT,
    )

    valid = _object(template_id=valid_template_id, template_version=1)
    repo.add(valid)
    assert repo.get(valid.id) == valid

    with postgresql_model_session.begin_nested():
        with pytest.raises(ObjectPersistenceError):
            repo.add(_object(template_id=uuid4(), template_version=1))

    with postgresql_model_session.begin_nested():
        with pytest.raises(ObjectPersistenceError):
            repo.add(_object(template_id=hole_template_id, template_version=2))

    draft_bound = _object(template_id=draft_template_id, template_version=1)
    repo.add(draft_bound)
    assert repo.get(draft_bound.id) == draft_bound


def test_postgresql_object_exact_template_version_restrict_and_unreferenced_sibling_delete(
    postgresql_model_session: Session,
) -> None:
    repo = _repo(postgresql_model_session)
    template_id = uuid4()
    _store_template_version(postgresql_model_session, template_id=template_id, version=1)
    _store_template_version(postgresql_model_session, template_id=template_id, version=2)
    bound = _object(template_id=template_id, template_version=1)
    repo.add(bound)

    referenced = postgresql_model_session.get(
        ObjectTemplateVersionRow,
        {"template_id": str(template_id), "version": 1},
    )
    assert referenced is not None
    with postgresql_model_session.begin_nested():
        postgresql_model_session.delete(referenced)
        with pytest.raises(IntegrityError):
            postgresql_model_session.flush()

    sibling = postgresql_model_session.get(
        ObjectTemplateVersionRow,
        {"template_id": str(template_id), "version": 2},
    )
    assert sibling is not None
    postgresql_model_session.delete(sibling)
    postgresql_model_session.flush()
    assert (
        postgresql_model_session.get(
            ObjectTemplateVersionRow,
            {"template_id": str(template_id), "version": 2},
        )
        is None
    )


def test_postgresql_object_duplicate_uuid_and_missing_replace_translate_correctly(
    postgresql_model_session: Session,
) -> None:
    repo = _repo(postgresql_model_session)
    object_value = _object(object_id=uuid4())
    repo.add(object_value)

    with pytest.raises(ObjectAlreadyExists):
        repo.add(_object(object_id=object_value.id))

    with pytest.raises(ObjectNotFound):
        repo.replace(_object())


@pytest.mark.parametrize("value", [{"bad": object()}, {"bad": float("nan")}, {"bad": float("inf")}])
def test_postgresql_object_add_rejects_non_json_serializable_or_non_finite_values(
    postgresql_model_session: Session,
    value: dict[str, object],
) -> None:
    repo = _repo(postgresql_model_session)
    with pytest.raises(ObjectPersistenceError):
        repo.add(_object(properties=value))


def test_postgresql_object_replace_complete_snapshot_and_atomic_failure_behavior(
    postgresql_model_session: Session,
) -> None:
    repo = _repo(postgresql_model_session)
    original = _object(properties={"hostname": "router-01"})
    replacement_template_id = uuid4()
    _store_template_version(
        postgresql_model_session,
        template_id=replacement_template_id,
        version=3,
    )
    updated = replace(
        original,
        template_id=replacement_template_id,
        template_version=3,
        properties={"serial": "ABC123"},
    )

    repo.add(original)
    repo.replace(updated)
    assert repo.get(original.id) == updated

    with postgresql_model_session.begin_nested():
        with pytest.raises(ObjectPersistenceError):
            repo.replace(
                replace(
                    updated,
                    template_id=uuid4(),
                    template_version=1,
                    properties={"serial": "BROKEN"},
                )
            )
    assert repo.get(original.id) == updated

    with pytest.raises(ObjectPersistenceError):
        repo.replace(
            replace(
                updated,
                template_id=replacement_template_id,
                template_version=3,
                properties={"bad": object()},
            )
        )
    assert repo.get(original.id) == updated


def test_postgresql_replace_if_current_parity_and_sql_shape(
    postgresql_model_session: Session,
) -> None:
    repo = _repo(postgresql_model_session)
    original = _object(properties={"hostname": "router-01"})
    updated_template_id = uuid4()
    _store_template_version(postgresql_model_session, template_id=updated_template_id, version=2)
    success = replace(
        original,
        template_id=updated_template_id,
        template_version=2,
        properties={"hostname": "router-02"},
    )

    repo.add(original)
    statements: list[str] = []
    engine = postgresql_model_session.bind
    assert engine is not None

    def recorder(
        conn: object,
        cursor: object,
        statement: str,
        parameters: object,
        context: object,
        executemany: object,
    ) -> None:
        del conn, cursor, parameters, context, executemany
        statements.append(statement.lower())

    event.listen(engine, "before_cursor_execute", recorder)
    try:
        repo.replace_if_current(original, success)
    finally:
        event.remove(engine, "before_cursor_execute", recorder)

    assert repo.get(original.id) == success
    assert sum("update objects" in statement for statement in statements) == 1
    assert not any(statement.lstrip().startswith("select") for statement in statements)

    stale_properties = replace(success, properties={"hostname": "current"})
    with pytest.raises(ObjectConcurrentModification):
        repo.replace_if_current(original, stale_properties)
    assert repo.get(original.id) == success

    stale_version_expected = original
    stale_version_replacement = replace(original, properties={"hostname": "router-03"})
    with pytest.raises(ObjectConcurrentModification):
        repo.replace_if_current(stale_version_expected, stale_version_replacement)
    assert repo.get(original.id) == success

    with pytest.raises(InvalidObject):
        repo.replace_if_current(success, replace(success, id=uuid4()))


def test_postgresql_membership_round_trip_missing_endpoints_and_uniqueness(
    postgresql_model_session: Session,
) -> None:
    repo = _repo(postgresql_model_session)
    parent = _object()
    parent_two = _object()
    child = _object()
    membership = _membership(parent_object_id=parent.id, child_object_id=child.id)

    with pytest.raises(ObjectNotFound):
        repo.add_membership(membership)
    repo.add(parent)
    with pytest.raises(ObjectNotFound):
        repo.add_membership(membership)

    repo.add(parent_two)
    repo.add(child)
    repo.add_membership(membership)
    assert repo.get_owner(child.id) == membership

    with postgresql_model_session.begin_nested():
        with pytest.raises(ComponentMembershipAlreadyExists):
            repo.add_membership(membership)
    with postgresql_model_session.begin_nested():
        with pytest.raises(ComponentMembershipAlreadyExists):
            repo.add_membership(
                _membership(parent_object_id=parent_two.id, child_object_id=child.id)
            )


def test_postgresql_membership_same_template_chain_list_order_filter_and_detach(
    postgresql_model_session: Session,
) -> None:
    repo = _repo(postgresql_model_session)
    root = _object(object_id=UUID("00000000-0000-0000-0000-000000000100"))
    middle = _object(object_id=UUID("00000000-0000-0000-0000-000000000200"))
    leaf = _object(object_id=UUID("00000000-0000-0000-0000-000000000300"))
    child_b = _object(object_id=UUID("00000000-0000-0000-0000-000000000020"))
    child_c = _object(object_id=UUID("00000000-0000-0000-0000-000000000005"))
    for object_value in (root, middle, leaf, child_b, child_c):
        repo.add(object_value)

    root_middle = _membership(
        parent_object_id=root.id,
        child_object_id=middle.id,
        slot_name="modules",
    )
    root_b = _membership(
        parent_object_id=root.id,
        child_object_id=child_b.id,
        slot_name="interfaces",
    )
    root_c = _membership(
        parent_object_id=root.id,
        child_object_id=child_c.id,
        slot_name="interfaces",
    )
    middle_leaf = _membership(
        parent_object_id=middle.id,
        child_object_id=leaf.id,
        slot_name="subinterfaces",
    )

    repo.add_membership(root_middle)
    repo.add_membership(root_b)
    repo.add_membership(root_c)
    repo.add_membership(middle_leaf)

    assert repo.list_components(root.id) == (root_c, root_b, root_middle)
    assert repo.list_components(root.id, slot_name="interfaces") == (root_c, root_b)
    assert repo.list_components(uuid4()) == ()
    assert repo.get_owner(middle.id) == root_middle
    assert repo.get_owner(leaf.id) == middle_leaf

    repo.remove_membership(middle.id)
    assert repo.get_owner(middle.id) is None
    assert repo.get_owner(leaf.id) == middle_leaf
    assert repo.list_components(middle.id) == (middle_leaf,)
    assert repo.get(root.id) == root
    assert repo.get(middle.id) == middle

    with pytest.raises(ComponentMembershipNotFound):
        repo.remove_membership(uuid4())


def test_postgresql_membership_delete_cascade_behavior(
    postgresql_model_session: Session,
) -> None:
    repo = _repo(postgresql_model_session)

    parent = _object()
    child = _object()
    repo.add(parent)
    repo.add(child)
    repo.add_membership(_membership(parent_object_id=parent.id, child_object_id=child.id))
    repo.delete(child.id)
    assert repo.get(parent.id) == parent
    assert repo.get(child.id) is None
    assert repo.list_components(parent.id) == ()

    parent_two = _object()
    child_two = _object()
    repo.add(parent_two)
    repo.add(child_two)
    repo.add_membership(_membership(parent_object_id=parent_two.id, child_object_id=child_two.id))
    repo.delete(parent_two.id)
    assert repo.get(parent_two.id) is None
    assert repo.get(child_two.id) == child_two
    assert repo.get_owner(child_two.id) is None

    root = _object()
    middle = _object()
    leaf = _object()
    for object_value in (root, middle, leaf):
        repo.add(object_value)
    repo.add_membership(_membership(parent_object_id=root.id, child_object_id=middle.id))
    repo.add_membership(_membership(parent_object_id=middle.id, child_object_id=leaf.id))
    repo.delete(middle.id)
    assert repo.get(root.id) == root
    assert repo.get(middle.id) is None
    assert repo.get(leaf.id) == leaf
    assert repo.list_components(root.id) == ()
    assert repo.get_owner(leaf.id) is None


def test_postgresql_membership_physical_checks_and_corruption_mapping(
    postgresql_model_session: Session,
) -> None:
    repo = _repo(postgresql_model_session)
    parent = _object()
    child = _object()
    repo.add(parent)
    repo.add(child)

    with postgresql_model_session.begin_nested():
        postgresql_model_session.add(
            ObjectComponentRow(
                parent_object_id=str(parent.id),
                slot_name="",
                child_object_id=str(child.id),
            )
        )
        with pytest.raises(IntegrityError):
            postgresql_model_session.flush()
    postgresql_model_session.expunge_all()

    with postgresql_model_session.begin_nested():
        postgresql_model_session.add(
            ObjectComponentRow(
                parent_object_id=str(parent.id),
                slot_name="children",
                child_object_id=str(parent.id),
            )
        )
        with pytest.raises(IntegrityError):
            postgresql_model_session.flush()
    postgresql_model_session.expunge_all()

    postgresql_model_session.add(
        ObjectRow(
            id="not-a-uuid",
            template_id=str(DEFAULT_TEMPLATE_ID),
            template_version=1,
            properties_json="{}",
        )
    )
    postgresql_model_session.flush()
    with pytest.raises(ObjectPersistenceError):
        repo.list()


@contextmanager
def _fresh_session(
    postgresql_engine,
    schema: str,
) -> Generator[Session, None, None]:
    connection = postgresql_engine.connect()
    quoted_schema = postgresql_engine.dialect.identifier_preparer.quote_identifier(schema)
    connection.execute(text(f"SET search_path TO {quoted_schema}"))
    session = Session(bind=connection, expire_on_commit=False)
    try:
        yield session
    finally:
        session.close()
        connection.close()
