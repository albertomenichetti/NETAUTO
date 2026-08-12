from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from netauto.core.datatype import (
    Constraint,
    ConstraintName,
    DataType,
    DataTypeAlreadyExists,
    DataTypeFactory,
    DataTypeNotFound,
    DataTypePersistenceError,
    DataTypeVersion,
    DataTypeVersionAlreadyExists,
    DataTypeVersioningService,
    DataTypeVersionNotFound,
    DataTypeVersionStatus,
    PrimitiveTypeRegistry,
)
from netauto.persistence.sqlalchemy.datatype_repository import SqlAlchemyDataTypeRepository
from netauto.persistence.sqlalchemy.models import (
    ObjectTemplatePropertyRow,
    ObjectTemplateRow,
    ObjectTemplateVersionRow,
)

pytestmark = pytest.mark.postgresql


def test_postgresql_datatype_identity_round_trip_and_ordering(
    postgresql_model_session: Session,
) -> None:
    repo = SqlAlchemyDataTypeRepository(postgresql_model_session)
    zeta, _ = DataTypeFactory().create(
        namespace="zeta",
        name="beta",
        description=None,
        base_type="core.string",
    )
    hostname, _ = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description="Network hostname",
        base_type="core.string",
    )
    vlan, _ = DataTypeFactory().create(
        namespace="network",
        name="vlan_id",
        description=None,
        base_type="core.integer",
    )

    repo.add(zeta)
    repo.add(vlan)
    repo.add(hostname)

    listed = repo.list()
    loaded = repo.get(hostname.id)
    by_name = repo.get_by_name("network", "hostname")

    assert [(datatype.namespace, datatype.name) for datatype in listed] == [
        ("network", "hostname"),
        ("network", "vlan_id"),
        ("zeta", "beta"),
    ]
    assert loaded == hostname
    assert by_name == hostname
    assert isinstance(loaded.id, UUID)  # type: ignore[union-attr]
    assert repo.get(uuid4()) is None


def test_postgresql_datatype_identity_uniqueness_and_missing_delete(
    postgresql_model_session: Session,
) -> None:
    repo = SqlAlchemyDataTypeRepository(postgresql_model_session)
    datatype, _ = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description=None,
        base_type="core.string",
    )
    duplicate_id = DataType(
        id=datatype.id,
        namespace="asset",
        name="device_status",
        description="duplicate uuid",
    )
    duplicate_name = DataType(
        id=uuid4(),
        namespace=datatype.namespace,
        name=datatype.name,
        description="duplicate logical name",
    )

    repo.add(datatype)
    postgresql_model_session.commit()

    with pytest.raises(DataTypeAlreadyExists):
        repo.add(duplicate_id)
    postgresql_model_session.rollback()

    with pytest.raises(DataTypeAlreadyExists):
        repo.add(duplicate_name)
    postgresql_model_session.rollback()

    with pytest.raises(DataTypeNotFound):
        repo.delete(uuid4())

    assert repo.get(datatype.id) == datatype


def test_postgresql_datatype_version_round_trip_and_ordering_with_enum_constraints(
    postgresql_model_session: Session,
) -> None:
    repo = SqlAlchemyDataTypeRepository(postgresql_model_session)
    datatype, v1 = DataTypeFactory().create(
        namespace="asset",
        name="device_status",
        description="Lifecycle state",
        base_type="core.string",
        constraints=(
            Constraint(
                name=ConstraintName.ENUM,
                value=("active", "planned", "retired"),
            ),
        ),
    )
    service = DataTypeVersioningService()
    v1_published = service.publish(v1)
    v2 = service.create_next_version(v1_published, existing_versions=(v1_published,))
    v5 = DataTypeVersion(
        datatype_id=datatype.id,
        version=5,
        status=DataTypeVersionStatus.DRAFT,
        base_type=v1.base_type,
        constraints=v1.constraints,
    )

    repo.add(datatype)
    repo.add_version(v1)
    repo.replace_version(v1_published)
    repo.add_version(v5)
    repo.add_version(v2)

    loaded = repo.get_version(datatype.id, 1)
    listed = repo.list_versions(datatype.id)

    assert loaded == v1_published
    assert loaded is not None
    assert loaded.base_type is PrimitiveTypeRegistry().get("core.string")
    assert loaded.constraints == v1.constraints
    assert tuple(version.version for version in listed) == (1, 2, 5)


