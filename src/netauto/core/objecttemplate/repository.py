"""Persistence-neutral repository contract for object templates."""

from typing import Protocol
from uuid import UUID

from netauto.core.objecttemplate.models import ObjectTemplate, ObjectTemplateVersion


class ObjectTemplateRepository(Protocol):
    """Repository contract for object template persistence."""

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

    def add_version(self, version: ObjectTemplateVersion) -> None:
        """Persist a new object template version snapshot."""
        ...

    def get_version(self, template_id: UUID, version: int) -> ObjectTemplateVersion | None:
        """Return an exact object template version or None."""
        ...

    def list_versions(self, template_id: UUID) -> tuple[ObjectTemplateVersion, ...]:
        """Return all versions ordered by version ascending."""
        ...

    def replace_version(self, version: ObjectTemplateVersion) -> None:
        """Replace an existing object template version snapshot."""
        ...
