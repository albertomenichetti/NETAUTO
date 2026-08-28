# M4 WIP — Object components physical index candidate

Status: FROZEN DISCOVERY INPUT / M4 WIP / ALWAYS NON-NORMATIVE

## Scope

This note records the current physical-index candidate for the M4 Object component-slot runtime structures:

```text
object_component_slots
object_components
```

It closes the route/workload-level index-design question that was left REOPENED in:

```text
object-components-physical-schema-discovery.md
```

and supersedes only that document's `Index direction — REOPENED` subsection.

It does **not** freeze the complete relational schema, authorize implementation, or replace the later required PostgreSQL `EXPLAIN`/measurement evidence.

The candidate is derived from the complete currently identified Object/ownership workload, not from the component-navigation route in isolation.

## Inputs already established

Current slot materialization candidate:

```text
object_component_slots
    object_id                    NOT NULL
    slot_declaring_template_id   NOT NULL
    slot_name                    NOT NULL
    target_template_id           NOT NULL
```

Current ownership-edge candidate:

```text
object_components
    child_object_id              NOT NULL
    parent_object_id             NOT NULL
    slot_declaring_template_id   NOT NULL
    slot_name                    NOT NULL
```

Current edge-to-slot FK candidate:

```text
(parent_object_id, slot_declaring_template_id, slot_name)
    ->
(object_id, slot_declaring_template_id, slot_name)
```

Current navigation ordering:

```text
child_object_id ASC
```

Current navigation keyset continuation:

```text
child_object_id > :cursor_child_id
```

after the exact current semantic slot has been resolved.

## Workload requirements

The physical design must support at least the following without route-local duplicate indexes.

### `object_component_slots`

```text
GET component slot
ATTACH
    -> lookup one current slot by (object_id, slot_name)

GET Object
    -> enumerate all current slots for one object_id

edge FK
SCHEMA_CHANGE REMOVE / semantic replacement
Object DELETE slot cascade arbitration
    -> exact semantic referenced key
       (object_id, slot_declaring_template_id, slot_name)
```

### `object_components`

```text
GET component slot
    -> exact parent + semantic slot
    -> child_object_id keyset range/order

GET Object
    -> all outgoing edges for one parent
    -> deterministic child ordering inside semantic slots

edge FK reverse lookup
    -> rows referencing one current semantic slot

GET owner
ATTACH ownerlessness checks
DETACH requested-child work
ownership root traversal
    -> child_object_id lookup
```

The last group is already naturally served by the single-owner `child_object_id` primary key and does not justify a second parent/slot-oriented index.

## Candidate key set

### 1. `object_component_slots` semantic primary key

Preferred candidate:

```text
PRIMARY KEY (
    object_id,
    slot_declaring_template_id,
    slot_name
)
```

Rationale:

- this is the persisted current semantic slot identity under one Object;
- it is the exact referenced key used by `object_components`;
- semantic replacement changes this key rather than silently reinterpreting attached membership;
- the leading `object_id` also supports range access to all slots owned by one Object.

This resolves the earlier OPEN choice between PRIMARY KEY and UNIQUE in favor of making the semantic key the declared primary key.

### 2. `object_component_slots` public/current-name alternate key

Retain:

```text
UNIQUE (
    object_id,
    slot_name
)
```

Rationale:

- one Object exposes at most one current effective member under a given slot name;
- public component navigation and ATTACH identify the current slot through `(object_id, slot_name)`;
- the lookup returns `slot_declaring_template_id` and `target_template_id` from the one matched row;
- this alternate key is also useful as an Object-prefix range path.

The semantic three-column PK does not replace this alternate key because a lookup that knows only `(object_id, slot_name)` does not constrain the middle `slot_declaring_template_id` column.

### 3. `object_components` single-owner primary key

Retain:

```text
PRIMARY KEY (child_object_id)
```

Rationale:

- a child Object has at most one current owner;
- GET owner is direct by child;
- ATTACH ownerlessness/admission and upward ownership traversal are child-rooted;
- batch DETACH starts from requested child ids and can use the same key before applying exact-edge predicates.

No change is justified here by component-slot materialization.

### 4. `object_components` semantic parent-page / FK-support index

Preferred single secondary index:

```text
INDEX (
    parent_object_id,
    slot_declaring_template_id,
    slot_name,
    child_object_id
)
```

This replaces the AS-IS direction:

```text
(parent_object_id, slot_name, child_object_id)
```

rather than adding another index beside it.

## Why this edge column order

### `parent_object_id` first

The high-cardinality forward ownership reads are parent-rooted:

```text
GET Object
GET one component slot
```

The parent prefix also supports current-reference work over all outgoing edges of one Object where required.

### Semantic slot key next

The route resolves the current `object_component_slots` row before paging membership, so the edge page has equality values for:

```text
parent_object_id
slot_declaring_template_id
slot_name
```

Putting the exact referencing-side FK tuple at the left of the index allows the same physical structure to support:

```text
one semantic-slot membership range
+
referencing-row lookup when a slot row is deleted or its semantic key changes
```

