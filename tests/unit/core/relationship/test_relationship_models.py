from __future__ import annotations

from dataclasses import FrozenInstanceError
from uuid import UUID, uuid4

import pytest

from netauto.core.relationship import (
    InvalidRelationshipIdentifier,
    RelationshipDefinition,
)


def _definition(
    *,
    source_template_id: UUID | None = None,
    target_template_id: UUID | None = None,
    forward_name: str = "uses",
    reverse_name: str = "is_used_by",
) -> RelationshipDefinition:
    return RelationshipDefinition(
        id=uuid4(),
        source_template_id=source_template_id or uuid4(),
        target_template_id=target_template_id or uuid4(),
        forward_name=forward_name,
        reverse_name=reverse_name,
    )


def test_valid_relationship_definition_construction() -> None:
    source_id = uuid4()
    target_id = uuid4()
    definition = _definition(
        source_template_id=source_id,
        target_template_id=target_id,
        forward_name="uses",
        reverse_name="is_used_by",
    )

    assert definition.source_template_id == source_id
    assert definition.target_template_id == target_id
    assert definition.forward_name == "uses"
    assert definition.reverse_name == "is_used_by"


def test_relationship_definition_stores_stable_uuid_unchanged() -> None:
    relationship_id = uuid4()
    definition = RelationshipDefinition(
        id=relationship_id,
        source_template_id=uuid4(),
        target_template_id=uuid4(),
        forward_name="connects_to",
        reverse_name="connected_from",
    )

    assert definition.id == relationship_id


def test_same_template_relationship_definition_is_allowed() -> None:
    template_id = uuid4()
    definition = _definition(
        source_template_id=template_id,
        target_template_id=template_id,
    )

    assert definition.source_template_id == definition.target_template_id


@pytest.mark.parametrize(
    "name",
    ["uses", "is_used_by", "connects_to", "connected_from", "manages"],
)
def test_valid_lower_case_semantic_identifiers_are_accepted(name: str) -> None:
    definition = _definition(forward_name=name, reverse_name=name)

    assert definition.forward_name == name
    assert definition.reverse_name == name


@pytest.mark.parametrize("name", ["", "USES", "is used by", "uses-device", "1uses"])
def test_invalid_forward_identifier_is_rejected(name: str) -> None:
    with pytest.raises(InvalidRelationshipIdentifier):
        _definition(forward_name=name)


@pytest.mark.parametrize("name", ["", "USES", "is used by", "uses-device", "1uses"])
def test_invalid_reverse_identifier_is_rejected(name: str) -> None:
    with pytest.raises(InvalidRelationshipIdentifier):
        _definition(reverse_name=name)


def test_relationship_definition_is_immutable() -> None:
    definition = _definition()

    with pytest.raises(FrozenInstanceError):
        definition.forward_name = "manages"  # type: ignore[misc]
