"""Pure RelationshipDefinition aggregate and conflict semantics."""

from dataclasses import replace
from uuid import UUID, uuid4

import pytest

from netauto.domain.datatypes import VersionStatus
from netauto.domain.objecttemplates import ValueMode
from netauto.domain.relationships import (
    RelationshipDefinition,
    RelationshipDefinitionProperty,
    RelationshipDefinitionValidationError,
    RelationshipDefinitionVersion,
    RelationshipPerspective,
    RelationshipResolution,
    ResolutionRename,
    first_conflict,
    new_non_symmetric_definition,
    new_symmetric_definition,
    rename_non_symmetric,
    rename_symmetric,
    semantic_signature,
    validate_definition,
    validate_lineage_graph,
    validate_relationship_definition_version,
    validate_relationship_property_history,
)


def test_non_symmetric_derivation_is_order_independent_and_reciprocal() -> None:
    first_template = uuid4()
    second_template = uuid4()
    perspectives = (
        RelationshipPerspective(first_template, "hosts"),
        RelationshipPerspective(second_template, "hosted_by"),
    )
    first = new_non_symmetric_definition(perspectives)
    second = new_non_symmetric_definition((perspectives[1], perspectives[0]))

    assert semantic_signature(first) == semantic_signature(second)
    assert len(first.resolutions) == 2
    assert {
        (item.from_template_id, item.to_template_id, item.name)
        for item in first.resolutions
    } == {
        (first_template, second_template, "hosts"),
        (second_template, first_template, "hosted_by"),
    }


def test_non_symmetric_same_template_keeps_two_named_perspectives() -> None:
    template_id = uuid4()
    value = new_non_symmetric_definition(
        (
            RelationshipPerspective(template_id, "manages"),
            RelationshipPerspective(template_id, "managed_by"),
        )
    )
    assert len(value.resolutions) == 2
    assert {item.name for item in value.resolutions} == {"manages", "managed_by"}
    assert all(
        item.from_template_id == item.to_template_id == template_id
        for item in value.resolutions
    )


def test_symmetric_derivation_has_frozen_same_and_different_template_shapes() -> None:
    first_template = uuid4()
    second_template = uuid4()
    same = new_symmetric_definition((first_template, first_template), "peer")
    different = new_symmetric_definition((first_template, second_template), "connected")
    reversed_input = new_symmetric_definition(
        (second_template, first_template), "connected"
    )

    assert len(same.resolutions) == 1
    assert len(different.resolutions) == 2
    assert semantic_signature(different) == semantic_signature(reversed_input)


def test_semantic_signature_excludes_all_stable_ids() -> None:
    value = new_symmetric_definition((uuid4(), uuid4()), "connected")
    replacement_id = uuid4()
    replaced = RelationshipDefinition(
        replacement_id,
        value.symmetric,
        tuple(
            replace(
                item,
                id=uuid4(),
                relationship_definition_id=replacement_id,
            )
            for item in value.resolutions
        ),
    )
    assert semantic_signature(value) == semantic_signature(replaced)


def test_complete_rename_preserves_ids_endpoints_and_membership() -> None:
    value = new_non_symmetric_definition(
        (
            RelationshipPerspective(uuid4(), "contains"),
            RelationshipPerspective(uuid4(), "contained_by"),
        )
    )
    first, second = value.resolutions
    renamed = rename_non_symmetric(
        value,
        (
            ResolutionRename(second.id, "member_of"),
            ResolutionRename(first.id, "members"),
        ),
    )
    assert {
        (item.id, item.from_template_id, item.to_template_id)
        for item in renamed.resolutions
    } == {
        (item.id, item.from_template_id, item.to_template_id)
        for item in value.resolutions
    }
    assert {item.name for item in renamed.resolutions} == {"members", "member_of"}

    symmetric = new_symmetric_definition((uuid4(), uuid4()), "old_name")
    symmetric_renamed = rename_symmetric(symmetric, "new_name")
    assert {item.name for item in symmetric_renamed.resolutions} == {"new_name"}
    assert {item.id for item in symmetric_renamed.resolutions} == {
        item.id for item in symmetric.resolutions
    }


@pytest.mark.parametrize(
    ("value", "rule"),
    [
        (
            RelationshipDefinition(uuid4(), False, ()),
            "non_symmetric_requires_two_resolutions",
        ),
        (
            RelationshipDefinition(uuid4(), True, ()),
            "symmetric_requires_one_or_two_resolutions",
        ),
    ],
)
def test_incomplete_aggregate_shapes_are_rejected(
    value: RelationshipDefinition, rule: str
) -> None:
    with pytest.raises(RelationshipDefinitionValidationError) as caught:
        validate_definition(value)
    assert caught.value.rule == rule


