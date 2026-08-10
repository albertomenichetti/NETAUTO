# ADR 0014: Relationships / Graph Architecture

## Status

Accepted

## Context

NETAUTO currently implements:

- versioned `DataType` schemas;
- versioned `ObjectTemplate` schemas with exact pinned parent-version inheritance;
- runtime `Object` instances pinned to exact `ObjectTemplateVersion`;
- structural component composition through `ObjectTemplateVersion` component slots and
  runtime ownership edges;
- explicit additive `ObjectTemplate` and `Object` migration semantics.

The roadmap reserves M2 for Relationships / graph. This introduces a second
runtime connectivity model that must remain distinct from component ownership.

The repository already establishes several architectural constraints that also
apply to Relationships:

- the CLI is REST-only;
- FastAPI routers remain thin transport adapters;
- application services own orchestration;
- the domain core owns semantic rules;
- persistence remains behind repository and Unit of Work ports;
- template inheritance follows exact stored `ObjectTemplateVersionRef`
  parent references and never uses latest-version fallback.

Relationship architecture must preserve those boundaries while also satisfying
the following fixed requirements:

- Relationship definitions are version-independent and reference
  `ObjectTemplate` identity only.
- Relationship applicability is inheritance-aware on both endpoints.
- Every Relationship has mandatory forward and inverse semantics.
- One canonical persisted definition and one canonical persisted runtime edge
  must produce both navigation directions.
- Relationship semantics must remain separate from component composition,
  ownership, attach/detach, and subtree deletion.

## Decision

NETAUTO will model Relationships as an autonomous graph layer with:

- one canonical `RelationshipDefinition` entity between two
  `ObjectTemplate` identities;
- one canonical runtime `Relationship` edge between two `Object` identities;
- mandatory forward and reverse semantic names on every definition;
- inheritance-aware endpoint compatibility determined from each endpoint
  Object's exact pinned `ObjectTemplateVersion` ancestry;
- no version fields on `RelationshipDefinition`;
- no mirrored persisted forward/reverse copies at either definition or runtime
  level.

The first M2 design is architecture-only and intentionally defers
implementation, persistence, traversal algorithms, Relationship properties,
and destructive lifecycle workflows.

## RelationshipDefinition Conceptual Model

The canonical conceptual shape is:

```text
RelationshipDefinition
    id
    source_template_id
    target_template_id
    forward_name
    reverse_name
```

Rules:

- `id` is the stable primary identity.
- `source_template_id` and `target_template_id` reference stable
  `ObjectTemplate` identities.
- `forward_name` and `reverse_name` are mandatory semantic identifiers.
- `RelationshipDefinition` is autonomous and not owned by either endpoint
  template.

`RelationshipDefinition` must not contain:

```text
source_template_version
target_template_version
ObjectTemplateVersionRef
```

The definition:

```text
NetworkDevice USES Credential
```

means:

```text
NetworkDevice.template_id
    USES
Credential.template_id
```

not:

```text
NetworkDevice@1 USES Credential@2
```

Publishing new `ObjectTemplateVersion` values must not recreate, migrate,
rebind, or version-copy `RelationshipDefinition`.

## Runtime Relationship Conceptual Model

When runtime graph edges are introduced, the canonical conceptual shape is:

```text
Relationship
    id
    relationship_definition_id
    source_object_id
    target_object_id
```

Rules:

- one stored edge represents both semantic views;
- stored orientation follows the definition's canonical
  `source_template_id -> target_template_id` direction;
- reverse navigation is derived from the same edge through
  `reverse_name`.

Example:

```text
router-01 USES tacacs-prod
```

must also be visible as:

```text
tacacs-prod IS_USED_BY router-01
```

without persisting a second mirrored runtime edge.

## Version Independence

RelationshipDefinition is version-independent.

This means:

- it references stable `ObjectTemplate` identities only;
- it survives new `ObjectTemplateVersion` publication unchanged;
- `ObjectTemplate` and `Object` migration do not migrate RelationshipDefinitions;
- there is no "latest" or "current" Relationship binding.

Version independence does not mean that concrete Objects ignore versioned
inheritance. Objects remain pinned to exact `ObjectTemplateVersion` values, and
that exact pin determines the ancestry used to evaluate whether the Object
qualifies for one endpoint of a version-independent RelationshipDefinition.

