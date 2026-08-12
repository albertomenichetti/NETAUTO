from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from netauto.core.datatype import (
    DataType,
    DataTypeVersion,
    DataTypeVersioningService,
    DataTypeVersionStatus,
    PrimitiveTypeRegistry,
)
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
from netauto.persistence.sqlalchemy.datatype_repository import SqlAlchemyDataTypeRepository
from netauto.persistence.sqlalchemy.models import (
    ObjectRow,
    ObjectTemplateComponentRow,
    ObjectTemplatePropertyRow,
    ObjectTemplateRow,
    RelationshipDefinitionRow,
)
from netauto.persistence.sqlalchemy.objecttemplate_repository import (
    SqlAlchemyObjectTemplateRepository,
)

pytestmark = pytest.mark.postgresql


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


def _property(
    name: str,
    *,
    datatype_id: UUID | None = None,
    datatype_version: int = 1,
    required: bool = False,
) -> ObjectTemplateProperty:
    return ObjectTemplateProperty(
        name=name,
        datatype_id=datatype_id or uuid4(),
        datatype_version=datatype_version,
        required=required,
    )


def _component(
    name: str,
    *,
    template_id: UUID | None = None,
) -> ObjectTemplateComponent:
    return ObjectTemplateComponent(
        name=name,
        template_id=template_id or uuid4(),
    )


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


def _store_datatype_version(
    session: Session,
    *,
    datatype_id: UUID | None = None,
    version: int = 1,
    namespace: str | None = None,
    name: str | None = None,
    status: DataTypeVersionStatus = DataTypeVersionStatus.PUBLISHED,
) -> tuple[DataType, DataTypeVersion]:
    datatype_uuid = datatype_id or uuid4()
    logical_suffix = datatype_uuid.hex[:8]
    datatype = DataType(
        id=datatype_uuid,
        namespace=namespace or f"network_{logical_suffix}",
        name=name or f"value_{logical_suffix}",
        description=None,
    )
    datatype_version = DataTypeVersion(
        datatype_id=datatype.id,
        version=version,
        status=status,
        base_type=PrimitiveTypeRegistry().get("core.string"),
        constraints=(),
    )
    repo = SqlAlchemyDataTypeRepository(session)
    repo.add(datatype)
    draft = DataTypeVersion(
        datatype_id=datatype_version.datatype_id,
        version=datatype_version.version,
        status=DataTypeVersionStatus.DRAFT,
        base_type=datatype_version.base_type,
        constraints=datatype_version.constraints,
    )
    repo.add_version(draft)
    if datatype_version.status is DataTypeVersionStatus.PUBLISHED:
        repo.replace_version(datatype_version)
    elif datatype_version.status is DataTypeVersionStatus.DEPRECATED:
        repo.replace_version(DataTypeVersioningService().publish(draft))
        repo.replace_version(datatype_version)
    return datatype, datatype_version


def _store_template_identity(
    session: Session,
    *,
    template_id: UUID | None = None,
    namespace: str | None = None,
    name: str | None = None,
    abstract: bool = False,
) -> ObjectTemplate:
    template_uuid = template_id or uuid4()
    logical_suffix = template_uuid.hex[:8]
    template = ObjectTemplate(
        id=template_uuid,
        namespace=namespace or f"network_{logical_suffix}",
        name=name or f"template_{logical_suffix}",
        description=None,
        abstract=abstract,
    )
    session.add(
        ObjectTemplateRow(
            id=str(template.id),
            namespace=template.namespace,
            name=template.name,
            description=template.description,
            abstract=template.abstract,
        )
    )
    session.flush()
    return template


