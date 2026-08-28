# M4 WIP — TO-BE Object ATTACH batch contract

Status: PUBLIC/SEMANTIC CONTRACT RETAINED / EXECUTION PATH REOPENED / M4 WIP / NON-NORMATIVE GLOBALLY

## Revalidation notice

This consolidation has been reopened by [`object-component-slots-data-plane-materialization.md`](object-component-slots-data-plane-materialization.md).

The earlier execution candidate depended on:

```text
parent exact template pin
component-schema cache resolution
parent FOR NO KEY UPDATE + exact-binding recheck
```

Those dependencies are no longer the preferred current candidate if every Object materializes its current effective slot contract in `object_component_slots` and ownership edges reference that slot row relationally.

A separate continuous-revalidation pass also found that this file still contained the superseded route without the explicit `/attach` command segment. The owning command-route WIP `object-ownership-command-routes.md` had already superseded that shape. This file is corrected here to match the current public checkpoint.

## Public signature

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}/attach
```

Request body:

```json
{
  "child_object_ids": [
    "<child-1>",
    "<child-2>",
    "<child-3>"
  ]
}
```

Current request rules retained:

- `child_object_ids` is non-empty;
- duplicate ids in the same request are invalid;
- input ordering has no semantic meaning;
- `parent_object_id` may not appear in `child_object_ids`;
- the batch is atomic.

Success:

```http
204 No Content
```

ATTACH adds membership only. It never replaces a slot collection and never performs implicit DETACH.

## Same-edge semantics retained

Any requested child that already has a current owner causes the entire batch to fail, including the exact same current parent/slot edge.

There is no `ON CONFLICT` convergence path and no partial success.

## Reopened parent/slot preparation

### Superseded checkpoint

The previous candidate did:

```text
read parent Object
    -> template_id/template_version

component-schema cache
    -> resolve slot_name
    -> slot_declaring_template_id
    -> target_template_id
```

and later re-locked/re-read the parent binding in the UoW.

That path remains historical discovery evidence only.

### Current materialized-slot candidate

One current data-plane statement should instead obtain:

```text
parent Object existence
parent canonical_name
requested slot existence
slot_declaring_template_id
target_template_id
```

from:

```text
objects parent
LEFT JOIN object_component_slots
    ON object_id = parent.id
   AND slot_name = requested slot
```

The statement must preserve the distinction:

```text
parent absent
    -> 404 resource_not_found

parent present + slot absent
    -> 409 ownership_slot_unavailable

parent present + slot present
    -> current ATTACH contract available directly
```

No exact parent template pin or component-schema cache lookup is needed merely to resolve the current slot contract.

A parent pinned to a DEPRECATED exact OTV remains governed by its current materialized slot contract; ATTACH still does not require a current lifecycle-status admission query for the parent OTV.

## Child batch preparation retained

One bulk Object read loads all requested children:

```text
id
template_id
canonical_name
```

No current-owner join is performed.

All ids must exist. Exact child `template_version` remains irrelevant for component compatibility because compatibility is stable-lineage based.

Collect DISTINCT `child.template_id` values and resolve compatibility against current `slot.target_template_id` through stable ancestry knowledge.

Ancestry cache direction remains useful:

```text
cache[source][target] -> TRUE | FALSE | MISS
```

A READY source contains its complete sparse ancestor set, including self. MISS loads missing source-lineage ancestry in bounded bulk.

## Reopened ATTACH x SCHEMA_CHANGE arbitration

The prior parent `FOR NO KEY UPDATE` step existed primarily to ensure that the parent exact binding did not change after the slot had been resolved from exact-schema cache.

With the current materialization candidate, ownership rows reference current slot identity:

```text
FK (
    parent_object_id,
    slot_declaring_template_id,
    slot_name
)
-> object_component_slots (
    object_id,
    slot_declaring_template_id,
    slot_name
)
```

This creates a narrower arbitration boundary.

### REMOVE slot race

```text
SCHEMA_CHANGE removes slot first
    -> old slot row no longer exists
    -> ATTACH edge INSERT cannot satisfy FK

ATTACH edge commits first
    -> slot row becomes referenced
    -> SCHEMA_CHANGE cannot remove it while edge exists
```

### Semantic replacement race

`slot_declaring_template_id` participates in the referenced key. A replacement of `(old declaring lineage, slot_name)` with `(new declaring lineage, slot_name)` therefore cannot silently reinterpret already-attached edges.

### Target widening race

Normal slot target evolution is widening toward an ancestor lineage.

```text
ATTACH validates child against old narrower target
SCHEMA_CHANGE widens target_template_id
ATTACH commits afterward
```

is semantically safe because every child admitted by the old target remains admitted by the wider target.

A parent `template_version` change is therefore no longer by itself a reason to reject ATTACH.

The previous `concurrent_object_change` outcome that existed solely because the complete parent binding changed is reopened and is not part of the preferred current candidate unless later architecture finds another required use for it.

## Current candidate Unit of Work

After preparation:

```text
BEGIN

