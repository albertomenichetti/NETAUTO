"""Persistence-neutral repository contract and guards for object templates."""

from typing import Literal, Protocol
from uuid import UUID

from netauto.core.objecttemplate.exceptions import ObjectTemplatePersistenceError
from netauto.core.objecttemplate.models import (
    ObjectTemplate,
    ObjectTemplateVersion,
    ObjectTemplateVersionStatus,
)

ObjectTemplateReplaceMode = Literal["draft_replace", "status_only"]


class ObjectTemplateRepository(Protocol):
    """Repository contract for object template persistence.

    Repositories enforce the persisted ObjectTemplateVersion lifecycle contract:

    - new persisted versions must enter as DRAFT
    - DRAFT -> DRAFT may revise parent, properties, and components
    - DRAFT -> PUBLISHED is status-only over the exact snapshot
    - PUBLISHED -> DEPRECATED is status-only over the exact snapshot
    - DEPRECATED is terminal
    """

    def list(self) -> tuple[ObjectTemplate, ...]:
        """Return all object templates ordered deterministically."""
        ...

    def add(self, template: ObjectTemplate) -> None:
        """Persist a new object template identity."""
        ...

    def get(self, template_id: UUID) -> ObjectTemplate | None:
        """Return an object template by UUID or None."""
        ...

    def get_by_name(self, namespace: str, name: str) -> ObjectTemplate | None:
        """Return an object template by logical name or None."""
        ...

    def delete(self, template_id: UUID) -> None:
        """Delete an object template identity and all of its versions."""
        ...

    def add_version(self, version: ObjectTemplateVersion) -> None:
        """Persist a new object template version snapshot as a new DRAFT only."""
        ...

    def get_version(self, template_id: UUID, version: int) -> ObjectTemplateVersion | None:
        """Return an exact object template version or None."""
        ...

    def list_versions(self, template_id: UUID) -> tuple[ObjectTemplateVersion, ...]:
        """Return all versions ordered by version ascending."""
        ...

    def replace_version(self, version: ObjectTemplateVersion) -> None:
        """Replace an existing version using the constrained lifecycle rules."""
        ...


def validate_object_template_version_add(version: ObjectTemplateVersion) -> None:
    """Validate that a new persisted version satisfies repository invariants."""
    if version.status is not ObjectTemplateVersionStatus.DRAFT:
        raise ObjectTemplatePersistenceError(
            "New object template versions must be persisted as draft."
        )


def validate_object_template_version_replace(
    current: ObjectTemplateVersion,
    replacement: ObjectTemplateVersion,
) -> ObjectTemplateReplaceMode:
    """Validate that an exact persisted version replacement is legal."""
    if (
        replacement.template_id != current.template_id
        or replacement.version != current.version
    ):
        raise ObjectTemplatePersistenceError("ObjectTemplate version identity is immutable.")

    current_status = current.status
    replacement_status = replacement.status

    if current_status is ObjectTemplateVersionStatus.DRAFT:
        if replacement_status is ObjectTemplateVersionStatus.DRAFT:
            return "draft_replace"
        if replacement_status is ObjectTemplateVersionStatus.PUBLISHED:
            _require_same_object_template_snapshot(current, replacement)
            return "status_only"
        raise ObjectTemplatePersistenceError(
            "Draft object template versions may only be revised or published."
        )

    if current_status is ObjectTemplateVersionStatus.PUBLISHED:
        if replacement_status is ObjectTemplateVersionStatus.DEPRECATED:
            _require_same_object_template_snapshot(current, replacement)
            return "status_only"
        raise ObjectTemplatePersistenceError(
            "Published object template versions may only transition to deprecated."
        )

    raise ObjectTemplatePersistenceError("Deprecated object template versions are terminal.")


def _require_same_object_template_snapshot(
    current: ObjectTemplateVersion,
    replacement: ObjectTemplateVersion,
) -> None:
    if current.parent != replacement.parent:
        raise ObjectTemplatePersistenceError(
            "Lifecycle status transitions may not change the parent snapshot."
        )
    if current.properties != replacement.properties:
        raise ObjectTemplatePersistenceError(
            "Lifecycle status transitions may not change the property snapshot."
        )
    if current.components != replacement.components:
        raise ObjectTemplatePersistenceError(
            "Lifecycle status transitions may not change the component snapshot."
        )
