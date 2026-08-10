from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from netauto.core.objecttemplate import (
    ObjectTemplateInheritanceCycle,
    ObjectTemplateParentNotFound,
    ObjectTemplateSelfInheritance,
    ObjectTemplateVersion,
    ObjectTemplateVersionRef,
    ObjectTemplateVersionStatus,
)
from netauto.core.relationship import (
    RelationshipDefinition,
    relationship_definition_applies,
    relationship_definition_source_applies,
    relationship_definition_target_applies,
    relationship_definitions_are_semantically_equivalent,
)


def _definition(
    *,
    source_template_id: UUID,
    target_template_id: UUID,
    forward_name: str = "uses",
    reverse_name: str = "is_used_by",
) -> RelationshipDefinition:
    return RelationshipDefinition(
        id=uuid4(),
        source_template_id=source_template_id,
        target_template_id=target_template_id,
        forward_name=forward_name,
        reverse_name=reverse_name,
    )


def _version(
    template_id: UUID,
    version: int,
    *,
    parent: ObjectTemplateVersionRef | None = None,
) -> ObjectTemplateVersion:
    return ObjectTemplateVersion(
        template_id=template_id,
        version=version,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        parent=parent,
    )


def _lookup(
    versions: tuple[ObjectTemplateVersion, ...],
):
    version_map = {(version.template_id, version.version): version for version in versions}

    def parent_lookup(ref: ObjectTemplateVersionRef) -> ObjectTemplateVersion | None:
        return version_map.get((ref.template_id, ref.version))

    return parent_lookup


def test_same_orientation_same_semantics_are_equivalent() -> None:
    source_id = uuid4()
    target_id = uuid4()
    left = _definition(source_template_id=source_id, target_template_id=target_id)
    right = _definition(source_template_id=source_id, target_template_id=target_id)

    assert relationship_definitions_are_semantically_equivalent(left, right) is True


def test_inverse_orientation_with_swapped_names_is_equivalent() -> None:
    source_id = uuid4()
    target_id = uuid4()
    left = _definition(source_template_id=source_id, target_template_id=target_id)
    right = _definition(
        source_template_id=target_id,
        target_template_id=source_id,
        forward_name="is_used_by",
        reverse_name="uses",
    )

    assert relationship_definitions_are_semantically_equivalent(left, right) is True


def test_same_endpoints_with_different_semantic_pair_is_not_equivalent() -> None:
    source_id = uuid4()
    target_id = uuid4()
    left = _definition(source_template_id=source_id, target_template_id=target_id)
    right = _definition(
        source_template_id=source_id,
        target_template_id=target_id,
        forward_name="manages",
        reverse_name="managed_by",
    )

    assert relationship_definitions_are_semantically_equivalent(left, right) is False


def test_reversed_endpoints_without_swapped_semantics_is_not_equivalent() -> None:
    source_id = uuid4()
    target_id = uuid4()
    left = _definition(source_template_id=source_id, target_template_id=target_id)
    right = _definition(source_template_id=target_id, target_template_id=source_id)

    assert relationship_definitions_are_semantically_equivalent(left, right) is False


def test_endpoint_applicability_exact_source_and_target_is_true() -> None:
    source_id = uuid4()
    target_id = uuid4()
    definition = _definition(source_template_id=source_id, target_template_id=target_id)
    source_version = _version(source_id, 1)
    target_version = _version(target_id, 1)

    assert relationship_definition_applies(
        definition,
        source_version=source_version,
        target_version=target_version,
        parent_lookup=_lookup((source_version, target_version)),
    )


def test_source_descendant_and_exact_target_is_true() -> None:
    source_id = uuid4()
    child_source_id = uuid4()
    target_id = uuid4()
    definition = _definition(source_template_id=source_id, target_template_id=target_id)
    source_parent = _version(source_id, 1)
    source_child = _version(
        child_source_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=source_id, version=1),
    )
    target_version = _version(target_id, 1)

    assert relationship_definition_applies(
        definition,
        source_version=source_child,
        target_version=target_version,
        parent_lookup=_lookup((source_parent, source_child, target_version)),
    )


def test_exact_source_and_target_descendant_is_true() -> None:
    source_id = uuid4()
    target_id = uuid4()
    child_target_id = uuid4()
    definition = _definition(source_template_id=source_id, target_template_id=target_id)
    source_version = _version(source_id, 1)
    target_parent = _version(target_id, 1)
    target_child = _version(
        child_target_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=target_id, version=1),
    )

    assert relationship_definition_applies(
        definition,
        source_version=source_version,
        target_version=target_child,
        parent_lookup=_lookup((source_version, target_parent, target_child)),
    )


