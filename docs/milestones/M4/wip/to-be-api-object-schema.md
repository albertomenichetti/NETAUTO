# M4 TO-BE API — Object schema binding

Status: GET FULL-SWEEP REVALIDATION — BLOCKS 1-2 RATIFIED / POST ACTIVE REVALIDATION / M4 WIP / NON-NORMATIVE GLOBALLY

## Current GET review status

`GET /objects/{object_id}/schema` is being revalidated against the current reviewed M4 baseline before absorption into [`object.md`](object.md).

Ratified in the current review pass:

```text
BLOCK 1 — public contract
    route remains GET /api/v1/core/objects/{object_id}/schema
    response remains exactly template_id + template_name + version
    template_name remains stable human-readable convenience, not identity
    revision remains internal and is not exposed
    effective schema/model metadata remain excluded

BLOCK 2 — read path + coherence/concurrency
    one PostgreSQL statement
    bounded Object PK -> ObjectTemplate PK path
    no exact ObjectTemplateVersion read merely to re-admit the persisted binding
    no revision read
    no cache
    no locks
    no retries
    no diagnostic-only consistency query
    statement snapshot is the complete coherence boundary
```

Still to close before current full-sweep absorption:

```text
BLOCK 3 — final failure mapping + architecture handoff/closure
```

## POST revalidation notice — materialized current component slots

The POST schema-mutation realization remains actively revalidated by [`object-schema-change.md`](object-schema-change.md) and the current component-persistence owner [`object-components-persistence.md`](object-components-persistence.md).

The current candidate maintains `object_component_slots` atomically with the Object exact binding and uses edge->slot relational arbitration for REMOVE/replacement races. Existing `object_components` edges still remain unchanged on successful normal schema migration.

Earlier supporting SCHEMA_CHANGE WIPs remain discovery evidence, but fingerprint/final-DML conclusions from them must not be treated as current without revalidation against the reviewed Object revision and component-persistence baseline.

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

Request body: none.

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

`template_id` is the authoritative template-lineage identity. `version` identifies the exact ObjectTemplateVersion currently persisted on the Object.

`template_name` is a stable human-readable convenience for the caller and does not participate in identity:

```text
binding identity
    = (template_id, version)

template_name
    = stable display/convenience metadata
```

Keeping `template_name` avoids forcing a second caller round trip merely to render a readable binding while the route can obtain it through the same bounded database statement.

`revision` is deliberately excluded. `objects.revision` is the internal technical intrinsic-row generation token owned by [`object-revision.md`](object-revision.md); this GET does not turn it into public Object or CAS state.

The route therefore complements rather than replaces:

```http
GET /api/v1/core/object-templates/{template_id}/versions/{version}/effective-schema
```

which remains the detailed model-plane schema surface.

### GET ratified read path

The read returns the Object's current exact binding plus the stable template name in one coherent PostgreSQL statement.

Preferred conceptual SQL shape:

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

The SQL text and planner join order are not frozen. The required logical/physical direction is bounded:

```text
objects PK lookup by object_id
    -> at most one Object row
    -> obtain template_id/template_version

object_templates PK lookup by template_id
    -> at most one ObjectTemplate lineage row
    -> obtain stable name
```

Architecture-wide physical review must later verify that the realized plan preserves this bounded access path with `EXPLAIN (ANALYZE, BUFFERS)` or equivalent evidence. Discovery does not freeze the exact SQL/SQLAlchemy carrier or final index set.

### No exact ObjectTemplateVersion read/re-admission

Normal GET schema does not join/read `object_template_versions` merely to re-admit the binding.

It does not ask whether the persisted exact version is currently:

```text
PUBLISHED
DEPRECATED
current default
latest/highest
otherwise admissible for a new binding today
```

The route reports the Object's current persisted exact binding. An Object legitimately pinned to a now-DEPRECATED exact ObjectTemplateVersion therefore remains a normal `200` result.

The existence of the exact version is already a persistence invariant of the current Object row through the Object -> exact ObjectTemplateVersion foreign-key relationship. The exact version in turn belongs to its ObjectTemplate lineage.

Normal GET schema therefore does not spend another read to recertify persisted reference integrity.

### GET cache/denormalization decision

No cache is used for this route.

Although `ObjectTemplate.name` is stable and cacheable, PostgreSQL must already be consulted for current Object existence and current mutable exact binding. A PK-to-PK join adds no extra round trip and is simpler than splitting one public result across DB current state plus worker-local cache lookup/fill.

