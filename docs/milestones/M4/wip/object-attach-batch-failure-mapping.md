# M4 WIP — Object ATTACH batch failure mapping

Status: INCORPORATED INTO ROUTE-LOCAL CLOSURE / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note preserves the first frozen ATTACH error-mapping block. The complete and current route-local error mapping and precedence are now owned by:

```text
docs/milestones/M4/wip/to-be-api-object-attach-batch.md

docs/milestones/M4/wip/object-attach-error-precedence.md
```

This file is not an independent complete error catalog.

## Retained baseline

The existing API failure classes remain the starting taxonomy:

```text
INVALID_REQUEST       -> 400
NOT_FOUND             -> 404
SEMANTIC_VALIDATION   -> 422
STATE_CONFLICT        -> 409
INTERNAL_FAILURE      -> 500
```

`404` is reserved for the resource identity selected by the URI/path; absent command operands use semantic-validation mapping.

## Retained frozen block

### Invalid request shape

Examples:

```text
missing/malformed body
missing child_object_ids
empty child_object_ids
malformed child UUID
duplicate child_object_ids
```

map to:

```text
HTTP 400
code = invalid_request
```

### Missing parent Object

```text
HTTP 404
code = resource_not_found
```

because `parent_object_id` is the path-target resource identity.

### Missing child Object operands discovered by normal bulk read

```text
HTTP 422
code = referenced_resource_not_found
```

All missing child ids already known from the normal bulk read may be exposed without extra DB work.

## Later decisions now authoritative elsewhere

Subsequent discovery added and froze:

```text
self reference
slot unavailable
child lineage incompatibility
parent binding changed concurrently
ownership conflict
ownership cycle
residual constraint-race translation
error precedence
no diagnostic-only DB queries
```

Those decisions are deliberately not duplicated here. Use the route-local closure files named above.

M4 also supersedes older M1 ATTACH identical-edge convergence and success-body behavior; normative reconciliation remains a milestone/global architecture task.