def test_descendant_on_both_sides_is_true() -> None:
    source_id = uuid4()
    child_source_id = uuid4()
    target_id = uuid4()
    child_target_id = uuid4()
    definition = _definition(source_template_id=source_id, target_template_id=target_id)
    source_parent = _version(source_id, 1)
    source_child = _version(
        child_source_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=source_id, version=1),
    )
    target_parent = _version(target_id, 1)
    target_child = _version(
        child_target_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=target_id, version=1),
    )

    assert relationship_definition_applies(
        definition,
        source_version=source_child,
        target_version=target_child,
        parent_lookup=_lookup((source_parent, source_child, target_parent, target_child)),
    )


def test_unrelated_source_is_false() -> None:
    definition = _definition(source_template_id=uuid4(), target_template_id=uuid4())
    source_version = _version(uuid4(), 1)
    target_version = _version(definition.target_template_id, 1)

    assert relationship_definition_applies(
        definition,
        source_version=source_version,
        target_version=target_version,
        parent_lookup=_lookup((source_version, target_version)),
    ) is False


def test_unrelated_target_is_false() -> None:
    definition = _definition(source_template_id=uuid4(), target_template_id=uuid4())
    source_version = _version(definition.source_template_id, 1)
    target_version = _version(uuid4(), 1)

    assert relationship_definition_applies(
        definition,
        source_version=source_version,
        target_version=target_version,
        parent_lookup=_lookup((source_version, target_version)),
    ) is False


def test_child_defined_relationship_does_not_apply_upward_to_parent() -> None:
    parent_source_id = uuid4()
    child_source_id = uuid4()
    target_id = uuid4()
    definition = _definition(
        source_template_id=child_source_id,
        target_template_id=target_id,
    )
    parent_source = _version(parent_source_id, 1)
    child_source = _version(
        child_source_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=parent_source_id, version=1),
    )
    target_version = _version(target_id, 1)

    assert relationship_definition_applies(
        definition,
        source_version=parent_source,
        target_version=target_version,
        parent_lookup=_lookup((parent_source, child_source, target_version)),
    ) is False


def test_multi_level_ancestry_works() -> None:
    source_root_id = uuid4()
    source_mid_id = uuid4()
    source_leaf_id = uuid4()
    target_id = uuid4()
    definition = _definition(source_template_id=source_root_id, target_template_id=target_id)
    source_root = _version(source_root_id, 1)
    source_mid = _version(
        source_mid_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=source_root_id, version=1),
    )
    source_leaf = _version(
        source_leaf_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=source_mid_id, version=1),
    )
    target_version = _version(target_id, 1)

    assert relationship_definition_applies(
        definition,
        source_version=source_leaf,
        target_version=target_version,
        parent_lookup=_lookup((source_root, source_mid, source_leaf, target_version)),
    )


def test_same_template_identity_with_different_ancestry_versions_is_version_sensitive() -> None:
    required_source_id = uuid4()
    router_id = uuid4()
    target_id = uuid4()
    definition = _definition(
        source_template_id=required_source_id,
        target_template_id=target_id,
    )
    required_source = _version(required_source_id, 1)
    router_v1 = _version(
        router_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=required_source_id, version=1),
    )
    router_v2 = _version(router_id, 2)
    target_version = _version(target_id, 1)

    lookup = _lookup((required_source, router_v1, router_v2, target_version))
    assert relationship_definition_applies(
        definition,
        source_version=router_v1,
        target_version=target_version,
        parent_lookup=lookup,
    )
    assert relationship_definition_applies(
        definition,
        source_version=router_v2,
        target_version=target_version,
        parent_lookup=lookup,
    ) is False


def test_missing_exact_parent_propagates_existing_parent_not_found_error() -> None:
    source_id = uuid4()
    child_source_id = uuid4()
    target_id = uuid4()
    definition = _definition(source_template_id=source_id, target_template_id=target_id)
    source_child = _version(
        child_source_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=source_id, version=1),
    )
    target_version = _version(target_id, 1)

    with pytest.raises(ObjectTemplateParentNotFound):
        relationship_definition_applies(
            definition,
            source_version=source_child,
            target_version=target_version,
            parent_lookup=_lookup((source_child, target_version)),
        )


def test_source_endpoint_applicability_exact_same_template_is_true() -> None:
    source_id = uuid4()
    definition = _definition(source_template_id=source_id, target_template_id=uuid4())
    source_version = _version(source_id, 1)

    assert relationship_definition_source_applies(
        definition,
        object_version=source_version,
        parent_lookup=_lookup((source_version,)),
    )


def test_source_endpoint_applicability_exact_descendant_is_true() -> None:
    source_id = uuid4()
    child_source_id = uuid4()
    definition = _definition(source_template_id=source_id, target_template_id=uuid4())
    source_parent = _version(source_id, 1)
    source_child = _version(
        child_source_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=source_id, version=1),
    )

    assert relationship_definition_source_applies(
        definition,
        object_version=source_child,
        parent_lookup=_lookup((source_parent, source_child)),
    )


