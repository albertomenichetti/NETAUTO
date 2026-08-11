from __future__ import annotations

import sqlite3
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import event
from sqlalchemy.engine import Engine, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from netauto.application.object import ObjectApplicationService
from netauto.application.relationship import RelationshipApplicationService
from netauto.core.datatype import (
    DataType,
    DataTypeFactory,
    DataTypeVersion,
    DataTypeVersioningService,
)
from netauto.core.object import (
    ComponentMembership,
    ComponentMembershipAlreadyExists,
    Object,
    ObjectChange,
    ObjectChangeKind,
    ObjectConcurrentModification,
)
from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateComponent,
    ObjectTemplateProperty,
    ObjectTemplateVersion,
    ObjectTemplateVersionStatus,
)
from netauto.core.relationship import (
    Relationship,
    RelationshipAlreadyExists,
    RelationshipDefinition,
)
from netauto.persistence.sqlalchemy.database import create_schema
from netauto.persistence.sqlalchemy.datatype_repository import SqlAlchemyDataTypeRepository
from netauto.persistence.sqlalchemy.object_change_repository import (
    SqlAlchemyObjectChangeRepository,
)
from netauto.persistence.sqlalchemy.object_repository import SqlAlchemyObjectRepository
from netauto.persistence.sqlalchemy.objecttemplate_repository import (
    SqlAlchemyObjectTemplateRepository,
)
from netauto.persistence.sqlalchemy.relationship_repository import (
    SqlAlchemyRelationshipDefinitionRepository,
    SqlAlchemyRelationshipRepository,
)
from netauto.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork


def _engine(tmp_path: Path, filename: str, *, timeout: float = 0.0) -> Engine:
    engine = create_engine(
        f"sqlite:///{tmp_path / filename}",
        connect_args={
            "check_same_thread": False,
            "timeout": timeout,
        },
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection: sqlite3.Connection, _record: object) -> None:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()

    return engine


def _template(*, name: str, template_id: UUID | None = None) -> ObjectTemplate:
    return ObjectTemplate(
        id=template_id or uuid4(),
        namespace="network",
        name=name,
        description=f"{name} template",
        abstract=False,
    )


def _object(
    *,
    template_id: UUID,
    template_version: int = 1,
    properties: dict[str, object] | None = None,
    object_id: UUID | None = None,
) -> Object:
    return Object(
        id=object_id or uuid4(),
        template_id=template_id,
        template_version=template_version,
        properties=properties or {},
    )


def _property(
    name: str,
    *,
    datatype_id: UUID,
    datatype_version: int,
    required: bool = False,
) -> ObjectTemplateProperty:
    return ObjectTemplateProperty(
        name=name,
        datatype_id=datatype_id,
        datatype_version=datatype_version,
        required=required,
    )


def _component(name: str, *, template_id: UUID) -> ObjectTemplateComponent:
    return ObjectTemplateComponent(name=name, template_id=template_id)


def _membership(parent_object_id: UUID, child_object_id: UUID) -> ComponentMembership:
    return ComponentMembership(
        parent_object_id=parent_object_id,
        slot_name="children",
        child_object_id=child_object_id,
    )


def _relationship_definition(
    *,
    source_template_id: UUID,
    target_template_id: UUID,
) -> RelationshipDefinition:
    return RelationshipDefinition(
        id=uuid4(),
        source_template_id=source_template_id,
        target_template_id=target_template_id,
        forward_name="connects_to",
        reverse_name="connected_from",
    )


def _persist_published_datatype(
    uow: SqlAlchemyUnitOfWork,
    *,
    name: str,
) -> tuple[DataType, DataTypeVersion]:
    datatype, draft = DataTypeFactory().create(
        namespace="network",
        name=name,
        description=f"{name} datatype",
        base_type="core.string",
    )
    published = DataTypeVersioningService().publish(draft)
    uow.datatypes.add(datatype)
    uow.datatypes.add_version(draft)
    uow.datatypes.replace_version(published)
    return datatype, published


def _persist_template_version(
    uow: SqlAlchemyUnitOfWork,
    version: ObjectTemplateVersion,
) -> None:
    draft = ObjectTemplateVersion(
        template_id=version.template_id,
        version=version.version,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=version.parent,
        properties=version.properties,
        components=version.components,
    )
    uow.object_templates.add_version(draft)
    if version.status is not ObjectTemplateVersionStatus.DRAFT:
        uow.object_templates.replace_version(version)


