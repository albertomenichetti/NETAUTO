# M4 WIP — Object ATTACH Q3 graph admission

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note freezes Q3 of the TO-BE batch `Object.ATTACH` mutation UoW.

Public candidate:

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}
```

with a non-empty `child_object_ids` batch.

Q1 has already acquired the ownership graph edge-add advisory gate and Q2 has already locked the parent Object and verified that its current `(template_id, template_version)` still matches the binding used during preparation to resolve the requested slot.

## Q3 purpose

Q3 certifies the mutable ownership-graph predicates required before inserting any requested edge.

Under the single-owner invariant:

```text
object_components.child_object_id PRIMARY KEY
```

a requested child can be attached only if it currently has no owner.

In addition, ownerless alone is not sufficient for acyclicity. Given one parent `P`, once every requested child is certified ownerless, the only requested child that could already be an ancestor of `P` is the current root of `P`'s ownership tree.

Therefore the frozen batch predicate is:

```text
all requested children are currently ownerless
AND
root(parent) is not among requested child ids
```

## One protected statement

Q3 evaluates both conditions in one PostgreSQL statement/snapshot while the ownership graph edge-add gate is already held.

Conceptually:

```sql
WITH RECURSIVE
requested(child_id) AS (
    SELECT unnest(:child_ids::uuid[])
),

owner_chain(object_id) AS (
    SELECT :parent_object_id

    UNION ALL

    SELECT oc.parent_object_id
    FROM owner_chain chain
    JOIN object_components oc
      ON oc.child_object_id = chain.object_id
),

root AS (
    SELECT chain.object_id
    FROM owner_chain chain
    WHERE NOT EXISTS (
        SELECT 1
        FROM object_components oc
        WHERE oc.child_object_id = chain.object_id
    )
)

SELECT
    NOT EXISTS (
        SELECT 1
        FROM requested r
        JOIN object_components oc
          ON oc.child_object_id = r.child_id
    )
    AND NOT EXISTS (
        SELECT 1
        FROM requested r
        JOIN root
          ON root.object_id = r.child_id
    ) AS admissible;
```

Exact SQL shape remains subject to implementation/query-plan verification; the semantic predicate and one-statement snapshot are the frozen requirements.

## Outcome

```text
admissible = false
    -> no ownership DML
    -> fail / rollback whole atomic batch

admissible = true
    -> graph admission succeeds
    -> proceed directly to bulk edge INSERT
```

The application does not need the full owner chain or root value as a public/domain result; Q3 may return only the boolean admission outcome.

## Why root-only is sufficient here

For a general candidate edge `P -> C`, ownerless alone is not cycle-safe. Example:

```text
A -> B -> P
owner(A) = NULL
P -> A would create A -> B -> P -> A
```

However, once Q3 proves every requested child ownerless in the same protected snapshot, any requested child that is already an ancestor of `P` cannot be an intermediate ancestor, because an intermediate ancestor has an owner. It must be the unique root of `P`'s current tree.

Thus:

```text
all requested C are ownerless
+
root(P) not in requested C
```

is equivalent to the full required cycle predicate for this batch shape.

## Concurrency boundary

The ownership graph edge-add advisory gate is acquired before Q3 and remains held through edge insertion and commit.

Therefore no competing ATTACH can add an edge between certification and commit.

A concurrent DETACH can only remove ownership edges. It may make a previously rejected batch become valid later, which is an acceptable conservative false failure, but it cannot turn a Q3-positive candidate into a newly cyclic graph.

The parent Object row remains locked through the same UoW so a concurrent parent `SCHEMA_CHANGE` cannot invalidate the already-resolved slot before commit.

## Relational authority split

Q3 owns the transitive graph admission predicate.

PostgreSQL constraints remain final authority for direct persistence invariants during the following bulk INSERT:

```text
PK(child_object_id)
    -> single current owner

FK parent_object_id -> objects.id
FK child_object_id -> objects.id
    -> referenced Object lifetime

CHECK parent_object_id != child_object_id
    -> direct self-edge prevention
```

Q3 does not duplicate those relational constraints; it adds the transitive no-cycle certification that ordinary PK/FK/CHECK constraints cannot express.