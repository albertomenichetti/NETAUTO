"""In-memory append-only object change repository."""

from uuid import UUID

from netauto.core.object import (
    ObjectChange,
    ObjectChangeAlreadyExists,
    ObjectChangeRepository,
)


class InMemoryObjectChangeRepository(ObjectChangeRepository):
    """Reference in-memory repository for runtime object history."""

    def __init__(self) -> None:
        self._changes: dict[UUID, ObjectChange] = {}

    def add(self, change: ObjectChange) -> None:
        if change.id in self._changes:
            raise ObjectChangeAlreadyExists("Object change UUID already exists.")
        self._changes[change.id] = change

    def list_by_object(self, object_id: UUID) -> tuple[ObjectChange, ...]:
        changes = [
            change for change in self._changes.values() if change.object_id == object_id
        ]
        changes.sort(key=lambda change: (change.occurred_at, str(change.id)))
        return tuple(changes)
