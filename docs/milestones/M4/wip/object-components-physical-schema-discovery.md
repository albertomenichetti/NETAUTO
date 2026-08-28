# M4 WIP — Object components physical schema discovery

Status: ACTIVE REVALIDATION / M4 WIP / NON-NORMATIVE

## Scope

This note is the current physical-schema discovery owner for Object component-slot runtime materialization and ownership edges.

It supersedes the earlier single-table direction that enriched only `object_components.slot_declaring_template_id` while leaving empty effective slots exclusively in model-plane state.

The current candidate is driven by the cross-operation analysis in:

```text
object-component-slots-data-plane-materialization.md
```

and remains fully subject to further M4 revalidation.

## AS-IS baseline

Delivered persistence stores only current ownership edges:

```text
object_components
    child_object_id      PK
    parent_object_id
    slot_name
```

This represents single-owner membership well, but it does not persist:

```text
stable declaring-lineage identity
empty current effective slots
current target-template contract
```

The earlier M4 candidate addressed only the first point by adding:

```text
slot_declaring_template_id
```

to each edge.

The current revalidation asks a broader question: should the current effective component contract itself be materialized once per Object so frequent runtime operations do not repeatedly recover it from ObjectTemplate state/cache?

## Candidate runtime layering

```text
objects
    = current intrinsic Object state + exact ObjectTemplate binding

object_component_slots
    = owned derived current effective component contract for one Object

object_components
    = current child membership facts constrained to those slots
```

ObjectTemplate exact effective schema remains the semantic source. `object_component_slots` is a transactionally maintained data-plane derivative, not an independent model authority.

## Candidate `object_component_slots`

Current useful non-minimal shape:

```text
object_component_slots
    object_id                    NOT NULL
    slot_declaring_template_id   NOT NULL
    slot_name                    NOT NULL
    target_template_id           NOT NULL
```

One row exists for every effective component slot of the Object current exact ObjectTemplateVersion, including slots with zero attached children.

### Logical identity constraints

Two uniqueness properties matter:

```text
semantic current slot identity
    UNIQUE (object_id, slot_declaring_template_id, slot_name)

public/runtime name lookup
    UNIQUE (object_id, slot_name)
```

The exact declaration of PRIMARY KEY vs UNIQUE is a physical-design choice still OPEN.

The second constraint mirrors the ObjectTemplate effective-schema invariant that effective property/component names are unambiguous and inherited members cannot be hidden/overridden.

### Object ownership/lifetime

Candidate:

```text
FK object_component_slots.object_id
    -> objects.id
    ON DELETE CASCADE
```

Slot rows are owned derived state. They must disappear automatically when their Object is deleted, provided no current ownership edge still references them.

### Direct model-plane FKs — OPEN

Potential direct constraints:

```text
slot_declaring_template_id -> object_templates.id
target_template_id         -> object_templates.id
```

remain OPEN.

Reasons to avoid them unless they add a distinct guarantee:

- these ids are copied from a certified exact effective ObjectTemplate schema;
- model-plane declarations/ancestry already protect the relevant stable lineages;
- extra FKs add write/check cost and may create duplicate low-level delete blockers;
- the slot materialization is owned by the Object, not a new model-plane dependency source.

Reasons in favor remain local corruption prevention and explicit referential integrity. Architecture must decide with the complete lifetime graph in view.

## Why `target_template_id` is materialized

This field is current exact-slot contract state rather than stable ownership identity, but it is consumed by frequent ATTACH admission.

Workload direction supplied during discovery:

```text
SCHEMA_CHANGE : ATTACH
    approximately 1 : 100
```

Normal slot-target evolution is widening toward an ancestor lineage.

Therefore:

```text
rare SCHEMA_CHANGE
    -> UPDATE target_template_id on affected slot row

frequent ATTACH
    -> read target_template_id directly from current slot row
    -> no component-schema cache/exact-schema resolution
```

This is the central non-minimal denormalization trade-off currently favored.

## Why `effective_ordinal` / `position` is not materialized now

A stronger full-copy candidate was evaluated.

