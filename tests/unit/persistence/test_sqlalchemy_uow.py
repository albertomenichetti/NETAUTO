from pathlib import Path
from typing import Callable, cast
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from netauto.core.datatype import (
    Constraint,
    ConstraintName,
    DataTypeAlreadyExists,
    DataTypeFactory,
    DataTypeVersionAlreadyExists,
    DataTypeVersioningService,
)
from netauto.core.object import ComponentMembership, Object
from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateVersion,
    ObjectTemplateVersionStatus,
)
from netauto.core.relationship import Relationship, RelationshipDefinition
from netauto.persistence.sqlalchemy.database import create_schema, create_sqlite_engine
from netauto.persistence.sqlalchemy.datatype_repository import SqlAlchemyDataTypeRepository
from netauto.persistence.sqlalchemy.object_repository import SqlAlchemyObjectRepository
from netauto.persistence.sqlalchemy.objecttemplate_repository import (
    SqlAlchemyObjectTemplateRepository,
)
from netauto.persistence.sqlalchemy.relationship_repository import (
    SqlAlchemyRelationshipDefinitionRepository,
    SqlAlchemyRelationshipRepository,
)
from netauto.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork

DEFAULT_TEMPLATE_ID = UUID("00000000-0000-0000-0000-0000000000ac")


def _uow(tmp_path: Path, filename: str) -> tuple[SqlAlchemyUnitOfWork, Engine]:
    engine = create_sqlite_engine(f"sqlite:///{tmp_path / filename}")
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    seed_session = session_factory()
    try:
        template_repo = SqlAlchemyObjectTemplateRepository(seed_session)
        default_template = ObjectTemplate(
            id=DEFAULT_TEMPLATE_ID,
            namespace="network",
            name="default_object_template",
            description=None,
            abstract=False,
        )
        template_repo.add(default_template)
        template_repo.add_version(
            ObjectTemplateVersion(
                template_id=default_template.id,
                version=1,
                status=ObjectTemplateVersionStatus.DRAFT,
                properties=(),
            )
        )
        seed_session.commit()
    finally:
        seed_session.close()
    return SqlAlchemyUnitOfWork(session_factory), engine


def _object_template(
    *,
    namespace: str = "network",
    name: str = "device",
    description: str | None = "Network device template",
    abstract: bool = False,
) -> ObjectTemplate:
    return ObjectTemplate(
        id=uuid4(),
        namespace=namespace,
        name=name,
        description=description,
        abstract=abstract,
    )


def _object_template_version(template_id: UUID) -> ObjectTemplateVersion:
    return ObjectTemplateVersion(
        template_id=template_id,
        version=1,
        status=ObjectTemplateVersionStatus.DRAFT,
        properties=(),
    )


def _relationship_definition(
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


class _SpySession:
    def __init__(self) -> None:
        self.rollback_called = False
        self.close_called = False
        self.commit_called = False
        self._in_transaction = True

    def commit(self) -> None:
        self.commit_called = True
        self._in_transaction = False

    def rollback(self) -> None:
        self.rollback_called = True
        self._in_transaction = False

    def close(self) -> None:
        self.close_called = True

    def in_transaction(self) -> bool:
        return self._in_transaction


def test_clean_exit_after_explicit_commit_does_not_call_rollback() -> None:
    spy_session = _SpySession()
    session_factory = cast("Callable[[], Session]", lambda: spy_session)
    uow = SqlAlchemyUnitOfWork(session_factory)

    with uow:
        uow.commit()

    assert spy_session.commit_called is True
    assert spy_session.rollback_called is False
    assert spy_session.close_called is True


def test_both_repositories_are_available_in_one_unit_of_work(tmp_path: Path) -> None:
    uow, engine = _uow(tmp_path, "both_repositories.sqlite3")
    try:
        with uow:
            assert isinstance(uow.datatypes, SqlAlchemyDataTypeRepository)
            assert isinstance(uow.object_templates, SqlAlchemyObjectTemplateRepository)
            assert isinstance(uow.objects, SqlAlchemyObjectRepository)
            assert isinstance(uow.relationships, SqlAlchemyRelationshipRepository)
            assert isinstance(
                uow.relationship_definitions,
                SqlAlchemyRelationshipDefinitionRepository,
            )
    finally:
        engine.dispose()


def test_unit_of_work_commit_persists(tmp_path: Path) -> None:
    datatype, version = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description="Network hostname",
        base_type="core.string",
        constraints=(Constraint(name=ConstraintName.MIN_LENGTH, value=1),),
    )
    uow, engine = _uow(tmp_path, "commit.sqlite3")
    try:
        with uow:
            uow.datatypes.add(datatype)
            uow.datatypes.add_version(version)
            uow.commit()

        session_factory = sessionmaker(engine, expire_on_commit=False)
        session = session_factory()
        try:
            repo = SqlAlchemyDataTypeRepository(session)
            assert repo.get(datatype.id) == datatype
            assert repo.get_version(datatype.id, 1) == version
        finally:
            session.close()
    finally:
        engine.dispose()


