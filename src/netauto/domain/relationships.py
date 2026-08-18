"""Plain-Python Relationship model-plane and factual runtime semantics."""

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from netauto.domain.datatypes import VersionStatus
from netauto.domain.objects import (
    ObjectValidationError,
    RuntimePropertySpec,
    canonicalize_properties,
)
from netauto.domain.objecttemplates import ValueMode
from netauto.domain.primitives import JsonValue

_IDENTIFIER = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")

type ResolutionSemanticKey = tuple[UUID, UUID, str]
type DefinitionSemanticSignature = tuple[bool, frozenset[ResolutionSemanticKey]]


def _empty_properties() -> dict[str, JsonValue]:
    return {}


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
    default_version: int | None = None


@dataclass(frozen=True, slots=True)
class RelationshipDefinitionProperty:
    name: str
    position: int
    datatype_id: UUID
    datatype_version: int
    value_mode: ValueMode


@dataclass(frozen=True, slots=True)
class RelationshipDefinitionVersion:
    relationship_definition_id: UUID
    version: int
    revision: int
    status: VersionStatus
    properties: tuple[RelationshipDefinitionProperty, ...]


@dataclass(frozen=True, slots=True)
class RelationshipDefinitionVersionSummary:
    relationship_definition_id: UUID
    version: int
    revision: int
    status: VersionStatus


@dataclass(frozen=True, slots=True)
class RelationshipPropertyCandidate:
    name: str
    position: int
    datatype_id: UUID
    datatype_version: int | None
    value_mode: ValueMode


@dataclass(frozen=True, slots=True)
class CreateRelationshipDefinitionResult:
    relationship_definition: RelationshipDefinition
    version: RelationshipDefinitionVersion


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
    default_version: int | None = None


@dataclass(frozen=True, slots=True)
class RuntimeRelationshipResolution:
    relationship_id: UUID
    relationship_definition_id: UUID
    resolution_id: UUID
    from_object_id: UUID
    to_object_id: UUID


@dataclass(frozen=True, slots=True)
class Relationship:
    id: UUID
    relationship_definition_id: UUID
    resolutions: tuple[RuntimeRelationshipResolution, ...]
    relationship_definition_version: int
    properties: dict[str, JsonValue] = field(default_factory=_empty_properties)


@dataclass(frozen=True, slots=True)
class RelationshipView:
    object_id: UUID
    destination_object_id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class ObjectRelationshipView:
    relationship_id: UUID
    relationship_definition_id: UUID
    object_id: UUID
    destination_object_id: UUID
    name: str
    relationship_definition_version: int
    properties: dict[str, JsonValue] = field(default_factory=_empty_properties)


@dataclass(frozen=True, slots=True)
class RelationshipLifecycleView:
    object_id: UUID
    canonical_name: str
    destination_object_id: UUID
    destination_canonical_name: str
    relationship_name: str


@dataclass(frozen=True, slots=True)
class RelationshipSchemaPropertySpec:
    """Resolved factual property declaration with its stable semantic identity."""

    position: int
    datatype_id: UUID
    runtime: RuntimePropertySpec


class RelationshipSchemaChangeBlocked(ValueError):
    def __init__(self, property_name: str) -> None:
        self.property_name = property_name
        super().__init__(property_name)


class RelationshipDefinitionValidationError(ValueError):
    def __init__(self, path: str, rule: str) -> None:
        self.path = path
        self.rule = rule
        super().__init__(f"{path}: {rule}")


class RelationshipValidationError(ValueError):
    def __init__(self, path: str, rule: str) -> None:
        self.path = path
        self.rule = rule
        super().__init__(f"{path}: {rule}")


def validate_relationship_name(name: str, path: str = "name") -> None:
    if _IDENTIFIER.fullmatch(name) is None:
        raise RelationshipDefinitionValidationError(path, "invalid_identifier")


def validate_relationship_definition_version(
    value: RelationshipDefinitionVersion,
) -> None:
    if value.version <= 0:
        raise RelationshipDefinitionValidationError("version", "positive_required")
    if value.revision <= 0:
        raise RelationshipDefinitionValidationError("revision", "positive_required")
    names: set[str] = set()
    positions: set[int] = set()
    for item in value.properties:
        validate_relationship_name(item.name, f"properties.{item.name}.name")
        if item.name in names:
            raise RelationshipDefinitionValidationError(
                f"properties.{item.name}.name", "duplicate_property_name"
            )
        if item.position <= 0 or item.position in positions:
            raise RelationshipDefinitionValidationError(
                f"properties.{item.name}.position",
                "duplicate_or_invalid_position",
            )
        if item.datatype_version <= 0:
            raise RelationshipDefinitionValidationError(
                f"properties.{item.name}.datatype_version", "positive_required"
            )
        names.add(item.name)
        positions.add(item.position)