def test_malformed_reciprocal_and_name_shapes_are_rejected() -> None:
    definition_id = uuid4()
    first_template = uuid4()
    second_template = uuid4()
    third_template = uuid4()
    malformed = RelationshipDefinition(
        definition_id,
        False,
        (
            RelationshipResolution(
                uuid4(), definition_id, first_template, second_template, "uses"
            ),
            RelationshipResolution(
                uuid4(), definition_id, third_template, first_template, "used_by"
            ),
        ),
    )
    with pytest.raises(RelationshipDefinitionValidationError) as caught:
        validate_definition(malformed)
    assert caught.value.rule == "non_symmetric_resolutions_must_be_reciprocal"


def test_cross_definition_conflict_requires_name_and_both_space_overlaps() -> None:
    root = uuid4()
    child = uuid4()
    other = uuid4()
    parent_by_id = {root: None, child: root, other: None}
    existing = new_symmetric_definition((root, root), "linked")
    equality = new_symmetric_definition((root, root), "linked")
    descendant = new_symmetric_definition((child, child), "linked")
    different_name = new_symmetric_definition((child, child), "other_name")
    only_from_overlap = new_symmetric_definition((child, other), "linked")

    assert first_conflict(equality, existing, parent_by_id) is not None
    assert first_conflict(descendant, existing, parent_by_id) is not None
    assert first_conflict(existing, descendant, parent_by_id) is not None
    assert first_conflict(different_name, existing, parent_by_id) is None
    assert first_conflict(only_from_overlap, existing, parent_by_id) is None


def test_same_definition_resolutions_are_not_cross_conflicted() -> None:
    template_id = uuid4()
    value = new_non_symmetric_definition(
        (
            RelationshipPerspective(template_id, "parent"),
            RelationshipPerspective(template_id, "child"),
        )
    )
    assert first_conflict(value, value, {template_id: None}) is None


def test_lineage_graph_corruption_is_rejected_defensively() -> None:
    first = uuid4()
    second = uuid4()
    with pytest.raises(RelationshipDefinitionValidationError) as cycle:
        validate_lineage_graph({first: second, second: first})
    assert cycle.value.rule == "persisted_inheritance_cycle"
    with pytest.raises(RelationshipDefinitionValidationError) as missing:
        validate_lineage_graph({first: second})
    assert missing.value.rule == "persisted_lineage_dependency_missing"


def _rdv_property(
    name: str,
    position: int,
    datatype_id: UUID,
    value_mode: ValueMode = ValueMode.SCALAR,
) -> RelationshipDefinitionProperty:
    return RelationshipDefinitionProperty(
        name,
        position,
        datatype_id,
        1,
        value_mode,
    )


def test_rdv_declaration_shape_and_complete_history_rules() -> None:
    definition_id = uuid4()
    datatype_id = uuid4()
    published = RelationshipDefinitionVersion(
        definition_id,
        1,
        1,
        VersionStatus.PUBLISHED,
        (_rdv_property("value", 1, datatype_id),),
    )
    widened = RelationshipDefinitionVersion(
        definition_id,
        3,
        2,
        VersionStatus.DRAFT,
        (_rdv_property("value", 2, datatype_id, ValueMode.LIST),),
    )
    validate_relationship_property_history(widened, (published,))

    narrowed = RelationshipDefinitionVersion(
        definition_id,
        2,
        1,
        VersionStatus.DRAFT,
        (_rdv_property("value", 1, datatype_id),),
    )
    with pytest.raises(RelationshipDefinitionValidationError) as narrowing:
        validate_relationship_property_history(narrowed, (published, widened))
    assert narrowing.value.rule == "list_to_scalar_forbidden"

    rebound = RelationshipDefinitionVersion(
        definition_id,
        4,
        1,
        VersionStatus.DRAFT,
        (_rdv_property("value", 1, uuid4()),),
    )
    with pytest.raises(RelationshipDefinitionValidationError) as lineage:
        validate_relationship_property_history(rebound, (published,))
    assert lineage.value.rule == "property_datatype_lineage_changed"


@pytest.mark.parametrize(
    "properties",
    [
        (
            _rdv_property("duplicate", 1, uuid4()),
            _rdv_property("duplicate", 2, uuid4()),
        ),
        (
            _rdv_property("first", 1, uuid4()),
            _rdv_property("second", 1, uuid4()),
        ),
        (_rdv_property("Invalid", 1, uuid4()),),
    ],
)
def test_rdv_declaration_rejects_duplicate_and_noncanonical_identity(
    properties: tuple[RelationshipDefinitionProperty, ...],
) -> None:
    candidate = RelationshipDefinitionVersion(
        uuid4(), 1, 1, VersionStatus.DRAFT, properties
    )
    with pytest.raises(RelationshipDefinitionValidationError):
        validate_relationship_definition_version(candidate)
