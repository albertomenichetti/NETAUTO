"""Lifecycle and version creation operations for object template versions."""

from collections.abc import Callable, Iterable
from uuid import UUID

from netauto.core.datatype.models import DataTypeVersion, DataTypeVersionStatus
from netauto.core.objecttemplate.exceptions import (
    InvalidObjectTemplateVersionTransition,
    MismatchedObjectTemplateVersion,
    ObjectTemplateComponentVersionNotFound,
    ObjectTemplateComponentVersionNotPublished,
    ObjectTemplateDataTypeVersionDowngrade,
    ObjectTemplateDataTypeVersionNotFound,
    ObjectTemplateDataTypeVersionNotPublished,
    ObjectTemplateInheritanceCycle,
    ObjectTemplateParentIdentityChanged,
    ObjectTemplateParentNotFound,
    ObjectTemplateParentNotPublished,
    ObjectTemplateParentVersionDowngrade,
    ObjectTemplatePersistenceError,
    ObjectTemplateSelfInheritance,
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
        proposed_properties = tuple(properties)
        current_by_name = {prop.name: prop for prop in version.properties}

        for proposed in proposed_properties:
            current = current_by_name.get(proposed.name)
            if current is None:
                continue
            if current.datatype_id != proposed.datatype_id:
                continue
            if proposed.datatype_version < current.datatype_version:
                raise ObjectTemplateDataTypeVersionDowngrade(
                    "Object template properties cannot downgrade datatype versions."
                )

        return ObjectTemplateVersion(
            template_id=version.template_id,
            version=version.version,
            status=ObjectTemplateVersionStatus.DRAFT,
            parent=parent,
            properties=proposed_properties,
            components=tuple(components),
        )

    def validate_parent_evolution(
        self,
        prospective: ObjectTemplateVersion,
        *,
        existing_versions: Iterable[ObjectTemplateVersion],
        parent_lookup: ObjectTemplateVersionLookup,
    ) -> None:
        versions = tuple(existing_versions)
        for candidate in versions:
            if candidate.template_id != prospective.template_id:
                raise MismatchedObjectTemplateVersion(
                    "All existing versions must belong to the same object template."
                )

        self._assert_parent_chain_is_structurally_valid(
            prospective,
            parent_lookup=parent_lookup,
        )

        published_lineage = tuple(
            candidate
            for candidate in versions
            if candidate.status
            in (
                ObjectTemplateVersionStatus.PUBLISHED,
                ObjectTemplateVersionStatus.DEPRECATED,
            )
        )
        if not published_lineage:
            return

        stable_parent = published_lineage[0].parent
        for candidate in published_lineage[1:]:
            if not self._same_parent_identity(candidate.parent, stable_parent):
                raise ObjectTemplatePersistenceError(
                    "Stored object template lineage is internally inconsistent."
                )

        first_published_version = min(candidate.version for candidate in published_lineage)
        relevant_versions = list(versions)
        replaced = False
        for index, candidate in enumerate(relevant_versions):
            if (
                candidate.template_id == prospective.template_id
                and candidate.version == prospective.version
            ):
                relevant_versions[index] = prospective
                replaced = True
                break
        if not replaced:
            relevant_versions.append(prospective)
        relevant_versions.sort(key=lambda candidate: candidate.version)

        if stable_parent is None:
            for candidate in relevant_versions:
                if candidate.version < first_published_version:
                    continue
                if candidate.parent is None:
                    continue
                if candidate is prospective:
                    raise ObjectTemplateParentIdentityChanged(
                        "Object template parent identity cannot change after publication."
                    )
                raise ObjectTemplatePersistenceError(
                    "Stored object template lineage is internally inconsistent."
                )
            return

        highest_parent_version = 0
        for candidate in relevant_versions:
            if candidate.version < first_published_version:
                continue
            parent = candidate.parent
            if parent is None or parent.template_id != stable_parent.template_id:
                if candidate is prospective:
                    raise ObjectTemplateParentIdentityChanged(
                        "Object template parent identity cannot change after publication."
                    )
                raise ObjectTemplatePersistenceError(
                    "Stored object template lineage is internally inconsistent."
                )
            if parent.version < highest_parent_version:
                if candidate is prospective:
                    raise ObjectTemplateParentVersionDowngrade(
                        "Object template parent version cannot move backwards."
                    )
                raise ObjectTemplatePersistenceError(
                    "Stored object template lineage is internally inconsistent."
                )
            highest_parent_version = parent.version

    def create_next_version(
        self,
        source: ObjectTemplateVersion,
        *,
        existing_versions: Iterable[ObjectTemplateVersion],
    ) -> ObjectTemplateVersion:
        if source.status not in (
            ObjectTemplateVersionStatus.PUBLISHED,
            ObjectTemplateVersionStatus.DEPRECATED,
        ):
            raise InvalidObjectTemplateVersionTransition(
                "Only published or deprecated versions may be used to create the next version."
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
        template_exists: Callable[[UUID], bool] | None = None,
        template_versions_lister: (
            Callable[[UUID], tuple[ObjectTemplateVersion, ...]] | None
        ) = None,
    ) -> ObjectTemplateVersion:
        component_template_exists = template_exists or (lambda _template_id: False)
        component_template_versions_lister = template_versions_lister or (
            lambda _template_id: ()
        )
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
            published_versions = tuple(
                candidate
                for candidate in component_template_versions_lister(component.template_id)
                if candidate.status is ObjectTemplateVersionStatus.PUBLISHED
            )
            if published_versions:
                continue
            if not component_template_exists(component.template_id):
                raise ObjectTemplateComponentVersionNotFound(
                    "Referenced component target template was not found."
                )
            raise ObjectTemplateComponentVersionNotPublished(
                "Referenced component target template must have a published version."
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

    def _assert_parent_chain_is_structurally_valid(
        self,
        prospective: ObjectTemplateVersion,
        *,
        parent_lookup: ObjectTemplateVersionLookup,
    ) -> None:
        parent = prospective.parent
        if parent is None:
            return
        if parent.template_id == prospective.template_id:
            raise ObjectTemplateSelfInheritance(
                "Object template version cannot inherit from another version of the same "
                "template."
            )

        visited = {(prospective.template_id, prospective.version)}
        current_ref = parent
        while current_ref is not None:
            identity = (current_ref.template_id, current_ref.version)
            if identity in visited:
                raise ObjectTemplateInheritanceCycle(
                    "Object template inheritance cycle detected."
                )
            visited.add(identity)
            current = parent_lookup(current_ref)
            if current is None:
                raise ObjectTemplateParentNotFound(
                    "Referenced parent object template version was not found."
                )
            next_parent = current.parent
            if next_parent is not None and next_parent.template_id == current.template_id:
                raise ObjectTemplateSelfInheritance(
                    "Object template version cannot inherit from another version of the same "
                    "template."
                )
            current_ref = next_parent

    def _same_parent_identity(
        self,
        left: ObjectTemplateVersionRef | None,
        right: ObjectTemplateVersionRef | None,
    ) -> bool:
        if left is None or right is None:
            return left is None and right is None
        return left.template_id == right.template_id
