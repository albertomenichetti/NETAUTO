# M4 WIP — Object ownership command routes

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note freezes the current M4 public HTTP command-route shape for Object ownership ATTACH and DETACH.

It remains a WIP discovery checkpoint, not architecture authority. Current route-local ownership is:

```text
ATTACH
    -> docs/milestones/M4/wip/object.md
       section: ATTACH children to one slot
       full-sweep complete

DETACH
    -> docs/milestones/M4/wip/to-be-api-object-detach-batch.md
       active route-local discovery input
```

The former ATTACH micro-WIP family was removed after lossless consolidation and reference cleanup; Git history remains the historical reasoning record. DETACH remains subject to its focused full sweep and later architecture-phase revalidation.

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

The reviewed ATTACH route-local discovery owner is now:

```text
object.md
    -> section: ATTACH children to one slot
```

That section owns the full-swept public contract, data/cache path, failure semantics, concurrency guarantees, lifecycle semantics, cost profile and architecture handoff.

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

The current DETACH route-local discovery candidate — including strict/non-convergent semantics, validation, candidate data path, lifecycle realization, failure mapping, cost profile and architecture handoffs — is consolidated in:

```text
to-be-api-object-detach-batch.md
```

That consolidation supersedes older DETACH route-local WIP directions where explicitly stated, while remaining fully non-normative until the focused DETACH full sweep and architecture-phase revalidation are complete.

## Why not DELETE with a body

The route:

```http
DELETE /api/v1/core/objects/{parent_object_id}/components/{slot_name}
```

would naturally read as deletion of the slot collection/current membership as a whole, while the intended DETACH command selects a caller-provided subset of child Object ids.

Using an explicit `/detach` command avoids overloading DELETE request-body semantics and keeps ATTACH/DETACH visibly symmetric.

A future true "detach all children from this slot" capability, if ever required, is a separate semantic operation and is not introduced by M4 here.

## Current WIP pair

```text
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}/attach
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}/detach
```

Both receive a non-empty `child_object_ids` batch body shape and return `204 No Content` on candidate success.

Current route-local owners:

```text
ATTACH -> object.md / ATTACH section / REVIEWED BASELINE
DETACH -> to-be-api-object-detach-batch.md / ACTIVE REVIEW INPUT
```

All material remains M4 WIP and must be deliberately adopted through the normal milestone governance/architecture gates before implementation is authorized.
