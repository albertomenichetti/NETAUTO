"""Pure factual Relationship closure and semantic-view coverage."""

from uuid import uuid4

import pytest

from netauto.domain.relationships import (
    Relationship,
    RelationshipPerspective,
    RelationshipValidationError,
    derive_runtime_closure,
    new_non_symmetric_definition,
    new_symmetric_definition,
    relationship_views,
    validate_relationship,
)


def _keys(value: Relationship) -> set[tuple[object, object, object]]:
    return {
        (item.resolution_id, item.from_object_id, item.to_object_id)
        for item in value.resolutions
    }


def test_non_symmetric_closure_preserves_selected_factual_orientation() -> None:
    root = uuid4()
    child = uuid4()
    definition = new_non_symmetric_definition(
        (
            RelationshipPerspective(root, "manages"),
            RelationshipPerspective(root, "managed_by"),
        )
    )
    selected = next(item for item in definition.resolutions if item.name == "manages")
    first = uuid4()
    second = uuid4()
    relationship_id = uuid4()
    resolutions = derive_runtime_closure(
        definition,
        selected_resolution_id=selected.id,
        from_object_id=first,
        from_template_id=child,
        to_object_id=second,
        to_template_id=child,
        parent_by_id={root: None, child: root},
        relationship_id=relationship_id,
    )
    value = Relationship(relationship_id, definition.id, resolutions)
    assert len(resolutions) == 2
    assert (selected.id, first, second) in _keys(value)
    assert (selected.id, second, first) not in _keys(value)


def test_non_symmetric_same_template_self_loop_keeps_two_names() -> None:
    template_id = uuid4()
    definition = new_non_symmetric_definition(
        (
            RelationshipPerspective(template_id, "parent_of"),
            RelationshipPerspective(template_id, "child_of"),
        )
    )
    object_id = uuid4()
    relationship_id = uuid4()
    resolutions = derive_runtime_closure(
        definition,
        selected_resolution_id=definition.resolutions[0].id,
        from_object_id=object_id,
        from_template_id=template_id,
        to_object_id=object_id,
        to_template_id=template_id,
        parent_by_id={template_id: None},
        relationship_id=relationship_id,
    )
    value = Relationship(relationship_id, definition.id, resolutions)
    assert len(resolutions) == 2
    assert {item.name for item in relationship_views(value, definition)} == {
        "parent_of",
        "child_of",
    }


def test_symmetric_same_template_distinct_pair_and_self_loop() -> None:
    template_id = uuid4()
    definition = new_symmetric_definition((template_id, template_id), "peers")
    selected = definition.resolutions[0]
    first = uuid4()
    second = uuid4()
    distinct = derive_runtime_closure(
        definition,
        selected_resolution_id=selected.id,
        from_object_id=first,
        from_template_id=template_id,
        to_object_id=second,
        to_template_id=template_id,
        parent_by_id={template_id: None},
    )
    self_loop = derive_runtime_closure(
        definition,
        selected_resolution_id=selected.id,
        from_object_id=first,
        from_template_id=template_id,
        to_object_id=first,
        to_template_id=template_id,
        parent_by_id={template_id: None},
    )
    assert len(distinct) == 2
    assert len(self_loop) == 1


def test_symmetric_disjoint_and_inheritance_overlap_closure_shapes() -> None:
    root = uuid4()
    child = uuid4()
    unrelated = uuid4()
    first = uuid4()
    second = uuid4()
    disjoint = new_symmetric_definition((root, unrelated), "connected")
    disjoint_rows = derive_runtime_closure(
        disjoint,
        selected_resolution_id=disjoint.resolutions[0].id,
        from_object_id=first,
        from_template_id=disjoint.resolutions[0].from_template_id,
        to_object_id=second,
        to_template_id=disjoint.resolutions[0].to_template_id,
        parent_by_id={root: None, child: root, unrelated: None},
    )
    assert len(disjoint_rows) == 2

    overlap = new_symmetric_definition((root, child), "related")
    overlap_rows = derive_runtime_closure(
        overlap,
        selected_resolution_id=overlap.resolutions[0].id,
        from_object_id=first,
        from_template_id=child,
        to_object_id=second,
        to_template_id=child,
        parent_by_id={root: None, child: root},
    )
    value = Relationship(overlap_rows[0].relationship_id, overlap.id, overlap_rows)
    assert len(overlap_rows) == 4
    assert len(relationship_views(value, overlap)) == 2


def test_endpoint_admission_uses_stable_lineage_and_reports_operand() -> None:
    first_template = uuid4()
    second_template = uuid4()
    incompatible = uuid4()
    definition = new_symmetric_definition(
        (first_template, second_template), "connected"
    )
    selected = definition.resolutions[0]
    with pytest.raises(RelationshipValidationError) as caught:
        derive_runtime_closure(
            definition,
            selected_resolution_id=selected.id,
            from_object_id=uuid4(),
            from_template_id=incompatible,
            to_object_id=uuid4(),
            to_template_id=selected.to_template_id,
            parent_by_id={
                first_template: None,
                second_template: None,
                incompatible: None,
            },
        )
    assert caught.value.path == "from_object_id"
    assert caught.value.rule == "incompatible_template_lineage"


def test_persisted_incomplete_closure_is_rejected() -> None:
    template_id = uuid4()
    definition = new_symmetric_definition((template_id, template_id), "peers")
    first = uuid4()
    second = uuid4()
    rows = derive_runtime_closure(
        definition,
        selected_resolution_id=definition.resolutions[0].id,
        from_object_id=first,
        from_template_id=template_id,
        to_object_id=second,
        to_template_id=template_id,
        parent_by_id={template_id: None},
    )
    malformed = Relationship(rows[0].relationship_id, definition.id, rows[:1])
    with pytest.raises(RelationshipValidationError) as caught:
        validate_relationship(
            malformed,
            definition,
            parent_by_id={template_id: None},
            template_by_object_id={first: template_id, second: template_id},
        )
    assert caught.value.rule == "incomplete_closure"
