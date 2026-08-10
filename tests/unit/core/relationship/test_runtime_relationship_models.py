from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import cast
from uuid import UUID, uuid4

import pytest

from netauto.core.relationship import InvalidRelationship, Relationship


def test_runtime_relationship_construction() -> None:
    relationship_id = uuid4()
    definition_id = uuid4()
    source_object_id = uuid4()
    target_object_id = uuid4()

    relationship = Relationship(
        id=relationship_id,
        relationship_definition_id=definition_id,
        source_object_id=source_object_id,
        target_object_id=target_object_id,
    )

    assert relationship.id == relationship_id
    assert relationship.relationship_definition_id == definition_id
    assert relationship.source_object_id == source_object_id
    assert relationship.target_object_id == target_object_id


def test_runtime_relationship_self_link_is_allowed() -> None:
    object_id = uuid4()

    relationship = Relationship(
        id=uuid4(),
        relationship_definition_id=uuid4(),
        source_object_id=object_id,
        target_object_id=object_id,
    )

    assert relationship.source_object_id == relationship.target_object_id


def test_runtime_relationship_rejects_non_uuid_fields() -> None:
    with pytest.raises(InvalidRelationship):
        Relationship(
            id=cast(UUID, "not-a-uuid"),
            relationship_definition_id=uuid4(),
            source_object_id=uuid4(),
            target_object_id=uuid4(),
        )


def test_runtime_relationship_is_immutable() -> None:
    relationship = Relationship(
        id=uuid4(),
        relationship_definition_id=uuid4(),
        source_object_id=uuid4(),
        target_object_id=uuid4(),
    )

    with pytest.raises(FrozenInstanceError):
        relationship.source_object_id = uuid4()  # type: ignore[misc]
