# Relationship — Current AS-IS

## Purpose and authority

This document owns RelationshipDefinition topology, exact versioned property schemas, factual Relationship state, runtime-resolution closure, commands, reads and lifecycle meaning. Persistence, public transport and concurrency realization belong to their respective current owners.

The current Relationship model separates five concepts:

```text
RelationshipDefinition
    -> stable identity and structural classification of a relationship type

RelationshipResolution
    -> model-plane resolved semantic perspective

RelationshipDefinitionVersion
    -> exact lifecycle-managed property-schema snapshot

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

and a nullable mutable selection policy:

```text
default_version
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

## RelationshipDefinitionVersion

An exact version is identified by:

```text
(relationship_definition_id, version)
```

`version` is a positive lineage-local integer. An exact version contains:

```text
revision
status = DRAFT | PUBLISHED | DEPRECATED
complete ordered property declaration set
```

CREATE atomically creates the stable Definition, its complete Resolution set and
version 1 as `DRAFT`, revision 1. Omitted initial declarations mean an exactly
empty property schema. The initial `default_version` is null.

CREATE_NEXT accepts an exact PUBLISHED or DEPRECATED source, clones its complete
declaration snapshot and allocates `max(existing version) + 1` as a DRAFT at
revision 1. Multiple DRAFT versions may coexist.

REVISE replaces the complete declaration candidate of one exact DRAFT. It
requires the current `expected_revision` and increments the revision exactly
once. PUBLISH and DELETE_DRAFT consume the same generation token. A stale token
is a conflict; there is no merge of DRAFT candidates.

PUBLISH makes an exact DRAFT immutable and usable by direct bindings. The first
serial publication sets a missing default to that exact version. A later
publication does not replace an existing default. SET_DEFAULT accepts only a
same-Definition PUBLISHED version; CLEAR_DEFAULT stores null. The current default
cannot be deprecated. DEPRECATED versions remain historical exact dependencies
but admit no lifecycle-sensitive direct binding. Deprecation is irreversible.

DELETE_DRAFT removes only an exact DRAFT at the expected revision. Definition
deletion removes the whole aggregate only after current reference admission.

### Property declarations

Each declaration has exact semantic identity within the Definition history:

```text
(relationship_definition_id, name)
```

and exact-version physical identity:

```text
(relationship_definition_id, relationship_definition_version, name)
```

A declaration contains:

```text
name
position
datatype_id
datatype_version
value_mode = SCALAR | LIST
```

Names and positions are unique within an exact version; positions are positive
and define projection order. Every declaration pins one exact PUBLISHED
DataTypeVersion through publication and use. Relationship properties are always
optional, and a present value is never null. There is no declaration default,
migration default or required-property state.

After a name first appears in a PUBLISHED version, that name and DataType lineage
are stable across the complete published history. `SCALAR -> LIST` is the only
normal cardinality widening; `LIST -> SCALAR` is rejected. Removing and later
re-adding a name retains the same historical semantic identity and continuity
rules. Publication re-certifies the complete history, including concurrent
publication of distinct versions.

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
- Object exact schema version or property state.

An applicable Resolution becomes an exposed capability only while its Definition
has at least one PUBLISHED exact version. This separates topology applicability
from factual creation eligibility. A null default does not hide the capability;
it requires callers to select an exact PUBLISHED version explicitly.

The ObjectTemplate relationship-capability projection exposes:

```text
resolution_id
relationship_definition_id
name
from_template_id
to_template_id
default_version
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

It also stores current exact factual state:

```text
relationship_definition_version
properties
```

The version pin is a positive exact version of the same Definition. `properties`
is the complete canonical map admitted by that exact schema. Missing optional
properties are absent keys, LIST values are non-empty, and JSON null is invalid.

A factual association is not publicly identified by an endpoint tuple. The
factual identity remains independent of property state and exact version. CREATE
fails with `relationship_fact_conflict` when any exact runtime view is already
owned by a current fact; it never treats the existing fact as a successful CREATE.

Public CREATE is expressed by:

```text
resolution_id
from_object_id
to_object_id
relationship_definition_version, optional
properties, optional complete map
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

