"""Bounded S08 FK diagnostic translation at the persistence boundary."""

from typing import cast
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection

from netauto.persistence.datatypes import DataTypeStore, DeleteReferenceError
from netauto.persistence.objects import ObjectDeleteReferenceError, ObjectStore
from netauto.persistence.objecttemplates import (
    ObjectTemplateDeleteReferenceError,
    ObjectTemplateStore,
)


class _Diagnostic:
    def __init__(self, constraint_name: str) -> None:
        self.constraint_name = constraint_name


class _OriginalError(Exception):
    def __init__(self, constraint_name: str) -> None:
        self.diag = _Diagnostic(constraint_name)
        super().__init__(constraint_name)


class _FailingConnection:
    def __init__(self, constraint_name: str, *, fail_on_call: int = 1) -> None:
        self._error = IntegrityError(
            "bounded test statement", {}, _OriginalError(constraint_name)
        )
        self._fail_on_call = fail_on_call
        self._calls = 0

    async def execute(self, statement: object) -> object:
        del statement
        self._calls += 1
        if self._calls == self._fail_on_call:
            raise self._error
        return object()


def _connection(constraint_name: str, *, fail_on_call: int = 1) -> AsyncConnection:
    return cast(
        AsyncConnection,
        cast(object, _FailingConnection(constraint_name, fail_on_call=fail_on_call)),
    )


@pytest.mark.parametrize(
    ("constraint_name", "blocker_type"),
    [
        ("fk_object_templates_parent", "child_object_template"),
        ("fk_object_template_versions_parent_version", "child_object_template"),
        ("fk_object_template_components_target", "object_template_component"),
        ("fk_objects_template_version", "object"),
        ("fk_relationship_resolutions_from_template", "relationship_resolution"),
        ("fk_relationship_resolutions_to_template", "relationship_resolution"),
    ],
)
async def test_object_template_delete_maps_only_known_external_constraints(
    constraint_name: str, blocker_type: str
) -> None:
    store = ObjectTemplateStore(_connection(constraint_name, fail_on_call=2))
    with pytest.raises(ObjectTemplateDeleteReferenceError) as caught:
        await store.delete_lineage(uuid4())
    assert caught.value.blocker_type == blocker_type


async def test_datatype_delete_maps_exact_property_reference_constraint() -> None:
    store = DataTypeStore(
        _connection("fk_object_template_properties_datatype_version", fail_on_call=2)
    )
    with pytest.raises(DeleteReferenceError):
        await store.delete_lineage(uuid4())


@pytest.mark.parametrize(
    ("constraint_name", "blocker_type"),
    [
        ("fk_object_components_child", "ownership"),
        ("fk_object_components_parent", "ownership"),
        ("fk_runtime_resolutions_from_object", "relationship"),
        ("fk_runtime_resolutions_to_object", "relationship"),
    ],
)
async def test_object_delete_maps_only_known_current_reference_constraints(
    constraint_name: str, blocker_type: str
) -> None:
    store = ObjectStore(_connection(constraint_name))
    with pytest.raises(ObjectDeleteReferenceError) as caught:
        await store.delete(uuid4())
    assert caught.value.blocker_type == blocker_type


async def test_unexpected_delete_integrity_error_is_not_semantically_translated() -> (
    None
):
    with pytest.raises(IntegrityError):
        await ObjectStore(_connection("unexpected_constraint")).delete(uuid4())
