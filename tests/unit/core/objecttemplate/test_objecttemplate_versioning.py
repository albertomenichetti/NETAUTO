from uuid import UUID, uuid4

import pytest

from netauto.core.datatype import (
    DataTypeVersion,
    DataTypeVersionStatus,
    PrimitiveTypeRegistry,
)
from netauto.core.objecttemplate import (
    InheritedObjectTemplateComponentConflict,
    InheritedObjectTemplatePropertyConflict,
    InvalidObjectTemplateVersionTransition,
    MismatchedObjectTemplateVersion,
    ObjectTemplateComponent,
    ObjectTemplateComponentVersionNotFound,
    ObjectTemplateComponentVersionNotPublished,
    ObjectTemplateDataTypeVersionDowngrade,
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


def _component(
    name: str,
    *,
    template_id: UUID | None = None,
    template_version: int = 1,
) -> ObjectTemplateComponent:
    del template_version
    return ObjectTemplateComponent(
        name=name,
        template_id=template_id or uuid4(),
    )


def _version(
    template_id: UUID,
    version: int,
    *,
    status: ObjectTemplateVersionStatus,
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


def _publish(
    service: ObjectTemplateVersioningService,
    version: ObjectTemplateVersion,
    *,
    parent_lookup,
    datatype_lookup,
    template_versions: dict[UUID, tuple[ObjectTemplateVersion, ...]] | None = None,
) -> ObjectTemplateVersion:
    component_versions = template_versions or {}
    return service.publish(
        version,
        parent_lookup=parent_lookup,
        datatype_lookup=datatype_lookup,
        template_exists=lambda template_id: template_id in component_versions,
        template_versions_lister=lambda template_id: component_versions.get(template_id, ()),
    )


def test_revise_draft_returns_replacement_snapshot() -> None:
    service = ObjectTemplateVersioningService()
    template_id = uuid4()
    original = _version(
        template_id,
        1,
        status=ObjectTemplateVersionStatus.DRAFT,
        properties=(_property("hostname"),),
        components=(_component("interfaces"),),
    )
    parent = ObjectTemplateVersionRef(template_id=uuid4(), version=2)
    revised_property = _property("serial")
    revised_component = _component("routing_engines")

    revised = service.revise_draft(
        original,
        parent=parent,
        properties=(revised_property,),
        components=(revised_component,),
    )

    assert revised.template_id == original.template_id
    assert revised.version == original.version
    assert revised.status is ObjectTemplateVersionStatus.DRAFT
    assert revised.parent == parent
    assert revised.properties == (revised_property,)
    assert revised.components == (revised_component,)
    assert original.parent is None
    assert tuple(prop.name for prop in original.properties) == ("hostname",)
    assert tuple(component.name for component in original.components) == ("interfaces",)


def test_revise_draft_allows_same_datatype_same_version() -> None:
    service = ObjectTemplateVersioningService()
    datatype_id = uuid4()
    original = _version(
        uuid4(),
        1,
        status=ObjectTemplateVersionStatus.DRAFT,
        properties=(_property("email", datatype_id=datatype_id, datatype_version=3),),
    )

    revised = service.revise_draft(
        original,
        parent=None,
        properties=(_property("email", datatype_id=datatype_id, datatype_version=3),),
        components=(),
    )

    assert revised.properties[0].datatype_version == 3


def test_revise_draft_allows_same_datatype_higher_version() -> None:
    service = ObjectTemplateVersioningService()
    datatype_id = uuid4()
    original = _version(
        uuid4(),
        1,
        status=ObjectTemplateVersionStatus.DRAFT,
        properties=(_property("email", datatype_id=datatype_id, datatype_version=3),),
    )

    revised = service.revise_draft(
        original,
        parent=None,
        properties=(_property("email", datatype_id=datatype_id, datatype_version=4),),
        components=(),
    )

    assert revised.properties[0].datatype_version == 4


def test_revise_draft_rejects_same_datatype_lower_version_and_leaves_source_unchanged() -> None:
    service = ObjectTemplateVersioningService()
    datatype_id = uuid4()
    original = _version(
        uuid4(),
        1,
        status=ObjectTemplateVersionStatus.DRAFT,
        properties=(_property("email", datatype_id=datatype_id, datatype_version=3),),
    )

    with pytest.raises(ObjectTemplateDataTypeVersionDowngrade):
        service.revise_draft(
            original,
            parent=None,
            properties=(_property("email", datatype_id=datatype_id, datatype_version=2),),
            components=(),
        )

    assert original.properties == (_property("email", datatype_id=datatype_id, datatype_version=3),)


def test_revise_draft_allows_different_datatype_identity_with_lower_numeric_version() -> None:
    service = ObjectTemplateVersioningService()
    original = _version(
        uuid4(),
        1,
        status=ObjectTemplateVersionStatus.DRAFT,
        properties=(_property("email", datatype_id=uuid4(), datatype_version=3),),
    )
    new_datatype_id = uuid4()

    revised = service.revise_draft(
        original,
        parent=None,
        properties=(_property("email", datatype_id=new_datatype_id, datatype_version=1),),
        components=(),
    )

    assert revised.properties[0].datatype_id == new_datatype_id
    assert revised.properties[0].datatype_version == 1


def test_revise_draft_allows_added_removed_and_required_changes() -> None:
    service = ObjectTemplateVersioningService()
    datatype_id = uuid4()
    other_datatype_id = uuid4()
    original = _version(
        uuid4(),
        1,
        status=ObjectTemplateVersionStatus.DRAFT,
        properties=(
            _property("hostname", datatype_id=datatype_id, datatype_version=1),
            _property("serial", datatype_id=other_datatype_id, datatype_version=2),
        ),
    )

    revised = service.revise_draft(
        original,
        parent=None,
        properties=(
            ObjectTemplateProperty(
                name="hostname",
                datatype_id=datatype_id,
                datatype_version=1,
                required=True,
            ),
            _property("email", datatype_id=uuid4(), datatype_version=1),
        ),
        components=(),
    )

    assert tuple(prop.name for prop in revised.properties) == ("hostname", "email")
    assert revised.properties[0].required is True


def test_revise_draft_supports_generator_properties_with_downgrade_guard() -> None:
    service = ObjectTemplateVersioningService()
    datatype_id = uuid4()
    original = _version(
        uuid4(),
        1,
        status=ObjectTemplateVersionStatus.DRAFT,
        properties=(_property("email", datatype_id=datatype_id, datatype_version=3),),
    )
    proposed = (
        prop
        for prop in (
            _property("email", datatype_id=datatype_id, datatype_version=4),
            _property("hostname", datatype_id=uuid4(), datatype_version=1),
        )
    )

    revised = service.revise_draft(
        original,
        parent=None,
        properties=proposed,
        components=(),
    )

    assert tuple(prop.datatype_version for prop in revised.properties) == (4, 1)


@pytest.mark.parametrize(
    "status",
    [ObjectTemplateVersionStatus.PUBLISHED, ObjectTemplateVersionStatus.DEPRECATED],
)
def test_revise_non_draft_rejected(status: ObjectTemplateVersionStatus) -> None:
    service = ObjectTemplateVersioningService()
    version = _version(uuid4(), 1, status=status)

    with pytest.raises(InvalidObjectTemplateVersionTransition):
        service.revise_draft(version, parent=None, properties=(), components=())


def test_publish_valid_root_template() -> None:
    service = ObjectTemplateVersioningService()
    datatype_id = uuid4()
    component_target_id = uuid4()
    component_target = _version(
        component_target_id,
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
    )
    draft = _version(
        uuid4(),
        1,
        status=ObjectTemplateVersionStatus.DRAFT,
        properties=(_property("hostname", datatype_id=datatype_id),),
        components=(_component("interfaces", template_id=component_target_id),),
    )
    datatype_versions = {
        (datatype_id, 1): _datatype_version(
            datatype_id,
            1,
            status=DataTypeVersionStatus.PUBLISHED,
        )
    }
    template_versions = {(component_target_id, 1): component_target}

    published = _publish(
        service,
        draft,
        parent_lookup=lambda ref: template_versions.get((ref.template_id, ref.version)),
        datatype_lookup=lambda datatype_uuid, version: datatype_versions.get(
            (datatype_uuid, version)
        ),
        template_versions={component_target_id: (component_target,)},
    )

    assert published.template_id == draft.template_id
    assert published.version == draft.version
    assert published.status is ObjectTemplateVersionStatus.PUBLISHED
    assert published.parent == draft.parent
    assert published.properties == draft.properties
    assert published.components == draft.components
    assert draft.status is ObjectTemplateVersionStatus.DRAFT


def test_publish_valid_inherited_template() -> None:
    service = ObjectTemplateVersioningService()
    parent_id = uuid4()
    inherited_datatype_id = uuid4()
    local_datatype_id = uuid4()
    inherited_component_target_id = uuid4()
    local_component_target_id = uuid4()
    inherited_component_target = _version(
        inherited_component_target_id,
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
    )
    local_component_target = _version(
        local_component_target_id,
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
    )
    parent = _version(
        parent_id,
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        properties=(_property("hostname", datatype_id=inherited_datatype_id),),
        components=(
            _component("interfaces", template_id=inherited_component_target_id),
        ),
    )
    child = _version(
        uuid4(),
        1,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=ObjectTemplateVersionRef(template_id=parent_id, version=1),
        properties=(_property("routing_id", datatype_id=local_datatype_id),),
        components=(
            _component("routing_engines", template_id=local_component_target_id),
        ),
    )
    parent_versions = {
        (parent_id, 1): parent,
        (inherited_component_target_id, 1): inherited_component_target,
        (local_component_target_id, 1): local_component_target,
    }
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

    published = _publish(
        service,
        child,
        parent_lookup=lambda ref: parent_versions.get((ref.template_id, ref.version)),
        datatype_lookup=lambda datatype_uuid, version: datatype_versions.get(
            (datatype_uuid, version)
        ),
        template_versions={
            inherited_component_target_id: (inherited_component_target,),
            local_component_target_id: (local_component_target,),
        },
    )

    assert published.status is ObjectTemplateVersionStatus.PUBLISHED
    assert published.parent == child.parent
    assert published.properties == child.properties
    assert published.components == child.components


def test_publish_missing_parent() -> None:
    service = ObjectTemplateVersioningService()
    child = _version(
        uuid4(),
        1,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=ObjectTemplateVersionRef(template_id=uuid4(), version=1),
    )

    with pytest.raises(ObjectTemplateParentNotFound):
        _publish(
            service,
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
        _publish(
            service,
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
        _publish(
            service,
            child,
            parent_lookup=lambda _ref: parent,
            datatype_lookup=lambda _datatype_uuid, _version: _datatype_version(
                datatype_id,
                1,
                status=DataTypeVersionStatus.PUBLISHED,
            ),
        )


def test_publish_component_inheritance_conflict_behavior_is_preserved() -> None:
    service = ObjectTemplateVersioningService()
    parent_id = uuid4()
    target_id = uuid4()
    target = _version(target_id, 1, status=ObjectTemplateVersionStatus.PUBLISHED)
    parent = _version(
        parent_id,
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        components=(_component("interfaces", template_id=target_id),),
    )
    child = _version(
        uuid4(),
        1,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=ObjectTemplateVersionRef(template_id=parent_id, version=1),
        components=(_component("interfaces", template_id=target_id),),
    )

    with pytest.raises(InheritedObjectTemplateComponentConflict):
        _publish(
            service,
            child,
            parent_lookup=lambda ref: {  # noqa: ARG005
                (parent_id, 1): parent,
                (target_id, 1): target,
            }.get((ref.template_id, ref.version)),
            datatype_lookup=lambda _datatype_uuid, _version: None,
            template_versions={target_id: (target,)},
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
        _publish(
            service,
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
        _publish(
            service,
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
        _publish(
            service,
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
        _publish(
            service,
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
        _publish(
            service,
            child,
            parent_lookup=lambda _ref: parent,
            datatype_lookup=lambda datatype_uuid, version: datatype_versions.get(
                (datatype_uuid, version)
            ),
        )


def test_publish_missing_component_target_version() -> None:
    service = ObjectTemplateVersioningService()
    target_id = uuid4()
    draft = _version(
        uuid4(),
        1,
        status=ObjectTemplateVersionStatus.DRAFT,
        components=(_component("interfaces", template_id=target_id),),
    )
    with pytest.raises(ObjectTemplateComponentVersionNotFound):
        _publish(
            service,
            draft,
            parent_lookup=lambda _ref: None,
            datatype_lookup=lambda _datatype_uuid, _version: None,
            template_versions={},
        )


@pytest.mark.parametrize(
    "status",
    [ObjectTemplateVersionStatus.DRAFT, ObjectTemplateVersionStatus.DEPRECATED],
)
def test_publish_rejects_non_published_component_target_versions(
    status: ObjectTemplateVersionStatus,
) -> None:
    service = ObjectTemplateVersioningService()
    target_id = uuid4()
    target = _version(target_id, 1, status=status)
    draft = _version(
        uuid4(),
        1,
        status=ObjectTemplateVersionStatus.DRAFT,
        components=(_component("interfaces", template_id=target_id),),
    )

    with pytest.raises(ObjectTemplateComponentVersionNotPublished):
        _publish(
            service,
            draft,
            parent_lookup=lambda _ref: target,
            datatype_lookup=lambda _datatype_uuid, _version: None,
            template_versions={target_id: (target,)},
        )


def test_publish_checks_inherited_components_too() -> None:
    service = ObjectTemplateVersioningService()
    parent_id = uuid4()
    inherited_target_id = uuid4()
    local_target_id = uuid4()
    parent = _version(
        parent_id,
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        components=(_component("interfaces", template_id=inherited_target_id),),
    )
    local_target = _version(local_target_id, 1, status=ObjectTemplateVersionStatus.PUBLISHED)
    versions = {
        (parent_id, 1): parent,
        (local_target_id, 1): local_target,
    }
    child = _version(
        uuid4(),
        1,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=ObjectTemplateVersionRef(template_id=parent_id, version=1),
        components=(_component("routing_engines", template_id=local_target_id),),
    )

    with pytest.raises(ObjectTemplateComponentVersionNotFound):
        _publish(
            service,
            child,
            parent_lookup=lambda ref: versions.get((ref.template_id, ref.version)),
            datatype_lookup=lambda _datatype_uuid, _version: None,
            template_versions={local_target_id: (local_target,)},
        )


@pytest.mark.parametrize(
    "inherited_status",
    [ObjectTemplateVersionStatus.DRAFT, ObjectTemplateVersionStatus.DEPRECATED],
)
def test_publish_rejects_non_published_inherited_component_target_versions(
    inherited_status: ObjectTemplateVersionStatus,
) -> None:
    service = ObjectTemplateVersioningService()
    parent_id = uuid4()
    inherited_target_id = uuid4()
    local_target_id = uuid4()
    inherited_target = _version(inherited_target_id, 1, status=inherited_status)
    local_target = _version(local_target_id, 1, status=ObjectTemplateVersionStatus.PUBLISHED)
    parent = _version(
        parent_id,
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        components=(_component("interfaces", template_id=inherited_target_id),),
    )
    versions = {
        (parent_id, 1): parent,
        (inherited_target_id, 1): inherited_target,
        (local_target_id, 1): local_target,
    }
    child = _version(
        uuid4(),
        1,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=ObjectTemplateVersionRef(template_id=parent_id, version=1),
        components=(_component("routing_engines", template_id=local_target_id),),
    )

    with pytest.raises(ObjectTemplateComponentVersionNotPublished):
        _publish(
            service,
            child,
            parent_lookup=lambda ref: versions.get((ref.template_id, ref.version)),
            datatype_lookup=lambda _datatype_uuid, _version: None,
            template_versions={
                inherited_target_id: (inherited_target,),
                local_target_id: (local_target,),
            },
        )


def test_create_next_version_clones_component_identity_refs() -> None:
    service = ObjectTemplateVersioningService()
    component = _component("interfaces", template_id=uuid4(), template_version=3)
    source = _version(
        uuid4(),
        2,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        components=(component,),
    )

    next_version = service.create_next_version(source, existing_versions=(source,))

    assert next_version.version == 3
    assert next_version.status is ObjectTemplateVersionStatus.DRAFT
    assert next_version.components == (component,)
    assert source.components == (component,)


def test_publish_preserves_local_components() -> None:
    service = ObjectTemplateVersioningService()
    target_id = uuid4()
    target = _version(target_id, 1, status=ObjectTemplateVersionStatus.PUBLISHED)
    component = _component("interfaces", template_id=target_id, template_version=1)
    draft = _version(
        uuid4(),
        1,
        status=ObjectTemplateVersionStatus.DRAFT,
        components=(component,),
    )

    published = _publish(
        service,
        draft,
        parent_lookup=lambda ref: {(target_id, 1): target}.get((ref.template_id, ref.version)),
        datatype_lookup=lambda _datatype_uuid, _version: None,
        template_versions={target_id: (target,)},
    )

    assert published.components == (component,)
    assert draft.components == (component,)


def test_deprecate_published() -> None:
    service = ObjectTemplateVersioningService()
    component = _component("interfaces", template_id=uuid4(), template_version=1)
    published = _version(
        uuid4(),
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        components=(component,),
    )

    deprecated = service.deprecate(published)

    assert deprecated.template_id == published.template_id
    assert deprecated.version == published.version
    assert deprecated.status is ObjectTemplateVersionStatus.DEPRECATED
    assert deprecated.parent == published.parent
    assert deprecated.properties == published.properties
    assert deprecated.components == published.components


@pytest.mark.parametrize(
    "status",
    [ObjectTemplateVersionStatus.DRAFT, ObjectTemplateVersionStatus.DEPRECATED],
)
def test_deprecate_non_published_rejected(status: ObjectTemplateVersionStatus) -> None:
    service = ObjectTemplateVersioningService()
    version = _version(uuid4(), 1, status=status)

    with pytest.raises(InvalidObjectTemplateVersionTransition):
        service.deprecate(version)


def test_create_next_version_rejects_non_published_source() -> None:
    service = ObjectTemplateVersioningService()
    source = _version(uuid4(), 1, status=ObjectTemplateVersionStatus.DRAFT)

    with pytest.raises(InvalidObjectTemplateVersionTransition):
        service.create_next_version(source, existing_versions=(source,))


def test_create_next_version_rejects_mismatched_template_versions() -> None:
    service = ObjectTemplateVersioningService()
    source = _version(uuid4(), 1, status=ObjectTemplateVersionStatus.PUBLISHED)
    other = _version(uuid4(), 2, status=ObjectTemplateVersionStatus.PUBLISHED)

    with pytest.raises(MismatchedObjectTemplateVersion):
        service.create_next_version(source, existing_versions=(source, other))


def test_ordinary_template_without_components_still_publishes() -> None:
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

    published = _publish(
        service,
        draft,
        parent_lookup=lambda _: None,
        datatype_lookup=lambda datatype_uuid, version: datatype_versions.get(
            (datatype_uuid, version)
        ),
    )

    assert published.status is ObjectTemplateVersionStatus.PUBLISHED
    assert published.components == ()
