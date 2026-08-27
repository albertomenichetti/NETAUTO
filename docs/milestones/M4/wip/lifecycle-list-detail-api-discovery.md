# M4 WIP — Lifecycle list/detail API discovery

Status: WIP / NON-NORMATIVE

## Scope

This note records an M4 API-design direction for lifecycle-event reads. It does not freeze the final wire contract and does not authorize implementation.

The question emerged while reviewing the Object read surface and comparing collection/detail semantics across Object and factual Relationship APIs.

## Concrete problem

The current lifecycle collection endpoints return complete lifecycle events, including complete `before` / `after` snapshots where the event family carries them:

```text
GET /api/v1/core/lifecycle-events
GET /api/v1/core/objects/{object_id}/lifecycle-events
```

For intrinsic Object events, a snapshot currently contains:

```text
id
canonical_name
template_id
template_version
properties
```

For factual Relationship events, factual state contains:

```text
relationship_definition_version
properties
```

The property objects are not bounded by the collection page size. A page of 100 DATA_CHANGE events can therefore carry 100 complete `before` snapshots plus 100 complete `after` snapshots, each with potentially large property maps.

Example:

```text
GET /objects/server-1/lifecycle-events?limit=100

100 DATA_CHANGE events
x 2 complete snapshots
x N properties per snapshot
```

This makes collection response size depend on both event count and arbitrary historical state size.

## Agreed direction

Use collection endpoints as paginated event summaries and introduce a single-event detail read for the complete historical payload.

Conceptually:

```text
GET /lifecycle-events
GET /objects/{object_id}/lifecycle-events
    -> paginated event summaries
    -> no complete before/after snapshots by default

GET /lifecycle-events/{event_id}
    -> one complete lifecycle event
    -> before/after included where the event family defines them
```

This follows the same collection/detail separation currently favored for other M4 public reads:

```text
GET /objects
    -> Object summaries
GET /objects/{id}
    -> complete Object first-level representation

GET /objects/{id}/relationships
    -> Object-relative Relationship summaries
GET one specific Relationship detail
    -> complete factual properties
```

## Concrete summary examples

The exact summary DTO is intentionally still OPEN, but it should carry enough information to understand and select an event without carrying the complete historical state.

Example intrinsic summary candidate:

```json
{
  "id": "event-id",
  "occurred_at": "...",
  "kind": "DATA_CHANGE",
  "object": {
    "id": "object-id",
    "canonical_name": "server-1"
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

Relationship summaries can analogously expose the historical object/destination names and relationship name needed to identify the event without duplicating complete factual property state.

## Single-event detail

A single-event detail API is the natural place for complete historical state.

Conceptually:

```text
GET /lifecycle-events/{event_id}
```

For intrinsic events this may include:

```json
{
  "before": {
    "id": "...",
    "canonical_name": "server-1",
    "template_id": "...",
    "template_version": 4,
    "properties": { "...": "..." }
  },
  "after": {
    "id": "...",
    "canonical_name": "server-1",
    "template_id": "...",
    "template_version": 4,
    "properties": { "...": "..." }
  }
}
```

The already-agreed historical snapshot boundary remains unchanged: enriching current `GET Object` with direct components does **not** imply adding components to lifecycle snapshots. Ownership history remains represented through ATTACH/DETACH events.

## Important non-decisions

This WIP intentionally does **not** decide yet:

- exact summary fields for every lifecycle event family;
- exact detail DTO discriminated-union shape;
- whether a summary should carry small family-specific metadata beyond the current identifiers/names;
- exact ordering/cursor contract changes, if any;
- whether the object-scoped lifecycle list has any summary field different from the global list;
- exact 404 semantics for `GET /lifecycle-events/{event_id}`;
- physical SQL projection changes and indexes.

Those points belong to the detailed operation-level API/read analysis.

## Candidate first-phase conclusion

Treat lifecycle-event collection endpoints as paginated discovery/history summaries whose response size is primarily bounded by page cardinality. Treat one lifecycle event as the resource whose detail read returns the complete persisted historical `before` / `after` state.
