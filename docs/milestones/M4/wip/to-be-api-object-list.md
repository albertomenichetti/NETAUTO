# M4 TO-BE API — Object LIST

Status: ROUTE-LOCAL CLOSED / M4 WIP / NON-NORMATIVE GLOBALLY

This file records the agreed TO-BE public contract and data path for `GET /api/v1/core/objects`.

The route is considered closed for the current M4 top-down sweep. This does not constitute the global M4 normative freeze and does not authorize implementation by itself.

## Signature

```http
GET /api/v1/core/objects
```

Request body: none.

Supported query parameters:

```text
object_template_id: UUID | optional
object_template_version: positive integer | optional
canonical_name: string | optional
cursor: string | optional
limit: positive integer | optional, default 100
```

Validation rule:

```text
object_template_version requires object_template_id
```

Success status: `200 OK`.

Collection filters do not dereference a path resource. An unknown `object_template_id` therefore yields an empty `200 OK` page rather than `404`.

## Exact, non-polymorphic ObjectTemplate filter semantics

`object_template_id` means exact equality against the stable ObjectTemplate lineage id stored on the Object:

```sql
objects.template_id = :object_template_id
```

It is explicitly **not** a polymorphic ObjectTemplate-space filter.

Given:

```text
Device
  -> Server
      -> LinuxServer
```

and current Objects:

```text
server-1.template_id = Server
linux-1.template_id  = LinuxServer
```

then:

```http
GET /api/v1/core/objects?object_template_id=<Server>
```

returns `server-1` but does not include `linux-1` merely because `LinuxServer` descends from `Server`.

This route does not consult ObjectTemplate ancestry and does not expand ancestors or descendants.

A future request such as "all Objects whose template is T or descends from T" is a distinct polymorphic query capability and must not be hidden inside this exact filter.

`object_template_version` is likewise exact version equality within the selected lineage:

```sql
objects.template_id = :object_template_id
AND objects.template_version = :object_template_version
```

## Canonical-name filter

`canonical_name` uses exact equality semantics:

```sql
objects.canonical_name = :canonical_name
```

It is not substring, prefix, fuzzy or full-text search.

## Success representation

```json
{
  "items": [
    {
      "id": "11111111-1111-1111-1111-111111111111",
      "canonical_name": "server-1",
      "object_template": {
        "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "version": 4
      }
    },
    {
      "id": "22222222-2222-2222-2222-222222222222",
      "canonical_name": "server-2",
      "object_template": {
        "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "version": 4
      }
    }
  ],
  "next_cursor": "..."
}
```

Empty page:

```json
{
  "items": [],
  "next_cursor": null
}
```

## Wire model

```text
ObjectSummaryDto
    id: UUID
    canonical_name: string
    object_template: ExactObjectTemplateRef

ExactObjectTemplateRef
    id: UUID
    version: positive integer

ObjectPageDto
    items: ObjectSummaryDto[]
    next_cursor: string | null
```

The structured `object_template: {id, version}` representation intentionally matches the exact ObjectTemplate reference frozen for `GET /objects/{object_id}`.

## Explicit exclusions

The collection summary does not include:

```text
properties
components
owner
relationships
ObjectTemplate mutable metadata
```

The route is a search/navigation collection surface, not a repeated complete Object representation.

## Pagination

Preserve deterministic keyset pagination over Object id.

Conceptually:

```text
ORDER BY objects.id ASC
cursor key = last returned Object id
limit + 1 internally to determine next_cursor
```

Cursor identity remains bound to the complete filter set:

```text
object_template_id
object_template_version
canonical_name
```

A cursor produced for a different filter set is not interchangeable.

## Data structures touched

TO-BE and AS-IS both require only:

```text
objects
```

No ObjectTemplate, ownership, Relationship or lifecycle table participates in the read.

## AS-IS cost

The current persistence path already projects only:

```text
id
canonical_name
template_id
template_version
```

from `objects`, applies optional equality filters plus the keyset predicate, orders by `id`, and applies the page limit.

Current database statements:

```text
1
```

Current read-side semantic revalidation:

```text
none
```

Current cache use:

```text
none
```

## TO-BE data path

Keep the same persistence shape:

```text
ordinary read UoW
    -> one SELECT on objects
    -> minimal summary projection
    -> application/wire reshape of template_id + template_version
       into object_template {id, version}
```

Conceptual SQL:

```sql
SELECT
    id,
    canonical_name,
    template_id,
    template_version
FROM objects
WHERE
    optional exact filters
    AND optional id > :cursor_id
ORDER BY id
LIMIT :limit_plus_one;
```

No properties JSONB should be read for this route.

## Complexity and weight

The operation is intentionally light.

Its cost is driven by:

```text
filter selectivity
page size
keyset traversal
```

It does not scale with:

```text
Object property count
component count
ownership depth
ObjectTemplate inheritance depth
Relationship count
lifecycle-event count
```

No M4 denormalization is required to make this operation viable.

## Concurrency guarantee

One PostgreSQL statement is the complete public read projection, so the statement snapshot is sufficient.

Required guarantee:

```text
one coherent page projection from one PostgreSQL statement snapshot
```

No application lock is required.

No multi-statement `coherent_read()` transaction is required.

Concurrent Object CREATE/RENAME/SCHEMA_CHANGE/DELETE may naturally affect whether a row is visible before or after the statement snapshot; the page itself must not mix observations from multiple statements because there is only one authoritative read statement.

## Caching

No cache is required or justified for this route.

The collection is current mutable data-plane state:

```text
Object existence
canonical_name
current exact ObjectTemplate pin
```

Caching it worker-locally would require coherency/invalidation semantics and is contrary to the M4 cache policy.

## Denormalization and schema implications

Required relational changes for this route:

```text
none
```

Required M4 materializations for this route:

```text
none
```

The route remains a direct projection from `objects`.

## Physical index review

The current schema already has the Object primary-key index and explicit indexes supporting ObjectTemplate and canonical-name filtering.

The exact final physical index set is intentionally reviewed globally in the following architecture phase, together with the complete Object workload, rather than frozen route-locally here.

This is the only intentionally deferred physical-design point for this route; it does not leave the logical data path or public contract open.

## Route-local closure

Frozen for this route:

- `GET /api/v1/core/objects`;
- no request body;
- query parameter names `object_template_id`, `object_template_version`, `canonical_name`, `cursor`, `limit`;
- `object_template_version` requires `object_template_id`;
- `object_template_id` is exact lineage equality and explicitly non-polymorphic;
- `object_template_version` is exact version equality;
- `canonical_name` is exact equality;
- unknown filter values yield an empty collection, not `404`;
- summary response with `id`, `canonical_name`, `object_template: {id, version}` only;
- no properties/components in list items;
- deterministic id-based keyset pagination;
- one SQL statement over `objects` only;
- no cache;
- no locks;
- no coherent multi-statement read;
- no denormalization/schema change required by this route.

Open only for the later global architecture phase:

```text
PHYSICAL INDEX REVIEW
```
