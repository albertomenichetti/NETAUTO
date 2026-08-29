# M4 WIP — Object component-slot GET consolidated discovery

**Status:** FULL-SWEEP COMPLETE / REVIEWED BASELINE CANDIDATE / M4 WIP / ALWAYS NON-NORMATIVE

## Purpose

This file is the consolidated route owner for:

```http
GET /api/v1/core/objects/{parent_object_id}/components/{slot_name}
```

It absorbs the public-contract, cursor, one-statement data-path, failure, cost and architecture-handoff findings previously split across the component-navigation WIPs. `object.md` remains the Object-family owner; `object-components-persistence.md` owns the shared current slot/edge persistence semantics.

Everything under `wip/` remains globally non-normative and does not authorize implementation.

# 1. Public contract

```http
GET /api/v1/core/objects/{parent_object_id}/components/{slot_name}
    ?cursor=...
    &limit=...
```

Path:

```text
parent_object_id
    UUID

slot_name
    canonical component-slot name
    ^[a-z][a-z0-9_]{0,63}$
```

Query:

```text
cursor
    opaque string
    optional

limit
    positive integer 1..500
    optional
    default 100
```

No request body. Unknown or repeated query parameters are invalid request input. No additional child filter is part of the M4 contract.

The TO-BE surface does not retain the generic cross-slot route:

```http
GET /api/v1/core/objects/{parent_object_id}/components
```

`slot_name` is a path resource identity, not an optional filter. The route is the bounded/paginated view of one current direct-child collection already visible in the complete first-level `GET /objects/{id}` representation.

# 2. Response and nested-resource semantics

Response:

```json
{
  "items": [
    {
      "id": "<child-object-id>",
      "canonical_name": "eth0"
    }
  ],
  "next_cursor": null
}
```

The child representation is exactly the same first-level reference used by Object GET. It does not expose:

```text
slot_declaring_template_id
target_template_id
child ObjectTemplate binding
child properties
child components
```

Canonical ordering:

```text
child_object_id ASC
```

Public current-resource outcomes:

```text
parent absent
    -> 404 resource_not_found
       resource_type = object

parent present + current slot absent
    -> 404 resource_not_found
       resource_type = object_component_slot

parent present + current slot present + zero children
    -> 200 {"items": [], "next_cursor": null}

parent present + current slot present + children
    -> 200 bounded page
```

A valid empty slot is therefore distinct from a nonexistent nested slot resource.

# 3. Cursor semantics

The cursor identifies the semantic slot collection, not the complete parent Object generation and not a repeatable membership snapshot.

Canonical cursor identity:

```text
codec route
    object_component_slot_children

semantic query identity
    parent_object_id
    slot_name
    slot_declaring_template_id

position
    child_object_id ASC

limit
    excluded from semantic identity
```

`slot_declaring_template_id` is internal opaque cursor material only. It remains excluded from the public path/query/response contract.

It is required because one public path `(parent_object_id, slot_name)` can later resolve after SCHEMA_CHANGE to a different semantic slot declaration.

Consequences:

```text
same-name semantic replacement
    current slot_declaring_template_id differs
    -> 400 invalid_cursor

current slot removal
    -> 404 object_component_slot

SCHEMA_CHANGE preserving the same semantic slot identity
    -> cursor remains semantically compatible

target widening preserving semantic slot identity
    -> cursor remains compatible

ATTACH / DETACH
child RENAME
    -> do not structurally invalidate cursor
```

The cursor is not a cross-request snapshot. Membership/display changes between page requests are visible according to ordinary keyset semantics.

The position child need not remain current:

```text
cursor key = child C
C later detached or deleted
    -> continuation still uses child_object_id > C
    -> no lookup/admission of C itself
```

`limit` may change between pages.

Publicly the cursor remains only an opaque string. The current realization may reuse the existing v1 canonical-JSON/base64url envelope with a route-specific identity and no server-side cursor state; exact envelope internals are not a caller contract.

# 4. Failure precedence

Static request validation:

```text
malformed parent_object_id
malformed slot_name
malformed/out-of-range limit
unknown/repeated query parameter
request body present
    -> 400 invalid_request
```

Static cursor validation happens before database access:

```text
malformed envelope
wrong route identity
cursor parent != requested parent
cursor slot_name != requested slot
missing/malformed internal semantic id
malformed position key
    -> 400 invalid_cursor
```

Then the authoritative current-state statement classifies in this order:

```text
parent absent
    -> 404 resource_not_found / object

parent present + slot absent
    -> 404 resource_not_found / object_component_slot

slot present + continuation semantic id differs
    -> 400 invalid_cursor

otherwise
    -> 200 current page
```

Unexpected persistence/invariant failures encountered on the required path are `500 internal_error`.

There is no normal route-level:

```text
409
422
```

