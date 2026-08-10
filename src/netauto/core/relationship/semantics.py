"""Pure domain semantics for relationship definitions."""

from netauto.core.objecttemplate import (
    ObjectTemplateInheritanceResolver,
    ObjectTemplateVersion,
    ObjectTemplateVersionLookup,
)
from netauto.core.relationship.models import RelationshipDefinition


def relationship_definitions_are_semantically_equivalent(
    left: RelationshipDefinition,
    right: RelationshipDefinition,
) -> bool:
    """Return True when two definitions express the same canonical semantics."""

    return (
        (
            left.source_template_id == right.source_template_id
            and left.target_template_id == right.target_template_id
            and left.forward_name == right.forward_name
            and left.reverse_name == right.reverse_name
        )
        or (
            left.source_template_id == right.target_template_id
            and left.target_template_id == right.source_template_id
            and left.forward_name == right.reverse_name
            and left.reverse_name == right.forward_name
        )
    )


def relationship_definition_source_applies(
    definition: RelationshipDefinition,
    *,
    object_version: ObjectTemplateVersion,
    parent_lookup: ObjectTemplateVersionLookup,
) -> bool:
    """Return True when one concrete version satisfies the definition source endpoint."""

    return ObjectTemplateInheritanceResolver().is_same_or_descendant_template(
        object_version,
        required_template_id=definition.source_template_id,
        parent_lookup=parent_lookup,
    )


def relationship_definition_target_applies(
    definition: RelationshipDefinition,
    *,
    object_version: ObjectTemplateVersion,
    parent_lookup: ObjectTemplateVersionLookup,
) -> bool:
    """Return True when one concrete version satisfies the definition target endpoint."""

    return ObjectTemplateInheritanceResolver().is_same_or_descendant_template(
        object_version,
        required_template_id=definition.target_template_id,
        parent_lookup=parent_lookup,
    )


def relationship_definition_applies(
    definition: RelationshipDefinition,
    *,
    source_version: ObjectTemplateVersion,
    target_version: ObjectTemplateVersion,
    parent_lookup: ObjectTemplateVersionLookup,
) -> bool:
    """Return True when both concrete endpoint versions satisfy the definition."""

    return relationship_definition_source_applies(
        definition,
        object_version=source_version,
        parent_lookup=parent_lookup,
    ) and relationship_definition_target_applies(
        definition,
        object_version=target_version,
        parent_lookup=parent_lookup,
    )
