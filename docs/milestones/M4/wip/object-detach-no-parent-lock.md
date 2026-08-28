# M4 WIP — Object DETACH without explicit parent lock

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note freezes the route-local concurrency decision that Object DETACH does not acquire an explicit lock on the parent Object row.

## Frozen public context

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}/detach
```

with a non-empty, duplicate-free batch body:

```json
{
  "child_object_ids": ["...", "..."]
}
```

The batch is atomic and non-convergent: every requested child must currently own exactly the requested parent/slot edge, otherwise the entire batch fails.

## Why no parent lock is required

DETACH is schema-agnostic in M4. It does not resolve or interpret the parent's current ObjectTemplate binding, effective component schema, target lineage, ancestry, or cycle semantics.

The authoritative state being mutated is the persisted ownership edge itself in `object_components`.

Therefore DETACH does not need to stabilize `objects.template_id` / `objects.template_version` against concurrent SCHEMA_CHANGE.

Frozen exclusion:

```text
NO parent Object FOR NO KEY UPDATE
NO ObjectTemplate/cache preparation
NO stable ancestry lookup
NO OWNERSHIP_GRAPH_WRITE_GATE
```

## Concurrency consequences

### DETACH vs DETACH on the same edge

The DELETE of the same `object_components` row is the concurrency rendezvous. PostgreSQL row/write arbitration determines which transaction removes the row. Because DETACH is non-convergent, a competing request that can no longer remove the complete requested batch must fail rather than return false success.

### DETACH vs SCHEMA_CHANGE on the parent

They may proceed concurrently. DETACH does not reinterpret the edge under the parent's new schema; it removes an already-persisted ownership fact whose semantic slot identity is persisted with the edge.

### DETACH vs ATTACH

Current ownership uniqueness and normal PostgreSQL row/constraint arbitration remain authoritative. Once an edge is committed as removed, a later ATTACH is a new mutation and may independently succeed if its admission rules pass.

### DETACH vs Object DELETE

The ownership foreign keys continue to protect parent/child lifetime while the current edge exists. Removing the edge may legitimately unblock a concurrent or subsequent Object DELETE. DETACH does not add an Object-row lock only to preserve an Object after the ownership fact has been removed.

## Relational implication already assumed by M4

The authoritative ownership edge carries its semantic slot identity, including:

```text
child_object_id
parent_object_id
slot_declaring_template_id
slot_name
```

DETACH therefore does not need to reconstruct `slot_declaring_template_id` from the parent's current effective schema before deleting the edge or writing the historical DETACH event.

## Frozen takeaway

```text
DETACH mutates persisted ownership facts directly
-> no parent schema stabilization
-> no parent row lock
-> no graph gate
-> PostgreSQL edge-row/constraint arbitration is authoritative
```
