"""Plain-Python RelationshipDefinition aggregate semantics."""

import re
from collections.abc import Mapping
from dataclasses import dataclass
from uuid import UUID, uuid4

_IDENTIFIER = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")

type ResolutionSemanticKey = tuple[UUID, UUID, str]
type DefinitionSemanticSignature = tuple[bool, frozenset[ResolutionSemanticKey]]


@dataclass(frozen=True, slots=True)
class RelationshipResolution:
    id: UUID
    relationship_definition_id: UUID
    from_template_id: UUID
    to_template_id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class RelationshipDefinition:
    id: UUID
    symmetric: bool
    resolutions: tuple[RelationshipResolution, ...]


@dataclass(frozen=True, slots=True)
class RelationshipPerspective:
    template_id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class ResolutionRename:
    resolution_id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class RelationshipCapability:
    resolution_id: UUID
    relationship_definition_id: UUID
    name: str
    from_template_id: UUID
    to_template_id: UUID


class RelationshipDefinitionValidationError(ValueError):
    def __init__(self, path: str, rule: str) -> None:
        self.path = path
        self.rule = rule
        super().__init__(f"{path}: {rule}")


def validate_relationship_name(name: str, path: str = "name") -> None:
    if _IDENTIFIER.fullmatch(name) is None:
        raise RelationshipDefinitionValidationError(path, "invalid_identifier")


def validate_definition(value: RelationshipDefinition) -> None:
    resolutions = value.resolutions
    if len({item.id for item in resolutions}) != len(resolutions):
        raise RelationshipDefinitionValidationError(
            "resolutions", "duplicate_resolution_id"
        )
    if any(item.relationship_definition_id != value.id for item in resolutions):
        raise RelationshipDefinitionValidationError(
            "resolutions", "definition_membership_mismatch"
        )
    for item in resolutions:
        validate_relationship_name(item.name, f"resolutions.{item.id}.name")

    if not value.symmetric:
        if len(resolutions) != 2:
            raise RelationshipDefinitionValidationError(
                "resolutions", "non_symmetric_requires_two_resolutions"
            )
        first, second = resolutions
        if (
            first.from_template_id != second.to_template_id
            or first.to_template_id != second.from_template_id
        ):
            raise RelationshipDefinitionValidationError(
                "resolutions", "non_symmetric_resolutions_must_be_reciprocal"
            )
        if first.name == second.name:
            raise RelationshipDefinitionValidationError(
                "resolutions", "non_symmetric_names_must_be_distinct"
            )
        return

    if len(resolutions) == 1:
        only = resolutions[0]
        if only.from_template_id != only.to_template_id:
            raise RelationshipDefinitionValidationError(
                "resolutions", "single_symmetric_resolution_requires_same_template"
            )
        return
    if len(resolutions) != 2:
        raise RelationshipDefinitionValidationError(
            "resolutions", "symmetric_requires_one_or_two_resolutions"
        )
    first, second = resolutions
    if (
        first.from_template_id == first.to_template_id
        or first.from_template_id != second.to_template_id
        or first.to_template_id != second.from_template_id
    ):
        raise RelationshipDefinitionValidationError(
            "resolutions", "symmetric_resolutions_must_be_distinct_reciprocals"
        )
    if first.name != second.name:
        raise RelationshipDefinitionValidationError(
            "resolutions", "symmetric_names_must_match"
        )


def new_non_symmetric_definition(
    perspectives: tuple[RelationshipPerspective, RelationshipPerspective],
) -> RelationshipDefinition:
    for index, perspective in enumerate(perspectives):
        validate_relationship_name(perspective.name, f"perspectives.{index}.name")
    if perspectives[0].name == perspectives[1].name:
        raise RelationshipDefinitionValidationError(
            "perspectives", "non_symmetric_names_must_be_distinct"
        )
    first, second = sorted(
        perspectives, key=lambda item: (item.template_id.int, item.name)
    )
    definition_id = uuid4()
    value = RelationshipDefinition(
        definition_id,
        False,
        (
            RelationshipResolution(
                uuid4(),
                definition_id,
                first.template_id,
                second.template_id,
                first.name,
            ),
            RelationshipResolution(
                uuid4(),
                definition_id,
                second.template_id,
                first.template_id,
                second.name,
            ),
        ),
    )
    validate_definition(value)
    return value


