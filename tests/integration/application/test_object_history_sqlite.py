from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import sessionmaker

from netauto.application.object import ObjectApplicationService
from netauto.core.datatype import (
    DataTypeFactory,
    DataTypeVersion,
    DataTypeVersioningService,
    DataTypeVersionStatus,
)
from netauto.core.object import Object, ObjectChange, ObjectChangeKind, ObjectNotFound
from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateProperty,
    ObjectTemplateVersion,
    ObjectTemplateVersionStatus,
)
from netauto.persistence.sqlalchemy.database import create_schema, create_sqlite_engine
from netauto.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork


def _template(*, name: str = "device") -> ObjectTemplate:
    return ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name=name,
        description=f"{name} template",
        abstract=False,
    )


def _version(
    template_id: UUID,
    *,
    version: int = 1,
    properties: tuple[ObjectTemplateProperty, ...] = (),
) -> ObjectTemplateVersion:
    return ObjectTemplateVersion(
        template_id=template_id,
        version=version,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        properties=properties,
    )


def _property(
    name: str,
    *,
    datatype_id: UUID,
    datatype_version: int,
    required: bool = False,
) -> ObjectTemplateProperty:
    return ObjectTemplateProperty(
        name=name,
        datatype_id=datatype_id,
        datatype_version=datatype_version,
        required=required,
    )


def _object(
    *,
    template_id: UUID,
    template_version: int = 1,
    properties: dict[str, object] | None = None,
) -> Object:
    return Object(
        id=uuid4(),
        template_id=template_id,
        template_version=template_version,
        properties=properties or {},
    )


def _persist_template_version(
    uow: SqlAlchemyUnitOfWork,
    version: ObjectTemplateVersion,
) -> None:
    draft = ObjectTemplateVersion(
        template_id=version.template_id,
        version=version.version,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=version.parent,
        properties=version.properties,
        components=version.components,
    )
    uow.object_templates.add_version(draft)
    if version.status is not ObjectTemplateVersionStatus.DRAFT:
        uow.object_templates.replace_version(version)


def test_object_history_survives_create_update_delete_and_rollback_is_atomic(
    tmp_path: Path,
) -> None:
    engine = create_sqlite_engine(f"sqlite:///{tmp_path / 'object-history.sqlite3'}")
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)

    def uow_factory() -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(session_factory)

    timestamps = iter(
        (
            datetime(2026, 8, 11, 12, 0, tzinfo=UTC),
            datetime(2026, 8, 11, 12, 1, tzinfo=UTC),
            datetime(2026, 8, 11, 12, 2, tzinfo=UTC),
        )
    )
    service = ObjectApplicationService(
        uow_factory,
        clock=lambda: next(timestamps),
    )

    hostname, hostname_v1 = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description="Hostname",
        base_type="core.string",
    )
    hostname_v1 = DataTypeVersioningService().publish(hostname_v1)
    template = _template()
    try:
        with uow_factory() as uow:
            uow.datatypes.add(hostname)
            uow.datatypes.add_version(
                DataTypeVersion(
                    datatype_id=hostname.id,
                    version=hostname_v1.version,
                    status=DataTypeVersionStatus.DRAFT,
                    base_type=hostname_v1.base_type,
                    constraints=hostname_v1.constraints,
                )
            )
            uow.datatypes.replace_version(hostname_v1)
            uow.object_templates.add(template)
            _persist_template_version(
                uow,
                _version(
                    template.id,
                    properties=(
                        _property(
                            "hostname",
                            datatype_id=hostname.id,
                            datatype_version=hostname_v1.version,
                            required=True,
                        ),
                    ),
                ),
            )
            uow.commit()

        created = service.create_object(
            template_id=template.id,
            template_version=1,
            properties={"hostname": "router-01"},
        )
        updated = service.update_object(
            object_id=created.id,
            properties={"hostname": "router-02"},
            remove_properties=(),
        )
        service.delete_object(created.id)

        history = service.list_object_history(created.id)
        assert [change.kind for change in history] == [
            ObjectChangeKind.CREATED,
            ObjectChangeKind.UPDATED,
            ObjectChangeKind.DELETED,
        ]
        assert history[0].after is not None
        assert history[0].after.properties == {"hostname": "router-01"}
        assert history[1].before is not None
        assert history[1].after is not None
        assert history[1].before.properties == {"hostname": "router-01"}
        assert history[1].after.properties == {"hostname": "router-02"}
        assert history[2].before is not None
        assert history[2].after is None
        assert history[2].before.properties == {"hostname": "router-02"}
        with pytest.raises(ObjectNotFound):
            service.get_object(created.id)
        assert updated.properties == {"hostname": "router-02"}

        rollback_object = _object(template_id=template.id, properties={"hostname": "rollback"})
        with pytest.raises(RuntimeError):
            with uow_factory() as uow:
                uow.objects.add(rollback_object)
                uow.object_changes.add(
                    ObjectChange(
                        id=uuid4(),
                        object_id=rollback_object.id,
                        occurred_at=datetime(2026, 8, 11, 12, 5, tzinfo=UTC),
                        kind=ObjectChangeKind.CREATED,
                        before=None,
                        after=history[0].after,
                    )
                )
                raise RuntimeError("abort")

        with uow_factory() as uow:
            assert uow.objects.get(rollback_object.id) is None
            assert uow.object_changes.list_by_object(rollback_object.id) == ()
    finally:
        engine.dispose()
