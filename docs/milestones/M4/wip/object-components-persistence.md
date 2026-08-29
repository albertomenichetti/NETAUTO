# M4 WIP — Object component persistence consolidated discovery

**Status:** CROSS-OPERATION OWNER CONSOLIDATED / M4 WIP / ALWAYS NON-NORMATIVE

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
Object/slot/edge lifetime relationships
edge -> current semantic-slot dependency
cross-operation maintenance/read consequences
PostgreSQL FK-arbitration evidence
storage/write trade-off
migration/backfill direction
physical-design architecture handoff
```

Public Object routes, including the full-swept SCHEMA_CHANGE and ATTACH routes, are owned by [`object.md`](object.md).

This document does **not** freeze the final physical relational schema. Exact DDL, PRIMARY KEY vs UNIQUE realization, final index set/order, constraint names/actions, migration mechanics, `EXPLAIN` evidence and storage/write measurements belong to the later M4 architecture phase.

Everything under `wip/` remains non-normative. This file is only a discovery checkpoint.

The lossless comparison pass against the current materialization, runtime-schema, physical-schema, FK-arbitration, read-projection and physical-index WIPs is complete. Focused route closures, including SCHEMA_CHANGE and ATTACH, are owned losslessly by `object.md`; Git history remains the historical record for superseded route-local and micro-WIP material.

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

The first M4 improvement enriched the edge with stable semantic slot identity:

```text
object_components
    child_object_id
    parent_object_id
    slot_declaring_template_id
    slot_name
```

That removes repeated ObjectTemplate reconstruction for existing edges, but it still leaves empty effective slots exclusively in model-plane knowledge.

Later Object GET, component navigation and ATTACH discovery exposed repeated data-plane needs to answer:

```text
slot absent
!=
slot present but empty
```

and to retrieve the current slot target lineage for ATTACH.

The supplied workload direction also matters:

```text
Object.SCHEMA_CHANGE : Object.ATTACH
    approximately 1 : 100
```

The preferred discovery direction therefore shifts bounded current-slot maintenance to Object CREATE / SCHEMA_CHANGE so frequent reads and ATTACH can consume current runtime facts directly.

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

`object_component_slots` is **not** a second model authority. It is a transactionally maintained per-Object runtime derivative of the Object's current exact ObjectTemplateVersion.

The intended boundary is:

```text
ObjectTemplate exact effective schema
    -> semantic source

Object CREATE / SCHEMA_CHANGE
    -> materialization boundary

object_component_slots
    -> current runtime derivative

hot reads / ATTACH
    -> direct consumer
```

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

## 3.1 Why `target_template_id` is materialized

A minimal existence materialization could stop at:

```text
object_id
slot_declaring_template_id
slot_name
```

The stronger candidate includes:

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

## 3.2 Fields deliberately not materialized

Current discovery does not justify copying:

```text
effective ordinal / position
parent template_id
parent template_version
slot_declaring_template_version
child canonical_name
components JSONB
```

Rationale:

```text
position
    -> no identified runtime contract consumes slot ordering
    -> position-only schema evolution should not create runtime slot writes

parent exact binding
    -> already authoritative on objects

slot_declaring_template_version
    -> not part of stable slot semantic identity
    -> would become stale or require unnecessary rewrites

child canonical_name
    -> mutable current child Object state
    -> remains authoritative on objects

components JSONB
    -> would collapse independently constrained relational ownership
```

If a later runtime contract genuinely needs deterministic slot ordering, position can be reopened then rather than pre-materialized speculatively.

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

The architecture phase decides which unique key is declared PRIMARY KEY and which remains UNIQUE; discovery requires the uniqueness semantics, not a specific DDL spelling.

`slot_declaring_template_id` is deliberately part of semantic identity. Same-name replacement under a different declaring lineage is a different semantic slot rather than continuity by name alone.

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

For every current slot row:

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

The normal hot read path does not re-certify this invariant against model-plane schema. Correctness belongs to:

```text
write/maintenance protocol
relational constraints where applicable
migration/backfill verification
deterministic tests/evidence
```

# 6. `object_components` factual edge

Current logical edge candidate:

```text
object_components
    child_object_id              NOT NULL
    parent_object_id             NOT NULL
    slot_declaring_template_id   NOT NULL
    slot_name                    NOT NULL
