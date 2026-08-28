# M4 WIP — Object ATTACH batch cost profile

Status: RECONCILED ROUTE-LOCAL COST / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note freezes the PostgreSQL statement cost for the M4 TO-BE Object ATTACH batch path.

Public operation:

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}
```

with a non-empty batch of distinct `child_object_ids`.

The count excludes `BEGIN` and `COMMIT` and counts the transaction-scoped advisory graph gate as one PostgreSQL statement.

## Warm path

Warm means the worker already has both required semantic cache inputs READY:

```text
ImmutableObjectTemplateCache[(parent.template_id, parent.template_version)]
    facet = component_schema

StableObjectTemplateAncestryCache[source_template_id]
    READY
```

The warm path is:

```text
PREPARATION

1. parent Object read
   -> id, template_id, template_version, canonical_name

CACHE
   component_schema HIT
   -> resolve slot_name
   -> slot_declaring_template_id
   -> target_template_id

2. bulk child Object read
   -> id, template_id, canonical_name
   -> verify requested ids exist
   -> collect distinct child template lineages

CACHE
   stable ancestry HIT
   -> O(1)-conceptual compatibility lookups

MUTATION UoW

3. acquire OWNERSHIP_GRAPH_WRITE_GATE

4. parent Object FOR NO KEY UPDATE
   -> require exact binding match with preparation

5. one protected graph-admission statement
   -> has_owned_requested_child
   -> recursively derive root(parent)
   -> root_is_requested
   -> the two logical outcomes distinguish ownership_conflict from ownership_cycle

6. one bulk INSERT object_components
   -> N ownership edges
   -> no ON CONFLICT

7. one bulk INSERT lifecycle ATTACH_TO
   -> N lifecycle events

COMMIT
```

Therefore:

```text
WARM ATTACH BATCH = 7 PostgreSQL statements + COMMIT
```

The Q3 result-shape refinement from one opaque `admissible` boolean to two logical flags does not add a statement or round trip.

The statement count is independent of batch cardinality:

```text
1 child      -> 7 statements
10 children  -> 7 statements
100 children -> 7 statements
```

Batch cardinality increases row work in bulk child read, edge insert and lifecycle insert, but not database round trips.

The graph traversal is one upward owner-chain traversal for the parent; its work scales with current ownership depth.

## Full-cold path

Full-cold means neither required semantic cache input is READY.

The route adds at most:

```text
+1 bounded component_schema fill for the exact parent ObjectTemplateVersion
+1 bounded bulk ancestry fill for all missing distinct child template lineages
```

After each fill, the same cache-hit execution path resumes.

Therefore:

```text
FULL-COLD ATTACH BATCH = 9 PostgreSQL statements + COMMIT
```

or:

```text
warm route-local work              7
cold exact component_schema fill  +1
cold ancestry bulk fill           +1
------------------------------------
full-cold                           9
```

The ancestry fill is one bulk statement for all missing distinct source lineages, not one query per child.

## Scaling characteristics

```text
requested child count
    -> row volume only
    -> no statement-count growth

distinct child template lineages
    -> in-memory ancestry checks when READY
    -> one bulk fill on cold MISS

parent ownership depth
    -> recursive work in Q3

cache state
    -> warm 7
    -> full-cold 9
```

No mutable `object_id -> root_object_id` materialization is introduced; root is derived by the protected recursive read to avoid subtree-wide ATTACH/DETACH maintenance.

## Frozen takeaway

```text
warm      = 7 PostgreSQL statements + COMMIT
full-cold = 9 PostgreSQL statements + COMMIT
```

Physical index proof and EXPLAIN evidence remain global M4 relational-schema follow-up work.
