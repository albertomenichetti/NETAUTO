"""Application-facing unit of work abstractions."""

from collections.abc import Callable
from typing import Protocol, Self, TypeAlias

from netauto.core.datatype import DataTypeRepository
from netauto.core.objecttemplate import ObjectTemplateRepository


class DataTypeUnitOfWork(Protocol):
    """Persistence-neutral unit of work for datatype orchestration."""

    @property
    def datatypes(self) -> DataTypeRepository:
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

    def __enter__(self) -> Self:
        ...

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        ...

    def commit(self) -> None:
        ...


ObjectTemplateUnitOfWorkFactory: TypeAlias = Callable[[], ObjectTemplateUnitOfWork]