def test_postgresql_datatype_version_errors_translate_and_recover(
    postgresql_model_session: Session,
) -> None:
    repo = SqlAlchemyDataTypeRepository(postgresql_model_session)
    datatype, draft = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description=None,
        base_type="core.string",
        constraints=(
            Constraint(name=ConstraintName.MIN_LENGTH, value=1),
            Constraint(name=ConstraintName.MAX_LENGTH, value=253),
        ),
    )

    with pytest.raises(DataTypeNotFound):
        repo.add_version(draft)

    repo.add(datatype)
    repo.add_version(draft)
    postgresql_model_session.commit()

    with pytest.raises(DataTypeVersionAlreadyExists):
        repo.add_version(draft)
    postgresql_model_session.rollback()

    assert repo.get_version(datatype.id, 999) is None

    missing_version = DataTypeVersion(
        datatype_id=datatype.id,
        version=99,
        status=DataTypeVersionStatus.DRAFT,
        base_type=draft.base_type,
        constraints=draft.constraints,
    )
    with pytest.raises(DataTypeVersionNotFound):
        repo.replace_version(missing_version)

    assert repo.get_version(datatype.id, 1) == draft


def test_postgresql_datatype_replace_version_lifecycle_parity(
    postgresql_model_session: Session,
) -> None:
    repo = SqlAlchemyDataTypeRepository(postgresql_model_session)
    datatype, draft = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description=None,
        base_type="core.string",
        constraints=(
            Constraint(name=ConstraintName.MIN_LENGTH, value=1),
            Constraint(name=ConstraintName.MAX_LENGTH, value=253),
        ),
    )
    service = DataTypeVersioningService()
    revised = service.revise_draft(
        draft,
        constraints=(
            Constraint(name=ConstraintName.MIN_LENGTH, value=2),
            Constraint(name=ConstraintName.MAX_LENGTH, value=64),
        ),
    )
    published = service.publish(revised)
    deprecated = service.deprecate(published)

    repo.add(datatype)
    repo.add_version(draft)
    repo.replace_version(revised)
    assert repo.get_version(datatype.id, 1) == revised

    repo.replace_version(published)
    assert repo.get_version(datatype.id, 1) == published

    illegal_publish = DataTypeVersion(
        datatype_id=published.datatype_id,
        version=published.version,
        status=DataTypeVersionStatus.PUBLISHED,
        base_type=published.base_type,
        constraints=(Constraint(name=ConstraintName.MIN_LENGTH, value=3),),
    )
    with postgresql_model_session.begin_nested():
        with pytest.raises(DataTypePersistenceError):
            repo.replace_version(illegal_publish)

    assert repo.get_version(datatype.id, 1) == published

    repo.replace_version(deprecated)
    assert repo.get_version(datatype.id, 1) == deprecated


def test_postgresql_datatype_delete_removes_identity_and_versions(
    postgresql_model_session: Session,
) -> None:
    repo = SqlAlchemyDataTypeRepository(postgresql_model_session)
    first, v1 = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description=None,
        base_type="core.string",
    )
    second, v2 = DataTypeFactory().create(
        namespace="network",
        name="vlan_id",
        description=None,
        base_type="core.integer",
    )
    service = DataTypeVersioningService()
    v1_published = service.publish(v1)
    v1_next = service.create_next_version(v1_published, existing_versions=(v1_published,))

    repo.add(first)
    repo.add_version(v1)
    repo.replace_version(v1_published)
    repo.add_version(v1_next)
    repo.add(second)
    repo.add_version(v2)

    repo.delete(first.id)

    assert repo.get(first.id) is None
    assert repo.get_by_name(first.namespace, first.name) is None
    assert repo.list_versions(first.id) == ()
    assert repo.get(second.id) == second
    assert repo.list_versions(second.id) == (v2,)


def test_postgresql_datatype_delete_blocked_by_exact_version_property_reference(
    postgresql_model_session: Session,
) -> None:
    repo = SqlAlchemyDataTypeRepository(postgresql_model_session)
    datatype, version = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description=None,
        base_type="core.string",
    )

    repo.add(datatype)
    repo.add_version(version)
    postgresql_model_session.commit()

    template_id = str(uuid4())
    postgresql_model_session.add(
        ObjectTemplateRow(
            id=template_id,
            namespace="network",
            name="device_template",
            description=None,
            abstract=False,
        )
    )
    postgresql_model_session.add(
        ObjectTemplateVersionRow(
            template_id=template_id,
            version=1,
            status="draft",
            parent_template_id=None,
            parent_version=None,
        )
    )
    postgresql_model_session.flush()
    postgresql_model_session.add(
        ObjectTemplatePropertyRow(
            template_id=template_id,
            template_version=1,
            position=0,
            name="hostname",
            datatype_id=str(datatype.id),
            datatype_version=version.version,
            required=True,
        )
    )
    postgresql_model_session.commit()

    with pytest.raises(DataTypePersistenceError, match="Datatype deletion failed."):
        repo.delete(datatype.id)
    postgresql_model_session.rollback()

    assert repo.get(datatype.id) == datatype
    assert repo.get_version(datatype.id, version.version) == version
    property_row = postgresql_model_session.scalar(
        select(ObjectTemplatePropertyRow).where(
            ObjectTemplatePropertyRow.template_id == template_id,
            ObjectTemplatePropertyRow.template_version == 1,
            ObjectTemplatePropertyRow.name == "hostname",
        )
    )
    assert property_row is not None