@dataclass
class ScenarioHooks:
    before_object_replace_if_current: Callable[[str, Object, Object], None] | None = None
    before_add_membership: Callable[[str, ComponentMembership], None] | None = None
    before_object_change_add: Callable[[str, ObjectChange], None] | None = None
    before_relationship_add: Callable[[str, Relationship], None] | None = None


class HookedObjectRepository(SqlAlchemyObjectRepository):
    def __init__(self, session: Session, *, role: str, hooks: ScenarioHooks) -> None:
        super().__init__(session)
        self._role = role
        self._hooks = hooks

    def replace_if_current(self, expected: Object, replacement: Object) -> None:
        if self._hooks.before_object_replace_if_current is not None:
            self._hooks.before_object_replace_if_current(
                self._role,
                expected,
                replacement,
            )
        super().replace_if_current(expected, replacement)

    def add_membership(self, membership: ComponentMembership) -> None:
        if self._hooks.before_add_membership is not None:
            self._hooks.before_add_membership(self._role, membership)
        super().add_membership(membership)


class HookedObjectChangeRepository(SqlAlchemyObjectChangeRepository):
    def __init__(self, session: Session, *, role: str, hooks: ScenarioHooks) -> None:
        super().__init__(session)
        self._role = role
        self._hooks = hooks

    def add(self, change: ObjectChange) -> None:
        if self._hooks.before_object_change_add is not None:
            self._hooks.before_object_change_add(self._role, change)
        super().add(change)


class HookedRelationshipRepository(SqlAlchemyRelationshipRepository):
    def __init__(self, session: Session, *, role: str, hooks: ScenarioHooks) -> None:
        super().__init__(session)
        self._role = role
        self._hooks = hooks

    def add(self, relationship: Relationship) -> None:
        if self._hooks.before_relationship_add is not None:
            self._hooks.before_relationship_add(self._role, relationship)
        super().add(relationship)


class HookedSqlAlchemyUnitOfWork(SqlAlchemyUnitOfWork):
    def __init__(
        self,
        session_factory: Callable[[], Session],
        *,
        role: str,
        hooks: ScenarioHooks,
    ) -> None:
        super().__init__(session_factory)
        self._role = role
        self._hooks = hooks

    def _initialize_repositories(self) -> None:
        if self._session is None:
            raise RuntimeError("Unit of work is not active.")
        self.datatypes = SqlAlchemyDataTypeRepository(self._session)
        self.object_changes = HookedObjectChangeRepository(
            self._session,
            role=self._role,
            hooks=self._hooks,
        )
        self.objects = HookedObjectRepository(
            self._session,
            role=self._role,
            hooks=self._hooks,
        )
        self.relationships = HookedRelationshipRepository(
            self._session,
            role=self._role,
            hooks=self._hooks,
        )
        self.relationship_definitions = SqlAlchemyRelationshipDefinitionRepository(self._session)
        self.object_templates = SqlAlchemyObjectTemplateRepository(self._session)


@dataclass
class OperationOutcome:
    value: Any | None = None
    error: BaseException | None = None

    @property
    def succeeded(self) -> bool:
        return self.error is None


def _run_in_thread(
    target: Callable[[], Any],
    *,
    outcome: OperationOutcome,
    completed: threading.Event | None = None,
) -> threading.Thread:
    def runner() -> None:
        try:
            outcome.value = target()
        except BaseException as error:  # pragma: no cover - characterization captures real failures
            outcome.error = error
        finally:
            if completed is not None:
                completed.set()

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    return thread


@dataclass
class OrderedWriteGate:
    first_role: str
    barrier: threading.Barrier = field(default_factory=lambda: threading.Barrier(2))
    first_completed: threading.Event = field(default_factory=threading.Event)

    def wait(self, role: str) -> None:
        self.barrier.wait()
        if role != self.first_role:
            assert self.first_completed.wait(timeout=5.0)


@dataclass
class DeleteAttachGate:
    delete_ready: threading.Event = field(default_factory=threading.Event)
    attach_completed: threading.Event = field(default_factory=threading.Event)

    def before_object_change_add(self, role: str, change: ObjectChange) -> None:
        if role != "delete" or change.kind is not ObjectChangeKind.DELETED:
            return
        self.delete_ready.set()
        assert self.attach_completed.wait(timeout=5.0)

    def before_add_membership(self, role: str, _membership: ComponentMembership) -> None:
        if role != "attach":
            return
        assert self.delete_ready.wait(timeout=5.0)


