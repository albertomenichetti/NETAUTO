# M4 WIP — Object component-slot navigation data path

Status: FROZEN DISCOVERY INPUT / CURSOR CHECKPOINT INTEGRATED / M4 WIP / ALWAYS NON-NORMATIVE

## Scope

This note records the current route-local data-path candidate for:

```http
GET /api/v1/core/objects/{parent_object_id}/components/{slot_name}
    ?cursor=...
    &limit=...
```

The public contract is owned by:

```text
object-components-navigation-public-contract.md
```

The cursor identity/encoding/failure candidate is owned by:

```text
object-components-navigation-cursor.md
```

The persistence candidate used here is owned by:

```text
object-component-slots-data-plane-materialization.md
object-components-physical-schema-discovery.md
```

This note closes the current discovery candidate for the normal data path, statement-count target, and same-statement current semantic-slot cursor validation. Final physical indexes / EXPLAIN evidence remain separate open points.

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

Static cursor-envelope/path/key incompatibility is rejected before this database statement and is owned by `object-components-navigation-cursor.md`.

## Data-plane sources

Current candidate reads only mutable/current runtime structures:

```text
objects parent
object_component_slots requested current slot
object_components current membership
objects child for canonical_name
```

It does not need on the normal path:

```text
parent template_id/template_version lookup for schema interpretation
object_template_effective_components
ObjectTemplate inheritance traversal
component-schema worker cache
DataType knowledge
stable ancestry knowledge
locks
```

The current slot materialization already answers whether the requested slot exists, exposes its semantic identity, and provides the current fact required to validate a cursor's internal `slot_declaring_template_id`.

## Cursor inputs to the statement

After static cursor decoding/validation, the statement receives at most:

```text
cursor_slot_declaring_template_id: UUID | null
cursor_child_id: UUID | null
```

Both are null on the first page.

The application has already validated that the cursor's codec route, `parent_object_id`, `slot_name`, carrier types and key shape are compatible with the request.

The database remains authoritative for whether the current nested slot still has the semantic identity carried by the cursor.

## One-statement shape

Conceptually:

```text
parent PK lookup
    -> preserve parent row even when requested slot is absent

LEFT JOIN requested object_component_slots row by
    (object_id, slot_name)

LEFT/LATERAL paged object_components lookup by
    parent_object_id
    slot_declaring_template_id
    slot_name
    child_object_id cursor/order

LATERAL membership branch gated by
    first page
    OR current slot_declaring_template_id = cursor slot_declaring_template_id

JOIN child objects
    -> canonical_name
```

A representative non-normative SQL shape is:

```sql
WITH parent AS (
    SELECT id
    FROM objects
    WHERE id = :parent_object_id
)
SELECT
    p.id AS parent_id,
    s.slot_declaring_template_id,
    s.slot_name,
    page.child_object_id,
    page.child_canonical_name
FROM parent p
LEFT JOIN object_component_slots s
  ON s.object_id = p.id
 AND s.slot_name = :slot_name
LEFT JOIN LATERAL (
    SELECT
        oc.child_object_id,
        child.canonical_name AS child_canonical_name
    FROM object_components oc
    JOIN objects child
      ON child.id = oc.child_object_id
    WHERE s.slot_name IS NOT NULL
      AND (
          :cursor_slot_declaring_template_id IS NULL
          OR s.slot_declaring_template_id = :cursor_slot_declaring_template_id
      )
      AND oc.parent_object_id = s.object_id
      AND oc.slot_declaring_template_id = s.slot_declaring_template_id
      AND oc.slot_name = s.slot_name
      AND (:cursor_child_id IS NULL OR oc.child_object_id > :cursor_child_id)
    ORDER BY oc.child_object_id ASC
    LIMIT :limit_plus_one
) AS page ON TRUE;
```

The exact SQL/SQLAlchemy representation is not frozen. PostgreSQL may realize the same logical access path differently.

The important properties are:

```text
parent row survives slot absence
current slot row survives empty membership
current slot row survives cursor semantic mismatch
stale/replaced-slot cursor does not need to scan a page that will be rejected
paged child branch remains bounded to one resolved current slot
```

## Result classification and precedence

Classification uses only the one statement result plus the already-decoded cursor inputs.

### Parent absent

The parent CTE/root lookup returns no row:

```text
0 result rows
    -> 404 resource_not_found / object
```

This has precedence over current-slot semantic comparison because no current parent resource exists in the statement snapshot.

### Slot absent

The parent row exists but the slot LEFT JOIN is null:

```text
parent_id != null
slot_name == null
    -> 404 resource_not_found / object_component_slot
```

This has precedence over cursor semantic comparison because the nested resource does not exist in the statement snapshot.

### Slot present but cursor semantic identity stale

