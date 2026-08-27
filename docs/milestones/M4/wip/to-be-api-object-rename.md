# M4 WIP — TO-BE Object canonical-name mutation

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note records the caller-facing TO-BE contract and same-value semantics for the Object canonical-name mutation.

## Public signature

```http
PUT /api/v1/core/objects/{object_id}/canonical-name
```

Path:

```text
object_id UUID
```

Request body:

```json
{
  "canonical_name": "server-2"
}
```

`canonical_name` remains required current Object state with the existing semantic constraints:

```text
1..255 characters
no automatic normalization
not unique
not an alternative Object identity
```

## Success response

Successful mutation returns:

```http
204 No Content
```

The mutation does not return the full Object representation. Callers that need the current representation use the Object read surface explicitly.

## Same-name request

If the requested `canonical_name` is exactly equal to the Object's current persisted `canonical_name`, the command is a semantic no-op.

Frozen behavior:

```text
same current name
    -> 204 No Content
    -> no UPDATE
    -> no RENAME lifecycle event
```

A lifecycle event records a real semantic transition only; it is not emitted merely because a rename command was invoked.

## Public-surface rationale

The canonical-name change remains an explicit Object subresource mutation rather than introducing a generic Object PATCH/update operation.

Candidate surface:

```text
PUT /objects/{id}/canonical-name
```

This makes the replaced field explicit while retaining a narrow semantic command surface.

## Route-local closure status

Frozen here:

- HTTP method and route;
- request wire model;
- success response;
- same-name no-op semantics.

Still to close before route-local completion:

- minimal TO-BE data path;
- exact statement cost;
- concurrency behavior;
- lifecycle write realization;
- cache relevance;
- relational-schema implications.