@dataclass
class DeleteRelationshipGate:
    delete_ready: threading.Event = field(default_factory=threading.Event)
    create_completed: threading.Event = field(default_factory=threading.Event)

    def before_object_change_add(self, role: str, change: ObjectChange) -> None:
        if role != "delete" or change.kind is not ObjectChangeKind.DELETED:
            return
        self.delete_ready.set()
        assert self.create_completed.wait(timeout=5.0)

    def before_relationship_add(self, role: str, _relationship: Relationship) -> None:
        if role != "create":
            return
        assert self.delete_ready.wait(timeout=5.0)


def _make_object_service(
    session_factory: Callable[[], Session],
    *,
    role: str | None = None,
    hooks: ScenarioHooks | None = None,
) -> ObjectApplicationService:
    if role is None or hooks is None:
        return ObjectApplicationService(lambda: SqlAlchemyUnitOfWork(session_factory))
    return ObjectApplicationService(
        lambda: HookedSqlAlchemyUnitOfWork(
            session_factory,
            role=role,
            hooks=hooks,
        )
    )


def _make_relationship_service(
    session_factory: Callable[[], Session],
    *,
    role: str | None = None,
    hooks: ScenarioHooks | None = None,
) -> RelationshipApplicationService:
    if role is None or hooks is None:
        return RelationshipApplicationService(lambda: SqlAlchemyUnitOfWork(session_factory))
    return RelationshipApplicationService(
        lambda: HookedSqlAlchemyUnitOfWork(
            session_factory,
            role=role,
            hooks=hooks,
        )
    )


def _create_component_fixture(
    session_factory: Callable[[], Session],
) -> tuple[ObjectTemplate, Object, Object, Object]:
    template = _template(name="node")
    with SqlAlchemyUnitOfWork(session_factory) as uow:
        uow.object_templates.add(template)
        _persist_template_version(
            uow,
            ObjectTemplateVersion(
                template_id=template.id,
                version=1,
                status=ObjectTemplateVersionStatus.PUBLISHED,
                components=(_component("children", template_id=template.id),),
            ),
        )
        parent_a = _object(template_id=template.id)
        parent_b = _object(template_id=template.id)
        child = _object(template_id=template.id)
        for object_value in (parent_a, parent_b, child):
            uow.objects.add(object_value)
        uow.commit()
    return template, parent_a, parent_b, child


def _read_memberships(
    session_factory: Callable[[], Session],
    *,
    parent_id: UUID | None = None,
    child_id: UUID | None = None,
) -> tuple[ComponentMembership, ...]:
    with SqlAlchemyUnitOfWork(session_factory) as uow:
        if child_id is not None:
            owner = uow.objects.get_owner(child_id)
            return () if owner is None else (owner,)
        assert parent_id is not None
        return uow.objects.list_components(parent_id)


def _read_object(session_factory: Callable[[], Session], object_id: UUID) -> Object | None:
    with SqlAlchemyUnitOfWork(session_factory) as uow:
        return uow.objects.get(object_id)


def _read_history(
    session_factory: Callable[[], Session],
    object_id: UUID,
) -> tuple[ObjectChange, ...]:
    with SqlAlchemyUnitOfWork(session_factory) as uow:
        return uow.object_changes.list_by_object(object_id)


def _read_relationships(session_factory: Callable[[], Session]) -> tuple[Relationship, ...]:
    with SqlAlchemyUnitOfWork(session_factory) as uow:
        return uow.relationships.list()


def _create_property_fixture(
    session_factory: Callable[[], Session],
) -> tuple[ObjectTemplate, Object]:
    with SqlAlchemyUnitOfWork(session_factory) as uow:
        datatype_a, datatype_a_v1 = _persist_published_datatype(uow, name="prop_a")
        datatype_b, datatype_b_v1 = _persist_published_datatype(uow, name="prop_b")
        template = _template(name="device")
        uow.object_templates.add(template)
        _persist_template_version(
            uow,
            ObjectTemplateVersion(
                template_id=template.id,
                version=1,
                status=ObjectTemplateVersionStatus.PUBLISHED,
                properties=(
                    _property(
                        "a",
                        datatype_id=datatype_a.id,
                        datatype_version=datatype_a_v1.version,
                    ),
                    _property(
                        "b",
                        datatype_id=datatype_b.id,
                        datatype_version=datatype_b_v1.version,
                    ),
                ),
            ),
        )
        object_value = _object(
            template_id=template.id,
            properties={"a": "old-a", "b": "old-b"},
        )
        uow.objects.add(object_value)
        uow.commit()
    return template, object_value


