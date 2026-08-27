# M4 WIP — Object ATTACH batch cycle check

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note freezes the route-local acyclicity check for batch Object ATTACH.

Public candidate:

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}
```

with one parent Object `P` and a non-empty set of requested child Objects `{C1..Cn}`.

## Relevant ownership invariant

Current ownership is single-owner:

```text
child Object -> at most one current owner
```

Equivalently, following the incoming ownership relation from any Object yields at most one owner at each step.

Ownership edges are directed:

```text
parent -> child
```

Adding `P -> C` creates a cycle iff `C` is already an ancestor of `P` in the current ownership graph.

Because each Object has at most one owner, the current ancestors of `P` form one unique owner chain rather than a branching graph.

## Frozen batch simplification

For a batch that adds only edges from the same parent `P`:

```text
P -> C1
P -> C2
...
P -> Cn
```

acyclicity does not require one traversal per requested child.

The command may instead:

```text
1. obtain the current owner chain of P once
2. materialize requested child ids as a lookup set
3. fail if any requested child id occurs in P's owner chain
4. otherwise all requested P -> Ci edges are cycle-safe relative to that graph snapshot
```

Self-attachment `P -> P` is already rejected independently and is also a direct cycle.

## Why one traversal is sufficient

For any requested child `Ci`, a newly added edge `P -> Ci` creates a cycle exactly when a pre-existing path exists:

```text
Ci -> ... -> P
```

With single-owner ownership, that path exists iff `Ci` appears while repeatedly following the current owner of `P` upward.

All requested new edges share the same source parent. The batch itself introduces no edge between two requested children, so successful addition of several sibling edges does not create a new path among those children that would require sequential re-evaluation.

Therefore one owner-chain traversal of `P` is sufficient for the whole batch.

## Concurrency protection direction

The current architecture already identifies ownership edge addition as a graph-wide predicate that must not be certified concurrently by independent ATTACH operations capable of jointly creating a cycle.

The route-local candidate therefore retains one ownership graph write gate for the whole batch:

```text
OWNERSHIP_GRAPH_WRITE_GATE
```

The gate is acquired once per batch, not once per child.

After the gate is held, the cycle predicate is read from a fresh PostgreSQL statement before inserting the requested edges.

A concurrent DETACH does not require the graph-add gate because edge removal cannot create a cycle. If a DETACH removes part of the chain while ATTACH is checking it, a stale conservative failure is acceptable; it cannot produce a false-success cycle. Another concurrent ATTACH is serialized by the graph-add gate.

## Cost shape

For cycle certification, batch cost is therefore:

```text
1 gate acquisition
1 owner-chain traversal/query rooted at parent P
O(chain_length + requested_child_count) application comparison
```

not:

```text
N independent graph traversals
```

The exact SQL shape for loading the owner chain and its required physical index are deferred to the remaining ATTACH route-local SQL/index review and the final global physical-schema phase.

## Frozen decision

```text
single parent batch ATTACH
+
single-owner current ownership

=> cycle check = one current owner-chain traversal of parent
=> reject if any requested child appears in that chain
=> one graph-write gate acquisition for the whole batch
```
