# M4 TO-BE API — Object schema binding

Status: PARTIAL ROUTE-LOCAL FREEZE / M4 WIP / NON-NORMATIVE GLOBALLY

This file records the caller-facing contract frozen for the Object-relative schema surface during the M4 top-down TO-BE sweep. Execution path, cache use, concurrency and persistence realization for schema mutation remain to be closed before marking the mutation route locally complete.

## Resource concept

`/objects/{object_id}/schema` is the Object-relative view of the exact ObjectTemplate binding that currently governs the Object.

It is deliberately **not** a duplicate ObjectTemplate effective-schema API.

The model-plane detailed schema remains available through the ObjectTemplate API. The Object-relative schema surface answers only:

```text
which exact ObjectTemplate binding governs this Object now?
```

## GET current Object schema binding

```http
GET /api/v1/core/objects/{object_id}/schema
```

Path parameters:

```text
object_id: UUID
```

Query parameters: none.

### Success response

```json
{
  "template_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  "template_name": "Server",
  "version": 4
}
```

Conceptual DTO:

```text
ObjectSchemaBindingDto
    template_id: UUID
    template_name: string
    version: positive integer
```

No other ObjectTemplate metadata is returned.

Explicitly excluded:

```text
namespace
description
abstract
status
revision
parent binding
properties
effective properties
components
effective components
DataType semantics
```

`template_id` is the authoritative template-lineage identity. `template_name` is a stable human-readable convenience for the caller and does not participate in identity.

The route therefore complements rather than replaces:

```http
GET /api/v1/core/object-templates/{template_id}/versions/{version}/effective-schema
```

which remains the detailed model-plane schema surface.

## POST change Object schema binding

The former public route name `/schema-change` is replaced by the resource-oriented schema route:

```http
POST /api/v1/core/objects/{object_id}/schema
Content-Type: application/json
```

Path parameters:

```text
object_id: UUID
```

Query parameters: none.

### Request

```json
{
  "target_version": 5
}
```

Conceptual wire model:

```text
ObjectSchemaMutationBody
    target_version: positive integer
```

This operation changes only the exact version binding within the Object's existing ObjectTemplate lineage. It does not select a different `template_id`.

### Success response

```http
204 No Content
```

Response body: none.

The resulting binding is read through:

```http
GET /api/v1/core/objects/{object_id}/schema
```

The canonical complete Object representation remains:

```http
GET /api/v1/core/objects/{object_id}
```

## Separation of responsibilities

```text
GET /objects/{id}
    current Object representation

GET /objects/{id}/schema
    current exact ObjectTemplate binding, with readable template name

POST /objects/{id}/schema
    mutate the Object's exact version binding

GET /object-templates/{T}/versions/{V}/effective-schema
    detailed model-plane effective schema
```

This separation avoids copying complete effective schema into an Object-relative read while still giving callers a direct way to discover the schema governing one Object.

## Partial route-local freeze

Frozen so far:

- Object-relative schema resource path is `/api/v1/core/objects/{object_id}/schema`;
- `GET` returns exactly `template_id`, `template_name`, `version`;
- `GET` does not expose effective schema or other ObjectTemplate metadata;
- `POST` replaces the former `/schema-change` public route;
- `POST` request remains `{ "target_version": <positive integer> }`;
- schema mutation changes version only within the Object's existing template lineage;
- successful `POST` returns `204 No Content`;
- ObjectTemplate effective-schema API remains the detailed model-plane schema surface.

Still to close for POST schema mutation:

```text
target-version admission requirements
current Object state needed before preparation
source/target validation cache requirements
property migration and migration_default semantics
component/ownership compatibility checks
short mutation UoW
concurrency with properties mutation, ATTACH/DETACH, DELETE and another schema mutation
lifecycle SCHEMA_CHANGE persistence
no-op target-version semantics
TO-BE warm/cold cost
physical index review handoff
```

Still to close for GET schema binding:

```text
minimal read path / query count
cache benefit, if any
TO-BE cost
```
