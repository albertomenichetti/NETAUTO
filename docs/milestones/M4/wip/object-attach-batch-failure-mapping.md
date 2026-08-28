# M4 WIP — Object ATTACH batch failure mapping

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note records route-local public failure mapping decisions for the M4 Object ATTACH batch redesign.

Public route candidate:

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}
```

Body:

```json
{
  "child_object_ids": ["<child-1>", "<child-2>"]
}
```

This document is intentionally incremental. Additional ATTACH failure cases will be appended as discovery closes them.

## Existing API error-contract baseline

The existing API contract distinguishes:

```text
INVALID_REQUEST       -> 400
NOT_FOUND             -> 404
SEMANTIC_VALIDATION   -> 422
STATE_CONFLICT        -> 409
INTERNAL_FAILURE      -> 500
```

It also reserves `404` for the resource identity selected by the URI/path; absent command operands use semantic-validation mapping instead.

M4 may supersede older ATTACH-specific semantics where explicitly frozen during discovery. Any contradiction with current normative documentation must be reconciled at milestone closure rather than silently ignored.

## Frozen block 1 — request shape and resource existence

### Invalid request shape

The following are `INVALID_REQUEST` failures:

```text
missing/malformed body
missing child_object_ids
empty child_object_ids
malformed child UUID
request contains duplicate child_object_ids
```

Public mapping:

```text
HTTP 400
code = invalid_request
```

Rationale:

- these failures can be determined from the request representation itself;
- duplicate child ids make the batch representation invalid and are not a mutable-state conflict;
- no ownership/database state interpretation is required to classify them.

### Missing parent Object

If `parent_object_id` does not identify an existing Object:

```text
HTTP 404
code = resource_not_found
```

Canonical details candidate:

```json
{
  "resource_type": "object",
  "id": "<parent_object_id>"
}
```

Rationale:

`parent_object_id` is the resource identity selected by the request path, therefore absence is a path-target not-found condition.

### Missing child Object operands

If one or more requested `child_object_ids` do not identify existing Objects:

```text
HTTP 422
code = referenced_resource_not_found
```

The batch-aware `details` candidate exposes all missing child ids already known from the single bulk child read:

```json
{
  "resource_type": "object",
  "ids": [
    "<missing-child-1>",
    "<missing-child-2>"
  ]
}
```

Rationale:

- child ids are command operands, not URI/path target identities;
- returning all missing child ids does not require an additional database round-trip;
- batch diagnostics allow the caller to repair the request in one pass;
- the public details remain bounded by the request batch itself.

## Explicit M4 reconciliation note

Existing M1/Object documentation currently describes older ATTACH behavior including exact-edge idempotent convergence and a different success response shape. M4 discovery has explicitly superseded those route-local behaviors for the batch redesign. The global normative documentation must be reconciled during M4 closure; this WIP does not modify normative docs.
