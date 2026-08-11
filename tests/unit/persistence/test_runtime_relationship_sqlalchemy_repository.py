from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

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
from netauto.persistence.sqlalchemy.database import create_schema, create_sqlite_engine
from netauto.persistence.sqlalchemy.models import RelationshipDefinitionRow, RelationshipRow
from netauto.persistence.sqlalchemy.object_repository import SqlAlchemyObjectRepository
from netauto.persistence.sqlalchemy.objecttemplate_repository import (
    SqlAlchemyObjectTemplateRepository,
)
from netauto.persistence.sqlalchemy.relationship_repository import (
    SqlAlchemyRelationshipDefinitionRepository,
    SqlAlchemyRelationshipRepository,
)


def _repo(
    tmp_path: Path,
    filename: str,
) -> tuple[
    SqlAlchemyRelationshipRepository,
    SqlAlchemyRelationshipDefinitionRepository,
    SqlAlchemyObjectRepository,
    SqlAlchemyObjectTemplateRepository,
    Session,
    Engine,
]:
    engine = create_sqlite_engine(f"sqlite:///{tmp_path / filename}")
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    session = session_factory()
    return (
        SqlAlchemyRelationshipRepository(session),
        SqlAlchemyRelationshipDefinitionRepository(session),
        SqlAlchemyObjectRepository(session),
        SqlAlchemyObjectTemplateRepository(session),
        session,
        engine,
    )


def _template(
    *,
    name: str,
    template_id: UUID | None = None,
) -> ObjectTemplate:
    return ObjectTemplate(
        id=template_id or uuid4(),
        namespace="network",
        name=name,
        description=f"{name} template",
        abstract=False,
    )


