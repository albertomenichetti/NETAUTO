# M4 WIP — Object ATTACH cycle-safety rationale

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note records the exact reason why the Object ATTACH rule:

```text
requested child must currently have no owner
```

is **necessary but not sufficient** to guarantee ownership acyclicity, and freezes the refined batch-level predicate used by the M4 TO-BE candidate.

## Ownership direction

Ownership edges are directed:

```text
parent -> child
```

Example:

```text
A
└── B
    └── P
```

means:

```text
A -> B
B -> P
```

The single-owner invariant is represented relationally by:

```text
object_components.child_object_id PRIMARY KEY
```

so every Object can have at most one direct owner.

## Why an ownerless child can still create a cycle

Suppose:

```text
A -> B -> P
```

`A` is ownerless:

```text
owner(A) = NULL
```

but ATTACH:

```text
P -> A
```

would produce:

```text
A -> B -> P -> A
```

Therefore:

```text
OWNERLESS CHILD != CYCLE-SAFE CHILD
```

Ownerlessness protects the single-owner invariant. It does not by itself prove that the child is not already an ancestor of the requested parent.

## Key simplification under single-owner + ownerless certification

For one requested edge:

```text
P -> C
```

assume `C` is certified ownerless in the same protected graph state used for cycle admission.

Because every Object has at most one owner, the ancestors of `P` form one linear owner chain ending in exactly one root:

```text
P -> owner(P) -> owner(owner(P)) -> ... -> root(P)
```

Any ancestor of `P` other than `root(P)` necessarily has an owner.

Therefore an ownerless `C` can already be an ancestor of `P` **only if**:

```text
C == root(P)
```

This reduces the cycle predicate.

Instead of checking:

```text
C not in complete owner_chain(P)
```

we may check, in the same protected graph state:

```text
C is ownerless
AND
C != root(P)
```

For a batch:

```text
parent = P
children = {C1, C2, ..., Cn}
```

the final predicate is:

```text
ALL requested children are ownerless
AND
root(P) NOT IN requested_child_ids
```

The separate `parent != child` invariant remains independently protected, including by the relational CHECK candidate.

## Why one root lookup is sufficient for the whole batch

The batch has one parent `P`.

The root of `P` is common to all requested edges:

```text
P -> C1
P -> C2
...
P -> Cn
```

Therefore M4 does not need one traversal per child.

It needs only:

```text
1 fresh ownerless check for the whole child set
+
1 owner-chain traversal from P to root(P)
+
1 membership test root(P) IN requested_child_ids
```

The number of recursive traversals is independent of batch size.

## Protected PostgreSQL statement shape

The preferred direction is one PostgreSQL statement after ownership graph edge-add arbitration has been acquired.

Conceptually it should derive at least:

```text
has_owned_requested_child
root_object_id
```

For example, structurally:

```sql
WITH RECURSIVE
requested(child_id) AS (
    SELECT unnest(:requested_child_ids)
),
owner_chain(object_id) AS (
    SELECT :parent_object_id

    UNION ALL

    SELECT oc.parent_object_id
    FROM object_components oc
    JOIN owner_chain chain
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
    EXISTS (
        SELECT 1
        FROM object_components oc
        JOIN requested r
          ON r.child_id = oc.child_object_id
    ) AS has_owned_requested_child,
    (SELECT object_id FROM root) AS root_object_id;
```

Exact SQL is not normative here. The frozen semantic requirement is that ownerlessness and root discovery are evaluated from one protected current graph state.

Admission outcome:

```text
has_owned_requested_child == true
    -> FAIL whole batch

root_object_id IN requested_child_ids
    -> FAIL whole batch: cycle

otherwise
    -> graph predicate satisfied
```

## No root denormalization in M4

M4 deliberately does **not** introduce a mutable materialization such as:

```text
object_id -> root_object_id
```

A root lookup therefore remains a recursive owner-chain read bounded by tree depth.

The reason is write amplification. ATTACH or DETACH of a subtree root would change the root of every Object in that subtree, turning a small edge mutation into potentially `O(size of subtree)` derived-state maintenance.

For the ATTACH consumer currently under review, one recursive read is preferred over that mutable denormalization burden.

## Why graph-write arbitration is still required

The ownerless/root predicate is only valid if competing edge additions cannot change the graph between certification and commit.

Two ATTACH operations that are independently valid against stale snapshots can jointly create a cycle.

Therefore ATTACH edge additions require a common graph-write arbitration boundary, currently represented by:

```text
OWNERSHIP_GRAPH_WRITE_GATE
```

The intended order is:

```text
acquire graph-write gate
-> read fresh ownerless + root predicate
-> if safe, persist requested edges
-> commit
-> release gate
```

A concurrent DETACH removes edges and cannot create a cycle. It may make a conservatively rejected ATTACH become valid later; that false failure is acceptable and a caller retry can observe the newer state.

## Relationship with relational constraints

Responsibilities remain distinct:

```text
PRIMARY KEY(child_object_id)
    -> at most one current owner

FK parent_object_id -> objects.id
FK child_object_id  -> objects.id
    -> referenced Object existence/lifetime arbitration

CHECK parent_object_id != child_object_id
    -> direct self-cycle prevention

fresh ownerless + root(P) predicate
+ graph-write arbitration
    -> general cycle prevention
```

No ordinary PK/FK/CHECK expresses the transitive no-cycle invariant by itself.

## Frozen takeaway

For an atomic ATTACH batch to parent `P`, cycle admission is:

```text
1. every requested child is ownerless in the protected current graph
2. find root(P) by one owner-chain traversal
3. require root(P) not in requested_child_ids
```

This is sufficient under the single-owner invariant and requires only one recursive traversal for the whole batch.