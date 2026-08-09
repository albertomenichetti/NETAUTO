from uuid import UUID, uuid4

import pytest

from netauto.core.datatype import (
    DataTypeVersion,
    DataTypeVersionStatus,
    PrimitiveTypeRegistry,
)
from netauto.core.objecttemplate import (
    InheritedObjectTemplatePropertyConflict,
    InvalidObjectTemplateVersionTransition,
    MismatchedObjectTemplateVersion,
    ObjectTemplateDataTypeVersionNotFound,
    ObjectTemplateDataTypeVersionNotPublished,
    ObjectTemplateInheritanceCycle,
    ObjectTemplateParentNotFound,
    ObjectTemplateParentNotPublished,
    ObjectTemplateProperty,
    ObjectTemplateSelfInheritance,
    ObjectTemplateVersion,
    ObjectTemplateVersioningService,
    ObjectTemplateVersionRef,
    ObjectTemplateVersionStatus,
)


def _datatype_version(
    datatype_id: UUID,
    version: int,
    *,
    status: DataTypeVersionStatus,
) -> DataTypeVersion:
    return DataTypeVersion(
        datatype_id=datatype_id,
        version=version,
        status=status,
        base_type=PrimitiveTypeRegistry().get("core.string"),
        constraints=(),
    )


def _property(
    name: str,
    *,
    datatype_id: UUID | None = None,
    datatype_version: int = 1,
) -> ObjectTemplateProperty:
    return ObjectTemplateProperty(
        name=name,
        datatype_id=datatype_id or uuid4(),
        datatype_version=datatype_version,
    )


def _version(
    template_id: UUID,
    version: int,
    *,
    status: ObjectTemplateVersionStatus,
    parent: ObjectTemplateVersionRef | None = None,
    properties: tuple[ObjectTemplateProperty, ...] = (),
) -> ObjectTemplateVersion:
    return ObjectTemplateVersion(
        template_id=template_id,
        version=version,
        status=status,
        parent=parent,
        properties=properties,
    )


def test_revise_draft_returns_replacement_snapshot() -> None:
    service = ObjectTemplateVersioningService()
    template_id = uuid4()
    original = _version(
        template_id,
        1,
        status=ObjectTemplateVersionStatus.DRAFT,
        properties=(_property("hostname"),),
    )
    parent = ObjectTemplateVersionRef(template_id=uuid4(), version=2)
    revised_property = _property("serial")

    revised = service.revise_draft(
        original,
        parent=parent,
        properties=(revised_property,),
    )

    assert revised.template_id == original.template_id
    assert revised.version == original.version
    assert revised.status is ObjectTemplateVersionStatus.DRAFT
    assert revised.parent == parent
    assert revised.properties == (revised_property,)
    assert original.parent is None
    assert tuple(prop.name for prop in original.properties) == ("hostname",)


@pytest.mark.parametrize(
    "status",
    [ObjectTemplateVersionStatus.PUBLISHED, ObjectTemplateVersionStatus.DEPRECATED],
)
def test_revise_non_draft_rejected(status: ObjectTemplateVersionStatus) -> None:
    service = ObjectTemplateVersioningService()
    version = _version(uuid4(), 1, status=status)

    with pytest.raises(InvalidObjectTemplateVersionTransition):
        service.revise_draft(version, parent=None, properties=())


def test_publish_valid_root_template() -> None:
    service = ObjectTemplateVersioningService()
    datatype_id = uuid4()
    draft = _version(
        uuid4(),
        1,
        status=ObjectTemplateVersionStatus.DRAFT,
        properties=(_property("hostname", datatype_id=datatype_id),),
    )
    datatype_versions = {
        (datatype_id, 1): _datatype_version(
            datatype_id,
            1,
            status=DataTypeVersionStatus.PUBLISHED,
        )
    }

    published = service.publish(
        draft,
        parent_lookup=lambda _: None,
        datatype_lookup=lambda datatype_uuid, version: datatype_versions.get(
            (datatype_uuid, version)
        ),
    )

    assert published.template_id == draft.template_id
    assert published.version == draft.version
    assert published.status is ObjectTemplateVersionStatus.PUBLISHED
    assert published.parent == draft.parent
    assert published.properties == draft.properties
    assert draft.status is ObjectTemplateVersionStatus.DRAFT


