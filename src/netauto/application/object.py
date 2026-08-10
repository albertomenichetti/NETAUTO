"""Application service for runtime object workflows."""

from collections.abc import Iterable, Mapping
from uuid import UUID, uuid4

from netauto.application.unit_of_work import ObjectUnitOfWork, ObjectUnitOfWorkFactory
from netauto.core.object import (
    AbstractObjectTemplateInstantiation,
    ComponentMembership,
    ComponentMembershipAlreadyExists,
    ComponentMembershipNotFound,
    ComponentOwnershipCycle,
    InvalidObjectPatch,
    MissingObjectMigrationPropertyValue,
    Object,
    ObjectComponentSlotNotFound,
    ObjectComponentTemplateIncompatible,
    ObjectMigrationBlocked,
    ObjectMigrationResult,
    ObjectMigrationTargetVersionNotNewer,
    ObjectMigrationTargetVersionNotPublished,
    ObjectNotFound,
    ObjectTemplateMigrationAddedComponent,
    ObjectTemplateMigrationAddedProperty,
    ObjectTemplateMigrationAnalysis,
    ObjectTemplateMigrationBlockingChange,
    ObjectTemplateMigrationBlockingChangeKind,
    ObjectTemplateVersionNotPublished,
    ObjectValidationEngine,
    ObjectValidationFailed,
    UnexpectedObjectMigrationPropertyValue,
)
from netauto.core.objecttemplate import (
    ObjectTemplateComponent,
    ObjectTemplateInheritanceResolver,
    ObjectTemplateNotFound,
    ObjectTemplateProperty,
    ObjectTemplateVersion,
    ObjectTemplateVersionNotFound,
    ObjectTemplateVersionRef,
    ObjectTemplateVersionStatus,
)


