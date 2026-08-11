from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Engine, delete, event, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

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
from netauto.persistence.sqlalchemy.database import create_schema, create_sqlite_engine
from netauto.persistence.sqlalchemy.datatype_repository import SqlAlchemyDataTypeRepository
from netauto.persistence.sqlalchemy.models import (
    ObjectRow,
    ObjectTemplateComponentRow,
    ObjectTemplatePropertyRow,
    ObjectTemplateRow,
    ObjectTemplateVersionRow,
    RelationshipDefinitionRow,
)
from netauto.persistence.sqlalchemy.objecttemplate_repository import (
    SqlAlchemyObjectTemplateRepository,
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


def _repo(
    tmp_path: Path,
    filename: str,
) -> tuple[SqlAlchemyObjectTemplateRepository, Session, Engine]:
    engine = create_sqlite_engine(f"sqlite:///{tmp_path / filename}")
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    session = session_factory()
    return SqlAlchemyObjectTemplateRepository(session), session, engine


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
) -> ObjectTemplate:
    template_uuid = template_id or uuid4()
    logical_suffix = template_uuid.hex[:8]
    template = ObjectTemplate(
        id=template_uuid,
        namespace=namespace or f"network_{logical_suffix}",
        name=name or f"template_{logical_suffix}",
        description=None,
        abstract=False,
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


def _store_template_version(
    session: Session,
    template: ObjectTemplate,
    *,
    version: int = 1,
    status: ObjectTemplateVersionStatus = ObjectTemplateVersionStatus.DRAFT,
    parent: ObjectTemplateVersionRef | None = None,
    properties: tuple[ObjectTemplateProperty, ...] = (),
    components: tuple[ObjectTemplateComponent, ...] = (),
) -> ObjectTemplateVersion:
    object_template_version = _version(
        template.id,
        version,
        status=status,
        parent=parent,
        properties=properties,
        components=components,
    )
    repo = SqlAlchemyObjectTemplateRepository(session)
    draft = ObjectTemplateVersion(
        template_id=object_template_version.template_id,
        version=object_template_version.version,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=object_template_version.parent,
        properties=object_template_version.properties,
        components=object_template_version.components,
    )
    repo.add_version(draft)
    if object_template_version.status is ObjectTemplateVersionStatus.PUBLISHED:
        repo.replace_version(object_template_version)
    elif object_template_version.status is ObjectTemplateVersionStatus.DEPRECATED:
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
        repo.replace_version(object_template_version)
    return object_template_version


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


def test_empty_list(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "empty.sqlite3")
    try:
        assert repo.list() == ()
    finally:
        session.close()
        engine.dispose()


def test_add_get_round_trip(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "round_trip.sqlite3")
    template = _template()
    try:
        repo.add(template)
        assert repo.get(template.id) == template
    finally:
        session.close()
        engine.dispose()


@pytest.mark.parametrize(
    ("description", "abstract", "name"),
    [(None, False, "device_plain"), ("desc", True, "device_abstract")],
)
def test_description_and_abstract_round_trip(
    tmp_path: Path,
    description: str | None,
    abstract: bool,
    name: str,
) -> None:
    repo, session, engine = _repo(tmp_path, f"identity_{abstract}.sqlite3")
    template = _template(
        name=name,
        description=description,
        abstract=abstract,
    )
    try:
        repo.add(template)
        loaded = repo.get(template.id)
        assert loaded is not None
        assert loaded.description == description
        assert loaded.abstract is abstract
    finally:
        session.close()
        engine.dispose()


def test_get_by_name(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "by_name.sqlite3")
    template = _template(namespace="network", name="router")
    try:
        repo.add(template)
        assert repo.get_by_name("network", "router") == template
    finally:
        session.close()
        engine.dispose()


def test_deterministic_ordering(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "ordering.sqlite3")
    zeta = _template(namespace="zeta", name="beta", description=None)
    device = _template(namespace="network", name="device", description=None)
    router = _template(namespace="network", name="router", description=None)
    try:
        repo.add(zeta)
        repo.add(router)
        repo.add(device)
        listed = repo.list()
        assert [(template.namespace, template.name) for template in listed] == [
            ("network", "device"),
            ("network", "router"),
            ("zeta", "beta"),
        ]
    finally:
        session.close()
        engine.dispose()


def test_duplicate_uuid_rejected(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "dup_uuid.sqlite3")
    template = _template(template_id=uuid4(), namespace="network", name="device")
    duplicate = _template(template_id=template.id, namespace="network", name="router")
    try:
        repo.add(template)
        with pytest.raises(ObjectTemplateAlreadyExists):
            repo.add(duplicate)
    finally:
        session.close()
        engine.dispose()


def test_duplicate_logical_name_rejected(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "dup_name.sqlite3")
    first = _template(namespace="network", name="device")
    second = _template(namespace="network", name="device")
    try:
        repo.add(first)
        with pytest.raises(ObjectTemplateAlreadyExists):
            repo.add(second)
    finally:
        session.close()
        engine.dispose()


def test_add_get_version_round_trip(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "version_round_trip.sqlite3")
    template = _template()
    hostname_datatype, hostname_v1 = _store_datatype_version(session, name="hostname")
    serial_datatype, serial_v1 = _store_datatype_version(session, name="serial")
    version = _version(
        template.id,
        1,
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
            ),
        ),
    )
    try:
        repo.add(template)
        repo.add_version(version)
        assert repo.get_version(template.id, 1) == version
    finally:
        session.close()
        engine.dispose()


def test_status_round_trip(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "status.sqlite3")
    template = _template()
    draft = _version(template.id, 1, status=ObjectTemplateVersionStatus.DRAFT)
    published = _version(template.id, 2, status=ObjectTemplateVersionStatus.PUBLISHED)
    deprecated = _version(template.id, 3, status=ObjectTemplateVersionStatus.DEPRECATED)
    try:
        _store_versions(repo, template, (draft, published, deprecated))
        loaded = repo.list_versions(template.id)
        assert tuple(version.status for version in loaded) == (
            ObjectTemplateVersionStatus.DRAFT,
            ObjectTemplateVersionStatus.PUBLISHED,
            ObjectTemplateVersionStatus.DEPRECATED,
        )
    finally:
        session.close()
        engine.dispose()


def test_parent_none_round_trip(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "parent_none.sqlite3")
    template = _template()
    version = _version(template.id, 1)
    try:
        repo.add(template)
        repo.add_version(version)
        loaded = repo.get_version(template.id, 1)
        assert loaded is not None
        assert loaded.parent is None
    finally:
        session.close()
        engine.dispose()


def test_exact_pinned_parent_ref_round_trip(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "parent.sqlite3")
    template = _template()
    parent_template = _template(name="parent")
    parent_version = _version(parent_template.id, 7)
    version = _version(
        template.id,
        1,
        parent=ObjectTemplateVersionRef(template_id=parent_template.id, version=7),
    )
    try:
        repo.add(parent_template)
        repo.add_version(parent_version)
        repo.add(template)
        repo.add_version(version)
        loaded = repo.get_version(template.id, 1)
        assert loaded is not None
        assert loaded.parent == version.parent
    finally:
        session.close()
        engine.dispose()


def test_multiple_ordered_properties_round_trip_and_order_preserved(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "properties.sqlite3")
    template = _template()
    first_datatype, _ = _store_datatype_version(
        session,
        datatype_id=uuid4(),
        version=2,
        name="dt1",
    )
    second_datatype, _ = _store_datatype_version(
        session,
        datatype_id=uuid4(),
        version=3,
        name="dt2",
    )
    version = _version(
        template.id,
        1,
        properties=(
            _property(
                "hostname",
                datatype_id=first_datatype.id,
                datatype_version=2,
                required=True,
            ),
            _property(
                "serial",
                datatype_id=second_datatype.id,
                datatype_version=3,
                required=False,
            ),
        ),
    )
    try:
        repo.add(template)
        repo.add_version(version)
        loaded = repo.get_version(template.id, 1)
        assert loaded is not None
        assert tuple(prop.name for prop in loaded.properties) == ("hostname", "serial")
        assert loaded.properties[0].required is True
        assert loaded.properties[1].required is False
        assert loaded.properties[0].datatype_id == first_datatype.id
        assert loaded.properties[0].datatype_version == 2
        assert loaded.properties[1].datatype_id == second_datatype.id
        assert loaded.properties[1].datatype_version == 3
    finally:
        session.close()
        engine.dispose()


def test_empty_components_round_trip(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "empty_components.sqlite3")
    template = _template()
    version = _version(template.id, 1)
    try:
        repo.add(template)
        repo.add_version(version)
        loaded = repo.get_version(template.id, 1)
        assert loaded is not None
        assert loaded.components == ()
    finally:
        session.close()
        engine.dispose()


