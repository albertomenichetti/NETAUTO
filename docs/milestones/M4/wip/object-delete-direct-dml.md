# M4 WIP — Object DELETE direct DML candidate

Status: FROZEN DISCOVERY INPUT / M4 WIP / ALWAYS NON-NORMATIVE

## Scope

This note records the current route-local M4 candidate data path for:

```http
DELETE /api/v1/core/objects/{object_id}
```

The public contract is tracked separately in `object-delete-public-contract.md`.

This file freezes only the current discovery candidate. Final transaction, locking, wait-for graph, FK realization and verification remain architecture-phase responsibilities.

## Candidate direction

Object DELETE should not perform a preliminary blocker-count query, a separate Object snapshot read, or ObjectTemplate/DataType recertification solely to decide whether the Object may be deleted.

The candidate path is:

```text
BEGIN

Q1  DELETE FROM objects
    WHERE id = :object_id
    RETURNING
        id,
        canonical_name,
        template_id,
        template_version,
        properties

Q2  INSERT one DELETED lifecycle event
    from Q1 returned row
    without RETURNING

COMMIT
```

Successful route-local candidate cost:

```text
2 PostgreSQL business statements + COMMIT
```

There is no cache warm/cold distinction and no model-plane read.

## Q1 authority

Q1 is both:

```text
current Object existence test
+
actual root DML
+
authoritative before-snapshot capture
```

### Missing Object

```text
DELETE ... RETURNING returns zero rows
    -> ROLLBACK
    -> 404 resource_not_found
```

A second DELETE after an already-committed delete therefore remains non-convergent and returns `404`.

### Current references

Current cross-aggregate references to `objects.id` remain protected by PostgreSQL FK lifetime constraints.

Relevant current families include at least:

```text
object_components.child_object_id
object_components.parent_object_id
runtime_relationship_resolutions.from_object_id
runtime_relationship_resolutions.to_object_id
```

If any blocking reference wins before the Object deletion can commit, the Object DELETE statement fails through the relevant FK authority and the application maps the recognized current-reference failure to:

```text
409 delete_blocked
```

The M4 public contract does not require exact blocker counts, blocker identity lists, or an exhaustive blocker-type census.

No PostgreSQL query is issued solely to enrich `delete_blocked` diagnostics.

### Successful delete

If Q1 deletes one row, its `RETURNING` payload is the authoritative historical before snapshot for the DELETED lifecycle event:

```text
id
canonical_name
template_id
template_version
properties
```

No separate pre-delete Object SELECT is required solely for lifecycle capture.

## No blocker precheck

The current AS-IS `delete_blocker_counts()` query is not the correctness authority. PostgreSQL FK arbitration already determines whether a current reference prevents deletion.

The candidate therefore removes the normal-path pattern:

```text
count blockers
-> if zero, attempt DELETE
```

and uses instead:

```text
attempt DELETE directly
-> FK success/failure is the authoritative lifetime result
```

This removes an always-paid round trip and avoids scanning current reference sets merely for diagnostics.

## No persisted-state semantic recertification

DELETE admission asks whether the Object lifetime may end. It does not require re-proving that the already-persisted Object is semantically valid under its exact ObjectTemplate/DataType closure.

The candidate therefore does not perform DELETE-only work equivalent to:

```text
ObjectTemplate effective-schema reconstruction
DataTypeVersion loading
runtime-property re-canonicalization
schema admissibility recertification
ownership-slot interpretation
```

The persisted root row is decoded only to the extent required to produce the historical DELETED snapshot.

## Q2 lifecycle

Q2 inserts exactly one intrinsic lifecycle event:

```text
kind           = DELETED
object_id      = Q1.id
canonical_name = Q1.canonical_name
before_state   = {
    id,
    canonical_name,
    template_id,
    template_version,
    properties
}
after_state    = null
```

The public DELETE response is `204 No Content`; no later route step consumes the generated lifecycle row identity or timestamp.

Therefore the candidate lifecycle INSERT uses no `RETURNING`.

If Q2 fails:

```text
ROLLBACK
```

and Q1 deletion is restored. No Object deletion may commit without its required DELETED lifecycle event.

## Why Q1 and Q2 remain separate

A data-modifying CTE could technically combine Object deletion and lifecycle insertion into one PostgreSQL statement.

The current candidate keeps two statements because:

- PostgreSQL still performs one Object delete plus one lifecycle insert;
- combining them mainly removes one round trip while materially increasing SQL complexity;
- two simple statements preserve the same transaction atomicity;
- statement-count minimization alone is not a project goal.

This tradeoff remains available for later physical-query review.

## Concurrency / architecture handoff

This discovery candidate intentionally does not require preservation of the AS-IS preliminary `OBJ@U` acquisition as a route-local mechanism.

Future M4 architecture closure must compose direct root DELETE arbitration with all affected guarantees and decide the final stabilization mechanism, including at least:

```text
OS  DELETE vs intrinsic Object mutations
RL  DELETE vs ATTACH
RL  DELETE vs DETACH
RL  DELETE vs Relationship CREATE
RL  DELETE vs Relationship DELETE
RL  DELETE vs Relationship mutations retaining endpoint references
RL  Object exact OTV reference removal vs ObjectTemplate lineage delete
ATOMIC  Object deletion + DELETED lifecycle event
```

The architecture phase must prove:

```text
no dangling current references
no mutation-after-delete / resurrection
serially explainable Object state outcomes
no false success
atomic lifecycle emission
no unsupported-path deadlock
```

It may retain, replace, batchify or otherwise redesign the AS-IS LockPlan realization provided those guarantees remain satisfied.

## Supersession note

This candidate supersedes the route-local data-path parts of the older `object-delete-discovery.md` that proposed:

```text
stabilize/load Object snapshot
-> current blocker projection
-> DELETE
-> lifecycle
```

Retained semantic findings from that older note include:

```text
no schema/property recertification for DELETE
no implicit detach / relationship deletion / cascade
FK RESTRICT as final reference-lifetime authority
DELETED lifecycle atomic with real deletion
```

## Frozen discovery takeaway

```text
Object.DELETE candidate

Q1 = DELETE Object ... RETURNING before snapshot
Q2 = one DELETED lifecycle INSERT, no RETURNING

0 blocker-precheck queries
0 separate Object snapshot reads
0 schema/cache/model-plane reads

missing row -> 404
recognized current-reference FK failure -> 409 delete_blocked
success -> 204

candidate success path = 2 PostgreSQL statements + COMMIT
```