## Inheritance Semantics

Relationship definitions are inherited through `ObjectTemplate` inheritance.

Endpoint compatibility is:

```text
candidate compatible with required_template_id iff:

candidate.template_id == required_template_id

OR

some ancestor reached through the candidate's exact pinned
ObjectTemplateVersion parent chain has template_id == required_template_id
```

This rule applies independently to both endpoints.

For:

```text
NetworkDevice USES Credential
```

and:

```text
Router@3 extends NetworkDevice@2
TacacsCredential@2 extends Credential@1
```

all of the following are effective applications of one canonical
RelationshipDefinition:

```text
NetworkDevice USES Credential
Router USES Credential
NetworkDevice USES TacacsCredential
Router USES TacacsCredential
```

with the corresponding inverse views:

```text
Credential IS_USED_BY NetworkDevice
Credential IS_USED_BY Router
TacacsCredential IS_USED_BY NetworkDevice
TacacsCredential IS_USED_BY Router
```

Relationship inheritance must reuse the existing `ObjectTemplate`
inheritance semantics:

- exact stored parent-version traversal;
- missing-parent failure behavior;
- self-inheritance detection;
- inheritance-cycle detection;
- no latest fallback.

No unrelated second ancestry model should be introduced.

## Declared Versus Effective Relationships

The architecture distinguishes:

```text
declared RelationshipDefinitions
```

from:

```text
effective RelationshipDefinitions
```

Declared RelationshipDefinitions are the canonical persisted entities.

Effective RelationshipDefinitions for a concrete pinned
`ObjectTemplateVersion` are the definitions whose endpoint requirement is
satisfied either:

- directly by that template identity; or
- through the template version's exact pinned ancestor chain.

Inherited definitions must not be copied or materialized into descendant
templates. Inheritance is resolved dynamically and effectively.

One declared definition therefore already covers all inheritance-compatible
effective applications inside its source and target endpoint families. Users
must not create another RelationshipDefinition merely to represent one of those
inherited cases.

Relationship applicability is downward through inheritance only. For:

```text
A USES B
```

the definition applies to:

```text
self-or-descendants(A)
    ×
self-or-descendants(B)
```

It does not propagate upward to ancestors. For example, if:

```text
BaseDevice
└── Router
```

then:

```text
Router USES Credential
```

does not imply:

```text
BaseDevice USES Credential
```

The first M2 model is additive only:

- no disabling inherited Relationships;
- no renaming inherited forward semantics;
- no renaming inherited reverse semantics;
- no changing inherited endpoints;
- no version-specific overrides;
- no shadowing semantics.

## Bidirectional / Inverse Semantics

Every RelationshipDefinition has mandatory forward and inverse semantics.

Example:

```text
NetworkDevice USES Credential
Credential IS_USED_BY NetworkDevice
```

These are two semantic views of one canonical RelationshipDefinition, not two
independent definitions.

Forward and reverse semantics can never diverge because they are stored on the
same definition and applied to the same canonical runtime edge.

The repository must therefore prefer one canonical stored orientation and
derive the inverse view rather than persisting mirrored pairs.

## Duplicate Semantics

`RelationshipDefinition` UUID is the primary identity, but semantic duplicate
constraints exist in addition to UUID identity.

These descriptions represent the same definition:

```text
A USES B
B IS_USED_BY A
```

Therefore an attempted creation of:

```text
source=A
target=B
forward_name=USES
reverse_name=IS_USED_BY
```

followed by:

```text
source=B
target=A
forward_name=IS_USED_BY
reverse_name=USES
```

must be recognized as a duplicate of the same canonical semantic definition.

The preferred canonical duplicate comparison is orientation-normalized:

- compare the requested definition in its declared orientation;
- compare the same request in inverse orientation;
- if either matches an existing definition's canonical semantics, reject it as
  duplicate.

Inheritance makes the duplicate rule stricter than exact-endpoint equality.
For one forward/reverse semantic pair, there must not be two
`RelationshipDefinition` values whose effective source endpoint sets overlap
and whose effective target endpoint sets also overlap.

Conceptually:

```text
EffectiveEndpointSet(T) =
    T plus templates/ObjectTemplateVersions
    that qualify as descendants of T through
    exact pinned ancestry
```

For:

```text
A USES B
```

