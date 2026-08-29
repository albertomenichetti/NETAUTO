# M4 WIP — Object component persistence consolidated discovery

**Status:** ACTIVE CROSS-OPERATION CONSOLIDATION / M4 WIP / ALWAYS NON-NORMATIVE

## Purpose

This document is the consolidated working owner for the M4 Object component/ownership persistence boundary during discovery.

It owns the current cross-operation candidate for:

```text
object_component_slots
object_components
```

including:

```text
semantic/data-plane responsibilities
materialized fields and deliberately omitted fields
logical identities and invariants
Object lifetime relationship
edge -> current semantic-slot dependency
cross-operation maintenance/read consequences
PostgreSQL FK-arbitration evidence
storage/write trade-off
migration/backfill direction
architecture handoff
```

It does **not** own the public Object routes; those are consolidated in [`object.md`](object.md).

It also does not freeze the final physical relational schema. Exact DDL, PRIMARY KEY vs UNIQUE realization, final index set, constraint names, migration mechanics, `EXPLAIN` evidence and storage/write measurements belong to the later M4 architecture phase.

Everything under `wip/` remains non-normative. This file is a discovery checkpoint only.

# 1. Baseline and materialization challenge

Delivered persistence separates intrinsic Object state from ownership facts:

```text
objects
    id
    canonical_name
    template_id
    template_version
    properties

object_components
    child_object_id
    parent_object_id
    slot_name
```

Keeping ownership outside `objects.properties` remains desirable because ownership needs independent relational constraints, reverse lookup, cycle admission and lifetime blocking.

The first M4 improvement enriched the edge with stable slot semantic identity:

```text
object_components
    child_object_id
    parent_object_id
    slot_declaring_template_id
    slot_name
```

That solved repeated reconstruction for existing edges but left empty effective slots exclusively in model-plane knowledge.

Later Object GET, component navigation and ATTACH discovery exposed a repeated current data-plane question:

```text
slot absent
!=
slot present but empty
```

and a repeated need for the current slot target lineage during ATTACH.

The supplied workload direction also matters:

```text
Object.SCHEMA_CHANGE : Object.ATTACH
    approximately 1 : 100
```

The current preferred discovery direction therefore moves bounded slot-contract maintenance to Object CREATE / SCHEMA_CHANGE so frequent reads and ATTACH can consume current data-plane facts directly.

# 2. Candidate runtime layering

```text
objects
    = current intrinsic Object state
      + current exact ObjectTemplate binding

object_component_slots
    = owned derived current effective component-slot contract
      for one Object

object_components
    = factual current child membership
      constrained to current semantic slots
```

ObjectTemplate exact effective schema remains the semantic/model-plane authority.

`object_component_slots` is **not** a second model authority. It is a transactionally maintained per-Object runtime derivative of the current exact ObjectTemplateVersion.

# 3. `object_component_slots` logical shape

Current preferred logical fields:

```text
object_component_slots
    object_id                    NOT NULL
    slot_declaring_template_id   NOT NULL
    slot_name                    NOT NULL
    target_template_id           NOT NULL
```

One row exists for every component slot effective for the Object's current exact ObjectTemplateVersion, including slots with zero current children.

Meaning:

```text
one row
    = Object O currently exposes this semantic slot
      and this is its current target-lineage admission contract
```

## Why `target_template_id` is materialized

A minimal existence materialization would stop at:

```text
object_id
slot_declaring_template_id
slot_name
```

The current stronger candidate includes:

```text
target_template_id
```

because ATTACH consumes it on every child-lineage compatibility admission, while normal target evolution is rare and monotonic widening toward an ancestor lineage.

Trade-off:

```text
rare SCHEMA_CHANGE
    -> update affected current slot target

frequent ATTACH
    -> read target_template_id directly
    -> no exact component-schema cache lookup/fill merely for slot resolution
```

## Fields deliberately not materialized

Current discovery does not justify copying:

```text
effective ordinal / position
parent template_id
parent template_version
slot_declaring_template_version
child canonical_name
components JSONB
```