def test_source_endpoint_applicability_is_exact_version_sensitive() -> None:
    source_id = uuid4()
    router_id = uuid4()
    definition = _definition(source_template_id=source_id, target_template_id=uuid4())
    source_parent = _version(source_id, 1)
    router_v1 = _version(
        router_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=source_id, version=1),
    )
    router_v2 = _version(router_id, 2)
    lookup = _lookup((source_parent, router_v1, router_v2))

    assert relationship_definition_source_applies(
        definition,
        object_version=router_v1,
        parent_lookup=lookup,
    )
    assert (
        relationship_definition_source_applies(
            definition,
            object_version=router_v2,
            parent_lookup=lookup,
        )
        is False
    )


def test_source_and_target_endpoint_applicability_are_independent() -> None:
    source_id = uuid4()
    target_id = uuid4()
    unrelated_id = uuid4()
    definition = _definition(source_template_id=source_id, target_template_id=target_id)
    source_version = _version(source_id, 1)
    target_version = _version(target_id, 1)
    unrelated_version = _version(unrelated_id, 1)
    lookup = _lookup((source_version, target_version, unrelated_version))

    assert relationship_definition_source_applies(
        definition,
        object_version=source_version,
        parent_lookup=lookup,
    )
    assert (
        relationship_definition_source_applies(
            definition,
            object_version=unrelated_version,
            parent_lookup=lookup,
        )
        is False
    )
    assert relationship_definition_target_applies(
        definition,
        object_version=target_version,
        parent_lookup=lookup,
    )
    assert (
        relationship_definition_target_applies(
            definition,
            object_version=unrelated_version,
            parent_lookup=lookup,
        )
        is False
    )


def test_target_endpoint_applicability_missing_parent_propagates_error() -> None:
    target_id = uuid4()
    child_target_id = uuid4()
    definition = _definition(source_template_id=uuid4(), target_template_id=target_id)
    target_child = _version(
        child_target_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=target_id, version=1),
    )

    with pytest.raises(ObjectTemplateParentNotFound):
        relationship_definition_target_applies(
            definition,
            object_version=target_child,
            parent_lookup=_lookup((target_child,)),
        )


def test_cycle_propagates_existing_inheritance_cycle_error() -> None:
    required_source_id = uuid4()
    source_id = uuid4()
    child_source_id = uuid4()
    target_id = uuid4()
    definition = _definition(
        source_template_id=required_source_id,
        target_template_id=target_id,
    )
    source_root = _version(
        source_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=child_source_id, version=1),
    )
    source_child = _version(
        child_source_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=source_id, version=1),
    )
    target_version = _version(target_id, 1)

    with pytest.raises(ObjectTemplateInheritanceCycle):
        relationship_definition_applies(
            definition,
            source_version=source_child,
            target_version=target_version,
            parent_lookup=_lookup((source_root, source_child, target_version)),
        )


def test_source_endpoint_cycle_propagates_existing_inheritance_cycle_error() -> None:
    required_source_id = uuid4()
    source_id = uuid4()
    child_source_id = uuid4()
    definition = _definition(
        source_template_id=required_source_id,
        target_template_id=uuid4(),
    )
    source_root = _version(
        source_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=child_source_id, version=1),
    )
    source_child = _version(
        child_source_id,
        1,
        parent=ObjectTemplateVersionRef(template_id=source_id, version=1),
    )

    with pytest.raises(ObjectTemplateInheritanceCycle):
        relationship_definition_source_applies(
            definition,
            object_version=source_child,
            parent_lookup=_lookup((source_root, source_child)),
        )


def test_self_inheritance_propagates_existing_self_inheritance_error() -> None:
    required_source_id = uuid4()
    source_id = uuid4()
    target_id = uuid4()
    definition = _definition(
        source_template_id=required_source_id,
        target_template_id=target_id,
    )
    source_version = _version(
        source_id,
        2,
        parent=ObjectTemplateVersionRef(template_id=source_id, version=1),
    )
    target_version = _version(target_id, 1)

    with pytest.raises(ObjectTemplateSelfInheritance):
        relationship_definition_applies(
            definition,
            source_version=source_version,
            target_version=target_version,
            parent_lookup=_lookup((source_version, target_version)),
        )


def test_target_endpoint_self_inheritance_propagates_existing_error() -> None:
    required_target_id = uuid4()
    target_id = uuid4()
    definition = _definition(
        source_template_id=uuid4(),
        target_template_id=required_target_id,
    )
    target_version = _version(
        target_id,
        2,
        parent=ObjectTemplateVersionRef(template_id=target_id, version=1),
    )

    with pytest.raises(ObjectTemplateSelfInheritance):
        relationship_definition_target_applies(
            definition,
            object_version=target_version,
            parent_lookup=_lookup((target_version,)),
        )
