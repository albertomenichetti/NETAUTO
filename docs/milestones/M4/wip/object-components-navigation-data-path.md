# M4 WIP — Object component-slot navigation data path

Status: ROUTE-LOCAL DATA PATH RATIFIED / CURSOR INTEGRATED / M4 WIP / ALWAYS NON-NORMATIVE

## Scope

This note records the ratified route-local logical data path for:

```http
GET /api/v1/core/objects/{parent_object_id}/components/{slot_name}
    ?cursor=...
    &limit=...
```

The public contract is owned by:

```text
object-components-navigation-public-contract.md
```

The cursor identity/encoding/failure contract is owned by:

```text
object-components-navigation-cursor.md
```

Cross-operation current component persistence is owned by:

```text
object-components-persistence.md
```

This route-local block fixes the one-statement logical path, bounded cost target and same-statement current semantic-slot cursor validation. Exact SQL/SQLAlchemy realization, final indexes and `EXPLAIN` evidence remain architecture work.

## Required outcomes

The route must distinguish in one normal execution path:

```text
parent absent
    -> 404 resource_not_found / object

parent exists + requested current slot absent
    -> 404 resource_not_found / object_component_slot

parent exists + current slot present
+ cursor semantic slot differs from current slot
    -> 400 invalid_cursor

parent exists + slot exists + zero current children
    -> 200 {items: [], next_cursor: null}

parent exists + slot exists + current children
    -> 200 bounded page
```

No database query may exist solely to improve diagnostics or validate the current slot identity carried by the cursor.

Static request/cursor incompatibility is rejected before this database statement and is owned by the public/cursor blocks.

## Data-plane sources

The normal route reads only current runtime structures:

```text
objects parent
object_component_slots requested current slot
object_components current membership
objects child for canonical_name
```

It does not need on the normal path:

```text
parent template_id/template_version for schema interpretation
object_template_effective_components
ObjectTemplate inheritance traversal
component-schema worker cache
DataType knowledge
stable ancestry knowledge
objects.revision
explicit locks
```

The current slot materialization already answers whether the requested slot exists, exposes its semantic identity, and supplies the current fact required to validate a cursor's internal `slot_declaring_template_id`.

The hot read trusts the ratified cross-operation invariant:

```text
MaterializedSlots(O)
    == EffectiveComponentSlots(O.template_id, O.template_version)
```

It does not re-certify that invariant against model-plane schema.

## Cursor inputs to the statement

After static cursor decoding/validation, the statement receives at most:

```text
cursor_slot_declaring_template_id: UUID | null
cursor_child_id: UUID | null
```

Both are null on the first page.

The application has already validated that the cursor's route identity, `parent_object_id`, `slot_name`, carrier types and key shape are compatible with the request.

PostgreSQL remains authoritative for whether the current nested slot still has the semantic identity carried by the cursor.

## One-statement logical shape

Conceptually:

```text
parent PK lookup
    -> preserve parent root even when requested slot is absent

LEFT JOIN requested object_component_slots row by
    (object_id, slot_name)

LEFT/LATERAL or equivalent bounded object_components page by
    parent_object_id
    slot_declaring_template_id
    slot_name
    child_object_id cursor/order

membership branch gated by
    first page
    OR current slot_declaring_template_id = cursor slot_declaring_template_id

JOIN child objects
    -> current canonical_name
```

The exact SQL/SQLAlchemy representation is not frozen. PostgreSQL may realize the same logical access path differently.

The required properties are:

```text
parent root survives slot absence
current slot survives empty membership
current slot survives cursor semantic mismatch
stale/replaced-slot cursor need not scan a page that will be rejected
paged child branch remains bounded to one resolved current semantic slot
```

The route must not decompose this into independent preliminary parent, slot and page round trips merely for convenience; one statement snapshot is the route's coherence boundary.

## Result classification and precedence

Classification uses only the one statement result plus the already-decoded cursor inputs.

### Parent absent

```text
no parent root in the statement snapshot
    -> 404 resource_not_found / object
```

This has precedence over slot/cursor classification because the path parent itself does not exist.

### Slot absent

```text
parent exists
requested current slot row absent
    -> 404 resource_not_found / object_component_slot
```

This has precedence over cursor semantic comparison because the nested resource does not exist in the statement snapshot.

### Slot present but cursor semantic identity stale

If a continuation cursor was supplied and:

```text
current slot_declaring_template_id
    != cursor_slot_declaring_template_id
```

then:

```text
-> 400 invalid_cursor
```

The same public `(parent_object_id, slot_name)` path now denotes a different current semantic slot than the collection against which the keyset position was issued.

The bounded page branch should be gated off where practical; no child page is required to classify this result.

### Slot present, compatible cursor, empty page

```text
slot exists
semantic cursor identity matches if supplied
zero currently visible children after keyset position
    -> 200 empty page
```

This covers both a truly empty slot and continuation beyond the last currently visible child.

### Slot present with children

Each page item is:

```json
{
  "id": "<child_object_id>",
  "canonical_name": "<current child name>"
}
```

The statement returns at most `limit + 1` children. The application returns the first `limit` and uses the extra row only to determine continuation.

