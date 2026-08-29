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

## Exact lifecycle semantics — revalidated

The earlier M4 candidate that accepted best-effort/approximate RENAME lifecycle snapshots is superseded.

The delivered Object semantic contract requires RENAME to produce exact complete intrinsic snapshots of the Object generation on which the rename is actually performed:

```text
RENAME.before
    = exact complete intrinsic Object state immediately before this rename transition

RENAME.after
    = exact complete intrinsic Object state immediately after this rename transition

allowed semantic difference
    = canonical_name only
```

Intrinsic snapshot fields remain:

```text
id
canonical_name
template_id
template_version
properties
```

Therefore a concurrent DATA_CHANGE or SCHEMA_CHANGE must not cause the RENAME event to mix a stale preliminary intrinsic generation with a later row mutation.

Example requirement:

```text
SCHEMA_CHANGE commits first
    -> RENAME before/after use the post-SCHEMA_CHANGE exact binding/properties

RENAME commits first
    -> RENAME before/after use the pre-SCHEMA_CHANGE exact binding/properties
```

A hybrid historical event whose `before`/`after` do not describe the Object generation actually renamed is not accepted.

The reason to keep the stronger guarantee is also proportional: RENAME is not expected to be a high-frequency operation, so M4 does not weaken historical correctness merely to avoid bounded synchronization work.

## Logical execution requirement

The logical mutation flow is:

```text
validate canonical_name
    -> CPU only

BEGIN

obtain/protect exact current intrinsic Object state S
    absent -> 404 resource_not_found

perform canonical_name-only update against that protected generation

construct exact after state:
    S with canonical_name = requested_name

insert exactly one RENAME lifecycle event
    before_state = S
    after_state  = after

COMMIT
```

Current Object transition and its RENAME event commit or rollback atomically.

The route requirement is exactness and serialization, not a frozen statement count or PostgreSQL lock mode.

## Physical realization handoff

M4 discovery does not yet freeze whether architecture realizes the logical flow using:

```text
protected SELECT + UPDATE + lifecycle INSERT

UPDATE with an adequate old/new carrier + lifecycle INSERT

or another safe fused PostgreSQL realization
```

The exact SQL shape, row-lock mode, statement fusion and PostgreSQL-version-specific facilities are architecture concerns.

Any realization must preserve:

```text
exact before/after intrinsic snapshots
canonical_name-only current write
atomic Object + lifecycle transition
no lost intrinsic Object changes
no mutation-after-delete / resurrection
```

A PostgreSQL-version-specific optimization must not become an unstated semantic dependency of the route.

## Concurrency direction

RENAME participates in the complete-Object-state (`OS`) concurrency contract when racing with intrinsic mutations of the same Object.

Required outcomes are serially explainable:

```text
RENAME x RENAME
    -> both real transitions serialize
    -> each lifecycle event describes its own exact transition
    -> final canonical_name follows the serial commit order

RENAME x DATA_CHANGE
    -> one complete transition before the other
    -> RENAME never overwrites properties

RENAME x SCHEMA_CHANGE
    -> one complete transition before the other
    -> RENAME never overwrites exact binding/properties

RENAME x DELETE
    -> RENAME commits before DELETE
       OR DELETE wins and RENAME cannot commit against/resurrect the absent Object
```

RENAME is semantically independent from ownership mutations merely because the same Object participates; it does not read or change ownership state.

Exact locking/wait-for realization remains architecture work.

## Cost/cache/schema direction

There is no warm/cold cache distinction and no route-specific cache.

Logical required work is bounded to one Object row plus one lifecycle event. Exact successful PostgreSQL statement count remains an architecture optimization target after the exact-lifecycle requirement is satisfied.

No route-specific table, denormalization, materialization or index is introduced.

## Revalidation status

Public contract, same-name assignment semantics, semantic responsibility boundary and exact lifecycle requirement are ratified during the current full-sweep pass.

The remaining route-local sweep work is limited to confirming final failure/concurrency closure and then absorbing this direction into the consolidated Object route owner before marking `PUT /objects/{id}/canonical-name` full-sweep complete.
