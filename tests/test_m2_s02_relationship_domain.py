"""M2-S02 pure property, lifecycle-codec, and ownership evidence."""

from pathlib import Path
from typing import cast
from uuid import uuid4

import pytest
from hypothesis import given
from hypothesis import strategies as st
from sqlalchemy.ext.asyncio import AsyncConnection

from netauto.application.relationships import RelationshipService
from netauto.domain.objects import (
    DataChangeKind,
    DataChangeOperation,
    RuntimePropertySpec,
    apply_data_change,
)
from netauto.domain.objecttemplates import ValueMode
from netauto.domain.primitives import JsonValue, PrimitiveType
from netauto.domain.relationships import (
    Relationship,
    RelationshipLifecycleView,
    RelationshipSchemaChangeBlocked,
    RelationshipSchemaPropertySpec,
    migrate_relationship_properties,
)
from netauto.failures import ApplicationFailure
from netauto.persistence.lifecycle import (
    EventKind,
    LifecycleStore,
    decode_historical_properties,
    decode_relationship_factual_state,
)
from netauto.persistence.uow import UnitOfWorkFactory


def _schema(
    name: str,
    position: int,
    mode: ValueMode,
    *,
    maximum: int | None = None,
) -> RelationshipSchemaPropertySpec:
    constraints: dict[str, JsonValue] = {} if maximum is None else {"maximum": maximum}
    return RelationshipSchemaPropertySpec(
        position,
        uuid4(),
        RuntimePropertySpec(name, mode, False, PrimitiveType.INTEGER, constraints),
    )


@pytest.mark.property
@given(st.integers())
def test_m2_s02_scalar_to_list_migration_is_canonical(value: int) -> None:
    datatype_id = uuid4()
    source = RelationshipSchemaPropertySpec(
        1,
        datatype_id,
        RuntimePropertySpec(
            "metric", ValueMode.SCALAR, False, PrimitiveType.INTEGER, {}
        ),
    )
    target = RelationshipSchemaPropertySpec(
        1,
        datatype_id,
        RuntimePropertySpec("metric", ValueMode.LIST, False, PrimitiveType.INTEGER, {}),
    )
    assert migrate_relationship_properties({"metric": value}, (source,), (target,)) == {
        "metric": [value]
    }


@pytest.mark.property
@given(st.integers(), st.integers())
def test_m2_s02_data_change_complete_state_and_noop(before: int, after: int) -> None:
    spec = RuntimePropertySpec(
        "metric", ValueMode.SCALAR, False, PrimitiveType.INTEGER, {}
    )
    changed = apply_data_change(
        {"metric": before},
        (DataChangeOperation(DataChangeKind.SET, "metric", after),),
        (spec,),
    )
    assert changed == {"metric": after}
    assert (
        apply_data_change(
            changed,
            (DataChangeOperation(DataChangeKind.SET, "metric", after),),
            (spec,),
        )
        == changed
    )
    assert (
        apply_data_change(
            changed,
            (DataChangeOperation(DataChangeKind.REMOVE, "metric"),),
            (spec,),
        )
        == {}
    )


@pytest.mark.property
@given(st.integers(), st.integers())
def test_m2_s02_unique_operation_order_is_nonsemantic(metric: int, other: int) -> None:
    specs = (
        RuntimePropertySpec(
            "metric", ValueMode.SCALAR, False, PrimitiveType.INTEGER, {}
        ),
        RuntimePropertySpec(
            "other", ValueMode.SCALAR, False, PrimitiveType.INTEGER, {}
        ),
    )
    operations = (
        DataChangeOperation(DataChangeKind.SET, "metric", metric),
        DataChangeOperation(DataChangeKind.SET, "other", other),
    )
    assert apply_data_change({}, operations, specs) == apply_data_change(
        {}, tuple(reversed(operations)), specs
    )


async def test_m2_s02_application_rejects_empty_and_duplicate_operations() -> None:
    service = RelationshipService(cast(UnitOfWorkFactory, object()))
    candidates = (
        (),
        (
            DataChangeOperation(DataChangeKind.SET, "metric", 1),
            DataChangeOperation(DataChangeKind.REMOVE, "metric"),
        ),
    )
    for operations in candidates:
        with pytest.raises(ApplicationFailure) as caught:
            await service.data_change(uuid4(), operations)
        assert caught.value.code == "invalid_request"