def test_one_component_round_trip(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "one_component.sqlite3")
    template = _template()
    target = _store_template_identity(session, name="interface")
    component = _component("interfaces", template_id=target.id, template_version=7)
    version = _version(template.id, 1, components=(component,))
    try:
        repo.add(template)
        repo.add_version(version)
        loaded = repo.get_version(template.id, 1)
        assert loaded is not None
        assert loaded.components == (component,)
    finally:
        session.close()
        engine.dispose()


def test_multiple_ordered_components_round_trip_and_order_preserved(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "components.sqlite3")
    template = _template()
    first_target = _store_template_identity(session, name="interface")
    second_target = _store_template_identity(session, name="module")
    version = _version(
        template.id,
        1,
        components=(
            _component("interfaces", template_id=first_target.id, template_version=2),
            _component("modules", template_id=second_target.id, template_version=5),
        ),
    )
    try:
        repo.add(template)
        repo.add_version(version)
        rows = session.scalars(
            select(ObjectTemplateComponentRow)
            .where(
                ObjectTemplateComponentRow.template_id == str(template.id),
                ObjectTemplateComponentRow.template_version == 1,
            )
            .order_by(ObjectTemplateComponentRow.position.asc())
        ).all()
        assert [(row.name, row.position) for row in rows] == [
            ("interfaces", 0),
            ("modules", 1),
        ]
        loaded = repo.get_version(template.id, 1)
        assert loaded is not None
        assert tuple(component.name for component in loaded.components) == (
            "interfaces",
            "modules",
        )
        assert loaded.components[0].template_id == first_target.id
        assert loaded.components[1].template_id == second_target.id
    finally:
        session.close()
        engine.dispose()


def test_delete_removes_identity_and_owned_versions_only(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "delete.sqlite3")
    target = _template(name="device")
    unrelated = _template(name="router")
    try:
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
        assert repo.list_versions(target.id) == ()
        assert repo.get(unrelated.id) == unrelated
        assert tuple(version.version for version in repo.list_versions(unrelated.id)) == (1,)
    finally:
        session.close()
        engine.dispose()


def test_delete_missing_identity_rejected(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "delete_missing.sqlite3")
    try:
        with pytest.raises(ObjectTemplateNotFound):
            repo.delete(uuid4())
    finally:
        session.close()
        engine.dispose()


def test_delete_does_not_commit_inside_repository(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "delete_no_commit.sqlite3")
    target = _template(name="device")
    try:
        repo.add(target)
        repo.add_version(_version(target.id, 1))
        session.commit()

        repo.delete(target.id)

        assert session.in_transaction()
        session.rollback()
        assert repo.get(target.id) == target
    finally:
        session.close()
        engine.dispose()


def test_delete_blocked_by_runtime_object_persistence_safety_net(
    tmp_path: Path,
) -> None:
    repo, session, engine = _repo(tmp_path, "delete_object_ref.sqlite3")
    target = _template(name="device")
    try:
        repo.add(target)
        repo.add_version(_version(target.id, 1))
        session.add(
            ObjectRow(
                id=str(uuid4()),
                template_id=str(target.id),
                template_version=1,
                properties_json="{}",
            )
        )
        session.flush()

        with pytest.raises(ObjectTemplatePersistenceError, match="object reference"):
            repo.delete(target.id)

        assert repo.get(target.id) == target
        assert tuple(version.version for version in repo.list_versions(target.id)) == (1,)
        assert session.get(ObjectRow, session.scalar(select(ObjectRow.id))) is not None
    finally:
        session.close()
        engine.dispose()


def test_delete_blocked_by_inheritance_persistence_safety_net(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "delete_inheritance_ref.sqlite3")
    target = _template(name="device")
    child = _template(name="router")
    try:
        _store_versions(repo, target, (_version(target.id, 1),))
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

        with pytest.raises(ObjectTemplatePersistenceError, match="inheritance reference"):
            repo.delete(target.id)

        assert repo.get(target.id) == target
        assert tuple(version.version for version in repo.list_versions(target.id)) == (1,)
    finally:
        session.close()
        engine.dispose()


def test_delete_blocked_by_component_persistence_safety_net(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "delete_component_ref.sqlite3")
    target = _template(name="interface")
    owner = _template(name="device")
    backup = _store_template_identity(session, name="backup_target")
    try:
        _store_versions(repo, target, (_version(target.id, 1),))
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

        with pytest.raises(ObjectTemplatePersistenceError, match="component reference"):
            repo.delete(target.id)

        assert repo.get(target.id) == target
        assert tuple(version.version for version in repo.list_versions(target.id)) == (1,)
    finally:
        session.close()
        engine.dispose()


def test_delete_blocked_by_relationship_definition_repository_precheck(
    tmp_path: Path,
) -> None:
    repo, session, engine = _repo(tmp_path, "delete_relationship_ref.sqlite3")
    target = _template(name="device")
    other = _template(name="credential")
    try:
        _store_versions(repo, target, (_version(target.id, 1),))
        _store_versions(repo, other, (_version(other.id, 1),))
        session.add(
            RelationshipDefinitionRow(
                id=str(uuid4()),
                source_template_id=str(target.id),
                target_template_id=str(other.id),
                forward_name="uses",
                reverse_name="is_used_by",
            )
        )
        session.flush()

        with pytest.raises(
            ObjectTemplatePersistenceError,
            match="relationship-definition reference",
        ):
            repo.delete(target.id)

        assert repo.get(target.id) == target
        assert tuple(version.version for version in repo.list_versions(target.id)) == (1,)
        assert session.get(
            RelationshipDefinitionRow,
            session.scalar(select(RelationshipDefinitionRow.id)),
        ) is not None
    finally:
        session.close()
        engine.dispose()


def test_delete_discovers_late_relationship_blocker_before_mutation(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "delete_late_relationship_ref.sqlite3")
    target = _template(name="device")
    other = _template(name="credential")
    try:
        _store_versions(
            repo,
            target,
            (
                _version(target.id, 1),
                _version(target.id, 2, status=ObjectTemplateVersionStatus.PUBLISHED),
            ),
        )
        _store_versions(repo, other, (_version(other.id, 1),))
        session.add(
            RelationshipDefinitionRow(
                id=str(uuid4()),
                source_template_id=str(other.id),
                target_template_id=str(target.id),
                forward_name="binds",
                reverse_name="bound_by",
            )
        )
        session.flush()

        with pytest.raises(ObjectTemplatePersistenceError):
            repo.delete(target.id)

        assert tuple(version.version for version in repo.list_versions(target.id)) == (1, 2)
    finally:
        session.close()
        engine.dispose()


def test_raw_session_delete_still_hits_relationship_definition_fk_restrict(
    tmp_path: Path,
) -> None:
    _repo_instance, session, engine = _repo(tmp_path, "raw_fk_restrict.sqlite3")
    target = _template(name="device")
    other = _template(name="credential")
    try:
        session.add(
            ObjectTemplateRow(
                id=str(target.id),
                namespace=target.namespace,
                name=target.name,
                description=target.description,
                abstract=target.abstract,
            )
        )
        session.add(
            ObjectTemplateRow(
                id=str(other.id),
                namespace=other.namespace,
                name=other.name,
                description=other.description,
                abstract=other.abstract,
            )
        )
        session.add(
            RelationshipDefinitionRow(
                id=str(uuid4()),
                source_template_id=str(target.id),
                target_template_id=str(other.id),
                forward_name="uses",
                reverse_name="is_used_by",
            )
        )
        session.commit()

        with pytest.raises(IntegrityError):
            session.execute(
                delete(ObjectTemplateRow).where(ObjectTemplateRow.id == str(target.id))
            )
    finally:
        session.close()
        engine.dispose()


def test_properties_and_components_coexist_in_same_version(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "properties_components.sqlite3")
    template = _template()
    datatype, datatype_version = _store_datatype_version(session, name="hostname")
    target = _store_template_identity(session, name="interface")
    version = _version(
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
        components=(_component("interfaces", template_id=target.id, template_version=3),),
    )
    try:
        repo.add(template)
        repo.add_version(version)
        loaded = repo.get_version(template.id, 1)
        assert loaded == version
    finally:
        session.close()
        engine.dispose()


def test_missing_owning_template_rejected(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "missing_owner.sqlite3")
    version = _version(uuid4(), 1)
    try:
        with pytest.raises(ObjectTemplateNotFound, match="Owning object template does not exist."):
            repo.add_version(version)
    finally:
        session.close()
        engine.dispose()


