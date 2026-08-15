"""Deterministic real-PostgreSQL runtime Relationship scenarios."""

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass, field
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Engine, func, select

from netauto.application.objects import ObjectService
from netauto.application.objecttemplates import ObjectTemplateService, PropertyCandidate
from netauto.application.relationshipdefinitions import RelationshipDefinitionService
from netauto.application.relationships import (
    RelationshipCreateResult,
    RelationshipService,
)
from netauto.domain.objects import DataChangeKind, DataChangeOperation, Object
from netauto.domain.objecttemplates import ValueMode
from netauto.domain.primitives import JsonValue
from netauto.domain.relationships import (
    Relationship,
    RelationshipDefinition,
    RelationshipLifecycleView,
    RelationshipPerspective,
    ResolutionRename,
    derive_runtime_closure,
)
from netauto.failures import ApplicationFailure, FailureClass
from netauto.persistence.metadata import (
    object_lifecycle_events,
    relationships,
    runtime_relationship_resolutions,
)
from netauto.persistence.objects import ObjectStore
from netauto.persistence.relationships import (
    RelationshipDefinitionDeleteReferenceError,
    RelationshipDefinitionStore,
    RuntimeRelationshipStore,
)
from netauto.persistence.uow import UnitOfWorkFactory
from tests.support.pg_harness import PgWorker, WorkerRole, wait_for_blocker
from tests.support.semantic_concurrency import (
    ObservedUnitOfWorkFactory,
    PhaseCut,
    SemanticActors,
    blocked_race,
    capture,
    progress_race,
    semantic_actors,
)


@dataclass(frozen=True, slots=True)
class RelationshipSeed:
    definition: RelationshipDefinition
    first_object: Object
    second_object: Object

    @property
    def first_resolution_id(self) -> UUID:
        return next(
            item.id
            for item in self.definition.resolutions
            if item.from_template_id == self.first_object.template_id
        )

    @property
    def second_resolution_id(self) -> UUID:
        return next(
            item.id
            for item in self.definition.resolutions
            if item.from_template_id == self.second_object.template_id
        )


@dataclass(slots=True)
class ExactReadCut:
    reached: asyncio.Event = field(default_factory=asyncio.Event)
    release: asyncio.Event = field(default_factory=asyncio.Event)
    calls: int = 0


def _relationship_services(
    actors: SemanticActors,
) -> tuple[RelationshipService, RelationshipService]:
    return (
        RelationshipService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        ),
        RelationshipService(
            ObservedUnitOfWorkFactory(actors.t2_engine, actors.tracker, "T2")
        ),
    )


def _reader(actors: SemanticActors) -> RelationshipService:
    return RelationshipService(UnitOfWorkFactory(actors.t1_engine))


async def _seed(
    actors: SemanticActors,
    prefix: str,
    *,
    first_name: str = "contains",
    second_name: str = "contained_by",
) -> RelationshipSeed:
    factory = UnitOfWorkFactory(actors.t1_engine)
    templates = ObjectTemplateService(factory)
    first_template = await templates.create(
        "relationship_concurrency",
        f"{prefix}_first",
        False,
        None,
        None,
        None,
        (),
        (),
    )
    second_template = await templates.create(
        "relationship_concurrency",
        f"{prefix}_second",
        False,
        None,
        None,
        None,
        (),
        (),
    )
    await templates.publish(first_template.object_template.id, 1, 1)
    await templates.publish(second_template.object_template.id, 1, 1)
    objects = ObjectService(factory)
    first_object = await objects.create(
        first_template.object_template.id, 1, f"{prefix}-first", {}
    )
    second_object = await objects.create(
        second_template.object_template.id, 1, f"{prefix}-second", {}
    )
    definition = await RelationshipDefinitionService(factory).create_non_symmetric(
        (
            RelationshipPerspective(first_template.object_template.id, first_name),
            RelationshipPerspective(second_template.object_template.id, second_name),
        )
    )
    return RelationshipSeed(definition, first_object, second_object)


async def _symmetric_seed(
    actors: SemanticActors, prefix: str, *, inheritance_overlap: bool = False
) -> RelationshipSeed:
    factory = UnitOfWorkFactory(actors.t1_engine)
    templates = ObjectTemplateService(factory)
    root = await templates.create(
        "relationship_concurrency",
        f"{prefix}_root",
        False,
        None,
        None,
        None,
        (),
        (),
    )
    await templates.publish(root.object_template.id, 1, 1)
    endpoint_template_id = root.object_template.id
    definition_templates = (endpoint_template_id, endpoint_template_id)
    if inheritance_overlap:
        child = await templates.create(
            "relationship_concurrency",
            f"{prefix}_child",
            False,
            None,
            root.object_template.id,
            None,
            (),
            (),
        )
        await templates.publish(child.object_template.id, 1, 1)
        endpoint_template_id = child.object_template.id
        definition_templates = (root.object_template.id, endpoint_template_id)
    objects = ObjectService(factory)
    first_object = await objects.create(endpoint_template_id, 1, f"{prefix}-first", {})
    second_object = await objects.create(
        endpoint_template_id, 1, f"{prefix}-second", {}
    )
    definition = await RelationshipDefinitionService(factory).create_symmetric(
        definition_templates, f"{prefix}_link"
    )
    return RelationshipSeed(definition, first_object, second_object)


