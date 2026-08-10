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
    Object,
    ObjectComponentSlotNotFound,
    ObjectComponentTemplateIncompatible,
    ObjectNotFound,
    ObjectTemplateVersionNotPublished,
    ObjectValidationEngine,
    ObjectValidationFailed,
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
            required = ObjectTemplateVersionRef(
                template_id=slot.template_id,
                version=slot.template_version,
            )
            compatible = self._inheritance.is_same_or_descendant(
                child_version,
                required=required,
                parent_lookup=lambda ref: self._lookup_parent_version(uow, ref),
            )
            if not compatible:
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
