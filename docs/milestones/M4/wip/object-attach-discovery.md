# M4 — Object.ATTACH initial discovery

**Status:** SUPERSEDED BY ROUTE-LOCAL CLOSURE / NON-NORMATIVE

## Purpose of this note

This file preserves the first-phase ATTACH discovery that identified the missing semantic slot identity in `object_components`.

Its execution/idempotency candidates are superseded by the reconciled route-local authority:

```text
docs/milestones/M4/wip/to-be-api-object-attach-batch.md
```

Do not use this note as the current ATTACH execution contract.

## Structural finding retained

Current `object_components` persists only:

```text
child_object_id
parent_object_id
slot_name
```

while slot semantic identity is:

```text
(slot_declaring_template_id, slot_name)
```

The candidate resulting ownership fact therefore remains:

```text
object_components
    child_object_id              PK
    parent_object_id             NOT NULL
    slot_declaring_template_id   NOT NULL
    slot_name                    NOT NULL
```

Do **not** persist `slot_declaring_template_version`: the semantic slot identity is stable-lineage based and the current edge is interpreted against the parent Object's current exact effective schema.

A candidate referential relationship remains:

```text
slot_declaring_template_id -> object_templates.id
```

with exact referential actions deferred to the global relational-schema phase.

## Superseded execution candidates

The original single-child-shaped path and same-edge idempotence discussion are no longer current.

M4 route-local closure now freezes:

```text
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}
body = {"child_object_ids": [...]}
```

with atomic batch semantics.

An already-owned requested child causes `ownership_conflict`, including an already-current identical edge. There is no same-edge convergence path.

Current owner is not read during unlocked child preparation. Ownerlessness and cycle admission are certified by protected Q3 under the ownership graph edge-add gate, then Q4 bulk INSERT relies on relational constraints as final persistence authorities.

## Retained architecture principle

PostgreSQL remains direct authority for current ownership facts and persistence integrity, while immutable/stable ObjectTemplate knowledge is resolved through worker-local cache structures.

The full current route semantics, concurrency sequence, error mapping and statement costs live only in the route-local closure file cited above.