def test_duplicate_version_rejected(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "dup_version.sqlite3")
    template = _template()
    version = _version(template.id, 1)
    try:
        repo.add(template)
        repo.add_version(version)
        with pytest.raises(ObjectTemplateVersionAlreadyExists):
            repo.add_version(version)
    finally:
        session.close()
        engine.dispose()


def test_list_versions_ascending(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "list_versions.sqlite3")
    template = _template()
    v5 = _version(template.id, 5, status=ObjectTemplateVersionStatus.DEPRECATED)
    v1 = _version(template.id, 1, status=ObjectTemplateVersionStatus.PUBLISHED)
    v2 = _version(template.id, 2)
    try:
        _store_versions(repo, template, (v5, v1, v2))
        versions = repo.list_versions(template.id)
        assert tuple(version.version for version in versions) == (1, 2, 5)
    finally:
        session.close()
        engine.dispose()


def test_replace_version_with_revised_properties(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "replace_props.sqlite3")
    template = _template()
    hostname_datatype, hostname_v1 = _store_datatype_version(session, name="hostname")
    serial_datatype, serial_v1 = _store_datatype_version(session, name="serial")
    original = _version(
        template.id,
        1,
        properties=(
            _property(
                "hostname",
                datatype_id=hostname_datatype.id,
                datatype_version=hostname_v1.version,
            ),
        ),
    )
    replacement = _version(
        template.id,
        1,
        properties=(
            _property(
                "serial",
                datatype_id=serial_datatype.id,
                datatype_version=serial_v1.version,
            ),
        ),
    )
    try:
        repo.add(template)
        repo.add_version(original)
        repo.replace_version(replacement)
        loaded = repo.get_version(template.id, 1)
        assert loaded == replacement
    finally:
        session.close()
        engine.dispose()


def test_replace_version_replaces_components(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "replace_components.sqlite3")
    template = _template()
    original_target = _store_template_identity(session, name="interface")
    replacement_target = _store_template_identity(session, name="module")
    original = _version(
        template.id,
        1,
        components=(_component("interfaces", template_id=original_target.id, template_version=1),),
    )
    replacement = _version(
        template.id,
        1,
        components=(_component("modules", template_id=replacement_target.id, template_version=7),),
    )
    try:
        repo.add(template)
        repo.add_version(original)
        repo.replace_version(replacement)
        loaded = repo.get_version(template.id, 1)
        assert loaded == replacement
        rows = session.scalars(
            select(ObjectTemplateComponentRow)
            .where(
                ObjectTemplateComponentRow.template_id == str(template.id),
                ObjectTemplateComponentRow.template_version == 1,
            )
            .order_by(ObjectTemplateComponentRow.position.asc())
        ).all()
        assert [(row.name, row.position) for row in rows] == [("modules", 0)]
    finally:
        session.close()
        engine.dispose()


def test_replace_version_with_changed_parent(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "replace_parent.sqlite3")
    template = _template(name="child")
    parent = _template(name="parent")
    original = _version(template.id, 1, parent=None)
    replacement = _version(
        template.id,
        1,
        parent=ObjectTemplateVersionRef(template_id=parent.id, version=2),
    )
    try:
        repo.add(parent)
        repo.add_version(_version(parent.id, 2))
        repo.add(template)
        repo.add_version(original)
        repo.replace_version(replacement)
        loaded = repo.get_version(template.id, 1)
        assert loaded == replacement
    finally:
        session.close()
        engine.dispose()


def test_replace_version_missing_exact_parent_maps_to_persistence_error(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "replace_missing_parent.sqlite3")
    template = _template(name="child")
    parent = _template(name="parent")
    original = _version(template.id, 1, parent=None)
    replacement = _version(
        template.id,
        1,
        parent=ObjectTemplateVersionRef(template_id=parent.id, version=2),
    )
    try:
        repo.add(parent)
        repo.add_version(_version(parent.id, 1))
        repo.add(template)
        repo.add_version(original)
        with pytest.raises(ObjectTemplatePersistenceError):
            repo.replace_version(replacement)
    finally:
        session.close()
        engine.dispose()


def test_replace_lifecycle_snapshot_preserves_complete_replacement_snapshot(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "replace_status.sqlite3")
    template = _template()
    hostname_datatype, hostname_v1 = _store_datatype_version(session, name="hostname")
    serial_datatype, serial_v1 = _store_datatype_version(session, name="serial")
    original_target = _store_template_identity(session, name="interface")
    original = _version(
        template.id,
        1,
        status=ObjectTemplateVersionStatus.DRAFT,
        properties=(
            _property(
                "hostname",
                datatype_id=hostname_datatype.id,
                datatype_version=hostname_v1.version,
            ),
        ),
        components=(_component("interfaces", template_id=original_target.id, template_version=2),),
    )
    replacement = _version(
        template.id,
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        properties=original.properties,
        components=original.components,
    )
    try:
        repo.add(template)
        repo.add_version(original)
        repo.replace_version(replacement)
        loaded = repo.get_version(template.id, 1)
        assert loaded == replacement
        assert loaded is not None
        assert loaded.status is ObjectTemplateVersionStatus.PUBLISHED
        assert tuple(prop.name for prop in loaded.properties) == ("hostname",)
        assert tuple(component.name for component in loaded.components) == ("interfaces",)
    finally:
        session.close()
        engine.dispose()


def test_add_version_requires_draft_status(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "add_status_requires_draft.sqlite3")
    template = _template()
    published = _version(template.id, 1, status=ObjectTemplateVersionStatus.PUBLISHED)
    deprecated = _version(template.id, 1, status=ObjectTemplateVersionStatus.DEPRECATED)
    try:
        repo.add(template)
        with pytest.raises(ObjectTemplatePersistenceError):
            repo.add_version(published)
        with pytest.raises(ObjectTemplatePersistenceError):
            repo.add_version(deprecated)
        assert repo.get_version(template.id, 1) is None
    finally:
        session.close()
        engine.dispose()


def test_duplicate_version_precedes_add_status_validation(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "add_duplicate_precedes_status.sqlite3")
    template = _template()
    draft = _version(template.id, 1)
    published = _version(template.id, 1, status=ObjectTemplateVersionStatus.PUBLISHED)
    try:
        _store_versions(repo, template, (draft,))
        with pytest.raises(ObjectTemplateVersionAlreadyExists):
            repo.add_version(published)
    finally:
        session.close()
        engine.dispose()


def test_replace_version_rejects_publication_parent_change(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "publish_parent_change.sqlite3")
    template = _template(name="child")
    parent = _template(name="parent")
    draft = _version(
        template.id,
        1,
        parent=ObjectTemplateVersionRef(template_id=parent.id, version=1),
    )
    illegal = _version(
        template.id,
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        parent=ObjectTemplateVersionRef(template_id=parent.id, version=2),
    )
    try:
        repo.add(parent)
        repo.add_version(_version(parent.id, 1))
        repo.add_version(_version(parent.id, 2))
        repo.add(template)
        repo.add_version(draft)
        with pytest.raises(ObjectTemplatePersistenceError):
            repo.replace_version(illegal)
        assert repo.get_version(template.id, 1) == draft
    finally:
        session.close()
        engine.dispose()


def test_replace_version_rejects_publication_property_change(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "publish_property_change.sqlite3")
    template = _template()
    hostname_datatype, hostname_v1 = _store_datatype_version(session, name="hostname")
    serial_datatype, serial_v1 = _store_datatype_version(session, name="serial")
    draft = _version(
        template.id,
        1,
        properties=(
            _property(
                "hostname",
                datatype_id=hostname_datatype.id,
                datatype_version=hostname_v1.version,
            ),
        ),
    )
    illegal = _version(
        template.id,
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        properties=(
            _property(
                "serial",
                datatype_id=serial_datatype.id,
                datatype_version=serial_v1.version,
            ),
        ),
    )
    try:
        repo.add(template)
        repo.add_version(draft)
        with pytest.raises(ObjectTemplatePersistenceError):
            repo.replace_version(illegal)
        assert repo.get_version(template.id, 1) == draft
    finally:
        session.close()
        engine.dispose()


def test_replace_version_rejects_publication_component_change(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "publish_component_change.sqlite3")
    template = _template()
    interface = _store_template_identity(session, name="interface")
    module = _store_template_identity(session, name="module")
    draft = _version(
        template.id,
        1,
        components=(_component("interfaces", template_id=interface.id),),
    )
    illegal = _version(
        template.id,
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        components=(_component("modules", template_id=module.id),),
    )
    try:
        repo.add(template)
        repo.add_version(draft)
        with pytest.raises(ObjectTemplatePersistenceError):
            repo.replace_version(illegal)
        assert repo.get_version(template.id, 1) == draft
    finally:
        session.close()
        engine.dispose()


