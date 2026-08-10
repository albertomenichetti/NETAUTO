"""SQLAlchemy relationship repository implementations."""

from collections.abc import Collection
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from netauto.core.relationship import (
    Relationship,
    RelationshipAlreadyExists,
    RelationshipDefinition,
    RelationshipDefinitionAlreadyExists,
    RelationshipDefinitionNotFound,
    RelationshipDefinitionPersistenceError,
    RelationshipDefinitionRepository,
    RelationshipNotFound,
    RelationshipPersistenceError,
    RelationshipRepository,
)
from netauto.persistence.sqlalchemy.models import RelationshipDefinitionRow, RelationshipRow


def _is_duplicate_relationship_integrity_error(error: IntegrityError) -> bool:
    message = str(getattr(error, "orig", error))
    if "UNIQUE constraint failed: relationships.id" in message:
        return True
    if (
        "UNIQUE constraint failed: "
        "relationships.relationship_definition_id, "
        "relationships.source_object_id, "
        "relationships.target_object_id"
    ) in message:
        return True
    return False


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


def _row_to_relationship(row: RelationshipRow) -> Relationship:
    try:
        return Relationship(
            id=UUID(row.id),
            relationship_definition_id=UUID(row.relationship_definition_id),
            source_object_id=UUID(row.source_object_id),
            target_object_id=UUID(row.target_object_id),
        )
    except Exception as error:
        raise RelationshipPersistenceError("Stored relationship row is invalid.") from error


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


class SqlAlchemyRelationshipRepository(RelationshipRepository):
    """SQLAlchemy-backed runtime relationship repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list(self) -> tuple[Relationship, ...]:
        rows = self._session.scalars(
            select(RelationshipRow).order_by(RelationshipRow.id.asc())
        ).all()
        return tuple(_row_to_relationship(row) for row in rows)

    def get(self, relationship_id: UUID) -> Relationship | None:
        row = self._session.get(RelationshipRow, str(relationship_id))
        if row is None:
            return None
        return _row_to_relationship(row)

    def get_by_endpoints(
        self,
        relationship_definition_id: UUID,
        source_object_id: UUID,
        target_object_id: UUID,
    ) -> Relationship | None:
        row = self._session.scalar(
            select(RelationshipRow).where(
                RelationshipRow.relationship_definition_id
                == str(relationship_definition_id),
                RelationshipRow.source_object_id == str(source_object_id),
                RelationshipRow.target_object_id == str(target_object_id),
            )
        )
        if row is None:
            return None
        return _row_to_relationship(row)

    def add(self, relationship: Relationship) -> None:
        if self._session.get(RelationshipRow, str(relationship.id)) is not None:
            raise RelationshipAlreadyExists("Relationship already exists.")
        if (
            self.get_by_endpoints(
                relationship.relationship_definition_id,
                relationship.source_object_id,
                relationship.target_object_id,
            )
            is not None
        ):
            raise RelationshipAlreadyExists("Relationship already exists.")
        self._session.add(
            RelationshipRow(
                id=str(relationship.id),
                relationship_definition_id=str(relationship.relationship_definition_id),
                source_object_id=str(relationship.source_object_id),
                target_object_id=str(relationship.target_object_id),
            )
        )
        try:
            self._session.flush()
        except IntegrityError as error:
            if _is_duplicate_relationship_integrity_error(error):
                raise RelationshipAlreadyExists("Relationship already exists.") from error
            raise RelationshipPersistenceError("Relationship could not be persisted.") from error
        except Exception as error:
            raise RelationshipPersistenceError("Relationship could not be persisted.") from error

    def list_by_definition(
        self,
        relationship_definition_id: UUID,
    ) -> tuple[Relationship, ...]:
        rows = self._session.scalars(
            select(RelationshipRow)
            .where(RelationshipRow.relationship_definition_id == str(relationship_definition_id))
            .order_by(RelationshipRow.id.asc())
        ).all()
        return tuple(_row_to_relationship(row) for row in rows)

    def list_incident_to_objects(
        self,
        object_ids: Collection[UUID],
    ) -> tuple[Relationship, ...]:
        object_id_strings = sorted({str(object_id) for object_id in object_ids})
        if not object_id_strings:
            return ()
        rows = self._session.scalars(
            select(RelationshipRow)
            .where(
                or_(
                    RelationshipRow.source_object_id.in_(object_id_strings),
                    RelationshipRow.target_object_id.in_(object_id_strings),
                )
            )
            .order_by(RelationshipRow.id.asc())
        ).all()
        return tuple(_row_to_relationship(row) for row in rows)

    def delete(self, relationship_id: UUID) -> None:
        row = self._session.get(RelationshipRow, str(relationship_id))
        if row is None:
            raise RelationshipNotFound("Relationship does not exist.")
        self._session.delete(row)
        try:
            self._session.flush()
        except Exception as error:
            raise RelationshipPersistenceError("Relationship could not be deleted.") from error