Current runtime consumers do not require slot ordering:

- Object GET gives no contract meaning to JSON component-key order;
- component navigation pages children within one slot;
- ATTACH/DETACH do not use slot order.

Persisting ordering would make position-only SCHEMA_CHANGE perform data-plane updates without removing work from a currently identified hot path.

Current candidate therefore excludes:

```text
effective_ordinal
position
```

with explicit reopen if a future runtime contract needs them.

## Other fields explicitly not copied

Do not currently persist on `object_component_slots`:

```text
parent template_id
parent template_version
slot_declaring_template_version
```

The current binding already belongs to `objects`. Declaring exact version is not part of slot semantic identity.

Do not persist mutable child display state such as `canonical_name` in either slot or edge rows.

## Candidate `object_components`

Current edge candidate remains:

```text
object_components
    child_object_id              PK
    parent_object_id             NOT NULL
    slot_declaring_template_id   NOT NULL
    slot_name                    NOT NULL
```

### Child lifetime / single owner

Retain:

```text
PK child_object_id
FK child_object_id -> objects.id RESTRICT
CHECK parent_object_id <> child_object_id
```

### Edge -> current slot FK

Add:

```text
FK (
    parent_object_id,
    slot_declaring_template_id,
    slot_name
)
REFERENCES object_component_slots (
    object_id,
    slot_declaring_template_id,
    slot_name
)
RESTRICT
```

This becomes the final relational authority for:

```text
edge parent exists through an owned current slot
requested semantic slot currently exists
edge semantic identity matches current slot identity
SCHEMA_CHANGE cannot remove/replace a referenced slot
```

### Direct parent Object FK — REOPENED

The earlier schema retained:

```text
FK parent_object_id -> objects.id RESTRICT
```

With the new composite slot FK plus `object_component_slots.object_id -> objects.id`, parent existence/lifetime is already implied transitively.

Keeping the direct parent FK may therefore duplicate an invariant and add another FK check to every ATTACH.

Current state:

```text
OPEN
```

Architecture should retain it only if it provides a distinct lifetime/arbitration or physical-planning benefit.

## Semantic replacement backstop

A same-name slot with a different declaring lineage is a different semantic slot.

Because `slot_declaring_template_id` participates in the edge FK key, changing the current slot semantic identity is a referenced-key mutation.

Therefore:

```text
old slot has current edges
    -> semantic-key change/remove cannot complete

old slot has zero edges
    -> semantic-key transition may proceed
```

This directly realizes the existing Object.SCHEMA_CHANGE rule without silently reinterpreting membership.

## CREATE maintenance boundary

For a new Object bound to exact `(T,V)`:

```text
INSERT Object
+
INSERT one object_component_slots row
    for every object_template_effective_components(T,V) row
```

Candidate direction is a bounded DB-internal `INSERT ... SELECT` from the certified immutable effective-component materialization in the same final Object creation statement when practical.

No ownership edge is created by Object CREATE.

## SCHEMA_CHANGE maintenance boundary

The current immutable MigrationPlan already classifies SOURCE -> TARGET effective slot changes.

Candidate data-plane delta:

```text
ADD
    -> INSERT slot row

REMOVE
    -> DELETE slot row
    -> referenced-edge FK is final blocker authority

same semantic slot + target widening
    -> UPDATE target_template_id

semantic replacement under same effective name
    -> key-changing UPDATE slot_declaring_template_id
       and target_template_id as required
    -> FK blocks while old edges exist

position-only change
    -> no slot-row DML
```

Existing `object_components` rows are unchanged by every successful normal SCHEMA_CHANGE.

## Object DELETE consequence

Candidate slot FK to Object is CASCADE because slots are owned derived state.

With edge -> slot RESTRICT:

```text
Object with attached child edges
    -> slot cascade cannot remove referenced slot
    -> root Object DELETE remains blocked

Object with only empty slots
    -> slot rows cascade
    -> Object DELETE succeeds if no other blockers exist
```

No explicit DELETE statement for slot rows is required on the route.

## Runtime read consequences

### GET Object

Candidate access:

```text
objects by id
+ object_component_slots by object_id
+ object_components by parent/semantic slot
+ child objects for canonical_name
```

Target is one coherent PostgreSQL statement with no component-schema cache or model-plane effective-component lookup.

### GET one component slot

Candidate current-slot lookup:

```text
(object_id, slot_name)
```

then paged membership through `object_components` ordered by child id.

### GET owner

Reverse ownership remains rooted at `object_components.child_object_id`.

If future owner projection needs current target/declaration contract beyond the persisted edge fields, it may join the referenced slot row. No ObjectTemplate reconstruction is required.

## ATTACH consequence

Current parent slot lookup returns directly:

```text
slot_declaring_template_id
target_template_id
```

The edge INSERT references that current slot.

This removes the current preferred need for:

```text
parent exact-template pin solely for slot resolution
component-schema cache lookup/fill
parent exact-binding recheck solely for slot safety
```

Stable child-lineage ancestry checking remains independently useful.

## DETACH consequence

DETACH still removes factual edges directly and obtains semantic identity from the deleted row.

The slot FK may remove the need for a generic parent lock used only to rendezvous with SCHEMA_CHANGE because REMOVE/replacement arbitration now occurs at the referenced slot row.

## Index direction — REOPENED

Earlier direction retained only:

```text
object_components(parent_object_id, slot_name, child_object_id)
```

The complete workload now needs a joint index review.

Logical access requirements include at least:

```text
object_component_slots
    unique current slot lookup by (object_id, slot_name)
    unique semantic referenced key for edge FK
    all slots for one Object

object_components
    child_object_id PK
    page one parent+slot by child_object_id
    all outgoing edges for one parent where still needed
    composite FK support for current slot reference
```

A likely useful edge access key remains:

```text
(parent_object_id, slot_name, child_object_id)
```

but whether `slot_declaring_template_id` belongs in a key, INCLUDE list, or relies on another supporting index must be decided from the complete DDL and EXPLAIN evidence.

The slot table will likely need at least two logical uniqueness paths unless a different key design proves both lookup and semantic-FK requirements with less write cost.

No final index is frozen here.

## Storage scaling

Let:

```text
O = number of current Objects
S = average current effective component-slot count per Object
```

Then:

```text
object_component_slots row count ~= O * S
```

This, plus its indexes, is the principal cost of the denormalization.

Exact byte cost must be measured using realistic name lengths, Object counts and slot cardinalities before architecture freeze.

The current discovery does not hide this cost behind statement-count savings.

## Migration/backfill direction — REOPENED

After `object_template_effective_components` exists, populate current slot materialization from admitted Object bindings:

```text
objects O
JOIN object_template_effective_components E
  ON E.template_id      = O.template_id
 AND E.template_version = O.template_version

INSERT object_component_slots(
    object_id,
    slot_declaring_template_id,
    slot_name,
    target_template_id
)
```

Then backfill/verify every existing ownership edge semantic identity against exactly one current slot row before enabling the edge FK.

Required migration invariant:

```text
every existing edge
    -> exactly one current slot row
```

Zero or multiple matches indicate pre-existing corruption or an incorrect migration and must fail rather than invent a value.

The exact migration order, validation queries, constraint validation mode and lock impact remain architecture/migration design items.

## Current candidate conclusion

Preferred runtime physical direction is now:

```text
objects
    current intrinsic state + exact binding

object_component_slots
    one current derived row per effective slot
    includes target_template_id

object_components
    one factual row per attached child
    FK -> current semantic slot row
```

Current expected trade-off:

```text
COST
    O * S additional rows + indexes
    more bounded writes on CREATE/SCHEMA_CHANGE/DELETE

BENEFIT
    GET Object candidate 1 statement
    component navigation pure data-plane
    ATTACH no component-schema cache and less parent stabilization
    DETACH less generic lock coupling
    relational REMOVE/replacement arbitration
    reduced ownership-edge fingerprint/retry coupling in SCHEMA_CHANGE
```

Everything remains M4 WIP and may be reopened again if later Object/Relationship work changes the workload or reveals a better materialization boundary.