def test_replace_version_rejects_publication_property_order_change(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "publish_property_order_change.sqlite3")
    template = _template()
    hostname_datatype, hostname_v1 = _store_datatype_version(session, name="hostname")
    serial_datatype, serial_v1 = _store_datatype_version(session, name="serial")
    first = _property(
        "hostname",
        datatype_id=hostname_datatype.id,
        datatype_version=hostname_v1.version,
    )
    second = _property("serial", datatype_id=serial_datatype.id, datatype_version=serial_v1.version)
    draft = _version(template.id, 1, properties=(first, second))
    illegal = _version(
        template.id,
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        properties=(second, first),
    )
    try:
        repo.add(template)
        repo.add_version(draft)
        with pytest.raises(ObjectTemplatePersistenceError):
            repo.replace_version(illegal)
        assert repo.get_version(template.id, 1) == draft
    finally:
        session.close()
        engine.dispose()


def test_replace_version_allows_published_to_deprecated_status_only(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "published_to_deprecated.sqlite3")
    template = _template()
    published = _version(template.id, 1, status=ObjectTemplateVersionStatus.PUBLISHED)
    deprecated = _version(template.id, 1, status=ObjectTemplateVersionStatus.DEPRECATED)
    try:
        _store_versions(repo, template, (published,))
        repo.replace_version(deprecated)
        assert repo.get_version(template.id, 1) == deprecated
    finally:
        session.close()
        engine.dispose()


def test_replace_version_rejects_deprecation_snapshot_change(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "deprecate_property_change.sqlite3")
    template = _template()
    hostname_datatype, hostname_v1 = _store_datatype_version(session, name="hostname")
    serial_datatype, serial_v1 = _store_datatype_version(session, name="serial")
    published = _version(
        template.id,
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        properties=(
            _property(
                "hostname",
                datatype_id=hostname_datatype.id,
                datatype_version=hostname_v1.version,
            ),
        ),
    )
    illegal = _version(
        template.id,
        1,
        status=ObjectTemplateVersionStatus.DEPRECATED,
        properties=(
            _property(
                "serial",
                datatype_id=serial_datatype.id,
                datatype_version=serial_v1.version,
            ),
        ),
    )
    try:
        _store_versions(repo, template, (published,))
        with pytest.raises(ObjectTemplatePersistenceError):
            repo.replace_version(illegal)
        assert repo.get_version(template.id, 1) == published
    finally:
        session.close()
        engine.dispose()


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
    tmp_path: Path,
    stored: ObjectTemplateVersionStatus,
    replacement_status: ObjectTemplateVersionStatus,
) -> None:
    repo, session, engine = _repo(
        tmp_path,
        f"lifecycle_reject_{stored.value}_{replacement_status.value}.sqlite3",
    )
    template = _template()
    current = _version(template.id, 1, status=stored)
    illegal = _version(template.id, 1, status=replacement_status)
    try:
        _store_versions(repo, template, (current,))
        with pytest.raises(ObjectTemplatePersistenceError):
            repo.replace_version(illegal)
        assert repo.get_version(template.id, 1) == current
    finally:
        session.close()
        engine.dispose()


def test_rejected_replace_leaves_committed_snapshot_unchanged_after_rollback(
    tmp_path: Path,
) -> None:
    repo, session, engine = _repo(tmp_path, "replace_rollback_immutability.sqlite3")
    session_factory = sessionmaker(engine, expire_on_commit=False)
    template = _template()
    hostname_datatype, hostname_v1 = _store_datatype_version(session, name="hostname")
    serial_datatype, serial_v1 = _store_datatype_version(session, name="serial")
    original = _version(
        template.id,
        1,
        properties=(
            _property(
                "hostname",
                datatype_id=hostname_datatype.id,
                datatype_version=hostname_v1.version,
            ),
        ),
    )
    illegal = _version(
        template.id,
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        properties=(
            _property(
                "serial",
                datatype_id=serial_datatype.id,
                datatype_version=serial_v1.version,
            ),
        ),
    )
    try:
        repo.add(template)
        repo.add_version(original)
        session.commit()

        with pytest.raises(ObjectTemplatePersistenceError):
            repo.replace_version(illegal)
        session.rollback()

        fresh_session = session_factory()
        try:
            fresh_repo = SqlAlchemyObjectTemplateRepository(fresh_session)
            assert fresh_repo.get_version(template.id, 1) == original
        finally:
            fresh_session.close()
    finally:
        session.close()
        engine.dispose()


def test_publish_status_transition_does_not_rewrite_parent_or_child_rows(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "publish_status_only_sql_shape.sqlite3")
    statements: list[str] = []

    def recorder(
        conn, cursor, statement, parameters, context, executemany
    ) -> None:
        del conn, cursor, parameters, context, executemany
        statements.append(statement.lower())

    template = _template(name="child")
    parent = _template(name="parent")
    datatype, datatype_version = _store_datatype_version(session, name="hostname")
    component_target = _store_template_identity(session, name="interface")
    draft = _version(
        template.id,
        1,
        parent=ObjectTemplateVersionRef(template_id=parent.id, version=1),
        properties=(
            _property(
                "hostname",
                datatype_id=datatype.id,
                datatype_version=datatype_version.version,
            ),
        ),
        components=(_component("interfaces", template_id=component_target.id),),
    )
    published = _version(
        template.id,
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        parent=draft.parent,
        properties=draft.properties,
        components=draft.components,
    )
    try:
        repo.add(parent)
        repo.add_version(_version(parent.id, 1))
        repo.add(template)
        repo.add_version(draft)

        event.listen(engine, "before_cursor_execute", recorder)
        try:
            repo.replace_version(published)
        finally:
            event.remove(engine, "before_cursor_execute", recorder)

        version_updates = [
            statement
            for statement in statements
            if "update object_template_versions" in statement
        ]
        assert any("status" in statement for statement in version_updates)
        assert all("parent_template_id" not in statement for statement in version_updates)
        assert all("parent_version" not in statement for statement in version_updates)
        assert not any(
            "delete from object_template_properties" in statement
            for statement in statements
        )
        assert not any(
            "insert into object_template_properties" in statement
            for statement in statements
        )
        assert not any(
            "delete from object_template_components" in statement
            for statement in statements
        )
        assert not any(
            "insert into object_template_components" in statement
            for statement in statements
        )
    finally:
        session.close()
        engine.dispose()


def test_deprecate_status_transition_does_not_rewrite_parent_or_child_rows(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "deprecate_status_only_sql_shape.sqlite3")
    statements: list[str] = []

    def recorder(
        conn, cursor, statement, parameters, context, executemany
    ) -> None:
        del conn, cursor, parameters, context, executemany
        statements.append(statement.lower())

    template = _template(name="child")
    parent = _template(name="parent")
    datatype, datatype_version = _store_datatype_version(session, name="hostname")
    component_target = _store_template_identity(session, name="interface")
    published = _version(
        template.id,
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        parent=ObjectTemplateVersionRef(template_id=parent.id, version=1),
        properties=(
            _property(
                "hostname",
                datatype_id=datatype.id,
                datatype_version=datatype_version.version,
            ),
        ),
        components=(_component("interfaces", template_id=component_target.id),),
    )
    deprecated = _version(
        template.id,
        1,
        status=ObjectTemplateVersionStatus.DEPRECATED,
        parent=published.parent,
        properties=published.properties,
        components=published.components,
    )
    try:
        repo.add(parent)
        repo.add_version(_version(parent.id, 1))
        _store_versions(repo, template, (published,))

        event.listen(engine, "before_cursor_execute", recorder)
        try:
            repo.replace_version(deprecated)
        finally:
            event.remove(engine, "before_cursor_execute", recorder)

        version_updates = [
            statement
            for statement in statements
            if "update object_template_versions" in statement
        ]
        assert any("status" in statement for statement in version_updates)
        assert all("parent_template_id" not in statement for statement in version_updates)
        assert all("parent_version" not in statement for statement in version_updates)
        assert not any(
            "delete from object_template_properties" in statement
            for statement in statements
        )
        assert not any(
            "insert into object_template_properties" in statement
            for statement in statements
        )
        assert not any(
            "delete from object_template_components" in statement
            for statement in statements
        )
        assert not any(
            "insert into object_template_components" in statement
            for statement in statements
        )
    finally:
        session.close()
        engine.dispose()


def test_replace_missing_rejected(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "replace_missing.sqlite3")
    template = _template()
    version = _version(template.id, 1)
    try:
        repo.add(template)
        with pytest.raises(ObjectTemplateVersionNotFound):
            repo.replace_version(version)
    finally:
        session.close()
        engine.dispose()