Inheritance overlap does not imply additional inverse assignments; those would represent the opposite factual relationship.

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
load the complete certified Definition Resolution set
resolve explicit version or current default
stabilize the exact PUBLISHED version and exact DTV dependencies
canonicalize the complete property map
derive and validate the deterministic complete closure
ensure no exact view belongs to another factual Relationship
insert factual header with exact pin and properties
insert complete closure
insert complete CREATED event set
commit atomically
```

Concurrent candidates may collide on exact-view uniqueness. A colliding Unit of
Work rolls back completely. Fresh classification returns the current owner as a
conflict. If the observed owner disappeared, the operation may restart in a fresh
Unit of Work within the bounded restart policy and rederive the complete fact.

No row-by-row partial `ON CONFLICT DO NOTHING` creates a partial aggregate.

## Factual state mutations

DATA_CHANGE accepts a non-empty set of unique per-property operations:

```text
SET(property, value)
REMOVE(property)
```

It derives a complete canonical map from fresh current state under the current
exact version. `SET` to the current canonical value and removal of an absent key
are semantic no-ops. A wholly no-op command performs no UPDATE and emits no
event. A real change replaces the complete JSONB map atomically, preserves the
version pin and runtime closure, and emits one complete DATA_CHANGE event set.

SCHEMA_CHANGE accepts one explicit, same-Definition, strictly forward PUBLISHED
target version. The source may be PUBLISHED or DEPRECATED. Migration is direct
from source to target: compatible values are preserved and recanonicalized,
SCALAR values widen to one-element LIST values, source-only properties are
removed, and target-only optional properties remain absent. There are no
defaults or caller remediation values. Any incompatible current value produces
`schema_change_blocked` and leaves the fact unchanged. A successful command
updates exact pin and property map in one row, keeps the closure unchanged and
always emits a SCHEMA_CHANGE event, even when the canonical maps are equal.

## Runtime DELETE semantics

Relationship DELETE targets exact `relationship_id`.

An absent exact ID returns `resource_not_found`; deletion is not idempotent on
absence.

A late `DELETE(X)` never deletes a semantically equivalent Relationship `Y` recreated after X was removed. This preserves exact-ID ABA safety.

A real deletion atomically removes:

```text
Relationship header
+
complete runtime-resolution child closure
+
complete DELETED lifecycle event set
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

The Relationship event vocabulary is exactly:

```text
RELATIONSHIP_CREATED
RELATIONSHIP_DATA_CHANGE
RELATIONSHIP_SCHEMA_CHANGE
RELATIONSHIP_DELETED
```

Every event carries factual `before_state` and/or `after_state` with exact shape:

```text
{
  "relationship_definition_version": positive integer,
  "properties": canonical property object
}
```

CREATED has only `after_state`; DELETED has only `before_state`; DATA_CHANGE has
two states with the same exact version and different properties; SCHEMA_CHANGE
has two states with a strictly increasing version.

The complete event set is atomic with the factual mutation and runtime closure change.

Relationship names and Object display names captured in history are historical metadata, not live referential dependencies.

When a transition races with mutable Definition/Object naming metadata, the complete event set is derived from coherent committed metadata observations. It must not mix half-old and half-new Definition naming state.

## Read projections

```text
RelationshipDefinition GET
    -> stable header + complete Resolution aggregate + nullable default

RelationshipDefinitionVersion GET/list
    -> exact lifecycle state + declarations ordered by position

Relationship GET
    -> factual exact pin + canonical properties + distinct semantic views[]

Object relationships
    -> deduplicated ObjectRelationshipView

ObjectTemplate relationship-capabilities
    -> applicable Resolution-based semantic capabilities with nullable default
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

One represented corrupt aggregate fails as `internal_error`. Reads never select a
different version, remove unknown properties, reconstruct closure or return a
partial page. Multi-statement aggregate validation uses one coherent read
snapshot.

## Evolution boundary

Topology and property schema are intentionally separate. Versioning a
RelationshipDefinition changes only its property declaration snapshots; it does
not version symmetry, Resolution membership, Resolution identity or endpoint
lineage spaces. Parallel factual edges are not distinguished by version or
properties, and no autonomous Resolution or property-declaration CRUD exists.

## Key invariants

- Definition, Resolution and factual Relationship identities are kernel-generated UUIDv4 and stable;
- Definition symmetry is immutable;
- Resolution identity remains stable independently of mutable `name`;
- Resolution names follow the frozen lowercase grammar and are non-key metadata;
- Resolution endpoints are stable ObjectTemplate lineages;
- capability applicability is lineage-polymorphic and independent of exact OTV lifecycle/default state;
- capability exposure requires at least one PUBLISHED RelationshipDefinitionVersion;
- exact version declarations are complete, ordered, optional and non-null when present;
- Definition default selection is nullable, explicit and never a latest/highest fallback;
- symmetric/non-symmetric aggregate shape is complete and valid;
- the committed Definition set is semantically non-duplicated and cross-definition conflict-free;
- runtime mutation consumes certified model semantics rather than reinterpreting them;
- factual Relationship identity and Definition binding are stable;
- every factual Relationship pins one exact same-Definition version and one complete canonical property map;
- every runtime row belongs to the same Definition as its Relationship header;
- every factual Relationship has exactly its deterministic complete runtime-resolution closure;
- exact resolved views are unique;
- runtime endpoint admission depends on stable ObjectTemplate lineage compatibility;
- Relationship has no ownership semantics;
- duplicate CREATE reports a factual conflict and creates no duplicate fact/event set;
- DATA_CHANGE no-ops write no state or event; real factual changes are atomic;
- SCHEMA_CHANGE is explicit, forward and preserve-or-fail;
- DELETE is exact-ID based and ABA-safe;
- current Definition/Object deletion is blocked by factual references;
- factual transitions and required lifecycle event sets are atomic;
- supported concurrent interleavings preserve all invariants above.
