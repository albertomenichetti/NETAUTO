from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from netauto.core.objecttemplate import (
    ObjectTemplateInheritanceCycle,
    ObjectTemplateParentNotFound,
    ObjectTemplateSelfInheritance,
    ObjectTemplateVersion,
    ObjectTemplateVersionRef,
    ObjectTemplateVersionStatus,
)
from netauto.core.relationship import (
    RelationshipDefinition,
    RelationshipDefinitionConflictSnapshot,
    RelationshipDefinitionSemanticConflict,
    ensure_relationship_definition_does_not_conflict,
    ensure_relationship_definition_set_has_no_conflicts,
    relationship_definitions_conflict,
)


def _definition(
    *,
    source_template_id: UUID,
    target_template_id: UUID,
    forward_name: str = "uses",
    reverse_name: str = "is_used_by",
) -> RelationshipDefinition:
    return RelationshipDefinition(
        id=uuid4(),
        source_template_id=source_template_id,
        target_template_id=target_template_id,
        forward_name=forward_name,
        reverse_name=reverse_name,
    )


def _version(
    template_id: UUID,
    version: int,
    *,
    status: ObjectTemplateVersionStatus = ObjectTemplateVersionStatus.PUBLISHED,
    parent: ObjectTemplateVersionRef | None = None,
) -> ObjectTemplateVersion:
    return ObjectTemplateVersion(
        template_id=template_id,
        version=version,
        status=status,
        parent=parent,
    )


def _snapshot(
    *versions: ObjectTemplateVersion,
) -> RelationshipDefinitionConflictSnapshot:
    return RelationshipDefinitionConflictSnapshot(
        all_versions=versions,
        usable_versions=tuple(
            version
            for version in versions
            if version.status
            in (
                ObjectTemplateVersionStatus.PUBLISHED,
                ObjectTemplateVersionStatus.DEPRECATED,
            )
        ),
    )


def test_exact_duplicate_always_conflicts() -> None:
    source_id = uuid4()
    target_id = uuid4()
    candidate = _definition(source_template_id=source_id, target_template_id=target_id)
    existing = _definition(source_template_id=source_id, target_template_id=target_id)

    with pytest.raises(RelationshipDefinitionSemanticConflict):
        ensure_relationship_definition_does_not_conflict(
            candidate,
            existing_definitions=(existing,),
            snapshot=_snapshot(),
        )


def test_inverse_duplicate_always_conflicts() -> None:
    source_id = uuid4()
    target_id = uuid4()
    candidate = _definition(
        source_template_id=target_id,
        target_template_id=source_id,
        forward_name="is_used_by",
        reverse_name="uses",
    )
    existing = _definition(source_template_id=source_id, target_template_id=target_id)

    with pytest.raises(RelationshipDefinitionSemanticConflict):
        ensure_relationship_definition_does_not_conflict(
            candidate,
            existing_definitions=(existing,),
            snapshot=_snapshot(),
        )


def test_direct_source_and_target_overlap_conflict() -> None:
    source_id = uuid4()
    target_id = uuid4()
    definition = _definition(source_template_id=source_id, target_template_id=target_id)
    version = _version(source_id, 1)
    target_version = _version(target_id, 1)

    assert relationship_definitions_conflict(
        definition,
        _definition(source_template_id=source_id, target_template_id=target_id),
        snapshot=_snapshot(version, target_version),
    )


def test_inverse_orientation_overlap_conflict() -> None:
    source_id = uuid4()
    target_id = uuid4()
    existing = _definition(source_template_id=source_id, target_template_id=target_id)
    candidate = _definition(
        source_template_id=target_id,
        target_template_id=source_id,
        forward_name="is_used_by",
        reverse_name="uses",
    )
    source_version = _version(source_id, 1)
    target_version = _version(target_id, 1)

    assert relationship_definitions_conflict(
        candidate,
        existing,
        snapshot=_snapshot(source_version, target_version),
    )


def test_no_source_overlap_is_not_conflict() -> None:
    left_source = uuid4()
    right_source = uuid4()
    target_id = uuid4()
    left = _definition(source_template_id=left_source, target_template_id=target_id)
    right = _definition(source_template_id=right_source, target_template_id=target_id)

    assert not relationship_definitions_conflict(
        left,
        right,
        snapshot=_snapshot(
            _version(left_source, 1),
            _version(right_source, 1),
            _version(target_id, 1),
        ),
    )


def test_no_target_overlap_is_not_conflict() -> None:
    source_id = uuid4()
    left_target = uuid4()
    right_target = uuid4()
    left = _definition(source_template_id=source_id, target_template_id=left_target)
    right = _definition(source_template_id=source_id, target_template_id=right_target)

    assert not relationship_definitions_conflict(
        left,
        right,
        snapshot=_snapshot(
            _version(source_id, 1),
            _version(left_target, 1),
            _version(right_target, 1),
        ),
    )


def test_different_semantics_are_not_conflicts() -> None:
    source_id = uuid4()
    target_id = uuid4()
    left = _definition(source_template_id=source_id, target_template_id=target_id)
    right = _definition(
        source_template_id=source_id,
        target_template_id=target_id,
        forward_name="manages",
        reverse_name="managed_by",
    )

    assert not relationship_definitions_conflict(
        left,
        right,
        snapshot=_snapshot(_version(source_id, 1), _version(target_id, 1)),
    )


