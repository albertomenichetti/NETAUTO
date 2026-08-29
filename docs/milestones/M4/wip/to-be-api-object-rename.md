# M4 WIP — TO-BE Object canonical-name mutation

Status: ROUTE-LOCAL ACTIVE REVALIDATION / M4 WIP / NON-NORMATIVE GLOBALLY

## Public signature

```http
PUT /api/v1/core/objects/{object_id}/canonical-name
Content-Type: application/json
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

No query parameters are accepted.

`canonical_name` remains required current Object state with the existing semantic constraints:

```text
string
1..255 characters
no automatic normalization
not unique
not an alternative Object identity
```

Malformed body/carrier, missing or explicit-null `canonical_name`, empty string and values longer than 255 characters belong to the normal `400 invalid_request` transport boundary.

Success:

```http
204 No Content
```

The mutation does not return the full Object representation. Current representation remains owned by `GET /objects/{id}`.

Missing path target:

```text
Object absent
    -> 404 resource_not_found
```

## Same-name semantics

The command semantics are assignment:

```text
Object O canonical_name := requested_name
```

not conditional change-only-if-different.

Therefore a same-name request is a normal successful mutation:

```text
Object exists + current name differs
    -> 204

Object exists + current name already equals requested name
    -> 204
```

No preliminary equality check is required merely to distinguish those cases. A successful same-name assignment follows the normal RENAME lifecycle path and may therefore produce a RENAME event whose before/after canonical-name values are equal.

This remains intentionally different from DATA_CHANGE, where a semantic no-op emits no fake lifecycle transition.

## Semantic responsibility boundary

RENAME changes only:

```text
canonical_name
```

It preserves:

```text
Object.id
Object.template_id
Object.template_version
Object.properties
ownership/component facts
factual Relationships
```

The requested name is validated from caller input. RENAME does not re-certify persisted Object state against ObjectTemplate/DataType semantics and does not perform a domain consistency sweep.

Normal path requires no:

```text
ObjectTemplate reads
DataType reads
effective-schema reconstruction
ancestry reads
ownership reads
Relationship reads
semantic cache
```

## Ratified lifecycle semantics — exact minimal transition

The lifecycle contract follows the general M4 principle that an event records the complete exact semantic transition owned by its operation, not automatically a complete before/after aggregate snapshot.

For RENAME, the complete semantic transition is only:

```text
canonical_name: old -> new
```

Therefore the RENAME lifecycle payload must record the exact old and new canonical-name values, but it must **not** duplicate unchanged intrinsic or structural Object state merely for payload uniformity.

Conceptually:

```text
RENAME event
    object_id = O

    before:
        canonical_name = old_name

    after:
        canonical_name = requested_name
```

Equivalent generic JSON-carrier direction:

```json
{
  "before": {
    "canonical_name": "server-1"
  },
  "after": {
    "canonical_name": "server-2"
  }
}
```

The exact final persistence/DTO carrier remains lifecycle-architecture work. The semantic requirement is the exact old/new name transition.

The RENAME event does not need to copy:

```text
id inside before/after payloads when object_id is already event identity
template_id
template_version
properties
ownership/components
Relationships
```

because RENAME cannot modify those facts.

This supersedes both earlier RENAME lifecycle candidates:

```text
full intrinsic before/after snapshots
best-effort / approximate full intrinsic snapshots
```

The former is unnecessary duplication and creates artificial coupling to unrelated intrinsic mutations; the latter weakens historical precision without need.

Current-state mutation and RENAME lifecycle event remain atomic. What becomes narrower is only the historical payload responsibility.

## Logical execution requirement

The logical route needs only the exact current name and the new requested name:

```text
validate canonical_name
    -> CPU only

BEGIN

obtain/protect current Object existence + exact old canonical_name
    absent -> 404 resource_not_found

perform canonical_name-only update

insert exactly one RENAME lifecycle event
    old canonical_name -> requested canonical_name

COMMIT
```

A same-name request follows the same path and may record:

```text
old_name == new_name
```

No complete Object snapshot is needed for RENAME lifecycle construction.

## Physical realization handoff

M4 discovery does not freeze whether architecture realizes the logical flow using:

```text
protected current-name read + UPDATE + lifecycle INSERT

one safe PostgreSQL old/new-name carrier + lifecycle INSERT

or another equivalent fused realization
```

Exact SQL, statement fusion and row-lock mode remain architecture concerns.

Any realization must preserve:

```text
exact old canonical_name
exact requested/new canonical_name
canonical_name-only current write
atomic Object + RENAME lifecycle transition
no lost same-field rename transition
no mutation-after-delete / resurrection
```

No PostgreSQL-version-specific optimization is part of the semantic contract.

## Concurrency direction

The lifecycle narrowing removes the need for RENAME to serialize semantically with unrelated intrinsic fields merely to obtain a complete aggregate snapshot.

Required route-level outcomes:

```text
RENAME x RENAME on same Object
    -> each real assignment has an exact old -> new name transition
    -> transitions are serially explainable
    -> final canonical_name is one complete committed assignment

RENAME x DATA_CHANGE on same Object
    -> neither operation overwrites the other's field ownership
    -> RENAME lifecycle needs no properties snapshot

RENAME x SCHEMA_CHANGE on same Object
    -> neither operation overwrites the other's field ownership
    -> RENAME lifecycle needs no exact binding/properties snapshot

RENAME x DELETE on same Object
    -> RENAME commits before DELETE
       OR DELETE wins and RENAME cannot commit against/resurrect the absent Object
```

PostgreSQL may still physically serialize updates to the same `objects` row. Such physical contention does not enlarge RENAME's semantic responsibility.

RENAME is semantically independent from ATTACH/DETACH current ownership state. Relationship/ownership event display-name coherence, where required by those operations, belongs to those operations' own lifecycle contracts rather than causing RENAME to load or validate their state.

Exact locking/wait-for realization remains architecture work.

## Failure mapping

Bounded public failures:

```text
400 invalid_request
    malformed/static transport input
    invalid canonical_name carrier/value

404 resource_not_found
    selected Object does not exist at mutation admission

500 internal_error
    unexpected persistence/lifecycle/invariant failure
```

The operation introduces no semantic `409`, `422`, name-conflict, schema-admission or ownership-admission failure class.

## Cost/cache/schema direction

There is no warm/cold cache distinction and no route-specific cache.

Logical required data is bounded to:

```text
current Object existence
old canonical_name
requested canonical_name
one RENAME lifecycle transition
```

A straightforward safe realization may use:

```text
1 protected current-name read
1 canonical_name UPDATE
1 lifecycle INSERT
+ COMMIT
```

but exact statement count remains an architecture optimization target rather than a discovery contract.

No route-specific table, denormalization, materialization or index is introduced.

## Revalidation status

Ratified during the current full-sweep pass:

- public contract;
- `204` / `404` / `400` direction;
- same-name assignment semantics;
- semantic responsibility boundary;
- exact minimal RENAME lifecycle payload;
- no schema/model/cache recertification;
- bounded current-name mutation path;
- route-level concurrency/failure direction.

The remaining work is consolidation into the main Object route owner and final full-sweep closure/cleanup.