```

The edge persists the stable semantic slot identity already resolved at ATTACH admission instead of discarding it after validation.

## 6.1 Stable identity, not declaring version

Ownership continuity uses:

```text
(slot_declaring_template_id, slot_name)
```

not an exact declaring ObjectTemplateVersion.

Persisting `slot_declaring_template_version` would either:

```text
leave stale exact-version provenance after parent schema evolution
or
force rewrites of ownership facts whose semantic membership did not change
```

Historical exact declaration provenance, if ever required, belongs to lifecycle/history rather than current edge identity.

## 6.2 Required logical guarantees

```text
child_object_id
    -> at most one current ownership edge

child Object must remain alive while referenced

parent_object_id != child_object_id
    -> relational self-edge backstop
```

The delivered/current `child_object_id` primary-key direction remains the natural architecture input because these paths are child-rooted:

```text
GET owner
ATTACH ownerlessness admission
DETACH requested-child lookup
upward ownership/root traversal
```

A direct child lifetime FK to `objects.id` and the self-edge CHECK remain natural physical candidates, but exact DDL remains architecture work.

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

## 7.1 Direct parent Object FK — OPEN

If:

```text
object_component_slots.object_id -> objects.id
```

and every edge references a current slot row, parent existence/lifetime is already implied transitively.

Therefore a separate:

```text
object_components.parent_object_id -> objects.id
```

may duplicate an invariant and add another FK check to ATTACH.

Architecture should retain it only if it proves a distinct lifetime/arbitration or physical-planning benefit.

## 7.2 Direct model-plane lineage FKs — OPEN

Potential direct FKs from:

```text
slot_declaring_template_id
target_template_id
```

to ObjectTemplate lineage rows remain open.

Possible benefit:

```text
local corruption prevention
explicit referential integrity
```

Possible cost:

```text
duplicate lifetime blockers already guaranteed through certified exact schema
additional write/check work
additional low-level delete interactions
```

The final lifetime graph must decide this globally.

# 8. Slot lifetime and Object DELETE

Slot rows are owned derived state of the Object, not independent facts that should keep the Object alive.

Current logical lifetime direction:

```text
object_component_slots.object_id
    -> objects.id
    owned/cascading lifetime
```

Combined with edge -> slot restrictive reference semantics:

```text
Object with only empty slots
    -> owned slot rows disappear with Object
    -> slot materialization does not block DELETE

Object with attached children
    -> referenced slot row cannot disappear
    -> root Object DELETE remains blocked
```

This preserves the semantic rule that Object DELETE never implicitly DETACHes children.

Exact `CASCADE` / `RESTRICT` / `NO ACTION` DDL spelling and timing belong to architecture.

# 9. PostgreSQL FK-arbitration evidence

The composite edge-to-slot FK is not only referential integrity; it is also the current candidate narrow concurrency rendezvous for slot continuity.

The supporting PostgreSQL evidence is that FK insertion protects the referenced key with key-share semantics: deletion or referenced-key mutation must arbitrate with that reference, while an ordinary non-key update need not conflict merely because the row is referenced.

Current referenced semantic key:

```text
(object_id, slot_declaring_template_id, slot_name)
```

## 9.1 Slot REMOVE

```text
SCHEMA_CHANGE removes slot first
    -> later ATTACH cannot satisfy the current-slot FK

ATTACH edge commits first
    -> referenced slot cannot be removed while the edge remains
```

No complete parent Object binding lock is required merely to obtain this semantic-slot arbitration.

## 9.2 Same-name semantic replacement

Replacement changes:

```text
slot_declaring_template_id
```

which participates in the referenced semantic key.

Therefore:

```text
old slot referenced
    -> semantic key change/removal cannot complete

old slot unreferenced
    -> semantic replacement may proceed
