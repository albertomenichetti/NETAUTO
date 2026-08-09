"""Application service for runtime object workflows."""

from collections.abc import Iterable, Mapping
from uuid import UUID, uuid4

from netauto.application.unit_of_work import ObjectUnitOfWork, ObjectUnitOfWorkFactory
from netauto.core.object import (
    AbstractObjectTemplateInstantiation,
    InvalidObjectPatch,
    Object,
    ObjectNotFound,
    ObjectTemplateVersionNotPublished,
    ObjectValidationEngine,
    ObjectValidationFailed,
)
from netauto.core.objecttemplate import (
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