def test_unit_of_work_commit_persists_datatypes_and_object_templates(tmp_path: Path) -> None:
    datatype, datatype_version = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description="Network hostname",
        base_type="core.string",
        constraints=(Constraint(name=ConstraintName.MIN_LENGTH, value=1),),
    )
    template = _object_template()
    template_version = _object_template_version(template.id)
    uow, engine = _uow(tmp_path, "shared_commit.sqlite3")
    try:
        with uow:
            uow.datatypes.add(datatype)
            uow.datatypes.add_version(datatype_version)
            uow.object_templates.add(template)
            uow.object_templates.add_version(template_version)
            uow.commit()

        session_factory = sessionmaker(engine, expire_on_commit=False)
        session = session_factory()
        try:
            datatype_repo = SqlAlchemyDataTypeRepository(session)
            template_repo = SqlAlchemyObjectTemplateRepository(session)
            assert datatype_repo.get(datatype.id) == datatype
            assert datatype_repo.get_version(datatype.id, 1) == datatype_version
            assert template_repo.get(template.id) == template
            assert template_repo.get_version(template.id, 1) == template_version
        finally:
            session.close()
    finally:
        engine.dispose()


def test_unit_of_work_rollback_does_not_persist(tmp_path: Path) -> None:
    datatype, version = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description="Network hostname",
        base_type="core.string",
        constraints=(Constraint(name=ConstraintName.MIN_LENGTH, value=1),),
    )
    uow, engine = _uow(tmp_path, "rollback.sqlite3")
    try:
        try:
            with uow:
                uow.datatypes.add(datatype)
                uow.datatypes.add_version(version)
                raise RuntimeError("abort")
        except RuntimeError:
            pass

        session_factory = sessionmaker(engine, expire_on_commit=False)
        session = session_factory()
        try:
            repo = SqlAlchemyDataTypeRepository(session)
            assert repo.get(datatype.id) is None
            assert repo.get_version(datatype.id, 1) is None
        finally:
            session.close()
    finally:
        engine.dispose()


def test_unit_of_work_rollback_does_not_persist_datatypes_and_object_templates(
    tmp_path: Path,
) -> None:
    datatype, datatype_version = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description="Network hostname",
        base_type="core.string",
        constraints=(Constraint(name=ConstraintName.MIN_LENGTH, value=1),),
    )
    template = _object_template()
    template_version = _object_template_version(template.id)
    uow, engine = _uow(tmp_path, "shared_rollback.sqlite3")
    try:
        try:
            with uow:
                uow.datatypes.add(datatype)
                uow.datatypes.add_version(datatype_version)
                uow.object_templates.add(template)
                uow.object_templates.add_version(template_version)
                raise RuntimeError("abort")
        except RuntimeError:
            pass

        session_factory = sessionmaker(engine, expire_on_commit=False)
        session = session_factory()
        try:
            datatype_repo = SqlAlchemyDataTypeRepository(session)
            template_repo = SqlAlchemyObjectTemplateRepository(session)
            assert datatype_repo.get(datatype.id) is None
            assert datatype_repo.get_version(datatype.id, 1) is None
            assert template_repo.get(template.id) is None
            assert template_repo.get_version(template.id, 1) is None
        finally:
            session.close()
    finally:
        engine.dispose()


