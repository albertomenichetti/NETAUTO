# Relationship — Current AS-IS

## Responsibility

The current Relationship model separates four concepts:

```text
RelationshipDefinition
    -> stable identity and structural classification of a relationship type

RelationshipResolution
    -> model-plane resolved semantic perspective

Relationship
    -> factual runtime association identity

RuntimeRelationshipResolution
    -> concrete object-relative resolved access path
       for a factual Relationship
```

A complete RelationshipDefinition is an aggregate composed of its header plus the complete Resolution set. A complete factual Relationship is an aggregate composed of its header plus the complete runtime-resolution closure.

## Identity generation

Current domain identities are opaque kernel/application-generated UUIDv4 values:

```text
RelationshipDefinition.id
RelationshipResolution.id
Relationship.id
```

They are not caller-supplied and are immutable after creation.

`RelationshipResolution.id` remains stable across Definition rename. `Relationship.id` identifies the factual association, not one resolved view.

RuntimeRelationshipResolution has no surrogate identity; its exact resolved-view tuple is authoritative.

## Resolved-graph principle

Interpretation complexity is paid on the model plane.

RelationshipDefinition CREATE/RENAME:

- construct or re-certify the complete Resolution set;
- preserve the required symmetric/non-symmetric shape;
- validate semantic equivalence;
- validate cross-Definition Resolution conflicts;
- persist a completely resolved model contract atomically.

Runtime Relationship CREATE/DELETE consume the certified contract. They do not reinterpret source/target or forward/reverse semantics.

## No privileged source/target orientation

The current domain model does not define:

```text
source_template
target_template
forward_name
reverse_name
```

A non-symmetric Definition has two endpoint perspectives. Neither is inherently "forward".

Example:

```text
VM         -> Hypervisor / is_hosted_by
Hypervisor -> VM         / hosts
```

## RelationshipDefinition

A Definition has stable:

```text
id
symmetric
```

`id` is the authoritative relationship-type identity. `symmetric` is immutable structural contract.

Definition mutation operates on the complete aggregate; Resolution child state is not an autonomous public CRUD/lifecycle resource.

### Non-symmetric shape

`symmetric=false` requires exactly two reciprocal perspectives:

```text
R1.from_template_id == R2.to_template_id
R1.to_template_id   == R2.from_template_id
R1.name             != R2.name
```

The rule also applies when both endpoint lineages are the same.

### Symmetric shape

`symmetric=true` has one semantic name.

- same-template endpoints -> one Resolution;
- different-template endpoints -> two reciprocal Resolutions with the same name.

Endpoint references are stable ObjectTemplate lineages, never exact ObjectTemplateVersions.

Changing symmetry, endpoint lineage, Resolution membership or cardinality defines a different relationship type and therefore requires a new Definition.

## RelationshipResolution

A Resolution has stable:

```text
id
relationship_definition_id
from_template_id
to_template_id
```

and mutable non-key `name` metadata.

Name grammar:

```text
[a-z][a-z0-9_]*
maximum length = 64
```

No automatic normalization is applied.

`name` is not identity. A rename preserves `RelationshipResolution.id`.

`name` must not become a key-changing persistence identity. In particular, the current architecture does not make this tuple a business/FK-referencable key:

```text
(relationship_definition_id, from_template_id, to_template_id, name)
```

The complete Definition candidate must remain free of duplicate semantic child tuples and satisfy the symmetry rules.

## Capability applicability

A Resolution `R` is applicable as a from-perspective to a stable ObjectTemplate lineage `T` iff:

```text
T == R.from_template_id
OR
T is descendant of R.from_template_id
```

The expected related endpoint compatibility space is `R.to_template_id`, also lineage-polymorphic.

Capability applicability depends on stable lineage ancestry only. It does not depend on:

- exact ObjectTemplateVersions;
- ObjectTemplate default state;
- availability of a current PUBLISHED version;
- Object exact schema version or property state.

The ObjectTemplate relationship-capability projection exposes:

```text
resolution_id
relationship_definition_id
name
from_template_id
to_template_id
```

`from_template_id` remains explicit because the applicable capability may be declared on an ancestor space.