The slot row exists and a continuation cursor was supplied, but:

```text
slot_declaring_template_id
    != cursor_slot_declaring_template_id
```

then:

```text
-> 400 invalid_cursor
```

The same public `(parent_object_id, slot_name)` path now denotes a different current semantic slot than the one against which the keyset position was issued.

The LATERAL branch is gated off for this case; no child page is required to classify the failure.

### Slot present, compatible cursor, empty page

The slot row exists, semantic identity is compatible, but the LATERAL page yields no child:

```text
slot_name != null
child_object_id == null
    -> 200 empty page
```

This covers both a truly empty slot and a continuation position after the final currently visible child.

### Slot present with children

One result row per page child is projected to:

```json
{
  "id": "<child_object_id>",
  "canonical_name": "<current child name>"
}
```

The application consumes at most `limit + 1` children to determine whether another page exists.

If another page exists, the cursor is generated from values already available in the request/result context:

```text
parent_object_id
slot_name
current slot_declaring_template_id
last returned child_object_id
```

No additional read is required.

## Ordering direction

Current candidate reuses the Object GET deterministic child ordering:

```text
child_object_id ASC
```

This gives a stable keyset direction and matches the existing useful ownership index shape.

The complete route-local cursor candidate is now:

```text
semantic identity
    parent_object_id
    slot_name
    slot_declaring_template_id

position
    child_object_id ASC

limit
    not identity
```

Opaque encoding and static invalid-cursor rules are recorded in `object-components-navigation-cursor.md`.

## Read coherence

All mutable response and current cursor-compatibility facts are observed by one PostgreSQL statement:

```text
parent existence
current slot existence/semantic identity
current membership
current child canonical names
```

Therefore the route does not require the multi-statement coherent-read protocol previously needed by the cache-based Object GET candidate.

Concurrent:

```text
SCHEMA_CHANGE
ATTACH
DETACH
child RENAME
```

is observed according to one statement snapshot rather than by combining independently timed reads.

For a cursor request, a concurrent semantic replacement is therefore observed coherently as either:

```text
BEFORE replacement
    -> old slot identity visible
    -> cursor can continue against that statement snapshot

AFTER replacement
    -> new slot identity visible
    -> cursor rejected as invalid_cursor
```

A concurrent slot removal committed before the statement snapshot is `404 object_component_slot`.

No row lock is required by this read candidate.

## Cost target

Normal route cost remains:

```text
1 PostgreSQL statement
0 cache lookups
0 model-plane reads
0 recursive traversal
0 explicit locks
```

Cursor support adds:

```text
0 PostgreSQL statements
0 cache lookups
0 model-plane reads
0 recursive traversal
0 explicit locks
0 server-side cursor storage
```

The continuation statement adds only bounded predicates over already-required current data:

```text
current slot semantic-id equality
child_object_id keyset comparison
```

Cursor generation performs only small application JSON/Base64 serialization over values already available from the page.

Work scales approximately with:

```text
O(1) parent lookup
+ O(1) requested-slot lookup / semantic-id comparison
+ O(page size) ownership/child rows
```

subject to final physical-plan/index verification.

Empty/absent/stale-slot cases do not scan all slots or all children of the parent.

## Persistence/index handoff

Final physical review must prove bounded access for:

```text
objects PK(parent_object_id)

object_component_slots UNIQUE(object_id, slot_name)

object_components page access beginning with
    parent_object_id
    slot_name
    child_object_id

semantic-key column availability for FK-consistent filtering and cursor identity comparison

child objects PK(child_object_id)
```

Whether the final edge index key includes `slot_declaring_template_id`, uses INCLUDE, or relies on another supporting index remains global physical design.

The final plan review must also confirm that the semantic-id LATERAL gate does not defeat bounded index/keyset access.

## Superseded alternative

Before per-Object slot materialization, one-statement navigation could have joined:

```text
objects
-> object_template_effective_components
-> object_components
-> child objects
```

That alternative remains technically possible but is no longer the preferred current candidate because it leaves ATTACH and GET Object dependent on repeated model/runtime composition that the stronger data-plane materialization removes cross-operation.

The materialization is therefore chosen for system-level workload benefit, not because this route alone could not be implemented with one statement otherwise.

## Current discovery takeaway

```text
GET /objects/{parent}/components/{slot}

current candidate:
    one PostgreSQL statement
    parent PK
    current materialized slot lookup
    same-snapshot cursor semantic-id comparison
    bounded membership page + child names

no component-schema cache
no exact ObjectTemplate read
no multi-statement coherent-read transaction

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

cursor runtime delta
    -> +0 PostgreSQL statements
    -> +0 model-plane reads
    -> +0 cache lookups

remaining open micro-point:
    final physical indexes / EXPLAIN evidence
```