def _create_migration_fixture(
    session_factory: Callable[[], Session],
) -> tuple[ObjectTemplate, Object]:
    with SqlAlchemyUnitOfWork(session_factory) as uow:
        datatype_a, datatype_a_v1 = _persist_published_datatype(uow, name="mig_a")
        datatype_b, datatype_b_v1 = _persist_published_datatype(uow, name="mig_b")
        datatype_c, datatype_c_v1 = _persist_published_datatype(uow, name="mig_c")
        template = _template(name="migratable")
        uow.object_templates.add(template)
        _persist_template_version(
            uow,
            ObjectTemplateVersion(
                template_id=template.id,
                version=1,
                status=ObjectTemplateVersionStatus.PUBLISHED,
                properties=(
                    _property(
                        "a",
                        datatype_id=datatype_a.id,
                        datatype_version=datatype_a_v1.version,
                    ),
                    _property(
                        "b",
                        datatype_id=datatype_b.id,
                        datatype_version=datatype_b_v1.version,
                    ),
                ),
            ),
        )
        _persist_template_version(
            uow,
            ObjectTemplateVersion(
                template_id=template.id,
                version=2,
                status=ObjectTemplateVersionStatus.PUBLISHED,
                properties=(
                    _property(
                        "a",
                        datatype_id=datatype_a.id,
                        datatype_version=datatype_a_v1.version,
                    ),
                    _property(
                        "b",
                        datatype_id=datatype_b.id,
                        datatype_version=datatype_b_v1.version,
                    ),
                    _property(
                        "c",
                        datatype_id=datatype_c.id,
                        datatype_version=datatype_c_v1.version,
                        required=False,
                    ),
                ),
            ),
        )
        object_value = _object(
            template_id=template.id,
            properties={"a": "old-a", "b": "old-b"},
        )
        uow.objects.add(object_value)
        uow.commit()
    return template, object_value


def _create_relationship_fixture(
    session_factory: Callable[[], Session],
) -> tuple[ObjectTemplate, RelationshipDefinition, Object, Object]:
    with SqlAlchemyUnitOfWork(session_factory) as uow:
        template = _template(name="node")
        uow.object_templates.add(template)
        _persist_template_version(
            uow,
            ObjectTemplateVersion(
                template_id=template.id,
                version=1,
                status=ObjectTemplateVersionStatus.PUBLISHED,
            ),
        )
        source = _object(template_id=template.id)
        target = _object(template_id=template.id)
        uow.objects.add(source)
        uow.objects.add(target)
        definition = _relationship_definition(
            source_template_id=template.id,
            target_template_id=template.id,
        )
        uow.relationship_definitions.add(definition)
        uow.commit()
    return template, definition, source, target


def test_characterizes_same_child_competing_owners_race(tmp_path: Path) -> None:
    engine = _engine(tmp_path, "c0_1_same_child.sqlite3")
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    _, parent_a, parent_b, child = _create_component_fixture(session_factory)
    gate = OrderedWriteGate(first_role="attach_a")
    hooks = ScenarioHooks(before_add_membership=lambda role, membership: gate.wait(role))
    service_a = _make_object_service(session_factory, role="attach_a", hooks=hooks)
    service_b = _make_object_service(session_factory, role="attach_b", hooks=hooks)
    outcome_a = OperationOutcome()
    outcome_b = OperationOutcome()

    thread_a = _run_in_thread(
        lambda: service_a.attach_component(
            parent_object_id=parent_a.id,
            slot_name="children",
            child_object_id=child.id,
        ),
        outcome=outcome_a,
        completed=gate.first_completed,
    )
    thread_b = _run_in_thread(
        lambda: service_b.attach_component(
            parent_object_id=parent_b.id,
            slot_name="children",
            child_object_id=child.id,
        ),
        outcome=outcome_b,
    )
    thread_a.join()
    thread_b.join()

    owner_rows = _read_memberships(session_factory, child_id=child.id)
    assert len(owner_rows) == 1
    assert outcome_a.succeeded is True
    assert isinstance(outcome_b.error, ComponentMembershipAlreadyExists)
    assert outcome_a.value == owner_rows[0]
    assert owner_rows[0].child_object_id == child.id

    engine.dispose()


