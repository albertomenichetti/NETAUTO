# M4 WIP — TO-BE Object ATTACH batch contract

Status: ROUTE-LOCAL CLOSED DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note records the reconciled caller-facing and route-local execution contract for Object ownership ATTACH.

## Public signature

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}
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

Frozen request rules:

- `child_object_ids` is non-empty;
- duplicate ids in the same request are invalid;
- input ordering has no semantic meaning;
- `parent_object_id` may not appear in `child_object_ids`;
- the batch is atomic.

Success:

```http
204 No Content
```

`POST` adds membership only. It never replaces a slot collection and never performs implicit DETACH.

## Same-edge semantics

M4 deliberately supersedes the previous idempotent ATTACH convergence rule.

Any requested child that already has a current owner causes the entire batch to fail, including the exact same current parent/slot edge.

There is no `ON CONFLICT` convergence path and no partial success.

## Parent preparation and slot resolution

Preparation begins with one PostgreSQL read of the parent Object:

```text
id
template_id
template_version
canonical_name
```

The path parent remains PostgreSQL-authoritative for current existence.

The slot is then resolved cache-first from:

```text
ImmutableObjectTemplateCache[(template_id, template_version)]
facet = component_schema
```

READY hit:

```text
slot_name
slot_declaring_template_id
target_template_id
```

with no semantic DB query.

On MISS, load only the missing exact immutable effective-component knowledge, compile/canonicalize it, mark the facet READY, and resume the same lookup path.

The full validation facet, effective properties and DataType validators are not needed by ATTACH.

A parent pinned to a DEPRECATED exact OTV remains governed by that immutable exact schema; ATTACH does not perform a current lifecycle-status admission query for the parent OTV.

## Child batch preparation

One bulk Object read loads all requested children:

```text
id
template_id
canonical_name
```

No current-owner join is performed.

All ids must exist. Exact child `template_version` is irrelevant for component compatibility because compatibility is stable-lineage based.

The batch may contain heterogeneous child template lineages.

Collect DISTINCT `child.template_id` values and resolve compatibility against `slot.target_template_id` through stable ancestry knowledge.

Ancestry cache semantics are:

```text
cache[source][target] -> TRUE | FALSE | MISS
```

A READY source contains its complete sparse ancestor set, including self. Absence in a READY source is therefore authoritative FALSE. MISS loads all ancestry rows for the missing source lineages in bounded bulk, then marks those sources READY.

## Unit of Work

After preparation:

```text
BEGIN

Q1  acquire OWNERSHIP_GRAPH_WRITE_GATE

Q2  SELECT parent Object FOR NO KEY UPDATE
    -> reread id, template_id, template_version
    -> parent must still exist
    -> binding must equal the prepared exact binding

Q3  one protected graph-admission statement
    -> compute whether any requested child is currently owned
    -> find root(parent) by following the single-owner chain upward
    -> compute whether root(parent) is among requested child ids

Q4  one bulk INSERT into object_components

Q5  one bulk INSERT of lifecycle ATTACH_TO events

COMMIT
```

If Q2 sees a different exact parent binding, the attempt fails conservatively with `concurrent_object_change`. The slot is not re-resolved inside the UoW.

## Cycle admission

Single-owner ownership implies that any requested child that is both ownerless and already an ancestor of the parent must be exactly the current root of the parent's ownership tree.

Therefore the frozen cycle predicate is:

```text
all requested children ownerless
AND
root(parent) not in requested_child_ids
```

under the graph edge-add gate.

Q3 returns two logical facts, not one opaque boolean:

```text
has_owned_requested_child
root_is_requested
```

Precedence:

```text
has_owned_requested_child = true
    -> ownership_conflict

otherwise root_is_requested = true
    -> ownership_cycle

otherwise
    -> graph admission succeeds
```

No materialized `object_id -> root_object_id` structure is introduced. Root lookup remains one recursive owner-chain read, proportional to tree depth. This avoids ATTACH/DETACH write amplification over entire subtrees.

