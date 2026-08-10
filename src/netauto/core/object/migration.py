"""Object migration analysis models."""

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class ObjectTemplateMigrationBlockingChangeKind(StrEnum):
    """Stable machine-readable blocking change kinds."""

    PROPERTY_REMOVED = "property_removed"
    PROPERTY_CHANGED = "property_changed"
    COMPONENT_REMOVED = "component_removed"
    COMPONENT_CHANGED = "component_changed"


@dataclass(frozen=True, slots=True)
class ObjectTemplateMigrationAddedProperty:
    """One newly added effective property on the target schema."""

    name: str
    required: bool


@dataclass(frozen=True, slots=True)
class ObjectTemplateMigrationAddedComponent:
    """One newly added effective component slot on the target schema."""

    name: str
    template_id: UUID


@dataclass(frozen=True, slots=True)
class ObjectTemplateMigrationBlockingChange:
    """One structural change that blocks automatic migration."""

    kind: ObjectTemplateMigrationBlockingChangeKind
    name: str


@dataclass(frozen=True, slots=True)
class ObjectTemplateMigrationAnalysis:
    """Deterministic additive-migration analysis for one template/version pair."""

    template_id: UUID
    source_version: int
    target_version: int
    added_properties: tuple[ObjectTemplateMigrationAddedProperty, ...] = ()
    added_components: tuple[ObjectTemplateMigrationAddedComponent, ...] = ()
    blocking_changes: tuple[ObjectTemplateMigrationBlockingChange, ...] = ()

    @property
    def automatic(self) -> bool:
        return not self.blocking_changes


@dataclass(frozen=True, slots=True)
class ObjectMigrationResult:
    """Result summary for one bulk object migration operation."""

    template_id: UUID
    source_version: int
    target_version: int
    migrated_count: int