def test_symmetric_names_conflict_when_any_orientation_overlaps() -> None:
    source_id = uuid4()
    child_source_id = uuid4()
    target_id = uuid4()
    existing = _definition(
        source_template_id=source_id,
        target_template_id=target_id,
        forward_name="connects_to",
        reverse_name="connects_to",
    )
    candidate = _definition(
        source_template_id=target_id,
        target_template_id=child_source_id,
        forward_name="connects_to",
        reverse_name="connects_to",
    )
    root = _version(source_id, 1)
    child = _version(
        child_source_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=source_id, version=1),
    )
    target = _version(target_id, 1)

    assert relationship_definitions_conflict(
        candidate,
        existing,
        snapshot=_snapshot(root, child, target),
    )


def test_deprecated_versions_participate_and_draft_versions_do_not() -> None:
    source_id = uuid4()
    child_source_id = uuid4()
    target_id = uuid4()
    existing = _definition(source_template_id=source_id, target_template_id=target_id)
    candidate = _definition(source_template_id=child_source_id, target_template_id=target_id)
    root = _version(source_id, 1)
    deprecated_child = _version(
        child_source_id,
        1,
        status=ObjectTemplateVersionStatus.DEPRECATED,
        parent=ObjectTemplateVersionRef(template_id=source_id, version=1),
    )
    draft_child = _version(
        child_source_id,
        2,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=ObjectTemplateVersionRef(template_id=source_id, version=1),
    )
    target = _version(target_id, 1)

    assert relationship_definitions_conflict(
        candidate,
        existing,
        snapshot=_snapshot(root, deprecated_child, draft_child, target),
    )


def test_exact_version_ancestry_is_evaluated_per_usable_version() -> None:
    ancestor_id = uuid4()
    router_id = uuid4()
    target_id = uuid4()
    existing = _definition(source_template_id=ancestor_id, target_template_id=target_id)
    candidate = _definition(source_template_id=router_id, target_template_id=target_id)
    ancestor = _version(ancestor_id, 1)
    router_v1 = _version(
        router_id,
        1,
        status=ObjectTemplateVersionStatus.DEPRECATED,
        parent=ObjectTemplateVersionRef(template_id=ancestor_id, version=1),
    )
    router_v2 = _version(router_id, 2, status=ObjectTemplateVersionStatus.PUBLISHED)
    target = _version(target_id, 1)

    assert relationship_definitions_conflict(
        candidate,
        existing,
        snapshot=_snapshot(ancestor, router_v1, router_v2, target),
    )


def test_relationship_definition_set_conflict_detection_uses_pairwise_overlap() -> None:
    source_id = uuid4()
    child_source_id = uuid4()
    target_id = uuid4()
    root = _version(source_id, 1)
    child = _version(
        child_source_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=source_id, version=1),
    )
    target = _version(target_id, 1)
    definitions = (
        _definition(source_template_id=source_id, target_template_id=target_id),
        _definition(source_template_id=child_source_id, target_template_id=target_id),
    )

    with pytest.raises(RelationshipDefinitionSemanticConflict):
        ensure_relationship_definition_set_has_no_conflicts(
            definitions,
            snapshot=_snapshot(root, child, target),
        )


def test_missing_parent_error_propagates() -> None:
    source_id = uuid4()
    child_source_id = uuid4()
    target_id = uuid4()
    existing = _definition(source_template_id=source_id, target_template_id=target_id)
    candidate = _definition(source_template_id=child_source_id, target_template_id=target_id)
    child = _version(
        child_source_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=source_id, version=1),
    )
    target = _version(target_id, 1)

    with pytest.raises(ObjectTemplateParentNotFound):
        relationship_definitions_conflict(
            candidate,
            existing,
            snapshot=_snapshot(child, target),
        )


def test_self_inheritance_error_propagates() -> None:
    source_id = uuid4()
    target_id = uuid4()
    existing = _definition(source_template_id=source_id, target_template_id=target_id)
    candidate = _definition(source_template_id=source_id, target_template_id=target_id)
    source = _version(
        source_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=source_id, version=1),
    )
    target = _version(target_id, 1)

    with pytest.raises(ObjectTemplateSelfInheritance):
        relationship_definitions_conflict(
            candidate,
            existing,
            snapshot=_snapshot(source, target),
        )


def test_inheritance_cycle_error_propagates() -> None:
    source_id = uuid4()
    child_source_id = uuid4()
    target_id = uuid4()
    existing = _definition(source_template_id=source_id, target_template_id=target_id)
    candidate = _definition(source_template_id=child_source_id, target_template_id=target_id)
    source = _version(
        source_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=child_source_id, version=1),
    )
    child = _version(
        child_source_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=source_id, version=1),
    )
    target = _version(target_id, 1)

    with pytest.raises(ObjectTemplateInheritanceCycle):
        relationship_definitions_conflict(
            candidate,
            existing,
            snapshot=_snapshot(source, child, target),
        )