Reasons:

```text
position
    -> no identified runtime contract consumes slot ordering
    -> position-only schema evolution should not create runtime slot writes

parent exact binding
    -> already authoritative on objects

slot_declaring_template_version
    -> not part of stable slot semantic identity
    -> would become stale or require unnecessary edge/slot rewrites

child canonical_name
    -> mutable current child Object state
    -> remains authoritative on objects

components JSONB
    -> would collapse independently constrained relational ownership
```

If a later runtime contract genuinely needs slot ordering, position can be reopened rather than pre-materialized speculatively.

# 4. Slot identities and logical uniqueness

Two identities matter and must remain unambiguous.

Public/current lookup identity:

```text
(object_id, slot_name)
```

Stable current semantic identity:

```text
(object_id, slot_declaring_template_id, slot_name)
```

The persistence design must enforce both logical uniqueness properties:

```text
one current semantic slot row per
    (object_id, slot_declaring_template_id, slot_name)

one current effective slot under a public name per Object
    (object_id, slot_name)
```

The architecture phase decides which unique key is declared PRIMARY KEY and which remains UNIQUE; discovery requires the uniqueness semantics, not a particular DDL spelling.

`slot_declaring_template_id` is intentionally part of semantic identity. Same-name replacement under a different declaring lineage is a different slot rather than continuity by name alone.

# 5. Fundamental derived-state invariant

For every current Object `O`:

```text
MaterializedSlots(O)
    ==
EffectiveComponentSlots(
        O.template_id,
        O.template_version
    )
```

For every materialized slot row:

```text
slot_declaring_template_id
slot_name
target_template_id
```

must equal the corresponding certified exact effective component-slot contract.

Atomic visibility requirement:

```text
Object exact binding
+
complete current object_component_slots set

must become visible atomically
```

No committed state may expose:

```text
new objects.template_version + old slot set
or
old objects.template_version + new slot set
```

The normal hot read path does not re-certify this invariant against model-plane schema. Correctness belongs to maintenance protocol, relational constraints where applicable, migration/backfill verification and deterministic tests/evidence.

# 6. `object_components` factual edge

Current logical edge candidate:

```text
object_components
    child_object_id              NOT NULL
    parent_object_id             NOT NULL
    slot_declaring_template_id   NOT NULL
    slot_name                    NOT NULL
```

The edge persists the stable semantic slot identity already resolved at ATTACH admission rather than discarding it after validation.

## Stable identity, not declaring version

Current ownership continuity uses:

```text
(slot_declaring_template_id, slot_name)
```

not an exact declaring ObjectTemplateVersion.

Persisting `slot_declaring_template_version` would either leave stale exact-version provenance after parent schema evolution or require rewriting unchanged ownership facts. Historical exact declaration provenance, if ever required, belongs to lifecycle/history rather than current edge identity.

## Single owner and child lifetime

Required logical guarantees remain:

```text
child_object_id
    -> at most one current ownership edge

child Object must remain alive while referenced

parent_object_id != child_object_id
    -> relational self-edge backstop
```

The delivered/current `child_object_id` primary-key direction remains the natural candidate because owner lookup, ownerlessness admission and upward ownership traversal are child-rooted.

# 7. Edge -> current semantic-slot dependency

Current strong relational candidate:

```text
(parent_object_id, slot_declaring_template_id, slot_name)
    ->
object_component_slots(
    object_id,
    slot_declaring_template_id,
    slot_name
)
```

Required semantic guarantee:

```text
an ownership edge may exist only through a slot
that currently exists on that parent Object
under the same semantic slot identity
```

This dependency is the key reason to materialize semantic slot identity on both current slot and edge rows.

## Direct parent Object FK — OPEN

If:

```text
object_component_slots.object_id -> objects.id
```

and every edge references a current slot row, parent existence/lifetime is already implied transitively.

Therefore a separate:

```text
object_components.parent_object_id -> objects.id
```