async def _mutable_object_seed(actors: SemanticActors, prefix: str) -> RelationshipSeed:
    factory = UnitOfWorkFactory(actors.t1_engine)
    datatype = await actors.t1.create(
        "relationship_concurrency", f"{prefix}_value", "core.integer", None, {}
    )
    await actors.t1.publish(datatype.datatype.id, 1, 1)
    templates = ObjectTemplateService(factory)
    value_property = PropertyCandidate(
        "value", 1, datatype.datatype.id, 1, ValueMode.SCALAR, False
    )
    first_template = await templates.create(
        "relationship_concurrency",
        f"{prefix}_mutable",
        False,
        None,
        None,
        None,
        (value_property,),
        (),
    )
    await templates.publish(first_template.object_template.id, 1, 1)
    await templates.create_next(first_template.object_template.id, 1)
    added_property = PropertyCandidate(
        "added", 2, datatype.datatype.id, 1, ValueMode.SCALAR, False
    )
    await templates.revise(
        first_template.object_template.id,
        2,
        1,
        None,
        (value_property, added_property),
        (),
    )
    await templates.publish(first_template.object_template.id, 2, 2)
    second_template = await templates.create(
        "relationship_concurrency",
        f"{prefix}_peer",
        False,
        None,
        None,
        None,
        (),
        (),
    )
    await templates.publish(second_template.object_template.id, 1, 1)
    objects = ObjectService(factory)
    first_object = await objects.create(
        first_template.object_template.id, 1, f"{prefix}-mutable", {"value": 0}
    )
    second_object = await objects.create(
        second_template.object_template.id, 1, f"{prefix}-peer", {}
    )
    definition = await RelationshipDefinitionService(factory).create_non_symmetric(
        (
            RelationshipPerspective(
                first_template.object_template.id, "contains_mutable"
            ),
            RelationshipPerspective(second_template.object_template.id, "in_mutable"),
        )
    )
    return RelationshipSeed(definition, first_object, second_object)


def _insert_cut(monkeypatch: pytest.MonkeyPatch) -> tuple[PhaseCut, list[Relationship]]:
    cut = PhaseCut()
    candidates: list[Relationship] = []
    original = RuntimeRelationshipStore.insert

    async def intercepted(store: RuntimeRelationshipStore, value: Relationship) -> None:
        candidates.append(value)
        await original(store, value)
        task = asyncio.current_task()
        if task is not None and task.get_name() == "T1":
            cut.reached.set()
            await cut.release.wait()

    monkeypatch.setattr(RuntimeRelationshipStore, "insert", intercepted)
    return cut, candidates


def _object_update_cut(
    monkeypatch: pytest.MonkeyPatch, *, schema_change: bool
) -> PhaseCut:
    cut = PhaseCut()
    if schema_change:
        original_schema = ObjectStore.update_schema

        async def intercepted_schema(
            store: ObjectStore,
            object_id: UUID,
            template_version: int,
            properties: dict[str, JsonValue],
        ) -> None:
            await original_schema(store, object_id, template_version, properties)
            task = asyncio.current_task()
            if task is not None and task.get_name() == "T1":
                cut.reached.set()
                await cut.release.wait()

        monkeypatch.setattr(ObjectStore, "update_schema", intercepted_schema)
    else:
        original_properties = ObjectStore.update_properties

        async def intercepted_properties(
            store: ObjectStore, object_id: UUID, properties: dict[str, JsonValue]
        ) -> None:
            await original_properties(store, object_id, properties)
            task = asyncio.current_task()
            if task is not None and task.get_name() == "T1":
                cut.reached.set()
                await cut.release.wait()

        monkeypatch.setattr(ObjectStore, "update_properties", intercepted_properties)
    return cut


def _delete_owner_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    cut = PhaseCut()
    original = RuntimeRelationshipStore.lock_update

    async def intercepted(
        store: RuntimeRelationshipStore, relationship_id: UUID
    ) -> bool:
        result = await original(store, relationship_id)
        task = asyncio.current_task()
        if task is not None and task.get_name() == "T1":
            cut.reached.set()
            await cut.release.wait()
        return result

    monkeypatch.setattr(RuntimeRelationshipStore, "lock_update", intercepted)
    return cut


def _definition_delete_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    cut = PhaseCut()
    original = RelationshipDefinitionStore.delete

    async def intercepted(
        store: RelationshipDefinitionStore, definition_id: UUID
    ) -> None:
        await original(store, definition_id)
        task = asyncio.current_task()
        if task is not None and task.get_name() == "T1":
            cut.reached.set()
            await cut.release.wait()

    monkeypatch.setattr(RelationshipDefinitionStore, "delete", intercepted)
    return cut


def _object_delete_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    cut = PhaseCut()
    original = ObjectStore.delete

    async def intercepted(store: ObjectStore, object_id: UUID) -> None:
        await original(store, object_id)
        task = asyncio.current_task()
        if task is not None and task.get_name() == "T1":
            cut.reached.set()
            await cut.release.wait()

    monkeypatch.setattr(ObjectStore, "delete", intercepted)
    return cut


def _metadata_cut(monkeypatch: pytest.MonkeyPatch) -> tuple[PhaseCut, list[int]]:
    cut = PhaseCut()
    observations: list[int] = []
    original = RuntimeRelationshipStore.lifecycle_views

    async def intercepted(store: RuntimeRelationshipStore, relationship_id: UUID):
        value = await original(store, relationship_id)
        observations.append(len(value))
        task = asyncio.current_task()
        if task is not None and task.get_name() == "T1":
            cut.reached.set()
            await cut.release.wait()
        return value

    monkeypatch.setattr(RuntimeRelationshipStore, "lifecycle_views", intercepted)
    return cut, observations


