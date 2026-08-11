"""SQLAlchemy unit of work for shared persistence repositories."""

from collections.abc import Callable
from typing import Self

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from netauto.persistence.sqlalchemy.datatype_repository import SqlAlchemyDataTypeRepository
from netauto.persistence.sqlalchemy.object_change_repository import (
    SqlAlchemyObjectChangeRepository,
)
from netauto.persistence.sqlalchemy.object_repository import SqlAlchemyObjectRepository
from netauto.persistence.sqlalchemy.objecttemplate_repository import (
    SqlAlchemyObjectTemplateRepository,
)
from netauto.persistence.sqlalchemy.relationship_repository import (
    SqlAlchemyRelationshipDefinitionRepository,
    SqlAlchemyRelationshipRepository,
)


class _SqlAlchemyUnitOfWorkBase:
    """Explicit transaction boundary for SQLAlchemy persistence."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None
        self.datatypes: SqlAlchemyDataTypeRepository
        self.object_changes: SqlAlchemyObjectChangeRepository
        self.objects: SqlAlchemyObjectRepository
        self.relationships: SqlAlchemyRelationshipRepository
        self.relationship_definitions: SqlAlchemyRelationshipDefinitionRepository
        self.object_templates: SqlAlchemyObjectTemplateRepository

    def _after_session_created(self) -> None:
        """Allow specialized unit-of-work entry behavior before repositories are exposed."""

    def _initialize_repositories(self) -> None:
        if self._session is None:
            raise RuntimeError("Unit of work is not active.")
        self.datatypes = SqlAlchemyDataTypeRepository(self._session)
        self.object_changes = SqlAlchemyObjectChangeRepository(self._session)
        self.objects = SqlAlchemyObjectRepository(self._session)
        self.relationships = SqlAlchemyRelationshipRepository(self._session)
        self.relationship_definitions = SqlAlchemyRelationshipDefinitionRepository(self._session)
        self.object_templates = SqlAlchemyObjectTemplateRepository(self._session)

    def __enter__(self) -> Self:
        self._session = self._session_factory()
        try:
            self._after_session_created()
            self._initialize_repositories()
        except Exception:
            self._session.close()
            self._session = None
            raise
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


class SqlAlchemyUnitOfWork(_SqlAlchemyUnitOfWorkBase):
    """Ordinary SQLAlchemy unit of work."""


class SqliteModelWriteUnitOfWork(_SqlAlchemyUnitOfWorkBase):
    """SQLite-backed model-plane writer UoW using a transaction-scoped writer reservation."""

    def _after_session_created(self) -> None:
        if self._session is None:
            raise RuntimeError("Unit of work is not active.")
        try:
            self._session.connection().execute(text("BEGIN IMMEDIATE"))
        except SQLAlchemyError:
            if self._session.in_transaction():
                self._session.rollback()
            raise
