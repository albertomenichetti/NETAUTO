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

`symmetric=false` requires exactly two reciprocal semantic perspectives with distinct names.

Conceptually:

```text
A -> B / name_1
B -> A / name_2
```

### Symmetric shape

`symmetric=true` has one semantic name.

- same-template endpoints -> one Resolution;
- different-template endpoints -> two reciprocal Resolutions with the same semantic name.

Endpoint template references are stable ObjectTemplate lineages, never exact ObjectTemplateVersions.

## RelationshipResolution

A Resolution has stable:

```text
id
relationship_definition_id
from_template_id
to_template_id
```

and mutable non-key `name` metadata.

`RelationshipResolution.id` is kernel-generated and remains the stable child identity independently of rename.

`name` must not become a key-changing persistence identity. In particular the current architecture does not make `(definition, from_template, to_template, name)` a business/FK-referencable key.

The complete Definition candidate must remain free of duplicate semantic child tuples and satisfy symmetry rules.

## Definition equivalence and conflict freedom

The committed model-plane Definition set must satisfy both:

### Semantic uniqueness

Two Definitions with the same `symmetric + complete semantic Resolution set` cannot coexist.

### Cross-Definition conflict freedom

Resolution perspectives from distinct Definitions cannot expose the same semantic name where their from-lineage spaces and to-lineage spaces both overlap.

Definition CREATE and RENAME therefore operate against a globally certified set and are serialized through the concurrency mechanism described in `concurrency.md`.

Definition DELETE only removes a member of that certified set; it cannot introduce a new equivalence/conflict by itself.

## Factual Relationship

A factual Relationship has authoritative stable identity:

```text
relationship_id
```

and a stable binding to one `relationship_definition_id`.

A factual association is not identified publicly by an endpoint tuple. Successful CREATE either creates a new factual identity or converges on an already-current factual Relationship representing the same semantic fact.

## Runtime resolved closure

For every factual Relationship, the committed runtime-resolution set is the deterministic **complete closure** of the factual Object pair under its Definition.

Every runtime row must satisfy:

- referenced Resolution belongs to the same Definition as the Relationship header;
- all rows represent one factual Object pair, including supported self-pairs;
- from/to Objects satisfy stable-lineage compatibility for the selected Resolution;
- the closure is complete, not a partial set of access paths;
- an exact resolved view is globally unique.

Exact resolved-view identity/uniqueness is:

```text
(resolution_id, from_object_id, to_object_id)
```

There is no surrogate runtime-resolution row identity.

## Runtime CREATE semantics

Public Relationship CREATE is expressed by:

```text
resolution_id
from_object_id
to_object_id
```

The selected Resolution determines the requested semantic perspective.

Endpoint admission depends only on stable `Object.template_id` lineage compatibility. Exact ObjectTemplateVersion, Object property state, template default state and OTV lifecycle do not determine current runtime Relationship validity.

### Symmetric semantics

For symmetric Definitions the endpoint assignment is semantically interchangeable according to the certified Definition shape.

### Non-symmetric semantics

For non-symmetric Definitions the endpoint role expressed by the selected Resolution is preserved and is not interchangeable.

### Self-loop

A factual pair `(A, A)` is allowed when the Definition/Resolution lineage admission permits it. Self-loop is not structurally forbidden by the current model.

### Idempotent convergence

If CREATE discovers that the requested exact/semantic factual view already exists, it returns the current factual Relationship and performs no duplicate mutation or lifecycle-event set.

Concurrent equivalent CREATE operations may race on exact-view uniqueness. One candidate wins; a colliding candidate rolls back its entire Unit of Work and re-evaluates in a fresh transaction. It then either converges on the winner if still current or creates a new factual identity if the previous fact has already been deleted.

## Runtime DELETE semantics

Relationship DELETE targets exact `relationship_id`.

Deletion is idempotent on absence for this specific domain operation.

A late `DELETE(X)` never deletes a semantically equivalent Relationship `Y` that may have been recreated after X was removed. This preserves exact-ID ABA safety.

A real deletion atomically removes:

```text
Relationship header
+
complete runtime-resolution child closure
+
complete required lifecycle event set
```

## RelationshipDefinition delete safety

A RelationshipDefinition cannot be deleted while any current factual Relationship references it.

Current runtime references use non-cascading lifetime protection. Definition deletion never implicitly removes factual Relationships.

## Object delete interaction

An Object cannot be deleted while any current factual Relationship includes it.

Relationship is not ownership:

- no single-owner rule;
- no ownership acyclicity rule;
- no subtree/delete-composition semantics;
- no implicit Relationship removal during Object delete.

## Lifecycle events

A real factual Relationship transition produces one lifecycle event for every distinct object-relative **semantic view**, not mechanically one event for each raw runtime-resolution row.

The complete event set is atomic with the factual mutation and runtime-closure change.

Relationship names and Object display names captured in lifecycle history are historical metadata, not live referential dependencies.

When a Relationship transition races with mutable Definition/Object naming metadata, the complete event set must be derived from coherent committed metadata observations. It must not mix half-old and half-new Definition naming state.

## Read projections

Current public reads expose semantic aggregate/projection state:

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

A relationship capability should be declared on the most general template space for which the semantics is correct for all descendants:

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

A future typed-property evolution may introduce a versioned property schema, but it must not silently reinterpret the stable topology/navigation contract (`symmetric`, Resolution set, endpoint lineage spaces) without an explicit architectural change.

## Key invariants

- Definition identity is stable and symmetry is immutable;
- Resolution identity is stable independently of mutable `name`;
- Resolution endpoints are stable ObjectTemplate lineages;
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
