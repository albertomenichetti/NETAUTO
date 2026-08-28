# M4 WIP — Object DETACH Q1 failure mapping

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note freezes the route-local public failure precedence for Object DETACH Q1, without adding diagnostic-only PostgreSQL round trips.

## Route context

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}/detach
```

Body:

```json
{
  "child_object_ids": ["...", "..."]
}
```

The batch is atomic and non-convergent: every requested child must currently own the exact requested edge.

## Frozen Q1 shape

Q1 is one PostgreSQL business statement that combines:

- parent target existence lookup;
- requested child existence capture needed for lifecycle labels;
- bulk exact-edge DELETE;
- `RETURNING` of every actually deleted edge plus already-needed parent/child canonical names.

It returns enough information for the application to derive:

```text
parent_exists
existing_requested_child_count
deleted_count
deleted rows
```

No additional PostgreSQL statement is executed solely to improve error diagnostics.

## Frozen public precedence

```text
parent_exists = false
    -> HTTP 404
    -> resource_not_found

parent_exists = true
AND existing_requested_child_count < requested_count
    -> HTTP 422
    -> referenced_resource_not_found

all requested child Objects exist
AND deleted_count < requested_count
    -> HTTP 409
    -> ownership_conflict

deleted_count = requested_count
    -> continue to Q2 bulk DETACH_FROM lifecycle INSERT
```

## Meaning of ownership_conflict

`ownership_conflict` deliberately covers all current-state mismatches where the referenced child Object exists but the exact requested edge is not current, including:

```text
child is ownerless
child is owned by another parent
child is owned by the same parent under another slot
```

The route does not perform further diagnostic reads to distinguish those subcases.

## Why child absence remains 422

A missing child is a referenced command operand, not the URI/path target. Therefore it remains:

```text
422 referenced_resource_not_found
```

This mirrors the ATTACH distinction between path-target absence and referenced-operand absence.

## Failure atomicity

Q1 may physically delete a subset of matching edges before the application compares counts, but those deletes remain inside the open transaction.

If:

```text
deleted_count != requested_count
```

the application rolls back the transaction, restoring every edge deleted by Q1. Q2 is not executed.

## No diagnostic-only queries

Frozen route-local rule:

```text
failure details may use only information already produced by required execution work;
DETACH never issues an extra PostgreSQL query solely to enrich an error response.
```

## Frozen takeaway

```text
Q1 itself carries enough information to distinguish:
404 path target missing
422 referenced child missing
409 exact ownership edge not current

without any additional round trip.
```