def test_malformed_stored_uuid_produces_persistence_error(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "bad_uuid.sqlite3")
    try:
        session.add(
            ObjectTemplateRow(
                id="not-a-uuid",
                namespace="network",
                name="device",
                description=None,
                abstract=False,
            )
        )
        session.flush()
        with pytest.raises(ObjectTemplatePersistenceError):
            repo.get_by_name("network", "device")
    finally:
        session.close()
        engine.dispose()


def test_malformed_status_produces_persistence_error(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "bad_status.sqlite3")
    template = _template()
    try:
        repo.add(template)
        session.add(
            ObjectTemplateVersionRow(
                template_id=str(template.id),
                version=1,
                status="invalid",
                parent_template_id=None,
                parent_version=None,
            )
        )
        session.flush()
        with pytest.raises(ObjectTemplatePersistenceError):
            repo.get_version(template.id, 1)
    finally:
        session.close()
        engine.dispose()


def test_malformed_stored_property_row_produces_persistence_error(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "bad_property_row.sqlite3")
    template = _template()
    datatype, datatype_version = _store_datatype_version(session, name="hostname")
    try:
        repo.add(template)
        session.add(
            ObjectTemplateVersionRow(
                template_id=str(template.id),
                version=1,
                status=ObjectTemplateVersionStatus.DRAFT.value,
                parent_template_id=None,
                parent_version=None,
            )
        )
        session.flush()
        session.add(
            ObjectTemplatePropertyRow(
                template_id=str(template.id),
                template_version=1,
                position=0,
                name="Host-Name",
                datatype_id=str(datatype.id),
                datatype_version=datatype_version.version,
                required=True,
            )
        )
        session.flush()
        with pytest.raises(ObjectTemplatePersistenceError):
            repo.get_version(template.id, 1)
    finally:
        session.close()
        engine.dispose()


def test_malformed_stored_component_row_produces_persistence_error(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "bad_component_row.sqlite3")
    template = _template()
    target = _store_template_identity(session, name="interface")
    try:
        repo.add(template)
        session.add(
            ObjectTemplateVersionRow(
                template_id=str(template.id),
                version=1,
                status=ObjectTemplateVersionStatus.DRAFT.value,
                parent_template_id=None,
                parent_version=None,
            )
        )
        session.flush()
        session.add(
            ObjectTemplateComponentRow(
                template_id=str(template.id),
                template_version=1,
                position=0,
                name="Interfaces",
                target_template_id=str(target.id),
            )
        )
        session.flush()
        with pytest.raises(ObjectTemplatePersistenceError):
            repo.get_version(template.id, 1)
    finally:
        session.close()
        engine.dispose()


def test_missing_component_target_identity_is_rejected_by_fk(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "missing_component_target.sqlite3")
    template = _template()
    version = _version(
        template.id,
        1,
        components=(_component("interfaces", template_id=uuid4(), template_version=7),),
    )
    try:
        repo.add(template)
        with pytest.raises(ObjectTemplatePersistenceError):
            repo.add_version(version)
    finally:
        session.close()
        engine.dispose()


def test_component_target_existing_identity_with_only_draft_versions_persists(
    tmp_path: Path,
) -> None:
    repo, session, engine = _repo(tmp_path, "draft_only_component_target.sqlite3")
    template = _template()
    target = _template(name="interface")
    try:
        repo.add(template)
        repo.add(target)
        repo.add_version(_version(target.id, 1, status=ObjectTemplateVersionStatus.DRAFT))
        version = _version(
            template.id,
            1,
            components=(_component("interfaces", template_id=target.id, template_version=7),),
        )
        repo.add_version(version)
        assert repo.get_version(template.id, 1) == version
    finally:
        session.close()
        engine.dispose()


def test_add_version_missing_parent_identity_hits_exact_parent_fk(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "missing_parent_identity.sqlite3")
    template = _template()
    version = _version(
        template.id,
        1,
        parent=ObjectTemplateVersionRef(template_id=uuid4(), version=1),
    )
    try:
        repo.add(template)
        with pytest.raises(ObjectTemplatePersistenceError):
            repo.add_version(version)
    finally:
        session.close()
        engine.dispose()


def test_add_version_missing_exact_parent_version_hits_exact_parent_fk(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "missing_parent_version.sqlite3")
    child = _template(name="child")
    parent = _template(name="parent")
    try:
        repo.add(parent)
        repo.add_version(_version(parent.id, 1))
        repo.add_version(_version(parent.id, 3))
        repo.add(child)
        with pytest.raises(ObjectTemplatePersistenceError):
            repo.add_version(
                _version(
                    child.id,
                    1,
                    parent=ObjectTemplateVersionRef(template_id=parent.id, version=2),
                )
            )
    finally:
        session.close()
        engine.dispose()


def test_add_version_with_valid_exact_parent_round_trips(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "valid_exact_parent.sqlite3")
    child = _template(name="child")
    parent = _template(name="parent")
    parent_version = _version(parent.id, 2)
    child_version = _version(
        child.id,
        1,
        parent=ObjectTemplateVersionRef(template_id=parent.id, version=2),
    )
    try:
        repo.add(parent)
        repo.add_version(parent_version)
        repo.add(child)
        repo.add_version(child_version)
        assert repo.get_version(child.id, 1) == child_version
    finally:
        session.close()
        engine.dispose()


def test_add_version_allows_exact_existing_draft_parent(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "draft_parent_persists.sqlite3")
    child = _template(name="child")
    parent = _template(name="parent")
    parent_version = _version(parent.id, 1, status=ObjectTemplateVersionStatus.DRAFT)
    child_version = _version(
        child.id,
        1,
        parent=ObjectTemplateVersionRef(template_id=parent.id, version=1),
    )
    try:
        repo.add(parent)
        repo.add_version(parent_version)
        repo.add(child)
        repo.add_version(child_version)
        assert repo.get_version(child.id, 1) == child_version
    finally:
        session.close()
        engine.dispose()


def test_partial_parent_template_id_without_version_is_db_rejected(tmp_path: Path) -> None:
    _repo_instance, session, engine = _repo(tmp_path, "partial_parent_template_only.sqlite3")
    template = _template()
    try:
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
        with pytest.raises(IntegrityError):
            session.add(
                ObjectTemplateVersionRow(
                    template_id=str(template.id),
                    version=1,
                    status=ObjectTemplateVersionStatus.DRAFT.value,
                    parent_template_id=str(uuid4()),
                    parent_version=None,
                )
            )
            session.flush()
    finally:
        session.close()
        engine.dispose()


def test_partial_parent_version_without_template_id_is_db_rejected(tmp_path: Path) -> None:
    _repo_instance, session, engine = _repo(tmp_path, "partial_parent_version_only.sqlite3")
    template = _template()
    try:
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
        with pytest.raises(IntegrityError):
            session.add(
                ObjectTemplateVersionRow(
                    template_id=str(template.id),
                    version=1,
                    status=ObjectTemplateVersionStatus.DRAFT.value,
                    parent_template_id=None,
                    parent_version=1,
                )
            )
            session.flush()
    finally:
        session.close()
        engine.dispose()


def test_replace_version_requires_component_target_identity_to_exist(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "replace_component_target.sqlite3")
    template = _template()
    original_target = _store_template_identity(session, name="interface")
    original = _version(
        template.id,
        1,
        components=(_component("interfaces", template_id=original_target.id),),
    )
    replacement = _version(
        template.id,
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        components=(_component("interfaces", template_id=uuid4(), template_version=99),),
    )
    try:
        repo.add(template)
        repo.add_version(original)
        with pytest.raises(ObjectTemplatePersistenceError):
            repo.replace_version(replacement)
    finally:
        session.close()
        engine.dispose()


def test_raw_delete_of_referenced_exact_parent_version_hits_fk_restrict(
    tmp_path: Path,
) -> None:
    repo, session, engine = _repo(tmp_path, "parent_fk_restrict.sqlite3")
    parent = _template(name="parent")
    child = _template(name="child")
    try:
        repo.add(parent)
        repo.add(child)
        repo.add_version(_version(parent.id, 1))
        repo.add_version(_version(parent.id, 2))
        repo.add_version(
            _version(
                child.id,
                1,
                parent=ObjectTemplateVersionRef(template_id=parent.id, version=1),
            )
        )
        session.commit()

        with pytest.raises(IntegrityError):
            session.execute(
                delete(ObjectTemplateVersionRow).where(
                    ObjectTemplateVersionRow.template_id == str(parent.id),
                    ObjectTemplateVersionRow.version == 1,
                )
            )
            session.commit()
    finally:
        session.close()
        engine.dispose()