def test_characterizes_reciprocal_attach_cycle_race(tmp_path: Path) -> None:
    engine = _engine(tmp_path, "c0_2_reciprocal_attach.sqlite3")
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    template, parent_a, parent_b, _ = _create_component_fixture(session_factory)
    del template
    gate = OrderedWriteGate(first_role="attach_a")
    hooks = ScenarioHooks(before_add_membership=lambda role, membership: gate.wait(role))
    service_a = _make_object_service(session_factory, role="attach_a", hooks=hooks)
    service_b = _make_object_service(session_factory, role="attach_b", hooks=hooks)
    outcome_a = OperationOutcome()
    outcome_b = OperationOutcome()

    thread_a = _run_in_thread(
        lambda: service_a.attach_component(
            parent_object_id=parent_a.id,
            slot_name="children",
            child_object_id=parent_b.id,
        ),
        outcome=outcome_a,
        completed=gate.first_completed,
    )
    thread_b = _run_in_thread(
        lambda: service_b.attach_component(
            parent_object_id=parent_b.id,
            slot_name="children",
            child_object_id=parent_a.id,
        ),
        outcome=outcome_b,
    )
    thread_a.join()
    thread_b.join()

    owners = (
        _read_memberships(session_factory, child_id=parent_a.id),
        _read_memberships(session_factory, child_id=parent_b.id),
    )
    assert outcome_a.succeeded is True
    assert outcome_b.succeeded is True
    assert owners[0] == (_membership(parent_b.id, parent_a.id),)
    assert owners[1] == (_membership(parent_a.id, parent_b.id),)

    engine.dispose()


def test_characterizes_current_concurrent_object_update_race(tmp_path: Path) -> None:
    engine = _engine(tmp_path, "c0_3_update_update.sqlite3")
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    _, object_value = _create_property_fixture(session_factory)
    gate = OrderedWriteGate(first_role="update_a")
    hooks = ScenarioHooks(
        before_object_replace_if_current=lambda role, expected, replacement: gate.wait(role)
    )
    service_a = _make_object_service(session_factory, role="update_a", hooks=hooks)
    service_b = _make_object_service(session_factory, role="update_b", hooks=hooks)
    outcome_a = OperationOutcome()
    outcome_b = OperationOutcome()

    thread_a = _run_in_thread(
        lambda: service_a.update_object(
            object_id=object_value.id,
            properties={"a": "new-a"},
        ),
        outcome=outcome_a,
        completed=gate.first_completed,
    )
    thread_b = _run_in_thread(
        lambda: service_b.update_object(
            object_id=object_value.id,
            properties={"b": "new-b"},
        ),
        outcome=outcome_b,
    )
    thread_a.join()
    thread_b.join()

    persisted = _read_object(session_factory, object_value.id)
    history = _read_history(session_factory, object_value.id)
    assert persisted is not None
    # C1a regression: one stale writer must lose via optimistic concurrency.
    assert outcome_a.succeeded is True
    assert isinstance(outcome_b.error, ObjectConcurrentModification)
    assert persisted.properties == {"a": "new-a", "b": "old-b"}
    assert [change.kind for change in history] == [ObjectChangeKind.UPDATED]
    assert history[0].before is not None
    assert history[0].after is not None
    assert history[0].before.properties == {"a": "old-a", "b": "old-b"}
    assert history[0].after.properties == {"a": "new-a", "b": "old-b"}

    engine.dispose()


