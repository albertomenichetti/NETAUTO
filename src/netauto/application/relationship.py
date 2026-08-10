"""Application service for relationship definition workflows."""

from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID, uuid4

from netauto.application.unit_of_work import (
    RelationshipDefinitionUnitOfWork,
    RelationshipDefinitionUnitOfWorkFactory,
)
from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateInheritanceResolver,
    ObjectTemplateVersion,
    ObjectTemplateVersionRef,
    ObjectTemplateVersionStatus,
)
from netauto.core.relationship import (
    RelationshipDefinition,
    RelationshipDefinitionNotFound,
    RelationshipDefinitionSemanticConflict,
    RelationshipDefinitionTemplateNotFound,
    RelationshipDefinitionTemplateNotPublished,
    relationship_definitions_are_semantically_equivalent,
)


@dataclass(frozen=True, slots=True)
class _RelationshipDefinitionConflictSnapshot:
    templates: tuple[ObjectTemplate, ...]
    all_versions: tuple[ObjectTemplateVersion, ...]
    usable_versions: tuple[ObjectTemplateVersion, ...]
    existing_definitions: tuple[RelationshipDefinition, ...]

    def lookup_parent(
        self,
        version_ref: ObjectTemplateVersionRef,
    ) -> ObjectTemplateVersion | None:
        for version in self.all_versions:
            if (
                version.template_id == version_ref.template_id
                and version.version == version_ref.version
            ):
                return version
        return None


