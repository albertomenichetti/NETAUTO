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

many state-change events
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

Concrete ratified examples:

```text
Object.RENAME
    -> exact canonical_name old -> new only

Object.DATA_CHANGE
    -> exact delta of actually changed properties
    -> exact ObjectTemplate binding context
    -> each property identified by (declaring_template_id, property_name)
    -> before/after distinguish canonical value from ABSENT

Object.SCHEMA_CHANGE
    -> exact binding transition (template_id, source_version, target_version)
    -> exact delta of runtime properties that actually changed
    -> each property identified by (declaring_template_id, property_name)
    -> before/after distinguish canonical value from ABSENT
    -> no full intrinsic Object snapshots
    -> no duplicated materialized slot or ownership payload
```

Conceptual RENAME detail fragment:

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

Conceptual DATA_CHANGE semantics:

```text
binding = T@V
changes = [
    (declaring_template_id, "hostname"): "srv01" -> "srv02",
    (declaring_template_id, "description"): value -> ABSENT
]
```

Conceptual SCHEMA_CHANGE semantics:

```text
binding_transition = T@VS -> T@VT
changes = [
    (declaring_template_id, "environment"): ABSENT -> "production",
    (declaring_template_id, "tag"): ["core"] -> "core"
]
```

A SCHEMA_CHANGE detail remains meaningful even when `changes = []`, because the exact binding transition itself is historical state.

The exact JSON shape for `ABSENT`, property-delta arrays/maps and binding placement remains open for Lifecycle API design; the semantic information is already fixed by the owning Object operations.

Other event kinds may have broader payloads when their semantic transition genuinely requires them. CREATE/DELETE may legitimately preserve broader resource state. Factual Relationship and ownership event families analogously retain only the complete transition required by their own contracts.

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

DATA_CHANGE and SCHEMA_CHANGE detail specifically must be able to express exact value-vs-ABSENT property deltas without expanding untouched Object state.

SCHEMA_CHANGE detail must additionally carry the exact source/target binding transition independently of whether any property value changed.

Enriching current `GET Object` with direct components does not imply adding components to lifecycle payloads. Ownership history remains represented through ATTACH/DETACH events.

## Important non-decisions

This WIP intentionally does **not** decide yet:

- exact summary fields for every lifecycle event family;
- exact detail DTO discriminated-union shape;
- exact JSON/typed carrier for DATA_CHANGE/SCHEMA_CHANGE `ABSENT` and property deltas;
- exact field naming/placement for SCHEMA_CHANGE binding transition;
- whether a summary should carry small family-specific metadata beyond current identifiers/names;
- exact ordering/cursor contract changes, if any;
- whether the object-scoped lifecycle list has any summary field different from the global list;
- exact 404 semantics for `GET /lifecycle-events/{event_id}`;
- physical SQL projection changes and indexes.

Those points belong to detailed operation-level API/read analysis.

## Candidate first-phase conclusion

Treat lifecycle-event collection endpoints as paginated discovery/history summaries whose response size is primarily bounded by page cardinality. Treat one lifecycle event as the resource whose detail read returns its complete persisted **operation-owned semantic transition**, not an automatically expanded aggregate snapshot.

SCHEMA_CHANGE now has a closed semantic payload boundary for later detail-DTO design: exact binding transition plus changed runtime-property delta, with no full Object snapshot or duplicated slot/ownership state.