def test_raw_delete_of_unreferenced_sibling_parent_version_is_allowed(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "parent_sibling_delete.sqlite3")
    parent = _template(name="parent")
    child = _template(name="child")
    try:
        repo.add(parent)
        repo.add(child)
        repo.add_version(_version(parent.id, 1))
        repo.add_version(_version(parent.id, 2))
        repo.add_version(
            _version(
                child.id,
                1,
                parent=ObjectTemplateVersionRef(template_id=parent.id, version=1),
            )
        )
        session.commit()

        session.execute(
            delete(ObjectTemplateVersionRow).where(
                ObjectTemplateVersionRow.template_id == str(parent.id),
                ObjectTemplateVersionRow.version == 2,
            )
        )
        session.commit()

        assert repo.get_version(parent.id, 2) is None
        assert repo.get_version(parent.id, 1) is not None
    finally:
        session.close()
        engine.dispose()


def test_schema_normalizes_object_template_properties(tmp_path: Path) -> None:
    _repo_instance, session, engine = _repo(tmp_path, "schema.sqlite3")
    try:
        inspector = inspect(engine)
        columns = {column["name"] for column in inspector.get_columns("object_template_properties")}
        assert columns == {
            "template_id",
            "template_version",
            "position",
            "name",
            "datatype_id",
            "datatype_version",
            "required",
        }
        assert "properties_json" not in ObjectTemplateVersionRow.__table__.c
        assert "components_json" not in ObjectTemplateVersionRow.__table__.c

        pk = inspector.get_pk_constraint("object_template_properties")
        assert pk["name"] == "pk_object_template_properties"
        assert pk["constrained_columns"] == ["template_id", "template_version", "name"]

        unique_constraints = {
            constraint["name"]: tuple(constraint["column_names"])
            for constraint in inspector.get_unique_constraints("object_template_properties")
        }
        assert unique_constraints["uq_object_template_properties_owner_position"] == (
            "template_id",
            "template_version",
            "position",
        )

        foreign_keys = {
            fk["name"]: (
                tuple(fk["constrained_columns"]),
                fk["referred_table"],
                tuple(fk["referred_columns"]),
                (fk.get("options") or {}).get("ondelete"),
            )
            for fk in inspector.get_foreign_keys("object_template_properties")
        }
        assert foreign_keys["fk_object_template_properties_owner"] == (
            ("template_id", "template_version"),
            "object_template_versions",
            ("template_id", "version"),
            "CASCADE",
        )
        assert foreign_keys["fk_object_template_properties_datatype_version"] == (
            ("datatype_id", "datatype_version"),
            "datatype_versions",
            ("datatype_id", "version"),
            "RESTRICT",
        )

        indexes = {
            index["name"]: tuple(index["column_names"])
            for index in inspector.get_indexes("object_template_properties")
        }
        assert indexes["ix_object_template_properties_datatype_version"] == (
            "datatype_id",
            "datatype_version",
        )
    finally:
        session.close()
        engine.dispose()


def test_schema_normalizes_exact_parent_reference_on_object_template_versions(
    tmp_path: Path,
) -> None:
    _repo_instance, session, engine = _repo(tmp_path, "parent_schema.sqlite3")
    try:
        inspector = inspect(engine)

        pk = inspector.get_pk_constraint("object_template_versions")
        assert pk["name"] == "pk_object_template_versions"
        assert pk["constrained_columns"] == ["template_id", "version"]

        foreign_keys = {
            fk["name"]: (
                tuple(fk["constrained_columns"]),
                fk["referred_table"],
                tuple(fk["referred_columns"]),
                (fk.get("options") or {}).get("ondelete"),
            )
            for fk in inspector.get_foreign_keys("object_template_versions")
        }
        assert foreign_keys["fk_object_template_versions_parent"] == (
            ("parent_template_id", "parent_version"),
            "object_template_versions",
            ("template_id", "version"),
            "RESTRICT",
        )

        checks = {
            check["name"]: check["sqltext"]
            for check in inspector.get_check_constraints("object_template_versions")
        }
        assert "ck_object_template_versions_parent_pair" in checks

        indexes = {
            index["name"]: tuple(index["column_names"])
            for index in inspector.get_indexes("object_template_versions")
        }
        assert indexes["ix_object_template_versions_parent"] == (
            "parent_template_id",
            "parent_version",
        )
    finally:
        session.close()
        engine.dispose()


def test_schema_normalizes_object_template_components(tmp_path: Path) -> None:
    _repo_instance, session, engine = _repo(tmp_path, "component_schema.sqlite3")
    try:
        inspector = inspect(engine)
        columns = {column["name"] for column in inspector.get_columns("object_template_components")}
        assert columns == {
            "template_id",
            "template_version",
            "position",
            "name",
            "target_template_id",
        }
        assert "target_template_version" not in columns
        assert "template_target_version" not in columns
        assert "component_version" not in columns

        pk = inspector.get_pk_constraint("object_template_components")
        assert pk["name"] == "pk_object_template_components"
        assert pk["constrained_columns"] == ["template_id", "template_version", "name"]

        unique_constraints = {
            constraint["name"]: tuple(constraint["column_names"])
            for constraint in inspector.get_unique_constraints("object_template_components")
        }
        assert unique_constraints["uq_object_template_components_owner_position"] == (
            "template_id",
            "template_version",
            "position",
        )

        foreign_keys = {
            fk["name"]: (
                tuple(fk["constrained_columns"]),
                fk["referred_table"],
                tuple(fk["referred_columns"]),
                (fk.get("options") or {}).get("ondelete"),
            )
            for fk in inspector.get_foreign_keys("object_template_components")
        }
        assert foreign_keys["fk_object_template_components_owner"] == (
            ("template_id", "template_version"),
            "object_template_versions",
            ("template_id", "version"),
            "CASCADE",
        )
        assert foreign_keys["fk_object_template_components_target_template"] == (
            ("target_template_id",),
            "object_templates",
            ("id",),
            "RESTRICT",
        )

        indexes = {
            index["name"]: tuple(index["column_names"])
            for index in inspector.get_indexes("object_template_components")
        }
        assert indexes["ix_object_template_components_target_template"] == (
            "target_template_id",
        )
    finally:
        session.close()
        engine.dispose()


def test_add_version_missing_datatype_identity_hits_exact_fk(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "missing_datatype_identity.sqlite3")
    template = _template()
    version = _version(
        template.id,
        1,
        properties=(
            _property("hostname", datatype_id=uuid4(), datatype_version=1, required=True),
        ),
    )
    try:
        repo.add(template)
        with pytest.raises(ObjectTemplatePersistenceError):
            repo.add_version(version)
    finally:
        session.close()
        engine.dispose()


def test_add_version_missing_exact_datatype_version_hits_exact_fk(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "missing_datatype_version.sqlite3")
    template = _template()
    datatype, _ = _store_datatype_version(session, datatype_id=uuid4(), version=1, name="hostname")
    version = _version(
        template.id,
        1,
        properties=(
            _property("hostname", datatype_id=datatype.id, datatype_version=2, required=True),
        ),
    )
    try:
        repo.add(template)
        with pytest.raises(ObjectTemplatePersistenceError):
            repo.add_version(version)
    finally:
        session.close()
        engine.dispose()