def test_publish_valid_inherited_template() -> None:
    service = ObjectTemplateVersioningService()
    parent_id = uuid4()
    inherited_datatype_id = uuid4()
    local_datatype_id = uuid4()
    parent = _version(
        parent_id,
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        properties=(_property("hostname", datatype_id=inherited_datatype_id),),
    )
    child = _version(
        uuid4(),
        1,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=ObjectTemplateVersionRef(template_id=parent_id, version=1),
        properties=(_property("routing_id", datatype_id=local_datatype_id),),
    )
    parent_versions = {(parent_id, 1): parent}
    datatype_versions = {
        (inherited_datatype_id, 1): _datatype_version(
            inherited_datatype_id,
            1,
            status=DataTypeVersionStatus.PUBLISHED,
        ),
        (local_datatype_id, 1): _datatype_version(
            local_datatype_id,
            1,
            status=DataTypeVersionStatus.PUBLISHED,
        ),
    }

    published = service.publish(
        child,
        parent_lookup=lambda ref: parent_versions.get((ref.template_id, ref.version)),
        datatype_lookup=lambda datatype_uuid, version: datatype_versions.get(
            (datatype_uuid, version)
        ),
    )

    assert published.status is ObjectTemplateVersionStatus.PUBLISHED
    assert published.parent == child.parent
    assert published.properties == child.properties


def test_publish_missing_parent() -> None:
    service = ObjectTemplateVersioningService()
    child = _version(
        uuid4(),
        1,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=ObjectTemplateVersionRef(template_id=uuid4(), version=1),
    )

    with pytest.raises(ObjectTemplateParentNotFound):
        service.publish(
            child,
            parent_lookup=lambda _: None,
            datatype_lookup=lambda _datatype_uuid, _version: None,
        )


def test_publish_parent_not_published() -> None:
    service = ObjectTemplateVersioningService()
    parent_id = uuid4()
    datatype_id = uuid4()
    parent = _version(
        parent_id,
        1,
        status=ObjectTemplateVersionStatus.DEPRECATED,
        properties=(_property("hostname", datatype_id=datatype_id),),
    )
    child = _version(
        uuid4(),
        1,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=ObjectTemplateVersionRef(template_id=parent_id, version=1),
    )
    datatype_versions = {
        (datatype_id, 1): _datatype_version(
            datatype_id,
            1,
            status=DataTypeVersionStatus.PUBLISHED,
        )
    }

    with pytest.raises(ObjectTemplateParentNotPublished):
        service.publish(
            child,
            parent_lookup=lambda _ref: parent,
            datatype_lookup=lambda datatype_uuid, version: datatype_versions.get(
                (datatype_uuid, version)
            ),
        )


def test_publish_inheritance_conflict_behavior_is_preserved() -> None:
    service = ObjectTemplateVersioningService()
    parent_id = uuid4()
    datatype_id = uuid4()
    parent = _version(
        parent_id,
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        properties=(_property("hostname", datatype_id=datatype_id),),
    )
    child = _version(
        uuid4(),
        1,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=ObjectTemplateVersionRef(template_id=parent_id, version=1),
        properties=(_property("hostname", datatype_id=datatype_id),),
    )

    with pytest.raises(InheritedObjectTemplatePropertyConflict):
        service.publish(
            child,
            parent_lookup=lambda _ref: parent,
            datatype_lookup=lambda _datatype_uuid, _version: _datatype_version(
                datatype_id,
                1,
                status=DataTypeVersionStatus.PUBLISHED,
            ),
        )


