"""SQLAlchemy unit of work for shared persistence repositories."""

from collections.abc import Callable
from time import sleep as _sleep
from typing import Self

from sqlalchemy import text
from sqlalchemy.orm import Session

from netauto.application.unit_of_work import (
    ModelWriteUnavailable,
    OwnershipGraphWriteUnavailable,
)
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

# Stable PostgreSQL advisory-lock namespace/domain keys for NETAUTO.
# 0x4E455441 is the ASCII bytes for "NETA".
# Key 1 is reserved for MODEL_PLANE_GUARD.
# Key 2 is reserved for OWNERSHIP_GRAPH_GUARD.
_POSTGRESQL_ADVISORY_NAMESPACE_KEY = 0x4E455441
_POSTGRESQL_MODEL_PLANE_GUARD_KEY = 1
_POSTGRESQL_OWNERSHIP_GRAPH_GUARD_KEY = 2


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


def _ensure_postgresql_bind(session: Session) -> None:
    bind = session.get_bind()
    if bind.dialect.name != "postgresql":
        raise RuntimeError("PostgreSQL advisory-guard unit of work requires a PostgreSQL bind.")


def _try_acquire_postgresql_advisory_guard(session: Session, *, guard_key: int) -> bool:
    return bool(
        session.execute(
            text(
                "SELECT pg_try_advisory_xact_lock("
                ":namespace_key, :guard_key)"
            ),
            {
                "namespace_key": _POSTGRESQL_ADVISORY_NAMESPACE_KEY,
                "guard_key": guard_key,
            },
        ).scalar_one()
    )


class PostgresqlModelWriteUnitOfWork(_SqlAlchemyUnitOfWorkBase):
    """PostgreSQL-backed model-plane writer UoW using a transaction advisory lock."""

    def __init__(
        self,
        session_factory: Callable[[], Session],
        *,
        max_guard_attempts: int = 2,
        retry_delay_seconds: float = 0.1,
        sleeper: Callable[[float], None] = _sleep,
    ) -> None:
        super().__init__(session_factory)
        if max_guard_attempts < 1:
            raise ValueError("max_guard_attempts must be at least 1.")
        if retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds must be non-negative.")
        self._max_guard_attempts = max_guard_attempts
        self._retry_delay_seconds = retry_delay_seconds
        self._sleeper = sleeper

    def _ensure_postgresql_bind(self) -> None:
        if self._session is None:
            raise RuntimeError("Unit of work is not active.")
        _ensure_postgresql_bind(self._session)

    def _try_acquire_model_plane_guard(self) -> bool:
        if self._session is None:
            raise RuntimeError("Unit of work is not active.")
        return _try_acquire_postgresql_advisory_guard(
            self._session,
            guard_key=_POSTGRESQL_MODEL_PLANE_GUARD_KEY,
        )

    def _after_session_created(self) -> None:
        self._ensure_postgresql_bind()
        for attempt in range(1, self._max_guard_attempts + 1):
            if self._try_acquire_model_plane_guard():
                return
            if attempt == self._max_guard_attempts:
                break
            self._sleeper(self._retry_delay_seconds)
        raise ModelWriteUnavailable("Model mutation is temporarily unavailable.")


class PostgresqlOwnershipGraphWriteUnitOfWork(_SqlAlchemyUnitOfWorkBase):
    """PostgreSQL-backed ownership-topology writer UoW using a transaction advisory lock."""

    def __init__(
        self,
        session_factory: Callable[[], Session],
        *,
        max_guard_attempts: int = 2,
        retry_delay_seconds: float = 0.1,
        sleeper: Callable[[float], None] = _sleep,
    ) -> None:
        super().__init__(session_factory)
        if max_guard_attempts < 1:
            raise ValueError("max_guard_attempts must be at least 1.")
        if retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds must be non-negative.")
        self._max_guard_attempts = max_guard_attempts
        self._retry_delay_seconds = retry_delay_seconds
        self._sleeper = sleeper

    def _ensure_postgresql_bind(self) -> None:
        if self._session is None:
            raise RuntimeError("Unit of work is not active.")
        _ensure_postgresql_bind(self._session)

    def _try_acquire_ownership_graph_guard(self) -> bool:
        if self._session is None:
            raise RuntimeError("Unit of work is not active.")
        return _try_acquire_postgresql_advisory_guard(
            self._session,
            guard_key=_POSTGRESQL_OWNERSHIP_GRAPH_GUARD_KEY,
        )

    def _after_session_created(self) -> None:
        self._ensure_postgresql_bind()
        for attempt in range(1, self._max_guard_attempts + 1):
            if self._try_acquire_ownership_graph_guard():
                return
            if attempt == self._max_guard_attempts:
                break
            self._sleeper(self._retry_delay_seconds)
        raise OwnershipGraphWriteUnavailable(
            "Ownership topology mutation is temporarily unavailable."
        )
