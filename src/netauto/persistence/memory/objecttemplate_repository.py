"""In-memory object template repository implementation."""

from uuid import UUID

from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateAlreadyExists,
    ObjectTemplateNotFound,
    ObjectTemplateRepository,
    ObjectTemplateVersion,
    ObjectTemplateVersionAlreadyExists,
    ObjectTemplateVersionNotFound,
)
from netauto.core.objecttemplate.repository import (
    validate_object_template_version_add,
    validate_object_template_version_replace,
)


class InMemoryObjectTemplateRepository(ObjectTemplateRepository):
    """Reference in-memory object template repository."""

    def __init__(self) -> None:
        self._templates: dict[UUID, ObjectTemplate] = {}
        self._template_names: dict[tuple[str, str], UUID] = {}
        self._versions: dict[tuple[UUID, int], ObjectTemplateVersion] = {}

    def list(self) -> tuple[ObjectTemplate, ...]:
        templates = list(self._templates.values())
        templates.sort(key=lambda item: (item.namespace, item.name, str(item.id)))
        return tuple(templates)

    def add(self, template: ObjectTemplate) -> None:
        if template.id in self._templates:
            raise ObjectTemplateAlreadyExists("ObjectTemplate UUID already exists.")
        name_key = (template.namespace, template.name)
        if name_key in self._template_names:
            raise ObjectTemplateAlreadyExists("ObjectTemplate logical name already exists.")
        self._templates[template.id] = template
        self._template_names[name_key] = template.id

    def get(self, template_id: UUID) -> ObjectTemplate | None:
        return self._templates.get(template_id)

    def get_by_name(self, namespace: str, name: str) -> ObjectTemplate | None:
        template_id = self._template_names.get((namespace, name))
        if template_id is None:
            return None
        return self._templates[template_id]

    def delete(self, template_id: UUID) -> None:
        template = self._templates.get(template_id)
        if template is None:
            raise ObjectTemplateNotFound("ObjectTemplate does not exist.")
        del self._templates[template_id]
        del self._template_names[(template.namespace, template.name)]
        version_keys = [key for key in self._versions if key[0] == template_id]
        for version_key in version_keys:
            del self._versions[version_key]

    def add_version(self, version: ObjectTemplateVersion) -> None:
        if version.template_id not in self._templates:
            raise ObjectTemplateNotFound("Owning object template does not exist.")
        version_key = (version.template_id, version.version)
        if version_key in self._versions:
            raise ObjectTemplateVersionAlreadyExists("ObjectTemplate version already exists.")
        validate_object_template_version_add(version)
        self._versions[version_key] = version

    def get_version(self, template_id: UUID, version: int) -> ObjectTemplateVersion | None:
        return self._versions.get((template_id, version))

    def list_versions(self, template_id: UUID) -> tuple[ObjectTemplateVersion, ...]:
        versions = [
            version
            for (candidate_template_id, _), version in self._versions.items()
            if candidate_template_id == template_id
        ]
        versions.sort(key=lambda item: item.version)
        return tuple(versions)

    def replace_version(self, version: ObjectTemplateVersion) -> None:
        version_key = (version.template_id, version.version)
        current = self._versions.get(version_key)
        if current is None:
            raise ObjectTemplateVersionNotFound("ObjectTemplate version does not exist.")
        validate_object_template_version_replace(current, version)
        self._versions[version_key] = version
