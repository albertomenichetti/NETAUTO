"""Shared semantic conflict detection for relationship definitions."""

from dataclasses import dataclass
from itertools import combinations
from typing import cast
from uuid import UUID

from netauto.core.objecttemplate import (
    ObjectTemplateInheritanceResolver,
    ObjectTemplateVersion,
    ObjectTemplateVersionLookup,
    ObjectTemplateVersionRef,
)
from netauto.core.relationship.exceptions import RelationshipDefinitionSemanticConflict
from netauto.core.relationship.models import RelationshipDefinition
from netauto.core.relationship.semantics import (
    relationship_definitions_are_semantically_equivalent,
)


@dataclass(frozen=True, slots=True)
class RelationshipDefinitionConflictSnapshot:
    """Exact version snapshot used for effective endpoint overlap analysis."""

    all_versions: tuple[ObjectTemplateVersion, ...]
    usable_versions: tuple[ObjectTemplateVersion, ...]

    def lookup_parent(self, version_ref: ObjectTemplateVersionRef) -> ObjectTemplateVersion | None:
        for version in self.all_versions:
            if (
                version.template_id == version_ref.template_id
                and version.version == version_ref.version
            ):
                return version
        return None


def ensure_relationship_definition_does_not_conflict(
    candidate: RelationshipDefinition,
    *,
    existing_definitions: tuple[RelationshipDefinition, ...],
    snapshot: RelationshipDefinitionConflictSnapshot,
) -> None:
    """Raise when a candidate definition conflicts with any existing definition."""

    for existing in existing_definitions:
        if relationship_definitions_are_semantically_equivalent(candidate, existing):
            raise RelationshipDefinitionSemanticConflict(
                "RelationshipDefinition conflicts semantically with an existing definition."
            )
        if relationship_definitions_conflict(candidate, existing, snapshot=snapshot):
            raise RelationshipDefinitionSemanticConflict(
                "RelationshipDefinition conflicts semantically with an existing definition."
            )


def ensure_relationship_definition_set_has_no_conflicts(
    definitions: tuple[RelationshipDefinition, ...],
    *,
    snapshot: RelationshipDefinitionConflictSnapshot,
) -> None:
    """Raise when any pair of existing definitions conflicts under the snapshot."""

    for left, right in combinations(definitions, 2):
        if relationship_definitions_are_semantically_equivalent(left, right):
            raise RelationshipDefinitionSemanticConflict(
                "RelationshipDefinition conflicts semantically with an existing definition."
            )
        if relationship_definitions_conflict(left, right, snapshot=snapshot):
            raise RelationshipDefinitionSemanticConflict(
                "RelationshipDefinition conflicts semantically with an existing definition."
            )


def relationship_definitions_conflict(
    left: RelationshipDefinition,
    right: RelationshipDefinition,
    *,
    snapshot: RelationshipDefinitionConflictSnapshot,
) -> bool:
    """Return True when two definitions overlap under a snapshot."""

    for (
        left_source_id,
        right_source_id,
        left_target_id,
        right_target_id,
    ) in _matching_orientations(left, right):
        if _endpoint_spaces_overlap(
            left_source_id,
            right_source_id,
            snapshot=snapshot,
        ) and _endpoint_spaces_overlap(
            left_target_id,
            right_target_id,
            snapshot=snapshot,
        ):
            return True
    return False


def _matching_orientations(
    left: RelationshipDefinition,
    right: RelationshipDefinition,
) -> tuple[tuple[UUID, UUID, UUID, UUID], ...]:
    orientations: list[tuple[UUID, UUID, UUID, UUID]] = []
    if left.forward_name == right.forward_name and left.reverse_name == right.reverse_name:
        orientations.append(
            (
                left.source_template_id,
                right.source_template_id,
                left.target_template_id,
                right.target_template_id,
            )
        )
    if left.forward_name == right.reverse_name and left.reverse_name == right.forward_name:
        orientations.append(
            (
                left.source_template_id,
                right.target_template_id,
                left.target_template_id,
                right.source_template_id,
            )
        )
    return tuple(orientations)


def _endpoint_spaces_overlap(
    required_left_template_id: UUID,
    required_right_template_id: UUID,
    *,
    snapshot: RelationshipDefinitionConflictSnapshot,
) -> bool:
    resolver = ObjectTemplateInheritanceResolver()
    parent_lookup: ObjectTemplateVersionLookup = cast(
        ObjectTemplateVersionLookup,
        snapshot.lookup_parent,
    )
    for version in snapshot.usable_versions:
        if resolver.is_same_or_descendant_template(
            version,
            required_template_id=required_left_template_id,
            parent_lookup=parent_lookup,
        ) and resolver.is_same_or_descendant_template(
            version,
            required_template_id=required_right_template_id,
            parent_lookup=parent_lookup,
        ):
            return True
    return False