## Definition equivalence and conflict freedom

The committed model-plane Definition set must satisfy both:

### Semantic uniqueness

Two Definitions with the same `symmetric + complete semantic Resolution set` cannot coexist.

### Cross-Definition conflict freedom

Resolution perspectives from distinct Definitions conflict when:

```text
same name
AND
from-lineage spaces overlap
AND
to-lineage spaces overlap
```

With single stable ObjectTemplate inheritance, spaces overlap when lineages are equal or one is an ancestor/descendant of the other.

Resolutions inside the same Definition are not evaluated as cross-Definition conflicts; their overlap may be intentional and is handled by runtime closure semantics.

Definition CREATE and RENAME operate against a globally certified set and are serialized through the concurrency contract.

Definition DELETE removes a member of that set and cannot introduce a new equivalence/conflict by itself.

## Factual Relationship

A factual Relationship has authoritative stable identity:

```text
relationship_id
```

and stable binding to one `relationship_definition_id`.

A factual association is not publicly identified by an endpoint tuple. Successful CREATE either creates a new factual identity or converges on an already-current factual Relationship representing the same semantic fact.

Public CREATE is expressed by:

```text
resolution_id
from_object_id
to_object_id
```

The selected Resolution determines the requested semantic perspective.

Endpoint admission depends only on stable `Object.template_id` lineage compatibility. Exact ObjectTemplateVersion, Object property state, canonical name, ownership, template default state and OTV lifecycle do not determine runtime Relationship validity.

## Factual endpoint semantics

### Non-symmetric

The selected Resolution determines endpoint roles and the assignment is not interchangeable.

For reciprocal perspectives `R1` and `R2`:

```text
R1 / A -> B
```

represents the same fact as:

```text
R2 / B -> A
```

but is a different fact from:

```text
R1 / B -> A
```

unless the actual endpoint assignment is the same self-pair and the Definition semantics make it so.

### Symmetric

The factual pair is unordered semantically. Any applicable Resolution/assignment expressing the same unordered pair converges on the same factual Relationship.

### Self-loop

A factual pair `(A, A)` is allowed when lineage admission permits it. Self-loop is not structurally forbidden.

## Deterministic complete runtime closure

Every factual Relationship materializes the deterministic **complete set** of exact object-relative resolved views required by its Definition.

Every runtime row must satisfy:

- its Resolution belongs to the same Definition as the Relationship header;
- it uses only the one factual Object pair;
- from/to Objects satisfy stable-lineage compatibility for the selected Resolution;
- the complete required closure is present, not a subset;
- each exact resolved view is globally unique.

Exact resolved-view identity:

```text
(resolution_id, from_object_id, to_object_id)
```

There is no surrogate runtime-resolution row identity.

### Non-symmetric closure

Given selected perspective `R1` and input `A -> B`, with reciprocal `R2`, the complete closure is:

```text
R1 / A -> B
R2 / B -> A
```

If `A == B`, two rows remain when `R1 != R2`.

No additional inverse assignments are added merely because inheritance overlap makes them type-compatible; those would represent the opposite factual relationship.

### Symmetric closure

For unordered pair `{A, B}`, the closure is the set of all distinct tuples:

```text
(resolution_id, from_object_id, to_object_id)
```

obtained from every model Resolution and both assignments `(A,B)` / `(B,A)` that satisfy the respective lineage predicates.

Consequences:

- same-template, `A != B`: two runtime rows using the same Resolution ID;
- same-template self-loop: one runtime row;
- different-template disjoint spaces: normally two reciprocal rows;
- different-template overlapping spaces: up to four rows;
- current closure remains bounded because a Definition owns at most two model Resolutions.

## Runtime CREATE semantics

Conceptual pipeline:

```text
load selected Resolution
load endpoint Objects
validate selected perspective admission
lookup exact current resolved view

if present:
    return current factual Relationship
    no mutation
    no lifecycle event set

if absent:
    load the complete certified Definition Resolution set
    derive deterministic complete closure
    validate complete candidate
    ensure no exact view belongs to another factual Relationship
    insert Relationship header
    insert complete closure
    insert complete required lifecycle event set
    commit atomically
```

