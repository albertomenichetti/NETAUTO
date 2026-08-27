# M4 WIP — Object ATTACH root materialization decision

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note records the M4 decision on whether to denormalize the current ownership-tree root for each Object in order to accelerate Object ATTACH cycle checks.

The candidate denormalization considered was conceptually:

```text
object_roots
------------
object_id       PK / FK -> objects.id
root_object_id  FK -> objects.id
```

Such a structure would make lookup of the current root of an Object conceptually O(1):

```text
root(P) = object_roots[P]
```

## Why root lookup matters to ATTACH

Under the single-owner invariant, every requested ATTACH child must be ownerless at the protected mutation boundary.

If all requested children are ownerless, then a requested child can already be an ancestor of the parent only if that child is exactly the current root of the parent's ownership tree.

Therefore the protected cycle predicate can be reduced to:

```text
all requested children are currently ownerless
AND
root(parent) NOT IN requested_child_ids
```

The current normalized model has no persisted `root_object_id`, so finding `root(parent)` requires following the ownership chain upward until an Object with no owner is reached.

Because `object_components.child_object_id` is the single-owner authority, that traversal never branches: it is one linear owner chain.

## Denormalization trade-off

Persisting `object_id -> root_object_id` would make the read side cheaper but makes root state mutable for an entire subtree.

Example detached tree:

```text
B
└── C
    └── D
```

Before attachment:

```text
root(B) = B
root(C) = B
root(D) = B
```

After:

```text
ATTACH A -> B
```

all three derived rows would need to change:

```text
root(B) = A
root(C) = A
root(D) = A
```

Similarly:

```text
DETACH A -> B
```

would require rewriting the complete subtree back to:

```text
root(B) = B
root(C) = B
root(D) = B
```

Therefore root materialization trades:

```text
cycle-check read cost
    O(tree height)
```

for:

```text
ATTACH / DETACH derived-state maintenance
    O(subtree size)
```

and would broaden the mutation/concurrency surface because a single ownership edge mutation could require updates across many otherwise unrelated Object-root rows.

## M4 decision

M4 does **not** introduce a persisted `object_id -> root_object_id` denormalization for the normal ownership model.

The current cycle-check direction remains:

```text
ownership graph write arbitration
-> establish requested children are ownerless
-> resolve the current root of the parent through one recursive owner-chain query
-> verify root(parent) is not one of the requested child ids
-> bulk INSERT requested edges
```

The root lookup is one PostgreSQL statement and its work is bounded by ownership depth, not by the number of children in the ATTACH batch.

There is no worker cache for current Object roots because root membership is mutable runtime state and would require coherence/invalidation after ATTACH/DETACH.

## Why no denormalization yet

For the currently identified consumer, root lookup is needed only by cycle-safe ATTACH admission.

A recursive owner-chain read is therefore preferred over maintaining a mutable materialized root for every Object because it avoids:

- subtree-wide write amplification;
- extra mutable derived state;
- additional FK/index/maintenance requirements;
- broader concurrency coordination on ATTACH/DETACH;
- cache-coherence concerns for current roots.

## Revisit condition

`object_id -> root_object_id` remains a possible future optimization only if evidence shows that current root lookup becomes a frequent shared data-plane primitive whose aggregate read cost materially exceeds the write-amplification and concurrency cost of maintaining it.

Any future adoption must explicitly document its table, PK, FKs, indexes, consistency-maintenance protocol and denormalization rationale under the milestone relational-schema closure requirement.

## Frozen takeaway

For M4:

```text
NO persisted Object root materialization
NO current-root cache

root(parent)
    -> one recursive owner-chain statement
    -> bounded by tree height

ATTACH cycle safety
    -> all requested children ownerless
    -> root(parent) not requested
    -> protected by ownership graph write arbitration
```