def new_symmetric_definition(
    endpoint_template_ids: tuple[UUID, UUID], name: str
) -> RelationshipDefinition:
    validate_relationship_name(name)
    first, second = sorted(endpoint_template_ids, key=lambda item: item.int)
    definition_id = uuid4()
    resolutions = [RelationshipResolution(uuid4(), definition_id, first, second, name)]
    if first != second:
        resolutions.append(
            RelationshipResolution(uuid4(), definition_id, second, first, name)
        )
    value = RelationshipDefinition(definition_id, True, tuple(resolutions))
    validate_definition(value)
    return value


def rename_non_symmetric(
    value: RelationshipDefinition,
    updates: tuple[ResolutionRename, ResolutionRename],
) -> RelationshipDefinition:
    validate_definition(value)
    if value.symmetric:
        raise RelationshipDefinitionValidationError(
            "resolutions", "rename_shape_does_not_match_symmetric_definition"
        )
    update_ids = {item.resolution_id for item in updates}
    current_ids = {item.id for item in value.resolutions}
    if len(update_ids) != 2 or update_ids != current_ids:
        raise RelationshipDefinitionValidationError(
            "resolutions", "rename_must_cover_complete_resolution_set"
        )
    names = {item.resolution_id: item.name for item in updates}
    renamed = RelationshipDefinition(
        value.id,
        value.symmetric,
        tuple(
            RelationshipResolution(
                item.id,
                item.relationship_definition_id,
                item.from_template_id,
                item.to_template_id,
                names[item.id],
            )
            for item in value.resolutions
        ),
    )
    validate_definition(renamed)
    return renamed


def rename_symmetric(
    value: RelationshipDefinition, name: str
) -> RelationshipDefinition:
    validate_definition(value)
    if not value.symmetric:
        raise RelationshipDefinitionValidationError(
            "name", "rename_shape_does_not_match_non_symmetric_definition"
        )
    renamed = RelationshipDefinition(
        value.id,
        value.symmetric,
        tuple(
            RelationshipResolution(
                item.id,
                item.relationship_definition_id,
                item.from_template_id,
                item.to_template_id,
                name,
            )
            for item in value.resolutions
        ),
    )
    validate_definition(renamed)
    return renamed


def semantic_signature(value: RelationshipDefinition) -> DefinitionSemanticSignature:
    validate_definition(value)
    return (
        value.symmetric,
        frozenset(
            (item.from_template_id, item.to_template_id, item.name)
            for item in value.resolutions
        ),
    )


def lineage_is_ancestor(
    parent_by_id: Mapping[UUID, UUID | None], ancestor_id: UUID, descendant_id: UUID
) -> bool:
    current: UUID | None = descendant_id
    seen: set[UUID] = set()
    while current is not None:
        if current in seen:
            raise RelationshipDefinitionValidationError(
                "lineage", "persisted_inheritance_cycle"
            )
        seen.add(current)
        if current == ancestor_id:
            return True
        if current not in parent_by_id:
            raise RelationshipDefinitionValidationError(
                "lineage", "persisted_lineage_dependency_missing"
            )
        current = parent_by_id[current]
    return False


def validate_lineage_graph(parent_by_id: Mapping[UUID, UUID | None]) -> None:
    for lineage_id in parent_by_id:
        current: UUID | None = lineage_id
        seen: set[UUID] = set()
        while current is not None:
            if current in seen:
                raise RelationshipDefinitionValidationError(
                    "lineage", "persisted_inheritance_cycle"
                )
            seen.add(current)
            if current not in parent_by_id:
                raise RelationshipDefinitionValidationError(
                    "lineage", "persisted_lineage_dependency_missing"
                )
            current = parent_by_id[current]


def lineage_spaces_overlap(
    parent_by_id: Mapping[UUID, UUID | None], first_id: UUID, second_id: UUID
) -> bool:
    return lineage_is_ancestor(
        parent_by_id, first_id, second_id
    ) or lineage_is_ancestor(parent_by_id, second_id, first_id)


def first_conflict(
    candidate: RelationshipDefinition,
    existing: RelationshipDefinition,
    parent_by_id: Mapping[UUID, UUID | None],
) -> tuple[RelationshipResolution, RelationshipResolution] | None:
    validate_definition(candidate)
    validate_definition(existing)
    if candidate.id == existing.id:
        return None
    for candidate_resolution in candidate.resolutions:
        for existing_resolution in existing.resolutions:
            if candidate_resolution.name != existing_resolution.name:
                continue
            if not lineage_spaces_overlap(
                parent_by_id,
                candidate_resolution.from_template_id,
                existing_resolution.from_template_id,
            ):
                continue
            if lineage_spaces_overlap(
                parent_by_id,
                candidate_resolution.to_template_id,
                existing_resolution.to_template_id,
            ):
                return candidate_resolution, existing_resolution
    return None
