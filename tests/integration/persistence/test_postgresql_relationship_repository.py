from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from sqlalchemy import event, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from netauto.core.object import Object
from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateVersion,
    ObjectTemplateVersionStatus,
)
from netauto.core.relationship import (
    Relationship,
    RelationshipAlreadyExists,
    RelationshipNotFound,
    RelationshipPersistenceError,
)
from netauto.persistence.sqlalchemy.models import (
    ObjectRow,
    RelationshipDefinitionRow,
    RelationshipRow,
)
from netauto.persistence.sqlalchemy.object_repository import SqlAlchemyObjectRepository
from netauto.persistence.sqlalchemy.objecttemplate_repository import (
    SqlAlchemyObjectTemplateRepository,
)
from netauto.persistence.sqlalchemy.relationship_repository import (
    SqlAlchemyRelationshipDefinitionRepository,
    SqlAlchemyRelationshipRepository,
)

pytestmark = pytest.mark.postgresql


def _template(
    *,
    template_id: UUID | None = None,
    namespace: str = "network",
    name: str = "device",
) -> ObjectTemplate:
    return ObjectTemplate(
        id=template_id or uuid4(),
        namespace=namespace,
        name=name,
        description=None,
        abstract=False,
    )


def _store_template(
    repo: SqlAlchemyObjectTemplateRepository,
    *,
    template_id: UUID | None = None,
    namespace: str = "network",
    name: str = "device",
) -> UUID:
    template = _template(
        template_id=template_id,
        namespace=namespace,
        name=name,
    )
    repo.add(template)
    repo.add_version(
        ObjectTemplateVersion(
            template_id=template.id,
            version=1,
            status=ObjectTemplateVersionStatus.DRAFT,
            properties=(),
        )
    )
    return template.id


def _definition_row(
    *,
    definition_id: UUID | None = None,
    source_template_id: UUID,
    target_template_id: UUID,
    forward_name: str = "uses",
    reverse_name: str = "used_by",
) -> RelationshipDefinitionRow:
    return RelationshipDefinitionRow(
        id=str(definition_id or uuid4()),
        source_template_id=str(source_template_id),
        target_template_id=str(target_template_id),
        forward_name=forward_name,
        reverse_name=reverse_name,
    )


def _object(
    *,
    object_id: UUID | None = None,
    template_id: UUID,
) -> Object:
    return Object(
        id=object_id or uuid4(),
        template_id=template_id,
        template_version=1,
        properties={},
    )


def _relationship(
    *,
    relationship_id: UUID | None = None,
    relationship_definition_id: UUID,
    source_object_id: UUID,
    target_object_id: UUID,
) -> Relationship:
    return Relationship(
        id=relationship_id or uuid4(),
        relationship_definition_id=relationship_definition_id,
        source_object_id=source_object_id,
        target_object_id=target_object_id,
    )


def _seed_definition_and_objects(
    template_repo: SqlAlchemyObjectTemplateRepository,
    object_repo: SqlAlchemyObjectRepository,
    session: Session,
) -> tuple[UUID, Object, Object]:
    source_template_id = _store_template(
        template_repo,
        template_id=UUID("00000000-0000-0000-0000-0000000000c1"),
        name="source",
    )
    target_template_id = _store_template(
        template_repo,
        template_id=UUID("00000000-0000-0000-0000-0000000000c2"),
        name="target",
    )
    definition_row = _definition_row(
        definition_id=UUID("00000000-0000-0000-0000-0000000000d1"),
        source_template_id=source_template_id,
        target_template_id=target_template_id,
    )
    session.add(definition_row)
    session.flush()
    source_object = _object(
        object_id=UUID("00000000-0000-0000-0000-0000000000e1"),
        template_id=source_template_id,
    )
    target_object = _object(
        object_id=UUID("00000000-0000-0000-0000-0000000000e2"),
        template_id=target_template_id,
    )
    object_repo.add(source_object)
    object_repo.add(target_object)
    return UUID(definition_row.id), source_object, target_object