No diagnostic-only second query is permitted solely to enrich failure details or search for impossible corruption.

# 5. Current data path

The normal route reads only current data-plane state:

```text
objects parent
object_component_slots requested current slot
object_components current semantic-slot membership
objects child for current canonical_name
```

Required logical path:

```text
one root-preserving PostgreSQL statement

parent Object PK lookup
-> requested current slot by (object_id, slot_name)
-> compare current slot_declaring_template_id with cursor semantic id when present
-> bounded semantic-slot membership page
-> child Object id/current canonical_name
```

The membership branch uses the resolved current semantic identity:

```text
parent_object_id
slot_declaring_template_id
slot_name
child_object_id > cursor_child_id when present
ORDER BY child_object_id ASC
LIMIT limit + 1
```

For a continuation cursor, the bounded child-page branch should be gated by semantic-id equality so a stale same-name replacement cursor does not scan a page that will be rejected.

The application returns the first `limit` rows and builds `next_cursor` from the last returned child only when the `limit + 1` probe proves another row exists.

Cursor generation requires no additional database read.

# 6. Authority boundary

ObjectTemplate exact effective schema remains the semantic/model-plane authority for component-slot definitions.

`object_component_slots` is the transactionally maintained current per-Object derivative produced by Object CREATE/SCHEMA_CHANGE.

The read consumes the already-admitted current invariant:

```text
MaterializedSlots(O)
    == EffectiveComponentSlots(O.template_id, O.template_version)
```

It does not re-certify that invariant on the hot path.

Normal route work therefore requires no:

```text
parent template binding read for schema interpretation
object_template_effective_components
ObjectTemplate inheritance traversal
component semantic cache
DataType semantics
ancestry cache
objects.revision
explicit row locks
lifecycle reads/writes
```

The current persistence model is also responsible for preventing dangling membership/child facts. The GET does not add integrity sweeps or diagnostic reads to re-prove those write-owned invariants.

# 7. Coherence and concurrency

One PostgreSQL statement snapshot is the complete current-read coherence boundary.

```text
SCHEMA_CHANGE
    -> old semantic slot state OR new semantic slot state
    -> never an intermediate mixture

same-name semantic replacement
    snapshot before replacement
        -> old cursor may continue on old semantic collection
    snapshot after replacement
        -> current semantic id differs
        -> invalid_cursor

slot removal visible in snapshot
    -> 404 object_component_slot

ATTACH
    -> child absent before commit / present after commit

DETACH
    -> child present before commit / absent after commit

child RENAME
    -> old or new canonical_name according to the same statement snapshot

parent DELETE
    -> current parent result or 404 according to statement visibility
```

No revision check, retry or multi-statement coherent-read protocol is needed.

# 8. Cost profile

Static request/cursor failure:

```text
0 PostgreSQL statements
```

Every path that consults current state, including:

```text
first page
continuation page
empty valid slot
missing slot
missing parent
stale semantic cursor
```

has target cost:

```text
1 PostgreSQL business statement maximum
0 cache lookups
0 model-plane reads
0 recursive traversal
0 explicit locks
0 lifecycle work
```

Logical work:

```text
O(1) parent lookup
+ O(1) requested current-slot lookup / semantic-id comparison
+ O(page size) membership and child-name rows
```

It must not scale with:

```text
total slots on the parent
total children in other slots
Object property count
ObjectTemplate inheritance depth
Relationship count
lifecycle-event count
```

# 9. Architecture handoff

Deferred physical decisions:

```text
exact SQL / SQLAlchemy root-preserving carrier
LEFT/LATERAL vs equivalent realization
final PK/UNIQUE/index realization
edge index key order / INCLUDE choices
EXPLAIN (ANALYZE, BUFFERS) evidence
payload/runtime measurements
```

Architecture must prove the bounded path:

```text
objects PK(parent_object_id)
-> one current slot by (object_id, slot_name)
-> one keyset range for that semantic slot only
-> child Object PK/name access
```

and preserve:

```text
one statement
limit + 1 pagination
no semantic N+1
no other-slot scan
no model/cache dependency
no diagnostic follow-up query
```

No route-local physical index is frozen during discovery.

# 10. Full-sweep closure

The logical `GET /objects/{parent_object_id}/components/{slot_name}` route is **full-sweep complete** on:

```text
public route/query/response contract
removal of generic cross-slot GET surface
slot absent vs empty semantics
semantic-slot cursor identity
keyset ordering and limit semantics
SCHEMA_CHANGE cursor compatibility/replacement behavior
failure precedence
one-statement current data path
no cache/model/revision/lock/lifecycle boundary
statement-snapshot concurrency semantics
bounded cost profile
architecture physical-design handoff
```

The older navigation cursor/data-path and broad Object-components brainstorming files are source evidence only after this consolidation. Git history is the historical record once they are removed.