```

An existing edge cannot silently become membership of a new same-name slot declared by another lineage.

## 9.3 Target widening

Normal target evolution changes only:

```text
target_template_id
```

which is deliberately not part of the edge referenced key.

Semantically, widening moves from a narrower descendant target to an ancestor target, so every child admitted under the old target remains admissible under the wider one.

Therefore:

```text
parent template_version changed
    !=
ATTACH must fail
```

Only actual slot removal or semantic identity replacement must arbitrate with edge insertion.

## 9.4 Position-only evolution

Position/order is not materialized. Position-only schema evolution therefore performs no current-slot DML and creates no ownership conflict surface.

## 9.5 DETACH

DETACH removes the referencing edge:

```text
DETACH commits first
    -> last reference may disappear
    -> slot REMOVE/replacement may proceed

slot transition reaches FK arbitration while edge remains
    -> invalid removal/key change cannot commit
```

This supports removing route-local parent-binding stabilization whose only purpose was semantic slot continuity.

## 9.6 What this evidence does not prove

This evidence does **not** close the complete global concurrency architecture.

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

Public and route-local details remain owned by `object.md`; this section records persistence consequences only.

## 10.1 CREATE

For a new Object bound to exact `(T,V)`:

```text
INSERT Object
+
materialize one current slot row for every certified
object_template_effective_components(T,V) row
```

Preferred logical direction is a bounded DB-internal copy from immutable certified effective components in the final Object-admission transaction.

No ownership edge is created by CREATE.

Additional row work is approximately:

```text
+ S current slot writes
+ one bounded exact-effective-component source range
```

where `S` is effective slot count.

Whether Object insert + slot copy are physically fused into one SQL statement remains architecture realization work.

## 10.2 GET Object

Current data-plane sources become:

```text
objects
object_component_slots
object_components
objects child
```

The route can obtain current root + complete current slots + current children in one statement snapshot with:

```text
0 component-schema cache dependency
0 normal model-plane read
```

Detailed GET semantics and SQL-carrier handoff are owned by `object.md`.

## 10.3 GET one component slot

Current slot existence/identity is looked up directly by:

```text
(object_id, slot_name)
```

and membership is paged from `object_components` using the resolved semantic identity.

This permits direct distinction between:

```text
parent absent
slot absent
slot present + empty
slot present + children
```

without exact-schema reconstruction.

## 10.4 GET owner

Reverse ownership remains child-rooted at `object_components.child_object_id`.

Persisted semantic edge identity removes the need to reconstruct ObjectTemplate ancestry merely to describe the current owner edge.

## 10.5 ATTACH

Current parent-slot lookup supplies directly:

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

Stable child Object-lineage and ancestry validation remain independently useful and are now prepared cache-first as owned by `object.md` / `object-template-ancestry-cache.md`.

Current route-level semantics and cost are owned only by `object.md`. The full-sweep logical baseline is:

```text
warm      = 6 PostgreSQL statements + COMMIT
full-cold = 8 PostgreSQL statements + COMMIT
```

This persistence materialization is one enabling input to that profile; the complete route cost also reflects the stable Object-lineage cache and the post-edge lifecycle display-name read. The cross-operation persistence owner must not be used as a competing route-cost authority.

## 10.6 DETACH

DETACH removes factual edge rows directly and receives semantic identity from the deleted edge itself.

The edge-to-slot dependency narrows SCHEMA_CHANGE sequencing and weakens the case for a generic parent lock used only as slot-transition rendezvous.

## 10.7 SCHEMA_CHANGE

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

The final REMOVE/replacement relational boundary also reopens the old assumption that outgoing ownership membership must participate in the optimistic SCHEMA_CHANGE fingerprint:

```text
preserved/widened membership
    -> need not invalidate prepared migration merely because ATTACH/DETACH happened

REMOVE/replacement
    -> final current slot dependency arbitrates actual blocker state