def test_context_exit_without_commit_does_not_persist(tmp_path: Path) -> None:
    datatype, version = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description="Network hostname",
        base_type="core.string",
        constraints=(Constraint(name=ConstraintName.MIN_LENGTH, value=1),),
    )
    uow, engine = _uow(tmp_path, "no_commit.sqlite3")
    try:
        with uow:
            uow.datatypes.add(datatype)
            uow.datatypes.add_version(version)

        session_factory = sessionmaker(engine, expire_on_commit=False)
        session = session_factory()
        try:
            repo = SqlAlchemyDataTypeRepository(session)
            assert repo.get(datatype.id) is None
            assert repo.get_version(datatype.id, 1) is None
        finally:
            session.close()
    finally:
        engine.dispose()


def test_atomic_datatype_and_v1_creation(tmp_path: Path) -> None:
    datatype, version = DataTypeFactory().create(
        namespace="network",
        name="vlan_id",
        description="VLAN identifier",
        base_type="core.integer",
        constraints=(
            Constraint(name=ConstraintName.MINIMUM, value=1),
            Constraint(name=ConstraintName.MAXIMUM, value=4094),
        ),
    )
    uow, engine = _uow(tmp_path, "atomic.sqlite3")
    try:
        with uow:
            uow.datatypes.add(datatype)
            uow.datatypes.add_version(version)
            uow.commit()

        session_factory = sessionmaker(engine, expire_on_commit=False)
        session = session_factory()
        try:
            repo = SqlAlchemyDataTypeRepository(session)
            assert repo.get(datatype.id) == datatype
            assert repo.get_version(datatype.id, 1) == version
        finally:
            session.close()
    finally:
        engine.dispose()


def test_real_sqlite_file_survives_engine_and_session_recreation(tmp_path: Path) -> None:
    database_path = tmp_path / "durable.sqlite3"
    datatype, version = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description="Network hostname",
        base_type="core.string",
        constraints=(
            Constraint(name=ConstraintName.MIN_LENGTH, value=1),
            Constraint(name=ConstraintName.MAX_LENGTH, value=253),
        ),
    )

    first_engine = create_sqlite_engine(f"sqlite:///{database_path}")
    create_schema(first_engine)
    first_session_factory = sessionmaker(first_engine, expire_on_commit=False)
    seed_session = first_session_factory()
    try:
        template_repo = SqlAlchemyObjectTemplateRepository(seed_session)
        default_template = ObjectTemplate(
            id=DEFAULT_TEMPLATE_ID,
            namespace="network",
            name="default_object_template",
            description=None,
            abstract=False,
        )
        template_repo.add(default_template)
        template_repo.add_version(
            ObjectTemplateVersion(
                template_id=default_template.id,
                version=1,
                status=ObjectTemplateVersionStatus.DRAFT,
                properties=(),
            )
        )
        seed_session.commit()
    finally:
        seed_session.close()
    first_uow = SqlAlchemyUnitOfWork(first_session_factory)
    with first_uow:
        first_uow.datatypes.add(datatype)
        first_uow.datatypes.add_version(version)
        first_uow.commit()
    first_engine.dispose()

    second_engine = create_sqlite_engine(f"sqlite:///{database_path}")
    second_session_factory = sessionmaker(second_engine, expire_on_commit=False)
    session = second_session_factory()
    try:
        repo = SqlAlchemyDataTypeRepository(session)
        assert repo.get(datatype.id) == datatype
        assert repo.get_version(datatype.id, 1) == version
    finally:
        session.close()
        second_engine.dispose()


def test_unit_of_work_commit_persists_objects_and_memberships(tmp_path: Path) -> None:
    parent = _object()
    child = _object()
    membership = _membership(parent_object_id=parent.id, child_object_id=child.id)
    uow, engine = _uow(tmp_path, "objects_commit.sqlite3")
    try:
        with uow:
            uow.objects.add(parent)
            uow.objects.add(child)
            uow.objects.add_membership(membership)
            uow.commit()

        session_factory = sessionmaker(engine, expire_on_commit=False)
        session = session_factory()
        try:
            repo = SqlAlchemyObjectRepository(session)
            assert repo.get(parent.id) == parent
            assert repo.get(child.id) == child
            assert repo.get_owner(child.id) == membership
        finally:
            session.close()
    finally:
        engine.dispose()


