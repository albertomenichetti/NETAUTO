# M4 WIP — Object DETACH Q1 parent existence + exact-edge delete

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note freezes the first PostgreSQL business statement for Object DETACH.

Public command surface:

```text
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}/detach
```

with a non-empty duplicate-free `child_object_ids` batch.

DETACH is route-local non-convergent and atomic: every requested child must currently own exactly the requested parent/slot edge or the whole batch fails.

## Frozen Q1 shape

DETACH does not perform unlocked semantic preparation, does not resolve ObjectTemplate schema/cache state, does not acquire the ownership graph write gate, and does not explicitly lock the parent Object.

Q1 combines, in one bounded statement:

1. target-parent existence check by `objects.id`;
2. bulk deletion of the exact requested ownership edges;
3. capture of data required for DETACH lifecycle rows via `DELETE ... RETURNING` / joined current Object labels.

Conceptually:

```text
WITH parent AS (
    SELECT id, canonical_name
    FROM objects
    WHERE id = :parent_object_id
),
deleted AS (
    DELETE FROM object_components AS edge
    USING parent, objects AS child
    WHERE edge.parent_object_id = parent.id
      AND edge.slot_name = :slot_name
      AND edge.child_object_id = child.id
      AND edge.child_object_id = ANY(:child_object_ids)
    RETURNING
        edge.child_object_id,
        edge.parent_object_id,
        edge.slot_declaring_template_id,
        edge.slot_name,
        child.canonical_name AS child_canonical_name,
        parent.canonical_name AS parent_canonical_name
)
SELECT parent-existence signal plus deleted rows/count
```

The exact SQL carrier is implementation detail. The frozen semantic requirement is one business statement covering parent existence and exact-edge bulk deletion, with lifecycle inputs returned to the application.

## Application admission after Q1

```text
parent absent
    -> ROLLBACK
    -> 404 resource_not_found

parent present
AND deleted_count != requested_count
    -> ROLLBACK
    -> 409 ownership_conflict

parent present
AND deleted_count == requested_count
    -> Q2 bulk DETACH_FROM lifecycle INSERT
    -> COMMIT
    -> 204 No Content
```

No post-failure diagnostic query is allowed.

## Why parent existence is folded into Q1

A separate unconditional parent SELECT would add an always-paid PostgreSQL round trip while performing work that can be folded into the same bounded statement that deletes the edges.

This is not a diagnostic-after-failure query. Parent identity is the URI/path target and therefore must be distinguished from an ownership-edge mismatch:

```text
missing parent path target -> 404
existing parent but requested edge set not current -> 409
```

The folded Q1 preserves that public distinction without a third success-path statement.

## Why lifecycle remains Q2

Lifecycle insertion stays separate from Q1 because combining DELETE and lifecycle INSERT into one data-modifying CTE does not materially reduce PostgreSQL row work; it mainly removes one round trip while making the SQL more complex.

The two-statement realization is preferred for readability and also avoids lifecycle insertion work entirely when Q1 proves the batch inadmissible.

## Cost consequence

Successful DETACH has no cache warm/cold distinction.

```text
Q1 parent existence + exact-edge bulk DELETE ... RETURNING
Q2 bulk DETACH_FROM lifecycle INSERT

=> 2 PostgreSQL business statements
```

excluding BEGIN/COMMIT.

Round-trip count is independent of the number of requested child IDs; row volume grows with the batch, not statement count.

## Frozen takeaway

```text
DETACH Q1 = parent-target existence + exact batch edge deletion + returning
DETACH Q2 = lifecycle bulk insert
no diagnostic reread
no parent row lock
no graph gate
no schema/cache work
```
