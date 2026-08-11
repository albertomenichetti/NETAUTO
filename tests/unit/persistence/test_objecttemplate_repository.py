from uuid import UUID, uuid4

import pytest

from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateAlreadyExists,
    ObjectTemplateComponent,
    ObjectTemplateNotFound,
    ObjectTemplatePersistenceError,
    ObjectTemplateProperty,
    ObjectTemplateVersion,
    ObjectTemplateVersionAlreadyExists,
    ObjectTemplateVersionNotFound,
    ObjectTemplateVersionRef,
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
    parent: ObjectTemplateVersionRef | None = None,
    properties: tuple[ObjectTemplateProperty, ...] = (),
    components: tuple[ObjectTemplateComponent, ...] = (),
) -> ObjectTemplateVersion:
    return ObjectTemplateVersion(
        template_id=template_id,
        version=version,
        status=status,
        parent=parent,
        properties=properties,
        components=components,
    )


def _store_versions(
    repo: InMemoryObjectTemplateRepository,
    template: ObjectTemplate,
    versions: tuple[ObjectTemplateVersion, ...],
) -> None:
    repo.add(template)
    for version in versions:
        draft = ObjectTemplateVersion(
            template_id=version.template_id,
            version=version.version,
            status=ObjectTemplateVersionStatus.DRAFT,
            parent=version.parent,
            properties=version.properties,
            components=version.components,
        )
        repo.add_version(draft)
        if version.status is ObjectTemplateVersionStatus.PUBLISHED:
            repo.replace_version(version)
        elif version.status is ObjectTemplateVersionStatus.DEPRECATED:
            repo.replace_version(
                ObjectTemplateVersion(
                    template_id=draft.template_id,
                    version=draft.version,
                    status=ObjectTemplateVersionStatus.PUBLISHED,
                    parent=draft.parent,
                    properties=draft.properties,
                    components=draft.components,
                )
            )
            repo.replace_version(version)


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

    _store_versions(repo, template, (version,))

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

    _store_versions(repo, template, (version,))

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

    _store_versions(repo, template, (v5, v1, v2))

    versions = repo.list_versions(template.id)

    assert tuple(version.version for version in versions) == (1, 2, 5)


def test_list_versions_for_unknown_or_no_versions_returns_empty_tuple() -> None:
    repo = InMemoryObjectTemplateRepository()
    template = _template()

    repo.add(template)

    assert repo.list_versions(template.id) == ()
    assert repo.list_versions(uuid4()) == ()


def test_delete_removes_identity_and_all_versions_only_for_target() -> None:
    repo = InMemoryObjectTemplateRepository()
    target = _template(name="device")
    unrelated = _template(name="router")
    _store_versions(
        repo,
        target,
        (
            _version(target.id, 1),
            _version(target.id, 2, status=ObjectTemplateVersionStatus.PUBLISHED),
        ),
    )
    _store_versions(repo, unrelated, (_version(unrelated.id, 1),))

    repo.delete(target.id)

    assert repo.get(target.id) is None
    assert repo.get_by_name(target.namespace, target.name) is None
    assert repo.list_versions(target.id) == ()
    assert repo.get(unrelated.id) == unrelated
    assert repo.list_versions(unrelated.id) == (_version(unrelated.id, 1),)


def test_delete_missing_identity_rejected() -> None:
    repo = InMemoryObjectTemplateRepository()

    with pytest.raises(ObjectTemplateNotFound):
        repo.delete(uuid4())


def test_replace_existing_version() -> None:
    repo = InMemoryObjectTemplateRepository()
    template = _template()
    draft = _version(template.id, 1, properties=(_property("hostname"),))
    revised = ObjectTemplateVersion(
        template_id=draft.template_id,
        version=draft.version,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=None,
        properties=(_property("serial"),),
        components=draft.components,
    )

    _store_versions(repo, template, (draft,))
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
    template = _template()
    draft = _version(
        template.id,
        1,
        properties=(_property("hostname"),),
    )
    published = ObjectTemplateVersion(
        template_id=draft.template_id,
        version=draft.version,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        parent=draft.parent,
        properties=draft.properties,
        components=draft.components,
    )
    deprecated = ObjectTemplateVersion(
        template_id=published.template_id,
        version=published.version,
        status=ObjectTemplateVersionStatus.DEPRECATED,
        parent=published.parent,
        properties=published.properties,
        components=published.components,
    )

    _store_versions(repo, template, (published,))
    repo.replace_version(deprecated)

    loaded = repo.get_version(template.id, 1)

    assert loaded == deprecated
    assert loaded is not None
    assert loaded.template_id == template.id
    assert loaded.version == 1
    assert loaded.status is ObjectTemplateVersionStatus.DEPRECATED


