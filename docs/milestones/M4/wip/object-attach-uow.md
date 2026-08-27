# M4 WIP — Object ATTACH batch Unit of Work

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note records the statement-by-statement mutation Unit of Work for the M4 TO-BE batch ATTACH surface:

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}
```

The public contract, cache-first slot resolution, child bulk validation, ancestry cache, relational arbitration and cycle-safety rationale are recorded in dedicated M4 WIP notes.

## Preparation identity carried into the UoW

Before opening the mutation UoW, the command has already resolved and validated the immutable/model-plane knowledge needed for the candidate, including:

```text
prepared parent binding:
    parent_object_id
    parent_template_id
    parent_template_version

resolved effective slot:
    slot_name
    slot_declaring_template_id
    target_template_id

requested child_object_ids
```

The parent exact slot was resolved from the READY immutable `component_schema` facet. The candidate may therefore reuse that semantic knowledge inside the mutation attempt only if the protected parent binding remains unchanged.

## Q1 — ownership graph write gate

The first mutation-step arbitration is the transaction-scoped ownership graph edge-add gate:

```text
Q1 acquire OWNERSHIP_GRAPH_WRITE_GATE
```

Conceptually:

```sql
SELECT pg_advisory_xact_lock(:ownership_graph_write_gate);
```

Purpose:

- serialize ownership **edge additions** around the transitive acyclicity predicate;
- ensure no competing ATTACH can add graph structure between cycle certification and commit;
- amortize graph arbitration once for the whole batch rather than once per child.

The gate is not a public busy/conflict outcome. A waiter waits and then evaluates fresh protected graph state.

DETACH does not require this edge-add gate because edge removal cannot create a cycle. A concurrent DETACH may only make a later predicate less restrictive; conservative false failure remains acceptable.

## Q2 — protected parent binding

After the graph gate, the parent Object is the concurrency owner of its current exact schema and outgoing ownership validity.

Q2 locks and rereads the minimal parent binding:

```sql
SELECT
    id,
    template_id,
    template_version
FROM objects
WHERE id = :parent_object_id
FOR NO KEY UPDATE;
```

### Parent absent

```text
0 rows
    -> path Object absent
    -> fail / rollback
```

### Binding unchanged

The protected row is compared with the exact binding used during preparation:

```text
protected template_id      == prepared template_id
AND
protected template_version == prepared template_version
```

If equal, the already-resolved immutable slot remains valid because the exact ObjectTemplateVersion semantic closure is immutable.

No ObjectTemplate cache fill, effective-component reread or schema traversal is performed while holding the Object lock.

### Binding changed

If the current protected binding differs from the prepared binding:

```text
-> fail conservatively
-> rollback current ATTACH attempt
```

The operation does not silently re-resolve another slot contract while holding the mutation locks. A fresh caller request may observe and validate the new current schema.

## Why the parent lock is required

The explicit parent Object lock is not primarily a lifetime mechanism. Parent/child lifetime is also protected by the relational foreign keys when ownership edges are inserted.

The parent lock instead protects the semantic invariant:

```text
resolved current exact parent slot
<->
persisted outgoing ownership edge
```

Without this rendezvous, preparation could resolve a slot under parent version `V1`, a concurrent SCHEMA_CHANGE could commit `V2`, and ATTACH could persist an edge no longer admitted by the parent's current exact schema.

The parent `FOR NO KEY UPDATE` lock serializes with parent SCHEMA_CHANGE until the ATTACH transaction commits or rolls back.

## Frozen sequence so far

```text
BEGIN

Q1 OWNERSHIP_GRAPH_WRITE_GATE

Q2 parent Object @ FOR NO KEY UPDATE
   -> absent: fail
   -> binding changed: fail conservatively
   -> binding unchanged: continue

Q3 graph/current-owner certification
   -> to be frozen next

...
COMMIT / ROLLBACK
```

Exact physical index review remains deferred to the final M4 relational-schema phase.
