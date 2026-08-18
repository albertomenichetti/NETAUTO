"""Deterministic real-PostgreSQL RelationshipDefinition scenarios."""

import asyncio
from uuid import UUID

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.ext.asyncio import AsyncConnection

import netauto.application.relationshipdefinitions as relationshipdefinition_application
import netauto.persistence.locking as locking_persistence
from netauto.application.objecttemplates import ObjectTemplateService
from netauto.application.relationshipdefinitions import RelationshipDefinitionService
from netauto.domain.relationships import (
    RelationshipDefinition,
    RelationshipDefinitionVersion,
    RelationshipPerspective,
    ResolutionRename,
)
from netauto.failures import ApplicationFailure, FailureClass
from netauto.persistence.gates import AdvisoryGate, acquire_advisory_gate
from netauto.persistence.locking import RowLockClass, RowLockMode
from netauto.persistence.objecttemplates import ObjectTemplateStore
from netauto.persistence.relationships import RelationshipDefinitionStore
from netauto.persistence.uow import UnitOfWorkFactory
from tests.support.pg_harness import wait_for_blocker
from tests.support.semantic_concurrency import (
    ObservedUnitOfWorkFactory,
    PhaseCut,
    SemanticActors,
    blocked_race,
    install_lock_plan_cut,
    semantic_actors,
)


def _definition_services(
    actors: SemanticActors,
) -> tuple[RelationshipDefinitionService, RelationshipDefinitionService]:
    return (
        RelationshipDefinitionService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        ),
        RelationshipDefinitionService(
            ObservedUnitOfWorkFactory(actors.t2_engine, actors.tracker, "T2")
        ),
    )


def _definition_reader(actors: SemanticActors) -> RelationshipDefinitionService:
    return RelationshipDefinitionService(UnitOfWorkFactory(actors.t1_engine))


def _template_reader(actors: SemanticActors) -> ObjectTemplateService:
    return ObjectTemplateService(UnitOfWorkFactory(actors.t1_engine))


async def _template(actors: SemanticActors, name: str) -> UUID:
    created = await _template_reader(actors).create(
        "relationship_concurrency", name, False, None, None, None, (), ()
    )
    return created.object_template.id


async def _non_symmetric(
    service: RelationshipDefinitionService,
    first_template_id: UUID,
    second_template_id: UUID,
    first_name: str,
    second_name: str,
) -> RelationshipDefinition:
    created = await service.create_non_symmetric(
        (
            RelationshipPerspective(first_template_id, first_name),
            RelationshipPerspective(second_template_id, second_name),
        )
    )
    return created.relationship_definition


async def _symmetric(
    service: RelationshipDefinitionService,
    template_ids: tuple[UUID, UUID],
    name: str,
) -> RelationshipDefinition:
    created = await service.create_symmetric(template_ids, name)
    return created.relationship_definition


def _failure_code(value: object) -> str | None:
    return value.code if isinstance(value, ApplicationFailure) else None


def _gate_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    cut = PhaseCut()
    original = locking_persistence.acquire_advisory_gate

    async def intercepted(connection: AsyncConnection, gate: AdvisoryGate) -> None:
        await original(connection, gate)
        task = asyncio.current_task()
        if task is not None and task.get_name() == "T1":
            cut.reached.set()
            await cut.release.wait()

    monkeypatch.setattr(locking_persistence, "acquire_advisory_gate", intercepted)
    return cut


def _definition_owner_cut(
    monkeypatch: pytest.MonkeyPatch, *, delete: bool = False
) -> PhaseCut:
    return install_lock_plan_cut(
        monkeypatch,
        relationshipdefinition_application,
        RowLockClass.RELATIONSHIP_DEFINITION_HEADER,
        RowLockMode.U if delete else RowLockMode.KS,
    )


def _definition_insert_cut(
    monkeypatch: pytest.MonkeyPatch, *, fail_after_release: bool = False
) -> PhaseCut:
    cut = PhaseCut()
    original = RelationshipDefinitionStore.insert

    async def intercepted(
        store: RelationshipDefinitionStore,
        value: RelationshipDefinition,
        version: RelationshipDefinitionVersion,
    ) -> None:
        await original(store, value, version)
        task = asyncio.current_task()
        if task is not None and task.get_name() == "T1":
            cut.reached.set()
            await cut.release.wait()
            if fail_after_release:
                raise ApplicationFailure(
                    FailureClass.INTERNAL_FAILURE,
                    "internal_error",
                    "forced rollback after complete candidate write",
                )

    monkeypatch.setattr(RelationshipDefinitionStore, "insert", intercepted)
    return cut