class ObjectApplicationService:
    """Orchestrate object workflows over a unit of work boundary."""

    def __init__(self, uow_factory: ObjectUnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory
        self._validation = ObjectValidationEngine()
        self._inheritance = ObjectTemplateInheritanceResolver()

    def create_object(
        self,
        *,
        template_id: UUID,
        template_version: int,
        properties: Mapping[str, object],
    ) -> Object:
        with self._uow_factory() as uow:
            template = uow.object_templates.get(template_id)
            if template is None:
                raise ObjectTemplateNotFound("Object template does not exist.")

            version = self._get_template_version(
                uow,
                template_id=template_id,
                template_version=template_version,
            )
            if version.status is not ObjectTemplateVersionStatus.PUBLISHED:
                raise ObjectTemplateVersionNotPublished(
                    "Object template version must be published."
                )
            if template.abstract:
                raise AbstractObjectTemplateInstantiation(
                    "Abstract object template cannot be instantiated."
                )

            effective_properties = self._resolve_effective_properties(uow, version)
            result = self._validation.validate_properties(
                properties=properties,
                effective_properties=effective_properties,
                datatype_lookup=uow.datatypes.get_version,
            )
            if not result.is_valid:
                raise ObjectValidationFailed(result)

            created = Object(
                id=uuid4(),
                template_id=template_id,
                template_version=template_version,
                properties=properties,
            )
            uow.objects.add(created)
            uow.commit()
            return created

    def list_objects(self) -> tuple[Object, ...]:
        with self._uow_factory() as uow:
            return uow.objects.list()

    def get_object(self, object_id: UUID) -> Object:
        with self._uow_factory() as uow:
            object_value = uow.objects.get(object_id)
            if object_value is None:
                raise ObjectNotFound("Object does not exist.")
            return object_value

    def update_object(
        self,
        *,
        object_id: UUID,
        properties: Mapping[str, object] | None = None,
        remove_properties: Iterable[str] = (),
    ) -> Object:
        with self._uow_factory() as uow:
            current = uow.objects.get(object_id)
            if current is None:
                raise ObjectNotFound("Object does not exist.")

            set_properties = dict(properties or {})
            remove_names = tuple(remove_properties)
            if not set_properties and not remove_names:
                return current

            self._validate_patch_shape(set_properties=set_properties, remove_names=remove_names)

            version = self._get_template_version(
                uow,
                template_id=current.template_id,
                template_version=current.template_version,
            )
            effective_properties = self._resolve_effective_properties(uow, version)
            declared_names = {property_value.name for property_value in effective_properties}
            for property_name in remove_names:
                if property_name not in declared_names:
                    raise InvalidObjectPatch(
                        "Cannot remove a property that is not declared in the template."
                    )

            candidate = dict(current.properties)
            candidate.update(set_properties)
            for property_name in remove_names:
                candidate.pop(property_name, None)

            result = self._validation.validate_properties(
                properties=candidate,
                effective_properties=effective_properties,
                datatype_lookup=uow.datatypes.get_version,
            )
            if not result.is_valid:
                raise ObjectValidationFailed(result)

            updated = Object(
                id=current.id,
                template_id=current.template_id,
                template_version=current.template_version,
                properties=candidate,
            )
            uow.objects.replace(updated)
            uow.commit()
            return updated

    def attach_component(
        self,
        *,
        parent_object_id: UUID,
        slot_name: str,
        child_object_id: UUID,
    ) -> ComponentMembership:
        with self._uow_factory() as uow:
            parent = uow.objects.get(parent_object_id)
            if parent is None:
                raise ObjectNotFound("Parent object does not exist.")

            child = uow.objects.get(child_object_id)
            if child is None:
                raise ObjectNotFound("Child object does not exist.")

            membership = ComponentMembership(
                parent_object_id=parent_object_id,
                slot_name=slot_name,
                child_object_id=child_object_id,
            )

            existing_owner = uow.objects.get_owner(child_object_id)
            if existing_owner is not None:
                raise ComponentMembershipAlreadyExists(
                    "Component membership for child object already exists."
                )

            parent_version = self._get_template_version(
                uow,
                template_id=parent.template_id,
                template_version=parent.template_version,
            )
            effective_components = self._resolve_effective_components(uow, parent_version)
            slot = self._find_component_slot(effective_components, slot_name)
            if slot is None:
                raise ObjectComponentSlotNotFound(
                    "Requested component slot is not defined in the parent template."
                )

            child_version = self._get_template_version(
                uow,
                template_id=child.template_id,
                template_version=child.template_version,
            )
            if not self._inheritance.is_same_or_descendant_template(
                child_version,
                required_template_id=slot.template_id,
                parent_lookup=lambda ref: self._lookup_parent_version(uow, ref),
            ):
                raise ObjectComponentTemplateIncompatible(
                    "Child object template is incompatible with the requested component slot."
                )

            self._ensure_no_ownership_cycle(
                uow,
                parent_object_id=parent_object_id,
                child_object_id=child_object_id,
            )
            uow.objects.add_membership(membership)
            uow.commit()
            return membership

    def detach_component(self, child_object_id: UUID) -> ComponentMembership:
        with self._uow_factory() as uow:
            child = uow.objects.get(child_object_id)
            if child is None:
                raise ObjectNotFound("Object does not exist.")

            membership = uow.objects.get_owner(child.id)
            if membership is None:
                raise ComponentMembershipNotFound("Component membership does not exist.")

            uow.objects.remove_membership(child.id)
            uow.commit()
            return membership

    def get_owner(self, child_object_id: UUID) -> ComponentMembership | None:
        with self._uow_factory() as uow:
            child = uow.objects.get(child_object_id)
            if child is None:
                raise ObjectNotFound("Object does not exist.")
            return uow.objects.get_owner(child.id)

    def list_components(
        self,
        parent_object_id: UUID,
        slot_name: str | None = None,
    ) -> tuple[ComponentMembership, ...]:
        with self._uow_factory() as uow:
            parent = uow.objects.get(parent_object_id)
            if parent is None:
                raise ObjectNotFound("Object does not exist.")
            return uow.objects.list_components(parent.id, slot_name=slot_name)

    def delete_object(self, object_id: UUID) -> None:
        with self._uow_factory() as uow:
            target = uow.objects.get(object_id)
            if target is None:
                raise ObjectNotFound("Object does not exist.")

            deletion_order = self._collect_subtree_postorder(uow, target.id)
            incident_relationships = uow.relationships.list_incident_to_objects(deletion_order)
            for relationship in incident_relationships:
                uow.relationships.delete(relationship.id)
            for candidate_id in deletion_order:
                uow.objects.delete(candidate_id)
            uow.commit()

    def analyze_object_migration(
        self,
        *,
        template_id: UUID,
        source_version: int,
        target_version: int,
    ) -> ObjectTemplateMigrationAnalysis:
        with self._uow_factory() as uow:
            return self._analyze_object_migration(
                uow,
                template_id=template_id,
                source_version=source_version,
                target_version=target_version,
            )

    def migrate_objects(
        self,
        *,
        template_id: UUID,
        source_version: int,
        target_version: int,
        property_values: Mapping[str, object],
    ) -> ObjectMigrationResult:
        with self._uow_factory() as uow:
            analysis = self._analyze_object_migration(
                uow,
                template_id=template_id,
                source_version=source_version,
                target_version=target_version,
            )
            if not analysis.automatic:
                raise ObjectMigrationBlocked("Object migration contains blocking schema changes.")

            values_by_name = dict(property_values)
            self._validate_migration_property_names(values_by_name, analysis=analysis)

            target = self._get_template_version(
                uow,
                template_id=template_id,
                template_version=target_version,
            )
            target_effective_properties = self._resolve_effective_properties(uow, target)
            candidates = uow.objects.list_by_template_version(template_id, source_version)
            if not candidates:
                return ObjectMigrationResult(
                    template_id=template_id,
                    source_version=source_version,
                    target_version=target_version,
                    migrated_count=0,
                )

            self._validate_required_migration_property_values(
                values_by_name,
                analysis=analysis,
            )

            migrated_objects = [
                self._build_migrated_object(
                    current,
                    target_version=target_version,
                    property_values=values_by_name,
                    effective_properties=target_effective_properties,
                    datatype_lookup=uow.datatypes.get_version,
                )
                for current in candidates
            ]

            for migrated in migrated_objects:
                uow.objects.replace(migrated)
            uow.commit()
            return ObjectMigrationResult(
                template_id=template_id,
                source_version=source_version,
                target_version=target_version,
                migrated_count=len(migrated_objects),
            )

    def _get_template_version(
        self,
        uow: ObjectUnitOfWork,
        *,
        template_id: UUID,
        template_version: int,
    ) -> ObjectTemplateVersion:
        version = uow.object_templates.get_version(template_id, template_version)
        if version is None:
            raise ObjectTemplateVersionNotFound("Object template version does not exist.")
        return version

    def _resolve_effective_properties(
        self,
        uow: ObjectUnitOfWork,
        version: ObjectTemplateVersion,
    ) -> tuple[ObjectTemplateProperty, ...]:
        return self._inheritance.resolve_effective_properties(
            version,
            parent_lookup=lambda ref: self._lookup_parent_version(uow, ref),
        )

    def _resolve_effective_components(
        self,
        uow: ObjectUnitOfWork,
        version: ObjectTemplateVersion,
    ) -> tuple[ObjectTemplateComponent, ...]:
        return self._inheritance.resolve_effective_components(
            version,
            parent_lookup=lambda ref: self._lookup_parent_version(uow, ref),
        )

    def _lookup_parent_version(
        self,
        uow: ObjectUnitOfWork,
        ref: ObjectTemplateVersionRef,
    ) -> ObjectTemplateVersion | None:
        return uow.object_templates.get_version(ref.template_id, ref.version)

    def _validate_patch_shape(
        self,
        *,
        set_properties: Mapping[str, object],
        remove_names: tuple[object, ...],
    ) -> None:
        for property_name in remove_names:
            if not isinstance(property_name, str):
                raise InvalidObjectPatch("Property names in remove_properties must be strings.")

        overlapping_names = set(set_properties) & set(remove_names)
        if overlapping_names:
            raise InvalidObjectPatch(
                "The same property cannot be set and removed in one patch."
            )

    def _find_component_slot(
        self,
        effective_components: tuple[ObjectTemplateComponent, ...],
        slot_name: str,
    ) -> ObjectTemplateComponent | None:
        for component in effective_components:
            if component.name == slot_name:
                return component
        return None

    def _ensure_no_ownership_cycle(
        self,
        uow: ObjectUnitOfWork,
        *,
        parent_object_id: UUID,
        child_object_id: UUID,
    ) -> None:
        current_id = parent_object_id
        visited: set[UUID] = set()
        while True:
            if current_id == child_object_id:
                raise ComponentOwnershipCycle(
                    "Component attachment would create an ownership cycle."
                )
            if current_id in visited:
                raise ComponentOwnershipCycle(
                    "Component attachment encountered an ownership cycle."
                )
            visited.add(current_id)

            owner = uow.objects.get_owner(current_id)
            if owner is None:
                return
            current_id = owner.parent_object_id

    def _collect_subtree_postorder(
        self,
        uow: ObjectUnitOfWork,
        object_id: UUID,
    ) -> tuple[UUID, ...]:
        ordered: list[UUID] = []
        visiting: set[UUID] = set()
        visited: set[UUID] = set()

        def visit(current_id: UUID) -> None:
            if current_id in visited:
                return
            if current_id in visiting:
                raise ComponentOwnershipCycle(
                    "Object deletion encountered an ownership cycle."
                )

            visiting.add(current_id)
            for membership in uow.objects.list_components(current_id):
                visit(membership.child_object_id)
            visiting.remove(current_id)
            visited.add(current_id)
            ordered.append(current_id)

        visit(object_id)
        return tuple(ordered)

    def _analyze_object_migration(
        self,
        uow: ObjectUnitOfWork,
        *,
        template_id: UUID,
        source_version: int,
        target_version: int,
    ) -> ObjectTemplateMigrationAnalysis:
        template = uow.object_templates.get(template_id)
        if template is None:
            raise ObjectTemplateNotFound("Object template does not exist.")
        if target_version <= source_version:
            raise ObjectMigrationTargetVersionNotNewer(
                "Object migration target version must be newer than the source version."
            )

        source = self._get_template_version(
            uow,
            template_id=template_id,
            template_version=source_version,
        )
        target = self._get_template_version(
            uow,
            template_id=template_id,
            template_version=target_version,
        )
        if target.status is not ObjectTemplateVersionStatus.PUBLISHED:
            raise ObjectMigrationTargetVersionNotPublished(
                "Object migration target version must be published."
            )

        source_effective_properties = self._resolve_effective_properties(uow, source)
        target_effective_properties = self._resolve_effective_properties(uow, target)
        source_effective_components = self._resolve_effective_components(uow, source)
        target_effective_components = self._resolve_effective_components(uow, target)

        added_properties, property_blocking_changes = self._compare_properties(
            source_effective_properties,
            target_effective_properties,
        )
        added_components, component_blocking_changes = self._compare_components(
            source_effective_components,
            target_effective_components,
        )
        return ObjectTemplateMigrationAnalysis(
            template_id=template_id,
            source_version=source_version,
            target_version=target_version,
            added_properties=added_properties,
            added_components=added_components,
            blocking_changes=property_blocking_changes + component_blocking_changes,
        )

    def _compare_properties(
        self,
        source: tuple[ObjectTemplateProperty, ...],
        target: tuple[ObjectTemplateProperty, ...],
    ) -> tuple[
        tuple[ObjectTemplateMigrationAddedProperty, ...],
        tuple[ObjectTemplateMigrationBlockingChange, ...],
    ]:
        source_by_name = {property_value.name: property_value for property_value in source}
        target_by_name = {property_value.name: property_value for property_value in target}

        added = tuple(
            ObjectTemplateMigrationAddedProperty(
                name=name,
                required=target_by_name[name].required,
            )
            for name in sorted(target_by_name)
            if name not in source_by_name
        )
        blocking: list[ObjectTemplateMigrationBlockingChange] = []
        for name in sorted(source_by_name):
            if name not in target_by_name:
                blocking.append(
                    ObjectTemplateMigrationBlockingChange(
                        kind=ObjectTemplateMigrationBlockingChangeKind.PROPERTY_REMOVED,
                        name=name,
                    )
                )
            elif target_by_name[name] != source_by_name[name]:
                blocking.append(
                    ObjectTemplateMigrationBlockingChange(
                        kind=ObjectTemplateMigrationBlockingChangeKind.PROPERTY_CHANGED,
                        name=name,
                    )
                )
        return added, tuple(blocking)

    def _compare_components(
        self,
        source: tuple[ObjectTemplateComponent, ...],
        target: tuple[ObjectTemplateComponent, ...],
    ) -> tuple[
        tuple[ObjectTemplateMigrationAddedComponent, ...],
        tuple[ObjectTemplateMigrationBlockingChange, ...],
    ]:
        source_by_name = {component.name: component for component in source}
        target_by_name = {component.name: component for component in target}

        added = tuple(
            ObjectTemplateMigrationAddedComponent(
                name=name,
                template_id=target_by_name[name].template_id,
            )
            for name in sorted(target_by_name)
            if name not in source_by_name
        )
        blocking: list[ObjectTemplateMigrationBlockingChange] = []
        for name in sorted(source_by_name):
            if name not in target_by_name:
                blocking.append(
                    ObjectTemplateMigrationBlockingChange(
                        kind=ObjectTemplateMigrationBlockingChangeKind.COMPONENT_REMOVED,
                        name=name,
                    )
                )
            elif target_by_name[name] != source_by_name[name]:
                blocking.append(
                    ObjectTemplateMigrationBlockingChange(
                        kind=ObjectTemplateMigrationBlockingChangeKind.COMPONENT_CHANGED,
                        name=name,
                    )
                )
        return added, tuple(blocking)

    def _validate_migration_property_names(
        self,
        property_values: Mapping[str, object],
        *,
        analysis: ObjectTemplateMigrationAnalysis,
    ) -> None:
        added_by_name = {
            property_value.name: property_value for property_value in analysis.added_properties
        }
        unexpected_names = sorted(name for name in property_values if name not in added_by_name)
        if unexpected_names:
            raise UnexpectedObjectMigrationPropertyValue(
                "Migration supplied values may only target newly added properties."
            )

    def _validate_required_migration_property_values(
        self,
        property_values: Mapping[str, object],
        *,
        analysis: ObjectTemplateMigrationAnalysis,
    ) -> None:
        missing_required_names = [
            property_value.name
            for property_value in analysis.added_properties
            if property_value.required and property_value.name not in property_values
        ]
        if missing_required_names:
            raise MissingObjectMigrationPropertyValue(
                "Migration requires values for all newly added required properties."
            )

    def _build_migrated_object(
        self,
        current: Object,
        *,
        target_version: int,
        property_values: Mapping[str, object],
        effective_properties: tuple[ObjectTemplateProperty, ...],
        datatype_lookup,
    ) -> Object:
        candidate = dict(current.properties)
        candidate.update(property_values)
        result = self._validation.validate_properties(
            properties=candidate,
            effective_properties=effective_properties,
            datatype_lookup=datatype_lookup,
        )
        if not result.is_valid:
            raise ObjectValidationFailed(result)
        return Object(
            id=current.id,
            template_id=current.template_id,
            template_version=target_version,
            properties=candidate,
        )
