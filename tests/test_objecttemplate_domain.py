"""Pure ObjectTemplate effective-schema semantics."""

from uuid import uuid4

import pytest

from netauto.domain.datatypes import VersionStatus
from netauto.domain.objecttemplates import (
    LocalComponent,
    LocalProperty,
    ObjectTemplateValidationError,
    ObjectTemplateVersion,
    ValueMode,
    resolve_effective_schema,
)


def _version(
    template_id: object,
    properties: tuple[LocalProperty, ...] = (),
    components: tuple[LocalComponent, ...] = (),
) -> ObjectTemplateVersion:
    from uuid import UUID

    assert isinstance(template_id, UUID)
    return ObjectTemplateVersion(
        template_id,
        1,
        1,
        VersionStatus.DRAFT,
        None,
        None,
        properties,
        components,
    )


def test_effective_schema_is_root_to_leaf_and_preserves_local_positions() -> None:
    root_id = uuid4()
    leaf_id = uuid4()
    datatype_id = uuid4()
    target_id = uuid4()
    root = _version(
        root_id,
        (
            LocalProperty(
                "root_value", 2, datatype_id, 1, ValueMode.SCALAR, False, None
            ),
        ),
    )
    leaf = _version(
        leaf_id,
        (LocalProperty("leaf_value", 1, datatype_id, 1, ValueMode.LIST, False, None),),
        (LocalComponent("port", 1, target_id),),
    )

    schema = resolve_effective_schema(leaf_id, 1, (root, leaf))

    assert [
        (item.declaring_template_id, item.declaration.name)
        for item in schema.properties
    ] == [
        (root_id, "root_value"),
        (leaf_id, "leaf_value"),
    ]
    assert schema.components[0].declaring_template_id == leaf_id


def test_effective_schema_rejects_cross_kind_inherited_collision() -> None:
    root_id = uuid4()
    leaf_id = uuid4()
    root = _version(root_id, components=(LocalComponent("member", 1, uuid4()),))
    leaf = _version(
        leaf_id,
        (LocalProperty("member", 1, uuid4(), 1, ValueMode.SCALAR, False, None),),
    )

    with pytest.raises(
        ObjectTemplateValidationError, match="inherited_member_collision"
    ):
        resolve_effective_schema(leaf_id, 1, (root, leaf))


def test_effective_schema_defensively_rejects_cycles() -> None:
    template_id = uuid4()
    version = _version(template_id)

    with pytest.raises(ObjectTemplateValidationError, match="inheritance_cycle"):
        resolve_effective_schema(template_id, 1, (version, version))