PostgreSQL does not automatically create an index on FK referencing columns. The candidate therefore intentionally makes the hot read index double as the FK-support index instead of paying for a separate structure.

### `child_object_id` last

After equality on the first three columns, the remaining key is exactly the route ordering/keyset dimension:

```text
ORDER BY child_object_id ASC
child_object_id > :cursor_child_id
LIMIT :limit_plus_one
```

The candidate should therefore permit a bounded ordered B-tree range rather than collecting/sorting all children in the slot.

## Why not `(parent_object_id, slot_name, child_object_id)`

That AS-IS index matches the old public route shape but omits the semantic slot identity now persisted on the edge.

Keeping it as the only parent index would mean the physical access path does not directly match the new FK/reference identity and may require another FK-support index.

Keeping it **in addition** to the semantic index would duplicate nearly the same write workload on every ATTACH/DETACH.

The new navigation route does not need an edge access path with only `(parent_object_id, slot_name)` because it first resolves the unique current slot row and therefore knows `slot_declaring_template_id` before entering the bounded edge page.

## Why not `(parent_object_id, slot_name, slot_declaring_template_id, child_object_id)`

This order could also satisfy the fully constrained navigation query.

The current preference is the FK-semantic order:

```text
parent_object_id,
slot_declaring_template_id,
slot_name,
child_object_id
```

because:

- it mirrors the referencing FK tuple exactly;
- no identified hot path requires an edge prefix of only `(parent_object_id, slot_name)`;
- parent-only scans remain available in either order;
- child ordering remains available after equality on the full semantic slot tuple.

If later `EXPLAIN` evidence demonstrates a material planner/runtime advantage for the alternative order under the final SQL shapes, this local ordering decision must be reopened rather than defended abstractly.

## Why no second edge secondary index

Current identified operations do not justify one.

```text
GET owner
ATTACH ownerlessness
DETACH by requested child ids
root(parent) recursive traversal
```

are child-rooted and use:

```text
PRIMARY KEY (child_object_id)
```

while:

```text
GET Object
GET component slot
slot FK reverse checks
```

are covered by the semantic parent index.

The candidate therefore keeps the edge table at:

```text
1 primary-key index
1 secondary B-tree index
```

which is the same **index-count shape** as AS-IS, although the secondary key is wider by the added UUID semantic-identity column.

## Why no `INCLUDE` columns now

No INCLUDE payload is currently justified.

### Slot lookup

`(object_id, slot_name)` identifies exactly one slot row. Fetching:

```text
slot_declaring_template_id
target_template_id
```

from that row is bounded O(1) work. Duplicating them into the alternate-key index solely to chase an index-only scan would enlarge every slot index entry and increase CREATE/SCHEMA_CHANGE maintenance without evidence of a meaningful hot-path gain.

### Edge page

The edge index already contains every persisted edge field needed to identify membership:

```text
parent_object_id
slot_declaring_template_id
slot_name
child_object_id
```

Child `canonical_name` belongs to the mutable `objects` row and must still be read from that authority. It must not be copied into the edge index/materialization merely to make this route covering.

`INCLUDE` may be reopened only from measured evidence against final queries and realistic cardinalities.

## Why no `target_template_id` index

Current consumers retrieve `target_template_id` **after** identifying one slot by `(object_id, slot_name)`.

No current hot path searches or groups slot rows by target lineage.

Therefore a standalone or leading-key target index would add write/storage cost without an identified runtime consumer.

## Surrogate `slot_id` alternative — rejected for current candidate

A surrogate slot-row id could narrow the edge FK, for example:

```text
object_component_slots.slot_id PK
object_components.slot_id FK
```

but it weakens the direct relational expression of the semantic invariant.

To preserve current behavior, semantic replacement would then need an additional rule ensuring an attached edge cannot keep referencing the same surrogate row while that row's declaring-lineage identity changes. It would also force additional slot joins on edge-centered operations that currently obtain semantic identity directly from the factual edge.

The current candidate therefore prefers the explicit composite semantic FK despite the wider edge/index key.

This may be reopened only if measured storage/write amplification proves material enough to justify the extra indirection and a separately proven replacement invariant.

## Write-cost interpretation

### `object_components`

Relative to AS-IS:

```text
index count
    unchanged:
        child PK
        + one parent-oriented secondary index

secondary index width
    increases by slot_declaring_template_id UUID
```

ATTACH/DETACH therefore pay no extra **number** of edge secondary indexes from this design; they pay the wider semantic key already justified by the ownership invariant.

Exact byte/write-amplification cost remains a measurement item.

### `object_component_slots`

Each materialized slot row participates in:

```text
semantic PK
public/current-name UNIQUE
```

This is additional storage/write work introduced by the per-Object slot materialization.

That cost is intentionally paid on Object CREATE and rare SCHEMA_CHANGE so frequent GET/ATTACH paths avoid repeated model-plane work.

No third slot index is currently justified.

## Expected navigation access path

For:

```http
GET /objects/{parent_object_id}/components/{slot_name}
```

expected logical access is:

```text
1. objects PK
   -> parent existence

2. object_component_slots UNIQUE(object_id, slot_name)
   -> current slot existence
   -> slot_declaring_template_id

3. object_components semantic parent-page index
   equality:
       parent_object_id
       slot_declaring_template_id
       slot_name
   optional range:
       child_object_id > cursor_child_id
   order:
       child_object_id ASC
   bound:
       limit + 1

4. objects child PK
   -> current canonical_name for only the bounded page rows
```

For an absent slot, empty slot, or stale semantic cursor, the edge branch should not require scanning unrelated parent membership.

## Expected cross-operation access coverage

### GET Object

The edge secondary index has `parent_object_id` as the leading key and therefore provides one parent-rooted range over current direct children.

The slot table's two uniqueness indexes both begin with `object_id`, so no third `object_component_slots(object_id)` index is required merely to enumerate all current slots of one Object.

Final one-statement Object GET SQL may choose flat joins or another equivalent shape; exact sort/plan details remain to be measured there.

### ATTACH

Current slot lookup:

```text
object_component_slots UNIQUE(object_id, slot_name)
```

Current child-owner check:

```text
object_components PK(child_object_id)
```

Final edge INSERT maintains:

```text
child PK
semantic parent-page secondary index
edge -> semantic slot FK
```

No component-navigation-only extra index is introduced.

### DETACH

Requested child ids are the selective operands and use the child PK. Exact parent/slot predicates certify that each found row is the requested edge.

No separate `(parent_object_id, slot_name, ...)` index is justified by DETACH.

### Ownership root traversal

The recursive upward traversal follows:

```text
child_object_id -> parent_object_id
```

and uses the edge child PK at each step.

### Slot REMOVE / semantic replacement / Object DELETE cascade

The edge semantic parent index begins with the complete FK referencing tuple and is the intended reverse-reference probe for current edges that would block slot deletion/key change.

This is important because PostgreSQL FK declarations do not automatically create a referencing-side index.

## Required PostgreSQL evidence before architecture freeze

The index candidate is design-closed, but physical evidence remains OPEN.

Evidence must use final TO-BE DDL/query shapes and representative cardinalities; tiny fixture tables where PostgreSQL rationally chooses sequential scans are not sufficient to reject the design.

At minimum record `EXPLAIN (ANALYZE, BUFFERS)` or the project-approved equivalent for:

### Navigation — populated first page

Prove that work is bounded to one exact semantic slot and approximately the requested page size.

Expected properties:

```text
no scan of unrelated parent slots
no sort over all children in the slot
bounded child-object PK joins
```

### Navigation — continuation page

Prove that:

```text
child_object_id > cursor_child_id
```

becomes an index range boundary after equality on the semantic slot tuple.

### Navigation — empty slot

Prove that current slot existence is distinguished without scanning all ownership edges.

### Navigation — absent slot

Prove that `(object_id, slot_name)` lookup fails directly and the edge branch performs no material membership scan.

### Navigation — stale semantic cursor

Prove that current slot identity mismatch gates the edge page and avoids scanning a page that will be rejected.

### GET Object representative fan-out

Prove parent-rooted edge access and slot enumeration remain bounded by that Object's current fan-out rather than global edge/slot cardinality.

### FK reverse-reference cases

Exercise slot DELETE / semantic-key UPDATE with both:

```text
zero referencing edges
non-zero referencing edges
```

and verify that reverse-reference work uses the intended referencing-side index at representative scale.

### Write/storage measurement

Measure at least:

```text
edge secondary-index size delta versus AS-IS key
slot-table PK + alternate-key index size
ATTACH/DETACH write cost at representative batch sizes
CREATE/SCHEMA_CHANGE slot-index maintenance cost
```

The candidate must be reopened if measured costs materially invalidate the current workload trade-off.

## Planner-node caution

The evidence requirement is about bounded work and workload behavior, not forcing a particular node name.

PostgreSQL may legitimately choose:

```text
Index Scan
Index Only Scan
Bitmap paths
Nested Loop
Seq Scan on genuinely tiny relations
```

according to statistics and cardinality.

The architecture invariant is that the available index set permits bounded/selective execution for the production-shaped workload; it is not that every test fixture must display a specific `EXPLAIN` spelling.

## Frozen discovery takeaway

```text
object_component_slots
    PRIMARY KEY (
        object_id,
        slot_declaring_template_id,
        slot_name
    )

    UNIQUE (
        object_id,
        slot_name
    )

object_components
    PRIMARY KEY (child_object_id)

    INDEX (
        parent_object_id,
        slot_declaring_template_id,
        slot_name,
        child_object_id
    )

no retained AS-IS parent+slot+child duplicate index
no third slot index
no INCLUDE candidate
no target_template_id index

navigation
    -> exact slot lookup
    -> semantic B-tree keyset range
    -> child PK joins for bounded page

edge index also supports
    -> parent-rooted GET Object
    -> referencing-side semantic FK lookup

child PK continues to support
    -> owner lookup
    -> ATTACH ownerlessness
    -> DETACH requested-child work
    -> upward root traversal

remaining evidence gate
    -> final DDL/query EXPLAIN + storage/write measurements
```