def test_characterizes_current_update_vs_migration_race(tmp_path: Path) -> None:
    engine = _engine(tmp_path, "c0_4_update_migrate.sqlite3")
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    template, object_value = _create_migration_fixture(session_factory)
    gate = OrderedWriteGate(first_role="migrate")
    hooks = ScenarioHooks(
        before_object_replace_if_current=lambda role, expected, replacement: gate.wait(role)
    )
    update_service = _make_object_service(session_factory, role="update", hooks=hooks)
    migrate_service = _make_object_service(session_factory, role="migrate", hooks=hooks)
    outcome_update = OperationOutcome()
    outcome_migrate = OperationOutcome()

    thread_migrate = _run_in_thread(
        lambda: migrate_service.migrate_objects(
            template_id=template.id,
            source_version=1,
            target_version=2,
            property_values={},
        ),
        outcome=outcome_migrate,
        completed=gate.first_completed,
    )
    thread_update = _run_in_thread(
        lambda: update_service.update_object(
            object_id=object_value.id,
            properties={"b": "new-b"},
        ),
        outcome=outcome_update,
    )
    thread_migrate.join()
    thread_update.join()

    persisted = _read_object(session_factory, object_value.id)
    history = _read_history(session_factory, object_value.id)
    assert persisted is not None
    # C1a regression: stale update must conflict after successful migration.
    assert outcome_migrate.succeeded is True
    assert isinstance(outcome_update.error, ObjectConcurrentModification)
    assert persisted.template_version == 2
    assert persisted.properties == {"a": "old-a", "b": "old-b"}
    assert [change.kind for change in history] == [ObjectChangeKind.MIGRATED]
    assert history[0].after is not None
    assert history[0].after.template_version == 2
    assert history[0].after.properties == {"a": "old-a", "b": "old-b"}

    engine.dispose()


def test_migration_cas_conflict_rolls_back_whole_batch(tmp_path: Path) -> None:
    engine = _engine(tmp_path, "c1a_migration_batch_rollback.sqlite3")
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    template, first_seed = _create_migration_fixture(session_factory)
    with SqlAlchemyUnitOfWork(session_factory) as uow:
        second_seed = _object(
            template_id=template.id,
            template_version=1,
            properties={"a": "old-a-2", "b": "old-b-2"},
        )
        uow.objects.add(second_seed)
        uow.commit()

    with SqlAlchemyUnitOfWork(session_factory) as uow:
        candidates = uow.objects.list_by_template_version(template.id, 1)
        first = next(candidate for candidate in candidates if candidate.id == first_seed.id)
        second = next(candidate for candidate in candidates if candidate.id == second_seed.id)

    conflict_triggered = False

    class ConflictOnSecondCasObjectRepository(HookedObjectRepository):
        def __init__(self, session: Session, *, role: str, hooks: ScenarioHooks) -> None:
            super().__init__(session, role=role, hooks=hooks)
            self._cas_count = 0

        def replace_if_current(self, expected: Object, replacement: Object) -> None:
            nonlocal conflict_triggered
            self._cas_count += 1
            if self._cas_count == 2:
                conflict_triggered = True
                raise ObjectConcurrentModification("Object was modified concurrently.")
            super().replace_if_current(expected, replacement)

    class ConflictUow(HookedSqlAlchemyUnitOfWork):
        def _initialize_repositories(self) -> None:
            if self._session is None:
                raise RuntimeError("Unit of work is not active.")
            self.datatypes = SqlAlchemyDataTypeRepository(self._session)
            self.object_changes = HookedObjectChangeRepository(
                self._session,
                role=self._role,
                hooks=self._hooks,
            )
            self.objects = ConflictOnSecondCasObjectRepository(
                self._session,
                role=self._role,
                hooks=self._hooks,
            )
            self.relationships = HookedRelationshipRepository(
                self._session,
                role=self._role,
                hooks=self._hooks,
            )
            self.relationship_definitions = SqlAlchemyRelationshipDefinitionRepository(
                self._session
            )
            self.object_templates = SqlAlchemyObjectTemplateRepository(self._session)

    service = ObjectApplicationService(
        lambda: ConflictUow(session_factory, role="migrate", hooks=ScenarioHooks())
    )

    with pytest.raises(ObjectConcurrentModification):
        service.migrate_objects(
            template_id=template.id,
            source_version=1,
            target_version=2,
            property_values={},
        )

    assert conflict_triggered is True
    persisted_first = _read_object(session_factory, first.id)
    persisted_second = _read_object(session_factory, second.id)
    assert persisted_first is not None
    assert persisted_second is not None
    assert persisted_first.template_version == 1
    assert persisted_second.template_version == 1
    assert _read_history(session_factory, first.id) == ()
    assert _read_history(session_factory, second.id) == ()

    engine.dispose()