def test_postgresql_relationship_list_add_get_and_get_by_endpoints_round_trip(
    postgresql_model_session: Session,
) -> None:
    template_repo = SqlAlchemyObjectTemplateRepository(postgresql_model_session)
    object_repo = SqlAlchemyObjectRepository(postgresql_model_session)
    repo = SqlAlchemyRelationshipRepository(postgresql_model_session)
    definition_id, source_object, target_object = _seed_definition_and_objects(
        template_repo,
        object_repo,
        postgresql_model_session,
    )
    low = _relationship(
        relationship_id=UUID("00000000-0000-0000-0000-000000000001"),
        relationship_definition_id=definition_id,
        source_object_id=source_object.id,
        target_object_id=target_object.id,
    )
    other_source = _object(
        object_id=UUID("00000000-0000-0000-0000-0000000000e3"),
        template_id=source_object.template_id,
    )
    other_target = _object(
        object_id=UUID("00000000-0000-0000-0000-0000000000e4"),
        template_id=target_object.template_id,
    )
    object_repo.add(other_source)
    object_repo.add(other_target)
    high = _relationship(
        relationship_id=UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"),
        relationship_definition_id=definition_id,
        source_object_id=other_source.id,
        target_object_id=other_target.id,
    )

    assert repo.list() == ()

    repo.add(high)
    repo.add(low)

    assert repo.get(low.id) == low
    assert repo.get(uuid4()) is None
    assert repo.get_by_endpoints(definition_id, source_object.id, target_object.id) == low
    assert repo.get_by_endpoints(definition_id, target_object.id, source_object.id) is None
    assert repo.list() == (low, high)

    row = postgresql_model_session.get(RelationshipRow, str(low.id))
    assert row is not None
    assert row.relationship_definition_id == str(definition_id)
    assert row.source_object_id == str(source_object.id)
    assert row.target_object_id == str(target_object.id)


def test_postgresql_relationship_duplicate_contracts_and_self_link(
    postgresql_model_session: Session,
) -> None:
    template_repo = SqlAlchemyObjectTemplateRepository(postgresql_model_session)
    object_repo = SqlAlchemyObjectRepository(postgresql_model_session)
    repo = SqlAlchemyRelationshipRepository(postgresql_model_session)
    definition_id, source_object, target_object = _seed_definition_and_objects(
        template_repo,
        object_repo,
        postgresql_model_session,
    )
    relationship = _relationship(
        relationship_id=UUID("11111111-1111-1111-1111-111111111111"),
        relationship_definition_id=definition_id,
        source_object_id=source_object.id,
        target_object_id=target_object.id,
    )
    repo.add(relationship)
    postgresql_model_session.commit()

    with pytest.raises(RelationshipAlreadyExists):
        repo.add(
            _relationship(
                relationship_id=relationship.id,
                relationship_definition_id=definition_id,
                source_object_id=target_object.id,
                target_object_id=source_object.id,
            )
        )
    postgresql_model_session.rollback()

    with pytest.raises(RelationshipAlreadyExists):
        repo.add(
            _relationship(
                relationship_definition_id=definition_id,
                source_object_id=source_object.id,
                target_object_id=target_object.id,
            )
        )
    postgresql_model_session.rollback()

    another_definition = _definition_row(
        definition_id=UUID("00000000-0000-0000-0000-0000000000d2"),
        source_template_id=source_object.template_id,
        target_template_id=target_object.template_id,
        forward_name="manages",
        reverse_name="managed_by",
    )
    postgresql_model_session.add(another_definition)
    postgresql_model_session.flush()
    same_endpoints_other_definition = _relationship(
        relationship_id=UUID("22222222-2222-2222-2222-222222222222"),
        relationship_definition_id=UUID(another_definition.id),
        source_object_id=source_object.id,
        target_object_id=target_object.id,
    )
    repo.add(same_endpoints_other_definition)

    self_link = _relationship(
        relationship_id=UUID("33333333-3333-3333-3333-333333333333"),
        relationship_definition_id=definition_id,
        source_object_id=source_object.id,
        target_object_id=source_object.id,
    )
    repo.add(self_link)

    assert repo.get(self_link.id) == self_link