No denormalized template name is copied into `objects` solely for this read.

### GET revision decision

`objects.revision` is not read.

The route neither exposes revision nor requires optimistic mutation freshness. One PostgreSQL statement already provides the complete coherent read snapshot, so reading the technical generation token would add no public correctness guarantee.

### GET concurrency/coherence

One PostgreSQL statement snapshot is the complete coherence boundary for:

```text
Object existence
current template_id/template_version
matching stable template_name
```

No explicit lock, retry, revision check or multi-statement read protocol is required.

Concurrent SCHEMA_CHANGE:

```text
GET snapshot before SCHEMA_CHANGE commit
    -> old exact version

GET snapshot after SCHEMA_CHANGE commit
    -> new exact version
```

The GET never exposes an intermediate binding generation.

Concurrent DELETE:

```text
GET snapshot sees Object
    -> 200 current binding

GET snapshot no longer sees Object
    -> 404 resource_not_found
```

RENAME, DATA_CHANGE, ATTACH, DETACH and factual Relationship mutations require no synchronization with this read because they do not change the public binding facts projected by this route.

### GET no diagnostic-only consistency query

The normal read path is not a persistence consistency audit.

Current database reference integrity is expected to make an Object row with a missing exact ObjectTemplateVersion or missing ObjectTemplate lineage unrepresentable through normal admitted writes.

Therefore the route does not split the read into multiple queries merely to distinguish hypothetical out-of-band corruption from normal Object absence.

Canonical hot-path principle:

```text
normal current read
    -> consume admitted persisted invariants

normal current read
    != proactive consistency sweep
```

If architecture later weakens/removes the database reference invariants on which this one-statement shape relies, this route must be revalidated rather than silently retaining the same failure interpretation.

### GET current cost target

```text
1 PostgreSQL business statement

bounded reads
    objects PK(object_id)
    object_templates PK(template_id)

public projection
    template_id
    template_version -> version
    template_name

0 exact-OTV semantic/status reads
0 cache lookups
0 locks
0 retries
0 revision reads
0 model-plane effective-schema reconstruction
0 lifecycle work
0 diagnostic-only consistency reads
```

The route has no warm/cold distinction.

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

The full POST path is still not closed. Its current detailed owner is [`object-schema-change.md`](object-schema-change.md), interpreted through the reviewed baseline in [`object-revision.md`](object-revision.md) and [`object-components-persistence.md`](object-components-persistence.md).

Current high-level component-side direction remains:

```text
MigrationPlan SOURCE -> TARGET
    -> immutable model-plane component delta

Object SCHEMA_CHANGE UoW
    -> use universal intrinsic expected_revision for intrinsic freshness
    -> maintain current object_component_slots delta atomically
    -> use relational slot/edge arbitration for REMOVE/replacement blockers
    -> update Object exact binding/properties
    -> advance intrinsic revision on committed new Object generation
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

Old intrinsic fingerprint conclusions in earlier SCHEMA_CHANGE source WIPs are not current authority where they conflict with the universal `objects.revision` baseline.

## Route-local state

Ratified in the current GET revalidation pass:

- Object-relative schema resource path is `/api/v1/core/objects/{object_id}/schema`;
- `GET` returns exactly `template_id`, `template_name`, `version`;
- `template_name` remains stable human-readable convenience and not identity;
- `GET` does not expose technical `revision`;
- `GET` does not expose effective schema or other ObjectTemplate metadata;
- one coherent PostgreSQL statement is the complete read boundary;
- no exact ObjectTemplateVersion read/status re-admission is required merely to report the persisted binding;
- no cache;
- no locks;
- no retries;
- no revision read;
- no denormalized template name on Object;
- bounded `Object PK -> ObjectTemplate PK` access path;
- no diagnostic-only consistency read;
- architecture-wide EXPLAIN/index verification remains a later handoff.

Still to close for the current GET full sweep:

```text
final failure mapping
architecture handoff / full-sweep closure wording
lossless absorption into object.md
```

Still to close for POST schema mutation:

```text
target-version admission requirements
current intrinsic Object state needed before preparation
source/target validation cache requirements
property migration and migration_default semantics
current object_component_slots maintenance
universal revision-aligned final freshness/retry path
short mutation UoW / slot-delta statement decomposition
constraint failure mapping for slot blockers
concurrency with DATA_CHANGE, ATTACH/DETACH, DELETE and another schema mutation
lifecycle SCHEMA_CHANGE persistence
no-op target-version semantics
TO-BE warm/cold cost
physical index review handoff
```