def _store_versions(
    repo: SqlAlchemyObjectTemplateRepository,
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


def test_postgresql_objecttemplate_identity_round_trip_and_ordering(
    postgresql_model_session: Session,
) -> None:
    repo = SqlAlchemyObjectTemplateRepository(postgresql_model_session)
    zeta = _template(namespace="zeta", name="beta", description=None)
    device = _template(namespace="network", name="device", description=None, abstract=False)
    router = _template(namespace="network", name="router", description="Router", abstract=True)

    repo.add(zeta)
    repo.add(router)
    repo.add(device)

    listed = repo.list()
    loaded = repo.get(router.id)
    by_name = repo.get_by_name("network", "router")

    assert [(template.namespace, template.name) for template in listed] == [
        ("network", "device"),
        ("network", "router"),
        ("zeta", "beta"),
    ]
    assert loaded == router
    assert loaded is not None
    assert isinstance(loaded.id, UUID)
    assert loaded.abstract is True
    assert repo.get(uuid4()) is None
    assert by_name == router


def test_postgresql_objecttemplate_identity_uniqueness_and_missing_delete(
    postgresql_model_session: Session,
) -> None:
    repo = SqlAlchemyObjectTemplateRepository(postgresql_model_session)
    template = _template(template_id=uuid4(), namespace="network", name="device")
    duplicate_uuid = _template(
        template_id=template.id,
        namespace="network",
        name="router",
    )
    duplicate_name = _template(
        template_id=uuid4(),
        namespace=template.namespace,
        name=template.name,
    )

    repo.add(template)
    postgresql_model_session.commit()

    with pytest.raises(ObjectTemplateAlreadyExists):
        repo.add(duplicate_uuid)
    postgresql_model_session.rollback()

    with pytest.raises(ObjectTemplateAlreadyExists):
        repo.add(duplicate_name)
    postgresql_model_session.rollback()

    with pytest.raises(ObjectTemplateNotFound):
        repo.delete(uuid4())

    assert repo.get(template.id) == template


def test_postgresql_objecttemplate_version_round_trip_with_parent_properties_and_components(
    postgresql_model_session: Session,
) -> None:
    repo = SqlAlchemyObjectTemplateRepository(postgresql_model_session)
    template = _template()
    parent = _template(name="parent")
    interface = _store_template_identity(postgresql_model_session, name="interface")
    module = _store_template_identity(postgresql_model_session, name="module")
    hostname_datatype, hostname_v1 = _store_datatype_version(
        postgresql_model_session, name="hostname"
    )
    serial_datatype, serial_v1 = _store_datatype_version(postgresql_model_session, name="serial")
    parent_version = _version(parent.id, 7)
    version = _version(
        template.id,
        1,
        parent=ObjectTemplateVersionRef(template_id=parent.id, version=7),
        properties=(
            _property(
                "hostname",
                datatype_id=hostname_datatype.id,
                datatype_version=hostname_v1.version,
                required=True,
            ),
            _property(
                "serial",
                datatype_id=serial_datatype.id,
                datatype_version=serial_v1.version,
                required=False,
            ),
        ),
        components=(
            _component("interfaces", template_id=interface.id),
            _component("modules", template_id=module.id),
        ),
    )

    repo.add(parent)
    repo.add_version(parent_version)
    repo.add(template)
    repo.add_version(version)

    loaded = repo.get_version(template.id, 1)
    assert loaded == version


def test_postgresql_objecttemplate_list_versions_orders_and_separates_structural_rows(
    postgresql_model_session: Session,
) -> None:
    repo = SqlAlchemyObjectTemplateRepository(postgresql_model_session)
    template = _template()
    datatype_one, datatype_one_v1 = _store_datatype_version(
        postgresql_model_session, name="hostname"
    )
    datatype_two, datatype_two_v1 = _store_datatype_version(
        postgresql_model_session, name="serial"
    )
    interface = _store_template_identity(postgresql_model_session, name="interface")
    module = _store_template_identity(postgresql_model_session, name="module")
    v5 = _version(
        template.id,
        5,
        status=ObjectTemplateVersionStatus.DEPRECATED,
        properties=(
            _property(
                "serial",
                datatype_id=datatype_two.id,
                datatype_version=datatype_two_v1.version,
            ),
        ),
        components=(_component("modules", template_id=module.id),),
    )
    v1 = _version(
        template.id,
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        properties=(
            _property(
                "hostname",
                datatype_id=datatype_one.id,
                datatype_version=datatype_one_v1.version,
            ),
        ),
        components=(_component("interfaces", template_id=interface.id),),
    )
    v2 = _version(template.id, 2)

    _store_versions(repo, template, (v5, v1, v2))

    loaded = repo.list_versions(template.id)

    assert tuple(version.version for version in loaded) == (1, 2, 5)
    assert loaded[0].properties == v1.properties
    assert loaded[0].components == v1.components
    assert loaded[1].properties == ()
    assert loaded[1].components == ()
    assert loaded[2].properties == v5.properties
    assert loaded[2].components == v5.components


def test_postgresql_objecttemplate_exact_datatype_version_fk_behavior(
    postgresql_model_session: Session,
) -> None:
    repo = SqlAlchemyObjectTemplateRepository(postgresql_model_session)
    template = _template()
    datatype, datatype_version = _store_datatype_version(
        postgresql_model_session, name="hostname"
    )
    valid = _version(
        template.id,
        1,
        properties=(
            _property(
                "hostname",
                datatype_id=datatype.id,
                datatype_version=datatype_version.version,
                required=True,
            ),
        ),
    )
    invalid_template = _template(name="device_invalid_pin")
    invalid = _version(
        invalid_template.id,
        1,
        properties=(
            _property(
                "hostname",
                datatype_id=datatype.id,
                datatype_version=999,
                required=True,
            ),
        ),
    )

    repo.add(template)
    repo.add_version(valid)
    assert repo.get_version(template.id, 1) == valid

    repo.add(invalid_template)
    with postgresql_model_session.begin_nested():
        with pytest.raises(ObjectTemplatePersistenceError):
            repo.add_version(invalid)

    assert repo.get(invalid_template.id) == invalid_template
    assert repo.get_version(invalid_template.id, 1) is None


def test_postgresql_objecttemplate_component_target_identity_fk_behavior(
    postgresql_model_session: Session,
) -> None:
    repo = SqlAlchemyObjectTemplateRepository(postgresql_model_session)
    target = _store_template_identity(postgresql_model_session, name="interface")
    valid_owner = _template(name="device_valid_component")
    invalid_owner = _template(name="device_invalid_component")
    valid = _version(
        valid_owner.id,
        1,
        components=(_component("interfaces", template_id=target.id),),
    )
    invalid = _version(
        invalid_owner.id,
        1,
        components=(_component("interfaces", template_id=uuid4()),),
    )

    repo.add(valid_owner)
    repo.add_version(valid)
    assert repo.get_version(valid_owner.id, 1) == valid

    repo.add(invalid_owner)
    with postgresql_model_session.begin_nested():
        with pytest.raises(ObjectTemplatePersistenceError):
            repo.add_version(invalid)

    assert repo.get(invalid_owner.id) == invalid_owner
    assert repo.get_version(invalid_owner.id, 1) is None


def test_postgresql_objecttemplate_parent_exact_version_fk_behavior(
    postgresql_model_session: Session,
) -> None:
    repo = SqlAlchemyObjectTemplateRepository(postgresql_model_session)
    parent = _template(name="parent")
    child_valid = _template(name="child_valid")
    child_invalid = _template(name="child_invalid")
    repo.add(parent)
    repo.add_version(_version(parent.id, 1))

    valid = _version(
        child_valid.id,
        1,
        parent=ObjectTemplateVersionRef(template_id=parent.id, version=1),
    )
    invalid = _version(
        child_invalid.id,
        1,
        parent=ObjectTemplateVersionRef(template_id=parent.id, version=2),
    )

    repo.add(child_valid)
    repo.add_version(valid)
    assert repo.get_version(child_valid.id, 1) == valid

    repo.add(child_invalid)
    with postgresql_model_session.begin_nested():
        with pytest.raises(ObjectTemplatePersistenceError):
            repo.add_version(invalid)

    assert repo.get(child_invalid.id) == child_invalid
    assert repo.get_version(child_invalid.id, 1) is None


def test_postgresql_objecttemplate_duplicate_and_missing_version_behaviors(
    postgresql_model_session: Session,
) -> None:
    repo = SqlAlchemyObjectTemplateRepository(postgresql_model_session)
    template = _template()
    version = _version(template.id, 1)
    repo.add(template)
    repo.add_version(version)
    postgresql_model_session.commit()

    with pytest.raises(ObjectTemplateVersionAlreadyExists):
        repo.add_version(version)
    postgresql_model_session.rollback()

    missing = _version(template.id, 99)
    with pytest.raises(ObjectTemplateVersionNotFound):
        repo.replace_version(missing)

    assert repo.get_version(template.id, 1) == version


def test_postgresql_objecttemplate_replace_draft_structure_rewrites_rows_and_order(
    postgresql_model_session: Session,
) -> None:
    repo = SqlAlchemyObjectTemplateRepository(postgresql_model_session)
    parent = _template(name="parent")
    template = _template(name="child")
    interface = _store_template_identity(postgresql_model_session, name="interface")
    module = _store_template_identity(postgresql_model_session, name="module")
    hostname_datatype, hostname_v1 = _store_datatype_version(
        postgresql_model_session, name="hostname"
    )
    serial_datatype, serial_v1 = _store_datatype_version(postgresql_model_session, name="serial")
    repo.add(parent)
    repo.add_version(_version(parent.id, 1))
    repo.add_version(_version(parent.id, 2))

    original = _version(
        template.id,
        1,
        parent=ObjectTemplateVersionRef(template_id=parent.id, version=1),
        properties=(
            _property(
                "hostname",
                datatype_id=hostname_datatype.id,
                datatype_version=hostname_v1.version,
            ),
        ),
        components=(_component("interfaces", template_id=interface.id),),
    )
    replacement = _version(
        template.id,
        1,
        parent=ObjectTemplateVersionRef(template_id=parent.id, version=2),
        properties=(
            _property(
                "serial",
                datatype_id=serial_datatype.id,
                datatype_version=serial_v1.version,
                required=True,
            ),
            _property(
                "hostname",
                datatype_id=hostname_datatype.id,
                datatype_version=hostname_v1.version,
            ),
        ),
        components=(
            _component("modules", template_id=module.id),
            _component("interfaces", template_id=interface.id),
        ),
    )

    repo.add(template)
    repo.add_version(original)
    repo.replace_version(replacement)

    loaded = repo.get_version(template.id, 1)
    property_rows = postgresql_model_session.scalars(
        select(ObjectTemplatePropertyRow)
        .where(
            ObjectTemplatePropertyRow.template_id == str(template.id),
            ObjectTemplatePropertyRow.template_version == 1,
        )
        .order_by(ObjectTemplatePropertyRow.position.asc())
    ).all()
    component_rows = postgresql_model_session.scalars(
        select(ObjectTemplateComponentRow)
        .where(
            ObjectTemplateComponentRow.template_id == str(template.id),
            ObjectTemplateComponentRow.template_version == 1,
        )
        .order_by(ObjectTemplateComponentRow.position.asc())
    ).all()

    assert loaded == replacement
    assert [(row.name, row.position) for row in property_rows] == [
        ("serial", 0),
        ("hostname", 1),
    ]
    assert [(row.name, row.position) for row in component_rows] == [
        ("modules", 0),
        ("interfaces", 1),
    ]


def test_postgresql_objecttemplate_status_only_replace_preserves_structure_rows(
    postgresql_model_session: Session,
) -> None:
    repo = SqlAlchemyObjectTemplateRepository(postgresql_model_session)
    template = _template()
    datatype, datatype_version = _store_datatype_version(
        postgresql_model_session, name="hostname"
    )
    interface = _store_template_identity(postgresql_model_session, name="interface")
    draft = _version(
        template.id,
        1,
        status=ObjectTemplateVersionStatus.DRAFT,
        properties=(
            _property(
                "hostname",
                datatype_id=datatype.id,
                datatype_version=datatype_version.version,
                required=True,
            ),
        ),
        components=(_component("interfaces", template_id=interface.id),),
    )
    published = _version(
        template.id,
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        parent=draft.parent,
        properties=draft.properties,
        components=draft.components,
    )

    repo.add(template)
    repo.add_version(draft)
    before_property_ids = tuple(
        id_
        for (id_,) in postgresql_model_session.execute(
            select(ObjectTemplatePropertyRow.name).where(
                ObjectTemplatePropertyRow.template_id == str(template.id),
                ObjectTemplatePropertyRow.template_version == 1,
            )
        )
    )
    before_component_ids = tuple(
        id_
        for (id_,) in postgresql_model_session.execute(
            select(ObjectTemplateComponentRow.name).where(
                ObjectTemplateComponentRow.template_id == str(template.id),
                ObjectTemplateComponentRow.template_version == 1,
            )
        )
    )

    repo.replace_version(published)
    loaded = repo.get_version(template.id, 1)
    after_property_ids = tuple(
        id_
        for (id_,) in postgresql_model_session.execute(
            select(ObjectTemplatePropertyRow.name).where(
                ObjectTemplatePropertyRow.template_id == str(template.id),
                ObjectTemplatePropertyRow.template_version == 1,
            )
        )
    )
    after_component_ids = tuple(
        id_
        for (id_,) in postgresql_model_session.execute(
            select(ObjectTemplateComponentRow.name).where(
                ObjectTemplateComponentRow.template_id == str(template.id),
                ObjectTemplateComponentRow.template_version == 1,
            )
        )
    )

    assert loaded == published
    assert after_property_ids == before_property_ids
    assert after_component_ids == before_component_ids


def test_postgresql_objecttemplate_delete_unreferenced_removes_identity_versions_and_owned_rows(
    postgresql_model_session: Session,
) -> None:
    repo = SqlAlchemyObjectTemplateRepository(postgresql_model_session)
    target = _template(name="device")
    unrelated = _template(name="router")
    datatype, datatype_version = _store_datatype_version(
        postgresql_model_session, name="hostname"
    )
    component_target = _store_template_identity(postgresql_model_session, name="interface")
    _store_versions(
        repo,
        target,
        (
            _version(
                target.id,
                1,
                properties=(
                    _property(
                        "hostname",
                        datatype_id=datatype.id,
                        datatype_version=datatype_version.version,
                    ),
                ),
                components=(_component("interfaces", template_id=component_target.id),),
            ),
            _version(target.id, 2, status=ObjectTemplateVersionStatus.PUBLISHED),
        ),
    )
    _store_versions(repo, unrelated, (_version(unrelated.id, 1),))

    repo.delete(target.id)

    assert repo.get(target.id) is None
    assert repo.list_versions(target.id) == ()
    assert repo.get(unrelated.id) == unrelated
    assert tuple(version.version for version in repo.list_versions(unrelated.id)) == (1,)
    assert postgresql_model_session.scalar(
        select(ObjectTemplatePropertyRow).where(
            ObjectTemplatePropertyRow.template_id == str(target.id)
        )
    ) is None
    assert postgresql_model_session.scalar(
        select(ObjectTemplateComponentRow).where(
            ObjectTemplateComponentRow.template_id == str(target.id)
        )
    ) is None


@pytest.mark.parametrize("dependency_kind", ["object", "inheritance", "component", "relationship"])
def test_postgresql_objecttemplate_delete_blocking_dependencies_preserve_contract_and_data(
    postgresql_model_session: Session,
    dependency_kind: str,
) -> None:
    repo = SqlAlchemyObjectTemplateRepository(postgresql_model_session)
    target = _template(name=f"target_{dependency_kind}")
    _store_versions(repo, target, (_version(target.id, 1),))

    if dependency_kind == "object":
        postgresql_model_session.add(
            ObjectRow(
                id=str(uuid4()),
                template_id=str(target.id),
                template_version=1,
                properties_json="{}",
            )
        )
        expected_match = "object reference"
    elif dependency_kind == "inheritance":
        child = _template(name="router")
        _store_versions(
            repo,
            child,
            (
                _version(
                    child.id,
                    1,
                    status=ObjectTemplateVersionStatus.DEPRECATED,
                    parent=ObjectTemplateVersionRef(template_id=target.id, version=1),
                ),
            ),
        )
        expected_match = "inheritance reference"
    elif dependency_kind == "component":
        owner = _template(name="owner")
        backup = _store_template_identity(postgresql_model_session, name="backup_target")
        _store_versions(
            repo,
            owner,
            (
                _version(
                    owner.id,
                    1,
                    status=ObjectTemplateVersionStatus.PUBLISHED,
                    components=(
                        _component("ports", template_id=target.id),
                        _component("backup", template_id=backup.id),
                    ),
                ),
            ),
        )
        expected_match = "component reference"
    else:
        other = _store_template_identity(postgresql_model_session, name="credential")
        postgresql_model_session.add(
            RelationshipDefinitionRow(
                id=str(uuid4()),
                source_template_id=str(target.id),
                target_template_id=str(other.id),
                forward_name="uses",
                reverse_name="is_used_by",
            )
        )
        expected_match = "relationship-definition reference"

    postgresql_model_session.flush()

    with pytest.raises(ObjectTemplatePersistenceError, match=expected_match):
        repo.delete(target.id)

    assert repo.get(target.id) == target
    assert tuple(version.version for version in repo.list_versions(target.id)) == (1,)