def test_add_version_requires_draft_status() -> None:
    repo = InMemoryObjectTemplateRepository()
    template = _template()
    published = _version(template.id, 1, status=ObjectTemplateVersionStatus.PUBLISHED)
    deprecated = _version(template.id, 1, status=ObjectTemplateVersionStatus.DEPRECATED)

    repo.add(template)

    with pytest.raises(ObjectTemplatePersistenceError):
        repo.add_version(published)
    with pytest.raises(ObjectTemplatePersistenceError):
        repo.add_version(deprecated)
    assert repo.get_version(template.id, 1) is None


def test_duplicate_version_precedes_add_status_validation() -> None:
    repo = InMemoryObjectTemplateRepository()
    template = _template()
    draft = _version(template.id, 1)
    published = _version(template.id, 1, status=ObjectTemplateVersionStatus.PUBLISHED)

    _store_versions(repo, template, (draft,))

    with pytest.raises(ObjectTemplateVersionAlreadyExists):
        repo.add_version(published)


def test_replace_version_allows_draft_revision_of_parent_properties_and_components() -> None:
    repo = InMemoryObjectTemplateRepository()
    template = _template(name="child")
    original = _version(template.id, 1, properties=(_property("hostname"),))
    parent = _template(name="parent")
    revised = ObjectTemplateVersion(
        template_id=template.id,
        version=1,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=ObjectTemplateVersionRef(template_id=parent.id, version=2),
        properties=(original.properties[0], _property("serial")),
    )

    repo.add(parent)
    _store_versions(repo, template, (original,))
    repo.replace_version(revised)

    assert repo.get_version(template.id, 1) == revised


def test_replace_version_allows_draft_to_published_status_only() -> None:
    repo = InMemoryObjectTemplateRepository()
    template = _template()
    draft = _version(template.id, 1, properties=(_property("hostname"),))
    published = ObjectTemplateVersion(
        template_id=draft.template_id,
        version=draft.version,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        parent=draft.parent,
        properties=draft.properties,
        components=draft.components,
    )

    _store_versions(repo, template, (draft,))
    repo.replace_version(published)

    assert repo.get_version(template.id, 1) == published


@pytest.mark.parametrize(
    "replacement",
    [
        lambda draft: ObjectTemplateVersion(
            template_id=draft.template_id,
            version=draft.version,
            status=ObjectTemplateVersionStatus.PUBLISHED,
            parent=ObjectTemplateVersionRef(template_id=uuid4(), version=2),
            properties=draft.properties,
            components=draft.components,
        ),
        lambda draft: ObjectTemplateVersion(
            template_id=draft.template_id,
            version=draft.version,
            status=ObjectTemplateVersionStatus.PUBLISHED,
            parent=draft.parent,
            properties=(draft.properties[0], _property("serial")),
            components=draft.components,
        ),
        lambda draft: ObjectTemplateVersion(
            template_id=draft.template_id,
            version=draft.version,
            status=ObjectTemplateVersionStatus.PUBLISHED,
            parent=draft.parent,
            properties=tuple(reversed(draft.properties)),
            components=draft.components,
        ),
    ],
)
def test_replace_version_rejects_publication_snapshot_change(
    replacement,
) -> None:
    repo = InMemoryObjectTemplateRepository()
    template = _template()
    first = _property("hostname")
    second = _property("serial")
    draft = _version(template.id, 1, properties=(first, second))

    _store_versions(repo, template, (draft,))

    with pytest.raises(ObjectTemplatePersistenceError):
        repo.replace_version(replacement(draft))
    assert repo.get_version(template.id, 1) == draft