def test_publish_inheritance_cycle_behavior_is_preserved() -> None:
    service = ObjectTemplateVersioningService()
    first_id = uuid4()
    second_id = uuid4()
    datatype_id = uuid4()
    first = _version(
        first_id,
        1,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=ObjectTemplateVersionRef(template_id=second_id, version=1),
        properties=(_property("hostname", datatype_id=datatype_id),),
    )
    second = _version(
        second_id,
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        parent=ObjectTemplateVersionRef(template_id=first_id, version=1),
        properties=(_property("serial", datatype_id=datatype_id),),
    )
    parents = {
        (first_id, 1): first,
        (second_id, 1): second,
    }

    with pytest.raises(ObjectTemplateInheritanceCycle):
        service.publish(
            first,
            parent_lookup=lambda ref: parents.get((ref.template_id, ref.version)),
            datatype_lookup=lambda _datatype_uuid, _version: _datatype_version(
                datatype_id,
                1,
                status=DataTypeVersionStatus.PUBLISHED,
            ),
        )


def test_publish_self_inheritance_behavior_is_preserved() -> None:
    service = ObjectTemplateVersioningService()
    template_id = uuid4()
    version = _version(
        template_id,
        1,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=ObjectTemplateVersionRef(template_id=template_id, version=1),
    )

    with pytest.raises(ObjectTemplateSelfInheritance):
        service.publish(
            version,
            parent_lookup=lambda _: pytest.fail("parent_lookup should not be called"),
            datatype_lookup=lambda _datatype_uuid, _version: None,
        )


def test_publish_missing_datatype_version() -> None:
    service = ObjectTemplateVersioningService()
    draft = _version(
        uuid4(),
        1,
        status=ObjectTemplateVersionStatus.DRAFT,
        properties=(_property("hostname"),),
    )

    with pytest.raises(ObjectTemplateDataTypeVersionNotFound):
        service.publish(
            draft,
            parent_lookup=lambda _: None,
            datatype_lookup=lambda _datatype_uuid, _version: None,
        )


@pytest.mark.parametrize(
    "status",
    [DataTypeVersionStatus.DRAFT, DataTypeVersionStatus.DEPRECATED],
)
def test_publish_rejects_non_published_datatype_versions(
    status: DataTypeVersionStatus,
) -> None:
    service = ObjectTemplateVersioningService()
    datatype_id = uuid4()
    draft = _version(
        uuid4(),
        1,
        status=ObjectTemplateVersionStatus.DRAFT,
        properties=(_property("hostname", datatype_id=datatype_id),),
    )
    datatype_version = _datatype_version(datatype_id, 1, status=status)

    with pytest.raises(ObjectTemplateDataTypeVersionNotPublished):
        service.publish(
            draft,
            parent_lookup=lambda _: None,
            datatype_lookup=lambda _datatype_uuid, _version: datatype_version,
        )


def test_publish_checks_inherited_properties_datatypes_too() -> None:
    service = ObjectTemplateVersioningService()
    parent_id = uuid4()
    inherited_datatype_id = uuid4()
    local_datatype_id = uuid4()
    parent = _version(
        parent_id,
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        properties=(_property("hostname", datatype_id=inherited_datatype_id),),
    )
    child = _version(
        uuid4(),
        1,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=ObjectTemplateVersionRef(template_id=parent_id, version=1),
        properties=(_property("routing_id", datatype_id=local_datatype_id),),
    )
    datatype_versions = {
        (inherited_datatype_id, 1): _datatype_version(
            inherited_datatype_id,
            1,
            status=DataTypeVersionStatus.DRAFT,
        ),
        (local_datatype_id, 1): _datatype_version(
            local_datatype_id,
            1,
            status=DataTypeVersionStatus.PUBLISHED,
        ),
    }

    with pytest.raises(ObjectTemplateDataTypeVersionNotPublished):
        service.publish(
            child,
            parent_lookup=lambda _ref: parent,
            datatype_lookup=lambda datatype_uuid, version: datatype_versions.get(
                (datatype_uuid, version)
            ),
        )


