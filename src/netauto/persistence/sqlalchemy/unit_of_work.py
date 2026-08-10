"""SQLAlchemy unit of work for shared persistence repositories."""

from collections.abc import Callable

from sqlalchemy.orm import Session

from netauto.persistence.sqlalchemy.datatype_repository import SqlAlchemyDataTypeRepository
from netauto.persistence.sqlalchemy.object_repository import SqlAlchemyObjectRepository
from netauto.persistence.sqlalchemy.objecttemplate_repository import (
    SqlAlchemyObjectTemplateRepository,
)
from netauto.persistence.sqlalchemy.relationship_repository import (
    SqlAlchemyRelationshipDefinitionRepository,
)


class SqlAlchemyUnitOfWork:
    """Explicit transaction boundary for SQLAlchemy persistence."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None
        self.datatypes: SqlAlchemyDataTypeRepository
        self.objects: SqlAlchemyObjectRepository
        self.relationship_definitions: SqlAlchemyRelationshipDefinitionRepository
        self.object_templates: SqlAlchemyObjectTemplateRepository

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        self._session = self._session_factory()
        self.datatypes = SqlAlchemyDataTypeRepository(self._session)
        self.objects = SqlAlchemyObjectRepository(self._session)
        self.relationship_definitions = SqlAlchemyRelationshipDefinitionRepository(self._session)
        self.object_templates = SqlAlchemyObjectTemplateRepository(self._session)
        return self

    def commit(self) -> None:
        if self._session is None:
            raise RuntimeError("Unit of work is not active.")
        self._session.commit()

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if self._session is None:
            return
        if exc is not None or self._session.in_transaction():
            self._session.rollback()
        self._session.close()
        self._session = None