def validate_relationship_property_history(
    candidate: RelationshipDefinitionVersion,
    published_history: tuple[RelationshipDefinitionVersion, ...],
) -> None:
    """Validate continuity against every committed published generation.

    Reviewing the complete history, rather than only the numerically previous
    version, keeps out-of-order publication serializable.
    """
    validate_relationship_definition_version(candidate)
    history_by_name: dict[str, list[RelationshipDefinitionProperty]] = {}
    for version in published_history:
        if version.relationship_definition_id != candidate.relationship_definition_id:
            raise RelationshipDefinitionValidationError(
                "properties", "history_definition_mismatch"
            )
        for item in version.properties:
            history_by_name.setdefault(item.name, []).append(item)
    for item in candidate.properties:
        previous = history_by_name.get(item.name, ())
        if any(value.datatype_id != item.datatype_id for value in previous):
            raise RelationshipDefinitionValidationError(
                f"properties.{item.name}.datatype_id",
                "property_datatype_lineage_changed",
            )
        if any(
            value.value_mode is ValueMode.LIST and item.value_mode is ValueMode.SCALAR
            for value in previous
        ):
            raise RelationshipDefinitionValidationError(
                f"properties.{item.name}.value_mode", "list_to_scalar_forbidden"
            )


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
        value.default_version,
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
        value.default_version,
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


def derive_runtime_closure(
    definition: RelationshipDefinition,
    *,
    selected_resolution_id: UUID,
    from_object_id: UUID,
    from_template_id: UUID,
    to_object_id: UUID,
    to_template_id: UUID,
    parent_by_id: Mapping[UUID, UUID | None],
    relationship_id: UUID | None = None,
) -> tuple[RuntimeRelationshipResolution, ...]:
    """Derive the complete exact runtime closure from one factual selector."""
    validate_definition(definition)
    by_id = {item.id: item for item in definition.resolutions}
    selected = by_id.get(selected_resolution_id)
    if selected is None:
        raise RelationshipValidationError(
            "resolution_id", "resolution_not_in_definition"
        )

    def admits(resolution: RelationshipResolution, first: UUID, second: UUID) -> bool:
        return lineage_is_ancestor(
            parent_by_id, resolution.from_template_id, first
        ) and lineage_is_ancestor(parent_by_id, resolution.to_template_id, second)

    if not admits(selected, from_template_id, to_template_id):
        if not lineage_is_ancestor(
            parent_by_id, selected.from_template_id, from_template_id
        ):
            raise RelationshipValidationError(
                "from_object_id", "incompatible_template_lineage"
            )
        raise RelationshipValidationError(
            "to_object_id", "incompatible_template_lineage"
        )

    factual_id = relationship_id or uuid4()
    exact: set[tuple[UUID, UUID, UUID]] = set()
    if not definition.symmetric:
        exact.add((selected.id, from_object_id, to_object_id))
        reciprocal = next(
            (
                item
                for item in definition.resolutions
                if item.id != selected.id
                and item.from_template_id == selected.to_template_id
                and item.to_template_id == selected.from_template_id
            ),
            None,
        )
        if reciprocal is None:
            raise RelationshipDefinitionValidationError(
                "resolutions", "non_symmetric_resolutions_must_be_reciprocal"
            )
        exact.add((reciprocal.id, to_object_id, from_object_id))
    else:
        assignments = (
            (from_object_id, from_template_id, to_object_id, to_template_id),
            (to_object_id, to_template_id, from_object_id, from_template_id),
        )
        for resolution in definition.resolutions:
            for first_id, first_template, second_id, second_template in assignments:
                if admits(resolution, first_template, second_template):
                    exact.add((resolution.id, first_id, second_id))

    return tuple(
        RuntimeRelationshipResolution(
            relationship_id=factual_id,
            relationship_definition_id=definition.id,
            resolution_id=resolution_id,
            from_object_id=first_id,
            to_object_id=second_id,
        )
        for resolution_id, first_id, second_id in sorted(
            exact, key=lambda item: (item[0].int, item[1].int, item[2].int)
        )
    )


