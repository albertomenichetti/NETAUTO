from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy.orm import sessionmaker

from netauto.application.relationship import RelationshipApplicationService
from netauto.core.object import Object
from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateVersion,
    ObjectTemplateVersionRef,
    ObjectTemplateVersionStatus,
)
from netauto.core.relationship import (
    RelationshipAlreadyExists,
    RelationshipDefinition,
    RelationshipEndpointIncompatible,
    RelationshipNotFound,
)
from netauto.persistence.sqlalchemy.database import create_schema, create_sqlite_engine
from netauto.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork


def _template(*, name: str, abstract: bool = False) -> ObjectTemplate:
    return ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name=name,
        description=f"{name} template",
        abstract=abstract,
    )


def _version(
    template_id,
    *,
    version: int,
    status: ObjectTemplateVersionStatus = ObjectTemplateVersionStatus.PUBLISHED,
    parent: ObjectTemplateVersionRef | None = None,
) -> ObjectTemplateVersion:
    return ObjectTemplateVersion(
        template_id=template_id,
        version=version,
        status=status,
        parent=parent,
    )


def _object(*, template_id, template_version: int) -> Object:
    return Object(
        id=uuid4(),
        template_id=template_id,
        template_version=template_version,
        properties={},
    )


def _definition(*, source_template_id, target_template_id) -> RelationshipDefinition:
    return RelationshipDefinition(
        id=uuid4(),
        source_template_id=source_template_id,
        target_template_id=target_template_id,
        forward_name="uses",
        reverse_name="is_used_by",
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


def test_relationship_service_sqlite_vertical_flow(tmp_path: Path) -> None:
    engine = create_sqlite_engine(f"sqlite:///{tmp_path / 'relationship-service.sqlite3'}")
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)

    def uow_factory() -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(session_factory)

    service = RelationshipApplicationService(uow_factory)

    network_device = _template(name="network_device", abstract=True)
    router = _template(name="router")
    credential = _template(name="credential")
    other = _template(name="other")
    definition = _definition(
        source_template_id=network_device.id,
        target_template_id=credential.id,
    )
    other_definition = RelationshipDefinition(
        id=uuid4(),
        source_template_id=network_device.id,
        target_template_id=credential.id,
        forward_name="manages",
        reverse_name="managed_by",
    )
    router_object = _object(template_id=router.id, template_version=1)
    credential_object = _object(template_id=credential.id, template_version=1)
    other_object = _object(template_id=other.id, template_version=1)

    try:
        with uow_factory() as uow:
            for template in (network_device, router, credential, other):
                uow.object_templates.add(template)
            _persist_template_version(uow, _version(network_device.id, version=1))
            _persist_template_version(
                uow,
                _version(
                    router.id,
                    version=1,
                    parent=ObjectTemplateVersionRef(template_id=network_device.id, version=1),
                )
            )
            _persist_template_version(uow, _version(credential.id, version=1))
            _persist_template_version(uow, _version(other.id, version=1))
            uow.relationship_definitions.add(definition)
            uow.relationship_definitions.add(other_definition)
            uow.objects.add(router_object)
            uow.objects.add(credential_object)
            uow.objects.add(other_object)
            uow.commit()

        created = service.create_relationship(
            relationship_definition_id=definition.id,
            source_object_id=router_object.id,
            target_object_id=credential_object.id,
        )
        assert service.get_relationship(created.id) == created
        assert service.list_relationships() == (created,)

        with pytest.raises(RelationshipAlreadyExists):
            service.create_relationship(
                relationship_definition_id=definition.id,
                source_object_id=router_object.id,
                target_object_id=credential_object.id,
            )

        second = service.create_relationship(
            relationship_definition_id=other_definition.id,
            source_object_id=router_object.id,
            target_object_id=credential_object.id,
        )
        listed = service.list_relationships()
        assert listed == tuple(sorted((created, second), key=lambda item: str(item.id)))

        with pytest.raises(RelationshipEndpointIncompatible):
            service.create_relationship(
                relationship_definition_id=definition.id,
                source_object_id=other_object.id,
                target_object_id=credential_object.id,
            )

        service.delete_relationship(created.id)

        assert service.get_relationship(second.id) == second
        with pytest.raises(RelationshipNotFound):
            service.get_relationship(created.id)
    finally:
        engine.dispose()
