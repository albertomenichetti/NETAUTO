# M4 TO-BE API — Object schema binding

Status: GET ROUTE-LOCAL CLOSED / POST PARTIAL ROUTE-LOCAL FREEZE / M4 WIP / NON-NORMATIVE GLOBALLY

This file records the caller-facing contract frozen for the Object-relative schema surface during the M4 top-down TO-BE sweep. The GET read path is route-locally closed. Execution path, cache use, concurrency and persistence realization for schema mutation remain to be closed before marking the POST mutation route locally complete.

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

### GET TO-BE read path

The read must return the Object's current exact binding plus the stable template name in one coherent database statement.

Preferred simple SQL shape:

```sql
SELECT
    o.template_id,
    ot.name AS template_name,
    o.template_version AS version
FROM objects o
JOIN object_templates ot
  ON ot.id = o.template_id
WHERE o.id = :object_id;
```

The frozen requirement is not the textual join order but the physical access path:

```text
objects PK lookup by object_id
    -> at most one Object row
    -> obtain template_id/template_version

object_templates PK lookup by template_id
    -> at most one ObjectTemplate row
    -> obtain stable name
```

PostgreSQL may reorder/push predicates during planning. The simple join form is acceptable only while physical verification proves the intended bounded path rather than broad join work followed by filtering.

Architecture-wide physical review must verify this with `EXPLAIN (ANALYZE, BUFFERS)` or equivalent evidence. Expected plan shape is conceptually:

```text
Index/PK lookup objects(id = :object_id)
    -> one row
Nested Loop / equivalent
    -> Index/PK lookup object_templates(id = objects.template_id)
```

If evidence does not show this bounded access path, the production query shape or physical design must be changed; the route does not normatively depend on blind planner trust.

### GET cache/denormalization decision

No cache is used for this route.

Although `ObjectTemplate.name` is stable and cacheable, PostgreSQL must already be consulted for current Object existence and current mutable exact binding. A PK-to-PK join adds no extra round-trip and is simpler than splitting the result across DB plus cache lookup/fill.

No denormalized template name is copied into `objects`.

### GET concurrency/coherence

One SQL statement gives one coherent database snapshot of:

```text
Object existence
current template_id/template_version
matching stable template name
```

No lock is required.

A concurrent schema mutation is observed either before or after its commit; the GET does not expose an intermediate binding.

Missing Object:

```text
0 rows -> 404
```

### GET cost target

```text
1 PostgreSQL statement
    objects PK lookup
    object_templates PK lookup

0 cache lookups
0 locks
0 model-plane semantic reconstruction
0 denormalization
0 lifecycle work
```

`GET /objects/{id}/schema` is therefore ROUTE-LOCAL CLOSED, subject only to the architecture-wide physical-plan/index verification shared by the final M4 relational review.

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

## Route-local state

Frozen for the shared Object schema surface:

- Object-relative schema resource path is `/api/v1/core/objects/{object_id}/schema`;
- `GET` returns exactly `template_id`, `template_name`, `version`;
- `GET` does not expose effective schema or other ObjectTemplate metadata;
- `POST` replaces the former `/schema-change` public route;
- `POST` request remains `{ "target_version": <positive integer> }`;
- schema mutation changes version only within the Object's existing template lineage;
- successful `POST` returns `204 No Content`;
- ObjectTemplate effective-schema API remains the detailed model-plane schema surface.

GET route-local closure additionally freezes:

- one coherent PostgreSQL statement;
- no cache;
- no locks;
- no denormalized template name on Object;
- required physical path `Object PK -> ObjectTemplate PK`;
- simple JOIN is acceptable only if physical-plan evidence proves that bounded path;
- `0 rows -> 404`;
- architecture-wide `EXPLAIN (ANALYZE, BUFFERS)` verification handoff.

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
