from uuid import UUID, uuid4

import pytest

from netauto.core.relationship import (
    RelationshipDefinition,
    RelationshipDefinitionAlreadyExists,
    RelationshipDefinitionNotFound,
)
from netauto.persistence.memory.relationship_repository import (
    InMemoryRelationshipDefinitionRepository,
)


def _definition(
    *,
    definition_id: UUID | None = None,
    source_template_id: UUID | None = None,
    target_template_id: UUID | None = None,
    forward_name: str = "uses",
    reverse_name: str = "is_used_by",
) -> RelationshipDefinition:
    return RelationshipDefinition(
        id=definition_id or uuid4(),
        source_template_id=source_template_id or uuid4(),
        target_template_id=target_template_id or uuid4(),
        forward_name=forward_name,
        reverse_name=reverse_name,
    )


def test_list_empty() -> None:
    repo = InMemoryRelationshipDefinitionRepository()

    assert repo.list() == ()


def test_add_and_get_round_trip() -> None:
    repo = InMemoryRelationshipDefinitionRepository()
    definition = _definition()

    repo.add(definition)

    assert repo.get(definition.id) == definition


def test_list_is_deterministic_by_uuid_string() -> None:
    repo = InMemoryRelationshipDefinitionRepository()
    low = _definition(definition_id=UUID("00000000-0000-0000-0000-000000000001"))
    high = _definition(definition_id=UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"))
    mid = _definition(definition_id=UUID("11111111-1111-1111-1111-111111111111"))

    repo.add(high)
    repo.add(mid)
    repo.add(low)

    assert repo.list() == (low, mid, high)


def test_get_missing_returns_none() -> None:
    repo = InMemoryRelationshipDefinitionRepository()

    assert repo.get(uuid4()) is None


def test_duplicate_uuid_rejected() -> None:
    repo = InMemoryRelationshipDefinitionRepository()
    definition = _definition(definition_id=uuid4())
    duplicate = _definition(definition_id=definition.id)

    repo.add(definition)

    with pytest.raises(RelationshipDefinitionAlreadyExists):
        repo.add(duplicate)


def test_delete_existing_definition() -> None:
    repo = InMemoryRelationshipDefinitionRepository()
    definition = _definition()
    repo.add(definition)

    repo.delete(definition.id)

    assert repo.get(definition.id) is None
    assert repo.list() == ()


def test_delete_missing_definition_raises_not_found() -> None:
    repo = InMemoryRelationshipDefinitionRepository()

    with pytest.raises(RelationshipDefinitionNotFound):
        repo.delete(uuid4())


def test_repository_does_not_mutate_stored_semantic_state() -> None:
    repo = InMemoryRelationshipDefinitionRepository()
    definition = _definition(forward_name="connects_to", reverse_name="connects_to")

    repo.add(definition)
    loaded = repo.get(definition.id)

    assert loaded is not None
    assert loaded == definition
    assert loaded.forward_name == "connects_to"
    assert loaded.reverse_name == "connects_to"
