# M4 WIP — Object ATTACH batch cost profile

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note freezes the route-local PostgreSQL statement cost for the M4 TO-BE Object ATTACH batch path.

Public operation:

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}
```

with a non-empty batch of distinct `child_object_ids`.

The count below excludes `BEGIN` and `COMMIT` and counts the transaction-scoped advisory graph gate as one PostgreSQL statement.

## Warm path

Warm means the worker already has both required immutable/stable semantic cache inputs READY:

```text
ImmutableObjectTemplateCache[(parent.template_id, parent.template_version)]
    facet = component_schema

StableObjectTemplateAncestryCache[source_template_id]
    READY
```

No database query is performed solely for semantic cache warming.

The warm path is:

```text
PREPARATION

1. parent Object read
   -> id
   -> template_id
   -> template_version
   -> canonical_name

CACHE
   component_schema HIT
   -> resolve slot_name in memory
   -> obtain slot_declaring_template_id
   -> obtain target_template_id

2. bulk child Object read
   -> id
   -> template_id
   -> canonical_name
   -> verify every requested id exists
   -> collect distinct child template lineages

CACHE
   stable ObjectTemplate ancestry HIT
   -> O(1)-conceptual source/target compatibility checks in memory

MUTATION UoW

3. acquire OWNERSHIP_GRAPH_WRITE_GATE

4. parent Object FOR NO KEY UPDATE
   -> reread current template_id/template_version
   -> require exact match with prepared binding
   -> mismatch causes conservative failure

5. one protected graph-admission statement
   -> every requested child is currently ownerless
   -> traverse the parent owner-chain to its root
   -> root(parent) is not among requested child ids
   -> return only admissibility outcome

6. one bulk INSERT into object_components
   -> N ownership edges in one statement
   -> no ON CONFLICT
   -> PK/FK/CHECK violation aborts the statement and whole batch

7. one bulk INSERT into lifecycle_events
   -> N ATTACH_TO events in one statement
   -> one event per successfully inserted ownership edge
   -> parent/child canonical names are best-effort historical labels

COMMIT
```

Therefore:

```text
WARM ATTACH BATCH = 7 PostgreSQL statements + COMMIT
```

The statement count is independent of batch cardinality:

```text
1 child    -> 7 statements
10 children -> 7 statements
100 children -> 7 statements
```

The amount of row work naturally grows with the batch for the bulk child read, edge insert, and lifecycle insert, but database round trips do not grow per child.

The only graph traversal is the single protected owner-chain traversal for the parent. Its work is bounded by current ownership depth, not by the number of requested children.

## Full-cold path

Full-cold means neither semantic cache input needed by this route is READY on the worker.

The route adds at most:

```text
+1 bounded full component_schema fill for the exact parent ObjectTemplateVersion
+1 bounded bulk stable ObjectTemplate ancestry fill for all missing distinct child template lineages
```

After each fill, the same cache-hit execution path is resumed; there is no separate semantic implementation for cold execution.

Therefore the first no-contention full-cold execution is:

```text
FULL-COLD ATTACH BATCH = 9 PostgreSQL statements + COMMIT
```

or equivalently:

```text
warm route-local work              7
cold exact component_schema fill  +1
cold ancestry bulk fill           +1
------------------------------------
full-cold                           9
```

The ancestry fill is one bulk statement for all missing distinct source template lineages, not one query per child.

## Scaling characteristics

The route deliberately avoids N+1 database behavior.

The dominant dimensions are:

```text
number of requested children
    -> row volume in bulk child read / edge insert / lifecycle insert
    -> does NOT increase statement count

number of distinct child template lineages
    -> in-memory ancestry checks when READY
    -> on cold miss, one bulk ancestry fill statement

parent ownership depth
    -> recursive work in the single graph-admission statement

cache state
    -> warm 7 statements
    -> full-cold 9 statements
```

No mutable `object_id -> root_object_id` denormalization is introduced in M4 for this route. The root is derived by the protected recursive owner-chain read because materializing current roots would turn ATTACH/DETACH into potentially subtree-wide maintenance and increase write/concurrency amplification.

## Frozen takeaway

The TO-BE batch design amortizes all expensive route work across the whole batch:

```text
one parent preparation
one bulk child read
one slot resolution
one bulk ancestry compatibility phase
one graph gate
one parent stabilization
one graph admission
one bulk edge write
one bulk lifecycle write
```

The frozen route-local cost target is:

```text
warm      = 7 PostgreSQL statements + COMMIT
full-cold = 9 PostgreSQL statements + COMMIT
```

Physical index proof and EXPLAIN evidence remain architecture-wide follow-up work and do not change this route-local semantic closure.