def validate_relationship(
    value: Relationship,
    definition: RelationshipDefinition,
    *,
    parent_by_id: Mapping[UUID, UUID | None],
    template_by_object_id: Mapping[UUID, UUID],
) -> None:
    """Validate that persisted runtime rows are exactly one factual closure."""
    if (
        isinstance(value.relationship_definition_version, bool)
        or value.relationship_definition_version <= 0
    ):
        raise RelationshipValidationError(
            "relationship_definition_version", "positive_required"
        )
    if value.relationship_definition_id != definition.id or not value.resolutions:
        raise RelationshipValidationError("relationship", "incomplete_closure")
    if any(
        item.relationship_id != value.id
        or item.relationship_definition_id != value.relationship_definition_id
        for item in value.resolutions
    ):
        raise RelationshipValidationError("relationship", "aggregate_mismatch")
    selector = min(
        value.resolutions,
        key=lambda item: (
            item.resolution_id.int,
            item.from_object_id.int,
            item.to_object_id.int,
        ),
    )
    try:
        from_template_id = template_by_object_id[selector.from_object_id]
        to_template_id = template_by_object_id[selector.to_object_id]
    except KeyError as error:
        raise RelationshipValidationError(
            "relationship", "missing_endpoint_object"
        ) from error
    expected = derive_runtime_closure(
        definition,
        selected_resolution_id=selector.resolution_id,
        from_object_id=selector.from_object_id,
        from_template_id=from_template_id,
        to_object_id=selector.to_object_id,
        to_template_id=to_template_id,
        parent_by_id=parent_by_id,
        relationship_id=value.id,
    )
    actual_keys = {
        (item.resolution_id, item.from_object_id, item.to_object_id)
        for item in value.resolutions
    }
    expected_keys = {
        (item.resolution_id, item.from_object_id, item.to_object_id)
        for item in expected
    }
    if actual_keys != expected_keys or len(actual_keys) != len(value.resolutions):
        raise RelationshipValidationError("relationship", "incomplete_closure")


def relationship_views(
    value: Relationship, definition: RelationshipDefinition
) -> tuple[RelationshipView, ...]:
    names = {item.id: item.name for item in definition.resolutions}
    try:
        views = {
            RelationshipView(
                object_id=item.from_object_id,
                destination_object_id=item.to_object_id,
                name=names[item.resolution_id],
            )
            for item in value.resolutions
        }
    except KeyError as error:
        raise RelationshipValidationError(
            "relationship", "resolution_not_in_definition"
        ) from error
    return tuple(
        sorted(
            views,
            key=lambda item: (
                item.object_id.int,
                item.destination_object_id.int,
                item.name,
            ),
        )
    )


def migrate_relationship_properties(
    current: Mapping[str, object],
    source: tuple[RelationshipSchemaPropertySpec, ...],
    target: tuple[RelationshipSchemaPropertySpec, ...],
) -> dict[str, JsonValue]:
    """Apply the frozen Relationship preserve-or-fail schema migration."""
    source_by_name = {item.runtime.name: item for item in source}
    candidate: dict[str, object] = {}
    carried_names: set[str] = set()
    for target_item in sorted(target, key=lambda item: item.position):
        target_spec = target_item.runtime
        source_item = source_by_name.get(target_spec.name)
        if source_item is None:
            continue
        if source_item.datatype_id != target_item.datatype_id:
            raise RelationshipValidationError(
                f"properties.{target_spec.name}", "property_datatype_lineage_changed"
            )
        if (
            source_item.runtime.value_mode is ValueMode.LIST
            and target_spec.value_mode is ValueMode.SCALAR
        ):
            raise RelationshipValidationError(
                f"properties.{target_spec.name}", "list_to_scalar_forbidden"
            )
        if target_spec.name not in current:
            continue
        value = current[target_spec.name]
        if (
            source_item.runtime.value_mode is ValueMode.SCALAR
            and target_spec.value_mode is ValueMode.LIST
        ):
            value = [value]
        elif source_item.runtime.value_mode is not target_spec.value_mode:
            raise RelationshipSchemaChangeBlocked(target_spec.name)
        candidate[target_spec.name] = value
        carried_names.add(target_spec.name)
    try:
        return canonicalize_properties(
            candidate, tuple(item.runtime for item in target)
        )
    except (ObjectValidationError, ValueError) as error:
        name = getattr(error, "path", "").removeprefix("properties.").split(".")[0]
        if name in carried_names:
            raise RelationshipSchemaChangeBlocked(name) from error
        raise
