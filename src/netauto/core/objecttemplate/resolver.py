"""Pure domain inheritance resolution for object template versions."""

from collections.abc import Callable
from uuid import UUID

from netauto.core.objecttemplate.exceptions import (
    InheritedObjectTemplatePropertyConflict,
    ObjectTemplateInheritanceCycle,
    ObjectTemplateParentNotFound,
    ObjectTemplateSelfInheritance,
)
from netauto.core.objecttemplate.models import (
    ObjectTemplateProperty,
    ObjectTemplateVersion,
    ObjectTemplateVersionRef,
)

ObjectTemplateVersionLookup = Callable[[ObjectTemplateVersionRef], ObjectTemplateVersion | None]


class ObjectTemplateInheritanceResolver:
    """Resolve effective properties through a pinned single-parent chain."""

    def resolve_effective_properties(
        self,
        version: ObjectTemplateVersion,
        *,
        parent_lookup: ObjectTemplateVersionLookup,
    ) -> tuple[ObjectTemplateProperty, ...]:
        return self._resolve_effective_properties(
            version,
            parent_lookup=parent_lookup,
            visited=set(),
        )

    def _resolve_effective_properties(
        self,
        version: ObjectTemplateVersion,
        *,
        parent_lookup: ObjectTemplateVersionLookup,
        visited: set[tuple[UUID, int]],
    ) -> tuple[ObjectTemplateProperty, ...]:
        identity = (version.template_id, version.version)
        if identity in visited:
            raise ObjectTemplateInheritanceCycle(
                "Object template inheritance cycle detected."
            )

        current_path = visited | {identity}
        inherited_properties: tuple[ObjectTemplateProperty, ...] = ()
        if version.parent is not None:
            if version.parent.template_id == version.template_id:
                raise ObjectTemplateSelfInheritance(
                    "Object template version cannot inherit from another version of the same "
                    "template."
                )
            parent_version = parent_lookup(version.parent)
            if parent_version is None:
                raise ObjectTemplateParentNotFound(
                    "Referenced parent object template version was not found."
                )
            inherited_properties = self._resolve_effective_properties(
                parent_version,
                parent_lookup=parent_lookup,
                visited=current_path,
            )

        inherited_names = {prop.name for prop in inherited_properties}
        for prop in version.properties:
            if prop.name in inherited_names:
                raise InheritedObjectTemplatePropertyConflict(
                    f"Property '{prop.name}' conflicts with an inherited property."
                )

        return inherited_properties + version.properties
