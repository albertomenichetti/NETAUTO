from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import Session

from netauto.core.object import Object
from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateVersion,
    ObjectTemplateVersionStatus,
)
from netauto.core.relationship import (
    Relationship,
    RelationshipDefinition,
    RelationshipDefinitionAlreadyExists,
    RelationshipDefinitionNotFound,
    RelationshipDefinitionPersistenceError,
)
from netauto.persistence.sqlalchemy.object_repository import SqlAlchemyObjectRepository
from netauto.persistence.sqlalchemy.objecttemplate_repository import (
    SqlAlchemyObjectTemplateRepository,
)
from netauto.persistence.sqlalchemy.relationship_repository import (
    SqlAlchemyRelationshipDefinitionRepository,
    SqlAlchemyRelationshipRepository,
)

pytestmark = pytest.mark.postgresql


def _definition(
    *,
    definition_id: UUID | None = None,
    source_template_id: UUID,
    target_template_id: UUID,
    forward_name: str = "uses",
    reverse_name: str = "used_by",
) -> RelationshipDefinition:
    return RelationshipDefinition(
        id=definition_id or uuid4(),
        source_template_id=source_template_id,
        target_template_id=target_template_id,
        forward_name=forward_name,
        reverse_name=reverse_name,
    )


def _store_template(
    repo: SqlAlchemyObjectTemplateRepository,
    *,
    template_id: UUID | None = None,
    namespace: str = "network",
    name: str = "device",
) -> UUID:
    template = ObjectTemplate(
        id=template_id or uuid4(),
        namespace=namespace,
        name=name,
        description=None,
        abstract=False,
    )
    repo.add(template)
    repo.add_version(
        ObjectTemplateVersion(
            template_id=template.id,
            version=1,
            status=ObjectTemplateVersionStatus.DRAFT,
            properties=(),
        )
    )
    return template.id


def _store_object(
    repo: SqlAlchemyObjectRepository,
    *,
    template_id: UUID,
    object_id: UUID | None = None,
) -> Object:
    object_value = Object(
        id=object_id or uuid4(),
        template_id=template_id,
        template_version=1,
        properties={},
    )
    repo.add(object_value)
    return object_value


def test_postgresql_relationship_definition_list_add_get_round_trip(
    postgresql_model_session: Session,
) -> None:
    template_repo = SqlAlchemyObjectTemplateRepository(postgresql_model_session)
    repo = SqlAlchemyRelationshipDefinitionRepository(postgresql_model_session)
    low_source = _store_template(
        template_repo,
        template_id=UUID("00000000-0000-0000-0000-0000000000a1"),
        namespace="network",
        name="source_low",
    )
    low_target = _store_template(
        template_repo,
        template_id=UUID("00000000-0000-0000-0000-0000000000a2"),
        namespace="network",
        name="target_low",
    )
    high_source = _store_template(
        template_repo,
        template_id=UUID("00000000-0000-0000-0000-0000000000a3"),
        namespace="network",
        name="source_high",
    )
    high_target = _store_template(
        template_repo,
        template_id=UUID("00000000-0000-0000-0000-0000000000a4"),
        namespace="network",
        name="target_high",
    )
    low = _definition(
        definition_id=UUID("00000000-0000-0000-0000-000000000001"),
        source_template_id=low_source,
        target_template_id=low_target,
        forward_name="uses",
        reverse_name="used_by",
    )
    high = _definition(
        definition_id=UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"),
        source_template_id=high_source,
        target_template_id=high_target,
        forward_name="manages",
        reverse_name="managed_by",
    )

    assert repo.list() == ()

    repo.add(high)
    repo.add(low)

    assert repo.get(low.id) == low
    assert repo.get(uuid4()) is None
    assert repo.list() == (low, high)
    loaded = repo.get(high.id)
    assert loaded is not None
    assert isinstance(loaded.id, UUID)


def test_postgresql_relationship_definition_fk_parity_and_recovery(
    postgresql_model_session: Session,
) -> None:
    template_repo = SqlAlchemyObjectTemplateRepository(postgresql_model_session)
    repo = SqlAlchemyRelationshipDefinitionRepository(postgresql_model_session)
    valid_source = _store_template(template_repo, name="valid_source")
    valid_target = _store_template(template_repo, name="valid_target")
    valid = _definition(source_template_id=valid_source, target_template_id=valid_target)

    repo.add(valid)
    postgresql_model_session.commit()

    with postgresql_model_session.begin_nested():
        with pytest.raises(RelationshipDefinitionPersistenceError):
            repo.add(
                _definition(
                    source_template_id=uuid4(),
                    target_template_id=valid_target,
                    forward_name="links_to",
                    reverse_name="linked_from",
                )
            )

    with postgresql_model_session.begin_nested():
        with pytest.raises(RelationshipDefinitionPersistenceError):
            repo.add(
                _definition(
                    source_template_id=valid_source,
                    target_template_id=uuid4(),
                    forward_name="depends_on",
                    reverse_name="dependency_of",
                )
            )

    assert repo.get(valid.id) == valid


def test_postgresql_relationship_definition_duplicate_and_delete_contracts(
    postgresql_model_session: Session,
) -> None:
    template_repo = SqlAlchemyObjectTemplateRepository(postgresql_model_session)
    definition_repo = SqlAlchemyRelationshipDefinitionRepository(postgresql_model_session)
    relationship_repo = SqlAlchemyRelationshipRepository(postgresql_model_session)
    object_repo = SqlAlchemyObjectRepository(postgresql_model_session)

    source_template_id = _store_template(
        template_repo,
        template_id=UUID("00000000-0000-0000-0000-0000000000b1"),
        name="source",
    )
    target_template_id = _store_template(
        template_repo,
        template_id=UUID("00000000-0000-0000-0000-0000000000b2"),
        name="target",
    )
    definition = _definition(
        definition_id=UUID("11111111-1111-1111-1111-111111111111"),
        source_template_id=source_template_id,
        target_template_id=target_template_id,
    )
    duplicate = _definition(
        definition_id=definition.id,
        source_template_id=target_template_id,
        target_template_id=source_template_id,
        forward_name="manages",
        reverse_name="managed_by",
    )

    definition_repo.add(definition)
    postgresql_model_session.commit()

    with pytest.raises(RelationshipDefinitionAlreadyExists):
        definition_repo.add(duplicate)
    postgresql_model_session.rollback()

    with pytest.raises(RelationshipDefinitionNotFound):
        definition_repo.delete(uuid4())

    source_object = _store_object(object_repo, template_id=source_template_id)
    target_object = _store_object(object_repo, template_id=target_template_id)
    relationship = Relationship(
        id=uuid4(),
        relationship_definition_id=definition.id,
        source_object_id=source_object.id,
        target_object_id=target_object.id,
    )
    relationship_repo.add(relationship)
    postgresql_model_session.commit()

    with postgresql_model_session.begin_nested():
        with pytest.raises(RelationshipDefinitionPersistenceError):
            definition_repo.delete(definition.id)

    assert definition_repo.get(definition.id) == definition
    assert relationship_repo.get(relationship.id) == relationship

    relationship_repo.delete(relationship.id)
    definition_repo.delete(definition.id)

    assert relationship_repo.get(relationship.id) is None
    assert definition_repo.get(definition.id) is None