```

A concurrent DETACH may therefore allow a slot removal/replacement to succeed if it removes the last reference before final arbitration rather than forcing a conservative failure derived from an older ownership snapshot.

The full SCHEMA_CHANGE route semantics, intrinsic freshness protocol, lifecycle, failure and cost closure are owned by `object.md`; exact SQL/UoW realization remains architecture work.

Slot-delta row work is proportional to changed slots rather than total slots:

```text
ADD + REMOVE + widened/replaced slots
```

No final SCHEMA_CHANGE statement count is frozen by this persistence WIP.

## 10.8 Object DELETE

Object DELETE gains owned slot-row removal/cascade work proportional to current slot count but no required slot precheck or additional route round trip.

Referenced ownership still blocks deletion through the slot dependency.

# 11. Cache boundary

The materialization does **not** delete immutable ObjectTemplate component-schema knowledge as a system capability.

It removes that cache/model-plane dependency from the normal candidates for:

```text
GET Object
GET one component slot
ATTACH slot resolution / target lookup
DETACH
```

Immutable exact schema and validation caches remain appropriate where a route genuinely performs semantic validation or migration.

The route-local ATTACH `ObjectLineageCache[object_id] -> template_id` and its current-existence boundary are owned by `object.md`, not by this persistence WIP. The reusable complete stable ObjectTemplate ancestry-cache contract is owned by `object-template-ancestry-cache.md`.

General boundary:

```text
current mutable/materialized runtime fact
    -> PostgreSQL data plane

immutable/stable semantic interpretation knowledge
    -> certified materialization + worker-local cache where useful
```

A normal data-plane read should not recertify a current fact against model-plane schema merely to reconstruct information already materialized relationally.

# 12. Storage and workload trade-off

Let:

```text
O = number of current Objects
S = average current effective component-slot count per Object
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

## 12.1 Workload-weighted illustration

The supplied approximate ratio is an explicit discovery assumption, not a product guarantee:

```text
100 ATTACH
1 SCHEMA_CHANGE
```

For warm ATTACH, the historical pre-materialization route candidate used `7` PostgreSQL statements while the current full-swept logical route baseline is `6`:

```text
old warm ATTACH      7
current warm ATTACH  6
```

The current full-cold ATTACH baseline is separately owned by `object.md` and is `8` statements + COMMIT; it includes both bounded stable Object-lineage and ancestry fills and must not be inferred from this materialization alone.

Using the warm counts only, 100 ATTACHes save approximately 100 PostgreSQL business statements before counting reads.

Even an illustrative conservative SCHEMA_CHANGE increase from `6` to `9` statements would produce:

```text
old illustrative mix
    100*7 + 1*6 = 706

new illustrative upper shape
    100*6 + 1*9 = 609
```

or roughly 97 fewer business statements for that mutation mix.

This is **not a benchmark** and ignores row volume, storage, cache state and latency. Its purpose is only to show why SCHEMA_CHANGE route-local statement count cannot reject a materialization whose benefits accrue repeatedly on hotter operations.

Frequent GET Object traffic strengthens the qualitative case further because its candidate moves from a former 2-statement warm / 3-statement cold cache path to one current data-plane statement.

## 12.2 Structural/write cost remains real

Exact byte footprint and write amplification must be measured before architecture freeze.

The materialization deliberately avoids fields such as effective position that would add write amplification without an identified hot-path benefit.

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

Exact migration order, validation SQL, constraint-validation strategy and lock impact belong to architecture/migration design.

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

The candidate attempts to cover:

```text
current slot lookup by (object_id, slot_name)
all slots for one Object
edge FK reverse/reference work
GET Object parent fan-out
one-slot child_id keyset pagination
GET owner / ownerlessness / upward traversal by child id
```

without adding route-local duplicate indexes.

## 14.1 Current physical-candidate cost interpretation

The non-ratified edge-index direction is intentionally a **replacement** for the old parent-oriented secondary index, not an additional near-duplicate.

Illustrative current candidate shape:

```text
object_components
    1 primary-key index by child_object_id
    1 parent/semantic-slot secondary B-tree
```

So relative to the AS-IS direction:

```text
edge index count
    -> unchanged in shape

secondary edge key width
    -> increases by slot_declaring_template_id UUID
```

ATTACH/DETACH therefore need not pay an extra *number* of edge secondary indexes merely because semantic identity is persisted, although they do pay the wider key. Exact bytes/write amplification remain measurement items.

