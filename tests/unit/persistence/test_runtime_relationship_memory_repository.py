from uuid import UUID, uuid4

import pytest

from netauto.core.relationship import (
    Relationship,
    RelationshipAlreadyExists,
    RelationshipNotFound,
)
from netauto.persistence.memory.relationship_repository import InMemoryRelationshipRepository


def _relationship(
    *,
    relationship_id: UUID | None = None,
    relationship_definition_id: UUID | None = None,
    source_object_id: UUID | None = None,
    target_object_id: UUID | None = None,
) -> Relationship:
    return Relationship(
        id=relationship_id or uuid4(),
        relationship_definition_id=relationship_definition_id or uuid4(),
        source_object_id=source_object_id or uuid4(),
        target_object_id=target_object_id or uuid4(),
    )


def test_list_empty() -> None:
    repo = InMemoryRelationshipRepository()

    assert repo.list() == ()


def test_add_get_and_get_by_endpoints_round_trip() -> None:
    repo = InMemoryRelationshipRepository()
    relationship = _relationship()

    repo.add(relationship)

    assert repo.get(relationship.id) == relationship
    assert (
        repo.get_by_endpoints(
            relationship.relationship_definition_id,
            relationship.source_object_id,
            relationship.target_object_id,
        )
        == relationship
    )


def test_list_is_deterministic_by_uuid_string() -> None:
    repo = InMemoryRelationshipRepository()
    low = _relationship(relationship_id=UUID("00000000-0000-0000-0000-000000000001"))
    mid = _relationship(relationship_id=UUID("11111111-1111-1111-1111-111111111111"))
    high = _relationship(relationship_id=UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"))

    repo.add(high)
    repo.add(mid)
    repo.add(low)

    assert repo.list() == (low, mid, high)


def test_duplicate_uuid_is_rejected() -> None:
    repo = InMemoryRelationshipRepository()
    relationship = _relationship(relationship_id=uuid4())
    duplicate = _relationship(
        relationship_id=relationship.id,
        relationship_definition_id=uuid4(),
    )

    repo.add(relationship)

    with pytest.raises(RelationshipAlreadyExists):
        repo.add(duplicate)


def test_duplicate_canonical_triple_is_rejected() -> None:
    repo = InMemoryRelationshipRepository()
    relationship = _relationship()
    duplicate = _relationship(
        relationship_definition_id=relationship.relationship_definition_id,
        source_object_id=relationship.source_object_id,
        target_object_id=relationship.target_object_id,
    )

    repo.add(relationship)

    with pytest.raises(RelationshipAlreadyExists):
        repo.add(duplicate)


def test_same_object_pair_with_different_definitions_is_allowed() -> None:
    repo = InMemoryRelationshipRepository()
    source_object_id = uuid4()
    target_object_id = uuid4()
    first = _relationship(
        relationship_definition_id=uuid4(),
        source_object_id=source_object_id,
        target_object_id=target_object_id,
    )
    second = _relationship(
        relationship_definition_id=uuid4(),
        source_object_id=source_object_id,
        target_object_id=target_object_id,
    )

    repo.add(first)
    repo.add(second)

    assert repo.list() == tuple(sorted((first, second), key=lambda item: str(item.id)))


def test_self_link_persists() -> None:
    repo = InMemoryRelationshipRepository()
    object_id = uuid4()
    relationship = _relationship(
        source_object_id=object_id,
        target_object_id=object_id,
    )

    repo.add(relationship)

    assert repo.get(relationship.id) == relationship


def test_delete_existing_relationship() -> None:
    repo = InMemoryRelationshipRepository()
    relationship = _relationship()
    repo.add(relationship)

    repo.delete(relationship.id)

    assert repo.get(relationship.id) is None
    assert repo.get_by_endpoints(
        relationship.relationship_definition_id,
        relationship.source_object_id,
        relationship.target_object_id,
    ) is None


def test_delete_missing_relationship_raises_not_found() -> None:
    repo = InMemoryRelationshipRepository()

    with pytest.raises(RelationshipNotFound):
        repo.delete(uuid4())