def _lineage_delete_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    cut = PhaseCut()
    original = ObjectTemplateStore.delete_lineage

    async def intercepted(store: ObjectTemplateStore, template_id: UUID) -> None:
        await original(store, template_id)
        task = asyncio.current_task()
        if task is not None and task.get_name() == "T1":
            cut.reached.set()
            await cut.release.wait()

    monkeypatch.setattr(ObjectTemplateStore, "delete_lineage", intercepted)
    return cut


def _renames(
    value: RelationshipDefinition, first_name: str, second_name: str
) -> tuple[ResolutionRename, ResolutionRename]:
    first, second = value.resolutions
    return (
        ResolutionRename(first.id, first_name),
        ResolutionRename(second.id, second_name),
    )


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_gate_04a_and_gate_06a_equivalent_create_reads_fresh_set(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "GATE-04A-06A-RD-EQUIV") as actors:
        first_template_id = await _template(actors, "gate04a_first")
        second_template_id = await _template(actors, "gate04a_second")
        first, second = _definition_services(actors)
        cut = _gate_cut(monkeypatch)
        winner, loser = await blocked_race(
            actors,
            cut,
            lambda: _non_symmetric(
                first,
                first_template_id,
                second_template_id,
                "hosts",
                "hosted_by",
            ),
            lambda: _non_symmetric(
                second,
                second_template_id,
                first_template_id,
                "hosted_by",
                "hosts",
            ),
        )
        assert isinstance(winner, RelationshipDefinition)
        assert _failure_code(loser) == "relationship_definition_equivalent"
        page = await _definition_reader(actors).list_definitions(cursor=None, limit=100)
        assert [item.id for item in page.items] == [winner.id]


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_gate_04b_conflicting_create_commits_only_one_candidate(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "GATE-04B-RD-CONFLICT") as actors:
        first_template_id = await _template(actors, "gate04b_first")
        second_template_id = await _template(actors, "gate04b_second")
        first, second = _definition_services(actors)
        cut = _gate_cut(monkeypatch)
        winner, loser = await blocked_race(
            actors,
            cut,
            lambda: _non_symmetric(
                first,
                first_template_id,
                second_template_id,
                "links",
                "linked_by",
            ),
            lambda: _symmetric(
                second, (first_template_id, second_template_id), "links"
            ),
        )
        assert isinstance(winner, RelationshipDefinition)
        assert _failure_code(loser) == "relationship_definition_conflict"
        page = await _definition_reader(actors).list_definitions(cursor=None, limit=100)
        assert len(page.items) == 1


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_gate_05a_create_and_rename_preserve_conflict_free_set(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "GATE-05A-CREATE-RENAME") as actors:
        first_template_id = await _template(actors, "gate05a_first")
        second_template_id = await _template(actors, "gate05a_second")
        reader = _definition_reader(actors)
        existing = await _non_symmetric(
            reader,
            first_template_id,
            second_template_id,
            "old_name",
            "old_reverse",
        )
        first, second = _definition_services(actors)
        cut = _gate_cut(monkeypatch)
        created, renamed = await blocked_race(
            actors,
            cut,
            lambda: _symmetric(
                first, (first_template_id, second_template_id), "shared_name"
            ),
            lambda: second.rename_non_symmetric(
                existing.id, _renames(existing, "shared_name", "other_reverse")
            ),
        )
        assert isinstance(created, RelationshipDefinition)
        assert _failure_code(renamed) == "relationship_definition_conflict"
        current = await reader.get(existing.id)
        assert {item.name for item in current.resolutions} == {
            "old_name",
            "old_reverse",
        }


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_gate_05b_different_definition_renames_serialize_globally(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "GATE-05B-RENAME-RENAME") as actors:
        first_template_id = await _template(actors, "gate05b_first")
        second_template_id = await _template(actors, "gate05b_second")
        reader = _definition_reader(actors)
        first_definition = await _non_symmetric(
            reader,
            first_template_id,
            second_template_id,
            "first_old",
            "first_reverse",
        )
        second_definition = await _symmetric(
            reader, (first_template_id, second_template_id), "second_old"
        )
        first, second = _definition_services(actors)
        cut = _gate_cut(monkeypatch)
        winner, loser = await blocked_race(
            actors,
            cut,
            lambda: first.rename_non_symmetric(
                first_definition.id,
                _renames(first_definition, "shared_name", "first_other"),
            ),
            lambda: second.rename_symmetric(second_definition.id, "shared_name"),
        )
        assert isinstance(winner, RelationshipDefinition)
        assert _failure_code(loser) == "relationship_definition_conflict"
        current = await reader.get(second_definition.id)
        assert {item.name for item in current.resolutions} == {"second_old"}


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_same_definition_rename_serializes_on_gate_before_header(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "GATE-05-SAME-RD-OWNER") as actors:
        first_template_id = await _template(actors, "same_owner_first")
        second_template_id = await _template(actors, "same_owner_second")
        reader = _definition_reader(actors)
        definition = await _non_symmetric(
            reader,
            first_template_id,
            second_template_id,
            "old_first",
            "old_second",
        )
        first, second = _definition_services(actors)
        cut = _gate_cut(monkeypatch)
        outcomes = await blocked_race(
            actors,
            cut,
            lambda: first.rename_non_symmetric(
                definition.id, _renames(definition, "middle_first", "middle_second")
            ),
            lambda: second.rename_non_symmetric(
                definition.id, _renames(definition, "final_first", "final_second")
            ),
        )
        assert all(isinstance(item, RelationshipDefinition) for item in outcomes)
        current = await reader.get(definition.id)
        assert {item.name for item in current.resolutions} == {
            "final_first",
            "final_second",
        }


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_17_rename_then_delete_share_definition_lifetime_owner(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-17-RENAME-DELETE") as actors:
        template_id = await _template(actors, "row17")
        reader = _definition_reader(actors)
        definition = await _symmetric(reader, (template_id, template_id), "old")
        first, second = _definition_services(actors)
        cut = _definition_owner_cut(monkeypatch)
        renamed, deleted = await blocked_race(
            actors,
            cut,
            lambda: first.rename_symmetric(definition.id, "new"),
            lambda: second.delete(definition.id),
        )
        assert isinstance(renamed, RelationshipDefinition)
        assert deleted is None
        with pytest.raises(ApplicationFailure) as caught:
            await reader.get(definition.id)
        assert caught.value.code == "resource_not_found"


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_17_delete_then_rename_observes_absent_definition(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-17-DELETE-RENAME") as actors:
        template_id = await _template(actors, "row17_reverse")
        reader = _definition_reader(actors)
        definition = await _symmetric(reader, (template_id, template_id), "old")
        first, second = _definition_services(actors)
        cut = _definition_owner_cut(monkeypatch, delete=True)
        deleted, renamed = await blocked_race(
            actors,
            cut,
            lambda: first.delete(definition.id),
            lambda: second.rename_symmetric(definition.id, "new"),
        )
        assert deleted is None
        assert _failure_code(renamed) == "resource_not_found"


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_ref_01_definition_create_then_lineage_delete_uses_fk_lifetime(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "REF-01-RD-FIRST") as actors:
        template_id = await _template(actors, "ref01_rd_first")
        first, _ = _definition_services(actors)
        second_template = ObjectTemplateService(
            ObservedUnitOfWorkFactory(actors.t2_engine, actors.tracker, "T2")
        )
        cut = _definition_insert_cut(monkeypatch)
        created, deleted = await blocked_race(
            actors,
            cut,
            lambda: _symmetric(first, (template_id, template_id), "reference"),
            lambda: second_template.delete_lineage(template_id),
        )
        assert isinstance(created, RelationshipDefinition)
        assert _failure_code(deleted) == "delete_blocked"


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_ref_01_lineage_delete_then_definition_create_fails_reference(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "REF-01-OT-FIRST") as actors:
        template_id = await _template(actors, "ref01_ot_first")
        first_template = ObjectTemplateService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        )
        _, second = _definition_services(actors)
        cut = _lineage_delete_cut(monkeypatch)
        deleted, created = await blocked_race(
            actors,
            cut,
            lambda: first_template.delete_lineage(template_id),
            lambda: _symmetric(second, (template_id, template_id), "lost_reference"),
        )
        assert deleted is None
        assert _failure_code(created) == "referenced_resource_not_found"
        assert isinstance(created, ApplicationFailure)
        assert created.details == {
            "resource_type": "object_template",
            "id": str(template_id),
        }


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_gate_06b_delete_commits_while_candidate_waits_then_unblocks_it(
    migrated_database_engine: Engine,
    test_database_url: str,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "GATE-06B-DELETE-BLOCKER") as actors:
        template_id = await _template(actors, "gate06b")
        reader = _definition_reader(actors)
        blocker = await _symmetric(
            reader, (template_id, template_id), "available_after_delete"
        )
        _, candidate_service = _definition_services(actors)
        actors.tracker.reset()

        async with actors.t1_engine.connect() as holder:
            transaction = await holder.begin()
            await acquire_advisory_gate(
                holder, AdvisoryGate.RELATIONSHIP_DEFINITION_CONFLICT_GATE
            )
            holder_pid = int(await holder.scalar(text("SELECT pg_backend_pid()")))
            candidate_task = asyncio.create_task(
                _symmetric(
                    candidate_service,
                    (template_id, template_id),
                    "available_after_delete",
                ),
                name="T2",
            )
            await actors.tracker.ready["T2"].wait()
            candidate_pid = actors.tracker.pids["T2"]
            blockers = await wait_for_blocker(
                actors.observer, candidate_pid, holder_pid
            )
            assert holder_pid in blockers
            async with asyncio.timeout(5):
                await reader.delete(blocker.id)
            assert not candidate_task.done()
            await transaction.commit()
            async with asyncio.timeout(5):
                created = await candidate_task

        assert isinstance(created, RelationshipDefinition)
        page = await reader.list_definitions(cursor=None, limit=100)
        assert [item.id for item in page.items] == [created.id]


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_unrelated_creates_still_serialize_on_global_gate(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "REALIZE-12-GLOBAL-GATE") as actors:
        first_template_id = await _template(actors, "global_first")
        second_template_id = await _template(actors, "global_second")
        first, second = _definition_services(actors)
        cut = _gate_cut(monkeypatch)
        outcomes = await blocked_race(
            actors,
            cut,
            lambda: _symmetric(
                first, (first_template_id, first_template_id), "first_name"
            ),
            lambda: _symmetric(
                second, (second_template_id, second_template_id), "second_name"
            ),
        )
        assert all(isinstance(item, RelationshipDefinition) for item in outcomes)


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_gate_rollback_releases_waiter_and_leaves_no_partial_candidate(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "REALIZE-12-GATE-ROLLBACK") as actors:
        template_id = await _template(actors, "gate_rollback")
        first, second = _definition_services(actors)
        cut = _definition_insert_cut(monkeypatch, fail_after_release=True)
        failed, winner = await blocked_race(
            actors,
            cut,
            lambda: _symmetric(first, (template_id, template_id), "rollback_name"),
            lambda: _symmetric(second, (template_id, template_id), "rollback_name"),
        )
        assert _failure_code(failed) == "internal_error"
        assert isinstance(winner, RelationshipDefinition)
        page = await _definition_reader(actors).list_definitions(cursor=None, limit=100)
        assert [item.id for item in page.items] == [winner.id]


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_certified_set_read_does_not_lock_unrelated_definition_rows(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "REALIZE-12-NO-FANOUT") as actors:
        first_template_id = await _template(actors, "fanout_first")
        second_template_id = await _template(actors, "fanout_second")
        reader = _definition_reader(actors)
        unrelated = await _symmetric(
            reader, (first_template_id, first_template_id), "existing_name"
        )
        first, _ = _definition_services(actors)
        cut = _definition_insert_cut(monkeypatch)
        create_task = asyncio.create_task(
            _symmetric(
                first, (second_template_id, second_template_id), "candidate_name"
            ),
            name="T1",
        )
        await cut.reached.wait()
        async with actors.t2_engine.connect() as connection:
            async with connection.begin():
                async with asyncio.timeout(5):
                    assert await RelationshipDefinitionStore(connection).lock_no_key(
                        unrelated.id
                    )
        cut.release.set()
        async with asyncio.timeout(5):
            assert isinstance(await create_task, RelationshipDefinition)


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_atomic_04c_rename_rollback_and_symmetric_two_row_update(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ATOMIC-04C-RD-RENAME") as actors:
        first_template_id = await _template(actors, "atomic_first")
        second_template_id = await _template(actors, "atomic_second")
        reader = _definition_reader(actors)
        non_symmetric = await _non_symmetric(
            reader,
            first_template_id,
            second_template_id,
            "before_first",
            "before_second",
        )
        original = RelationshipDefinitionStore.update_names

        async def fail_after_update(
            store: RelationshipDefinitionStore, value: RelationshipDefinition
        ) -> None:
            await original(store, value)
            raise ApplicationFailure(
                FailureClass.INTERNAL_FAILURE,
                "internal_error",
                "forced rollback after complete rename",
            )

        with monkeypatch.context() as context:
            context.setattr(
                RelationshipDefinitionStore, "update_names", fail_after_update
            )
            with pytest.raises(ApplicationFailure) as caught:
                await reader.rename_non_symmetric(
                    non_symmetric.id,
                    _renames(non_symmetric, "after_first", "after_second"),
                )
            assert caught.value.code == "internal_error"
        unchanged = await reader.get(non_symmetric.id)
        assert {item.name for item in unchanged.resolutions} == {
            "before_first",
            "before_second",
        }

        symmetric = await _symmetric(
            reader, (first_template_id, second_template_id), "symmetric_before"
        )
        renamed = await reader.rename_symmetric(symmetric.id, "symmetric_after")
        assert len(renamed.resolutions) == 2
        assert {item.name for item in renamed.resolutions} == {"symmetric_after"}
