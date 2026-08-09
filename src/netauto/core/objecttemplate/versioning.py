"""Lifecycle and version creation operations for object template versions."""

from collections.abc import Callable, Iterable
from uuid import UUID

from netauto.core.datatype.models import DataTypeVersion, DataTypeVersionStatus
from netauto.core.objecttemplate.exceptions import (
    InvalidObjectTemplateVersionTransition,
    MismatchedObjectTemplateVersion,
    ObjectTemplateComponentVersionNotFound,
    ObjectTemplateComponentVersionNotPublished,
    ObjectTemplateDataTypeVersionNotFound,
    ObjectTemplateDataTypeVersionNotPublished,
    ObjectTemplateParentNotPublished,
)
from netauto.core.objecttemplate.models import (
    ObjectTemplateComponent,
    ObjectTemplateProperty,
    ObjectTemplateVersion,
    ObjectTemplateVersionRef,
    ObjectTemplateVersionStatus,
)
from netauto.core.objecttemplate.resolver import (
    ObjectTemplateInheritanceResolver,
    ObjectTemplateVersionLookup,
)

DataTypeVersionLookup = Callable[[UUID, int], DataTypeVersion | None]


class ObjectTemplateVersioningService:
    """Operate on immutable object template version snapshots."""

    def __init__(self) -> None:
        self._resolver = ObjectTemplateInheritanceResolver()

    def revise_draft(
        self,
        version: ObjectTemplateVersion,
        *,
        parent: ObjectTemplateVersionRef | None,
        properties: Iterable[ObjectTemplateProperty],
        components: Iterable[ObjectTemplateComponent] = (),
    ) -> ObjectTemplateVersion:
        if version.status is not ObjectTemplateVersionStatus.DRAFT:
            raise InvalidObjectTemplateVersionTransition("Only draft versions may be revised.")
        return ObjectTemplateVersion(
            template_id=version.template_id,
            version=version.version,
            status=ObjectTemplateVersionStatus.DRAFT,
            parent=parent,
            properties=tuple(properties),
            components=tuple(components),
        )

    def create_next_version(
        self,
        source: ObjectTemplateVersion,
        *,
        existing_versions: Iterable[ObjectTemplateVersion],
    ) -> ObjectTemplateVersion:
        if source.status is not ObjectTemplateVersionStatus.PUBLISHED:
            raise InvalidObjectTemplateVersionTransition(
                "Only published versions may be used to create the next version."
            )

        versions = tuple(existing_versions)
        version_numbers = [source.version]
        for candidate in versions:
            if candidate.template_id != source.template_id:
                raise MismatchedObjectTemplateVersion(
                    "All existing versions must belong to the same object template."
                )
            version_numbers.append(candidate.version)

        return ObjectTemplateVersion(
            template_id=source.template_id,
            version=max(version_numbers) + 1,
            status=ObjectTemplateVersionStatus.DRAFT,
            parent=source.parent,
            properties=source.properties,
            components=source.components,
        )

    def publish(
        self,
        version: ObjectTemplateVersion,
        *,
        parent_lookup: ObjectTemplateVersionLookup,
        datatype_lookup: DataTypeVersionLookup,
    ) -> ObjectTemplateVersion:
        if version.status is not ObjectTemplateVersionStatus.DRAFT:
            raise InvalidObjectTemplateVersionTransition("Only draft versions may be published.")

        effective_properties = self._resolver.resolve_effective_properties(
            version,
            parent_lookup=parent_lookup,
        )
        effective_components = self._resolver.resolve_effective_components(
            version,
            parent_lookup=parent_lookup,
        )

        if version.parent is not None:
            parent_version = parent_lookup(version.parent)
            if (
                parent_version is not None
                and parent_version.status is not ObjectTemplateVersionStatus.PUBLISHED
            ):
                raise ObjectTemplateParentNotPublished(
                    "Referenced parent object template version must be published."
                )

        for prop in effective_properties:
            datatype_version = datatype_lookup(prop.datatype_id, prop.datatype_version)
            if datatype_version is None:
                raise ObjectTemplateDataTypeVersionNotFound(
                    "Referenced datatype version was not found."
                )
            if datatype_version.status is not DataTypeVersionStatus.PUBLISHED:
                raise ObjectTemplateDataTypeVersionNotPublished(
                    "Referenced datatype version must be published."
                )

        for component in effective_components:
            component_version = parent_lookup(
                ObjectTemplateVersionRef(
                    template_id=component.template_id,
                    version=component.template_version,
                )
            )
            if component_version is None:
                raise ObjectTemplateComponentVersionNotFound(
                    "Referenced component target version was not found."
                )
            if component_version.status is not ObjectTemplateVersionStatus.PUBLISHED:
                raise ObjectTemplateComponentVersionNotPublished(
                    "Referenced component target version must be published."
                )

        return ObjectTemplateVersion(
            template_id=version.template_id,
            version=version.version,
            status=ObjectTemplateVersionStatus.PUBLISHED,
            parent=version.parent,
            properties=version.properties,
            components=version.components,
        )

    def deprecate(self, version: ObjectTemplateVersion) -> ObjectTemplateVersion:
        if version.status is not ObjectTemplateVersionStatus.PUBLISHED:
            raise InvalidObjectTemplateVersionTransition(
                "Only published versions may be deprecated."
            )
        return ObjectTemplateVersion(
            template_id=version.template_id,
            version=version.version,
            status=ObjectTemplateVersionStatus.DEPRECATED,
            parent=version.parent,
            properties=version.properties,
            components=version.components,
        )