may duplicate an invariant and add another FK check on ATTACH.

Architecture must retain it only if it proves a distinct lifetime/arbitration or physical-planning benefit.

## Direct model-plane FKs — OPEN

Potential direct FKs from:

```text
slot_declaring_template_id
target_template_id
```

to ObjectTemplate lineage rows remain open.

Possible benefit:

```text
local corruption prevention / explicit referential integrity
```

Possible cost:

```text
duplicate lifetime blockers already guaranteed through certified exact schema
additional write/check cost
additional low-level delete interactions
```

The final lifetime graph must decide this globally.

# 8. Slot lifetime and Object DELETE

Slot rows are owned derived state of the Object, not independent current facts that should keep the Object alive.

Candidate ownership relation:

```text
object_component_slots.object_id
    -> objects.id
    ON DELETE CASCADE
```

Combined with edge -> slot RESTRICT/NO-ACTION-equivalent behavior:

```text
Object with only empty slots
    -> owned slot rows disappear with Object
    -> slot materialization does not block DELETE

Object with attached children
    -> referenced slot row cannot disappear
    -> root Object DELETE remains blocked
```

This preserves the semantic rule that Object DELETE never implicitly DETACHes children.

Exact FK actions/spelling remain architecture DDL.

# 9. PostgreSQL arbitration evidence

The current composite edge-to-slot FK is not only referential integrity; it is also a candidate narrow concurrency rendezvous for slot continuity.

PostgreSQL referential-integrity checking of an edge INSERT protects the referenced key in a way equivalent to key-share semantics:

```text
referenced current slot key
    (object_id, slot_declaring_template_id, slot_name)

DELETE referenced row
    -> conflicts

UPDATE referenced key values
    -> conflicts

ordinary non-key UPDATE
    -> need not conflict merely because the row is referenced
```

This aligns with the semantic split required by normal schema evolution.

## Slot REMOVE

```text
SCHEMA_CHANGE removes slot first
    -> later ATTACH cannot satisfy the current-slot FK

ATTACH edge commits first
    -> referenced slot cannot be removed while the edge remains
```

## Same-name semantic replacement

Replacement changes:

```text
slot_declaring_template_id
```

which participates in the semantic referenced key.

Therefore an existing edge cannot be silently reinterpreted under a new declaring lineage:

```text
old slot referenced
    -> semantic key change/removal cannot complete

old slot unreferenced
    -> semantic replacement may proceed
```

## Target widening

Normal target evolution changes only:

```text
target_template_id
```

which is deliberately not part of the edge referenced key.

This permits the relational realization to avoid treating every target widening as an ownership-identity conflict.

Semantically this is safe because widening moves from a narrower descendant target to an ancestor target; every child admitted under the old target remains admissible under the wider target.

Therefore:

```text
parent template_version changed
    !=
ATTACH must fail
```

Only actual slot removal or semantic identity replacement must arbitrate with edge insertion.

## DETACH

DETACH removes the referencing edge:

```text
DETACH commits first
    -> last reference may disappear
    -> slot REMOVE/replacement may proceed

slot transition reaches FK arbitration while edge remains
    -> invalid removal/key change cannot commit
```

This evidence supports removing route-local parent-binding stabilization whose only purpose was semantic slot continuity.

It does **not** prove the complete global concurrency architecture.

Still open globally:

```text
deadlock freedom
full lock/wait-for ordering
Object DELETE composition
graph-write gate composition
final transaction/isolation shapes
constraint failure -> public error mapping
```

# 10. Cross-operation consequences

Public/route-local details remain owned by `object.md`; this section records only persistence consequences.

## CREATE

For new Object bound to exact `(T,V)`:

```text
INSERT Object
+
materialize one slot row for every certified
object_template_effective_components(T,V) row
```

Preferred logical direction is bounded DB-internal copy from immutable certified effective components, in the final Object-admission transaction.

No ownership edge is created by CREATE.

Additional row work is approximately:

```text
+ S slot writes
```

where `S` is effective slot count.

## GET Object