the effective applicability space is:

```text
EffectiveEndpointSet(A) × EffectiveEndpointSet(B)
```

The canonical conflict invariant is:

```text
for two definitions with the same normalized
forward/reverse semantic pair:

conflict iff

source_effective_set_1 ∩ source_effective_set_2 != ∅

AND

target_effective_set_1 ∩ target_effective_set_2 != ∅
```

Therefore, if:

```text
A USES B
```

already exists, and inheritance makes `A1`, `A2`, and `B1` compatible
descendants, all of the following are semantically overlapping and must be
rejected as duplicate definitions:

```text
A1 USES B
A2 USES B
A USES B1
A1 USES B1
A2 USES B1
```

Ancestor definitions must still be inspected during conflict detection because
their descendant applicability may already cover the proposed endpoint. For
example, if:

```text
A USES B
```

already exists and `A1` is a descendant of `A`, then:

```text
A1 USES B
```

must be rejected because it is already covered by the ancestor definition.

The same protection must work in the opposite temporal direction. If:

```text
A1 USES B
```

already exists and `A1` is a descendant of `A`, then:

```text
A USES B
```

must also be rejected, because the two definitions would overlap once the
effective endpoint sets are considered together. This does not mean the child
definition propagates upward. It means the two downward applicability spaces
overlap.

The check must consider both endpoint families simultaneously. Only checking
one endpoint family would miss cases such as:

```text
A1 USES B1
```

followed by:

```text
A USES B
```

when both sides overlap through inheritance.

Equivalent inverse declarations are part of the same conflict space. Thus:

```text
B IS_USED_BY A1
B1 IS_USED_BY A
B1 IS_USED_BY A2
```

must be normalized back to the canonical semantics of:

```text
A USES B
```

before overlap is checked.

Different semantics between the same endpoint identities may coexist:

```text
A USES B
A MANAGES B
A MONITORS B
```

Future runtime duplicate detection follows the same canonical orientation rule.
The eventual uniqueness key is conceptually:

```text
relationship_definition_id
source_object_id
target_object_id
```

after normalizing the request to the definition's canonical direction.

Thus:

```text
router-01 USES credential-01
credential-01 IS_USED_BY router-01
```

represent the same runtime edge.

Because inheritance applicability depends on exact pinned
`ObjectTemplateVersion` ancestry, future implementation must enforce this
uniqueness invariant not only when a `RelationshipDefinition` is created, but
also before publishing an `ObjectTemplateVersion` whose new parent ancestry
would introduce overlap between existing definitions.

Example:

```text
Router USES Credential
NetworkDevice USES Credential
```

may be valid while `Router` is unrelated to `NetworkDevice`. If publishing:

```text
Router@2 extends NetworkDevice@3
```

would cause those two definitions to overlap through inheritance, publication
must be rejected before that ancestry becomes effective.

This safeguard must evaluate exact pinned ancestry rather than "latest"
template versions so that historical usable version pins remain semantically
correct.

## RelationshipDefinition Identity / Type

`RelationshipDefinition` has its own stable UUID identity.

That UUID is also the canonical relationship type/definition identity for the
initial model.

No additional speculative `RelationshipType` hierarchy is introduced.

The forward and reverse names provide human and API semantics for each
navigation direction, while the definition UUID remains the stable identity
used by repositories and future runtime edges.

## Same-Template and Self Decisions

The generic core permits same-template definitions:

```text
NetworkDevice CONNECTS_TO NetworkDevice
```

and eventual self-relationships:

```text
Object X CONNECTS_TO Object X
```

The initial architecture does not introduce a generic prohibition on either
same-template endpoint definitions or self runtime edges.

If future domain rules need to restrict particular RelationshipDefinitions,
that policy can be added explicitly later.

## Relationship Names

`forward_name` and `reverse_name` are mandatory user-defined semantic
identifiers.

They should follow the repository's existing identifier-validation conventions
for semantic names where practical, while remaining domain-generic. Examples
include:

```text
USES
IS_USED_BY
CONNECTS_TO
CONNECTED_FROM
```

NETAUTO must not hard-code infrastructure-specific vocabularies or a global
enum of allowed relationship types.

## Lifecycle Semantics

### Object deletion

Runtime Relationships cannot outlive either endpoint Object.

When runtime integration is implemented later:

