# M4 WIP — Object ATTACH Q3 error-result split

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note refines the already-frozen ATTACH batch graph-admission statement without changing its query count, locking, arbitration or semantic predicate.

The previous draft returned only:

```text
admissible = true | false
```

That is insufficient for the public API because two distinct state conflicts must remain distinguishable:

```text
requested child already owned
requested ATTACH would introduce a cycle
```

## Frozen Q3 result shape

The protected Q3 statement remains one PostgreSQL statement under `OWNERSHIP_GRAPH_WRITE_GATE`, but returns two independent facts:

```text
has_owned_requested_child
root_is_requested
```

Conceptually:

```text
has_owned_requested_child = true
    -> at least one requested child currently has an owner

root_is_requested = true
    -> root(parent) is present in requested_child_ids
```

The application mapping is:

```text
has_owned_requested_child = true
    -> HTTP 409
    -> code = ownership_conflict

has_owned_requested_child = false
AND root_is_requested = true
    -> HTTP 409
    -> code = ownership_cycle

both false
    -> graph admission succeeds
    -> continue to Q4 bulk INSERT
```

If both flags are true, `ownership_conflict` wins because the batch already fails the ownerless precondition. No edge is inserted and no lifecycle event is emitted.

## Same-edge behavior in M4

M4 explicitly supersedes the previous ATTACH convergence behavior.

If a requested child is already owned by the same parent and same slot, it is still currently owned. Therefore:

```text
same exact edge already current
    -> HTTP 409
    -> code = ownership_conflict
```

There is no idempotent ATTACH convergence in the M4 candidate.

This is intentionally simpler than distinguishing:

```text
same owner + same slot
same owner + different slot
different owner
```

for persistence arbitration. Any existing current ownership fact for a requested child makes the atomic batch fail.

## Cost and concurrency impact

None.

The refinement does not add a statement or round-trip.

Warm-path statement count remains:

```text
7 PostgreSQL statements + COMMIT
```

Full-cold remains:

```text
9 PostgreSQL statements + COMMIT
```

The ownership graph write gate still serializes edge-add certification against competing ATTACH operations.

## Normative reconciliation handoff

Current AS-IS/M1 documentation states that an exact-current ATTACH edge converges successfully and that ATTACH returns a component projection. The M4 route candidate instead uses:

```text
same edge already current -> 409 ownership_conflict
successful batch ATTACH    -> 204 No Content
```

This contradiction is intentional discovery output and MUST be reconciled in normative documentation during M4 closure. It must not be silently carried forward as two simultaneous contracts.
