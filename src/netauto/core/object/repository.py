"""Persistence-neutral repository contract for objects and composition membership."""

from typing import Protocol
from uuid import UUID

from netauto.core.object.models import ComponentMembership, Object


class ObjectRepository(Protocol):
    """Repository contract for object and component membership persistence."""

    def list(self) -> tuple[Object, ...]:
        """Return all objects ordered deterministically."""
        ...

    def add(self, object_value: Object) -> None:
        """Persist a new object snapshot."""
        ...

    def get(self, object_id: UUID) -> Object | None:
        """Return an object by UUID or None."""
        ...

    def replace(self, object_value: Object) -> None:
        """Replace an existing object snapshot."""
        ...

    def delete(self, object_id: UUID) -> None:
        """Delete an object and clean up incident membership edges."""
        ...

    def add_membership(self, membership: ComponentMembership) -> None:
        """Persist a new structural ownership edge."""
        ...

    def get_owner(self, child_object_id: UUID) -> ComponentMembership | None:
        """Return the direct ownership edge for a child object or None."""
        ...

    def list_components(
        self,
        parent_object_id: UUID,
        slot_name: str | None = None,
    ) -> tuple[ComponentMembership, ...]:
        """Return direct owned membership edges for a parent, optionally filtered by slot."""
        ...

    def remove_membership(self, child_object_id: UUID) -> None:
        """Remove the ownership edge for a child object."""
        ...
