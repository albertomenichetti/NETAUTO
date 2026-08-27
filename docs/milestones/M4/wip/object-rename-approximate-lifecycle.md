# M4 WIP — Object RENAME approximate lifecycle semantics

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note freezes a deliberate semantic simplification for the M4 TO-BE `Object.RENAME` path.

Public candidate:

```http
PUT /api/v1/core/objects/{object_id}/canonical-name
```

```json
{
  "canonical_name": "server-2"
}
```

Success:

```http
204 No Content
```

## Decision

`canonical_name` is treated as low-criticality mutable human/search metadata rather than a correctness-bearing structural field.

Therefore `RENAME` does not pay for a protected exact-before snapshot merely to make the lifecycle payload perfectly reflect concurrent intrinsic Object mutations.

The command may perform an unlocked preliminary read of the complete intrinsic Object snapshot for lifecycle construction, then execute the actual mutation separately.

Conceptually:

```text
Q1 unlocked preliminary Object read
    -> complete intrinsic snapshot S

build approximate lifecycle_before = S
build approximate lifecycle_after  = S with canonical_name replaced

Q2 mutation UoW
    -> UPDATE objects SET canonical_name = :new_name WHERE id = :object_id
    -> INSERT RENAME lifecycle event using the prepared before/after snapshots
    -> atomically commit mutation + event
```

The update is intentionally unconditional with respect to the current name.

```text
0 updated rows
    -> Object absent -> request fails

1 updated row
    -> success 204
    -> same-name and different-name requests are not distinguished
```

A same-name request therefore follows the normal mutation path and may emit a `RENAME` lifecycle event whose before/after names are equal.

## Accepted race semantics

Between Q1 and Q2 another intrinsic Object mutation may commit, for example:

```text
DATA_CHANGE
SCHEMA_CHANGE
another RENAME
```

`RENAME` itself updates only:

```text
canonical_name
```

so it does not overwrite concurrent `properties`, `template_version`, ownership or Relationship state.

The current `objects` row remains authoritative and correct.

However, the RENAME lifecycle `before_state` / `after_state` prepared from Q1 may be stale with respect to concurrently changed intrinsic fields. This is explicitly accepted for this operation.

Example:

```text
Q1 observes:
    name = server-1
    template_version = 4
    properties = P1

concurrent SCHEMA_CHANGE commits:
    template_version = 5
    properties = P2

RENAME commits:
    canonical_name = server-2

RENAME lifecycle may still record:
    before  = server-1 / v4 / P1
    after   = server-2 / v4 / P1

while the committed current Object is:
    server-2 / v5 / P2
```

This is an approximate historical observation for `RENAME`, not a false current-state success.

## Why this is acceptable

The design intentionally prioritizes the cost of a lightweight metadata mutation over exact historical reconstruction for this specific event kind.

The accepted asymmetry is:

```text
current Object correctness
    -> strong

RENAME lifecycle exactness under concurrent unrelated intrinsic mutations
    -> best-effort / approximate
```

No corresponding relaxation is implied for correctness-bearing operations such as `DATA_CHANGE`, `SCHEMA_CHANGE`, ownership mutations, factual Relationship mutations or DELETE.

## Concurrency implication

No explicit Object row lock is required solely to obtain an exact lifecycle before-state for RENAME.

The `UPDATE` itself provides normal PostgreSQL row-update serialization for `canonical_name`.

The global concurrency phase must reconcile this operation-specific relaxed lifecycle guarantee with the broader lifecycle documentation, which currently describes intrinsic before/after snapshots more strongly.

That existing stronger wording is intentionally superseded for RENAME by this M4 candidate if the decision is promoted into normative architecture.

## Cost implication

Normal successful TO-BE RENAME can remain bounded to:

```text
1 unlocked Object read
1 mutation statement (preferably UPDATE + lifecycle INSERT fused)
```

plus transaction control.

No ObjectTemplate/DataType semantic reads, cache fills, ancestry, ownership reads or Relationship reads are required.
