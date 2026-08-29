# M4 WIP — Lifecycle list/detail API discovery

Status: WIP / NON-NORMATIVE

## Scope

This note records an M4 API-design direction for lifecycle-event reads. It does not freeze the final wire contract and does not authorize implementation.

The question emerged while reviewing the Object read surface and comparing collection/detail semantics across Object and factual Relationship APIs.

## Concrete problem

The current lifecycle collection endpoints return complete lifecycle events, including `before_state` / `after_state` payloads where the event family carries them:

```text
GET /api/v1/core/lifecycle-events
GET /api/v1/core/objects/{object_id}/lifecycle-events
```

Some event kinds may legitimately carry large historical property payloads. A collection page can therefore become large for reasons unrelated to page cardinality.

Example candidate problem:

```text
GET /objects/server-1/lifecycle-events?limit=100

many DATA_CHANGE-like events
x potentially large historical transition payloads
```

Collection response size should not depend on complete historical payload size when the caller is only navigating events.

## Agreed collection/detail direction

Use collection endpoints as paginated event summaries and use a single-event detail read for the complete persisted transition payload of one event.

Conceptually:

```text
GET /lifecycle-events
GET /objects/{object_id}/lifecycle-events
    -> paginated event summaries
    -> no before_state / after_state payloads by default

GET /lifecycle-events/{event_id}
    -> one complete lifecycle event
    -> complete kind-specific historical transition payload
```

This follows the same collection/detail separation favored for other M4 public reads.

## Lifecycle payloads are kind-specific

M4 has ratified that lifecycle payload responsibility follows the owning operation:

```text
lifecycle payload
    = complete exact semantic transition owned by the operation

not automatically
    = complete aggregate before + after snapshots
```

Therefore single-event detail must not assume one universal full-snapshot shape for every intrinsic Object event.

Concrete ratified example:

```text
Object.RENAME
    -> exact canonical_name old -> new only
```

Conceptual detail fragment:

```json
{
  "before": {
    "canonical_name": "server-1"
  },
  "after": {
    "canonical_name": "web-01"
  }
}
```

Other event kinds may have broader payloads when their semantic transition genuinely requires them. CREATE/DELETE may legitimately preserve broader resource state; DATA_CHANGE and SCHEMA_CHANGE remain subject to their own full-sweep payload review.

Factual Relationship and ownership event families analogously retain only the complete transition required by their own contracts.

## Concrete summary examples

The exact summary DTO is intentionally still OPEN, but it should carry enough information to understand and select an event without carrying the complete historical transition payload.

Example intrinsic summary candidate:

```json
{
  "id": "event-id",
  "occurred_at": "...",
  "kind": "RENAME",
  "object": {
    "id": "object-id",
    "canonical_name": "web-01"
  }
}
```

Example ownership summary candidate:

```json
{
  "id": "event-id",
  "occurred_at": "...",
  "kind": "ATTACH_TO",
  "object": {
    "id": "child-id",
    "canonical_name": "eth0"
  },
  "destination": {
    "id": "parent-id",
    "canonical_name": "server-1"
  },
  "slot_name": "interfaces"
}
```

Relationship summaries can analogously expose historical identity/display metadata needed to select the event without carrying complete factual transition state.

## Single-event detail

A single-event detail API is the natural place for the complete **kind-specific** historical transition.

Conceptually:

```text
GET /lifecycle-events/{event_id}
```

Candidate public modeling direction:

```text
LifecycleEventDetail
    common event metadata
    + discriminated kind-specific payload
```

A generic `ObjectSnapshotDto` may still be useful for event kinds that genuinely own a complete intrinsic Object snapshot, but it is not the universal `before` / `after` type for all intrinsic events.

Enriching current `GET Object` with direct components does not imply adding components to lifecycle payloads. Ownership history remains represented through ATTACH/DETACH events.

## Important non-decisions

This WIP intentionally does **not** decide yet:

- exact summary fields for every lifecycle event family;
- exact detail DTO discriminated-union shape;
- exact payload boundary for Object DATA_CHANGE and SCHEMA_CHANGE;
- whether a summary should carry small family-specific metadata beyond current identifiers/names;
- exact ordering/cursor contract changes, if any;
- whether the object-scoped lifecycle list has any summary field different from the global list;
- exact 404 semantics for `GET /lifecycle-events/{event_id}`;
- physical SQL projection changes and indexes.

Those points belong to detailed operation-level API/read analysis.

## Candidate first-phase conclusion

Treat lifecycle-event collection endpoints as paginated discovery/history summaries whose response size is primarily bounded by page cardinality. Treat one lifecycle event as the resource whose detail read returns its complete persisted **operation-owned semantic transition**, not an automatically expanded aggregate snapshot.