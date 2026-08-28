# M4 WIP — Object DETACH batch non-convergent semantics

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note freezes the route-local semantic behavior of Object DETACH after the public ownership API was reshaped into command-explicit batch-by-slot routes.

Public route under review:

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}/detach
```

Request body:

```json
{
  "child_object_ids": ["...", "..."]
}
```

Success:

```http
204 No Content
```

## Frozen rule

DETACH uses the same strict/non-convergent direction chosen for ATTACH.

The requested batch is admissible only if every requested child currently has exactly the requested ownership edge:

```text
(parent_object_id,
 slot_declaring_template_id,
 slot_name,
 child_object_id)
```

Therefore:

```text
all N requested exact edges are current
    -> remove all N edges
    -> write corresponding DETACH_FROM lifecycle events
    -> commit once

one or more requested exact edges are not current
    -> fail the whole batch
    -> remove no edges
    -> write no lifecycle events
```

The batch remains atomic/all-or-nothing.

## No convergence on already-absent edge

M1 treated an exact DETACH that was already absent as a successful no-op. M4 intentionally supersedes that behavior for this route.

An already-absent requested edge is not considered successful convergence.

Rationale:

- the caller asked to remove a specific current semantic edge;
- if that edge is not current, the requested mutation did not occur;
- returning 204 would hide an incorrect parent, slot, child, or stale caller assumption;
- strict failure is consistent with the non-convergent ATTACH direction adopted in M4.

## Exact-edge identity matters

A child being owned somewhere is not sufficient.

For DETACH admission, the current ownership fact must match the requested parent and slot semantic identity exactly.

Examples:

```text
child ownerless
    -> requested exact edge absent -> batch fails

child owned by another parent
    -> requested exact edge absent -> batch fails

child owned by same parent but another slot
    -> requested exact edge absent -> batch fails

child owned by exact same parent + slot semantic edge
    -> requested edge exists -> candidate for removal
```

The precise public failure mapping is intentionally left to the later route-local failure pass.

## Batch shape

The same batch properties as ATTACH apply at the public boundary:

- `child_object_ids` is non-empty;
- duplicate IDs in the same request are invalid;
- request ordering has no semantic meaning;
- one request targets one parent and one slot;
- success is `204 No Content`;
- no persisted ownership rows are returned by the mutation.

## Consequence for implementation

The route must be able to certify that the set of current exact edges equals the requested child set before committing deletion semantics.

This does not yet freeze the exact SQL/locking realization. The next discovery steps must minimize PostgreSQL statements and avoid any diagnostic-only reads.

## Supersession note

This M4 decision supersedes the M1 rule:

```text
exact DETACH already absent -> success/no-op
```

for the M4 TO-BE Object ownership API.

## Frozen takeaway

```text
DETACH batch is strict and atomic.

Every requested exact edge must exist.
If any requested edge is absent or different,
the entire batch fails.

No no-op convergence.
```
