# M4 WIP — Lifecycle summary data-path discovery

Status: WIP / NON-NORMATIVE

## Scope

This note records the first-phase data-path consequence of the M4 API direction that lifecycle collection endpoints return paginated event summaries while complete historical `before` / `after` snapshots are retrieved only through a single-event detail read.

This is discovery only. It does not freeze route shapes, exact summary DTO fields, or implementation details.

## Agreed API direction

Collection reads:

```text
GET /api/v1/core/lifecycle-events
GET /api/v1/core/objects/{object_id}/lifecycle-events
```

are candidates to return bounded event summaries rather than complete event snapshots.

A separate single-event detail read is the candidate surface for complete historical state:

```text
GET /api/v1/core/lifecycle-events/{event_id}
```

The exact route and DTO are intentionally deferred to per-API design.

## Current persistence behavior

`LifecycleStore.list_events()` currently selects the complete `object_lifecycle_events` row for every collection item and passes every row through the complete lifecycle decoder.

For intrinsic and factual Relationship state-change events this means the collection path reads and decodes:

```text
before_state
after_state
```

including complete canonical historical property maps.

This can be materially larger than the event metadata needed to render a collection page.

Concrete example:

```text
100 DATA_CHANGE events
x 2 snapshots per event
x 200 properties per snapshot
```

A summary collection should not transfer or decode those JSONB payloads merely because they are stored in the same persistence row.

## Target collection projection

Strong candidate: keep one SQL statement, but project only metadata required by the summary DTO and filters/pagination.

Conceptually:

```text
id
occurred_at
kind
object_id
canonical_name
destination_object_id
destination_canonical_name
relationship_id
relationship_definition_id
relationship_name
slot_declaring_template_id
slot_name
```

with family-inapplicable fields remaining NULL as they already do in the shared lifecycle table.

Do not select in the collection path:

```text
before_state
after_state
```

The exact final summary field set is deferred until the public lifecycle routes are designed in detail.

## Single-event detail path

The single-event detail read is the candidate path that loads the complete row, including:

```text
before_state
after_state
```

and decodes the complete historical event carrier.

Historical Object snapshots remain intentionally distinct from the richer current `GET Object` representation:

```text
id
canonical_name
template_id
template_version
properties
```

They do not gain current component expansion merely because `GET /objects/{id}` becomes richer.

Ownership history remains represented by dedicated ATTACH/DETACH events.

## Decoder separation

The collection path should not invoke the complete historical snapshot decoder.

Candidate separation:

```text
LifecycleEventSummary
    -> metadata-only row decoder / projection

LifecycleEvent detail
    -> complete event decoder including before_state / after_state
```

This avoids decoding data that the public collection does not expose.

## Global lifecycle collection

For:

```text
GET /api/v1/core/lifecycle-events
```

the target remains one database statement.

No cache is needed.

No join is required solely to populate summary display names because lifecycle events already persist historical Object / destination names as event metadata.

Therefore:

```text
DB round trips
    current: 1
    target:  1

DB payload
    current: complete event rows
    target:  summary projection only

historical JSONB decoding
    current: every collection item
    target:  none in collection path
```

## Object-scoped lifecycle collection

For:

```text
GET /api/v1/core/objects/{object_id}/lifecycle-events
```

preserve the M3 single-statement framing that distinguishes:

```text
Object absent
    -> 404

Object exists, no matching events
    -> 200 []

Object exists, matching events
    -> paginated summary page
```

The M4 change is that the event-page CTE / projection should carry summary columns only rather than the complete `before_state` / `after_state` payloads.

## First-phase conclusion

Lifecycle collection optimization is not merely an HTTP serialization change.

The target data path should avoid reading and decoding complete historical snapshots when the caller requested only a paginated collection. `before_state` / `after_state` belong to the single-event detail path.

This keeps collection cost proportional primarily to event count and summary metadata rather than to the potentially unbounded size of historical property maps.

Locking and concurrency realization are intentionally deferred to the global second phase.