If another page exists, the next cursor is built from values already available in request/result context:

```text
parent_object_id
slot_name
current slot_declaring_template_id
last returned child_object_id
```

No additional read is allowed solely for cursor generation.

## Ordering and keyset boundary

Canonical ordering is:

```text
child_object_id ASC
```

The membership page is logically restricted by:

```text
parent_object_id
slot_declaring_template_id
slot_name
child_object_id > cursor_child_id when cursor present
ORDER BY child_object_id ASC
LIMIT limit + 1
```

The route therefore does not scan children belonging to other slots merely to construct the requested page.

## Read coherence and concurrency

All mutable response and current cursor-compatibility facts are observed by one PostgreSQL statement:

```text
parent existence
current slot existence/semantic identity
current membership
current child canonical names
```

No multi-statement coherent-read protocol, row lock or `objects.revision` check is required.

Concurrent operations are observed according to ordinary statement visibility:

```text
SCHEMA_CHANGE semantic replacement
    statement before commit
        -> old slot identity
        -> old compatible cursor may continue

    statement after commit
        -> new slot identity
        -> old cursor invalid_cursor

SCHEMA_CHANGE slot removal
    statement after commit
        -> 404 object_component_slot

SCHEMA_CHANGE preserving semantic slot / target widening
    -> same semantic slot identity
    -> cursor remains compatible

ATTACH
    -> child absent before commit / present after commit

DETACH
    -> child present before commit / absent after commit

child RENAME
    -> old or new canonical_name from the same statement snapshot

parent DELETE
    -> existing parent snapshot or 404 according to visibility
```

The cursor remains a continuation token rather than a cross-request membership snapshot; later pages may reflect committed membership/display changes.

## Referential-integrity trust boundary

The normal read path trusts already-admitted relational invariants:

```text
current ownership edge -> live child Object
current ownership edge -> current semantic parent slot
```

The route does not add:

```text
diagnostic child-existence query
model-plane recertification
ownership integrity sweep
second query to explain impossible corruption
```

An impossible required dependency inconsistency encountered incidentally on the required path is an internal invariant failure; this classification does not authorize diagnostic-only database work.

## Cost target

Static malformed request/cursor failures:

```text
0 PostgreSQL statements
```

Every database-backed normal classification path has a maximum target of:

```text
1 PostgreSQL business statement
```

including:

```text
first page
continuation page
empty current slot
absent current slot
stale semantic cursor
parent absence
```

Normal runtime profile:

```text
PostgreSQL statements     1
cache lookups             0
model-plane reads         0
recursive traversal       0
revision reads            0
explicit locks            0
server-side cursor state  0
diagnostic follow-up      0
```

Cursor generation adds:

```text
0 PostgreSQL statements
0 cache/model reads
small canonical serialization only
```

Logical work scales with:

```text
O(1) parent lookup
+ O(1) requested-slot lookup / semantic-id comparison
+ O(page size) ownership/child rows
```

and does not scale with:

```text
total slots on the parent
total children in other slots
ObjectTemplate inheritance depth
Object property count
Relationship count
lifecycle-event count
```

subject to final physical-plan verification.

## Architecture handoff

Architecture must prove bounded access for:

```text
objects PK(parent_object_id)

object_component_slots current lookup by
    (object_id, slot_name)

object_components keyset page restricted to the resolved semantic slot
    parent_object_id
    slot_declaring_template_id
    slot_name
    child_object_id

objects child lookup by child_object_id
```

Deferred physical choices include:

```text
exact SQL / SQLAlchemy carrier
LEFT/LATERAL vs equivalent root-preserving realization
final PK/UNIQUE/index key ordering
INCLUDE vs key columns
final object_components supporting index set
EXPLAIN (ANALYZE, BUFFERS) / equivalent evidence
payload/runtime measurements
```

The final plan must confirm that current semantic-id cursor gating does not defeat bounded keyset access.

No route-local physical index is frozen during discovery.

## Superseded alternative

Before per-Object slot materialization, one-statement navigation could have joined:

```text
objects
-> object_template_effective_components
-> object_components
-> child objects
```

That remains technically possible but is not the reviewed baseline because it recomposes model/runtime state already materialized cross-operation for frequent Object reads/ATTACH.

## Ratified discovery takeaway

```text
GET /objects/{parent}/components/{slot}

one authoritative PostgreSQL statement
parent PK
current materialized slot lookup
same-snapshot cursor semantic-id comparison
bounded limit+1 membership page + current child names

0 component-schema cache
0 exact ObjectTemplate read
0 ancestry read
0 revision
0 explicit locks
0 diagnostic follow-up

static malformed/incompatible cursor
    -> 400 invalid_cursor before DB

parent absent
    -> 404 object
slot absent
    -> 404 object_component_slot
slot present + semantic cursor identity differs
    -> 400 invalid_cursor
slot valid compatible + empty
    -> 200 []
slot valid compatible + populated
    -> 200 page

current slot/model invariant
    -> trusted admitted state on the hot read path

remaining architecture-only work
    -> exact carrier/indexes/EXPLAIN/measurements
```
