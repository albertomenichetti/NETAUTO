from uuid import UUID, uuid4

import pytest

from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateAlreadyExists,
    ObjectTemplateNotFound,
    ObjectTemplateProperty,
    ObjectTemplateVersion,
    ObjectTemplateVersionAlreadyExists,
    ObjectTemplateVersioningService,
    ObjectTemplateVersionNotFound,
    ObjectTemplateVersionStatus,
)
from netauto.persistence.memory.objecttemplate_repository import (
    InMemoryObjectTemplateRepository,
)


def _template(
    *,
    namespace: str = "network",
    name: str = "device",
    description: str | None = "Network device template",
    abstract: bool = False,
    template_id: UUID | None = None,
) -> ObjectTemplate:
    return ObjectTemplate(
        id=template_id or uuid4(),
        namespace=namespace,
        name=name,
        description=description,
        abstract=abstract,
    )


def _property(name: str) -> ObjectTemplateProperty:
    return ObjectTemplateProperty(name=name, datatype_id=uuid4(), datatype_version=1)


def _version(
    template_id: UUID,
    version: int,
    *,
    status: ObjectTemplateVersionStatus = ObjectTemplateVersionStatus.DRAFT,
    properties: tuple[ObjectTemplateProperty, ...] = (),
) -> ObjectTemplateVersion:
    return ObjectTemplateVersion(
        template_id=template_id,
        version=version,
        status=status,
        properties=properties,
    )


def test_list_empty() -> None:
    repo = InMemoryObjectTemplateRepository()

    assert repo.list() == ()


def test_list_returns_deterministic_ordering() -> None:
    repo = InMemoryObjectTemplateRepository()
    zeta = _template(namespace="zeta", name="beta", description=None)
    device = _template(namespace="network", name="device", description=None)
    router = _template(namespace="network", name="router", description=None)

    repo.add(zeta)
    repo.add(router)
    repo.add(device)

    listed = repo.list()

    assert [(template.namespace, template.name) for template in listed] == [
        ("network", "device"),
        ("network", "router"),
        ("zeta", "beta"),
    ]


def test_add_and_get_identity() -> None:
    repo = InMemoryObjectTemplateRepository()
    template = _template()

    repo.add(template)

    assert repo.get(template.id) == template


def test_get_unknown_identity_returns_none() -> None:
    repo = InMemoryObjectTemplateRepository()

    assert repo.get(uuid4()) is None


def test_get_by_name() -> None:
    repo = InMemoryObjectTemplateRepository()
    template = _template(namespace="network", name="router")

    repo.add(template)

    assert repo.get_by_name("network", "router") == template


def test_duplicate_uuid_rejected() -> None:
    repo = InMemoryObjectTemplateRepository()
    template = _template(template_id=uuid4(), namespace="network", name="device")
    duplicate = _template(
        template_id=template.id,
        namespace="network",
        name="router",
        description=None,
    )

    repo.add(template)

    with pytest.raises(ObjectTemplateAlreadyExists):
        repo.add(duplicate)


def test_duplicate_logical_name_rejected() -> None:
    repo = InMemoryObjectTemplateRepository()
    first = _template(namespace="network", name="device")
    second = _template(namespace="network", name="device")

    repo.add(first)

    with pytest.raises(ObjectTemplateAlreadyExists):
        repo.add(second)


def test_duplicate_add_does_not_partially_corrupt_name_index() -> None:
    repo = InMemoryObjectTemplateRepository()
    first = _template(namespace="network", name="device")
    duplicate = _template(namespace="network", name="device")

    repo.add(first)

    with pytest.raises(ObjectTemplateAlreadyExists):
        repo.add(duplicate)

    assert repo.get_by_name("network", "device") == first
    assert repo.get(duplicate.id) is None


def test_add_version() -> None:
    repo = InMemoryObjectTemplateRepository()
    template = _template()
    version = _version(template.id, 1, properties=(_property("hostname"),))

    repo.add(template)
    repo.add_version(version)

    assert repo.get_version(template.id, 1) == version


def test_add_version_with_missing_owning_template_rejected() -> None:
    repo = InMemoryObjectTemplateRepository()
    version = _version(uuid4(), 1)

    with pytest.raises(ObjectTemplateNotFound):
        repo.add_version(version)


def test_duplicate_version_rejected() -> None:
    repo = InMemoryObjectTemplateRepository()
    template = _template()
    version = _version(template.id, 1)

    repo.add(template)
    repo.add_version(version)

    with pytest.raises(ObjectTemplateVersionAlreadyExists):
        repo.add_version(version)


def test_get_version_exact() -> None:
    repo = InMemoryObjectTemplateRepository()
    template = _template()
    version = _version(template.id, 2)

    repo.add(template)
    repo.add_version(version)

    assert repo.get_version(template.id, 2) == version


def test_get_version_unknown_returns_none() -> None:
    repo = InMemoryObjectTemplateRepository()

    assert repo.get_version(uuid4(), 1) is None


def test_list_versions_ascending() -> None:
    repo = InMemoryObjectTemplateRepository()
    template = _template()
    v5 = _version(template.id, 5, status=ObjectTemplateVersionStatus.DEPRECATED)
    v1 = _version(template.id, 1, status=ObjectTemplateVersionStatus.PUBLISHED)
    v2 = _version(template.id, 2)

    repo.add(template)
    repo.add_version(v5)
    repo.add_version(v1)
    repo.add_version(v2)

    versions = repo.list_versions(template.id)

    assert tuple(version.version for version in versions) == (1, 2, 5)


def test_list_versions_for_unknown_or_no_versions_returns_empty_tuple() -> None:
    repo = InMemoryObjectTemplateRepository()
    template = _template()

    repo.add(template)

    assert repo.list_versions(template.id) == ()
    assert repo.list_versions(uuid4()) == ()


def test_replace_existing_version() -> None:
    repo = InMemoryObjectTemplateRepository()
    service = ObjectTemplateVersioningService()
    template = _template()
    draft = _version(template.id, 1, properties=(_property("hostname"),))
    revised = service.revise_draft(
        draft,
        parent=None,
        properties=(_property("serial"),),
    )

    repo.add(template)
    repo.add_version(draft)
    repo.replace_version(revised)

    loaded = repo.get_version(template.id, 1)

    assert loaded == revised


def test_replace_missing_version_rejected() -> None:
    repo = InMemoryObjectTemplateRepository()
    template = _template()
    version = _version(template.id, 1)

    repo.add(template)

    with pytest.raises(ObjectTemplateVersionNotFound):
        repo.replace_version(version)


def test_replaced_snapshot_keeps_same_key_and_exposes_new_state() -> None:
    repo = InMemoryObjectTemplateRepository()
    service = ObjectTemplateVersioningService()
    template = _template()
    published = _version(
        template.id,
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        properties=(_property("hostname"),),
    )
    deprecated = service.deprecate(published)

    repo.add(template)
    repo.add_version(published)
    repo.replace_version(deprecated)

    loaded = repo.get_version(template.id, 1)

    assert loaded == deprecated
    assert loaded is not None
    assert loaded.template_id == template.id
    assert loaded.version == 1
    assert loaded.status is ObjectTemplateVersionStatus.DEPRECATED
