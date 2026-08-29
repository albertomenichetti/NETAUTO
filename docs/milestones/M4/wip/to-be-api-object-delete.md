# M4 WIP — TO-BE Object DELETE

Status: ROUTE-LOCAL CLOSED / FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note is the current route-local consolidation owner for M4 `Object.DELETE` discovery.

It consolidates the accepted public-contract, direct-DML, lifecycle, failure-mapping and cost findings produced during the top-down Object sweep.

It remains WIP discovery material and must be deliberately revalidated/adopted during the later M4 architecture phase before implementation.

## Public signature

```http
DELETE /api/v1/core/objects/{object_id}
```

Path:

```text
object_id UUID
```

No request body is accepted.

No query parameter is introduced for:

```text
force
cascade
recursive/subtree deletion
implicit detach
implicit Relationship deletion
```

Malformed transport carriers are rejected by normal request validation before the semantic Unit of Work.

## Success semantics

Successful deletion returns:

```http
204 No Content
```

The deleted Object representation is not returned.

Object DELETE removes only the selected Object. It never mutates current references merely to make deletion admissible.

A second DELETE after an already committed deletion is not convergent success:

```text
Object already absent
    -> 404 resource_not_found
```

## Lifetime admission semantics

Deletion is admissible only if no current reference requiring the Object lifetime prevents removal.

Candidate semantic outcomes:

```text
Object absent
    -> 404 resource_not_found

Object exists but a current lifetime dependency blocks removal
    -> 409 delete_blocked

Object exists and no current lifetime dependency blocks removal
    -> delete Object
    -> append exactly one DELETED lifecycle event atomically
    -> COMMIT
    -> 204 No Content
```

DELETE does not:

```text
implicitly DETACH ownership
implicitly delete factual Relationships
implicitly delete a subtree
implicitly rewrite blockers
```

Current lifetime blockers are external current facts whose semantics require the Object to remain alive, including current ownership edges involving the Object and current factual Relationship runtime-closure references involving the Object. Object-owned derived state such as `object_component_slots` is not itself a blocker and is removed with the Object; historical lifecycle state is not a live reference and does not block deletion.

Object DELETE owns only the admission needed to terminate the selected Object lifetime. It does not perform a proactive consistency sweep, schema recertification, blocker census or global-domain audit.

## Public `delete_blocked` contract

The public failure remains intentionally bounded.

Required semantic detail is only the selected resource identity, for example:

```json
{
  "code": "delete_blocked",
  "details": {
    "resource_type": "object",
    "id": "<uuid>"
  }
}
```

The public contract does not require:

```text
blocker identities
complete blocker-type enumeration
exact blocker counts
PostgreSQL constraint names
```

No PostgreSQL statement may be required solely to enrich this diagnostic.

## Required data structures

The candidate route uses only current Object persistence, current lifetime enforcement and lifecycle persistence:

```text
objects
current inbound Object lifetime references
object_lifecycle_events
```

No ObjectTemplate, DataType, effective-schema, ancestry or cache structure is required by the route-local candidate.

## Removed AS-IS work

The current candidate removes DELETE-only work equivalent to:

```text
preliminary blocker-count queries
separate Object snapshot SELECT
ObjectTemplate effective-schema reconstruction
DataTypeVersion loading
persisted-property semantic recertification
ownership-slot interpretation
cache/model-plane preparation
diagnostic-only PostgreSQL reads
```

DELETE admission asks whether Object lifetime may terminate. It does not re-prove the semantic validity of already-persisted Object data.

## Candidate data path

The route-local candidate performs one data-modifying PostgreSQL business statement inside the semantic transaction:

```text
BEGIN

Q1  root DELETE from objects
    -> retain the deleted Object row server-side
    -> construct the historical DELETED before_state server-side
    -> INSERT exactly one DELETED lifecycle row
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

The exact SQL builder, CTE naming and JSON construction functions remain implementation details.

The tiny success carrier exists only to distinguish zero-row absence from one-row successful deletion/event insertion. The application does not fetch the complete lifecycle row, generated event id, timestamp or historical payload.

## Why DELETE and lifecycle are one statement here

An earlier candidate used:

```text
Q1 DELETE ... RETURNING complete Object snapshot
Q2 INSERT DELETED lifecycle
```

That would require the potentially large `properties` JSONB to travel:

```text
PostgreSQL -> application -> PostgreSQL
```

solely to reconstruct the historical snapshot and write it back.

The one-statement candidate keeps the deleted row inside PostgreSQL and feeds the mandatory lifecycle INSERT directly.

This fusion therefore removes real transfer/decoding/encoding work; it is not statement-count minimization for its own sake.

## Outcome and failure mapping

### Missing Object

If the root DELETE produces no row, the lifecycle INSERT also produces no row:

```text
Q1 returns zero success rows
    -> ROLLBACK
    -> 404 resource_not_found
