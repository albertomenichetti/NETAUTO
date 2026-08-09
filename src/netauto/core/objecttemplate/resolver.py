"""Pure domain inheritance resolution for object template versions."""

from collections.abc import Callable
from uuid import UUID

from netauto.core.objecttemplate.exceptions import (
    InheritedObjectTemplateComponentConflict,
    InheritedObjectTemplatePropertyConflict,
    ObjectTemplateInheritanceCycle,
    ObjectTemplateParentNotFound,
    ObjectTemplateSelfInheritance,
)
from netauto.core.objecttemplate.models import (
    ObjectTemplateComponent,
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

    def resolve_effective_components(
        self,
        version: ObjectTemplateVersion,
        *,
        parent_lookup: ObjectTemplateVersionLookup,
    ) -> tuple[ObjectTemplateComponent, ...]:
        return self._resolve_effective_components(
            version,
            parent_lookup=parent_lookup,
            visited=set(),
        )

    def is_same_or_descendant(
        self,
        candidate: ObjectTemplateVersion,
        *,
        required: ObjectTemplateVersionRef,
        parent_lookup: ObjectTemplateVersionLookup,
    ) -> bool:
        return self._is_same_or_descendant(
            candidate,
            required=required,
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

    def _is_same_or_descendant(
        self,
        version: ObjectTemplateVersion,
        *,
        required: ObjectTemplateVersionRef,
        parent_lookup: ObjectTemplateVersionLookup,
        visited: set[tuple[UUID, int]],
    ) -> bool:
        identity = (version.template_id, version.version)
        if identity == (required.template_id, required.version):
            return True
        if identity in visited:
            raise ObjectTemplateInheritanceCycle(
                "Object template inheritance cycle detected."
            )
        if version.parent is None:
            return False
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
        return self._is_same_or_descendant(
            parent_version,
            required=required,
            parent_lookup=parent_lookup,
            visited=visited | {identity},
        )

    def _resolve_effective_components(
        self,
        version: ObjectTemplateVersion,
        *,
        parent_lookup: ObjectTemplateVersionLookup,
        visited: set[tuple[UUID, int]],
    ) -> tuple[ObjectTemplateComponent, ...]:
        identity = (version.template_id, version.version)
        if identity in visited:
            raise ObjectTemplateInheritanceCycle(
                "Object template inheritance cycle detected."
            )

        current_path = visited | {identity}
        inherited_components: tuple[ObjectTemplateComponent, ...] = ()
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
            inherited_components = self._resolve_effective_components(
                parent_version,
                parent_lookup=parent_lookup,
                visited=current_path,
            )

        inherited_names = {component.name for component in inherited_components}
        for component in version.components:
            if component.name in inherited_names:
                raise InheritedObjectTemplateComponentConflict(
                    f"Component '{component.name}' conflicts with an inherited component."
                )

        return inherited_components + version.components