def test_unit_of_work_context_exit_without_commit_rolls_back_objects_and_memberships(
    tmp_path: Path,
) -> None:
    parent = _object()
    child = _object()
    membership = _membership(parent_object_id=parent.id, child_object_id=child.id)
    uow, engine = _uow(tmp_path, "objects_no_commit.sqlite3")
    try:
        with uow:
            uow.objects.add(parent)
            uow.objects.add(child)
            uow.objects.add_membership(membership)

        session_factory = sessionmaker(engine, expire_on_commit=False)
        session = session_factory()
        try:
            repo = SqlAlchemyObjectRepository(session)
            assert repo.get(parent.id) is None
            assert repo.get(child.id) is None
            assert repo.get_owner(child.id) is None
        finally:
            session.close()
    finally:
        engine.dispose()


def test_unit_of_work_exception_triggered_rollback_removes_object_and_membership_work(
    tmp_path: Path,
) -> None:
    parent = _object()
    child = _object()
    membership = _membership(parent_object_id=parent.id, child_object_id=child.id)
    uow, engine = _uow(tmp_path, "objects_rollback.sqlite3")
    try:
        try:
            with uow:
                uow.objects.add(parent)
                uow.objects.add(child)
                uow.objects.add_membership(membership)
                raise RuntimeError("abort")
        except RuntimeError:
            pass

        session_factory = sessionmaker(engine, expire_on_commit=False)
        session = session_factory()
        try:
            repo = SqlAlchemyObjectRepository(session)
            assert repo.get(parent.id) is None
            assert repo.get(child.id) is None
            assert repo.get_owner(child.id) is None
        finally:
            session.close()
    finally:
        engine.dispose()


def test_transaction_can_include_object_template_and_object_state_atomically(
    tmp_path: Path,
) -> None:
    template = _object_template()
    template_version = _object_template_version(template.id)
    object_value = _object(template_id=template.id, template_version=template_version.version)
    uow, engine = _uow(tmp_path, "template_and_object.sqlite3")
    try:
        with uow:
            uow.object_templates.add(template)
            uow.object_templates.add_version(template_version)
            uow.objects.add(object_value)
            uow.commit()

        session_factory = sessionmaker(engine, expire_on_commit=False)
        session = session_factory()
        try:
            template_repo = SqlAlchemyObjectTemplateRepository(session)
            object_repo = SqlAlchemyObjectRepository(session)
            assert template_repo.get(template.id) == template
            assert template_repo.get_version(template.id, 1) == template_version
            assert object_repo.get(object_value.id) == object_value
        finally:
            session.close()
    finally:
        engine.dispose()


