# M4 WIP — Object ATTACH batch Unit of Work

Status: ROUTE-LOCAL CLOSED DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note records the final statement-by-statement mutation Unit of Work for the M4 TO-BE batch ATTACH surface:

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}
```

The complete reconciled route authority is `to-be-api-object-attach-batch.md`.

## Preparation identity carried into the UoW

Before `BEGIN`, normal preparation has already produced:

```text
prepared parent:
    parent_object_id
    template_id
    template_version
    canonical_name

resolved slot:
    slot_name
    slot_declaring_template_id
    target_template_id

requested children:
    child_object_ids
    child stable template_ids
    child canonical_names
```

The slot comes from the READY immutable `component_schema` facet. Child compatibility has been resolved from stable ancestry knowledge. No preliminary current-owner read is performed.

## Final UoW

```text
BEGIN

Q1  acquire OWNERSHIP_GRAPH_WRITE_GATE

Q2  parent Object @ FOR NO KEY UPDATE
    -> reread id/template_id/template_version
    -> absent: fail
    -> binding differs from preparation: 409 concurrent_object_change
    -> binding unchanged: continue

Q3  one protected graph-admission statement
    -> has_owned_requested_child
    -> recursively derive root(parent)
    -> root_is_requested

    has_owned_requested_child = true
        -> 409 ownership_conflict

    else root_is_requested = true
        -> 409 ownership_cycle

    else
        -> continue

Q4  one bulk INSERT object_components
    -> no ON CONFLICT
    -> any PK/FK/CHECK failure aborts the whole batch

Q5  one bulk INSERT lifecycle ATTACH_TO
    -> one event per inserted edge

COMMIT
```

Any failure rolls back the entire batch.

## Q1 — graph edge-add arbitration

`OWNERSHIP_GRAPH_WRITE_GATE` is transaction-scoped and acquired once for the batch.

It serializes ATTACH edge additions around the transitive cycle predicate. It is not acquired per child.

DETACH does not require the gate because removing an edge cannot introduce a cycle.

## Q2 — parent stabilization

Q2 conceptually is:

```sql
SELECT id, template_id, template_version
FROM objects
WHERE id = :parent_object_id
FOR NO KEY UPDATE;
```

The lock protects the semantic relation between the exact parent schema used to resolve the component slot and the outgoing edges committed by this ATTACH.

If the binding changed, ATTACH does not re-resolve a new slot while locks are held. The attempt fails conservatively.

## Q3 — graph admission

Q3 is one statement/snapshot under the graph gate.

Because current ownership is single-owner, after every requested child is certified ownerless a requested child can be an ancestor of the parent only if it is exactly `root(parent)`.

Thus the cycle test is root-only, not full-chain intersection:

```text
all requested children ownerless
AND
root(parent) not requested
```

The statement returns separate conflict/cycle facts so the public failure can be selected without diagnostic rereads.

## Q4 — ownership persistence

Q4 attempts every requested edge in one multi-row INSERT.

There is no idempotent identical-edge path. An already-owned child, including one already attached to the exact same parent/slot, causes conflict/failure of the whole batch.

Relational constraints remain final authorities for:

```text
single owner
parent/child lifetime
self-edge prevention
```

They also close residual races between Q3 and the actual write where applicable.

## Q5 — lifecycle persistence

Q5 writes all required ATTACH_TO lifecycle rows in one bulk statement.

Lifecycle display names are best-effort historical values obtained from normal preparation; no rereads or additional locks exist only to improve their freshness.

## Diagnostic rule

No PostgreSQL statement may be issued solely to improve a failure message or identify a more precise failing child after the decisive gate/constraint has failed.

Error precedence follows this execution order.

## Cost

Successful path, excluding BEGIN/COMMIT:

```text
warm      = 7 PostgreSQL statements + COMMIT
full-cold = 9 PostgreSQL statements + COMMIT
```

The count includes Q1 advisory gate acquisition. It is independent of child batch cardinality; row volume grows with the batch and recursive Q3 work grows with parent ownership depth.

Physical index selection and EXPLAIN evidence remain deferred to the global M4 relational-schema phase.