Current data-plane sources become:

```text
objects
object_component_slots
object_components
objects child
```

The route can obtain current root + complete slots + current children in one statement snapshot without component-schema cache/model-plane read.

## GET one component slot

Current slot existence/identity is looked up directly by:

```text
(object_id, slot_name)
```

and current membership is paged from `object_components` using the resolved semantic slot identity.

This directly distinguishes:

```text
parent absent
slot absent
slot present + empty
slot present + children
```

without exact-schema reconstruction.

## GET owner

Reverse ownership remains child-rooted at `object_components.child_object_id`.

Persisted semantic edge identity removes the need to reconstruct ObjectTemplate ancestry solely to describe the current owner edge.

## ATTACH

Parent current slot lookup supplies directly:

```text
slot_declaring_template_id
target_template_id
```

The edge INSERT then references that current semantic slot row.

This removes the preferred normal need for:

```text
parent exact-template pin solely for slot resolution
component-schema cache lookup/fill
parent exact-binding recheck solely for semantic slot continuity
```

Stable child-lineage ancestry validation remains independently useful.

## DETACH

DETACH removes factual edge rows directly and receives semantic identity from the deleted edge itself.

The edge-to-slot dependency narrows SCHEMA_CHANGE sequencing and weakens the need for a generic parent lock used only as slot-transition rendezvous.

## SCHEMA_CHANGE

The immutable SOURCE -> TARGET MigrationPlan maintains current slot delta:

```text
ADD
    -> INSERT current slot row

REMOVE
    -> DELETE current slot row
    -> referenced-edge dependency is final blocker authority

continuous target widening
    -> UPDATE target_template_id

semantic replacement
    -> key-changing slot_declaring_template_id update
       + target_template_id as required
    -> blocked while old semantic edges remain

position-only change
    -> no slot-row DML
```

Existing `object_components` membership remains unchanged on every successful normal schema migration.

This also reopens the earlier need to include outgoing ownership membership in the optimistic SCHEMA_CHANGE fingerprint: preserved/widened membership no longer needs to invalidate a prepared candidate merely because ATTACH/DETACH happened, while REMOVE/replacement races are arbitrated at the current slot dependency.

The exact intrinsic fingerprint and UoW realization belong to `object-schema-change.md`.

## Object DELETE

Object DELETE gains owned slot-row cascade work proportional to current slot count but no required slot precheck or additional route round trip.

Referenced ownership still blocks deletion through the slot dependency.

# 11. Cache boundary

The materialization does **not** delete immutable ObjectTemplate component-schema knowledge as a system capability.

It removes that cache/model-plane dependency from the normal candidates for:

```text
GET Object
GET one component slot
ATTACH slot resolution
DETACH
```

Immutable exact schema and validation caches remain appropriate where a route genuinely performs semantic validation or migration.

General boundary:

```text
current mutable/materialized runtime fact
    -> PostgreSQL data plane

immutable semantic interpretation/certification
    -> certified model materialization + worker-local cache where useful
```

# 12. Storage and workload trade-off

Let:

```text
O = number of current Objects
S = average current effective slot count per Object
```

Then materialized slot row count is approximately:

```text
O * S
```

plus supporting indexes/constraints.

This is the principal structural cost of the candidate.

Additional mutation work includes:

```text
CREATE
    -> materialize S initial slot rows

SCHEMA_CHANGE
    -> maintain only changed slot rows

DELETE
    -> remove/cascade current slot rows
```

Current expected cross-operation benefit includes:

```text
GET Object
    -> pure current data-plane one-statement candidate

GET component slot
    -> pure current data-plane slot existence/page

ATTACH
    -> no component-schema cache for slot resolution
    -> narrower semantic slot arbitration

DETACH
    -> less generic SCHEMA_CHANGE lock coupling

SCHEMA_CHANGE
    -> REMOVE/replacement final arbitration at relational slot boundary
    -> potential reduction of outgoing-edge fingerprint/retry coupling
```

