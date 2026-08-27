# M4 — Object components runtime schema discovery

**Status:** WIP / NON-NORMATIVE

## Scope

This note captures first-phase discovery on the runtime relational shape for Object ownership/components. It does not freeze schema, migration, API or concurrency design.

## Current shape

Current Object intrinsic state is stored in `objects`:

```text
id
canonical_name
template_id
template_version
properties
```

Current ownership state is stored separately in `object_components` with the essential runtime fact:

```text
child_object_id
parent_object_id
slot_name
```

`child_object_id` is the single-owner authority.

The current schema intentionally keeps ownership outside the Object JSON/property snapshot, which remains desirable because ownership needs independent relational constraints, reverse lookup, cycle checks and delete blocking.

## Finding: current ownership fact is under-materialized

ObjectTemplate architecture defines slot continuity by:

```text
SlotSemanticKey = (declaring_template_id, name)
```

The current runtime edge persists only `slot_name`, discarding `declaring_template_id` after ATTACH resolves the current effective slot.

As a consequence, component/owner reads and Object.SCHEMA_CHANGE must recover the missing semantic identity by resolving the parent Object's current exact effective ObjectTemplate schema. Current read projections do this through exact-chain traversal and declaration lookup.

Working M4 candidate:

```text
object_components
    child_object_id              PK
    parent_object_id
    slot_declaring_template_id
    slot_name
```

This preserves the complete stable semantic identity already resolved at ATTACH time.

## Why no `slot_declaring_template_version`

The current ownership edge is interpreted against the parent Object's **current exact effective schema**, not against a version-pinned slot declaration.

Slot semantic identity is stable across ObjectTemplate version evolution:

```text
(declaring_template_id, slot_name)
```

while the exact declaration/version contract may evolve, including allowed target-lineage widening.

Persisting `slot_declaring_template_version` would either:

1. leave a stale old-version semantic pointer after parent Object.SCHEMA_CHANGE; or
2. require rewriting ownership rows on every schema change even when the logical attachment did not change.

Neither is desirable.

The runtime edge should therefore preserve only stable semantic identity. The parent Object's current `(template_id, template_version)` plus the immutable effective-schema cache/materialization determines the current exact slot contract.

Conceptually:

```text
ownership fact
    child_object_id
    parent_object_id
    slot_declaring_template_id
    slot_name

+
parent current exact OTV

-> current effective component contract
```

If historical provenance of the exact declaring version at ATTACH time were ever required, that would belong to lifecycle/history metadata rather than current ownership identity.

## Fields not currently justified on the runtime edge

Do not currently denormalize:

```text
target_template_id
slot_declaring_template_version
parent_template_version
slot position
```

These belong to the current exact schema contract, not the stable semantic identity of the attachment. Persisting them would cause write amplification or stale semantic copies across Object schema changes.

## Expected simplifications

### Component LIST / Owner GET

Current projections reconstruct the exact parent ObjectTemplate chain solely to derive `slot_declaring_template_id`.

With the candidate runtime edge, public projection can read directly from `object_components` while preserving 404/empty/null semantics.

### ATTACH

ATTACH already resolves a `ResolvedComponentSlot` containing:

```text
declaring_template_id
name
target_template_id
```

The candidate edge persists the first two fields together with parent/child identity, rather than discarding `declaring_template_id` after admission.

### Object.SCHEMA_CHANGE

Current flow starts from `fact.slot_name`, resolves the source effective schema to rediscover `declaring_template_id`, then looks up the same semantic key in the target effective schema.

With the candidate edge:

```text
semantic_key = (
    fact.slot_declaring_template_id,
    fact.slot_name
)
```

is already explicit. Schema change only needs to verify that this key exists in the target effective schema and that the child stable lineage remains compatible with the target slot contract.

## Architectural direction

The emerging principle mirrors factual Relationship materialization:

```text
model/runtime interpretation during admission
    -> resolve stable semantic identity
    -> persist resolved runtime fact
```

The separation between `objects` and `object_components` remains sound; the likely problem is not normalization itself but insufficient semantic materialization in `object_components`.

## Open items

- exact foreign-key shape for `slot_declaring_template_id`;
- whether the stable declaring lineage FK should reference `object_templates(id)` directly;
- index adjustments for parent/child/slot projections;
- ATTACH/DETACH/SCHEMA_CHANGE data paths under this shape;
- migration/backfill strategy for existing rows;
- concurrency implications remain deferred to the global phase.