For `object_component_slots`, the logical requirement for both semantic uniqueness and `(object_id, slot_name)` lookup naturally implies additional index/storage work; no third slot index is currently justified by identified consumers.

## 14.2 Why the current architecture input uses semantic edge order

The explored B-tree order:

```text
(parent_object_id,
 slot_declaring_template_id,
 slot_name,
 child_object_id)
```

was chosen because it can potentially serve both:

```text
exact semantic-slot membership/keyset page
and
referencing-side lookup for slot DELETE / semantic-key UPDATE
```

while retaining `parent_object_id` as a leading prefix for parent-rooted GET Object access.

The alternative order remains reopenable from final planner/runtime evidence.

## 14.3 Why no extra physical structures are currently justified

The existing exploration sees no demonstrated need for:

```text
second near-duplicate parent/slot edge index
third slot index
target_template_id search index
INCLUDE payloads
copied child canonical_name
```

Child `canonical_name` remains mutable current Object authority and must not be copied into ownership persistence merely to chase a covering read.

## 14.4 Surrogate `slot_id` alternative

A surrogate row identity could narrow the edge FK:

```text
object_component_slots.slot_id
object_components.slot_id
```

but the current exploration does not prefer it because it would weaken the direct expression of semantic replacement.

To preserve the same invariant, a surrogate design would need an additional proven rule ensuring that an attached edge cannot continue referencing the same surrogate row while that row's declaring-lineage identity changes.

It would also add slot joins to edge-centered operations that currently obtain semantic slot identity directly from the factual edge.

Therefore the explicit composite semantic identity remains the current architecture input unless measured storage/write cost proves the indirection worthwhile and the replacement invariant is separately proven.

These are architecture inputs, **not discovery-final physical decisions**.

# 15. Required architecture evidence

Before architecture freeze, verify final TO-BE DDL/query shapes with representative cardinalities.

At minimum cover:

```text
component navigation populated first page
component navigation continuation page
empty slot
absent slot
stale semantic cursor gating
GET Object representative fan-out
slot DELETE / semantic-key UPDATE with zero references
slot DELETE / semantic-key UPDATE with non-zero references
FK reverse-reference behavior
edge secondary-index size delta versus AS-IS key
slot-table uniqueness/index size
ATTACH/DETACH write cost at representative batches
CREATE/SCHEMA_CHANGE slot-index maintenance cost
```

Use `EXPLAIN (ANALYZE, BUFFERS)` or the project-approved equivalent where appropriate.

The evidence goal is bounded/selective production-shaped work, not forcing a particular PostgreSQL plan-node spelling on tiny fixtures. A sequential scan on a genuinely tiny test relation does not by itself invalidate the design.

The candidate must be reopened if measured costs materially invalidate the workload trade-off.

# 16. Current open points

Discovery-level logical candidate is strong, but architecture still must close:

```text
exact PK vs UNIQUE declarations
exact FK actions/timing and constraint set
whether direct parent Object FK remains
whether direct model-plane lineage FKs remain
final index keys/order
surrogate slot-id alternative if measurements justify it
exact CREATE Object + slot-copy statement realization
exact SCHEMA_CHANGE slot-delta statement decomposition
migration/backfill mechanics
constraint failure mapping without diagnostic-only queries
complete transaction/lock/wait-for graph
storage/write measurements
final PostgreSQL plan evidence
```

The full-swept SCHEMA_CHANGE and ATTACH sections in `object.md` have revalidated route-local assumptions against this persistence boundary; architecture must preserve the resulting relational arbitration semantics and route-level failure classes.

# 17. Consolidation sources

This consolidated owner absorbs current non-superseded findings from at least:

```text
object-component-slots-data-plane-materialization.md
object-components-physical-schema-discovery.md
object-component-slots-fk-arbitration.md
object-components-physical-index-candidate.md
object-components-runtime-schema-discovery.md
object-components-reads-discovery.md
```

Route-specific consequences are summarized here only to explain cross-operation value; `object.md` remains the route owner.