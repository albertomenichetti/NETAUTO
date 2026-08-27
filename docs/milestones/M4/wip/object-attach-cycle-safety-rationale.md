# M4 WIP — Object ATTACH cycle-safety rationale

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note records the exact reason why the Object ATTACH rule:

```text
requested child must currently have no owner
```

is **necessary but not sufficient** to guarantee ownership acyclicity.

The note also records the batch-safe cycle predicate agreed for M4 discovery.

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

which means:

```text
A -> B
B -> P
```

The relational single-owner invariant is enforced by the current ownership fact having one row at most per child:

```text
object_components.child_object_id PRIMARY KEY
```

Therefore an Object can have at most one direct owner.

## Why an ownerless child can still create a cycle

Suppose the current ownership graph is:

```text
A -> B -> P
```

`A` currently has no owner:

```text
owner(A) = NULL
```

so it satisfies the ordinary ATTACH precondition that a requested child must be ownerless.

Now request:

```text
parent = P
child  = A
```

The new edge would be:

```text
P -> A
```

and the resulting graph becomes:

```text
A -> B -> P -> A
```

which is a cycle.

Therefore:

```text
child currently has no owner
```

only proves that adding a new owner does not violate the single-owner invariant. It does **not** prove that the child is not already an ancestor of the requested parent.

## Necessary cycle predicate

For an ATTACH edge:

```text
P -> C
```

the edge is cycle-safe only if `C` is not already in the owner/ancestor chain of `P`.

Conceptually:

```text
C not in owner_chain(P)
```

For a batch:

```text
parent = P
children = {C1, C2, ..., Cn}
```

all requested edges are cycle-safe iff:

```text
owner_chain(P) INTERSECT requested_child_ids = empty
```

The separate `parent != child` invariant remains a direct/self-cycle check and may also be enforced relationally.

## Why one traversal is sufficient for a batch

Because every Object can have at most one owner, walking from an Object toward its owners does not branch.

Starting from `P`, the graph shape is at most:

```text
P -> owner(P) -> owner(owner(P)) -> ... -> root
```

when read in the upward/owner direction.

It is therefore a single linear chain, not a tree traversal.

For a batch of `N` children attached to the same parent, M4 does **not** need `N` independent graph traversals.

It needs:

```text
1 traversal of owner_chain(P)
+
1 set-membership comparison against all requested child ids
```

This is the batch-level amortization property.

## Candidate PostgreSQL shape

The current candidate is one recursive query after ownership graph write arbitration has been acquired.

Conceptually:

```sql
WITH RECURSIVE owner_chain AS (
    SELECT parent_object_id
    FROM object_components
    WHERE child_object_id = :parent_object_id

    UNION ALL

    SELECT oc.parent_object_id
    FROM object_components oc
    JOIN owner_chain chain
      ON oc.child_object_id = chain.parent_object_id
)
SELECT parent_object_id
FROM owner_chain
WHERE parent_object_id = ANY(:requested_child_ids)
LIMIT 1;
```

The query need not materialize the entire chain in the application. It may answer only whether at least one requested child is already an ancestor of the parent.

Outcome:

```text
row returned
    -> at least one requested edge would create a cycle
    -> fail the whole atomic batch

no row returned
    -> current graph contains no cycle blocker for any requested child
```

Exact SQL remains an implementation detail subject to later verification and query-plan review; the semantic predicate above is the frozen requirement.

## Why graph-write arbitration is still required

A correct traversal against one snapshot is not sufficient by itself if concurrent ATTACH operations may add ownership edges while the predicate is being certified.

Two independently valid ATTACH candidates can jointly create a cycle.

Therefore edge-add operations require a common ownership graph write arbitration boundary, currently represented by the candidate/current:

```text
OWNERSHIP_GRAPH_WRITE_GATE
```

The intended order is:

```text
acquire ownership graph write gate
-> read fresh cycle predicate
-> if safe, persist requested ownership edges
-> commit
-> release gate
```

No competing ATTACH edge-add can change the graph between cycle certification and commit.

DETACH only removes an edge and cannot create a cycle. A concurrent DETACH may make an ATTACH that was conservatively rejected become valid later; that is an acceptable false failure and a caller retry can observe the newer state.

## Relationship with relational constraints

The responsibilities remain distinct:

```text
PRIMARY KEY(child_object_id)
    -> at most one current owner

FK parent_object_id -> objects.id
FK child_object_id  -> objects.id
    -> referenced Object lifetime/existence arbitration

CHECK parent_object_id != child_object_id
    -> direct self-cycle prevention

owner-chain cycle predicate + graph-write arbitration
    -> general DAG acyclicity
```

No single PK/FK/CHECK above can express the general transitive no-cycle invariant.

## Frozen takeaway

The important rule to retain is:

```text
OWNERLESS CHILD != CYCLE-SAFE CHILD
```

For `P -> C`, ATTACH requires both:

```text
C has no current owner
AND
C is not already an ancestor of P
```

For a batch with one parent, the second rule is checked once as:

```text
owner_chain(P) INTERSECT requested_child_ids = empty
```

under graph-edge-add arbitration.