def test_deprecate_published() -> None:
    service = ObjectTemplateVersioningService()
    published = _version(uuid4(), 1, status=ObjectTemplateVersionStatus.PUBLISHED)

    deprecated = service.deprecate(published)

    assert deprecated.template_id == published.template_id
    assert deprecated.version == published.version
    assert deprecated.status is ObjectTemplateVersionStatus.DEPRECATED
    assert deprecated.parent == published.parent
    assert deprecated.properties == published.properties


@pytest.mark.parametrize(
    "status",
    [ObjectTemplateVersionStatus.DRAFT, ObjectTemplateVersionStatus.DEPRECATED],
)
def test_invalid_deprecate_transitions(status: ObjectTemplateVersionStatus) -> None:
    service = ObjectTemplateVersioningService()
    version = _version(uuid4(), 1, status=status)

    with pytest.raises(InvalidObjectTemplateVersionTransition):
        service.deprecate(version)


def test_create_next_version_clones_parent_and_properties() -> None:
    service = ObjectTemplateVersioningService()
    parent = ObjectTemplateVersionRef(template_id=uuid4(), version=2)
    prop = _property("hostname")
    source = _version(
        uuid4(),
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        parent=parent,
        properties=(prop,),
    )

    next_version = service.create_next_version(source, existing_versions=(source,))

    assert next_version.version == 2
    assert next_version.status is ObjectTemplateVersionStatus.DRAFT
    assert next_version.parent == source.parent
    assert next_version.properties == source.properties


def test_create_next_version_uses_max_plus_one_including_existing_drafts() -> None:
    service = ObjectTemplateVersioningService()
    template_id = uuid4()
    source = _version(template_id, 1, status=ObjectTemplateVersionStatus.PUBLISHED)
    existing_versions = (
        source,
        _version(template_id, 2, status=ObjectTemplateVersionStatus.DRAFT),
        _version(template_id, 5, status=ObjectTemplateVersionStatus.DEPRECATED),
    )

    next_version = service.create_next_version(source, existing_versions=existing_versions)

    assert next_version.version == 6


def test_create_next_version_rejects_mismatched_existing_versions() -> None:
    service = ObjectTemplateVersioningService()
    source = _version(uuid4(), 1, status=ObjectTemplateVersionStatus.PUBLISHED)
    other = _version(uuid4(), 2, status=ObjectTemplateVersionStatus.PUBLISHED)

    with pytest.raises(MismatchedObjectTemplateVersion):
        service.create_next_version(source, existing_versions=(source, other))


@pytest.mark.parametrize(
    "status",
    [ObjectTemplateVersionStatus.DRAFT, ObjectTemplateVersionStatus.DEPRECATED],
)
def test_create_next_version_source_must_be_published(
    status: ObjectTemplateVersionStatus,
) -> None:
    service = ObjectTemplateVersioningService()
    source = _version(uuid4(), 1, status=status)

    with pytest.raises(InvalidObjectTemplateVersionTransition):
        service.create_next_version(source, existing_versions=())


def test_originals_remain_unchanged_after_operations() -> None:
    service = ObjectTemplateVersioningService()
    datatype_id = uuid4()
    original = _version(
        uuid4(),
        1,
        status=ObjectTemplateVersionStatus.DRAFT,
        properties=(_property("hostname", datatype_id=datatype_id),),
    )
    datatype_versions = {
        (datatype_id, 1): _datatype_version(
            datatype_id,
            1,
            status=DataTypeVersionStatus.PUBLISHED,
        )
    }

    published = service.publish(
        original,
        parent_lookup=lambda _: None,
        datatype_lookup=lambda datatype_uuid, version: datatype_versions.get(
            (datatype_uuid, version)
        ),
    )
    next_version = service.create_next_version(published, existing_versions=(published,))
    deprecated = service.deprecate(published)

    assert original.status is ObjectTemplateVersionStatus.DRAFT
    assert published.status is ObjectTemplateVersionStatus.PUBLISHED
    assert next_version.status is ObjectTemplateVersionStatus.DRAFT
    assert deprecated.status is ObjectTemplateVersionStatus.DEPRECATED
