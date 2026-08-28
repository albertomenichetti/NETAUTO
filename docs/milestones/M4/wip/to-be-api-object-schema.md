# M4 TO-BE API — Object schema binding

Status: GET ROUTE-LOCAL CLOSED / POST ACTIVE REVALIDATION / M4 WIP / NON-NORMATIVE GLOBALLY

## POST revalidation notice — materialized current component slots

The GET `/objects/{object_id}/schema` checkpoint remains unchanged by the current finding.

The POST schema-mutation realization is actively revalidated by [`object-component-slots-data-plane-materialization.md`](object-component-slots-data-plane-materialization.md).

The new candidate materially reopens supporting schema-change WIPs that assumed effective slots remained model-plane-only and that outgoing ownership edges had to participate in the whole-Object optimistic fingerprint.

Current reopened assumptions include:

```text
ADD slot creates no runtime slot row
REMOVE/replacement admission decided from preparatory ownership snapshot
outgoing ownership edges belong to SCHEMA_CHANGE fingerprint
ATTACH/DETACH must rendezvous through the parent Object lock
final SCHEMA_CHANGE business write touches only objects + lifecycle
successful SCHEMA_CHANGE performs no component-related data-plane DML
```

The current candidate instead maintains `object_component_slots` atomically with the Object exact binding and uses edge->slot FK arbitration for REMOVE/replacement races. Existing `object_components` edges still remain unchanged on successful normal schema migration.

Supporting WIPs affected transitively include at least:

```text
object-schema-change-component-migration.md
object-schema-change-component-admission-from-snapshot.md
object-schema-change-preparation-aggregate-read.md
object-schema-change-protected-fingerprint-read.md
object-aggregate-fingerprint-canonical-json.md
object-aggregate-fingerprint-sha256.md
object-schema-change-q4-final-mutation.md
object-schema-change-warm-cost.md
```

They remain discovery evidence, but their ownership-edge fingerprint/final-DML conclusions must not be treated as current without revalidation against the new materialization candidate.

This file records the caller-facing contract for the Object-relative schema surface during the M4 top-down TO-BE sweep.

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

Architecture-wide physical review must verify this with `EXPLAIN (ANALYZE, BUFFERS)` or equivalent evidence.

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
0 denormalized template name
0 lifecycle work
```

`GET /objects/{id}/schema` remains ROUTE-LOCAL CLOSED, subject to architecture-wide physical-plan/index verification.

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

This separation avoids exposing complete model-plane effective schema in the Object-relative schema read.

## Current POST candidate direction after revalidation

The full POST path is still not closed, but the component side now has a stronger candidate:

```text
MigrationPlan SOURCE -> TARGET
    -> immutable model-plane component delta

Object SCHEMA_CHANGE UoW
    -> protect/revalidate mutable intrinsic Object state
    -> maintain current object_component_slots delta atomically
    -> existing edge FK is final REMOVE/replacement blocker authority
    -> update Object exact binding/properties
    -> append SCHEMA_CHANGE lifecycle
    -> COMMIT
```

Candidate slot delta:

```text
ADD
    -> INSERT slot row

REMOVE
    -> DELETE slot row

continuous target widening
    -> UPDATE target_template_id

semantic replacement
    -> key-changing UPDATE slot_declaring_template_id
       + target_template_id as required

position-only change
    -> no data-plane slot DML
```

The Object binding and slot materialization must become visible atomically.

Candidate fingerprint revalidation now questions whether outgoing `object_components` membership belongs in the optimistic fingerprint at all. The preferred direction is intrinsic Object fingerprinting plus final relational slot/edge arbitration, but exact UoW/statement decomposition remains OPEN.

## Route-local state

Frozen for the shared public schema surface:

- Object-relative schema resource path is `/api/v1/core/objects/{object_id}/schema`;
- `GET` returns exactly `template_id`, `template_name`, `version`;
- `GET` does not expose effective schema or other ObjectTemplate metadata;
- `POST` replaces the former `/schema-change` public route;
- `POST` request remains `{ "target_version": <positive integer> }`;
- schema mutation changes version only within the Object's existing template lineage;
- successful `POST` returns `204 No Content`;
- ObjectTemplate effective-schema API remains the detailed model-plane schema surface.

GET route-local closure retains:

- one coherent PostgreSQL statement;
- no cache;
- no locks;
- no denormalized template name on Object;
- required bounded `Object PK -> ObjectTemplate PK` physical path;
- `0 rows -> 404`;
- architecture-wide EXPLAIN verification handoff.

Still to close for POST schema mutation:

```text
target-version admission requirements
current intrinsic Object state needed before preparation
source/target validation cache requirements
property migration and migration_default semantics
current object_component_slots maintenance
final intrinsic fingerprint scope
short mutation UoW / slot-delta statement decomposition
constraint failure mapping for slot blockers
concurrency with properties mutation, ATTACH/DETACH, DELETE and another schema mutation
lifecycle SCHEMA_CHANGE persistence
no-op target-version semantics
TO-BE warm/cold cost
physical index review handoff
```
