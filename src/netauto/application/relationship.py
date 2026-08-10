"""Application services for relationship definition and runtime relationship workflows."""

from uuid import UUID, uuid4

from netauto.application.unit_of_work import (
    RelationshipDefinitionUnitOfWork,
    RelationshipDefinitionUnitOfWorkFactory,
    RelationshipUnitOfWork,
    RelationshipUnitOfWorkFactory,
)
from netauto.core.object import ObjectNotFound
from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateVersionLookup,
    ObjectTemplateVersionNotFound,
    ObjectTemplateVersionStatus,
)
from netauto.core.relationship import (
    EffectiveRelationshipDefinition,
    Relationship,
    RelationshipAlreadyExists,
    RelationshipDefinition,
    RelationshipDefinitionConflictSnapshot,
    RelationshipDefinitionInUse,
    RelationshipDefinitionNotFound,
    RelationshipDefinitionTemplateNotFound,
    RelationshipDefinitionTemplateNotPublished,
    RelationshipDirection,
    RelationshipEndpointIncompatible,
    RelationshipNavigationView,
    RelationshipNotFound,
    RelationshipObjectNotFound,
    ensure_relationship_definition_does_not_conflict,
    relationship_definition_applies,
    relationship_definition_source_applies,
    relationship_definition_target_applies,
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
            if uow.relationships.list_by_definition(definition_id):
                raise RelationshipDefinitionInUse("Relationship definition is in use.")
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


class RelationshipApplicationService:
    """Orchestrate runtime relationship workflows over a unit of work boundary."""

    def __init__(self, uow_factory: RelationshipUnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    def list_relationships(self) -> tuple[Relationship, ...]:
        with self._uow_factory() as uow:
            return uow.relationships.list()

    def get_relationship(self, relationship_id: UUID) -> Relationship:
        with self._uow_factory() as uow:
            relationship = uow.relationships.get(relationship_id)
            if relationship is None:
                raise RelationshipNotFound("Relationship does not exist.")
            return relationship

    def list_effective_relationship_definitions(
        self,
        object_id: UUID,
    ) -> tuple[EffectiveRelationshipDefinition, ...]:
        with self._uow_factory() as uow:
            object_value = uow.objects.get(object_id)
            if object_value is None:
                raise ObjectNotFound("Object does not exist.")

            object_version = uow.object_templates.get_version(
                object_value.template_id,
                object_value.template_version,
            )
            if object_version is None:
                raise ObjectTemplateVersionNotFound(
                    "Referenced object template version was not found."
                )

            parent_lookup = self._build_parent_lookup(uow)
            views: list[EffectiveRelationshipDefinition] = []
            for definition in uow.relationship_definitions.list():
                if relationship_definition_source_applies(
                    definition,
                    object_version=object_version,
                    parent_lookup=parent_lookup,
                ):
                    views.append(
                        EffectiveRelationshipDefinition(
                            relationship_definition_id=definition.id,
                            direction=RelationshipDirection.OUTGOING,
                            name=definition.forward_name,
                            related_template_id=definition.target_template_id,
                        )
                    )
                if relationship_definition_target_applies(
                    definition,
                    object_version=object_version,
                    parent_lookup=parent_lookup,
                ):
                    views.append(
                        EffectiveRelationshipDefinition(
                            relationship_definition_id=definition.id,
                            direction=RelationshipDirection.INCOMING,
                            name=definition.reverse_name,
                            related_template_id=definition.source_template_id,
                        )
                    )
            return tuple(views)

    def list_outgoing_relationships(
        self,
        object_id: UUID,
    ) -> tuple[RelationshipNavigationView, ...]:
        return self._list_navigation_views(
            object_id,
            directions=(RelationshipDirection.OUTGOING,),
        )

    def list_incoming_relationships(
        self,
        object_id: UUID,
    ) -> tuple[RelationshipNavigationView, ...]:
        return self._list_navigation_views(
            object_id,
            directions=(RelationshipDirection.INCOMING,),
        )

    def list_neighbor_relationships(
        self,
        object_id: UUID,
    ) -> tuple[RelationshipNavigationView, ...]:
        return self._list_navigation_views(
            object_id,
            directions=(
                RelationshipDirection.OUTGOING,
                RelationshipDirection.INCOMING,
            ),
        )

    def create_relationship(
        self,
        *,
        relationship_definition_id: UUID,
        source_object_id: UUID,
        target_object_id: UUID,
    ) -> Relationship:
        with self._uow_factory() as uow:
            definition = uow.relationship_definitions.get(relationship_definition_id)
            if definition is None:
                raise RelationshipDefinitionNotFound("RelationshipDefinition does not exist.")

            source_object = uow.objects.get(source_object_id)
            if source_object is None:
                raise RelationshipObjectNotFound("Source object does not exist.")
            target_object = uow.objects.get(target_object_id)
            if target_object is None:
                raise RelationshipObjectNotFound("Target object does not exist.")

            source_version = uow.object_templates.get_version(
                source_object.template_id,
                source_object.template_version,
            )
            if source_version is None:
                raise ObjectTemplateVersionNotFound(
                    "Referenced object template version was not found."
                )
            target_version = uow.object_templates.get_version(
                target_object.template_id,
                target_object.template_version,
            )
            if target_version is None:
                raise ObjectTemplateVersionNotFound(
                    "Referenced object template version was not found."
                )

            parent_lookup = self._build_parent_lookup(uow)
            if not relationship_definition_applies(
                definition,
                source_version=source_version,
                target_version=target_version,
                parent_lookup=parent_lookup,
            ):
                raise RelationshipEndpointIncompatible(
                    "Object endpoints do not satisfy the relationship definition."
                )

            if (
                uow.relationships.get_by_endpoints(
                    definition.id,
                    source_object_id,
                    target_object_id,
                )
                is not None
            ):
                raise RelationshipAlreadyExists("Relationship already exists.")

            relationship = Relationship(
                id=uuid4(),
                relationship_definition_id=definition.id,
                source_object_id=source_object_id,
                target_object_id=target_object_id,
            )
            uow.relationships.add(relationship)
            uow.commit()
            return relationship

    def delete_relationship(self, relationship_id: UUID) -> None:
        with self._uow_factory() as uow:
            if uow.relationships.get(relationship_id) is None:
                raise RelationshipNotFound("Relationship does not exist.")
            uow.relationships.delete(relationship_id)
            uow.commit()

    def _list_navigation_views(
        self,
        object_id: UUID,
        *,
        directions: tuple[RelationshipDirection, ...],
    ) -> tuple[RelationshipNavigationView, ...]:
        with self._uow_factory() as uow:
            if uow.objects.get(object_id) is None:
                raise ObjectNotFound("Object does not exist.")

            relationships = uow.relationships.list_incident_to_objects({object_id})
            definitions = {
                definition.id: definition
                for definition in uow.relationship_definitions.list()
            }
            views: list[RelationshipNavigationView] = []
            for relationship in relationships:
                definition = definitions.get(relationship.relationship_definition_id)
                if definition is None:
                    raise RelationshipDefinitionNotFound(
                        "RelationshipDefinition does not exist."
                    )
                if (
                    RelationshipDirection.OUTGOING in directions
                    and relationship.source_object_id == object_id
                ):
                    views.append(
                        RelationshipNavigationView(
                            relationship_id=relationship.id,
                            relationship_definition_id=definition.id,
                            source_object_id=relationship.source_object_id,
                            target_object_id=relationship.target_object_id,
                            direction=RelationshipDirection.OUTGOING,
                            name=definition.forward_name,
                            related_object_id=relationship.target_object_id,
                        )
                    )
                if (
                    RelationshipDirection.INCOMING in directions
                    and relationship.target_object_id == object_id
                ):
                    views.append(
                        RelationshipNavigationView(
                            relationship_id=relationship.id,
                            relationship_definition_id=definition.id,
                            source_object_id=relationship.source_object_id,
                            target_object_id=relationship.target_object_id,
                            direction=RelationshipDirection.INCOMING,
                            name=definition.reverse_name,
                            related_object_id=relationship.source_object_id,
                        )
                    )
            return tuple(views)

    @staticmethod
    def _build_parent_lookup(
        uow: RelationshipUnitOfWork,
    ) -> ObjectTemplateVersionLookup:
        versions = {
            (version.template_id, version.version): version
            for template in uow.object_templates.list()
            for version in uow.object_templates.list_versions(template.id)
        }

        def lookup(version_ref):
            return versions.get((version_ref.template_id, version_ref.version))

        return lookup
