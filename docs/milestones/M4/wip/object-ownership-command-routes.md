# M4 WIP — Object ownership command routes

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note freezes the M4 public HTTP command-route shape for Object ownership ATTACH and DETACH.

It supersedes only the previously frozen ATTACH route path. The already-closed ATTACH route-local semantic, concurrency, persistence, lifecycle, cost, and failure decisions remain unchanged unless explicitly superseded elsewhere.

## Command-surface principle

ATTACH and DETACH are semantic mutation commands, not generic CRUD operations on the `components` read projection.

They therefore use explicit command path segments and remain symmetric at the HTTP boundary.

## ATTACH

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}/attach
```

Request body:

```json
{
  "child_object_ids": [
    "<child-1>",
    "<child-2>"
  ]
}
```

Success:

```http
204 No Content
```

This route replaces the earlier M4 WIP path:

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}
```

No other closed ATTACH semantics are changed by this route correction.

## DETACH

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}/detach
```

Request body:

```json
{
  "child_object_ids": [
    "<child-1>",
    "<child-2>"
  ]
}
```

Success:

```http
204 No Content
```

The public shape is batch-per-slot, symmetric with ATTACH:

```text
one parent Object
+ one slot
+ N child Object ids
+ one explicit ownership command
```

Exact DETACH mutation semantics, convergence/idempotency, validation order, concurrency, Unit of Work, lifecycle realization, cost, failure mapping, and relational implications remain to be reviewed route-locally.

## Why not DELETE with a body

The route:

```http
DELETE /api/v1/core/objects/{parent_object_id}/components/{slot_name}
```

would naturally read as deletion of the slot collection/current membership as a whole, while the intended DETACH command selects a caller-provided subset of child Object ids.

Using an explicit `/detach` command avoids overloading DELETE request-body semantics and keeps ATTACH/DETACH visibly symmetric.

A future true "detach all children from this slot" capability, if ever required, is a separate semantic operation and is not introduced by M4 here.

## Frozen pair

```text
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}/attach
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}/detach
```

Both receive a non-empty `child_object_ids` batch body shape and return `204 No Content` on success.
