# M4 TO-BE API — Object canonical name mutation

Status: INTERFACE FROZEN / EXECUTION OPEN / M4 WIP / NON-NORMATIVE GLOBALLY

This note records the caller-facing contract frozen for the dedicated Object canonical-name mutation during the M4 top-down TO-BE sweep.

## Resource concept

`canonical_name` remains a dedicated mutable Object field rather than part of a generic PATCH surface.

This is intentionally retained even though the field is simple, because the Object mutation model continues to expose explicit semantic operations rather than a generic Object update endpoint. A real canonical-name change also owns its intrinsic lifecycle transition.

## TO-BE signature

```http
PUT /api/v1/core/objects/{object_id}/canonical-name
Content-Type: application/json
```

Path parameters:

```text
object_id: UUID
```

Query parameters: none.

Request body:

```json
{
  "canonical_name": "server-2"
}
```

Conceptual wire model:

```text
ObjectCanonicalNameMutationBody
    canonical_name: string, length 1..255
```

The value is not an Object identity and is not required to be unique.

## Success response

```http
204 No Content
```

Response body: none.

The updated Object representation is read through:

```http
GET /api/v1/core/objects/{object_id}
```

## Public-surface decision

The current public operation:

```http
POST /api/v1/core/objects/{object_id}/rename
```

is replaced in the M4 TO-BE candidate by the field-resource-oriented form:

```http
PUT /api/v1/core/objects/{object_id}/canonical-name
```

No generic Object PATCH/update operation is introduced.

## Frozen boundary

Frozen here:

- dedicated canonical-name mutation remains part of the public Object surface;
- method/path are `PUT /api/v1/core/objects/{object_id}/canonical-name`;
- request body is exactly `{ "canonical_name": <string> }`;
- canonical-name validation remains `1..255` characters;
- successful mutation returns `204 No Content`;
- no full Object representation is returned;
- no generic Object PATCH is introduced.

Still open for route-local closure:

```text
same-name / no-op semantics
minimal read/write path
lifecycle emission behavior
concurrency realization
TO-BE cost
relational/index implications
```