def test_real_sqlite_file_reconstruction_preserves_objects_and_memberships(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "object_durable.sqlite3"
    parent = _object()
    child = _object()
    membership = _membership(parent_object_id=parent.id, child_object_id=child.id)

    first_engine = create_sqlite_engine(f"sqlite:///{database_path}")
    create_schema(first_engine)
    first_session_factory = sessionmaker(first_engine, expire_on_commit=False)
    seed_session = first_session_factory()
    try:
        template_repo = SqlAlchemyObjectTemplateRepository(seed_session)
        default_template = ObjectTemplate(
            id=DEFAULT_TEMPLATE_ID,
            namespace="network",
            name="default_object_template",
            description=None,
            abstract=False,
        )
        template_repo.add(default_template)
        template_repo.add_version(
            ObjectTemplateVersion(
                template_id=default_template.id,
                version=1,
                status=ObjectTemplateVersionStatus.DRAFT,
                properties=(),
            )
        )
        seed_session.commit()
    finally:
        seed_session.close()
    first_uow = SqlAlchemyUnitOfWork(first_session_factory)
    with first_uow:
        first_uow.objects.add(parent)
        first_uow.objects.add(child)
        first_uow.objects.add_membership(membership)
        first_uow.commit()
    first_engine.dispose()

    second_engine = create_sqlite_engine(f"sqlite:///{database_path}")
    second_session_factory = sessionmaker(second_engine, expire_on_commit=False)
    session = second_session_factory()
    try:
        repo = SqlAlchemyObjectRepository(session)
        assert repo.get(parent.id) == parent
        assert repo.get(child.id) == child
        assert repo.get_owner(child.id) == membership
    finally:
        session.close()
        second_engine.dispose()


def test_unit_of_work_commit_persists_relationship_definitions(tmp_path: Path) -> None:
    source = _object_template(name="source")
    target = _object_template(name="target")
    definition = _relationship_definition(
        source_template_id=source.id,
        target_template_id=target.id,
    )
    uow, engine = _uow(tmp_path, "relationship_definitions_commit.sqlite3")
    try:
        with uow:
            uow.object_templates.add(source)
            uow.object_templates.add(target)
            uow.relationship_definitions.add(definition)
            uow.commit()

        session_factory = sessionmaker(engine, expire_on_commit=False)
        session = session_factory()
        try:
            repo = SqlAlchemyRelationshipDefinitionRepository(session)
            assert repo.get(definition.id) == definition
        finally:
            session.close()
    finally:
        engine.dispose()


def test_unit_of_work_commit_persists_runtime_relationships(tmp_path: Path) -> None:
    source_template = _object_template(name="source")
    target_template = _object_template(name="target")
    relationship_definition = _relationship_definition(
        source_template_id=source_template.id,
        target_template_id=target_template.id,
    )
    source_object = _object(template_id=source_template.id)
    target_object = _object(template_id=target_template.id)
    relationship = _relationship(
        relationship_definition_id=relationship_definition.id,
        source_object_id=source_object.id,
        target_object_id=target_object.id,
    )
    uow, engine = _uow(tmp_path, "runtime_relationship_commit.sqlite3")
    try:
        with uow:
            uow.object_templates.add(source_template)
            uow.object_templates.add(target_template)
            uow.object_templates.add_version(_object_template_version(source_template.id))
            uow.object_templates.add_version(_object_template_version(target_template.id))
            uow.relationship_definitions.add(relationship_definition)
            uow.objects.add(source_object)
            uow.objects.add(target_object)
            uow.relationships.add(relationship)
            uow.commit()

        session_factory = sessionmaker(engine, expire_on_commit=False)
        session = session_factory()
        try:
            relationship_repo = SqlAlchemyRelationshipRepository(session)
            assert relationship_repo.get(relationship.id) == relationship
        finally:
            session.close()
    finally:
        engine.dispose()


def test_unit_of_work_rollback_does_not_persist_relationship_definitions(
    tmp_path: Path,
) -> None:
    source = _object_template(name="source")
    target = _object_template(name="target")
    definition = _relationship_definition(
        source_template_id=source.id,
        target_template_id=target.id,
    )
    uow, engine = _uow(tmp_path, "relationship_definitions_rollback.sqlite3")
    try:
        try:
            with uow:
                uow.object_templates.add(source)
                uow.object_templates.add(target)
                uow.relationship_definitions.add(definition)
                raise RuntimeError("abort")
        except RuntimeError:
            pass

        session_factory = sessionmaker(engine, expire_on_commit=False)
        session = session_factory()
        try:
            repo = SqlAlchemyRelationshipDefinitionRepository(session)
            assert repo.get(definition.id) is None
        finally:
            session.close()
    finally:
        engine.dispose()


def test_replace_version_persists_lifecycle_replacements(tmp_path: Path) -> None:
    datatype, draft = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description="Network hostname",
        base_type="core.string",
        constraints=(Constraint(name=ConstraintName.MIN_LENGTH, value=1),),
    )
    service = DataTypeVersioningService()
    published = service.publish(draft)
    deprecated = service.deprecate(published)
    uow, engine = _uow(tmp_path, "replace.sqlite3")
    try:
        with uow:
            uow.datatypes.add(datatype)
            uow.datatypes.add_version(draft)
            uow.commit()
        with uow:
            uow.datatypes.replace_version(published)
            uow.commit()
        with uow:
            uow.datatypes.replace_version(deprecated)
            uow.commit()

        session_factory = sessionmaker(engine, expire_on_commit=False)
        session = session_factory()
        try:
            repo = SqlAlchemyDataTypeRepository(session)
            loaded = repo.get_version(datatype.id, 1)
            assert loaded == deprecated
        finally:
            session.close()
    finally:
        engine.dispose()