The approximate `SCHEMA_CHANGE : ATTACH ~= 1 : 100` workload input supports shifting bounded work toward the rare mutation, but it is an explicit discovery assumption rather than a product guarantee.

Exact byte footprint and write amplification must be measured before architecture freeze.

# 13. Migration/backfill direction

After certified exact effective-component materialization exists, current slot rows can be backfilled conceptually from:

```text
objects O
JOIN object_template_effective_components E
  ON E.template_id      = O.template_id
 AND E.template_version = O.template_version
```

producing:

```text
object_id
slot_declaring_template_id
slot_name
target_template_id
```

Existing ownership edges must then be verified/backfilled so every edge references **exactly one** current semantic slot row.

Required migration invariant:

```text
every existing edge
    -> exactly one current slot row
```

Zero or multiple matches are corruption/migration failure and must not be repaired by inventing an identity.

Exact migration ordering, validation SQL, constraint-validation strategy and lock impact belong to architecture/migration design.

# 14. Physical-design architecture handoff

Discovery requires the logical access paths and invariants above. It does not ratify the final physical schema.

The existing exploration produced the following **non-ratified architecture input**:

```text
possible slot semantic key
    (object_id, slot_declaring_template_id, slot_name)

required alternate current-name uniqueness
    (object_id, slot_name)

edge single-owner key
    child_object_id

possible parent/semantic-slot page + FK-support B-tree
    (parent_object_id,
     slot_declaring_template_id,
     slot_name,
     child_object_id)
```

This candidate attempts to cover:

```text
current slot lookup by (object_id, slot_name)
all slots for one Object
edge FK referenced/referencing work
GET Object parent fan-out
one-slot child_id keyset pagination
GET owner / ownerlessness / upward traversal by child id
```

without adding route-local duplicate indexes.

The same exploration currently sees no demonstrated need for:

```text
third slot index
target_template_id search index
INCLUDE payloads
copied child canonical_name
```

and prefers semantic composite identity over a surrogate `slot_id` while there is no measured storage/write reason to add indirection.

These are architecture inputs, **not discovery-final physical decisions**. They must be reopened if final DDL/query shapes or measurements favor another realization.

## Required architecture evidence

Before architecture freeze, verify with final TO-BE schema/query shapes and representative cardinalities at least:

```text
component navigation first/continuation page
empty and absent slot
stale semantic cursor gating
GET Object representative fan-out
slot DELETE / semantic-key UPDATE with zero/non-zero references
FK reverse-reference behavior
slot/edge index size
ATTACH/DETACH write cost
CREATE/SCHEMA_CHANGE slot maintenance cost
```

Use `EXPLAIN (ANALYZE, BUFFERS)` or the project-approved equivalent where appropriate.

The evidence goal is bounded/selective production-shaped work, not forcing a particular PostgreSQL plan-node spelling on tiny fixtures.

# 15. Current open points

Discovery-level logical candidate is strong, but architecture must still close:

```text
exact PK vs UNIQUE declaration
exact FK actions and constraint set
whether direct parent Object FK remains
whether direct model-plane lineage FKs remain
final index keys/order
surrogate slot-id alternative if measurements justify it
migration/backfill mechanics
constraint failure mapping
complete transaction/lock/wait-for graph
storage/write measurements
final plan evidence
```

Downstream Object SCHEMA_CHANGE consolidation must also revalidate the old outgoing-ownership fingerprint assumptions against this boundary.

# 16. Consolidation sources

This first consolidated version absorbs current findings from at least:

```text
object-component-slots-data-plane-materialization.md
object-components-physical-schema-discovery.md
object-component-slots-fk-arbitration.md
object-components-physical-index-candidate.md
object-components-runtime-schema-discovery.md
object-components-reads-discovery.md
```

Route-specific consequences are summarized here only to explain cross-operation value; `object.md` remains the route owner.

The older source WIPs remain temporarily in the tree until a lossless comparison pass and the `object-schema-change.md` consolidation are complete. Git history remains the historical record after cleanup.