Concurrent equivalent CREATE candidates may collide on exact-view uniqueness. A colliding candidate rolls back the entire Unit of Work and restarts the semantic operation in a fresh Unit of Work.

Fresh re-evaluation either:

- converges on the current winner; or
- creates a new factual identity if the previous fact has already been deleted.

No row-by-row partial `ON CONFLICT DO NOTHING` creates a partial aggregate.

## Runtime DELETE semantics

Relationship DELETE targets exact `relationship_id`.

Deletion is idempotent on absence for this specific operation.

A late `DELETE(X)` never deletes a semantically equivalent Relationship `Y` recreated after X was removed. This preserves exact-ID ABA safety.

A real deletion atomically removes:

```text
Relationship header
+
complete runtime-resolution child closure
+
complete required lifecycle event set
```

## RelationshipDefinition and Object delete safety

A RelationshipDefinition cannot be deleted while any current factual Relationship references it.

An Object cannot be deleted while any current factual Relationship includes it.

Current runtime references use non-cascading lifetime protection. Definition/Object deletion never implicitly removes factual Relationships.

Relationship is not ownership:

- no single-owner rule;
- no ownership acyclicity rule;
- no subtree/delete-composition semantics;
- no implicit Relationship removal during Object delete.

## Lifecycle events

A real factual transition produces one lifecycle event for every distinct object-relative **semantic view**, not mechanically one event for each raw runtime row.

The complete event set is atomic with the factual mutation and runtime closure change.

Relationship names and Object display names captured in history are historical metadata, not live referential dependencies.

When a transition races with mutable Definition/Object naming metadata, the complete event set is derived from coherent committed metadata observations. It must not mix half-old and half-new Definition naming state.

## Read projections

```text
RelationshipDefinition GET
    -> header + complete Resolution aggregate

Relationship GET
    -> factual aggregate + distinct semantic views[]

Object relationships
    -> deduplicated ObjectRelationshipView

ObjectTemplate relationship-capabilities
    -> applicable Resolution-based semantic capabilities
```

Raw RuntimeRelationshipResolution rows are persistence realization and are never the public Relationship representation.

Inheritance overlap must not create duplicate public semantic views.

## Modelling guideline

A capability should be declared on the most general template space for which the semantics is correct for all descendants:

```text
highest semantically correct,
lowest necessary
```

Do not duplicate specialized Definitions solely to narrow a compatibility space already represented correctly by lineage polymorphism.

## Current evolution boundary

The current model does not include:

```text
RelationshipDefinitionVersion
Relationship properties
exact DefinitionVersion pin on factual Relationship
parallel multi-edge factual instances distinguished by properties
```

A future typed-property evolution may introduce a versioned property schema, but it must not silently reinterpret the stable topology/navigation contract (`symmetric`, Resolution set, endpoint lineage spaces) without explicit architecture change.

## Key invariants

- Definition, Resolution and factual Relationship identities are kernel-generated UUIDv4 and stable;
- Definition symmetry is immutable;
- Resolution identity remains stable independently of mutable `name`;
- Resolution names follow the frozen lowercase grammar and are non-key metadata;
- Resolution endpoints are stable ObjectTemplate lineages;
- capability applicability is lineage-polymorphic and independent of exact OTV lifecycle/default state;
- symmetric/non-symmetric aggregate shape is complete and valid;
- the committed Definition set is semantically non-duplicated and cross-definition conflict-free;
- runtime mutation consumes certified model semantics rather than reinterpreting them;
- factual Relationship identity and Definition binding are stable;
- every runtime row belongs to the same Definition as its Relationship header;
- every factual Relationship has exactly its deterministic complete runtime-resolution closure;
- exact resolved views are unique;
- runtime endpoint admission depends on stable ObjectTemplate lineage compatibility;
- Relationship has no ownership semantics;
- CREATE convergence creates no duplicate fact/event set;
- DELETE is exact-ID based and ABA-safe;
- current Definition/Object deletion is blocked by factual references;
- factual transitions and required lifecycle event sets are atomic;
- supported concurrent interleavings preserve all invariants above.