"""Application service for object template workflows."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from uuid import UUID, uuid4

from netauto.application.unit_of_work import (
    ObjectTemplateUnitOfWork,
    ObjectTemplateUnitOfWorkFactory,
)
from netauto.core.datatype import DataType, DataTypeVersion, DataTypeVersionStatus
from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateComponent,
    ObjectTemplateComponentVersionNotFound,
    ObjectTemplateComponentVersionNotPublished,
    ObjectTemplateDataTypeVersionNotFound,
    ObjectTemplateDataTypeVersionNotPublished,
    ObjectTemplateInUse,
    ObjectTemplateNotFound,
    ObjectTemplateProperty,
    ObjectTemplateVersion,
    ObjectTemplateVersioningService,
    ObjectTemplateVersionNotFound,
    ObjectTemplateVersionRef,
    ObjectTemplateVersionStatus,
)
from netauto.core.relationship import (
    RelationshipDefinitionConflictSnapshot,
    ensure_relationship_definition_set_has_no_conflicts,
)


@dataclass(frozen=True, slots=True)
class ObjectTemplatePropertySpec:
    """Application input for a property before datatype version resolution."""

    name: str
    datatype_id: UUID
    datatype_version: int | None = None
    required: bool = False

    def __post_init__(self) -> None:
        if self.datatype_version is None:
            return
        if (
            isinstance(self.datatype_version, bool)
            or not isinstance(self.datatype_version, int)
            or self.datatype_version < 1
        ):
            raise ValueError(
                "ObjectTemplatePropertySpec datatype_version must be a plain int >= 1 "
                "or None."
            )


@dataclass(frozen=True, slots=True)
class ObjectTemplateComponentSpec:
    """Application input for a component before template version resolution."""

    name: str
    template_id: UUID


class ObjectTemplateApplicationService:
    """Orchestrate object template use cases over a unit of work boundary."""

    def __init__(
        self,
        uow_factory: ObjectTemplateUnitOfWorkFactory,
        *,
        model_write_uow_factory: ObjectTemplateUnitOfWorkFactory,
    ) -> None:
        self._uow_factory = uow_factory
        self._model_write_uow_factory = model_write_uow_factory
        self._versioning = ObjectTemplateVersioningService()

    def _validate_parent_evolution(
        self,
        uow: ObjectTemplateUnitOfWork,
        *,
        prospective: ObjectTemplateVersion,
        existing_versions: Iterable[ObjectTemplateVersion],
    ) -> None:
        self._versioning.validate_parent_evolution(
            prospective,
            existing_versions=existing_versions,
            parent_lookup=lambda ref: (
                prospective
                if (
                    ref.template_id == prospective.template_id
                    and ref.version == prospective.version
                )
                else uow.object_templates.get_version(ref.template_id, ref.version)
            ),
        )

    def _resolve_properties(
        self,
        *,
        properties: Iterable[ObjectTemplatePropertySpec],
        datatype_getter: Callable[[UUID], DataType | None],
        datatype_version_getter: Callable[[UUID, int], DataTypeVersion | None],
        datatype_versions_lister: Callable[[UUID], tuple[DataTypeVersion, ...]],
    ) -> tuple[ObjectTemplateProperty, ...]:
        resolved: list[ObjectTemplateProperty] = []
        for spec in properties:
            if spec.datatype_version is not None:
                datatype_version = datatype_version_getter(
                    spec.datatype_id,
                    spec.datatype_version,
                )
                if datatype_version is None:
                    raise ObjectTemplateDataTypeVersionNotFound(
                        "Referenced datatype version was not found."
                    )
                if datatype_version.status is not DataTypeVersionStatus.PUBLISHED:
                    raise ObjectTemplateDataTypeVersionNotPublished(
                        "Referenced datatype version must be published."
                    )
                concrete_version = datatype_version.version
            else:
                published_versions = tuple(
                    version
                    for version in datatype_versions_lister(spec.datatype_id)
                    if version.status is DataTypeVersionStatus.PUBLISHED
                )
                if published_versions:
                    concrete_version = max(
                        published_versions,
                        key=lambda version: version.version,
                    ).version
                else:
                    if datatype_getter(spec.datatype_id) is None:
                        raise ObjectTemplateDataTypeVersionNotFound(
                            "Referenced datatype version was not found."
                        )
                    raise ObjectTemplateDataTypeVersionNotPublished(
                        "Referenced datatype version must be published."
                    )

            resolved.append(
                ObjectTemplateProperty(
                    name=spec.name,
                    datatype_id=spec.datatype_id,
                    datatype_version=concrete_version,
                    required=spec.required,
                )
            )
        return tuple(resolved)

    def _resolve_components(
        self,
        *,
        components: Iterable[ObjectTemplateComponentSpec],
        template_getter: Callable[[UUID], ObjectTemplate | None],
        template_versions_lister: Callable[[UUID], tuple[ObjectTemplateVersion, ...]],
    ) -> tuple[ObjectTemplateComponent, ...]:
        resolved: list[ObjectTemplateComponent] = []
        for spec in components:
            published_versions = tuple(
                version
                for version in template_versions_lister(spec.template_id)
                if version.status is ObjectTemplateVersionStatus.PUBLISHED
            )
            if not published_versions:
                if template_getter(spec.template_id) is None:
                    raise ObjectTemplateComponentVersionNotFound(
                        "Referenced component target template was not found."
                    )
                raise ObjectTemplateComponentVersionNotPublished(
                    "Referenced component target template must have a published version."
                )

            resolved.append(
                ObjectTemplateComponent(
                    name=spec.name,
                    template_id=spec.template_id,
                )
            )
        return tuple(resolved)

    def list_object_templates(self) -> tuple[ObjectTemplate, ...]:
        with self._uow_factory() as uow:
            return uow.object_templates.list()

    def get_object_template(self, template_id: UUID) -> ObjectTemplate:
        with self._uow_factory() as uow:
            template = uow.object_templates.get(template_id)
            if template is None:
                raise ObjectTemplateNotFound("Object template does not exist.")
            return template

    def get_object_template_by_name(self, namespace: str, name: str) -> ObjectTemplate:
        with self._uow_factory() as uow:
            template = uow.object_templates.get_by_name(namespace, name)
            if template is None:
                raise ObjectTemplateNotFound("Object template does not exist.")
            return template

    def delete_object_template(self, template_id: UUID) -> None:
        with self._model_write_uow_factory() as uow:
            template = uow.object_templates.get(template_id)
            if template is None:
                raise ObjectTemplateNotFound("Object template does not exist.")

            for object_value in uow.objects.list():
                if object_value.template_id == template_id:
                    raise ObjectTemplateInUse(
                        "Object template is still referenced by a current object."
                    )

            for candidate_template in uow.object_templates.list():
                for version in uow.object_templates.list_versions(candidate_template.id):
                    if candidate_template.id != template_id:
                        parent = version.parent
                        if parent is not None and parent.template_id == template_id:
                            raise ObjectTemplateInUse(
                                "Object template is still referenced by inheritance."
                            )
                        for component in version.components:
                            if component.template_id == template_id:
                                raise ObjectTemplateInUse(
                                    "Object template is still referenced by a component "
                                    "declaration."
                                )

            for definition in uow.relationship_definitions.list():
                if (
                    definition.source_template_id == template_id
                    or definition.target_template_id == template_id
                ):
                    raise ObjectTemplateInUse(
                        "Object template is still referenced by a relationship definition."
                    )

            uow.object_templates.delete(template_id)
            uow.commit()

    def list_versions(self, template_id: UUID) -> tuple[ObjectTemplateVersion, ...]:
        with self._uow_factory() as uow:
            template = uow.object_templates.get(template_id)
            if template is None:
                raise ObjectTemplateNotFound("Object template does not exist.")
            return uow.object_templates.list_versions(template_id)

    def get_version(self, template_id: UUID, version: int) -> ObjectTemplateVersion:
        with self._uow_factory() as uow:
            template = uow.object_templates.get(template_id)
            if template is None:
                raise ObjectTemplateNotFound("Object template does not exist.")
            loaded = uow.object_templates.get_version(template_id, version)
            if loaded is None:
                raise ObjectTemplateVersionNotFound("Object template version does not exist.")
            return loaded

    def create_object_template(
        self,
        *,
        namespace: str,
        name: str,
        description: str | None,
        abstract: bool,
        parent: ObjectTemplateVersionRef | None,
        properties: Iterable[ObjectTemplatePropertySpec],
        components: Iterable[ObjectTemplateComponentSpec] = (),
    ) -> tuple[ObjectTemplate, ObjectTemplateVersion]:
        with self._model_write_uow_factory() as uow:
            resolved_properties = self._resolve_properties(
                properties=properties,
                datatype_getter=uow.datatypes.get,
                datatype_version_getter=uow.datatypes.get_version,
                datatype_versions_lister=uow.datatypes.list_versions,
            )
            resolved_components = self._resolve_components(
                components=components,
                template_getter=uow.object_templates.get,
                template_versions_lister=uow.object_templates.list_versions,
            )
            template = ObjectTemplate(
                id=uuid4(),
                namespace=namespace,
                name=name,
                description=description,
                abstract=abstract,
            )
            version = ObjectTemplateVersion(
                template_id=template.id,
                version=1,
                status=ObjectTemplateVersionStatus.DRAFT,
                parent=parent,
                properties=resolved_properties,
                components=resolved_components,
            )
            self._validate_parent_evolution(
                uow,
                prospective=version,
                existing_versions=(),
            )
            uow.object_templates.add(template)
            uow.object_templates.add_version(version)
            uow.commit()
            return template, version

    def revise_version(
        self,
        *,
        template_id: UUID,
        version: int,
        parent: ObjectTemplateVersionRef | None,
        properties: Iterable[ObjectTemplatePropertySpec],
        components: Iterable[ObjectTemplateComponentSpec] = (),
    ) -> ObjectTemplateVersion:
        with self._model_write_uow_factory() as uow:
            template = uow.object_templates.get(template_id)
            if template is None:
                raise ObjectTemplateNotFound("Object template does not exist.")
            current = uow.object_templates.get_version(template_id, version)
            if current is None:
                raise ObjectTemplateVersionNotFound("Object template version does not exist.")
            resolved_properties = self._resolve_properties(
                properties=properties,
                datatype_getter=uow.datatypes.get,
                datatype_version_getter=uow.datatypes.get_version,
                datatype_versions_lister=uow.datatypes.list_versions,
            )
            resolved_components = self._resolve_components(
                components=components,
                template_getter=uow.object_templates.get,
                template_versions_lister=uow.object_templates.list_versions,
            )
            revised = self._versioning.revise_draft(
                current,
                parent=parent,
                properties=resolved_properties,
                components=resolved_components,
            )
            self._validate_parent_evolution(
                uow,
                prospective=revised,
                existing_versions=uow.object_templates.list_versions(template_id),
            )
            uow.object_templates.replace_version(revised)
            uow.commit()
            return revised

    def create_next_version(
        self,
        *,
        template_id: UUID,
        source_version: int,
    ) -> ObjectTemplateVersion:
        with self._model_write_uow_factory() as uow:
            template = uow.object_templates.get(template_id)
            if template is None:
                raise ObjectTemplateNotFound("Object template does not exist.")
            source = uow.object_templates.get_version(template_id, source_version)
            if source is None:
                raise ObjectTemplateVersionNotFound("Object template version does not exist.")
            existing_versions = uow.object_templates.list_versions(template_id)
            next_version = self._versioning.create_next_version(
                source,
                existing_versions=existing_versions,
            )
            self._validate_parent_evolution(
                uow,
                prospective=next_version,
                existing_versions=existing_versions,
            )
            uow.object_templates.add_version(next_version)
            uow.commit()
            return next_version

    def publish_version(self, *, template_id: UUID, version: int) -> ObjectTemplateVersion:
        with self._model_write_uow_factory() as uow:
            template = uow.object_templates.get(template_id)
            if template is None:
                raise ObjectTemplateNotFound("Object template does not exist.")
            current = uow.object_templates.get_version(template_id, version)
            if current is None:
                raise ObjectTemplateVersionNotFound("Object template version does not exist.")
            published = self._versioning.publish(
                current,
                parent_lookup=lambda ref: uow.object_templates.get_version(
                    ref.template_id,
                    ref.version,
                ),
                datatype_lookup=lambda datatype_id, datatype_version: uow.datatypes.get_version(
                    datatype_id,
                    datatype_version,
                ),
                template_exists=(
                    lambda candidate_id: uow.object_templates.get(candidate_id) is not None
                ),
                template_versions_lister=uow.object_templates.list_versions,
            )
            self._validate_parent_evolution(
                uow,
                prospective=published,
                existing_versions=uow.object_templates.list_versions(template_id),
            )
            prospective_snapshot = self._build_relationship_conflict_snapshot(
                uow,
                prospective_published=published,
            )
            ensure_relationship_definition_set_has_no_conflicts(
                uow.relationship_definitions.list(),
                snapshot=prospective_snapshot,
            )
            uow.object_templates.replace_version(published)
            uow.commit()
            return published

    def deprecate_version(self, *, template_id: UUID, version: int) -> ObjectTemplateVersion:
        with self._model_write_uow_factory() as uow:
            template = uow.object_templates.get(template_id)
            if template is None:
                raise ObjectTemplateNotFound("Object template does not exist.")
            current = uow.object_templates.get_version(template_id, version)
            if current is None:
                raise ObjectTemplateVersionNotFound("Object template version does not exist.")
            deprecated = self._versioning.deprecate(current)
            uow.object_templates.replace_version(deprecated)
            uow.commit()
            return deprecated

    def _build_relationship_conflict_snapshot(
        self,
        uow: ObjectTemplateUnitOfWork,
        *,
        prospective_published: ObjectTemplateVersion,
    ) -> RelationshipDefinitionConflictSnapshot:
        all_versions = tuple(
            version
            for template in uow.object_templates.list()
            for version in uow.object_templates.list_versions(template.id)
        )
        replaced_versions = tuple(
            prospective_published
            if (
                version.template_id == prospective_published.template_id
                and version.version == prospective_published.version
            )
            else version
            for version in all_versions
        )
        usable_versions = tuple(
            version
            for version in replaced_versions
            if version.status
            in (
                ObjectTemplateVersionStatus.PUBLISHED,
                ObjectTemplateVersionStatus.DEPRECATED,
            )
        )
        return RelationshipDefinitionConflictSnapshot(
            all_versions=replaced_versions,
            usable_versions=usable_versions,
        )
