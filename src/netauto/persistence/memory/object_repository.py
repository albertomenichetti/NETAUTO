"""In-memory object repository implementation."""

from uuid import UUID

from netauto.core.object import (
    ComponentMembership,
    ComponentMembershipAlreadyExists,
    ComponentMembershipNotFound,
    InvalidObject,
    Object,
    ObjectAlreadyExists,
    ObjectConcurrentModification,
    ObjectNotFound,
    ObjectRepository,
)


class InMemoryObjectRepository(ObjectRepository):
    """Reference in-memory object repository."""

    def __init__(self) -> None:
        self._objects: dict[UUID, Object] = {}
        self._memberships_by_child: dict[UUID, ComponentMembership] = {}

    def list(self) -> tuple[Object, ...]:
        objects = list(self._objects.values())
        objects.sort(key=lambda item: str(item.id))
        return tuple(objects)

    def add(self, object_value: Object) -> None:
        if object_value.id in self._objects:
            raise ObjectAlreadyExists("Object UUID already exists.")
        self._objects[object_value.id] = object_value

    def get(self, object_id: UUID) -> Object | None:
        return self._objects.get(object_id)

    def list_by_template_version(
        self,
        template_id: UUID,
        template_version: int,
    ) -> tuple[Object, ...]:
        objects = [
            object_value
            for object_value in self._objects.values()
            if object_value.template_id == template_id
            and object_value.template_version == template_version
        ]
        objects.sort(key=lambda item: str(item.id))
        return tuple(objects)

    def replace(self, object_value: Object) -> None:
        if object_value.id not in self._objects:
            raise ObjectNotFound("Object does not exist.")
        self._objects[object_value.id] = object_value

    def replace_if_current(
        self,
        expected: Object,
        replacement: Object,
    ) -> None:
        if expected.id != replacement.id:
            raise InvalidObject("Conditional object replacement cannot change object identity.")
        current = self._objects.get(expected.id)
        if current is None or current != expected:
            raise ObjectConcurrentModification("Object was modified concurrently.")
        self._objects[expected.id] = replacement

    def delete(self, object_id: UUID) -> None:
        if object_id not in self._objects:
            raise ObjectNotFound("Object does not exist.")

        del self._objects[object_id]
        self._memberships_by_child.pop(object_id, None)

        children_to_remove = [
            child_object_id
            for child_object_id, membership in self._memberships_by_child.items()
            if membership.parent_object_id == object_id
        ]
        for child_object_id in children_to_remove:
            del self._memberships_by_child[child_object_id]

    def add_membership(self, membership: ComponentMembership) -> None:
        if membership.parent_object_id not in self._objects:
            raise ObjectNotFound("Object does not exist.")
        if membership.child_object_id not in self._objects:
            raise ObjectNotFound("Object does not exist.")
        if membership.child_object_id in self._memberships_by_child:
            raise ComponentMembershipAlreadyExists(
                "Component membership for child object already exists."
            )
        self._memberships_by_child[membership.child_object_id] = membership

    def get_owner(self, child_object_id: UUID) -> ComponentMembership | None:
        return self._memberships_by_child.get(child_object_id)

    def list_components(
        self,
        parent_object_id: UUID,
        slot_name: str | None = None,
    ) -> tuple[ComponentMembership, ...]:
        memberships = [
            membership
            for membership in self._memberships_by_child.values()
            if membership.parent_object_id == parent_object_id
            and (slot_name is None or membership.slot_name == slot_name)
        ]
        memberships.sort(key=lambda item: (item.slot_name, str(item.child_object_id)))
        return tuple(memberships)

    def remove_membership(self, child_object_id: UUID) -> None:
        if child_object_id not in self._memberships_by_child:
            raise ComponentMembershipNotFound("Component membership does not exist.")
        del self._memberships_by_child[child_object_id]
