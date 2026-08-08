"""SQLAlchemy unit of work for datatype persistence."""

from collections.abc import Callable

from sqlalchemy.orm import Session

from netauto.persistence.sqlalchemy.datatype_repository import SqlAlchemyDataTypeRepository


class SqlAlchemyUnitOfWork:
    """Explicit transaction boundary for SQLAlchemy persistence."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None
        self.datatypes: SqlAlchemyDataTypeRepository

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        self._session = self._session_factory()
        self.datatypes = SqlAlchemyDataTypeRepository(self._session)
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