- deleting an Object must atomically remove all incident runtime Relationship
  edges for that Object;
- this is referential cleanup only;
- deleting one endpoint must never imply deleting the other endpoint Object.

Example:

```text
A USES B
```

Deleting `A` means:

```text
delete A
delete edge A USES B
preserve B
```

This remains distinct from component ownership, where deleting a parent Object
deletes its owned component subtree.

For subtree deletion, any runtime Relationship edge incident to an Object that
is actually deleted must eventually be removed atomically with that deletion.
The graph edge is cleaned up; unrelated endpoint Objects survive.

### RelationshipDefinition deletion

The initial architectural preference is restrictive deletion:

```text
RelationshipDefinition with existing runtime Relationship instances
    -> deletion rejected
```

The system should not silently cascade-delete arbitrary graph data merely
because its definition was removed.

### ObjectTemplate deletion

A RelationshipDefinition cannot remain valid if one of its referenced
`ObjectTemplate` identities is deleted.

The initial principle is referential integrity rather than dangling
definition endpoints. The exact destructive workflow can be designed later when
ObjectTemplate deletion lifecycle semantics are mature enough to implement it
safely.

## Composition Versus Relationship

Relationships are explicitly distinct from component composition.

### Composition

```text
ObjectTemplateVersion
    component slot -> ObjectTemplate identity

Object
    owns component Object
```

Semantics:

- ownership;
- named slot;
- one owner per component;
- effective-template validation;
- ownership-cycle detection;
- attach/detach workflows;
- subtree deletion.

### Relationship

```text
ObjectTemplate identity
    <-> RelationshipDefinition <->
ObjectTemplate identity

Object identity
    <-> Relationship <->
Object identity
```

Semantics:

- no ownership;
- no component slots;
- no single-owner constraint;
- no subtree semantics;
- stable identity-level definition;
- inherited endpoint applicability;
- forward and reverse semantic views;
- one canonical stored definition and one canonical stored runtime edge.

Neither mechanism should internally reuse the persistence or lifecycle
semantics of the other.

## Alternatives Considered

### Versioned RelationshipDefinition endpoints

Rejected because it would couple graph semantics to schema-version churn and
would require rebinding or recreating definitions when new
`ObjectTemplateVersion` values are published.

### Mirrored forward and reverse definitions

Rejected because it would allow semantic divergence between the two directions,
complicate duplicate detection, and create redundant persistence.

### Mirrored runtime edges

Rejected because inverse navigation is a view over the same semantic edge, not
an independent relationship.

### Exact-template-identity-only applicability

Rejected because ObjectTemplate inheritance already establishes semantic
compatibility across descendants, and Relationship applicability must follow
that exact pinned ancestry on both endpoints.

### Treating Relationships as component ownership

Rejected because Relationships are peer graph edges without ownership, slot,
single-owner, or subtree-delete semantics.

### Introducing Relationship properties in the first design

Rejected because the first M2 scope is graph structure and semantics only.
Relationship metadata can be designed later when there is a concrete
requirement.

## Consequences

- Relationship definitions remain stable across template-version publication and
  Object migration.
- Effective applicability depends on exact pinned inheritance without making
  definitions versioned.
- One canonical stored definition and one canonical stored edge simplify
  inverse navigation and duplicate detection.
- Relationship lifecycle stays clearly separated from component ownership and
  subtree deletion.
- Future repositories, application services, REST routes, and CLI commands can
  implement Relationship behavior without reopening the identity/versioning
  architecture.

## Deferred Capabilities / Non-Goals

This ADR intentionally defers:

- Relationship domain implementation;
- repositories and Unit of Work changes;
- SQLAlchemy models and migrations;
- REST schemas and routes;
- CLI commands;
- effective Relationship resolver code;
- Relationship properties or metadata;
- Relationship overrides;
- shortest-path algorithms;
- reachability or transitive closure;
- recursive graph traversal APIs;
- topology calculations;
- path-query DSLs;
- graph database integration;
- inferred or discovered Relationships;
- deletion workflow implementation.

For the initial M2 scope, "graph" means:

```text
ObjectTemplate identity nodes
    connected through RelationshipDefinitions

Object identity nodes
    connected through Relationship instances
```

with inheritance-aware endpoint compatibility and bidirectional navigation.