def _relationship_definition_row(
    *,
    definition_id: UUID | None = None,
    source_template_id: UUID,
    target_template_id: UUID,
    forward_name: str = "uses",
    reverse_name: str = "is_used_by",
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
    template_version: int = 1,
) -> Object:
    return Object(
        id=object_id or uuid4(),
        template_id=template_id,
        template_version=template_version,
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
    source_template = _template(name="source")
    target_template = _template(name="target")
    template_repo.add(source_template)
    template_repo.add(target_template)
    template_repo.add_version(
        ObjectTemplateVersion(
            template_id=source_template.id,
            version=1,
            status=ObjectTemplateVersionStatus.DRAFT,
            properties=(),
        )
    )
    template_repo.add_version(
        ObjectTemplateVersion(
            template_id=target_template.id,
            version=1,
            status=ObjectTemplateVersionStatus.DRAFT,
            properties=(),
        )
    )
    definition_row = _relationship_definition_row(
        source_template_id=source_template.id,
        target_template_id=target_template.id,
    )
    session.add(definition_row)
    source_object = _object(template_id=source_template.id)
    target_object = _object(template_id=target_template.id)
    object_repo.add(source_object)
    object_repo.add(target_object)
    session.flush()
    return UUID(definition_row.id), source_object, target_object


def test_schema_encodes_runtime_relationship_invariants(tmp_path: Path) -> None:
    _repo_obj, _definition_repo, _object_repo, _template_repo, session, engine = _repo(
        tmp_path,
        "runtime_relationship_schema.sqlite3",
    )
    session.close()
    try:
        inspector = inspect(engine)
        pk = inspector.get_pk_constraint("relationships")
        fks = inspector.get_foreign_keys("relationships")
        columns = {column["name"] for column in inspector.get_columns("relationships")}
        unique_constraints = inspector.get_unique_constraints("relationships")

        assert pk["constrained_columns"] == ["id"]
        assert columns == {
            "id",
            "relationship_definition_id",
            "source_object_id",
            "target_object_id",
        }
        assert "source_template_id" not in columns
        assert "target_template_id" not in columns
        assert "forward_name" not in columns
        assert "reverse_name" not in columns
        assert unique_constraints == [
            {
                "name": "uq_relationships_definition_source_target",
                "column_names": [
                    "relationship_definition_id",
                    "source_object_id",
                    "target_object_id",
                ],
            }
        ]
        assert len(fks) == 3
        definition_fk = next(
            fk for fk in fks if fk["constrained_columns"] == ["relationship_definition_id"]
        )
        source_fk = next(fk for fk in fks if fk["constrained_columns"] == ["source_object_id"])
        target_fk = next(fk for fk in fks if fk["constrained_columns"] == ["target_object_id"])
        assert definition_fk["referred_table"] == "relationship_definitions"
        assert definition_fk["referred_columns"] == ["id"]
        assert source_fk["referred_table"] == "objects"
        assert source_fk["referred_columns"] == ["id"]
        assert target_fk["referred_table"] == "objects"
        assert target_fk["referred_columns"] == ["id"]
        assert definition_fk.get("options", {}).get("ondelete") == "RESTRICT"
        assert source_fk.get("options", {}).get("ondelete") == "RESTRICT"
        assert target_fk.get("options", {}).get("ondelete") == "RESTRICT"
    finally:
        engine.dispose()


def test_round_trip_and_get_by_endpoints(tmp_path: Path) -> None:
    repo, _definition_repo, object_repo, template_repo, session, engine = _repo(
        tmp_path,
        "runtime_relationship_round_trip.sqlite3",
    )
    try:
        definition_id, source_object, target_object = _seed_definition_and_objects(
            template_repo,
            object_repo,
            session,
        )
        relationship = _relationship(
            relationship_definition_id=definition_id,
            source_object_id=source_object.id,
            target_object_id=target_object.id,
        )

        repo.add(relationship)

        assert repo.get(relationship.id) == relationship
        assert (
            repo.get_by_endpoints(
                definition_id,
                source_object.id,
                target_object.id,
            )
            == relationship
        )
        rows = session.query(RelationshipRow).all()
        assert len(rows) == 1
        assert rows[0].id == str(relationship.id)
    finally:
        session.close()
        engine.dispose()


def test_list_is_deterministic_by_uuid_string(tmp_path: Path) -> None:
    repo, _definition_repo, object_repo, template_repo, session, engine = _repo(
        tmp_path,
        "runtime_relationship_ordering.sqlite3",
    )
    try:
        definition_id, source_object, target_object = _seed_definition_and_objects(
            template_repo,
            object_repo,
            session,
        )
        other_source = _object(template_id=source_object.template_id)
        other_target = _object(template_id=target_object.template_id)
        object_repo.add(other_source)
        object_repo.add(other_target)
        low = _relationship(
            relationship_id=UUID("00000000-0000-0000-0000-000000000001"),
            relationship_definition_id=definition_id,
            source_object_id=source_object.id,
            target_object_id=target_object.id,
        )
        mid = _relationship(
            relationship_id=UUID("11111111-1111-1111-1111-111111111111"),
            relationship_definition_id=definition_id,
            source_object_id=other_source.id,
            target_object_id=other_target.id,
        )
        another_definition = _relationship_definition_row(
            source_template_id=source_object.template_id,
            target_template_id=target_object.template_id,
            forward_name="manages",
            reverse_name="managed_by",
        )
        session.add(another_definition)
        session.flush()
        high = _relationship(
            relationship_id=UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"),
            relationship_definition_id=UUID(another_definition.id),
            source_object_id=source_object.id,
            target_object_id=target_object.id,
        )

        repo.add(high)
        repo.add(mid)
        repo.add(low)

        assert repo.list() == (low, mid, high)
    finally:
        session.close()
        engine.dispose()


def test_duplicate_primary_key_is_rejected(tmp_path: Path) -> None:
    repo, _definition_repo, object_repo, template_repo, session, engine = _repo(
        tmp_path,
        "runtime_relationship_duplicate_pk.sqlite3",
    )
    try:
        definition_id, source_object, target_object = _seed_definition_and_objects(
            template_repo,
            object_repo,
            session,
        )
        relationship = _relationship(
            relationship_id=uuid4(),
            relationship_definition_id=definition_id,
            source_object_id=source_object.id,
            target_object_id=target_object.id,
        )
        duplicate = _relationship(
            relationship_id=relationship.id,
            relationship_definition_id=definition_id,
            source_object_id=target_object.id,
            target_object_id=source_object.id,
        )

        repo.add(relationship)

        with pytest.raises(RelationshipAlreadyExists):
            repo.add(duplicate)
    finally:
        session.close()
        engine.dispose()


def test_duplicate_canonical_triple_is_rejected(tmp_path: Path) -> None:
    repo, _definition_repo, object_repo, template_repo, session, engine = _repo(
        tmp_path,
        "runtime_relationship_duplicate_triple.sqlite3",
    )
    try:
        definition_id, source_object, target_object = _seed_definition_and_objects(
            template_repo,
            object_repo,
            session,
        )
        relationship = _relationship(
            relationship_definition_id=definition_id,
            source_object_id=source_object.id,
            target_object_id=target_object.id,
        )
        duplicate = _relationship(
            relationship_definition_id=definition_id,
            source_object_id=source_object.id,
            target_object_id=target_object.id,
        )

        repo.add(relationship)

        with pytest.raises(RelationshipAlreadyExists):
            repo.add(duplicate)
    finally:
        session.close()
        engine.dispose()


def test_same_object_pair_with_different_definitions_is_allowed(tmp_path: Path) -> None:
    repo, _definition_repo, object_repo, template_repo, session, engine = _repo(
        tmp_path,
        "runtime_relationship_multi_definition.sqlite3",
    )
    try:
        definition_id, source_object, target_object = _seed_definition_and_objects(
            template_repo,
            object_repo,
            session,
        )
        another_definition = _relationship_definition_row(
            source_template_id=source_object.template_id,
            target_template_id=target_object.template_id,
            forward_name="manages",
            reverse_name="managed_by",
        )
        session.add(another_definition)
        session.flush()
        first = _relationship(
            relationship_definition_id=definition_id,
            source_object_id=source_object.id,
            target_object_id=target_object.id,
        )
        second = _relationship(
            relationship_definition_id=UUID(another_definition.id),
            source_object_id=source_object.id,
            target_object_id=target_object.id,
        )

        repo.add(first)
        repo.add(second)

        assert repo.list() == tuple(sorted((first, second), key=lambda item: str(item.id)))
    finally:
        session.close()
        engine.dispose()


def test_self_link_persists(tmp_path: Path) -> None:
    repo, _definition_repo, object_repo, template_repo, session, engine = _repo(
        tmp_path,
        "runtime_relationship_self_link.sqlite3",
    )
    try:
        definition_id, source_object, _target_object = _seed_definition_and_objects(
            template_repo,
            object_repo,
            session,
        )
        relationship = _relationship(
            relationship_definition_id=definition_id,
            source_object_id=source_object.id,
            target_object_id=source_object.id,
        )

        repo.add(relationship)

        assert repo.get(relationship.id) == relationship
    finally:
        session.close()
        engine.dispose()


def test_list_by_definition_filters_and_orders(tmp_path: Path) -> None:
    repo, _definition_repo, object_repo, template_repo, session, engine = _repo(
        tmp_path,
        "runtime_relationship_list_by_definition.sqlite3",
    )
    try:
        definition_id, source_object, target_object = _seed_definition_and_objects(
            template_repo,
            object_repo,
            session,
        )
        other_definition = _relationship_definition_row(
            source_template_id=source_object.template_id,
            target_template_id=target_object.template_id,
        )
        session.add(other_definition)
        session.flush()
        first = _relationship(
            relationship_id=UUID("00000000-0000-0000-0000-000000000001"),
            relationship_definition_id=definition_id,
            source_object_id=source_object.id,
            target_object_id=target_object.id,
        )
        second_source = _object(template_id=source_object.template_id)
        second_target = _object(template_id=target_object.template_id)
        object_repo.add(second_source)
        object_repo.add(second_target)
        second = _relationship(
            relationship_id=UUID("11111111-1111-1111-1111-111111111111"),
            relationship_definition_id=definition_id,
            source_object_id=second_source.id,
            target_object_id=second_target.id,
        )
        other = _relationship(
            relationship_id=UUID("22222222-2222-2222-2222-222222222222"),
            relationship_definition_id=UUID(other_definition.id),
            source_object_id=source_object.id,
            target_object_id=target_object.id,
        )

        repo.add(second)
        repo.add(other)
        repo.add(first)

        assert repo.list_by_definition(definition_id) == (first, second)
    finally:
        session.close()
        engine.dispose()


def test_list_incident_to_objects_matches_outgoing_incoming_internal_and_self_once(
    tmp_path: Path,
) -> None:
    repo, _definition_repo, object_repo, template_repo, session, engine = _repo(
        tmp_path,
        "runtime_relationship_list_incident.sqlite3",
    )
    try:
        definition_id, subtree_source, subtree_child = _seed_definition_and_objects(
            template_repo,
            object_repo,
            session,
        )
        external_template = _template(name="external")
        unrelated_template = _template(name="unrelated")
        template_repo.add(external_template)
        template_repo.add(unrelated_template)
        template_repo.add_version(
            ObjectTemplateVersion(
                template_id=external_template.id,
                version=1,
                status=ObjectTemplateVersionStatus.DRAFT,
                properties=(),
            )
        )
        template_repo.add_version(
            ObjectTemplateVersion(
                template_id=unrelated_template.id,
                version=1,
                status=ObjectTemplateVersionStatus.DRAFT,
                properties=(),
            )
        )
        incoming_definition = _relationship_definition_row(
            source_template_id=external_template.id,
            target_template_id=subtree_source.template_id,
        )
        internal_definition = _relationship_definition_row(
            source_template_id=subtree_source.template_id,
            target_template_id=subtree_source.template_id,
        )
        self_link_definition = _relationship_definition_row(
            source_template_id=subtree_source.template_id,
            target_template_id=subtree_source.template_id,
            forward_name="connects_to",
            reverse_name="connects_to",
        )
        unrelated_definition = _relationship_definition_row(
            source_template_id=unrelated_template.id,
            target_template_id=unrelated_template.id,
            forward_name="connects_to",
            reverse_name="connects_to",
        )
        session.add_all(
            (
                incoming_definition,
                internal_definition,
                self_link_definition,
                unrelated_definition,
            )
        )
        session.flush()
        external = _object(template_id=external_template.id)
        unrelated_a = _object(template_id=unrelated_template.id)
        unrelated_b = _object(template_id=unrelated_template.id)
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
            relationship_definition_id=UUID(self_link_definition.id),
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
            session.add(
                RelationshipRow(
                    id=str(relationship.id),
                    relationship_definition_id=str(relationship.relationship_definition_id),
                    source_object_id=str(relationship.source_object_id),
                    target_object_id=str(relationship.target_object_id),
                )
            )
        session.flush()

        assert repo.list_incident_to_objects({subtree_source.id, subtree_child.id}) == (
            outgoing,
            incoming,
            internal,
            self_link,
        )
    finally:
        session.close()
        engine.dispose()


def test_delete_existing_relationship(tmp_path: Path) -> None:
    repo, _definition_repo, object_repo, template_repo, session, engine = _repo(
        tmp_path,
        "runtime_relationship_delete.sqlite3",
    )
    try:
        definition_id, source_object, target_object = _seed_definition_and_objects(
            template_repo,
            object_repo,
            session,
        )
        relationship = _relationship(
            relationship_definition_id=definition_id,
            source_object_id=source_object.id,
            target_object_id=target_object.id,
        )
        repo.add(relationship)

        repo.delete(relationship.id)

        assert repo.get(relationship.id) is None
    finally:
        session.close()
        engine.dispose()


def test_delete_missing_relationship_raises_not_found(tmp_path: Path) -> None:
    repo, _definition_repo, _object_repo, _template_repo, session, engine = _repo(
        tmp_path,
        "runtime_relationship_delete_missing.sqlite3",
    )
    try:
        with pytest.raises(RelationshipNotFound):
            repo.delete(uuid4())
    finally:
        session.close()
        engine.dispose()


def test_invalid_stored_row_raises_persistence_error(tmp_path: Path) -> None:
    repo, _definition_repo, object_repo, template_repo, session, engine = _repo(
        tmp_path,
        "runtime_relationship_invalid_row.sqlite3",
    )
    try:
        definition_id, source_object, target_object = _seed_definition_and_objects(
            template_repo,
            object_repo,
            session,
        )
        session.execute(
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
        session.commit()

        with pytest.raises(RelationshipPersistenceError):
            repo.list()
    finally:
        session.close()
        engine.dispose()


def test_missing_relationship_definition_fk_is_persistence_error(tmp_path: Path) -> None:
    repo, _definition_repo, object_repo, template_repo, session, engine = _repo(
        tmp_path,
        "runtime_relationship_missing_definition_fk.sqlite3",
    )
    try:
        source_template = _template(name="source")
        target_template = _template(name="target")
        template_repo.add(source_template)
        template_repo.add(target_template)
        template_repo.add_version(
            ObjectTemplateVersion(
                template_id=source_template.id,
                version=1,
                status=ObjectTemplateVersionStatus.DRAFT,
                properties=(),
            )
        )
        template_repo.add_version(
            ObjectTemplateVersion(
                template_id=target_template.id,
                version=1,
                status=ObjectTemplateVersionStatus.DRAFT,
                properties=(),
            )
        )
        source_object = _object(template_id=source_template.id)
        target_object = _object(template_id=target_template.id)
        object_repo.add(source_object)
        object_repo.add(target_object)
        session.flush()
        relationship = _relationship(
            relationship_definition_id=uuid4(),
            source_object_id=source_object.id,
            target_object_id=target_object.id,
        )

        with pytest.raises(RelationshipPersistenceError):
            repo.add(relationship)
    finally:
        session.close()
        engine.dispose()


def test_missing_source_object_fk_is_persistence_error(tmp_path: Path) -> None:
    repo, _definition_repo, object_repo, template_repo, session, engine = _repo(
        tmp_path,
        "runtime_relationship_missing_source_fk.sqlite3",
    )
    try:
        definition_id, _source_object, target_object = _seed_definition_and_objects(
            template_repo,
            object_repo,
            session,
        )
        relationship = _relationship(
            relationship_definition_id=definition_id,
            source_object_id=uuid4(),
            target_object_id=target_object.id,
        )

        with pytest.raises(RelationshipPersistenceError):
            repo.add(relationship)
    finally:
        session.close()
        engine.dispose()


def test_missing_target_object_fk_is_persistence_error(tmp_path: Path) -> None:
    repo, _definition_repo, object_repo, template_repo, session, engine = _repo(
        tmp_path,
        "runtime_relationship_missing_target_fk.sqlite3",
    )
    try:
        definition_id, source_object, _target_object = _seed_definition_and_objects(
            template_repo,
            object_repo,
            session,
        )
        relationship = _relationship(
            relationship_definition_id=definition_id,
            source_object_id=source_object.id,
            target_object_id=uuid4(),
        )

        with pytest.raises(RelationshipPersistenceError):
            repo.add(relationship)
    finally:
        session.close()
        engine.dispose()
