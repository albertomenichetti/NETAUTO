# ADR 0018: Runtime Component Membership Integrity

## Status

Accepted

## Context

NETAUTO persists runtime composition as direct ownership edges between current
Object instances. These edges are current authoritative structural state, not
historical snapshots and not schema declarations.

The runtime edge model must preserve three separate boundaries:

- endpoint existence and one-owner shape belong in relational constraints
- recursive subtree deletion belongs in the application workflow
- multi-node ownership cycle prevention remains a semantic invariant enforced
  by supported application workflows

It is also important to distinguish Object instance identity from
ObjectTemplate identity. Two distinct Objects may legitimately participate in a
membership edge even when they use the same ObjectTemplate or the same exact
ObjectTemplateVersion.

## Decision

ComponentMembership is represented as an authoritative current structural edge
by a relational table with physical Object endpoint foreign keys.

The table shape remains:

- `parent_object_id`
- `slot_name`
- `child_object_id`

The child has at most one direct owner, physically represented by:

- `PRIMARY KEY(child_object_id)`

Both endpoint foreign keys remain:

- `parent_object_id -> objects.id ON DELETE CASCADE`
- `child_object_id -> objects.id ON DELETE CASCADE`

These cascades delete only the `object_components` edge row. They do not cause
deletion of the opposite Object endpoint.

Recursive subtree deletion remains application semantics and is still performed
explicitly by `ObjectApplicationService.delete_object(...)`.

Detaching the incoming membership makes a subtree independent. A detached
subtree survives later deletion of its former owner.

Self membership means the same Object instance:

- `parent_object_id == child_object_id`

It does not mean that parent and child use the same ObjectTemplate or the same
ObjectTemplateVersion.

Same-template composition remains legal. For example:

- `Folder #1 -> Folder #2 -> Folder #3`

is valid when the schema allows the slot and the ownership graph is acyclic,
even if all three Objects use the same ObjectTemplate identity or exact
version.

Same-instance self membership is physically forbidden by:

- `CHECK(parent_object_id <> child_object_id)`

Empty slot names are physically forbidden by:

- `CHECK(slot_name <> '')`

Multi-node cycles such as `A1 -> A2 -> A1` or `A1 -> A2 -> A3 -> A1` are not
made impossible by declarative SQL constraints in this slice. They remain
semantic invariants prevented by supported application workflows.

## Consequences

- The database physically guarantees endpoint existence, one owner per child,
  non-empty slot names, and no same-instance self edge.
- Deleting either endpoint Object removes the edge row only; it does not
  recursively delete the opposite endpoint or a subtree.
- Direct persistence deletion semantics remain:
  - delete parent `A` in `A -> B` -> `B` survives and becomes unowned
  - delete child `B` in `A -> B` -> `A` survives and the edge disappears
  - delete middle node `B` in `A -> B -> C` -> `A` and `C` survive, `C`
    becomes unowned
- Supported application subtree deletion remains responsible for complete
  subtree discovery, cycle detection, runtime Relationship cleanup, audit
  history, descendants-before-parent deletion order, and single-UoW commit
  semantics.
- Same-template runtime composition remains supported because the self-edge
  check compares Object instance IDs, not ObjectTemplate identities.
