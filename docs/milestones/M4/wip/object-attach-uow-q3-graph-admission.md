# M4 WIP — Object ATTACH Q3 graph admission

Status: RECONCILED DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note freezes the final Q3 semantics for batch `Object.ATTACH`.

Q1 has acquired `OWNERSHIP_GRAPH_WRITE_GATE`. Q2 has locked the parent Object and verified that its current exact binding still equals the binding used during preparation.

## Q3 predicate

Q3 evaluates the mutable ownership predicates in one PostgreSQL statement/snapshot:

```text
all requested children currently ownerless
AND
root(parent) not among requested child ids
```

The root is derived by recursively following the single-owner chain upward. No mutable root materialization is introduced.

Under the single-owner invariant, once all requested children are ownerless, any requested child that is already an ancestor of the parent must be exactly the current root; an intermediate ancestor necessarily has an owner.

## Final result shape

The earlier opaque result:

```text
admissible = true | false
```

is superseded because it cannot distinguish public ownership-conflict and cycle diagnostics without another query.

Q3 still remains **one statement**, but returns two logical facts:

```text
has_owned_requested_child
root_is_requested
```

Application precedence:

```text
has_owned_requested_child = true
    -> 409 ownership_conflict

otherwise root_is_requested = true
    -> 409 ownership_cycle

otherwise
    -> graph admission succeeds
    -> continue to Q4
```

An already-current identical edge is included in `has_owned_requested_child=true`; M4 ATTACH does not converge idempotently on an existing edge.

## One protected snapshot

Conceptually, one recursive statement contains:

```text
requested child set
+
EXISTS ownership row for requested children
+
owner chain rooted at parent
+
root derivation
+
root membership test against requested set
```

The exact SQL is an implementation detail subject to later query-plan verification. The frozen requirements are one statement, one protected snapshot, and the two-result classification above.

The application never receives or materializes the whole owner chain.

## Concurrency boundary

The graph edge-add gate remains held from before Q3 through Q4/Q5 and commit. No competing ATTACH can add ownership structure between certification and persistence.

DETACH may remove edges concurrently. Edge removal cannot create a cycle; it can at most make a failed ATTACH conservative relative to a later graph state.

The parent Object lock remains held so parent SCHEMA_CHANGE cannot invalidate the already-resolved slot before commit.

## Relational authority split

Q3 provides fresh mutable graph admission and distinguishes conflict/cycle outcomes.

Q4 constraints remain final persistence authorities:

```text
PK(child_object_id)
    -> at most one current owner, including residual races

FK parent_object_id -> objects.id
FK child_object_id  -> objects.id
    -> referenced Object lifetime

CHECK parent_object_id <> child_object_id
    -> self-edge backstop
```

No diagnostic-only reread is permitted after a failure.
