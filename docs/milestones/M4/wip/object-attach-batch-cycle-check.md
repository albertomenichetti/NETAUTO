# M4 WIP — Object ATTACH batch cycle check

Status: SUPERSEDED DETAIL RECONCILED / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note reconciles the earlier owner-chain-intersection candidate with the final route-local ATTACH cycle predicate.

Ownership edges are directed:

```text
parent -> child
```

and current ownership is single-owner:

```text
child Object -> at most one current owner
```

## Earlier candidate

The earlier sufficient predicate was:

```text
owner_chain(parent) INTERSECT requested_child_ids = empty
```

under the ownership graph edge-add gate.

That predicate remains logically correct, but M4 discovery found a simpler equivalent test once current ownerlessness of every requested child is certified in the same protected graph state.

## Final simplification

If a requested child `C` is currently ownerless and is already an ancestor of parent `P`, then under the single-owner invariant `C` cannot be an intermediate ancestor: every intermediate ancestor has an owner.

Therefore `C` must be exactly the current root of `P`'s ownership tree.

The final batch predicate is consequently:

```text
all requested children are currently ownerless
AND
root(parent) not in requested_child_ids
```

This is sufficient for all requested `P -> Ci` edges in one batch.

Self-attachment remains rejected independently and also has a relational CHECK backstop.

## Protected statement

After acquiring `OWNERSHIP_GRAPH_WRITE_GATE`, one PostgreSQL statement computes two logical facts:

```text
has_owned_requested_child
root_is_requested
```

Application mapping:

```text
has_owned_requested_child = true
    -> ownership_conflict

otherwise root_is_requested = true
    -> ownership_cycle

otherwise
    -> graph admission succeeds
```

The owner chain is not materialized in application memory.

## Root lookup

No denormalized `object_id -> root_object_id` table/cache is introduced for M4 ATTACH.

Root lookup remains one recursive traversal following `object_components.child_object_id -> parent_object_id` upward from the parent.

This keeps read cost proportional to ownership depth and avoids the much larger write amplification that a materialized root would impose on ATTACH/DETACH of subtrees.

## Concurrency protection

The graph write gate serializes edge-add operations so no concurrent ATTACH can change the graph between certification and commit.

DETACH removes edges only and therefore does not require the graph-add gate. A concurrent DETACH can make an attempt conservatively fail, but cannot turn a positive ownerless+root certification into a cycle-producing false success for the fixed requested batch.

## Frozen decision

```text
single-owner current ownership
+
all requested children certified ownerless
+
one graph-protected root(parent) lookup

=> cycle iff root(parent) is requested
```

This note supersedes the earlier requirement to compare the full owner chain against every requested child while preserving the same acyclicity guarantee.