def test_m2_s02_schema_migration_preserves_removes_and_blocks_by_member() -> None:
    datatype_id = uuid4()
    source_metric = _schema("metric", 1, ValueMode.LIST)
    source_metric = RelationshipSchemaPropertySpec(
        source_metric.position, datatype_id, source_metric.runtime
    )
    source_removed = _schema("removed", 2, ValueMode.SCALAR)
    target_metric = RelationshipSchemaPropertySpec(
        1,
        datatype_id,
        RuntimePropertySpec(
            "metric",
            ValueMode.LIST,
            False,
            PrimitiveType.INTEGER,
            {"maximum": 10},
        ),
    )
    target_new = _schema("new_optional", 2, ValueMode.SCALAR)
    assert migrate_relationship_properties(
        {"metric": [1, 2], "removed": 3},
        (source_metric, source_removed),
        (target_metric, target_new),
    ) == {"metric": [1, 2]}
    with pytest.raises(RelationshipSchemaChangeBlocked) as caught:
        migrate_relationship_properties(
            {"metric": [99]}, (source_metric,), (target_metric,)
        )
    assert caught.value.property_name == "metric"


@pytest.mark.parametrize(
    "candidate",
    [
        {"value": 1.5},
        {"value": {1: "non-string-key"}},
        {"value": [1, {"nested": 1.5}]},
    ],
)
def test_m2_s02_historical_property_codec_rejects_invalid_carriers(
    candidate: object,
) -> None:
    with pytest.raises(RuntimeError):
        decode_historical_properties(candidate)


def test_m2_s02_historical_property_codec_accepts_exact_carriers() -> None:
    candidate: dict[str, JsonValue] = {
        "null": None,
        "text": "x",
        "integer": 1,
        "boolean": True,
        "empty_list": [],
        "empty_object": {},
        "recursive": ["x", 1, True, None, {"nested": []}],
        "Bad-Key": 1,
    }
    assert decode_historical_properties(candidate) == candidate


@pytest.mark.parametrize(
    "candidate",
    [
        {},
        {"relationship_definition_version": 1},
        {"relationship_definition_version": True, "properties": {}},
    ],
)
def test_m2_s02_relationship_factual_state_requires_exact_shape(
    candidate: object,
) -> None:
    with pytest.raises(RuntimeError):
        decode_relationship_factual_state(candidate)


def test_m3_relationship_factual_state_ignores_extras_and_version_semantics() -> None:
    candidate: dict[str, JsonValue] = {
        "relationship_definition_version": 0,
        "properties": {"nested": [None, {}]},
        "extra": "ignored",
    }
    decoded = decode_relationship_factual_state(candidate)
    assert decoded is not None
    assert decoded.relationship_definition_version == 0
    assert decoded.properties == {"nested": [None, {}]}


async def test_m2_s02_relationship_writer_rejects_invalid_transition_shapes() -> None:
    definition_id = uuid4()
    relationship_id = uuid4()
    before = Relationship(relationship_id, definition_id, (), 1, {"metric": 1})
    same = Relationship(relationship_id, definition_id, (), 1, {"metric": 1})
    changed = Relationship(relationship_id, definition_id, (), 1, {"metric": 2})
    forward = Relationship(relationship_id, definition_id, (), 2, {"metric": 1})
    view = RelationshipLifecycleView(uuid4(), "from", uuid4(), "to", "related")
    store = LifecycleStore(cast(AsyncConnection, object()))
    invalid = (
        (EventKind.RELATIONSHIP_CREATED, before, same),
        (EventKind.RELATIONSHIP_DELETED, before, same),
        (EventKind.RELATIONSHIP_DATA_CHANGE, before, same),
        (EventKind.RELATIONSHIP_DATA_CHANGE, before, forward),
        (EventKind.RELATIONSHIP_SCHEMA_CHANGE, before, changed),
    )
    for kind, old, new in invalid:
        with pytest.raises(RuntimeError):
            await store.insert_relationship_events(
                kind=kind, before=old, after=new, views=(view,)
            )


def test_m2_s02_lifecycle_store_is_the_sole_event_table_sql_owner() -> None:
    root = Path("src/netauto/persistence")
    lifecycle = (root / "lifecycle.py").read_text()
    objects = (root / "objects.py").read_text()
    relationships = (root / "relationships.py").read_text()
    assert "class LifecycleStore" in lifecycle
    assert "class EventKind" in lifecycle
    assert "object_lifecycle_events" not in objects
    assert "object_lifecycle_events" not in relationships
    for forbidden in (
        "insert_intrinsic_event",
        "insert_ownership_event",
        "insert_relationship_events",
        "list_events",
    ):
        assert f"def {forbidden}" not in objects
        assert f"def {forbidden}" not in relationships