class RelationshipDefinitionApplicationService:
    """Orchestrate relationship definition workflows over a unit of work boundary."""

    def __init__(self, uow_factory: RelationshipDefinitionUnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory
        self._inheritance = ObjectTemplateInheritanceResolver()

    def list_relationship_definitions(self) -> tuple[RelationshipDefinition, ...]:
        with self._uow_factory() as uow:
            return uow.relationship_definitions.list()

    def get_relationship_definition(self, definition_id: UUID) -> RelationshipDefinition:
        with self._uow_factory() as uow:
            definition = uow.relationship_definitions.get(definition_id)
            if definition is None:
                raise RelationshipDefinitionNotFound("RelationshipDefinition does not exist.")
            return definition

    def create_relationship_definition(
        self,
        *,
        source_template_id: UUID,
        target_template_id: UUID,
        forward_name: str,
        reverse_name: str,
    ) -> RelationshipDefinition:
        with self._uow_factory() as uow:
            source_template = uow.object_templates.get(source_template_id)
            if source_template is None:
                raise RelationshipDefinitionTemplateNotFound(
                    "Source object template does not exist."
                )
            target_template = uow.object_templates.get(target_template_id)
            if target_template is None:
                raise RelationshipDefinitionTemplateNotFound(
                    "Target object template does not exist."
                )
            self._ensure_template_has_published_version(
                uow,
                template=source_template,
                endpoint_name="Source",
            )
            self._ensure_template_has_published_version(
                uow,
                template=target_template,
                endpoint_name="Target",
            )

            candidate = RelationshipDefinition(
                id=uuid4(),
                source_template_id=source_template.id,
                target_template_id=target_template.id,
                forward_name=forward_name,
                reverse_name=reverse_name,
            )

            snapshot = self._build_conflict_snapshot(uow)
            self._ensure_no_semantic_conflict(candidate, snapshot=snapshot)

            uow.relationship_definitions.add(candidate)
            uow.commit()
            return candidate

    def delete_relationship_definition(self, definition_id: UUID) -> None:
        with self._uow_factory() as uow:
            if uow.relationship_definitions.get(definition_id) is None:
                raise RelationshipDefinitionNotFound("RelationshipDefinition does not exist.")
            uow.relationship_definitions.delete(definition_id)
            uow.commit()

    def _ensure_template_has_published_version(
        self,
        uow: RelationshipDefinitionUnitOfWork,
        *,
        template: ObjectTemplate,
        endpoint_name: str,
    ) -> None:
        versions = uow.object_templates.list_versions(template.id)
        if any(
            version.status == ObjectTemplateVersionStatus.PUBLISHED for version in versions
        ):
            return
        raise RelationshipDefinitionTemplateNotPublished(
            f"{endpoint_name} object template has no published version."
        )

    def _build_conflict_snapshot(
        self,
        uow: RelationshipDefinitionUnitOfWork,
    ) -> _RelationshipDefinitionConflictSnapshot:
        templates = uow.object_templates.list()
        all_versions = tuple(
            version
            for template in templates
            for version in uow.object_templates.list_versions(template.id)
        )
        usable_versions = tuple(
            version
            for version in all_versions
            if version.status in (
                ObjectTemplateVersionStatus.PUBLISHED,
                ObjectTemplateVersionStatus.DEPRECATED,
            )
        )
        return _RelationshipDefinitionConflictSnapshot(
            templates=templates,
            all_versions=all_versions,
            usable_versions=usable_versions,
            existing_definitions=uow.relationship_definitions.list(),
        )

    def _ensure_no_semantic_conflict(
        self,
        candidate: RelationshipDefinition,
        *,
        snapshot: _RelationshipDefinitionConflictSnapshot,
    ) -> None:
        for existing in snapshot.existing_definitions:
            if relationship_definitions_are_semantically_equivalent(candidate, existing):
                raise RelationshipDefinitionSemanticConflict(
                    "RelationshipDefinition conflicts semantically with an existing definition."
                )

            if self._definitions_conflict(candidate, existing, snapshot=snapshot):
                raise RelationshipDefinitionSemanticConflict(
                    "RelationshipDefinition conflicts semantically with an existing definition."
                )

    def _definitions_conflict(
        self,
        candidate: RelationshipDefinition,
        existing: RelationshipDefinition,
        *,
        snapshot: _RelationshipDefinitionConflictSnapshot,
    ) -> bool:
        for (
            candidate_source_id,
            existing_source_id,
            candidate_target_id,
            existing_target_id,
        ) in self._matching_orientations(
            candidate,
            existing,
        ):
            if self._endpoint_spaces_overlap(
                candidate_source_id,
                existing_source_id,
                snapshot=snapshot,
            ) and self._endpoint_spaces_overlap(
                candidate_target_id,
                existing_target_id,
                snapshot=snapshot,
            ):
                return True
        return False

    def _matching_orientations(
        self,
        candidate: RelationshipDefinition,
        existing: RelationshipDefinition,
    ) -> tuple[tuple[UUID, UUID, UUID, UUID], ...]:
        orientations: list[tuple[UUID, UUID, UUID, UUID]] = []
        if (
            candidate.forward_name == existing.forward_name
            and candidate.reverse_name == existing.reverse_name
        ):
            orientations.append(
                (
                    candidate.source_template_id,
                    existing.source_template_id,
                    candidate.target_template_id,
                    existing.target_template_id,
                )
            )
        if (
            candidate.forward_name == existing.reverse_name
            and candidate.reverse_name == existing.forward_name
        ):
            orientations.append(
                (
                    candidate.source_template_id,
                    existing.target_template_id,
                    candidate.target_template_id,
                    existing.source_template_id,
                )
            )
        return tuple(orientations)

    def _endpoint_spaces_overlap(
        self,
        required_left_template_id: UUID,
        required_right_template_id: UUID,
        *,
        snapshot: _RelationshipDefinitionConflictSnapshot,
    ) -> bool:
        parent_lookup: Callable[[ObjectTemplateVersionRef], ObjectTemplateVersion | None] = (
            snapshot.lookup_parent
        )
        for version in snapshot.usable_versions:
            if self._inheritance.is_same_or_descendant_template(
                version,
                required_template_id=required_left_template_id,
                parent_lookup=parent_lookup,
            ) and self._inheritance.is_same_or_descendant_template(
                version,
                required_template_id=required_right_template_id,
                parent_lookup=parent_lookup,
            ):
                return True
        return False
