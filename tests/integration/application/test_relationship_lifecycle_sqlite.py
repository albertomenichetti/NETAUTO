from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import sessionmaker

from netauto.application.object import ObjectApplicationService
from netauto.application.relationship import (
    RelationshipApplicationService,
    RelationshipDefinitionApplicationService,
)
from netauto.core.object import ComponentMembership, Object, ObjectNotFound
from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateVersion,
    ObjectTemplateVersionStatus,
)
from netauto.core.relationship import (
    RelationshipDefinitionInUse,
    RelationshipDefinitionNotFound,
    RelationshipNotFound,
)
from netauto.persistence.sqlalchemy.database import create_schema, create_sqlite_engine
from netauto.persistence.sqlalchemy.unit_of_work import (
    SqlAlchemyUnitOfWork,
    SqliteModelWriteUnitOfWork,
)


def _template(*, name: str) -> ObjectTemplate:
    return ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name=name,
        description=f"{name} template",
        abstract=False,
    )


def _version(template_id: UUID, *, version: int = 1) -> ObjectTemplateVersion:
    return ObjectTemplateVersion(
        template_id=template_id,
        version=version,
        status=ObjectTemplateVersionStatus.PUBLISHED,
    )


def _object(*, template_id: UUID, template_version: int = 1) -> Object:
    return Object(
        id=uuid4(),
        template_id=template_id,
        template_version=template_version,
        properties={},
    )


def _membership(parent_object_id: UUID, child_object_id: UUID) -> ComponentMembership:
    return ComponentMembership(
        parent_object_id=parent_object_id,
        slot_name="children",
        child_object_id=child_object_id,
    )


def test_object_deletion_cleans_up_incident_relationships_before_fk_restrict(
    tmp_path: Path,
) -> None:
    engine = create_sqlite_engine(
        f"sqlite:///{tmp_path / 'relationship-object-lifecycle.sqlite3'}"
    )
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)

    def uow_factory() -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(session_factory)

    object_service = ObjectApplicationService(uow_factory)
    definition_service = RelationshipDefinitionApplicationService(
        uow_factory,
        model_write_uow_factory=lambda: SqliteModelWriteUnitOfWork(session_factory),
    )
    relationship_service = RelationshipApplicationService(uow_factory)

    node = _template(name="node")
    try:
        with uow_factory() as uow:
            uow.object_templates.add(node)
            uow.object_templates.add_version(_version(node.id))

            parent = _object(template_id=node.id)
            child = _object(template_id=node.id)
            grandchild = _object(template_id=node.id)
            external = _object(template_id=node.id)
            unrelated_a = _object(template_id=node.id)
            unrelated_b = _object(template_id=node.id)

            for object_value in (
                parent,
                child,
                grandchild,
                external,
                unrelated_a,
                unrelated_b,
            ):
                uow.objects.add(object_value)
            uow.objects.add_membership(_membership(parent.id, child.id))
            uow.objects.add_membership(_membership(child.id, grandchild.id))
            uow.commit()

        definition = definition_service.create_relationship_definition(
            source_template_id=node.id,
            target_template_id=node.id,
            forward_name="connects_to",
            reverse_name="connects_to",
        )
        external_to_parent = relationship_service.create_relationship(
            relationship_definition_id=definition.id,
            source_object_id=external.id,
            target_object_id=parent.id,
        )
        child_to_external = relationship_service.create_relationship(
            relationship_definition_id=definition.id,
            source_object_id=child.id,
            target_object_id=external.id,
        )
        child_to_grandchild = relationship_service.create_relationship(
            relationship_definition_id=definition.id,
            source_object_id=child.id,
            target_object_id=grandchild.id,
        )
        unrelated = relationship_service.create_relationship(
            relationship_definition_id=definition.id,
            source_object_id=unrelated_a.id,
            target_object_id=unrelated_b.id,
        )

        object_service.delete_object(parent.id)

        with pytest.raises(ObjectNotFound):
            object_service.get_object(parent.id)
        with pytest.raises(ObjectNotFound):
            object_service.get_object(child.id)
        with pytest.raises(ObjectNotFound):
            object_service.get_object(grandchild.id)

        assert object_service.get_object(external.id) == external
        assert object_service.get_object(unrelated_a.id) == unrelated_a
        assert object_service.get_object(unrelated_b.id) == unrelated_b

        assert relationship_service.list_relationships() == (unrelated,)
        with pytest.raises(RelationshipNotFound):
            relationship_service.get_relationship(external_to_parent.id)
        with pytest.raises(RelationshipNotFound):
            relationship_service.get_relationship(child_to_external.id)
        with pytest.raises(RelationshipNotFound):
            relationship_service.get_relationship(child_to_grandchild.id)
        assert relationship_service.get_relationship(unrelated.id) == unrelated
    finally:
        engine.dispose()


def test_relationship_definition_delete_is_restrictive_while_runtime_edges_exist(
    tmp_path: Path,
) -> None:
    engine = create_sqlite_engine(
        f"sqlite:///{tmp_path / 'relationship-definition-lifecycle.sqlite3'}"
    )
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)

    def uow_factory() -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(session_factory)

    definition_service = RelationshipDefinitionApplicationService(
        uow_factory,
        model_write_uow_factory=lambda: SqliteModelWriteUnitOfWork(session_factory),
    )
    relationship_service = RelationshipApplicationService(uow_factory)

    node = _template(name="node")
    try:
        with uow_factory() as uow:
            uow.object_templates.add(node)
            uow.object_templates.add_version(_version(node.id))
            source = _object(template_id=node.id)
            target = _object(template_id=node.id)
            uow.objects.add(source)
            uow.objects.add(target)
            uow.commit()

        definition = definition_service.create_relationship_definition(
            source_template_id=node.id,
            target_template_id=node.id,
            forward_name="connects_to",
            reverse_name="connects_to",
        )
        relationship = relationship_service.create_relationship(
            relationship_definition_id=definition.id,
            source_object_id=source.id,
            target_object_id=target.id,
        )

        with pytest.raises(RelationshipDefinitionInUse):
            definition_service.delete_relationship_definition(definition.id)

        assert definition_service.get_relationship_definition(definition.id) == definition
        assert relationship_service.get_relationship(relationship.id) == relationship

        relationship_service.delete_relationship(relationship.id)
        definition_service.delete_relationship_definition(definition.id)

        with pytest.raises(RelationshipDefinitionNotFound):
            definition_service.get_relationship_definition(definition.id)
    finally:
        engine.dispose()
