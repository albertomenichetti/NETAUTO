# ADR 0014: Relationships / Graph Architecture

## Status

Accepted

## Context

NETAUTO already implements:

- versioned `DataType` schemas
- versioned `ObjectTemplate` schemas with exact pinned parent-version
  inheritance
- runtime `Object` instances pinned to exact `ObjectTemplateVersion`
- structural component composition through `ObjectTemplateVersion` component
  slots and runtime ownership edges
- additive ObjectTemplate and Object migration semantics

Relationships add a second runtime connectivity model that must remain
distinct from component ownership.

## Decision

Relationships are modeled as an autonomous graph layer with:

- one canonical `RelationshipDefinition` entity between two
  `ObjectTemplate` identities
- one canonical runtime `Relationship` edge between two `Object` identities
- mandatory forward and reverse semantic names on every definition
- inheritance-aware endpoint compatibility determined from each endpoint
  Object's exact pinned `ObjectTemplateVersion` ancestry
- no version fields on `RelationshipDefinition`
- no mirrored persisted forward/reverse copies at either definition or runtime
  level

This architecture is implemented in the current system, including persistence,
navigation, semantic conflict detection, ObjectTemplate publication safeguards,
and restrictive delete behavior.

## RelationshipDefinition Model

The canonical conceptual shape is:

```text
RelationshipDefinition
    id
    source_template_id
    target_template_id
    forward_name
    reverse_name
```

Current rules:

- `id` is the stable primary identity
- `source_template_id` and `target_template_id` reference stable
  `ObjectTemplate` identities
- creating a new definition requires each endpoint identity to have at least
  one `PUBLISHED` ObjectTemplateVersion
- the exact published version is not pinned into the definition
- abstract endpoint templates are allowed if they have at least one
  `PUBLISHED` version
- identities with only `DRAFT` and/or `DEPRECATED` versions cannot be used to
  create new definitions
- `forward_name` and `reverse_name` are mandatory semantic identifiers

`RelationshipDefinition` is version-independent. It survives new
ObjectTemplate publication unchanged. Existing definitions still participate in
semantic conflict analysis through `PUBLISHED` and `DEPRECATED` concrete
template versions.

## Runtime Relationship Model

The canonical runtime shape is:

```text
Relationship
    id
    relationship_definition_id
    source_object_id
    target_object_id
```

One stored edge represents both semantic views. Stored orientation follows the
definition's canonical `source_template_id -> target_template_id` direction.
Reverse navigation is derived from the same stored edge through
`reverse_name`.

Important current behavior:

- runtime create uses canonical source->target orientation
- the application does not accept an inverse-oriented create command and
  normalize it automatically
- forward and reverse names are navigation semantics over one stored edge
- `(definition, A, B)` and `(definition, B, A)` are not automatically the same
  persisted runtime edge

The current physical uniqueness key is the ordered triple:

```text
UNIQUE(
    relationship_definition_id,
    source_object_id,
    target_object_id
)
```

## Inheritance-Aware Applicability

Relationship definitions are inherited through ObjectTemplate inheritance.

Endpoint compatibility is:

```text
candidate compatible with required_template_id iff:

candidate.template_id == required_template_id

OR

some ancestor reached through the candidate's exact pinned
ObjectTemplateVersion parent chain has template_id == required_template_id
```

This rule applies independently to both endpoints.

Declared RelationshipDefinitions are the canonical persisted entities.
Effective RelationshipDefinitions are read-time views for a concrete pinned
ObjectTemplateVersion whose source or target requirement is satisfied directly
or through exact pinned ancestry.

Inherited definitions are not copied into descendants. Applicability is
resolved dynamically.

## Semantic Conflict Detection

RelationshipDefinition UUID is the primary identity, but semantic conflict
rules exist in addition to UUID identity.

Inverse-equivalent declarations are normalized for semantic conflict analysis.
For the same normalized semantic pair, overlapping effective source endpoint
spaces and overlapping effective target endpoint spaces are rejected.

This applies both when creating a RelationshipDefinition and when publishing an
ObjectTemplateVersion, because new ancestry can make previously distinct
definitions overlap semantically.

Different semantic pairs between the same endpoint identities may coexist.

## Lifecycle Integration

Current implemented lifecycle interactions:

- RelationshipDefinition creation requires each endpoint template identity to
  have at least one `PUBLISHED` version
- RelationshipDefinition delete is rejected while runtime Relationships use it
- ObjectTemplate delete is rejected while a RelationshipDefinition references
  that template identity
- ObjectTemplate publication checks whether the resulting ancestry would create
  a RelationshipDefinition semantic conflict
- Object subtree deletion explicitly removes runtime Relationships incident to
  Objects actually being deleted before deleting those Objects
- unrelated endpoint Objects survive subtree deletion

## Consequences

Relationships remain separate from component ownership, exact template-version
ancestry still drives applicability, runtime edges have one canonical stored
orientation, and semantic conflict analysis covers both direct and
inheritance-induced overlap.