Q1  acquire OWNERSHIP_GRAPH_WRITE_GATE

Q2  one protected graph-admission statement
    -> compute whether any requested child is currently owned
    -> find root(parent) through the single-owner chain
    -> compute whether root(parent) is among requested child ids

Q3  one bulk INSERT into object_components
    -> edge must reference the current materialized semantic slot

Q4  one bulk INSERT of ATTACH_TO lifecycle events

COMMIT
```

The former parent exact-binding stabilization statement is removed from this current candidate.

Global architecture must still prove the PostgreSQL locking/FK behavior for ATTACH x SCHEMA_CHANGE before implementation.

## Cycle admission retained

Single-owner ownership implies that any requested child that is both ownerless and already an ancestor of the parent must be exactly the current root of the parent's ownership tree.

Protected graph predicate remains:

```text
all requested children ownerless
AND
root(parent) not in requested_child_ids
```

under the graph edge-add gate.

Q2 returns two logical facts:

```text
has_owned_requested_child
root_is_requested
```

Precedence retained:

```text
has_owned_requested_child = true
    -> ownership_conflict

otherwise root_is_requested = true
    -> ownership_cycle

otherwise
    -> graph admission succeeds
```

No persisted `object_id -> root_object_id` candidate is introduced by this revalidation.

## Persistence arbitration — reopened and strengthened

`object_components.child_object_id` remains the final one-owner authority.

Current candidate relational responsibilities:

```text
PK(child_object_id)
    -> at most one current owner

FK child_object_id -> objects.id
    -> child lifetime authority

FK edge semantic slot -> object_component_slots
    -> parent existence through owned current slot
    -> current slot existence
    -> semantic slot identity

CHECK parent_object_id <> child_object_id
    -> self-edge backstop

graph admission + graph-write gate
    -> DAG acyclicity
```

Whether the direct `parent_object_id -> objects.id` FK remains in addition to the slot FK is reopened as a possible redundant constraint.

Q3 remains one bulk INSERT with no `ON CONFLICT` and no per-child insert loop.

## Lifecycle retained

A successful batch writes one ATTACH_TO lifecycle row per inserted ownership edge, in one bulk statement.

Edge and lifecycle writes remain atomic in one transaction.

Parent/child canonical names remain best-effort historical display metadata obtained from normal preparation; no extra reread is added solely for freshness.

## Error precedence — partially reopened

Retained candidate precedence:

```text
1. invalid wire/static request
   -> 400 invalid_request

2. parent path target absent
   -> 404 resource_not_found

3. parent appears in child_object_ids
   -> 422 semantic_validation_failed / self_reference

4. slot unavailable in current materialized parent contract
   -> 409 ownership_slot_unavailable

5. one or more child operands absent
   -> 422 referenced_resource_not_found

6. one or more present children lineage-incompatible with slot target
   -> 422 semantic_validation_failed

7. protected graph admission finds an owned requested child
   -> 409 ownership_conflict

8. otherwise root(parent) is requested
   -> 409 ownership_cycle

9. residual constraint race at edge INSERT
   -> translate from the known violated constraint class
```

The former separate parent-binding-change / `concurrent_object_change` step is reopened and removed from the preferred sequence.

A final failure mapping is still required for the race where the slot disappears/replaces after unlocked preparation but before edge INSERT. No diagnostic-only query may be added solely to improve that classification.

## Revalidated candidate statement cost

Warm successful path, excluding BEGIN/COMMIT:

```text
1 parent + current slot read
1 bulk child read
0 component-schema cache/DB work
0 ancestry DB reads on cache HIT
1 graph gate acquisition
1 protected graph admission statement
1 bulk object_components INSERT
1 bulk lifecycle INSERT

= 6 PostgreSQL statements + COMMIT
```

Full-cold path adds only:

```text
+1 ancestry bulk fill
```

therefore current candidate:

```text
warm      = 6 PostgreSQL statements + COMMIT
full-cold = 7 PostgreSQL statements + COMMIT
```

These counts remain WIP estimates. Further fusion of graph admission and edge INSERT is a separate discovery question and is not assumed here.

## Current route-local state

Retained:

- explicit `/attach` public command route;
- batch-by-slot body and `204` success;
- atomic add-only semantics;
- same-edge conflict rather than convergence;
- heterogeneous child stable lineages;
- bulk child read;
- stable ancestry cache direction;
- no owner precheck outside protected graph admission;
- graph gate + root-only cycle predicate;
- bulk edge/lifecycle writes;
- no diagnostic-only DB queries.

Reopened/superseded:

```text
component-schema cache slot resolution
component-schema cold fill
parent exact-binding preparation as slot authority
parent FOR NO KEY UPDATE / binding recheck
concurrent_object_change caused only by binding change
7/9 statement cost profile
parent direct-FK necessity
```

Architecture handoff now includes the complete `object_component_slots` DDL and ATTACH x SCHEMA_CHANGE relational-locking proof.
