# M4 WIP — Lifecycle summary data-path discovery

Status: WIP / NON-NORMATIVE

## Scope

This note records the first-phase data-path consequence of the M4 API direction that lifecycle collection endpoints return paginated event summaries while complete historical transition payloads are retrieved only through a single-event detail read.

This is discovery only. It does not freeze route shapes, exact summary DTO fields, event-detail union shapes or implementation details.

## Agreed API direction

Collection reads:

```text
GET /api/v1/core/lifecycle-events
GET /api/v1/core/objects/{object_id}/lifecycle-events
```

are candidates to return bounded event summaries rather than complete event payloads.

A separate single-event detail read is the candidate surface for one complete historical transition:

```text
GET /api/v1/core/lifecycle-events/{event_id}
```

The exact route and DTO remain deferred to per-API design.

## Operation-specific payload principle

M4 has ratified:

```text
lifecycle payload
    = complete exact semantic transition owned by the operation

not automatically
    = complete aggregate before + after snapshots
```

Consequently `before_state` / `after_state`, where retained as persistence carriers, may contain different semantic shapes for different event kinds.

Ratified Object examples:

```text
RENAME
    before  = { canonical_name: old_name }
    after   = { canonical_name: new_name }

DATA_CHANGE
    exact binding context = (template_id, template_version)
    changed properties only
    property identity = (declaring_template_id, property_name)
    each before/after = canonical value | ABSENT

SCHEMA_CHANGE
    exact binding transition = (template_id, source_version, target_version)
    changed runtime properties only
    property identity = (declaring_template_id, property_name)
    each before/after = canonical value | ABSENT
    no complete intrinsic Object snapshot
    no duplicated materialized slot/ownership state
```

A complete Object snapshot is not required for these operations because unrelated Object state is outside their mutation responsibility.

CREATE/DELETE may legitimately require broader historical state because a resource enters or leaves current existence.

## Current persistence behavior

The delivered lifecycle persistence uses a shared row shape and the current collection path can select/deserialize complete event rows, including historical JSONB carriers.

When an event kind carries property transition state, this can be materially larger than the metadata needed to render a collection page.

A summary collection should not transfer or decode those payloads merely because they are stored in the same persistence row.

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

with family-inapplicable fields remaining NULL where the shared-table design keeps them so.

Do not select in the collection path:

```text
before_state
after_state
```

The exact final summary field set is deferred until lifecycle public routes are designed in detail.

## Single-event detail path

The single-event detail read is the candidate path that loads the complete row, including historical transition carriers where they apply, and decodes the complete **kind-specific** historical event payload.

The detail decoder must dispatch by event kind rather than assuming all intrinsic Object events contain the same complete Object snapshot shape.

Conceptually:

```text
RENAME
    -> old/new canonical_name transition

DATA_CHANGE
    -> exact changed-property delta
    -> exact ObjectTemplate binding context
    -> value-vs-ABSENT semantics

SCHEMA_CHANGE
    -> exact source/target ObjectTemplate binding transition
    -> exact changed-property delta
    -> value-vs-ABSENT semantics
    -> binding transition retained even when property delta is empty

CREATE / DELETE
    -> broader snapshot carrier where their final contracts require it
```

Ownership history remains represented by dedicated ATTACH/DETACH events rather than being embedded into intrinsic event payloads.

## DATA_CHANGE detail data consequence

The ratified DATA_CHANGE history does not require reading or decoding a complete historical Object property map merely because the Object may contain many properties.

A DATA_CHANGE detail payload scales with the number and size of properties that actually changed in that event:

```text
K_changed = number of changed semantic properties in the event

historical transition payload
    -> O(K_changed + changed value size)

not automatically
    -> O(total Object property count)
```

The exact persistence representation is still open. If the shared lifecycle row keeps JSONB transition carriers, those carriers must encode the exact binding and semantic property deltas without requiring reconstruction from current ObjectTemplate state during lifecycle reads.

Therefore a lifecycle detail read for DATA_CHANGE should not need:

```text
current ObjectTemplate reads
DataType reads
semantic cache
current Object properties
```

The event itself must persist enough historical semantic identity/value context to decode the transition independently of later current-state/model changes.

## SCHEMA_CHANGE detail data consequence

SCHEMA_CHANGE likewise does not require a complete historical intrinsic Object snapshot.

Its persisted detail scales with:

```text
constant exact binding-transition context
+
K_changed schema-migration property transitions
+
changed value size
```

rather than automatically with the complete Object property count.

Conceptually:

```text
historical transition payload
    -> O(1 + K_changed + changed value size)
```

The event must persist:

```text
template_id
source_version
target_version
changed property semantic identities
before/after canonical value | ABSENT
```

so lifecycle readback does not need current model-plane state merely to understand which exact schema endpoints governed the transition or which semantic properties changed.

The materialized `object_component_slots` delta is intentionally not copied into the lifecycle payload. The exact immutable SOURCE/TARGET bindings are the historical schema context; successful SCHEMA_CHANGE does not mutate ownership membership.

A detail read therefore should not need:

```text
current ObjectTemplate effective-schema reads
current object_component_slots
current object_components
current Object properties
semantic caches
```

solely to decode the persisted event.

## Decoder separation

The collection path should not invoke complete historical-payload decoders.

Candidate separation:

```text
LifecycleEventSummary
    -> metadata-only row decoder / projection

LifecycleEventDetail
    -> common metadata
    -> kind-dispatched transition decoder
```

This avoids decoding data that the public collection does not expose and avoids one artificially universal intrinsic snapshot type.

## Global lifecycle collection

For:

```text
GET /api/v1/core/lifecycle-events
```

the target remains one database statement.

No cache is needed.

No join is required solely to populate summary display names when historical identity/display metadata is already persisted on the event row.

Therefore:

```text
DB round trips
    current: 1
    target:  1

DB payload
    current: complete event rows
    target:  summary projection only

historical transition JSONB decoding
    current: potentially every collection item
    target:  none in collection path
```

## Object-scoped lifecycle collection

For:

```text
GET /api/v1/core/objects/{object_id}/lifecycle-events
```

preserve the single-statement framing that distinguishes:

```text
Object absent
    -> 404

Object exists, no matching events
    -> empty page

Object exists, matching events
    -> paginated summary page
```

The M4 change is that the event-page projection carries summary columns only rather than complete historical transition payloads.

## First-phase conclusion

Lifecycle collection optimization is not merely an HTTP serialization change.

The target data path should avoid reading and decoding complete historical transition carriers when the caller requested only a paginated collection. Full kind-specific payload belongs to single-event detail.

The event-detail payload itself follows the semantic responsibility of the owning operation; it is not automatically a complete aggregate snapshot.

For DATA_CHANGE, the detail payload is bounded by the actually changed property delta and contains sufficient historical binding/property semantic identity to avoid current model-plane lookups during readback.

For SCHEMA_CHANGE, the detail payload is the exact binding transition plus the actually changed runtime-property delta; it does not require full intrinsic snapshots or duplicated slot/ownership state.

Locking, persistence carrier finalization and concurrency realization remain deferred to their owning later phases.
