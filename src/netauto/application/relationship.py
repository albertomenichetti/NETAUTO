"""Application service for relationship definition workflows."""

from uuid import UUID, uuid4

from netauto.application.unit_of_work import (
    RelationshipDefinitionUnitOfWork,
    RelationshipDefinitionUnitOfWorkFactory,
)
from netauto.core.objecttemplate import ObjectTemplate, ObjectTemplateVersionStatus
from netauto.core.relationship import (
    RelationshipDefinition,
    RelationshipDefinitionConflictSnapshot,
    RelationshipDefinitionNotFound,
    RelationshipDefinitionTemplateNotFound,
    RelationshipDefinitionTemplateNotPublished,
    ensure_relationship_definition_does_not_conflict,
)


class RelationshipDefinitionApplicationService:
    """Orchestrate relationship definition workflows over a unit of work boundary."""

    def __init__(self, uow_factory: RelationshipDefinitionUnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

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
            ensure_relationship_definition_does_not_conflict(
                candidate,
                existing_definitions=uow.relationship_definitions.list(),
                snapshot=snapshot,
            )

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
    ) -> RelationshipDefinitionConflictSnapshot:
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
        return RelationshipDefinitionConflictSnapshot(
            all_versions=all_versions,
            usable_versions=usable_versions,
        )
