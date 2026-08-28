# M4 WIP — Object component-slot navigation data path

Status: FROZEN DISCOVERY INPUT / M4 WIP / ALWAYS NON-NORMATIVE

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

The persistence candidate used here is owned by:

```text
object-component-slots-data-plane-materialization.md
object-components-physical-schema-discovery.md
```

This note closes only the current discovery candidate for the normal data path and statement-count target. Cursor token encoding and final physical indexes remain separate open points.

## Required outcomes

The route must distinguish in one normal execution path:

```text
parent absent
    -> 404 resource_not_found / object

parent exists + requested current slot absent
    -> 404 resource_not_found / object_component_slot

parent exists + slot exists + zero current children
    -> 200 {items: [], next_cursor: null}

parent exists + slot exists + current children
    -> 200 bounded page
```

No database query may exist solely to improve diagnostics.

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

The current slot materialization already answers whether the requested slot exists and exposes its semantic identity.

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
      AND oc.parent_object_id = s.object_id
      AND oc.slot_declaring_template_id = s.slot_declaring_template_id
      AND oc.slot_name = s.slot_name
      AND (:cursor_child_id IS NULL OR oc.child_object_id > :cursor_child_id)
    ORDER BY oc.child_object_id ASC
    LIMIT :limit_plus_one
) AS page ON TRUE;
```

The exact SQL/SQLAlchemy representation is not frozen. PostgreSQL may realize the same logical access path differently.

The important property is that the parent row survives both:

```text
slot absent
slot present but empty
```

while the paged child branch is bounded and executes only against one resolved current slot.

## Result classification

### Parent absent

The parent CTE/root lookup returns no row:

```text
0 result rows
    -> 404 resource_not_found / object
```

### Slot absent

The parent row exists but the slot LEFT JOIN is null:

```text
parent_id != null
slot_name == null
    -> 404 resource_not_found / object_component_slot
```

### Slot present but empty

The slot row exists but the LATERAL page yields no child:

```text
slot_name != null
child_object_id == null
    -> 200 empty page
```

### Slot present with children

One result row per page child is projected to:

```json
{
  "id": "<child_object_id>",
  "canonical_name": "<current child name>"
}
```

The application consumes at most `limit + 1` children to determine whether another page exists.

## Ordering direction

Current candidate reuses the Object GET deterministic child ordering:

```text
child_object_id ASC
```

This gives a stable keyset direction and matches the existing useful ownership index shape.

The ordering key is a route-local candidate. The opaque cursor encoding, query-identity binding and malformed/stale-cursor semantics remain to be closed separately.

## Read coherence

All mutable response facts are observed by one PostgreSQL statement:

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

No row lock is required by this read candidate.

## Cost target

Normal route cost:

```text
1 PostgreSQL statement
0 cache lookups
0 model-plane reads
0 recursive traversal
0 explicit locks
```

Work scales approximately with:

```text
O(1) parent lookup
+ O(1) requested-slot lookup
+ O(page size) ownership/child rows
```

subject to final physical-plan/index verification.

Empty/absent slot cases do not scan all slots or all children of the parent.

## Persistence/index handoff

Final physical review must prove bounded access for:

```text
objects PK(parent_object_id)

object_component_slots UNIQUE(object_id, slot_name)

object_components page access beginning with
    parent_object_id
    slot_name
    child_object_id

semantic-key column availability for FK-consistent filtering

child objects PK(child_object_id)
```

Whether the final edge index key includes `slot_declaring_template_id`, uses INCLUDE, or relies on another supporting index remains global physical design.

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
    bounded membership page + child names

no component-schema cache
no exact ObjectTemplate read
no multi-statement coherent-read transaction

parent absent
    -> 404 object
slot absent
    -> 404 object_component_slot
slot valid empty
    -> 200 []
slot valid populated
    -> 200 page

next open micro-point:
    cursor identity / opaque encoding / pagination semantics
```