def test_postgresql_relationship_forced_db_unique_fallback_maps_to_already_exists(
    postgresql_model_session: Session,
) -> None:
    template_repo = SqlAlchemyObjectTemplateRepository(postgresql_model_session)
    object_repo = SqlAlchemyObjectRepository(postgresql_model_session)
    repo = SqlAlchemyRelationshipRepository(postgresql_model_session)
    definition_id, source_object, target_object = _seed_definition_and_objects(
        template_repo,
        object_repo,
        postgresql_model_session,
    )
    existing = _relationship(
        relationship_id=UUID("44444444-4444-4444-4444-444444444444"),
        relationship_definition_id=definition_id,
        source_object_id=source_object.id,
        target_object_id=target_object.id,
    )
    duplicate = _relationship(
        relationship_id=UUID("55555555-5555-5555-5555-555555555555"),
        relationship_definition_id=definition_id,
        source_object_id=source_object.id,
        target_object_id=target_object.id,
    )
    repo.add(existing)
    postgresql_model_session.commit()

    original = repo.get_by_endpoints
    repo.get_by_endpoints = lambda *_args, **_kwargs: None  # type: ignore[method-assign]
    try:
        with pytest.raises(RelationshipAlreadyExists):
            repo.add(duplicate)
    finally:
        repo.get_by_endpoints = original  # type: ignore[method-assign]
    postgresql_model_session.rollback()

    assert repo.get(existing.id) == existing
    assert repo.get(duplicate.id) is None


def test_postgresql_relationship_fk_errors_and_delete_contracts(
    postgresql_model_session: Session,
) -> None:
    template_repo = SqlAlchemyObjectTemplateRepository(postgresql_model_session)
    object_repo = SqlAlchemyObjectRepository(postgresql_model_session)
    definition_repo = SqlAlchemyRelationshipDefinitionRepository(postgresql_model_session)
    repo = SqlAlchemyRelationshipRepository(postgresql_model_session)
    definition_id, source_object, target_object = _seed_definition_and_objects(
        template_repo,
        object_repo,
        postgresql_model_session,
    )
    valid = _relationship(
        relationship_id=UUID("66666666-6666-6666-6666-666666666666"),
        relationship_definition_id=definition_id,
        source_object_id=source_object.id,
        target_object_id=target_object.id,
    )
    repo.add(valid)
    postgresql_model_session.commit()

    with postgresql_model_session.begin_nested():
        with pytest.raises(RelationshipPersistenceError):
            repo.add(
                _relationship(
                    relationship_definition_id=uuid4(),
                    source_object_id=source_object.id,
                    target_object_id=target_object.id,
                )
            )

    with postgresql_model_session.begin_nested():
        with pytest.raises(RelationshipPersistenceError):
            repo.add(
                _relationship(
                    relationship_definition_id=definition_id,
                    source_object_id=uuid4(),
                    target_object_id=target_object.id,
                )
            )

    with postgresql_model_session.begin_nested():
        with pytest.raises(RelationshipPersistenceError):
            repo.add(
                _relationship(
                    relationship_definition_id=definition_id,
                    source_object_id=source_object.id,
                    target_object_id=uuid4(),
                )
            )

    assert repo.get(valid.id) == valid

    with pytest.raises(RelationshipNotFound):
        repo.delete(uuid4())

    repo.delete(valid.id)
    assert repo.get(valid.id) is None
    assert postgresql_model_session.get(ObjectRow, str(source_object.id)) is not None
    assert postgresql_model_session.get(ObjectRow, str(target_object.id)) is not None
    assert definition_repo.get(definition_id) is not None


