"""Deterministic PostgreSQL evidence for the M2-S01 RDV lock cut."""

import asyncio
from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID

import pytest
from sqlalchemy import Engine, func, select
from sqlalchemy.ext.asyncio import AsyncConnection

import netauto.application.objecttemplates as object_template_application
import netauto.application.relationshipdefinitions as definition_application
from netauto.application.datatypes import DataTypeService
from netauto.application.objects import ObjectService
from netauto.application.objecttemplates import ObjectTemplateService
from netauto.application.objecttemplates import (
    PropertyCandidate as ObjectTemplatePropertyCandidate,
)
from netauto.application.relationshipdefinitions import RelationshipDefinitionService
from netauto.application.relationships import (
    RelationshipCreateResult,
    RelationshipService,
)
from netauto.domain.datatypes import CreateDataTypeResult, DataType
from netauto.domain.objecttemplates import ObjectTemplateVersion, ValueMode
from netauto.domain.relationships import (
    Relationship,
    RelationshipDefinition,
    RelationshipDefinitionVersion,
    RelationshipPerspective,
    RelationshipPropertyCandidate,
)
from netauto.failures import ApplicationFailure, FailureClass
from netauto.persistence.locking import (
    AdvisoryGate,
    LockPlan,
    RowLockClass,
    RowLockIntent,
    RowLockMode,
)
from netauto.persistence.metadata import (
    object_lifecycle_events,
    relationship_definition_properties,
    relationship_definition_versions,
    relationship_definitions,
    relationship_resolutions,
    relationships,
)
from netauto.persistence.relationships import (
    RelationshipDefinitionVersionStore,
    RuntimeRelationshipStore,
)
from netauto.persistence.uow import UnitOfWorkFactory
from tests.support.semantic_concurrency import (
    ObservedUnitOfWorkFactory,
    PhaseCut,
    SemanticActors,
    blocked_race,
    capture,
    install_lock_plan_cut,
    progress_race,
    run_worker,
    semantic_actors,
)


@dataclass(frozen=True, slots=True)
class RdvSeed:
    datatype: CreateDataTypeResult
    definition: RelationshipDefinition
    first_template_id: UUID
    second_template_id: UUID


