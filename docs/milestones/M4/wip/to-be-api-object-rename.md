# M4 WIP — TO-BE Object canonical-name mutation

Status: ROUTE-LOCAL CLOSED / FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Public signature

```http
PUT /api/v1/core/objects/{object_id}/canonical-name
```

Path:

```text
object_id UUID
```

Request body:

```json
{
  "canonical_name": "server-2"
}
```

`canonical_name` remains required current Object state with the existing semantic constraints:

```text
1..255 characters
no automatic normalization
not unique
not an alternative Object identity
```

Success:

```http
204 No Content
```

The mutation does not return the full Object representation.

## Same-name semantics

The command does not compare the requested value with the currently persisted name before writing.

```text
UPDATE objects
SET canonical_name = requested_name
WHERE id = object_id
```

Therefore:

```text
0 updated rows
    -> Object absent -> path-resource error

1 updated row
    -> success 204
    -> same-name and different-name assignments are intentionally not distinguished
```

A same-name request follows the normal mutation path and may emit a normal `RENAME` lifecycle event.

This supersedes the earlier same-name no-op candidate.

## Minimal TO-BE data path

Input validation of `canonical_name` is pure CPU work.

The runtime path is intentionally small:

```text
Q1 unlocked preliminary Object read
    -> complete intrinsic Object snapshot S
    -> used only to prepare lifecycle before/after

BEGIN short mutation UoW

Q2 UPDATE objects
    SET canonical_name = :new_name
    WHERE id = :object_id

    0 rows -> Object absent -> rollback/error
    1 row  -> continue

Q3 INSERT one RENAME lifecycle event
    before_state = S
    after_state  = S with canonical_name replaced

COMMIT
```

No ObjectTemplate, DataType, effective-schema, ancestry, ownership or Relationship knowledge is required.

## Lifecycle precision

`canonical_name` is low-criticality human/search metadata. `RENAME` deliberately does not pay for a protected exact-before snapshot.

Q1 is not row-locked. A concurrent intrinsic mutation can therefore make the prepared lifecycle before/after snapshots stale relative to the exact Object state at Q2.

This is accepted for `RENAME` only:

```text
current objects row correctness
    -> strong

RENAME lifecycle snapshot exactness under concurrent unrelated mutation
    -> best-effort / approximate
```

The mutation itself updates only `canonical_name`; it does not overwrite concurrent `properties`, `template_version`, ownership or Relationship state.

The event insert remains atomic with the rename update inside the same UoW. What is relaxed is the exactness of the historical snapshot content, not mutation/event commit atomicity.

## Concurrency behavior

No explicit Object row lock or optimistic fingerprint is required for RENAME.

The `UPDATE` itself is the PostgreSQL row-update concurrency rendezvous for `canonical_name`.

Concurrent RENAME assignments serialize as ordinary row updates; the final current name follows normal last-committed-writer behavior.

Concurrent DATA_CHANGE or SCHEMA_CHANGE do not need semantic coordination with RENAME merely to protect current Object correctness because their intended writes do not replace `canonical_name`; the global concurrency phase must preserve this column-level non-overwrite property in the final concrete SQL realization.

DELETE races are resolved by normal row lifetime/update behavior; an update that finds no current Object fails as path-resource absence.

## Cost

Route-total successful cost, excluding transaction-control commands:

```text
1 preliminary SELECT of one Object row
1 UPDATE of one Object row
1 INSERT of one lifecycle event row

= 3 PostgreSQL business statements
```

Mutation-UoW write cost specifically:

```text
1 Object UPDATE
1 lifecycle INSERT

= 2 write statements
```

All statements are bounded and PK-addressed or append-only. There is no model traversal, N+1 work or semantic recertification.

## Cache

Cache is not useful for this route.

The requested new name is caller input, current Object existence/current state belongs to PostgreSQL, and the lifecycle preparatory snapshot must observe current persisted data rather than worker-local cached state.

No cache key/value or fill path is introduced.

## Relational-schema implications

None.

The route uses the existing authoritative structures:

```text
objects
object_lifecycle_events
```

No new table, denormalization, materialization, key or route-specific index is required.

Physical index review remains part of the later architecture-wide relational/index phase, but this route introduces no new access pattern beyond Object PK lookup/update and lifecycle append.

## Public-surface rationale

The canonical-name change remains an explicit Object subresource mutation rather than introducing a generic Object PATCH/update operation:

```text
PUT /objects/{id}/canonical-name
```

This makes the replaced field explicit while retaining a narrow semantic mutation surface.

## Route-local closure

This operation is route-locally closed for the M4 TO-BE sweep on:

- HTTP signature and wire contract;
- success/error direction;
- same-name semantics;
- minimal data path;
- lifecycle semantics;
- concurrency guarantee;
- exact warm/cold cost (cache is irrelevant, so there is no warm/cold distinction);
- cache policy;
- relational-schema implications.

The later global concurrency/schema phase may change concrete SQL/lock realization only if required by cross-operation proof; it must preserve the caller-visible semantics and the explicitly accepted approximate RENAME lifecycle guarantee recorded here.