Concurrent ATTACH edge additions are serialized by the gate. DETACH does not need the gate because edge removal cannot create a cycle; a concurrent DETACH may only make an attempt conservatively fail, not produce a false-success cycle.

## Persistence arbitration

`object_components.child_object_id` remains the final one-owner authority.

Q4 is intentionally simple:

```text
one multi-row INSERT
no ON CONFLICT
no per-child insert loop
```

Any PK/FK/CHECK failure aborts the statement and therefore the whole transaction.

Relational responsibilities:

```text
PK(child_object_id)
    -> at most one current owner

FK parent_object_id -> objects.id
FK child_object_id  -> objects.id
    -> referenced Object lifetime/existence authority

CHECK parent_object_id <> child_object_id
    -> self-edge backstop

graph admission + graph-write gate
    -> general DAG acyclicity
```

No current-owner precheck query exists outside Q3.

## Lifecycle

A successful batch writes one ATTACH_TO lifecycle row per inserted ownership edge, in one bulk statement Q5.

Q4 and Q5 are atomic: either all requested edges and all required lifecycle rows commit, or none do.

Parent and child `canonical_name` fields carried in lifecycle metadata are best-effort historical display values read during normal preparation. No extra locks or rereads are performed solely to make those names fresher.

## Error precedence

Error precedence is the real execution/admission order; the route does not run a second diagnostic workflow.

```text
1. invalid wire/static request
   -> 400 invalid_request

2. parent path target absent
   -> 404 resource_not_found

3. parent appears in child_object_ids
   -> 422 semantic_validation_failed / self_reference

4. slot unavailable in prepared current parent schema
   -> 409 ownership_slot_unavailable

5. one or more child operands absent in the bulk read
   -> 422 referenced_resource_not_found

6. one or more present children lineage-incompatible with the slot target
   -> 422 semantic_validation_failed

7. Q2 detects changed parent binding
   -> 409 concurrent_object_change

8. Q3 detects an owned requested child
   -> 409 ownership_conflict

9. otherwise Q3 detects root(parent) requested
   -> 409 ownership_cycle

10. Q4 residual integrity failure caused by a race
    -> translate from the known violated constraint class
```

The route stops at the first failed gate. It does not continue only to discover additional diagnostic problems.

No PostgreSQL statement may be issued solely to improve error details. Diagnostic data must come from normal execution state or classification of the known violated constraint.

A child deleted after preparation but before Q4 is therefore resolved by the child FK at Q4; the route does not reread children just to identify the exact deleted id.

## Statement cost

Warm successful path, excluding BEGIN/COMMIT:

```text
1 parent preparation read
1 bulk child read
0 component_schema DB reads on cache HIT
0 ancestry DB reads on cache HIT
1 graph gate acquisition
1 parent FOR NO KEY UPDATE / binding verification
1 graph admission statement
1 bulk object_components INSERT
1 bulk lifecycle INSERT

= 7 PostgreSQL statements + COMMIT
```

Full-cold successful path adds:

```text
+1 component_schema fill
+1 ancestry bulk fill
```

therefore:

```text
full-cold = 9 PostgreSQL statements + COMMIT
```

The number of round trips is constant with respect to requested child count. Batch size affects rows processed and payload size, while cycle-read cost depends on parent owner-chain depth.

## Route-local closure and handoffs

Closed here:

- batch-by-slot public shape;
- atomic add-only semantics;
- same-edge is conflict, not convergence;
- cache-first exact slot resolution;
- heterogeneous child stable lineages;
- no owner precheck read;
- ancestry cache direction;
- graph gate and parent stabilization;
- root-only cycle predicate under ownerless certification;
- bulk persistence and lifecycle writes;
- lifecycle display-name freshness policy;
- warm/full-cold statement counts;
- public failure classes/precedence;
- no diagnostic-only DB queries.

Deferred/global handoffs:

- normative M4 API/object/concurrency documentation reconciliation;
- exact final relational DDL and referential actions;
- physical index choice and EXPLAIN evidence;
- global schema-closure document required at milestone closure.
