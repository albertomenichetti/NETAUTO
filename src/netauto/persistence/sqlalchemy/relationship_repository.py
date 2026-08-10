"""SQLAlchemy relationship definition repository implementation."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from netauto.core.relationship import (
    RelationshipDefinition,
    RelationshipDefinitionAlreadyExists,
    RelationshipDefinitionNotFound,
    RelationshipDefinitionPersistenceError,
    RelationshipDefinitionRepository,
)
from netauto.persistence.sqlalchemy.models import RelationshipDefinitionRow


def _row_to_relationship_definition(row: RelationshipDefinitionRow) -> RelationshipDefinition:
    try:
        return RelationshipDefinition(
            id=UUID(row.id),
            source_template_id=UUID(row.source_template_id),
            target_template_id=UUID(row.target_template_id),
            forward_name=row.forward_name,
            reverse_name=row.reverse_name,
        )
    except Exception as error:
        raise RelationshipDefinitionPersistenceError(
            "Stored relationship definition row is invalid."
        ) from error


class SqlAlchemyRelationshipDefinitionRepository(RelationshipDefinitionRepository):
    """SQLAlchemy-backed relationship definition repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list(self) -> tuple[RelationshipDefinition, ...]:
        rows = self._session.scalars(
            select(RelationshipDefinitionRow).order_by(RelationshipDefinitionRow.id.asc())
        ).all()
        return tuple(_row_to_relationship_definition(row) for row in rows)

    def add(self, definition: RelationshipDefinition) -> None:
        if self._session.get(RelationshipDefinitionRow, str(definition.id)) is not None:
            raise RelationshipDefinitionAlreadyExists(
                "RelationshipDefinition UUID already exists."
            )
        self._session.add(
            RelationshipDefinitionRow(
                id=str(definition.id),
                source_template_id=str(definition.source_template_id),
                target_template_id=str(definition.target_template_id),
                forward_name=definition.forward_name,
                reverse_name=definition.reverse_name,
            )
        )
        try:
            self._session.flush()
        except IntegrityError as error:
            raise RelationshipDefinitionPersistenceError(
                "RelationshipDefinition could not be persisted."
            ) from error

    def get(self, definition_id: UUID) -> RelationshipDefinition | None:
        row = self._session.get(RelationshipDefinitionRow, str(definition_id))
        if row is None:
            return None
        return _row_to_relationship_definition(row)

    def delete(self, definition_id: UUID) -> None:
        row = self._session.get(RelationshipDefinitionRow, str(definition_id))
        if row is None:
            raise RelationshipDefinitionNotFound("RelationshipDefinition does not exist.")
        self._session.delete(row)
        self._session.flush()