def test_characterizes_duplicate_relationship_create_race(tmp_path: Path) -> None:
    engine = _engine(tmp_path, "c0_5_duplicate_relationship.sqlite3")
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    _, definition, source, target = _create_relationship_fixture(session_factory)
    gate = OrderedWriteGate(first_role="create_a")
    hooks = ScenarioHooks(before_relationship_add=lambda role, relationship: gate.wait(role))
    service_a = _make_relationship_service(session_factory, role="create_a", hooks=hooks)
    service_b = _make_relationship_service(session_factory, role="create_b", hooks=hooks)
    outcome_a = OperationOutcome()
    outcome_b = OperationOutcome()

    thread_a = _run_in_thread(
        lambda: service_a.create_relationship(
            relationship_definition_id=definition.id,
            source_object_id=source.id,
            target_object_id=target.id,
        ),
        outcome=outcome_a,
        completed=gate.first_completed,
    )
    thread_b = _run_in_thread(
        lambda: service_b.create_relationship(
            relationship_definition_id=definition.id,
            source_object_id=source.id,
            target_object_id=target.id,
        ),
        outcome=outcome_b,
    )
    thread_a.join()
    thread_b.join()

    relationships = _read_relationships(session_factory)
    assert len(relationships) == 1
    assert outcome_a.succeeded is True
    assert isinstance(outcome_b.error, RelationshipAlreadyExists)
    assert outcome_a.value == relationships[0]

    engine.dispose()


def test_characterizes_delete_vs_attach_race(tmp_path: Path) -> None:
    engine = _engine(tmp_path, "c0_6_delete_attach.sqlite3")
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    template, root, _, child = _create_component_fixture(session_factory)
    del template
    gate = DeleteAttachGate()
    hooks = ScenarioHooks(
        before_object_change_add=gate.before_object_change_add,
        before_add_membership=gate.before_add_membership,
    )
    delete_service = _make_object_service(session_factory, role="delete", hooks=hooks)
    attach_service = _make_object_service(session_factory, role="attach", hooks=hooks)
    delete_outcome = OperationOutcome()
    attach_outcome = OperationOutcome()

    delete_thread = _run_in_thread(
        lambda: delete_service.delete_object(root.id),
        outcome=delete_outcome,
    )
    attach_thread = _run_in_thread(
        lambda: attach_service.attach_component(
            parent_object_id=root.id,
            slot_name="children",
            child_object_id=child.id,
        ),
        outcome=attach_outcome,
        completed=gate.attach_completed,
    )
    delete_thread.join()
    attach_thread.join()

    persisted_root = _read_object(session_factory, root.id)
    persisted_child = _read_object(session_factory, child.id)
    owner = _read_memberships(session_factory, child_id=child.id)
    root_history = _read_history(session_factory, root.id)
    child_history = _read_history(session_factory, child.id)
    # Characterization: attach reports success, delete reports success, the
    # parent disappears, and the newly attached child survives detached.
    assert delete_outcome.succeeded is True
    assert attach_outcome.succeeded is True
    assert persisted_root is None
    assert persisted_child is not None
    assert owner == ()
    assert [change.kind for change in root_history] == [ObjectChangeKind.DELETED]
    assert child_history == ()

    engine.dispose()


def test_characterizes_relationship_create_vs_endpoint_delete_race(tmp_path: Path) -> None:
    engine = _engine(tmp_path, "c0_7_relationship_delete.sqlite3")
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    _, definition, source, target = _create_relationship_fixture(session_factory)
    gate = DeleteRelationshipGate()
    hooks = ScenarioHooks(
        before_object_change_add=gate.before_object_change_add,
        before_relationship_add=gate.before_relationship_add,
    )
    create_service = _make_relationship_service(session_factory, role="create", hooks=hooks)
    delete_service = _make_object_service(session_factory, role="delete", hooks=hooks)
    create_outcome = OperationOutcome()
    delete_outcome = OperationOutcome()

    delete_thread = _run_in_thread(
        lambda: delete_service.delete_object(source.id),
        outcome=delete_outcome,
    )
    create_thread = _run_in_thread(
        lambda: create_service.create_relationship(
            relationship_definition_id=definition.id,
            source_object_id=source.id,
            target_object_id=target.id,
        ),
        outcome=create_outcome,
        completed=gate.create_completed,
    )
    delete_thread.join()
    create_thread.join()

    persisted_source = _read_object(session_factory, source.id)
    relationships = _read_relationships(session_factory)
    assert isinstance(delete_outcome.error, IntegrityError)
    assert create_outcome.succeeded is True
    assert persisted_source is not None
    assert len(relationships) == 1
    assert _read_history(session_factory, source.id) == ()

    engine.dispose()
