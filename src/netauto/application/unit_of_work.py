"""Application-facing unit of work abstractions."""

from collections.abc import Callable
from typing import Protocol, Self, TypeAlias

from netauto.core.datatype import DataTypeRepository
from netauto.core.object import ObjectChangeRepository, ObjectRepository
from netauto.core.objecttemplate import ObjectTemplateRepository
from netauto.core.relationship import (
    RelationshipDefinitionRepository,
    RelationshipRepository,
)


class DataTypeUnitOfWork(Protocol):
    """Persistence-neutral unit of work for datatype orchestration."""

    @property
    def datatypes(self) -> DataTypeRepository:
        ...

    @property
    def object_templates(self) -> ObjectTemplateRepository:
        ...

    def __enter__(self) -> Self:
        ...

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        ...

    def commit(self) -> None:
        ...


DataTypeUnitOfWorkFactory: TypeAlias = Callable[[], DataTypeUnitOfWork]


class ObjectTemplateUnitOfWork(Protocol):
    """Persistence-neutral unit of work for object template orchestration."""

    @property
    def datatypes(self) -> DataTypeRepository:
        ...

    @property
    def object_templates(self) -> ObjectTemplateRepository:
        ...

    @property
    def objects(self) -> ObjectRepository:
        ...

    @property
    def relationship_definitions(self) -> RelationshipDefinitionRepository:
        ...

    def __enter__(self) -> Self:
        ...

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        ...

    def commit(self) -> None:
        ...


ObjectTemplateUnitOfWorkFactory: TypeAlias = Callable[[], ObjectTemplateUnitOfWork]


class ObjectUnitOfWork(Protocol):
    """Persistence-neutral unit of work for object orchestration."""

    @property
    def datatypes(self) -> DataTypeRepository:
        ...

    @property
    def object_templates(self) -> ObjectTemplateRepository:
        ...

    @property
    def relationship_definitions(self) -> RelationshipDefinitionRepository:
        ...

    @property
    def relationships(self) -> RelationshipRepository:
        ...

    @property
    def objects(self) -> ObjectRepository:
        ...

    @property
    def object_changes(self) -> ObjectChangeRepository:
        ...

    def __enter__(self) -> Self:
        ...

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        ...

    def commit(self) -> None:
        ...


ObjectUnitOfWorkFactory: TypeAlias = Callable[[], ObjectUnitOfWork]


class RelationshipDefinitionUnitOfWork(Protocol):
    """Persistence-neutral unit of work for relationship definition orchestration."""

    @property
    def relationship_definitions(self) -> RelationshipDefinitionRepository:
        ...

    @property
    def object_templates(self) -> ObjectTemplateRepository:
        ...

    @property
    def relationships(self) -> RelationshipRepository:
        ...

    def __enter__(self) -> Self:
        ...

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        ...

    def commit(self) -> None:
        ...


RelationshipDefinitionUnitOfWorkFactory: TypeAlias = Callable[
    [],
    RelationshipDefinitionUnitOfWork,
]


class RelationshipUnitOfWork(Protocol):
    """Persistence-neutral unit of work for runtime relationship orchestration."""

    @property
    def relationships(self) -> RelationshipRepository:
        ...

    @property
    def relationship_definitions(self) -> RelationshipDefinitionRepository:
        ...

    @property
    def objects(self) -> ObjectRepository:
        ...

    @property
    def object_templates(self) -> ObjectTemplateRepository:
        ...

    def __enter__(self) -> Self:
        ...

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        ...

    def commit(self) -> None:
        ...


RelationshipUnitOfWorkFactory: TypeAlias = Callable[[], RelationshipUnitOfWork]
