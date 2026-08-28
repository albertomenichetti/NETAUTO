# M4 WIP — Object DELETE direct DML candidate

Status: FROZEN DISCOVERY INPUT / M4 WIP / ALWAYS NON-NORMATIVE

## Scope

This note records the current route-local M4 candidate data path for:

```http
DELETE /api/v1/core/objects/{object_id}
```

The public contract is tracked separately in `object-delete-public-contract.md`; FK failure mapping is tracked in `object-delete-fk-failure-mapping.md`.

This file freezes only the current discovery candidate. Final transaction, locking, wait-for graph, FK realization and verification remain architecture-phase responsibilities.

## Current candidate direction

Object DELETE should not perform:

```text
preliminary blocker-count query
separate Object snapshot read
ObjectTemplate/DataType recertification
cache/model-plane work
PostgreSQL diagnostics-only queries
```

The current candidate is one data-modifying PostgreSQL statement inside the semantic transaction:

```text
BEGIN

Q1  DELETE Object
    -> retain deleted row server-side
    -> construct DELETED before_state server-side
    -> INSERT one DELETED lifecycle row
    -> return only a tiny success carrier

COMMIT
```

Conceptually:

```sql
WITH deleted AS (
    DELETE FROM objects
    WHERE id = :object_id
    RETURNING
        id,
        canonical_name,
        template_id,
        template_version,
        properties
)
INSERT INTO object_lifecycle_events (
    kind,
    object_id,
    canonical_name,
    before_state,
    after_state
)
SELECT
    'DELETED',
    id,
    canonical_name,
    jsonb_build_object(
        'id', id::text,
        'canonical_name', canonical_name,
        'template_id', template_id::text,
        'template_version', template_version,
        'properties', properties
    ),
    NULL
FROM deleted
RETURNING object_id;
```

The exact SQL carrier/build functions remain implementation details.

## Why the single statement supersedes the earlier two-statement candidate

The previous candidate used:

```text
Q1 DELETE ... RETURNING complete Object before snapshot
Q2 INSERT DELETED lifecycle
```

That shape required the potentially large `properties` JSONB to travel:

```text
PostgreSQL -> application -> PostgreSQL
```

solely so the application could rebuild the lifecycle `before_state` and write the same payload back.

The single-statement candidate avoids that transfer, decode and re-encode. The deleted row remains inside PostgreSQL and feeds the mandatory lifecycle INSERT directly.

This refinement is therefore based on reduced real work, not statement-count minimization for its own sake.

## Outcome classification

### Missing Object

If the `deleted` CTE produces no row, the lifecycle INSERT also produces no row:

```text
Q1 returns zero success rows
    -> ROLLBACK
    -> 404 resource_not_found
```

A second DELETE after an already committed deletion remains non-convergent and returns `404`.

### Current reference blocker

The root `DELETE FROM objects` remains subject to current inbound lifetime enforcement.

Per the separate failure-mapping checkpoint:

```text
SQLSTATE 23503 during this root Object DELETE
    -> ROLLBACK
    -> 409 delete_blocked
```

No blocker count, blocker type or constraint-name whitelist is required by the public contract.

### Successful delete

Exactly one returned success row means:

```text
Object root deleted in the transaction
+
one DELETED lifecycle row inserted from that exact deleted row
```

The route commits and returns:

```http
204 No Content
```

The returned carrier should remain minimal; the application does not need lifecycle `id`, `occurred_at`, `before_state` or the full event row.

## Lifecycle mapping

The lifecycle row is constructed directly from the deleted Object row:

```text
kind           = DELETED
object_id      = deleted.id
canonical_name = deleted.canonical_name
before_state   = {
    id,
    canonical_name,
    template_id,
    template_version,
    properties
}
after_state    = null
```

Lifecycle row identity and timestamp remain PostgreSQL-generated/current persistence concerns.

Historical lifecycle identity/name fields remain historical data and do not create a live FK back to the deleted Object.

## Atomicity

DELETE and lifecycle INSERT are part of the same data-modifying statement and semantic transaction.

Therefore:

```text
root DELETE fails
    -> no lifecycle row

lifecycle INSERT fails
    -> whole statement fails
    -> Object deletion does not commit

statement succeeds + COMMIT
    -> deletion and DELETED event become durable together
```

No committed Object deletion may exist without its required lifecycle event.

## No blocker precheck

The AS-IS `delete_blocker_counts()` query is not the correctness authority. PostgreSQL lifetime arbitration is the definitive current-reference result.

The candidate uses:

```text
attempt root DELETE directly
-> success or FK-arbitrated failure
```

rather than:

```text
count blockers
-> attempt DELETE only when counts are zero
```

No PostgreSQL work is performed solely to enrich `delete_blocked` diagnostics.

## No persisted-state semantic recertification

DELETE asks whether Object lifetime may terminate; it does not re-prove the semantic validity of already-persisted Object data.

The candidate performs no DELETE-only:

```text
ObjectTemplate effective-schema reconstruction
DataTypeVersion loading
runtime-property re-canonicalization
schema admissibility recertification
ownership-slot interpretation
```

## Candidate cost

Excluding transaction-control commands:

```text
success path = 1 PostgreSQL business statement
```

The statement performs the necessary physical work:

```text
1 Object DELETE
+
1 DELETED lifecycle INSERT
+
current FK arbitration
```

while avoiding:

```text
blocker precheck round trips
separate Object pre-read
Object payload DB -> app -> DB transfer
lifecycle reread/decoding
model-plane/cache work
```

There is no hot/cold-cache distinction.

## Concurrency / architecture handoff

This discovery candidate intentionally does not require preservation of the AS-IS preliminary `OBJ@U` acquisition as a route-local mechanism.

Future M4 architecture closure must compose the one-statement direct root DELETE with all affected guarantees and decide the final stabilization/arbitration protocol, including at least:

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

Every TO-BE current dependency that must keep an Object alive must have FK enforcement or another proven arbitration mechanism capable of preventing a false-success root DELETE.

## Supersession note

This current candidate supersedes:

1. the route-local data-path parts of older `object-delete-discovery.md` that proposed a blocker projection before DELETE;
2. the earlier revision of this file that used two PostgreSQL business statements (`DELETE ... RETURNING` followed by a separate lifecycle INSERT).

Retained semantic findings include:

```text
no schema/property recertification for DELETE
no implicit detach / relationship deletion / cascade
current lifetime enforcement is authoritative
DELETED lifecycle atomic with the real deletion
```

## Frozen discovery takeaway

```text
Object.DELETE current candidate

one data-modifying PostgreSQL statement:
    DELETE objects
    -> keep deleted row server-side
    -> build before_state server-side
    -> INSERT DELETED lifecycle
    -> tiny success carrier only

0 blocker-precheck queries
0 separate Object reads
0 schema/cache/model-plane reads
0 Object properties round-trip through application

missing Object -> 404
23503 on root Object DELETE -> 409 delete_blocked
success -> COMMIT -> 204

candidate success path = 1 PostgreSQL business statement + COMMIT
```