def _definitions(
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


def _relationships(
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


def _failure(value: object) -> ApplicationFailure:
    assert isinstance(value, ApplicationFailure)
    return value


def _relationship_insert_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    cut = PhaseCut()
    original = RuntimeRelationshipStore.insert

    async def intercepted(store: RuntimeRelationshipStore, value: Relationship) -> None:
        await original(store, value)
        task = asyncio.current_task()
        if task is not None and task.get_name() == "T1":
            cut.reached.set()
            await cut.release.wait()

    monkeypatch.setattr(RuntimeRelationshipStore, "insert", intercepted)
    return cut


def _pre_acquisition_cut(monkeypatch: pytest.MonkeyPatch) -> PhaseCut:
    """Pause T1 after semantic discovery and before complete plan acquisition."""
    cut = PhaseCut()
    original = definition_application.prepare_lock_plan

    async def intercepted(
        connection: AsyncConnection,
        *,
        intents: Iterable[RowLockIntent] = (),
        gate: AdvisoryGate | None = None,
    ) -> LockPlan:
        task = asyncio.current_task()
        if task is not None and task.get_name() == "T1" and not cut.reached.is_set():
            cut.reached.set()
            await cut.release.wait()
        return await original(connection, intents=intents, gate=gate)

    monkeypatch.setattr(definition_application, "prepare_lock_plan", intercepted)
    return cut


async def _unreferenced_property_operand(
    actors: SemanticActors, prefix: str
) -> tuple[CreateDataTypeResult, UUID, UUID]:
    factory = UnitOfWorkFactory(actors.t1_engine)
    datatypes = DataTypeService(factory)
    datatype = await datatypes.create(
        "m2_s01_concurrency", f"{prefix}_value", "core.integer", None, {}
    )
    await datatypes.publish(datatype.datatype.id, 1, 1)
    templates = ObjectTemplateService(factory)
    first = await templates.create(
        "m2_s01_concurrency", f"{prefix}_first", False, None, None, None, (), ()
    )
    second = await templates.create(
        "m2_s01_concurrency", f"{prefix}_second", False, None, None, None, (), ()
    )
    return datatype, first.object_template.id, second.object_template.id


async def _relationship_model_counts(
    actors: SemanticActors,
) -> tuple[int, int, int, int]:
    async with actors.t1_engine.connect() as connection:
        return (
            int(
                await connection.scalar(
                    select(func.count()).select_from(relationship_definitions)
                )
                or 0
            ),
            int(
                await connection.scalar(
                    select(func.count()).select_from(relationship_resolutions)
                )
                or 0
            ),
            int(
                await connection.scalar(
                    select(func.count()).select_from(relationship_definition_versions)
                )
                or 0
            ),
            int(
                await connection.scalar(
                    select(func.count()).select_from(relationship_definition_properties)
                )
                or 0
            ),
        )


async def _seed(
    actors: SemanticActors,
    prefix: str,
    *,
    publish_definition: bool = True,
) -> RdvSeed:
    factory = UnitOfWorkFactory(actors.t1_engine)
    datatypes = DataTypeService(factory)
    datatype = await datatypes.create(
        "m2_s01_concurrency", f"{prefix}_value", "core.integer", None, {}
    )
    await datatypes.publish(datatype.datatype.id, 1, 1)
    templates = ObjectTemplateService(factory)
    first = await templates.create(
        "m2_s01_concurrency", f"{prefix}_first", False, None, None, None, (), ()
    )
    second = await templates.create(
        "m2_s01_concurrency", f"{prefix}_second", False, None, None, None, (), ()
    )
    await templates.publish(first.object_template.id, 1, 1)
    await templates.publish(second.object_template.id, 1, 1)
    definitions = RelationshipDefinitionService(factory)
    created = await definitions.create_non_symmetric(
        (
            RelationshipPerspective(first.object_template.id, "points_to"),
            RelationshipPerspective(second.object_template.id, "pointed_from"),
        ),
        (
            RelationshipPropertyCandidate(
                "value", 1, datatype.datatype.id, 1, ValueMode.SCALAR
            ),
        ),
    )
    if publish_definition:
        await definitions.publish(created.relationship_definition.id, 1, 1)
    return RdvSeed(
        datatype,
        created.relationship_definition,
        first.object_template.id,
        second.object_template.id,
    )


async def _two_published_rdv(actors: SemanticActors, prefix: str) -> RdvSeed:
    seed = await _seed(actors, prefix)
    service = RelationshipDefinitionService(UnitOfWorkFactory(actors.t1_engine))
    await service.create_next(seed.definition.id, 1)
    await service.publish(seed.definition.id, 2, 1)
    return seed


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_18_create_next_allocates_serial_distinct_versions(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-18-RDV") as actors:
        seed = await _seed(actors, "row18")
        first, second = _definitions(actors)
        cut = install_lock_plan_cut(
            monkeypatch,
            definition_application,
            RowLockClass.RELATIONSHIP_DEFINITION_HEADER,
            RowLockMode.NKU,
        )
        outcomes = await blocked_race(
            actors,
            cut,
            lambda: first.create_next(seed.definition.id, 1),
            lambda: second.create_next(seed.definition.id, 1),
        )
        assert all(isinstance(item, RelationshipDefinitionVersion) for item in outcomes)
        assert {
            item.version
            for item in outcomes
            if isinstance(item, RelationshipDefinitionVersion)
        } == {2, 3}


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_19_create_next_rereads_max_after_draft_delete(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-19-RDV") as actors:
        seed = await _seed(actors, "row19")
        setup = RelationshipDefinitionService(UnitOfWorkFactory(actors.t1_engine))
        assert (await setup.create_next(seed.definition.id, 1)).version == 2
        first, second = _definitions(actors)
        cut = install_lock_plan_cut(
            monkeypatch,
            definition_application,
            RowLockClass.RELATIONSHIP_DEFINITION_HEADER,
            RowLockMode.NKU,
        )
        deleted, created = await blocked_race(
            actors,
            cut,
            lambda: first.delete_draft(seed.definition.id, 2, 1),
            lambda: second.create_next(seed.definition.id, 1),
        )
        assert deleted is None
        assert isinstance(created, RelationshipDefinitionVersion)
        assert created.version == 2


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_20_one_exact_generation_consumer_wins(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-20-RDV") as actors:
        seed = await _seed(actors, "row20")
        setup = RelationshipDefinitionService(UnitOfWorkFactory(actors.t1_engine))
        await setup.create_next(seed.definition.id, 1)
        first, second = _definitions(actors)
        cut = install_lock_plan_cut(
            monkeypatch,
            definition_application,
            RowLockClass.RELATIONSHIP_DEFINITION_VERSION,
            RowLockMode.NKU,
        )
        revised, published = await blocked_race(
            actors,
            cut,
            lambda: first.revise(
                seed.definition.id,
                2,
                1,
                (
                    RelationshipPropertyCandidate(
                        "value",
                        1,
                        seed.datatype.datatype.id,
                        1,
                        ValueMode.LIST,
                    ),
                ),
            ),
            lambda: second.publish(seed.definition.id, 2, 1),
        )
        assert isinstance(revised, RelationshipDefinitionVersion)
        assert revised.revision == 2
        assert _failure(published).code == "stale_revision"


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_21_default_change_serializes_target_deprecation(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-21-RDV") as actors:
        seed = await _two_published_rdv(actors, "row21")
        first, second = _definitions(actors)
        cut = install_lock_plan_cut(
            monkeypatch,
            definition_application,
            RowLockClass.RELATIONSHIP_DEFINITION_HEADER,
            RowLockMode.NKU,
        )
        selected, deprecated = await blocked_race(
            actors,
            cut,
            lambda: first.set_default(seed.definition.id, 2),
            lambda: second.deprecate(seed.definition.id, 2),
        )
        assert isinstance(selected, RelationshipDefinition)
        assert selected.default_version == 2
        assert _failure(deprecated).code == "default_version_conflict"


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_22_object_template_publish_recertifies_member_history(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-22-OTV") as actors:
        factory = UnitOfWorkFactory(actors.t1_engine)
        datatype = await DataTypeService(factory).create(
            "m2_s01_concurrency", "row22_value", "core.integer", None, {}
        )
        await DataTypeService(factory).publish(datatype.datatype.id, 1, 1)
        setup = ObjectTemplateService(factory)
        scalar = ObjectTemplatePropertyCandidate(
            "value", 1, datatype.datatype.id, 1, ValueMode.SCALAR, False
        )
        created = await setup.create(
            "m2_s01_concurrency",
            "row22_template",
            False,
            None,
            None,
            None,
            (scalar,),
            (),
        )
        template_id = created.object_template.id
        await setup.publish(template_id, 1, 1)
        await setup.create_next(template_id, 1)
        await setup.create_next(template_id, 1)
        await setup.revise(
            template_id,
            2,
            1,
            None,
            (
                ObjectTemplatePropertyCandidate(
                    "value", 1, datatype.datatype.id, 1, ValueMode.LIST, False
                ),
            ),
            (),
        )
        first = ObjectTemplateService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        )
        second = ObjectTemplateService(
            ObservedUnitOfWorkFactory(actors.t2_engine, actors.tracker, "T2")
        )
        cut = install_lock_plan_cut(
            monkeypatch,
            object_template_application,
            RowLockClass.OBJECT_TEMPLATE_HEADER,
            RowLockMode.NKU,
        )
        widened, narrowed = await blocked_race(
            actors,
            cut,
            lambda: first.publish(template_id, 2, 2),
            lambda: second.publish(template_id, 3, 1),
        )
        assert isinstance(widened, ObjectTemplateVersion)
        assert widened.status.value == "PUBLISHED"
        assert _failure(narrowed).code == "semantic_validation_failed"


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_23_rdv_publish_recertifies_complete_history(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-23-RDV") as actors:
        seed = await _seed(actors, "row23")
        setup = RelationshipDefinitionService(UnitOfWorkFactory(actors.t1_engine))
        await setup.create_next(seed.definition.id, 1)
        await setup.create_next(seed.definition.id, 1)
        await setup.revise(
            seed.definition.id,
            2,
            1,
            (
                RelationshipPropertyCandidate(
                    "value", 1, seed.datatype.datatype.id, 1, ValueMode.LIST
                ),
            ),
        )
        first, second = _definitions(actors)
        cut = install_lock_plan_cut(
            monkeypatch,
            definition_application,
            RowLockClass.RELATIONSHIP_DEFINITION_HEADER,
            RowLockMode.NKU,
        )
        widened, narrowed = await blocked_race(
            actors,
            cut,
            lambda: first.publish(seed.definition.id, 2, 2),
            lambda: second.publish(seed.definition.id, 3, 1),
        )
        assert isinstance(widened, RelationshipDefinitionVersion)
        assert widened.status.value == "PUBLISHED"
        assert _failure(narrowed).code == "semantic_validation_failed"


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_24_implicit_dtv_binding_is_stable_through_commit(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-24-RDV") as actors:
        seed = await _seed(actors, "row24_seed", publish_definition=False)
        datatypes = DataTypeService(UnitOfWorkFactory(actors.t1_engine))
        await datatypes.create_next(seed.datatype.datatype.id, 1)
        await datatypes.publish(seed.datatype.datatype.id, 2, 1)
        first = RelationshipDefinitionService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        )
        second = DataTypeService(
            ObservedUnitOfWorkFactory(actors.t2_engine, actors.tracker, "T2")
        )
        cut = install_lock_plan_cut(
            monkeypatch,
            definition_application,
            RowLockClass.RELATIONSHIP_DEFINITION_VERSION,
            RowLockMode.NKU,
        )
        created, selected = await progress_race(
            cut,
            lambda: first.revise(
                seed.definition.id,
                1,
                1,
                (
                    RelationshipPropertyCandidate(
                        "value",
                        1,
                        seed.datatype.datatype.id,
                        None,
                        ValueMode.SCALAR,
                    ),
                ),
            ),
            lambda: second.set_default(seed.datatype.datatype.id, 2),
        )
        assert isinstance(created, RelationshipDefinitionVersion)
        assert created.properties[0].datatype_version == 2
        assert created.revision == 2
        assert isinstance(selected, DataType)
        assert selected.default_version == 2
        assert len(actors.tracker.transactions["T1"]) == 2
        assert len(set(actors.tracker.transactions["T1"])) == 2


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_24_explicit_create_delete_first_preserves_exact_selector(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(
        test_database_url, "ROW-24-RF03-EXPLICIT-CREATE"
    ) as actors:
        (
            datatype,
            first_template_id,
            second_template_id,
        ) = await _unreferenced_property_operand(actors, "rf03_create")
        before = await _relationship_model_counts(actors)
        service = RelationshipDefinitionService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        )
        deleter = DataTypeService(
            ObservedUnitOfWorkFactory(actors.t2_engine, actors.tracker, "T2")
        )
        cut = _pre_acquisition_cut(monkeypatch)
        operation = asyncio.create_task(
            capture(
                lambda: service.create_non_symmetric(
                    (
                        RelationshipPerspective(first_template_id, "links_to"),
                        RelationshipPerspective(second_template_id, "linked_from"),
                    ),
                    (
                        RelationshipPropertyCandidate(
                            "value",
                            1,
                            datatype.datatype.id,
                            1,
                            ValueMode.SCALAR,
                        ),
                    ),
                )
            ),
            name="T1",
        )
        await cut.reached.wait()
        try:
            await deleter.delete_lineage(datatype.datatype.id)
        finally:
            cut.release.set()
        async with asyncio.timeout(5):
            outcome = await operation

        failure = _failure(outcome)
        assert failure.code == "referenced_resource_not_found"
        assert failure.details == {
            "resource_type": "datatype_version",
            "id": str(datatype.datatype.id),
            "version": 1,
        }
        assert await _relationship_model_counts(actors) == before


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_ref_09_explicit_revise_delete_first_preserves_exact_selector(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(
        test_database_url, "REF-09-RF03-EXPLICIT-REVISE"
    ) as actors:
        seed = await _seed(actors, "rf03_revise", publish_definition=False)
        factory = UnitOfWorkFactory(actors.t1_engine)
        datatypes = DataTypeService(factory)
        target = await datatypes.create(
            "m2_s01_concurrency", "rf03_revise_target", "core.integer", None, {}
        )
        await datatypes.publish(target.datatype.id, 1, 1)
        service = RelationshipDefinitionService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        )
        deleter = DataTypeService(
            ObservedUnitOfWorkFactory(actors.t2_engine, actors.tracker, "T2")
        )
        cut = _pre_acquisition_cut(monkeypatch)
        operation = asyncio.create_task(
            capture(
                lambda: service.revise(
                    seed.definition.id,
                    1,
                    1,
                    (
                        RelationshipPropertyCandidate(
                            "replacement",
                            1,
                            target.datatype.id,
                            1,
                            ValueMode.SCALAR,
                        ),
                    ),
                )
            ),
            name="T1",
        )
        await cut.reached.wait()
        try:
            await deleter.delete_lineage(target.datatype.id)
        finally:
            cut.release.set()
        async with asyncio.timeout(5):
            outcome = await operation

        failure = _failure(outcome)
        assert failure.code == "referenced_resource_not_found"
        assert failure.details == {
            "resource_type": "datatype_version",
            "id": str(target.datatype.id),
            "version": 1,
        }
        current = await RelationshipDefinitionService(factory).get_version(
            seed.definition.id, 1
        )
        assert current.revision == 1
        assert len(current.properties) == 1
        assert current.properties[0].name == "value"
        assert current.properties[0].datatype_id == seed.datatype.datatype.id
        assert current.properties[0].datatype_version == 1


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_24_implicit_create_delete_first_identifies_lineage(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(
        test_database_url, "ROW-24-RF03-IMPLICIT-CREATE"
    ) as actors:
        (
            datatype,
            first_template_id,
            second_template_id,
        ) = await _unreferenced_property_operand(actors, "rf03_implicit")
        before = await _relationship_model_counts(actors)
        service = RelationshipDefinitionService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        )
        deleter = DataTypeService(
            ObservedUnitOfWorkFactory(actors.t2_engine, actors.tracker, "T2")
        )
        cut = _pre_acquisition_cut(monkeypatch)
        operation = asyncio.create_task(
            capture(
                lambda: service.create_non_symmetric(
                    (
                        RelationshipPerspective(first_template_id, "connects_to"),
                        RelationshipPerspective(second_template_id, "connected_from"),
                    ),
                    (
                        RelationshipPropertyCandidate(
                            "value",
                            1,
                            datatype.datatype.id,
                            None,
                            ValueMode.SCALAR,
                        ),
                    ),
                )
            ),
            name="T1",
        )
        await cut.reached.wait()
        try:
            await deleter.delete_lineage(datatype.datatype.id)
        finally:
            cut.release.set()
        async with asyncio.timeout(5):
            outcome = await operation

        failure = _failure(outcome)
        assert failure.code == "referenced_resource_not_found"
        assert failure.details == {
            "resource_type": "datatype",
            "id": str(datatype.datatype.id),
        }
        assert await _relationship_model_counts(actors) == before


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_25_published_rdv_blocks_dtv_deprecation_after_wait(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-25-RDV") as actors:
        seed = await _seed(actors, "row25", publish_definition=False)
        setup = DataTypeService(UnitOfWorkFactory(actors.t1_engine))
        await setup.clear_default(seed.datatype.datatype.id)
        first = RelationshipDefinitionService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        )
        second = DataTypeService(
            ObservedUnitOfWorkFactory(actors.t2_engine, actors.tracker, "T2")
        )
        cut = install_lock_plan_cut(
            monkeypatch,
            definition_application,
            RowLockClass.DATA_TYPE_VERSION,
            RowLockMode.S,
        )
        published, deprecated = await blocked_race(
            actors,
            cut,
            lambda: first.publish(seed.definition.id, 1, 1),
            lambda: second.deprecate(seed.datatype.datatype.id, 1),
        )
        assert isinstance(published, RelationshipDefinitionVersion)
        assert published.status.value == "PUBLISHED"
        assert _failure(deprecated).code == "active_dependency_conflict"


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_row_30_and_arb_08_factual_selection_and_partial_owner_conflict(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ROW-30-ARB-08") as actors:
        seed = await _two_published_rdv(actors, "row30")
        factory = UnitOfWorkFactory(actors.t1_engine)
        objects = ObjectService(factory)
        first_object = await objects.create(
            seed.first_template_id, 1, "row30-first", {}
        )
        second_object = await objects.create(
            seed.second_template_id, 1, "row30-second", {}
        )
        resolution_id = next(
            item.id
            for item in seed.definition.resolutions
            if item.from_template_id == seed.first_template_id
        )
        first, second = _relationships(actors)
        cut = _relationship_insert_cut(monkeypatch)
        winner, loser = await blocked_race(
            actors,
            cut,
            lambda: first.create(
                resolution_id,
                first_object.id,
                second_object.id,
                1,
                {"value": 1},
            ),
            lambda: second.create(
                resolution_id,
                first_object.id,
                second_object.id,
                2,
                {"value": 2},
            ),
        )
        assert isinstance(winner, RelationshipCreateResult)
        assert winner.relationship.relationship_definition_version == 1
        conflict = _failure(loser)
        assert conflict.code == "relationship_fact_conflict"
        assert conflict.details == {"relationship_id": str(winner.relationship.id)}
        async with actors.t1_engine.connect() as connection:
            assert (
                await connection.scalar(select(func.count()).select_from(relationships))
                == 1
            )
            assert (
                await connection.scalar(
                    select(func.count())
                    .select_from(object_lifecycle_events)
                    .where(object_lifecycle_events.c.kind == "RELATIONSHIP_CREATED")
                )
                == 2
            )


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_ref_07_clone_reference_blocks_datatype_root_delete(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "REF-07-RDV") as actors:
        seed = await _seed(actors, "ref07")
        first = RelationshipDefinitionService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        )
        second = DataTypeService(
            ObservedUnitOfWorkFactory(actors.t2_engine, actors.tracker, "T2")
        )
        cut = install_lock_plan_cut(
            monkeypatch,
            definition_application,
            RowLockClass.DATA_TYPE_HEADER,
            RowLockMode.KS,
        )
        cloned, deleted = await blocked_race(
            actors,
            cut,
            lambda: first.create_next(seed.definition.id, 1),
            lambda: second.delete_lineage(seed.datatype.datatype.id),
        )
        assert isinstance(cloned, RelationshipDefinitionVersion)
        assert cloned.version == 2
        assert _failure(deleted).code == "delete_blocked"


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_ref_09_rebound_reference_blocks_target_delete(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "REF-09-RDV") as actors:
        seed = await _seed(actors, "ref09")
        datatypes = DataTypeService(UnitOfWorkFactory(actors.t1_engine))
        target = await datatypes.create(
            "m2_s01_concurrency", "ref09_target", "core.integer", None, {}
        )
        await datatypes.publish(target.datatype.id, 1, 1)
        definitions = RelationshipDefinitionService(UnitOfWorkFactory(actors.t1_engine))
        await definitions.create_next(seed.definition.id, 1)
        first = RelationshipDefinitionService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        )
        second = DataTypeService(
            ObservedUnitOfWorkFactory(actors.t2_engine, actors.tracker, "T2")
        )
        cut = install_lock_plan_cut(
            monkeypatch,
            definition_application,
            RowLockClass.DATA_TYPE_HEADER,
            RowLockMode.KS,
        )
        revised, deleted = await blocked_race(
            actors,
            cut,
            lambda: first.revise(
                seed.definition.id,
                2,
                1,
                (
                    RelationshipPropertyCandidate(
                        "value",
                        1,
                        seed.datatype.datatype.id,
                        1,
                        ValueMode.SCALAR,
                    ),
                    RelationshipPropertyCandidate(
                        "additional", 2, target.datatype.id, 1, ValueMode.SCALAR
                    ),
                ),
            ),
            lambda: second.delete_lineage(target.datatype.id),
        )
        assert isinstance(revised, RelationshipDefinitionVersion)
        assert revised.revision == 2
        assert _failure(deleted).code == "delete_blocked"


@pytest.mark.postgresql
@pytest.mark.concurrency
async def test_atomic_05_differential_failure_rolls_back_revision_and_children(
    migrated_database_engine: Engine,
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del migrated_database_engine
    async with semantic_actors(test_database_url, "ATOMIC-05-RDV") as actors:
        seed = await _seed(actors, "atomic05")
        service = RelationshipDefinitionService(
            ObservedUnitOfWorkFactory(actors.t1_engine, actors.tracker, "T1")
        )
        await service.create_next(seed.definition.id, 1)
        original = RelationshipDefinitionVersionStore.replace_candidate

        async def fail_after_real_child_dml(
            store: RelationshipDefinitionVersionStore,
            candidate: RelationshipDefinitionVersion,
        ) -> None:
            await original(store, candidate)
            raise ApplicationFailure(
                FailureClass.INTERNAL_FAILURE,
                "internal_error",
                "forced failure after differential child DML",
            )

        monkeypatch.setattr(
            RelationshipDefinitionVersionStore,
            "replace_candidate",
            fail_after_real_child_dml,
        )
        with pytest.raises(ApplicationFailure) as failed:
            await run_worker(
                lambda: service.revise(
                    seed.definition.id,
                    2,
                    1,
                    (
                        RelationshipPropertyCandidate(
                            "replacement",
                            2,
                            seed.datatype.datatype.id,
                            1,
                            ValueMode.LIST,
                        ),
                    ),
                ),
                actors.tracker,
                "T1",
            )
        assert failed.value.code == "internal_error"
        current = await service.get_version(seed.definition.id, 2)
        assert current.revision == 1
        assert [(item.name, item.position) for item in current.properties] == [
            ("value", 1)
        ]
        async with actors.t1_engine.connect() as connection:
            assert (
                await connection.scalar(
                    select(func.count())
                    .select_from(relationship_definition_versions)
                    .where(
                        relationship_definition_versions.c.relationship_definition_id
                        == seed.definition.id,
                        relationship_definition_versions.c.version == 2,
                        relationship_definition_versions.c.revision == 1,
                    )
                )
                == 1
            )
            assert (
                await connection.scalar(
                    select(func.count())
                    .select_from(relationship_definition_properties)
                    .where(
                        relationship_definition_properties.c.relationship_definition_id
                        == seed.definition.id,
                        relationship_definition_properties.c.relationship_definition_version
                        == 2,
                    )
                )
                == 1
            )