```

### Current lifetime blocker

The root Object DELETE is the current-reference arbitration point.

Route-local candidate mapping:

```text
foreign_key_violation / SQLSTATE 23503
caused by the root DELETE from objects
    -> ROLLBACK
    -> 409 delete_blocked
```

No blocker precheck and no diagnostic reread follows the failure.

Constraint names may remain useful for logging or verification but are not required for public semantic correctness.

### Other PostgreSQL failures

Any persistence failure not classified as path absence or a current-lifetime delete blocker follows the normal bounded persistence/internal-failure policy.

No query is executed solely to discover a more specific diagnostic after failure.

## `23503` scope after statement fusion

The generic `23503 -> delete_blocked` rule is safe only when the combined statement cannot produce an unrelated FK violation from the lifecycle INSERT branch.

The current lifecycle persistence model supports this because historical Object identity/name/snapshot fields are historical data and do not carry live FK references back to current Object/model rows.

Architecture-phase revalidation must therefore preserve one of these conditions:

```text
A. lifecycle INSERT in this statement cannot raise an unrelated 23503

or

B. the final persistence boundary can distinguish the failure source
   without issuing a diagnostic-only PostgreSQL query
```

The route must never map an unrelated persistence defect to `409 delete_blocked` merely because it shares SQLSTATE `23503`.

## Referential-integrity dependency and reopen trigger

The current DELETE contract and one-statement data path deliberately depend on database-enforced referential integrity for Object lifetime arbitration.

In particular, the route assumes that every current external fact whose semantics require an Object to remain alive participates in an atomic database-level arbitration with the root `DELETE FROM objects`, preferably through immediate `RESTRICT` / `NO ACTION` foreign-key semantics or another globally proven database mechanism with equivalent guarantees.

Conceptually:

```text
current external lifetime reference exists
    -> root Object DELETE cannot commit

root Object DELETE commits first
    -> a new conflicting current lifetime reference cannot commit
```

This database-enforcement assumption is part of the current route contract, not merely a physical optimization. It is what allows Object DELETE to avoid blocker prechecks, blocker enumeration, application-side lifetime scans and consistency sweeps.

Therefore any later persistence change that alters the Object lifetime-reference graph or weakens/removes/replaces the database arbitration mechanism is an explicit DELETE revalidation trigger.

Examples include:

```text
adding a new current Object reference that must keep the Object alive
removing or changing an existing lifetime FK
changing CASCADE / RESTRICT / NO ACTION semantics
moving a current lifetime dependency outside database-enforced arbitration
introducing deferred or otherwise materially different enforcement timing
changing the object_component_slots / object_components lifetime composition
changing factual Relationship endpoint lifetime enforcement
```

Such a change must not be treated as transparent to this route. `Object.DELETE` must be reopened and re-proven for lifetime admission, concurrency outcomes, public `delete_blocked` mapping and one-statement correctness before the new persistence design can be considered compatible with the current DELETE contract.

The dependency direction is therefore explicit:

```text
Object.DELETE one-statement contract
    depends on
complete DB-enforced current Object lifetime integrity
```

## Lifecycle mapping

For one successfully deleted Object row:

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

Lifecycle row identity and `occurred_at` remain PostgreSQL-generated persistence concerns.

No current ownership or Relationship state is embedded in the intrinsic DELETED snapshot. Structural history remains represented by its own lifecycle event families.

## Atomicity

Object deletion and the DELETED lifecycle row are one semantic transition.

The candidate guarantees at the statement/UoW level:

```text
root DELETE fails
    -> no DELETED event

lifecycle INSERT fails
    -> entire statement fails
    -> Object deletion does not commit

statement succeeds + COMMIT
    -> Object absence + DELETED event become durable together