def test_failed_flush_rolls_back_whole_unit_of_work(tmp_path: Path) -> None:
    first = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description="Network hostname",
        base_type="core.string",
    )[0]
    duplicate = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description="Duplicate hostname",
        base_type="core.string",
    )[0]
    uow, engine = _uow(tmp_path, "failed_flush.sqlite3")
    try:
        with pytest.raises(DataTypeAlreadyExists) as error_info:
            with uow:
                uow.datatypes.add(first)
                uow.datatypes.add(duplicate)
                uow.commit()

        assert error_info.value.__cause__ is not None

        session_factory = sessionmaker(engine, expire_on_commit=False)
        session = session_factory()
        try:
            repo = SqlAlchemyDataTypeRepository(session)
            assert repo.get(first.id) is None
            assert repo.get_by_name("network", "hostname") is None
            assert repo.get(duplicate.id) is None
        finally:
            session.close()
    finally:
        engine.dispose()


def test_caught_repository_error_inside_uow_still_rolls_back_on_exit(tmp_path: Path) -> None:
    first = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description="Network hostname",
        base_type="core.string",
    )[0]
    duplicate = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description="Duplicate hostname",
        base_type="core.string",
    )[0]
    uow, engine = _uow(tmp_path, "caught_error.sqlite3")
    try:
        with uow:
            uow.datatypes.add(first)
            with pytest.raises(DataTypeAlreadyExists):
                uow.datatypes.add(duplicate)

        session_factory = sessionmaker(engine, expire_on_commit=False)
        session = session_factory()
        try:
            repo = SqlAlchemyDataTypeRepository(session)
            assert repo.get(first.id) is None
            assert repo.get_by_name("network", "hostname") is None
            assert repo.get(duplicate.id) is None
        finally:
            session.close()
    finally:
        engine.dispose()


def test_commit_then_uncommitted_work_only_persists_first_commit(tmp_path: Path) -> None:
    first = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description="Network hostname",
        base_type="core.string",
    )[0]
    second = DataTypeFactory().create(
        namespace="network",
        name="device_status",
        description="Device status",
        base_type="core.string",
    )[0]
    uow, engine = _uow(tmp_path, "commit_then_uncommitted.sqlite3")
    try:
        with uow:
            uow.datatypes.add(first)
            uow.commit()
            uow.datatypes.add(second)

        session_factory = sessionmaker(engine, expire_on_commit=False)
        session = session_factory()
        try:
            repo = SqlAlchemyDataTypeRepository(session)
            assert repo.get(first.id) == first
            assert repo.get(second.id) is None
            assert repo.get_by_name("network", "hostname") == first
            assert repo.get_by_name("network", "device_status") is None
        finally:
            session.close()
    finally:
        engine.dispose()


def test_two_explicit_commits_persist_both_transactions(tmp_path: Path) -> None:
    first = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description="Network hostname",
        base_type="core.string",
    )[0]
    second = DataTypeFactory().create(
        namespace="network",
        name="device_status",
        description="Device status",
        base_type="core.string",
    )[0]
    uow, engine = _uow(tmp_path, "two_commits.sqlite3")
    try:
        with uow:
            uow.datatypes.add(first)
            uow.commit()
            uow.datatypes.add(second)
            uow.commit()

        session_factory = sessionmaker(engine, expire_on_commit=False)
        session = session_factory()
        try:
            repo = SqlAlchemyDataTypeRepository(session)
            assert repo.get(first.id) == first
            assert repo.get(second.id) == second
        finally:
            session.close()
    finally:
        engine.dispose()


def test_duplicate_version_error_preserves_cause(tmp_path: Path) -> None:
    datatype, version = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description="Network hostname",
        base_type="core.string",
    )
    uow, engine = _uow(tmp_path, "duplicate_version.sqlite3")
    try:
        with pytest.raises(DataTypeVersionAlreadyExists) as error_info:
            with uow:
                uow.datatypes.add(datatype)
                uow.datatypes.add_version(version)
                uow.datatypes.add_version(version)
                uow.commit()

        assert error_info.value.__cause__ is not None
    finally:
        engine.dispose()