def test_postgresql_relationship_list_by_definition_filters_and_orders(
    postgresql_model_session: Session,
) -> None:
    template_repo = SqlAlchemyObjectTemplateRepository(postgresql_model_session)
    object_repo = SqlAlchemyObjectRepository(postgresql_model_session)
    repo = SqlAlchemyRelationshipRepository(postgresql_model_session)
    definition_id, source_object, target_object = _seed_definition_and_objects(
        template_repo,
        object_repo,
        postgresql_model_session,
    )
    other_definition = _definition_row(
        definition_id=UUID("00000000-0000-0000-0000-0000000000d3"),
        source_template_id=source_object.template_id,
        target_template_id=target_object.template_id,
        forward_name="connects_to",
        reverse_name="connected_from",
    )
    postgresql_model_session.add(other_definition)
    postgresql_model_session.flush()
    first = _relationship(
        relationship_id=UUID("00000000-0000-0000-0000-000000000001"),
        relationship_definition_id=definition_id,
        source_object_id=source_object.id,
        target_object_id=target_object.id,
    )
    second_source = _object(
        object_id=UUID("00000000-0000-0000-0000-0000000000e5"),
        template_id=source_object.template_id,
    )
    second_target = _object(
        object_id=UUID("00000000-0000-0000-0000-0000000000e6"),
        template_id=target_object.template_id,
    )
    object_repo.add(second_source)
    object_repo.add(second_target)
    second = _relationship(
        relationship_id=UUID("11111111-1111-1111-1111-111111111111"),
        relationship_definition_id=definition_id,
        source_object_id=second_source.id,
        target_object_id=second_target.id,
    )
    unrelated = _relationship(
        relationship_id=UUID("22222222-2222-2222-2222-222222222222"),
        relationship_definition_id=UUID(other_definition.id),
        source_object_id=source_object.id,
        target_object_id=target_object.id,
    )

    repo.add(second)
    repo.add(unrelated)
    repo.add(first)

    assert repo.list_by_definition(definition_id) == (first, second)
    assert repo.list_by_definition(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")) == ()


def test_postgresql_relationship_list_incident_to_objects_semantics(
    postgresql_model_session: Session,
) -> None:
    template_repo = SqlAlchemyObjectTemplateRepository(postgresql_model_session)
    object_repo = SqlAlchemyObjectRepository(postgresql_model_session)
    repo = SqlAlchemyRelationshipRepository(postgresql_model_session)
    definition_id, subtree_source, subtree_child = _seed_definition_and_objects(
        template_repo,
        object_repo,
        postgresql_model_session,
    )
    external_template_id = _store_template(
        template_repo,
        template_id=UUID("00000000-0000-0000-0000-0000000000c3"),
        name="external",
    )
    unrelated_template_id = _store_template(
        template_repo,
        template_id=UUID("00000000-0000-0000-0000-0000000000c4"),
        name="unrelated",
    )
    incoming_definition = _definition_row(
        definition_id=UUID("00000000-0000-0000-0000-0000000000d4"),
        source_template_id=external_template_id,
        target_template_id=subtree_source.template_id,
    )
    internal_definition = _definition_row(
        definition_id=UUID("00000000-0000-0000-0000-0000000000d5"),
        source_template_id=subtree_source.template_id,
        target_template_id=subtree_source.template_id,
        forward_name="contains",
        reverse_name="contained_by",
    )
    self_definition = _definition_row(
        definition_id=UUID("00000000-0000-0000-0000-0000000000d6"),
        source_template_id=subtree_source.template_id,
        target_template_id=subtree_source.template_id,
        forward_name="connects_to",
        reverse_name="connects_to",
    )
    unrelated_definition = _definition_row(
        definition_id=UUID("00000000-0000-0000-0000-0000000000d7"),
        source_template_id=unrelated_template_id,
        target_template_id=unrelated_template_id,
        forward_name="depends_on",
        reverse_name="dependency_of",
    )
    postgresql_model_session.add_all(
        (
            incoming_definition,
            internal_definition,
            self_definition,
            unrelated_definition,
        )
    )
    postgresql_model_session.flush()
    external = _object(
        object_id=UUID("00000000-0000-0000-0000-0000000000e7"),
        template_id=external_template_id,
    )
    unrelated_a = _object(
        object_id=UUID("00000000-0000-0000-0000-0000000000e8"),
        template_id=unrelated_template_id,
    )
    unrelated_b = _object(
        object_id=UUID("00000000-0000-0000-0000-0000000000e9"),
        template_id=unrelated_template_id,
    )
    object_repo.add(external)
    object_repo.add(unrelated_a)
    object_repo.add(unrelated_b)
    outgoing = _relationship(
        relationship_id=UUID("00000000-0000-0000-0000-000000000001"),
        relationship_definition_id=definition_id,
        source_object_id=subtree_source.id,
        target_object_id=external.id,
    )
    incoming = _relationship(
        relationship_id=UUID("11111111-1111-1111-1111-111111111111"),
        relationship_definition_id=UUID(incoming_definition.id),
        source_object_id=external.id,
        target_object_id=subtree_child.id,
    )
    internal = _relationship(
        relationship_id=UUID("22222222-2222-2222-2222-222222222222"),
        relationship_definition_id=UUID(internal_definition.id),
        source_object_id=subtree_source.id,
        target_object_id=subtree_child.id,
    )
    self_link = _relationship(
        relationship_id=UUID("33333333-3333-3333-3333-333333333333"),
        relationship_definition_id=UUID(self_definition.id),
        source_object_id=subtree_child.id,
        target_object_id=subtree_child.id,
    )
    unrelated = _relationship(
        relationship_id=UUID("44444444-4444-4444-4444-444444444444"),
        relationship_definition_id=UUID(unrelated_definition.id),
        source_object_id=unrelated_a.id,
        target_object_id=unrelated_b.id,
    )
    for relationship in (unrelated, self_link, internal, incoming, outgoing):
        postgresql_model_session.add(
            RelationshipRow(
                id=str(relationship.id),
                relationship_definition_id=str(relationship.relationship_definition_id),
                source_object_id=str(relationship.source_object_id),
                target_object_id=str(relationship.target_object_id),
            )
        )
    postgresql_model_session.flush()

    assert repo.list_incident_to_objects(set()) == ()
    assert repo.list_incident_to_objects(
        {
            subtree_source.id,
            subtree_child.id,
            subtree_source.id,
        }
    ) == (outgoing, incoming, internal, self_link)


def test_postgresql_relationship_restrict_semantics(
    postgresql_model_session: Session,
) -> None:
    template_repo = SqlAlchemyObjectTemplateRepository(postgresql_model_session)
    object_repo = SqlAlchemyObjectRepository(postgresql_model_session)
    definition_repo = SqlAlchemyRelationshipDefinitionRepository(postgresql_model_session)
    repo = SqlAlchemyRelationshipRepository(postgresql_model_session)
    definition_id, source_object, target_object = _seed_definition_and_objects(
        template_repo,
        object_repo,
        postgresql_model_session,
    )
    relationship = _relationship(
        relationship_id=UUID("77777777-7777-7777-7777-777777777777"),
        relationship_definition_id=definition_id,
        source_object_id=source_object.id,
        target_object_id=target_object.id,
    )
    repo.add(relationship)
    postgresql_model_session.commit()

    with postgresql_model_session.begin_nested():
        with pytest.raises(Exception):
            definition_repo.delete(definition_id)

    source_row = postgresql_model_session.get(ObjectRow, str(source_object.id))
    assert source_row is not None
    with postgresql_model_session.begin_nested():
        postgresql_model_session.delete(source_row)
        with pytest.raises(IntegrityError):
            postgresql_model_session.flush()

    target_row = postgresql_model_session.get(ObjectRow, str(target_object.id))
    assert target_row is not None
    with postgresql_model_session.begin_nested():
        postgresql_model_session.delete(target_row)
        with pytest.raises(IntegrityError):
            postgresql_model_session.flush()

    repo.delete(relationship.id)

    deletable_source = postgresql_model_session.get(ObjectRow, str(source_object.id))
    deletable_target = postgresql_model_session.get(ObjectRow, str(target_object.id))
    assert deletable_source is not None
    assert deletable_target is not None
    postgresql_model_session.delete(deletable_source)
    postgresql_model_session.delete(deletable_target)
    postgresql_model_session.flush()
    assert repo.get(relationship.id) is None


def test_postgresql_relationship_delete_removes_only_relationship_edge(
    postgresql_model_session: Session,
) -> None:
    template_repo = SqlAlchemyObjectTemplateRepository(postgresql_model_session)
    object_repo = SqlAlchemyObjectRepository(postgresql_model_session)
    definition_repo = SqlAlchemyRelationshipDefinitionRepository(postgresql_model_session)
    repo = SqlAlchemyRelationshipRepository(postgresql_model_session)
    definition_id, source_object, target_object = _seed_definition_and_objects(
        template_repo,
        object_repo,
        postgresql_model_session,
    )
    relationship = _relationship(
        relationship_definition_id=definition_id,
        source_object_id=source_object.id,
        target_object_id=target_object.id,
    )
    repo.add(relationship)

    repo.delete(relationship.id)

    assert repo.get(relationship.id) is None
    assert postgresql_model_session.get(ObjectRow, str(source_object.id)) is not None
    assert postgresql_model_session.get(ObjectRow, str(target_object.id)) is not None
    assert definition_repo.get(definition_id) is not None


def test_postgresql_relationship_add_executes_insert_sql(
    postgresql_model_session: Session,
) -> None:
    template_repo = SqlAlchemyObjectTemplateRepository(postgresql_model_session)
    object_repo = SqlAlchemyObjectRepository(postgresql_model_session)
    repo = SqlAlchemyRelationshipRepository(postgresql_model_session)
    definition_id, source_object, target_object = _seed_definition_and_objects(
        template_repo,
        object_repo,
        postgresql_model_session,
    )
    relationship = _relationship(
        relationship_definition_id=definition_id,
        source_object_id=source_object.id,
        target_object_id=target_object.id,
    )
    statements: list[str] = []

    def capture_sql(_conn, _cursor, statement, _parameters, _context, _executemany) -> None:
        statements.append(statement)

    event.listen(postgresql_model_session.bind, "before_cursor_execute", capture_sql)
    try:
        repo.add(relationship)
    finally:
        event.remove(postgresql_model_session.bind, "before_cursor_execute", capture_sql)

    assert any("insert into relationships" in statement.lower() for statement in statements)
    assert repo.get(relationship.id) == relationship


def test_postgresql_relationship_invalid_stored_row_raises_persistence_error(
    postgresql_model_session: Session,
) -> None:
    template_repo = SqlAlchemyObjectTemplateRepository(postgresql_model_session)
    object_repo = SqlAlchemyObjectRepository(postgresql_model_session)
    repo = SqlAlchemyRelationshipRepository(postgresql_model_session)
    definition_id, source_object, target_object = _seed_definition_and_objects(
        template_repo,
        object_repo,
        postgresql_model_session,
    )
    postgresql_model_session.execute(
        text(
            """
            INSERT INTO relationships (
                id,
                relationship_definition_id,
                source_object_id,
                target_object_id
            ) VALUES (:id, :definition_id, :source_id, :target_id)
            """
        ),
        {
            "id": "not-a-uuid",
            "definition_id": str(definition_id),
            "source_id": str(source_object.id),
            "target_id": str(target_object.id),
        },
    )
    postgresql_model_session.flush()

    with pytest.raises(RelationshipPersistenceError):
        repo.list()