def test_add_version_with_valid_exact_datatype_reference_succeeds(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "valid_exact_datatype_fk.sqlite3")
    template = _template()
    datatype, datatype_version = _store_datatype_version(
        session,
        datatype_id=uuid4(),
        version=2,
        name="hostname",
    )
    version = _version(
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
    try:
        repo.add(template)
        repo.add_version(version)
        assert repo.get_version(template.id, 1) == version
    finally:
        session.close()
        engine.dispose()


def test_raw_orphan_property_owner_fk_is_rejected(tmp_path: Path) -> None:
    _repo_instance, session, engine = _repo(tmp_path, "orphan_property_owner.sqlite3")
    datatype, datatype_version = _store_datatype_version(session, name="hostname")
    try:
        with pytest.raises(IntegrityError):
            session.add(
                ObjectTemplatePropertyRow(
                    template_id=str(uuid4()),
                    template_version=99,
                    position=0,
                    name="hostname",
                    datatype_id=str(datatype.id),
                    datatype_version=datatype_version.version,
                    required=True,
                )
            )
            session.flush()
    finally:
        session.close()
        engine.dispose()


def test_raw_orphan_component_owner_fk_is_rejected(tmp_path: Path) -> None:
    _repo_instance, session, engine = _repo(tmp_path, "orphan_component_owner.sqlite3")
    target = _store_template_identity(session, name="interface")
    try:
        with pytest.raises(IntegrityError):
            session.add(
                ObjectTemplateComponentRow(
                    template_id=str(uuid4()),
                    template_version=99,
                    position=0,
                    name="interfaces",
                    target_template_id=str(target.id),
                )
            )
            session.flush()
    finally:
        session.close()
        engine.dispose()


def test_duplicate_property_name_in_same_version_is_rejected_by_db(tmp_path: Path) -> None:
    _repo_instance, session, engine = _repo(tmp_path, "dup_property_name.sqlite3")
    template = _template()
    datatype, datatype_version = _store_datatype_version(session, name="hostname")
    try:
        session.add(
            ObjectTemplateRow(
                id=str(template.id),
                namespace=template.namespace,
                name=template.name,
                description=template.description,
                abstract=template.abstract,
            )
        )
        session.add(
            ObjectTemplateVersionRow(
                template_id=str(template.id),
                version=1,
                status=ObjectTemplateVersionStatus.DRAFT.value,
                parent_template_id=None,
                parent_version=None,
            )
        )
        session.flush()
        session.add(
            ObjectTemplatePropertyRow(
                template_id=str(template.id),
                template_version=1,
                position=0,
                name="hostname",
                datatype_id=str(datatype.id),
                datatype_version=datatype_version.version,
                required=True,
            )
        )
        session.add(
            ObjectTemplatePropertyRow(
                template_id=str(template.id),
                template_version=1,
                position=1,
                name="hostname",
                datatype_id=str(datatype.id),
                datatype_version=datatype_version.version,
                required=False,
            )
        )
        with pytest.raises(IntegrityError):
            session.flush()
    finally:
        session.close()
        engine.dispose()


def test_duplicate_property_position_in_same_version_is_rejected_by_db(tmp_path: Path) -> None:
    _repo_instance, session, engine = _repo(tmp_path, "dup_property_position.sqlite3")
    template = _template()
    datatype, datatype_version = _store_datatype_version(session, name="hostname")
    try:
        session.add(
            ObjectTemplateRow(
                id=str(template.id),
                namespace=template.namespace,
                name=template.name,
                description=template.description,
                abstract=template.abstract,
            )
        )
        session.add(
            ObjectTemplateVersionRow(
                template_id=str(template.id),
                version=1,
                status=ObjectTemplateVersionStatus.DRAFT.value,
                parent_template_id=None,
                parent_version=None,
            )
        )
        session.flush()
        session.add(
            ObjectTemplatePropertyRow(
                template_id=str(template.id),
                template_version=1,
                position=0,
                name="hostname",
                datatype_id=str(datatype.id),
                datatype_version=datatype_version.version,
                required=True,
            )
        )
        session.add(
            ObjectTemplatePropertyRow(
                template_id=str(template.id),
                template_version=1,
                position=0,
                name="serial",
                datatype_id=str(datatype.id),
                datatype_version=datatype_version.version,
                required=False,
            )
        )
        with pytest.raises(IntegrityError):
            session.flush()
    finally:
        session.close()
        engine.dispose()


def test_same_property_name_and_position_in_different_versions_are_allowed(tmp_path: Path) -> None:
    _repo_instance, session, engine = _repo(tmp_path, "same_name_position_diff_versions.sqlite3")
    template = _template()
    datatype, datatype_version = _store_datatype_version(session, name="hostname")
    try:
        session.add(
            ObjectTemplateRow(
                id=str(template.id),
                namespace=template.namespace,
                name=template.name,
                description=template.description,
                abstract=template.abstract,
            )
        )
        session.add_all(
            [
                ObjectTemplateVersionRow(
                    template_id=str(template.id),
                    version=1,
                    status=ObjectTemplateVersionStatus.DRAFT.value,
                    parent_template_id=None,
                    parent_version=None,
                ),
                ObjectTemplateVersionRow(
                    template_id=str(template.id),
                    version=2,
                    status=ObjectTemplateVersionStatus.DRAFT.value,
                    parent_template_id=None,
                    parent_version=None,
                ),
            ]
        )
        session.flush()
        session.add_all(
            [
                ObjectTemplatePropertyRow(
                    template_id=str(template.id),
                    template_version=1,
                    position=0,
                    name="hostname",
                    datatype_id=str(datatype.id),
                    datatype_version=datatype_version.version,
                    required=True,
                ),
                ObjectTemplatePropertyRow(
                    template_id=str(template.id),
                    template_version=2,
                    position=0,
                    name="hostname",
                    datatype_id=str(datatype.id),
                    datatype_version=datatype_version.version,
                    required=False,
                ),
            ]
        )
        session.flush()
    finally:
        session.close()
        engine.dispose()


def test_duplicate_component_name_in_same_version_is_rejected_by_db(tmp_path: Path) -> None:
    _repo_instance, session, engine = _repo(tmp_path, "dup_component_name.sqlite3")
    template = _template()
    target = _store_template_identity(session, name="interface")
    try:
        session.add(
            ObjectTemplateRow(
                id=str(template.id),
                namespace=template.namespace,
                name=template.name,
                description=template.description,
                abstract=template.abstract,
            )
        )
        session.add(
            ObjectTemplateVersionRow(
                template_id=str(template.id),
                version=1,
                status=ObjectTemplateVersionStatus.DRAFT.value,
                parent_template_id=None,
                parent_version=None,
            )
        )
        session.flush()
        session.add_all(
            [
                ObjectTemplateComponentRow(
                    template_id=str(template.id),
                    template_version=1,
                    position=0,
                    name="interfaces",
                    target_template_id=str(target.id),
                ),
                ObjectTemplateComponentRow(
                    template_id=str(template.id),
                    template_version=1,
                    position=1,
                    name="interfaces",
                    target_template_id=str(target.id),
                ),
            ]
        )
        with pytest.raises(IntegrityError):
            session.flush()
    finally:
        session.close()
        engine.dispose()


def test_duplicate_component_position_in_same_version_is_rejected_by_db(tmp_path: Path) -> None:
    _repo_instance, session, engine = _repo(tmp_path, "dup_component_position.sqlite3")
    template = _template()
    first_target = _store_template_identity(session, name="interface")
    second_target = _store_template_identity(session, name="module")
    try:
        session.add(
            ObjectTemplateRow(
                id=str(template.id),
                namespace=template.namespace,
                name=template.name,
                description=template.description,
                abstract=template.abstract,
            )
        )
        session.add(
            ObjectTemplateVersionRow(
                template_id=str(template.id),
                version=1,
                status=ObjectTemplateVersionStatus.DRAFT.value,
                parent_template_id=None,
                parent_version=None,
            )
        )
        session.flush()
        session.add_all(
            [
                ObjectTemplateComponentRow(
                    template_id=str(template.id),
                    template_version=1,
                    position=0,
                    name="interfaces",
                    target_template_id=str(first_target.id),
                ),
                ObjectTemplateComponentRow(
                    template_id=str(template.id),
                    template_version=1,
                    position=0,
                    name="modules",
                    target_template_id=str(second_target.id),
                ),
            ]
        )
        with pytest.raises(IntegrityError):
            session.flush()
    finally:
        session.close()
        engine.dispose()


def test_same_component_name_and_position_in_different_versions_are_allowed(
    tmp_path: Path,
) -> None:
    _repo_instance, session, engine = _repo(
        tmp_path,
        "same_component_name_position_diff_versions.sqlite3",
    )
    template = _template()
    target = _store_template_identity(session, name="interface")
    try:
        session.add(
            ObjectTemplateRow(
                id=str(template.id),
                namespace=template.namespace,
                name=template.name,
                description=template.description,
                abstract=template.abstract,
            )
        )
        session.add_all(
            [
                ObjectTemplateVersionRow(
                    template_id=str(template.id),
                    version=1,
                    status=ObjectTemplateVersionStatus.DRAFT.value,
                    parent_template_id=None,
                    parent_version=None,
                ),
                ObjectTemplateVersionRow(
                    template_id=str(template.id),
                    version=2,
                    status=ObjectTemplateVersionStatus.DRAFT.value,
                    parent_template_id=None,
                    parent_version=None,
                ),
            ]
        )
        session.flush()
        session.add_all(
            [
                ObjectTemplateComponentRow(
                    template_id=str(template.id),
                    template_version=1,
                    position=0,
                    name="interfaces",
                    target_template_id=str(target.id),
                ),
                ObjectTemplateComponentRow(
                    template_id=str(template.id),
                    template_version=2,
                    position=0,
                    name="interfaces",
                    target_template_id=str(target.id),
                ),
            ]
        )
        session.flush()
    finally:
        session.close()
        engine.dispose()


def test_replace_version_exactly_replaces_owned_property_rows_and_positions(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "replace_property_rows.sqlite3")
    template = _template()
    hostname_datatype, hostname_v1 = _store_datatype_version(session, name="hostname")
    serial_datatype, serial_v1 = _store_datatype_version(session, name="serial")
    model_datatype, model_v1 = _store_datatype_version(session, name="model")
    original = _version(
        template.id,
        1,
        properties=(
            _property(
                "hostname",
                datatype_id=hostname_datatype.id,
                datatype_version=hostname_v1.version,
            ),
            _property(
                "serial",
                datatype_id=serial_datatype.id,
                datatype_version=serial_v1.version,
            ),
        ),
    )
    replacement = _version(
        template.id,
        1,
        properties=(
            _property(
                "hostname",
                datatype_id=hostname_datatype.id,
                datatype_version=hostname_v1.version,
            ),
            _property(
                "model",
                datatype_id=model_datatype.id,
                datatype_version=model_v1.version,
            ),
        ),
    )
    try:
        repo.add(template)
        repo.add_version(original)
        repo.replace_version(replacement)

        rows = session.scalars(
            select(ObjectTemplatePropertyRow)
            .where(
                ObjectTemplatePropertyRow.template_id == str(template.id),
                ObjectTemplatePropertyRow.template_version == 1,
            )
            .order_by(ObjectTemplatePropertyRow.position.asc())
        ).all()
        assert [(row.name, row.position) for row in rows] == [("hostname", 0), ("model", 1)]
    finally:
        session.close()
        engine.dispose()


def test_owner_cascade_removes_property_rows_when_exact_version_deleted(tmp_path: Path) -> None:
    _repo_instance, session, engine = _repo(tmp_path, "owner_cascade_version.sqlite3")
    template = _template()
    datatype, datatype_version = _store_datatype_version(session, name="hostname")
    try:
        session.add(
            ObjectTemplateRow(
                id=str(template.id),
                namespace=template.namespace,
                name=template.name,
                description=template.description,
                abstract=template.abstract,
            )
        )
        session.add(
            ObjectTemplateVersionRow(
                template_id=str(template.id),
                version=1,
                status=ObjectTemplateVersionStatus.DRAFT.value,
                parent_template_id=None,
                parent_version=None,
            )
        )
        session.flush()
        session.add_all(
            [
                ObjectTemplatePropertyRow(
                    template_id=str(template.id),
                    template_version=1,
                    position=0,
                    name="hostname",
                    datatype_id=str(datatype.id),
                    datatype_version=datatype_version.version,
                    required=True,
                ),
                ObjectTemplatePropertyRow(
                    template_id=str(template.id),
                    template_version=1,
                    position=1,
                    name="serial",
                    datatype_id=str(datatype.id),
                    datatype_version=datatype_version.version,
                    required=False,
                ),
            ]
        )
        session.commit()

        session.execute(
            delete(ObjectTemplateVersionRow).where(
                ObjectTemplateVersionRow.template_id == str(template.id),
                ObjectTemplateVersionRow.version == 1,
            )
        )
        session.flush()

        remaining = session.execute(
            text(
                "SELECT COUNT(*) FROM object_template_properties "
                "WHERE template_id = :template_id AND template_version = :template_version"
            ),
            {"template_id": str(template.id), "template_version": 1},
        ).scalar_one()
        assert remaining == 0
    finally:
        session.close()
        engine.dispose()


def test_whole_template_delete_leaves_no_orphan_property_rows(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "owner_cascade_identity.sqlite3")
    template = _template()
    datatype, datatype_version = _store_datatype_version(session, name="hostname")
    version = _version(
        template.id,
        1,
        properties=(
            _property(
                "hostname",
                datatype_id=datatype.id,
                datatype_version=datatype_version.version,
            ),
            _property(
                "serial",
                datatype_id=datatype.id,
                datatype_version=datatype_version.version,
            ),
        ),
    )
    try:
        repo.add(template)
        repo.add_version(version)
        repo.delete(template.id)
        remaining = session.execute(
            text(
                "SELECT COUNT(*) FROM object_template_properties "
                "WHERE template_id = :template_id"
            ),
            {"template_id": str(template.id)},
        ).scalar_one()
        assert remaining == 0
    finally:
        session.close()
        engine.dispose()


def test_raw_delete_of_component_target_identity_hits_fk_restrict(tmp_path: Path) -> None:
    _repo_instance, session, engine = _repo(tmp_path, "component_target_fk_restrict.sqlite3")
    owner = _template(name="device")
    target = _store_template_identity(session, name="interface")
    try:
        session.add(
            ObjectTemplateRow(
                id=str(owner.id),
                namespace=owner.namespace,
                name=owner.name,
                description=owner.description,
                abstract=owner.abstract,
            )
        )
        session.add(
            ObjectTemplateVersionRow(
                template_id=str(owner.id),
                version=1,
                status=ObjectTemplateVersionStatus.DRAFT.value,
                parent_template_id=None,
                parent_version=None,
            )
        )
        session.flush()
        session.add(
            ObjectTemplateComponentRow(
                template_id=str(owner.id),
                template_version=1,
                position=0,
                name="interfaces",
                target_template_id=str(target.id),
            )
        )
        session.commit()

        with pytest.raises(IntegrityError):
            session.execute(
                delete(ObjectTemplateRow).where(ObjectTemplateRow.id == str(target.id))
            )
            session.commit()
    finally:
        session.close()
        engine.dispose()


def test_owner_cascade_removes_component_rows_when_exact_version_deleted(tmp_path: Path) -> None:
    _repo_instance, session, engine = _repo(tmp_path, "component_owner_cascade_version.sqlite3")
    owner = _template(name="device")
    first_target = _store_template_identity(session, name="interface")
    second_target = _store_template_identity(session, name="module")
    try:
        session.add(
            ObjectTemplateRow(
                id=str(owner.id),
                namespace=owner.namespace,
                name=owner.name,
                description=owner.description,
                abstract=owner.abstract,
            )
        )
        session.add(
            ObjectTemplateVersionRow(
                template_id=str(owner.id),
                version=1,
                status=ObjectTemplateVersionStatus.DRAFT.value,
                parent_template_id=None,
                parent_version=None,
            )
        )
        session.flush()
        session.add_all(
            [
                ObjectTemplateComponentRow(
                    template_id=str(owner.id),
                    template_version=1,
                    position=0,
                    name="interfaces",
                    target_template_id=str(first_target.id),
                ),
                ObjectTemplateComponentRow(
                    template_id=str(owner.id),
                    template_version=1,
                    position=1,
                    name="modules",
                    target_template_id=str(second_target.id),
                ),
            ]
        )
        session.commit()

        session.execute(
            delete(ObjectTemplateVersionRow).where(
                ObjectTemplateVersionRow.template_id == str(owner.id),
                ObjectTemplateVersionRow.version == 1,
            )
        )
        session.flush()

        remaining = session.execute(
            text(
                "SELECT COUNT(*) FROM object_template_components "
                "WHERE template_id = :template_id AND template_version = :template_version"
            ),
            {"template_id": str(owner.id), "template_version": 1},
        ).scalar_one()
        assert remaining == 0
    finally:
        session.close()
        engine.dispose()


def test_whole_template_delete_leaves_no_orphan_component_rows(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "component_owner_cascade_identity.sqlite3")
    owner = _template(name="device")
    first_target = _store_template_identity(session, name="interface")
    second_target = _store_template_identity(session, name="module")
    version = _version(
        owner.id,
        1,
        components=(
            _component("interfaces", template_id=first_target.id),
            _component("modules", template_id=second_target.id),
        ),
    )
    try:
        repo.add(owner)
        repo.add_version(version)
        repo.delete(owner.id)
        remaining = session.execute(
            text(
                "SELECT COUNT(*) FROM object_template_components "
                "WHERE template_id = :template_id"
            ),
            {"template_id": str(owner.id)},
        ).scalar_one()
        assert remaining == 0
    finally:
        session.close()
        engine.dispose()


def test_delete_allows_self_owned_component_reference_rows_to_disappear_with_owner(
    tmp_path: Path,
) -> None:
    repo, session, engine = _repo(tmp_path, "self_owned_component_delete.sqlite3")
    owner = _template(name="device")
    version = _version(
        owner.id,
        1,
        components=(_component("self_slot", template_id=owner.id),),
    )
    try:
        repo.add(owner)
        repo.add_version(version)
        repo.delete(owner.id)
        assert repo.get(owner.id) is None
        remaining = session.execute(
            text(
                "SELECT COUNT(*) FROM object_template_components "
                "WHERE template_id = :template_id OR target_template_id = :template_id"
            ),
            {"template_id": str(owner.id)},
        ).scalar_one()
        assert remaining == 0
    finally:
        session.close()
        engine.dispose()