```

No committed Object deletion may exist without its required DELETED lifecycle event.

## Candidate cost

Excluding transaction-control commands:

```text
successful PostgreSQL business statements = 1
```

Necessary physical work remains:

```text
1 Object DELETE
+
1 DELETED lifecycle INSERT
+
current reference/FK arbitration
```

Avoided work:

```text
0 blocker-precheck statements
0 separate Object SELECT
0 model-plane/schema reads
0 cache operations
0 diagnostic-only PostgreSQL queries
0 Object properties DB -> app -> DB round-trip
0 lifecycle-row reread/decoding
```

There is no hot/cold-cache distinction.

## Cache

Cache is not useful for this route.

Current Object existence and current reference lifetime are mutable PostgreSQL facts. Historical before-state material is obtained directly from the row actually deleted.

No cache key/value or fill policy is introduced.

## Relational-schema implications

No route-specific new table or denormalized blocker counter is justified.

The candidate does, however, impose two architecture-wide relational requirements:

```text
1. every TO-BE current reference that semantically keeps an Object alive
   must have DELETE-arbitrating enforcement;

2. the lifecycle branch of the fused statement must not make generic 23503
   ambiguous with an unrelated FK failure.
```

The preferred lifetime realization is an immediate `RESTRICT` / `NO ACTION` FK to `objects.id` where the relation is naturally relational, or another globally proven mechanism with equivalent arbitration semantics.

## Concurrency guarantees required

This discovery candidate does not require preservation of the AS-IS preliminary `OBJ@U` lock as a route-local mechanism.

The later M4 architecture phase must compose the candidate with the complete mutation set and prove at least:

```text
OS  DELETE vs intrinsic Object mutations
RL  DELETE vs ATTACH
RL  DELETE vs DETACH
RL  DELETE vs Relationship CREATE
RL  DELETE vs Relationship DELETE
RL  DELETE vs Relationship mutations retaining Object endpoint references
RL  Object exact-OTV reference removal vs ObjectTemplate deletion
ATOMIC  Object deletion + DELETED lifecycle
```

Required final outcomes include:

```text
reference commits first
    -> Object DELETE cannot commit

Object DELETE commits first
    -> a new current reference cannot commit

reference removal commits first
    -> Object DELETE may become admissible

intrinsic Object mutation vs DELETE
    -> serially explainable current-state/lifetime result

no dangling references
no mutation-after-delete/resurrection
no false success
no partial lifecycle transition
no unsupported-path deadlock
```

The final architecture may retain, replace or redesign the delivered LockPlan realization if these guarantees are globally proven.

## Supersession / consolidation map

This file is the current route-local consolidation owner.

### `object-delete-public-contract.md`

Retained and absorbed:

```text
DELETE /objects/{object_id}
204 / 404 / 409 direction
no force/cascade
bounded delete_blocked detail
no diagnostic-only DB work
```

### `object-delete-direct-dml.md`

Retained and absorbed:

```text
one fused DELETE + DELETED lifecycle statement
server-side before_state construction
one-statement success cost
no pre-read / blocker precheck / schema recertification
```

### `object-delete-fk-failure-mapping.md`

Retained:

```text
root Object DELETE foreign-key violation -> delete_blocked
constraint-name independence for semantic correctness
complete lifetime-enforcement architecture handoff
```

Superseded in statement sequencing by the fused one-statement candidate. Its older `Q1 DELETE -> Q2 lifecycle` description is historical only.

### `object-delete-discovery.md`

Retained:

```text
DELETE needs lifetime isolation, not persisted-schema recertification
no implicit detach / Relationship deletion / cascade
FK/reference enforcement is final lifetime authority
DELETED lifecycle must be atomic with real deletion
```

Superseded:

```text
preliminary blocker projection
separate current Object snapshot load
older multi-statement route cost
```

All source WIPs remain non-normative discovery history.

## Route-local closure

`Object.DELETE` is route-locally closed for the M4 top-down discovery sweep on:

- HTTP signature and no-body contract;
- `204` success and non-convergent `404` absence semantics;
- `409 delete_blocked` lifetime semantics;
- bounded public failure detail;
- direct relational lifetime arbitration;
- explicit dependency on complete database-enforced Object lifetime integrity;
- mandatory DELETE revalidation if the lifetime-reference graph or its DB arbitration changes materially;
- no blocker precheck or diagnostic query;
- no ObjectTemplate/DataType recertification;
- one fused root DELETE + DELETED lifecycle statement;
- server-side historical snapshot construction;
- candidate one-statement PostgreSQL success cost;
- no cache use;
- explicit relational/concurrency architecture handoffs.

The later M4 architecture phase must deliberately adopt, modify, supersede or discard this candidate when performing global relational, transaction, LockPlan, wait-for and verification closure.
