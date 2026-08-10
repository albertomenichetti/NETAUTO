from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Engine, inspect
from sqlalchemy.orm import Session, sessionmaker

from netauto.core.objecttemplate import ObjectTemplate
from netauto.core.relationship import (
    RelationshipDefinition,
    RelationshipDefinitionAlreadyExists,
    RelationshipDefinitionNotFound,
)
from netauto.persistence.sqlalchemy.database import create_schema, create_sqlite_engine
from netauto.persistence.sqlalchemy.models import RelationshipDefinitionRow
from netauto.persistence.sqlalchemy.objecttemplate_repository import (
    SqlAlchemyObjectTemplateRepository,
)
from netauto.persistence.sqlalchemy.relationship_repository import (
    SqlAlchemyRelationshipDefinitionRepository,
)


def _repo(
    tmp_path: Path,
    filename: str,
) -> tuple[
    SqlAlchemyRelationshipDefinitionRepository,
    SqlAlchemyObjectTemplateRepository,
    Session,
    Engine,
]:
    engine = create_sqlite_engine(f"sqlite:///{tmp_path / filename}")
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    session = session_factory()
    return (
        SqlAlchemyRelationshipDefinitionRepository(session),
        SqlAlchemyObjectTemplateRepository(session),
        session,
        engine,
    )


def _template(
    *,
    namespace: str = "network",
    name: str = "device",
    description: str | None = "Device template",
    abstract: bool = False,
    template_id: UUID | None = None,
) -> ObjectTemplate:
    return ObjectTemplate(
        id=template_id or uuid4(),
        namespace=namespace,
        name=name,
        description=description,
        abstract=abstract,
    )


def _definition(
    *,
    definition_id: UUID | None = None,
    source_template_id: UUID,
    target_template_id: UUID,
    forward_name: str = "uses",
    reverse_name: str = "is_used_by",
) -> RelationshipDefinition:
    return RelationshipDefinition(
        id=definition_id or uuid4(),
        source_template_id=source_template_id,
        target_template_id=target_template_id,
        forward_name=forward_name,
        reverse_name=reverse_name,
    )


def test_schema_encodes_relationship_definition_invariants(tmp_path: Path) -> None:
    _repo_obj, _template_repo, session, engine = _repo(
        tmp_path,
        "relationship_schema.sqlite3",
    )
    session.close()
    try:
        inspector = inspect(engine)
        pk = inspector.get_pk_constraint("relationship_definitions")
        fks = inspector.get_foreign_keys("relationship_definitions")
        columns = {column["name"] for column in inspector.get_columns("relationship_definitions")}
        unique_constraints = inspector.get_unique_constraints("relationship_definitions")

        assert pk["constrained_columns"] == ["id"]
        assert columns == {
            "id",
            "source_template_id",
            "target_template_id",
            "forward_name",
            "reverse_name",
        }
        assert "source_template_version" not in columns
        assert "target_template_version" not in columns
        assert unique_constraints == []
        assert len(fks) == 2

        source_fk = next(
            fk for fk in fks if fk["constrained_columns"] == ["source_template_id"]
        )
        target_fk = next(
            fk for fk in fks if fk["constrained_columns"] == ["target_template_id"]
        )
        assert source_fk["referred_table"] == "object_templates"
        assert source_fk["referred_columns"] == ["id"]
        assert target_fk["referred_table"] == "object_templates"
        assert target_fk["referred_columns"] == ["id"]
        assert source_fk.get("options", {}).get("ondelete") == "RESTRICT"
        assert target_fk.get("options", {}).get("ondelete") == "RESTRICT"
    finally:
        engine.dispose()


def test_round_trip_persists_canonical_definition_row(tmp_path: Path) -> None:
    repo, template_repo, session, engine = _repo(tmp_path, "relationship_round_trip.sqlite3")
    source = _template(name="source")
    target = _template(name="target")
    definition = _definition(
        source_template_id=source.id,
        target_template_id=target.id,
        forward_name="uses",
        reverse_name="is_used_by",
    )
    try:
        template_repo.add(source)
        template_repo.add(target)

        repo.add(definition)

        assert repo.get(definition.id) == definition
        rows = session.query(RelationshipDefinitionRow).all()
        assert len(rows) == 1
        assert rows[0].id == str(definition.id)
        assert rows[0].source_template_id == str(source.id)
        assert rows[0].target_template_id == str(target.id)
        assert rows[0].forward_name == "uses"
        assert rows[0].reverse_name == "is_used_by"
    finally:
        session.close()
        engine.dispose()


def test_list_is_deterministic_by_uuid_string(tmp_path: Path) -> None:
    repo, template_repo, session, engine = _repo(tmp_path, "relationship_ordering.sqlite3")
    source = _template(name="source")
    target = _template(name="target")
    extra = _template(name="extra")
    low = _definition(
        definition_id=UUID("00000000-0000-0000-0000-000000000001"),
        source_template_id=source.id,
        target_template_id=target.id,
    )
    high = _definition(
        definition_id=UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"),
        source_template_id=target.id,
        target_template_id=extra.id,
    )
    mid = _definition(
        definition_id=UUID("11111111-1111-1111-1111-111111111111"),
        source_template_id=extra.id,
        target_template_id=source.id,
    )
    try:
        for template in (source, target, extra):
            template_repo.add(template)
        repo.add(high)
        repo.add(mid)
        repo.add(low)

        assert repo.list() == (low, mid, high)
    finally:
        session.close()
        engine.dispose()


def test_get_missing_returns_none(tmp_path: Path) -> None:
    repo, _template_repo, session, engine = _repo(tmp_path, "relationship_missing_get.sqlite3")
    try:
        assert repo.get(uuid4()) is None
    finally:
        session.close()
        engine.dispose()


def test_duplicate_primary_key_is_rejected(tmp_path: Path) -> None:
    repo, template_repo, session, engine = _repo(tmp_path, "relationship_dup_pk.sqlite3")
    source = _template(name="source")
    target = _template(name="target")
    definition = _definition(
        definition_id=uuid4(),
        source_template_id=source.id,
        target_template_id=target.id,
    )
    duplicate = _definition(
        definition_id=definition.id,
        source_template_id=target.id,
        target_template_id=source.id,
        forward_name="manages",
        reverse_name="managed_by",
    )
    try:
        template_repo.add(source)
        template_repo.add(target)
        repo.add(definition)

        with pytest.raises(RelationshipDefinitionAlreadyExists):
            repo.add(duplicate)
    finally:
        session.close()
        engine.dispose()


def test_delete_existing_definition(tmp_path: Path) -> None:
    repo, template_repo, session, engine = _repo(tmp_path, "relationship_delete.sqlite3")
    source = _template(name="source")
    target = _template(name="target")
    definition = _definition(
        source_template_id=source.id,
        target_template_id=target.id,
    )
    try:
        template_repo.add(source)
        template_repo.add(target)
        repo.add(definition)

        repo.delete(definition.id)

        assert repo.get(definition.id) is None
        assert repo.list() == ()
    finally:
        session.close()
        engine.dispose()


def test_delete_missing_definition_raises_not_found(tmp_path: Path) -> None:
    repo, _template_repo, session, engine = _repo(
        tmp_path,
        "relationship_delete_missing.sqlite3",
    )
    try:
        with pytest.raises(RelationshipDefinitionNotFound):
            repo.delete(uuid4())
    finally:
        session.close()
        engine.dispose()