def test_replace_version_allows_published_to_deprecated_status_only() -> None:
    repo = InMemoryObjectTemplateRepository()
    template = _template()
    draft = _version(template.id, 1, properties=(_property("hostname"),))
    published = ObjectTemplateVersion(
        template_id=draft.template_id,
        version=draft.version,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        parent=draft.parent,
        properties=draft.properties,
        components=draft.components,
    )
    deprecated = ObjectTemplateVersion(
        template_id=published.template_id,
        version=published.version,
        status=ObjectTemplateVersionStatus.DEPRECATED,
        parent=published.parent,
        properties=published.properties,
        components=published.components,
    )

    _store_versions(repo, template, (published,))
    repo.replace_version(deprecated)

    assert repo.get_version(template.id, 1) == deprecated


def test_replace_version_rejects_deprecation_snapshot_change() -> None:
    repo = InMemoryObjectTemplateRepository()
    template = _template()
    draft = _version(template.id, 1, properties=(_property("hostname"),))
    published = ObjectTemplateVersion(
        template_id=draft.template_id,
        version=draft.version,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        parent=draft.parent,
        properties=draft.properties,
        components=draft.components,
    )
    illegal = ObjectTemplateVersion(
        template_id=published.template_id,
        version=published.version,
        status=ObjectTemplateVersionStatus.DEPRECATED,
        parent=published.parent,
        properties=(published.properties[0], _property("serial")),
        components=published.components,
    )

    _store_versions(repo, template, (published,))

    with pytest.raises(ObjectTemplatePersistenceError):
        repo.replace_version(illegal)
    assert repo.get_version(template.id, 1) == published


@pytest.mark.parametrize(
    ("stored", "replacement_status"),
    [
        (ObjectTemplateVersionStatus.DRAFT, ObjectTemplateVersionStatus.DEPRECATED),
        (ObjectTemplateVersionStatus.PUBLISHED, ObjectTemplateVersionStatus.PUBLISHED),
        (ObjectTemplateVersionStatus.PUBLISHED, ObjectTemplateVersionStatus.DRAFT),
        (ObjectTemplateVersionStatus.DEPRECATED, ObjectTemplateVersionStatus.DEPRECATED),
        (ObjectTemplateVersionStatus.DEPRECATED, ObjectTemplateVersionStatus.PUBLISHED),
        (ObjectTemplateVersionStatus.DEPRECATED, ObjectTemplateVersionStatus.DRAFT),
    ],
)
def test_replace_version_rejects_other_lifecycle_rewrites(
    stored: ObjectTemplateVersionStatus,
    replacement_status: ObjectTemplateVersionStatus,
) -> None:
    repo = InMemoryObjectTemplateRepository()
    template = _template()
    base_draft = _version(template.id, 1, properties=(_property("hostname"),))
    current = base_draft
    if stored is ObjectTemplateVersionStatus.PUBLISHED:
        current = ObjectTemplateVersion(
            template_id=base_draft.template_id,
            version=base_draft.version,
            status=ObjectTemplateVersionStatus.PUBLISHED,
            parent=base_draft.parent,
            properties=base_draft.properties,
            components=base_draft.components,
        )
    elif stored is ObjectTemplateVersionStatus.DEPRECATED:
        published = ObjectTemplateVersion(
            template_id=base_draft.template_id,
            version=base_draft.version,
            status=ObjectTemplateVersionStatus.PUBLISHED,
            parent=base_draft.parent,
            properties=base_draft.properties,
            components=base_draft.components,
        )
        current = ObjectTemplateVersion(
            template_id=published.template_id,
            version=published.version,
            status=ObjectTemplateVersionStatus.DEPRECATED,
            parent=published.parent,
            properties=published.properties,
            components=published.components,
        )

    _store_versions(repo, template, (current,))

    illegal = ObjectTemplateVersion(
        template_id=current.template_id,
        version=current.version,
        status=replacement_status,
        parent=current.parent,
        properties=current.properties,
        components=current.components,
    )
    with pytest.raises(ObjectTemplatePersistenceError):
        repo.replace_version(illegal)
    assert repo.get_version(template.id, 1) == current