def _failure_code(value: object) -> str | None:
    return value.code if isinstance(value, ApplicationFailure) else None


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_arb_05_reciprocal_create_uses_pk_and_converges(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ARB-05A-REL") as actors:
        seed = await _seed(actors, "arb05")
        first, second = _relationship_services(actors)
        cut, candidates = _insert_cut(monkeypatch)
        winner, loser = await blocked_race(
            actors,
            cut,
            lambda: first.create(
                seed.first_resolution_id,
                seed.first_object.id,
                seed.second_object.id,
            ),
            lambda: second.create(
                seed.second_resolution_id,
                seed.second_object.id,
                seed.first_object.id,
            ),
        )
        assert isinstance(winner, RelationshipCreateResult)
        assert isinstance(loser, RelationshipCreateResult)
        assert winner.created is True
        assert loser.created is False
        assert winner.relationship.id == loser.relationship.id
        assert len(candidates) == 2
        assert candidates[0].id != candidates[1].id
        async with actors.t1_engine.connect() as connection:
            assert (
                await connection.scalar(select(func.count()).select_from(relationships))
                == 1
            )
            assert (
                await connection.scalar(
                    select(func.count()).select_from(runtime_relationship_resolutions)
                )
                == 2
            )
            assert (
                await connection.scalar(
                    select(func.count())
                    .select_from(object_lifecycle_events)
                    .where(
                        object_lifecycle_events.c.relationship_id
                        == winner.relationship.id,
                        object_lifecycle_events.c.kind == "RELATIONSHIP_CREATED",
                    )
                )
                == 2
            )


@pytest.mark.postgresql
@pytest.mark.concurrency
@pytest.mark.parametrize("inheritance_overlap", [False, True])
async def test_arb_05_symmetric_inverse_and_overlap_create_converge(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
    *,
    inheritance_overlap: bool,
) -> None:
    del migrated_database_engine
    variant = "C" if inheritance_overlap else "B"
    async with semantic_actors(test_database_url, f"ARB-05{variant}-REL") as actors:
        seed = await _symmetric_seed(
            actors, f"arb05{variant.lower()}", inheritance_overlap=inheritance_overlap
        )
        first_resolution = seed.definition.resolutions[0]
        second_resolution = seed.definition.resolutions[-1]
        first, second = _relationship_services(actors)
        cut, _ = _insert_cut(monkeypatch)
        winner, loser = await blocked_race(
            actors,
            cut,
            lambda: first.create(
                first_resolution.id,
                seed.first_object.id,
                seed.second_object.id,
            ),
            lambda: second.create(
                second_resolution.id,
                seed.second_object.id,
                seed.first_object.id,
            ),
        )
        assert isinstance(winner, RelationshipCreateResult)
        assert isinstance(loser, RelationshipCreateResult)
        assert winner.created is True
        assert loser.created is False
        assert winner.relationship.id == loser.relationship.id
        expected_runtime_rows = 4 if inheritance_overlap else 2
        async with actors.t1_engine.connect() as connection:
            assert (
                await connection.scalar(
                    select(func.count()).select_from(runtime_relationship_resolutions)
                )
                == expected_runtime_rows
            )
            assert (
                await connection.scalar(
                    select(func.count())
                    .select_from(object_lifecycle_events)
                    .where(
                        object_lifecycle_events.c.relationship_id
                        == winner.relationship.id,
                        object_lifecycle_events.c.kind == "RELATIONSHIP_CREATED",
                    )
                )
                == 2
            )


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_arb_06_same_id_delete_locks_and_emits_one_event_set(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ARB-06-REL") as actors:
        seed = await _seed(actors, "arb06")
        initial = await _reader(actors).create(
            seed.first_resolution_id,
            seed.first_object.id,
            seed.second_object.id,
        )
        first, second = _relationship_services(actors)
        cut = _delete_owner_cut(monkeypatch)
        outcomes = await blocked_race(
            actors,
            cut,
            lambda: first.delete(initial.relationship.id),
            lambda: second.delete(initial.relationship.id),
        )
        assert outcomes == [None, None]
        async with actors.t1_engine.connect() as connection:
            assert (
                await connection.scalar(
                    select(func.count())
                    .select_from(object_lifecycle_events)
                    .where(
                        object_lifecycle_events.c.relationship_id
                        == initial.relationship.id,
                        object_lifecycle_events.c.kind == "RELATIONSHIP_DELETED",
                    )
                )
                == 2
            )


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_arb_07a_late_delete_cannot_remove_recreated_fact(
    migrated_database_engine: Engine,
    test_database_url: str,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ARB-07A-REL") as actors:
        seed = await _seed(actors, "arb07a")
        service = _reader(actors)
        original = await service.create(
            seed.first_resolution_id,
            seed.first_object.id,
            seed.second_object.id,
        )
        await service.delete(original.relationship.id)
        recreated = await service.create(
            seed.first_resolution_id,
            seed.first_object.id,
            seed.second_object.id,
        )
        assert recreated.created is True
        assert recreated.relationship.id != original.relationship.id

        await service.delete(original.relationship.id)

        assert (
            await service.get(recreated.relationship.id)
        ).id == recreated.relationship.id


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_arb_07b_winner_disappears_before_fresh_convergence_read(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ARB-07B-REL") as actors:
        seed = await _seed(actors, "arb07b")
        first, second = _relationship_services(actors)
        insert_cut, candidates = _insert_cut(monkeypatch)
        exact_cut = ExactReadCut()
        original_exact = RuntimeRelationshipStore.exact_relationship_id

        async def intercepted_exact(
            store: RuntimeRelationshipStore,
            resolution_id: UUID,
            from_object_id: UUID,
            to_object_id: UUID,
        ) -> UUID | None:
            task = asyncio.current_task()
            if task is not None and task.get_name() == "T2":
                exact_cut.calls += 1
                if exact_cut.calls == 2:
                    exact_cut.reached.set()
                    await exact_cut.release.wait()
            return await original_exact(
                store, resolution_id, from_object_id, to_object_id
            )

        monkeypatch.setattr(
            RuntimeRelationshipStore, "exact_relationship_id", intercepted_exact
        )
        actors.tracker.reset()
        winner_task = asyncio.create_task(
            capture(
                lambda: first.create(
                    seed.first_resolution_id,
                    seed.first_object.id,
                    seed.second_object.id,
                )
            ),
            name="T1",
        )
        await insert_cut.reached.wait()
        loser_task = asyncio.create_task(
            capture(
                lambda: second.create(
                    seed.second_resolution_id,
                    seed.second_object.id,
                    seed.first_object.id,
                )
            ),
            name="T2",
        )
        await actors.tracker.ready["T2"].wait()
        assert actors.tracker.pids["T1"] in await wait_for_blocker(
            actors.observer,
            actors.tracker.pids["T2"],
            actors.tracker.pids["T1"],
        )
        insert_cut.release.set()
        winner = await winner_task
        assert isinstance(winner, RelationshipCreateResult)
        await exact_cut.reached.wait()
        await _reader(actors).delete(winner.relationship.id)
        exact_cut.release.set()
        loser = await loser_task
        assert isinstance(loser, RelationshipCreateResult)
        assert loser.created is True
        assert loser.relationship.id != winner.relationship.id
        assert len(candidates) == 3
        assert candidates[1].id not in {
            winner.relationship.id,
            loser.relationship.id,
        }
        async with actors.t1_engine.connect() as connection:
            current_ids = set(await connection.scalars(select(relationships.c.id)))
        assert current_ids == {loser.relationship.id}


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_ref_04_create_reference_first_blocks_definition_delete(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "REF-04-REFERENCE-FIRST") as actors:
        seed = await _seed(actors, "ref04a")
        relationship, _ = _relationship_services(actors)
        definitions = RelationshipDefinitionService(
            ObservedUnitOfWorkFactory(actors.t2_engine, actors.tracker, "T2")
        )
        cut, _ = _insert_cut(monkeypatch)
        created, deleted = await blocked_race(
            actors,
            cut,
            lambda: relationship.create(
                seed.first_resolution_id,
                seed.first_object.id,
                seed.second_object.id,
            ),
            lambda: definitions.delete(seed.definition.id),
        )
        assert isinstance(created, RelationshipCreateResult)
        assert _failure_code(deleted) == "delete_blocked"


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_ref_04_definition_delete_first_rejects_relationship_create(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "REF-04-DELETE-FIRST") as actors:
        seed = await _seed(actors, "ref04b")
        definitions = RelationshipDefinitionService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        )
        relationship = RelationshipService(
            ObservedUnitOfWorkFactory(actors.t2_engine, actors.tracker, "T2")
        )
        cut = _definition_delete_cut(monkeypatch)
        deleted, created = await blocked_race(
            actors,
            cut,
            lambda: definitions.delete(seed.definition.id),
            lambda: relationship.create(
                seed.first_resolution_id,
                seed.first_object.id,
                seed.second_object.id,
            ),
        )
        assert deleted is None
        assert _failure_code(created) == "referenced_resource_not_found"


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_ref_03_and_ref_05_relationship_object_lifetime_arbitration(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "REF-03-05-REL-OBJECT") as actors:
        seed = await _seed(actors, "ref03_reference_first")
        relationship = RelationshipService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        )
        object_delete = ObjectService(
            ObservedUnitOfWorkFactory(actors.t2_engine, actors.tracker, "T2")
        )
        with monkeypatch.context() as context:
            cut, _ = _insert_cut(context)
            created, deleted = await blocked_race(
                actors,
                cut,
                lambda: relationship.create(
                    seed.first_resolution_id,
                    seed.first_object.id,
                    seed.second_object.id,
                ),
                lambda: object_delete.delete(seed.first_object.id),
            )
        assert isinstance(created, RelationshipCreateResult)
        assert isinstance(deleted, ApplicationFailure)
        assert deleted.code == "delete_blocked"
        assert deleted.details == {
            "resource_type": "object",
            "id": str(seed.first_object.id),
            "blockers": [{"type": "relationship", "count": 1}],
        }

        # REF-05: removing the factual reference first admits Object deletion.
        await _reader(actors).delete(created.relationship.id)
        await ObjectService(UnitOfWorkFactory(actors.t1_engine)).delete(
            seed.first_object.id
        )

        seed = await _seed(actors, "ref03_delete_first")
        object_delete = ObjectService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        )
        relationship = RelationshipService(
            ObservedUnitOfWorkFactory(actors.t2_engine, actors.tracker, "T2")
        )
        with monkeypatch.context() as context:
            cut = _object_delete_cut(context)
            deleted, created = await blocked_race(
                actors,
                cut,
                lambda: object_delete.delete(seed.first_object.id),
                lambda: relationship.create(
                    seed.first_resolution_id,
                    seed.first_object.id,
                    seed.second_object.id,
                ),
            )
        assert deleted is None
        assert _failure_code(created) == "referenced_resource_not_found"
        assert isinstance(created, ApplicationFailure)
        assert created.details == {
            "resource_type": "object",
            "id": str(seed.first_object.id),
        }


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_ref_06c_definition_cascade_loses_to_relationship_restrict(
    migrated_database_engine: Engine,
    test_database_url: str,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "REF-06C-RD-CASCADE") as actors:
        seed = await _seed(actors, "ref06c")
        cut = PhaseCut()
        precheck_counts: list[int] = []

        async def physical_delete_attempt() -> object:
            async with UnitOfWorkFactory(actors.t1_engine)() as uow:
                store = RelationshipDefinitionStore(uow.connection)
                precheck_counts.append(
                    await store.current_relationship_count(seed.definition.id)
                )
                cut.reached.set()
                await cut.release.wait()
                try:
                    await store.delete(seed.definition.id)
                except RelationshipDefinitionDeleteReferenceError as error:
                    return error
                raise AssertionError("external RESTRICT did not stop physical delete")

        relationship_service = RelationshipService(UnitOfWorkFactory(actors.t2_engine))
        physical_error, created = await progress_race(
            cut,
            physical_delete_attempt,
            lambda: relationship_service.create(
                seed.first_resolution_id,
                seed.first_object.id,
                seed.second_object.id,
            ),
        )
        assert precheck_counts == [0]
        assert isinstance(created, RelationshipCreateResult)
        assert isinstance(physical_error, RelationshipDefinitionDeleteReferenceError)

        definition_service = RelationshipDefinitionService(
            UnitOfWorkFactory(actors.t1_engine)
        )
        persisted_definition = await definition_service.get(seed.definition.id)
        assert persisted_definition.id == seed.definition.id
        assert persisted_definition.symmetric == seed.definition.symmetric
        assert set(persisted_definition.resolutions) == set(seed.definition.resolutions)
        assert len(persisted_definition.resolutions) == 2
        assert (
            await relationship_service.get(created.relationship.id)
        ).id == created.relationship.id

        with pytest.raises(ApplicationFailure) as blocked:
            await definition_service.delete(seed.definition.id)
        assert blocked.value.code == "delete_blocked"
        assert blocked.value.details == {
            "resource_type": "relationship_definition",
            "id": str(seed.definition.id),
            "blockers": [{"type": "relationship", "count": 1}],
        }


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_snap_01_delete_event_keeps_one_pre_rename_name_snapshot(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "SNAP-01-REL-DELETE") as actors:
        seed = await _seed(actors, "snap01", first_name="old_a", second_name="old_b")
        reader = _reader(actors)
        created = await reader.create(
            seed.first_resolution_id,
            seed.first_object.id,
            seed.second_object.id,
        )
        cut, observations = _metadata_cut(monkeypatch)
        delete_service = RelationshipService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        )
        delete_task = asyncio.create_task(
            delete_service.delete(created.relationship.id), name="T1"
        )
        await cut.reached.wait()
        first_resolution, second_resolution = seed.definition.resolutions
        await RelationshipDefinitionService(
            UnitOfWorkFactory(actors.t2_engine)
        ).rename_non_symmetric(
            seed.definition.id,
            (
                ResolutionRename(first_resolution.id, "new_a"),
                ResolutionRename(second_resolution.id, "new_b"),
            ),
        )
        cut.release.set()
        await delete_task
        assert observations == [2]
        async with actors.t1_engine.connect() as connection:
            names = set(
                await connection.scalars(
                    select(object_lifecycle_events.c.relationship_name).where(
                        object_lifecycle_events.c.relationship_id
                        == created.relationship.id,
                        object_lifecycle_events.c.kind == "RELATIONSHIP_DELETED",
                    )
                )
            )
        assert names == {"old_a", "old_b"}


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_snap_02_delete_event_keeps_one_pre_rename_object_snapshot(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "SNAP-02-REL-DELETE") as actors:
        seed = await _seed(actors, "snap02")
        service = _reader(actors)
        created = await service.create(
            seed.first_resolution_id,
            seed.first_object.id,
            seed.second_object.id,
        )
        cut, observations = _metadata_cut(monkeypatch)
        delete_service = RelationshipService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        )
        delete_task = asyncio.create_task(
            delete_service.delete(created.relationship.id), name="T1"
        )
        await cut.reached.wait()
        await ObjectService(UnitOfWorkFactory(actors.t2_engine)).rename(
            seed.first_object.id, "snap02-renamed-first"
        )
        cut.release.set()
        await delete_task
        assert observations == [2]
        async with actors.t1_engine.connect() as connection:
            names = {
                (row.object_id, row.canonical_name)
                for row in (
                    await connection.execute(
                        select(
                            object_lifecycle_events.c.object_id,
                            object_lifecycle_events.c.canonical_name,
                        ).where(
                            object_lifecycle_events.c.relationship_id
                            == created.relationship.id,
                            object_lifecycle_events.c.kind == "RELATIONSHIP_DELETED",
                        )
                    )
                ).all()
            }
        assert names == {
            (seed.first_object.id, seed.first_object.canonical_name),
            (seed.second_object.id, seed.second_object.canonical_name),
        }


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_snap_03_create_observes_one_real_two_endpoint_name_generation(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "SNAP-03-REL-CREATE") as actors:
        seed = await _seed(actors, "snap03")
        insert_cut, _ = _insert_cut(monkeypatch)
        metadata_cut, observations = _metadata_cut(monkeypatch)
        service = RelationshipService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        )
        create_task = asyncio.create_task(
            service.create(
                seed.first_resolution_id,
                seed.first_object.id,
                seed.second_object.id,
            ),
            name="T1",
        )
        await insert_cut.reached.wait()
        objects = ObjectService(UnitOfWorkFactory(actors.t2_engine))
        await objects.rename(seed.first_object.id, "snap03-renamed-first")
        insert_cut.release.set()
        await metadata_cut.reached.wait()
        await objects.rename(seed.second_object.id, "snap03-renamed-second")
        metadata_cut.release.set()
        created = await create_task
        assert isinstance(created, RelationshipCreateResult)
        assert observations == [2]

        async with actors.t1_engine.connect() as connection:
            relationship_rows = (
                await connection.execute(
                    select(
                        object_lifecycle_events.c.object_id,
                        object_lifecycle_events.c.canonical_name,
                        object_lifecycle_events.c.destination_object_id,
                        object_lifecycle_events.c.destination_canonical_name,
                        object_lifecycle_events.c.occurred_at,
                    ).where(
                        object_lifecycle_events.c.relationship_id
                        == created.relationship.id,
                        object_lifecycle_events.c.kind == "RELATIONSHIP_CREATED",
                    )
                )
            ).all()
            first_rename_time = await connection.scalar(
                select(object_lifecycle_events.c.occurred_at).where(
                    object_lifecycle_events.c.object_id == seed.first_object.id,
                    object_lifecycle_events.c.kind == "RENAME",
                )
            )
        assert {
            (
                row.object_id,
                row.canonical_name,
                row.destination_object_id,
                row.destination_canonical_name,
            )
            for row in relationship_rows
        } == {
            (
                seed.first_object.id,
                "snap03-renamed-first",
                seed.second_object.id,
                seed.second_object.canonical_name,
            ),
            (
                seed.second_object.id,
                seed.second_object.canonical_name,
                seed.first_object.id,
                "snap03-renamed-first",
            ),
        }
        assert first_rename_time is not None
        assert all(row.occurred_at < first_rename_time for row in relationship_rows)


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_atomic_02_later_closure_pk_collision_rolls_back_candidate(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ATOMIC-02-REL") as actors:
        seed = await _seed(actors, "atomic02")
        closure = derive_runtime_closure(
            seed.definition,
            selected_resolution_id=seed.first_resolution_id,
            from_object_id=seed.first_object.id,
            from_template_id=seed.first_object.template_id,
            to_object_id=seed.second_object.id,
            to_template_id=seed.second_object.template_id,
            parent_by_id={
                seed.first_object.template_id: None,
                seed.second_object.template_id: None,
            },
        )
        assert len(closure) == 2
        later_row = closure[1]
        blocker_id = uuid4()
        blocker = await PgWorker.open(test_database_url, "ATOMIC-02-REL", WorkerRole.B)
        candidates: list[Relationship] = []
        original = RuntimeRelationshipStore.insert

        async def recorded_insert(
            store: RuntimeRelationshipStore, value: Relationship
        ) -> None:
            candidates.append(value)
            await original(store, value)

        monkeypatch.setattr(RuntimeRelationshipStore, "insert", recorded_insert)
        try:
            await blocker.connection.execute(
                relationships.insert().values(
                    id=blocker_id,
                    relationship_definition_id=seed.definition.id,
                )
            )
            await blocker.connection.execute(
                runtime_relationship_resolutions.insert().values(
                    relationship_id=blocker_id,
                    relationship_definition_id=seed.definition.id,
                    resolution_id=later_row.resolution_id,
                    from_object_id=later_row.from_object_id,
                    to_object_id=later_row.to_object_id,
                )
            )
            actors.tracker.reset()
            service = RelationshipService(
                ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
            )
            create_task = asyncio.create_task(
                capture(
                    lambda: service.create(
                        seed.first_resolution_id,
                        seed.first_object.id,
                        seed.second_object.id,
                    )
                ),
                name="T1",
            )
            await actors.tracker.ready["T1"].wait()
            assert blocker.backend_pid in await wait_for_blocker(
                actors.observer,
                actors.tracker.pids["T1"],
                blocker.backend_pid,
            )
            await blocker.commit()
            outcome = await create_task
            assert _failure_code(outcome) == "internal_error"
            assert len(candidates) == 1
            candidate = candidates[0]
            assert candidate.resolutions[1].resolution_id == later_row.resolution_id

            async with actors.t1_engine.connect() as connection:
                assert (
                    await connection.scalar(
                        select(func.count())
                        .select_from(relationships)
                        .where(relationships.c.id == candidate.id)
                    )
                    == 0
                )
                assert (
                    await connection.scalar(
                        select(func.count())
                        .select_from(runtime_relationship_resolutions)
                        .where(
                            runtime_relationship_resolutions.c.relationship_id
                            == candidate.id
                        )
                    )
                    == 0
                )
                assert (
                    await connection.scalar(
                        select(func.count())
                        .select_from(object_lifecycle_events)
                        .where(
                            object_lifecycle_events.c.relationship_id == candidate.id
                        )
                    )
                    == 0
                )
            async with actors.t2_engine.begin() as connection:
                await connection.execute(
                    relationships.delete().where(relationships.c.id == blocker_id)
                )
        finally:
            await blocker.close()


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_create_event_failure_rolls_back_header_and_complete_closure(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(
        test_database_url, "REL-CREATE-EVENT-ROLLBACK"
    ) as actors:
        seed = await _seed(actors, "create_event_rollback")
        service = _reader(actors)
        original = RuntimeRelationshipStore.insert_lifecycle_events
        candidate_ids: list[UUID] = []

        async def failed_creation_events(
            store: RuntimeRelationshipStore,
            *,
            kind: str,
            relationship: Relationship,
            views: Sequence[RelationshipLifecycleView],
        ) -> None:
            if kind == "RELATIONSHIP_CREATED":
                candidate_ids.append(relationship.id)
                assert (
                    await store.connection.scalar(
                        select(func.count())
                        .select_from(relationships)
                        .where(relationships.c.id == relationship.id)
                    )
                    == 1
                )
                assert await store.connection.scalar(
                    select(func.count())
                    .select_from(runtime_relationship_resolutions)
                    .where(
                        runtime_relationship_resolutions.c.relationship_id
                        == relationship.id
                    )
                ) == len(relationship.resolutions)
                raise ApplicationFailure(
                    FailureClass.INTERNAL_FAILURE,
                    "internal_error",
                    "forced creation event failure",
                )
            await original(store, kind=kind, relationship=relationship, views=views)

        monkeypatch.setattr(
            RuntimeRelationshipStore,
            "insert_lifecycle_events",
            failed_creation_events,
        )
        with pytest.raises(ApplicationFailure) as caught:
            await service.create(
                seed.first_resolution_id,
                seed.first_object.id,
                seed.second_object.id,
            )
        assert caught.value.code == "internal_error"
        assert len(candidate_ids) == 1
        candidate_id = candidate_ids[0]
        async with actors.t1_engine.connect() as connection:
            assert (
                await connection.scalar(
                    select(func.count())
                    .select_from(relationships)
                    .where(relationships.c.id == candidate_id)
                )
                == 0
            )
            assert (
                await connection.scalar(
                    select(func.count())
                    .select_from(runtime_relationship_resolutions)
                    .where(
                        runtime_relationship_resolutions.c.relationship_id
                        == candidate_id
                    )
                )
                == 0
            )
            assert (
                await connection.scalar(
                    select(func.count())
                    .select_from(object_lifecycle_events)
                    .where(
                        object_lifecycle_events.c.relationship_id == candidate_id,
                        object_lifecycle_events.c.kind == "RELATIONSHIP_CREATED",
                    )
                )
                == 0
            )


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_atomic_03_delete_event_failure_rolls_back_complete_fact(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ATOMIC-03-REL") as actors:
        seed = await _seed(actors, "atomic03")
        service = _reader(actors)
        created = await service.create(
            seed.first_resolution_id,
            seed.first_object.id,
            seed.second_object.id,
        )
        original = RuntimeRelationshipStore.insert_lifecycle_events

        async def failed_events(
            store: RuntimeRelationshipStore,
            *,
            kind: str,
            relationship: Relationship,
            views: Sequence[RelationshipLifecycleView],
        ) -> None:
            if kind == "RELATIONSHIP_DELETED":
                raise ApplicationFailure(
                    FailureClass.INTERNAL_FAILURE,
                    "internal_error",
                    "forced deletion event failure",
                )
            await original(store, kind=kind, relationship=relationship, views=views)

        monkeypatch.setattr(
            RuntimeRelationshipStore, "insert_lifecycle_events", failed_events
        )
        with pytest.raises(ApplicationFailure) as caught:
            await service.delete(created.relationship.id)
        assert caught.value.code == "internal_error"
        assert (
            await service.get(created.relationship.id)
        ).id == created.relationship.id
        async with actors.t1_engine.connect() as connection:
            assert (
                await connection.scalar(
                    select(func.count())
                    .select_from(object_lifecycle_events)
                    .where(
                        object_lifecycle_events.c.relationship_id
                        == created.relationship.id,
                        object_lifecycle_events.c.kind == "RELATIONSHIP_DELETED",
                    )
                )
                == 0
            )


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_par_01_and_snap_02_create_progresses_during_object_rename(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "PAR-01-REL-OBJ-RENAME") as actors:
        seed = await _seed(actors, "par01")
        cut = PhaseCut()
        original = ObjectStore.update_name

        async def intercepted(
            store: ObjectStore, object_id: UUID, canonical_name: str
        ) -> None:
            await original(store, object_id, canonical_name)
            task = asyncio.current_task()
            if task is not None and task.get_name() == "T1":
                cut.reached.set()
                await cut.release.wait()

        monkeypatch.setattr(ObjectStore, "update_name", intercepted)
        rename = ObjectService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        )
        relationship = RelationshipService(
            ObservedUnitOfWorkFactory(actors.t2_engine, actors.tracker, "T2")
        )
        renamed, created = await progress_race(
            cut,
            lambda: rename.rename(seed.first_object.id, "renamed-first"),
            lambda: relationship.create(
                seed.first_resolution_id,
                seed.first_object.id,
                seed.second_object.id,
            ),
        )
        assert isinstance(renamed, Object)
        assert isinstance(created, RelationshipCreateResult)
        async with actors.t1_engine.connect() as connection:
            created_names = set(
                await connection.scalars(
                    select(object_lifecycle_events.c.canonical_name).where(
                        object_lifecycle_events.c.relationship_id
                        == created.relationship.id,
                        object_lifecycle_events.c.kind == "RELATIONSHIP_CREATED",
                    )
                )
            )
        assert created_names == {
            seed.first_object.canonical_name,
            seed.second_object.canonical_name,
        }


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_realize_15_relationship_create_progresses_after_object_data_update(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "REALIZE-15-REL-DATA") as actors:
        seed = await _mutable_object_seed(actors, "realize15_data")
        cut = _object_update_cut(monkeypatch, schema_change=False)
        objects = ObjectService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        )
        relationship = RelationshipService(
            ObservedUnitOfWorkFactory(actors.t2_engine, actors.tracker, "T2")
        )
        changed, created = await progress_race(
            cut,
            lambda: objects.data_change(
                seed.first_object.id,
                (DataChangeOperation(DataChangeKind.SET, "value", 1),),
            ),
            lambda: relationship.create(
                seed.first_resolution_id,
                seed.first_object.id,
                seed.second_object.id,
            ),
        )
        assert isinstance(changed, Object)
        assert changed.properties == {"value": 1}
        assert isinstance(created, RelationshipCreateResult)
        assert created.created is True


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_realize_15_relationship_create_progresses_after_object_schema_update(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "REALIZE-15-REL-SCHEMA") as actors:
        seed = await _mutable_object_seed(actors, "realize15_schema")
        cut = _object_update_cut(monkeypatch, schema_change=True)
        objects = ObjectService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        )
        relationship = RelationshipService(
            ObservedUnitOfWorkFactory(actors.t2_engine, actors.tracker, "T2")
        )
        migrated, created = await progress_race(
            cut,
            lambda: objects.schema_change(seed.first_object.id, 2),
            lambda: relationship.create(
                seed.first_resolution_id,
                seed.first_object.id,
                seed.second_object.id,
            ),
        )
        assert isinstance(migrated, Object)
        assert migrated.template_version == 2
        assert isinstance(created, RelationshipCreateResult)
        assert created.created is True


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_par_02_and_snap_01_create_progresses_during_definition_rename(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "PAR-02-REL-RD-RENAME") as actors:
        seed = await _seed(actors, "par02")
        cut = PhaseCut()
        original = RelationshipDefinitionStore.update_names

        async def intercepted(
            store: RelationshipDefinitionStore, value: RelationshipDefinition
        ) -> None:
            await original(store, value)
            task = asyncio.current_task()
            if task is not None and task.get_name() == "T1":
                cut.reached.set()
                await cut.release.wait()

        monkeypatch.setattr(RelationshipDefinitionStore, "update_names", intercepted)
        first_resolution, second_resolution = seed.definition.resolutions
        rename = RelationshipDefinitionService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        )
        relationship = RelationshipService(
            ObservedUnitOfWorkFactory(actors.t2_engine, actors.tracker, "T2")
        )
        renamed, created = await progress_race(
            cut,
            lambda: rename.rename_non_symmetric(
                seed.definition.id,
                (
                    ResolutionRename(first_resolution.id, "renamed_a"),
                    ResolutionRename(second_resolution.id, "renamed_b"),
                ),
            ),
            lambda: relationship.create(
                seed.first_resolution_id,
                seed.first_object.id,
                seed.second_object.id,
            ),
        )
        assert isinstance(renamed, RelationshipDefinition)
        assert isinstance(created, RelationshipCreateResult)
        async with actors.t1_engine.connect() as connection:
            created_names = set(
                await connection.scalars(
                    select(object_lifecycle_events.c.relationship_name).where(
                        object_lifecycle_events.c.relationship_id
                        == created.relationship.id,
                        object_lifecycle_events.c.kind == "RELATIONSHIP_CREATED",
                    )
                )
            )
        assert created_names in (
            {"contains", "contained_by"},
            {"renamed_a", "renamed_b"},
        )


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_par_05_unrelated_relationship_creates_have_no_global_gate(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "PAR-05-REL") as actors:
        seed = await _seed(actors, "par05")
        factory = UnitOfWorkFactory(actors.t1_engine)
        objects = ObjectService(factory)
        third = await objects.create(
            seed.first_object.template_id, 1, "par05-third", {}
        )
        fourth = await objects.create(
            seed.second_object.template_id, 1, "par05-fourth", {}
        )
        cut, _ = _insert_cut(monkeypatch)
        first, second = _relationship_services(actors)
        first_outcome, second_outcome = await progress_race(
            cut,
            lambda: first.create(
                seed.first_resolution_id,
                seed.first_object.id,
                seed.second_object.id,
            ),
            lambda: second.create(seed.first_resolution_id, third.id, fourth.id),
        )
        assert isinstance(first_outcome, RelationshipCreateResult)
        assert isinstance(second_outcome, RelationshipCreateResult)
