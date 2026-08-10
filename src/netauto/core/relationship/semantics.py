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


def relationship_definition_applies(
    definition: RelationshipDefinition,
    *,
    source_version: ObjectTemplateVersion,
    target_version: ObjectTemplateVersion,
    parent_lookup: ObjectTemplateVersionLookup,
) -> bool:
    """Return True when both concrete endpoint versions satisfy the definition."""

    resolver = ObjectTemplateInheritanceResolver()
    return resolver.is_same_or_descendant_template(
        source_version,
        required_template_id=definition.source_template_id,
        parent_lookup=parent_lookup,
    ) and resolver.is_same_or_descendant_template(
        target_version,
        required_template_id=definition.target_template_id,
        parent_lookup=parent_lookup,
    )
