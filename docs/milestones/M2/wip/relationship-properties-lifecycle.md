# M2 WIP — Relationship Properties Lifecycle Persistence

**Status:** LIFECYCLE CODEC AND EVENT-SET PERSISTENCE DESIGN CLOSED

**Authority:** DISCOVERY CAPTURE — NON-NORMATIVE

This document is the lifecycle-persistence addendum to:

```text
docs/milestones/M2/wip/relationship-properties.md
docs/milestones/M2/wip/relationship-properties-persistence.md
```

It closes the persistence-design item previously described as:

```text
lifecycle codec/decoder and complete event-set persistence realization
```

It does not yet close index realization, Alembic migration, semantic concurrency, PostgreSQL lock/gate realization, verification registries or normative propagation.

---

## 1. Governing decision

M2 retains one Object-relative lifecycle authority:

```text
object_lifecycle_events
```

Relationship lifecycle transitions remain part of the unified Object lifecycle stream and continue to fan out one record per distinct Object-relative semantic view.

No separate Relationship timeline, Relationship lifecycle table, Relationship-specific snapshot columns or generic event payload authority is introduced.

The canonical model is:

```text
current Relationship fact
    -> relationships + runtime_relationship_resolutions

historical Object-relative observation
    -> object_lifecycle_events
```

The complete event set is committed in the same Unit of Work as the owning factual mutation.

---

## 2. Persistence-boundary ownership

The lifecycle table is shared by intrinsic Object, ownership and Relationship event families. The persistence boundary should therefore be explicit and shared rather than split between `ObjectStore` and `RuntimeRelationshipStore`.

Introduce a dedicated conceptual module:

```text
src/netauto/persistence/lifecycle.py
```

It owns:

```text
EventKind
lifecycle read models
snapshot codecs
row decoder
LifecycleStore
    insert_intrinsic_event
    insert_ownership_event
    insert_relationship_event_set
    list_events
```

`ObjectService` and `RelationshipService` invoke `LifecycleStore` using the same connection already owned by their semantic Unit of Work.

Current-state stores remain focused on their aggregate authority:

```text
ObjectStore
    -> Object and ownership current state

RuntimeRelationshipStore
    -> factual Relationship header and runtime-resolution closure

LifecycleStore
    -> append-only historical event rows and lifecycle reads
```

This is a responsibility refactoring, not a new transaction boundary or public API.

---

## 3. Relationship factual historical state

Introduce one immutable conceptual value object:

```text
RelationshipFactualState
    relationship_definition_version: positive integer
    properties: canonical runtime property map
```

Canonical JSONB representation:

```json
{
  "relationship_definition_version": 3,
  "properties": {
    "weight": 10
  }
}
```

The snapshot contains only mutable factual state.

It intentionally excludes:

```text
relationship_id
relationship_definition_id
RelationshipResolution IDs
Object-relative views
relationship names
Object canonical names
property-schema declarations
DataTypeVersion metadata
```

Those values are either top-level typed event metadata or current model-plane data and must not be duplicated as a second historical authority.

The encoder must create an independent snapshot value; no historical event may retain a mutable alias to the runtime candidate map.

---

## 4. Historical snapshot validation boundary

Current Relationship state is validated against the live exact RDV and its exact DataTypeVersion dependencies.

Historical lifecycle state is intentionally self-contained and must remain decodable after deletion of:

```text
Relationship
RelationshipDefinition
RelationshipDefinitionVersion
DataTypeVersion
endpoint Object
```

Therefore the historical decoder performs no model-plane lookup.

It validates the exact snapshot carrier:

```text
exact keys:
    relationship_definition_version
    properties

relationship_definition_version:
    integer
    > 0
    bool forbidden

properties:
    JSON object
    property names use [a-z][a-z0-9_]{0,63}
```

Generic canonical runtime-value carrier rules are also enforced:

```text
allowed scalar carriers:
    string
    integer
    boolean

forbidden:
    JSON null
    float
    nested JSON object
    nested list

LIST:
    non-empty
    ordered
    every member is an allowed scalar carrier
    members use one homogeneous JSON carrier kind
```

The decoder does not attempt to infer whether a historical string represented `core.string`, `core.number`, `core.date`, `core.datetime`, `core.ip` or `core.ip_prefix`. That interpretation belongs to the exact historical schema at mutation time and cannot safely depend on current live rows.

A snapshot that violates these carrier rules is persisted invariant corruption.

---

## 5. Shared runtime-property snapshot codec

The generic runtime-property carrier validation should be factored into one helper reused by Object and Relationship lifecycle snapshots.

Conceptual API:

```text
encode_runtime_property_snapshot(properties)
decode_runtime_property_snapshot(raw)
```

Object and Relationship snapshot decoders then add their family-specific exact fields around the same validated property map.

This prevents the Relationship lifecycle codec from becoming stricter or semantically different from the equivalent Object lifecycle codec.

The helper validates historical carrier integrity only. It does not replace current-state validation against exact declarations and DataType constraints.

---

## 6. Event kind vocabulary and transition invariants

The lifecycle vocabulary includes:

```text
RELATIONSHIP_CREATED
RELATIONSHIP_DATA_CHANGE
RELATIONSHIP_SCHEMA_CHANGE
RELATIONSHIP_DELETED
```

One persistence read model may represent the family:

```text
RelationshipLifecycleEvent
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
    before: RelationshipFactualState | null
    after: RelationshipFactualState | null
```

The decoder enforces:

```text
RELATIONSHIP_CREATED
    before = null
    after != null

RELATIONSHIP_DATA_CHANGE
    before != null
    after != null
    before.relationship_definition_version
        == after.relationship_definition_version
    before.properties != after.properties

RELATIONSHIP_SCHEMA_CHANGE
    before != null
    after != null
    after.relationship_definition_version
        > before.relationship_definition_version
    before.properties may equal after.properties

RELATIONSHIP_DELETED
    before != null
    after = null
```

A persisted no-op `RELATIONSHIP_DATA_CHANGE` is invalid even though the command-level no-op itself remains a successful request with no event.

A non-forward persisted `RELATIONSHIP_SCHEMA_CHANGE` is invalid.

---

## 7. Coherent Object-relative metadata projection

Relationship event metadata contains mutable historical observations:

```text
Object canonical names
RelationshipResolution navigation names
```

The event writer must not combine names loaded by independent statements from incompatible committed generations.

Use one projection query that returns the raw current closure enriched with metadata:

```text
resolution_id
from_object_id
from_canonical_name
to_object_id
to_canonical_name
relationship_name
```

Writer pipeline:

```text
1. validate the factual structural closure
2. execute one metadata projection statement
3. compare projected structural keys:
       resolution_id
       from_object_id
       to_object_id
   with the validated closure
4. deduplicate semantic views
5. use the same projection result for:
       lifecycle fan-out
       mutation response views[]
```

The projection statement is authoritative for metadata observed by that transition. The writer does not compare projected names with potentially stale names loaded earlier from another statement.

A concurrent rename may therefore produce a complete all-old or complete all-new committed metadata observation, but never an incoherent half-set.

---

## 8. Semantic-view deduplication and fan-out cardinality

Raw runtime-resolution rows are not event rows.

The structural closure remains validated using exact keys:

```text
(resolution_id, from_object_id, to_object_id)
```

Relationship lifecycle fan-out is deduplicated by the public Object-relative semantic view:

```text
(object_id, destination_object_id, relationship_name)
```

The resulting view set must be:

```text
non-empty
unique
deterministically ordered
```

Expected consequences remain aligned with M1:

```text
non-symmetric ordinary fact
    -> two semantic event views

symmetric A != B
    -> normally two semantic event views

symmetric self-loop
    -> one semantic event view

inheritance overlap
    -> several runtime rows may still collapse
       to two semantic event views
```

Persistence normalization must never leak as duplicate public lifecycle events.

---

## 9. Complete event-set insertion

`LifecycleStore.insert_relationship_event_set` receives one complete, already-derived transition:

```text
kind
relationship_id
relationship_definition_id
ordered distinct views
before factual state
or null
after factual state
or null
```

Before writing it validates:

```text
kind belongs to the Relationship family
before/after transition shape is coherent
view set is non-empty
view semantic keys are unique
all rows share identical factual before/after states
all rows share the same Relationship identity
```

The writer then:

```text
1. builds all event rows
2. performs one batch INSERT
3. relies on PostgreSQL defaults for id and occurred_at
4. uses no ON CONFLICT behavior
5. treats every insert failure as failure of the whole Unit of Work
```

No compensating write, partial-success result or post-commit repair exists.

Atomic outcomes:

```text
success
    -> factual mutation committed
    -> complete event set committed

failure
    -> factual state unchanged
    -> runtime closure unchanged
    -> no event row from the failed transition committed
```

---

## 10. Event identity, ordering and grouping

Each event row retains:

```text
id
    -> PostgreSQL-generated UUID row identity

occurred_at
    -> transaction_timestamp()
```

Public ordering remains:

```text
(occurred_at, id) DESC
```

All event rows produced by one Unit of Work share the same transaction timestamp.

Do not introduce:

```text
event_set_id
transition_id
expected_event_count
```

There is no public grouping API or query that consumes such an identity. An extra ID would not by itself prove fan-out completeness and would introduce a new technical concept without a semantic read path.

A complete event set may be split across lifecycle pages. Atomic write completeness is not a pagination grouping guarantee.

---

## 11. Mutation integration

### 11.1 Relationship CREATE

```text
insert factual header
insert complete runtime closure
project complete semantic views
after = initial factual state
insert RELATIONSHIP_CREATED event set
commit
```

```text
before = null
after = {
    selected exact RDV version,
    canonical initial properties
}
```

### 11.2 Relationship DATA_CHANGE

```text
lock/load current fact
capture current factual state
derive complete canonical candidate
```

No-op:

```text
candidate == current
    -> no UPDATE
    -> no event
```

Real change:

```text
replace complete properties snapshot
insert RELATIONSHIP_DATA_CHANGE event set
commit
```

Every event row receives the same before and after factual snapshots.

### 11.3 Relationship SCHEMA_CHANGE

```text
lock/load source fact
capture source factual state
derive target factual state
atomically update exact RDV pin + properties
insert RELATIONSHIP_SCHEMA_CHANGE event set
commit
```

The event is emitted even when source and target property maps are equal because the exact version pin changes.

### 11.4 Relationship DELETE

```text
lock/load current fact
capture final factual state
project metadata before physical delete
delete header + cascade closure
insert RELATIONSHIP_DELETED event set
commit
```

A second exact-ID delete returns `resource_not_found` and produces no second event set.

---

## 12. PostgreSQL checks

Extend the closed event-kind vocabulary with:

```text
RELATIONSHIP_DATA_CHANGE
RELATIONSHIP_SCHEMA_CHANGE
```

The lifecycle family-shape check requires, for all four Relationship kinds:

```text
destination_object_id              IS NOT NULL
destination_canonical_name         IS NOT NULL
relationship_id                    IS NOT NULL
relationship_definition_id         IS NOT NULL
relationship_name                  IS NOT NULL
slot_declaring_template_id         IS NULL
slot_name                          IS NULL
```

State-shape check:

```text
RELATIONSHIP_CREATED
    before_state IS NULL
    after_state IS NOT NULL

RELATIONSHIP_DATA_CHANGE
RELATIONSHIP_SCHEMA_CHANGE
    before_state IS NOT NULL
    after_state IS NOT NULL

RELATIONSHIP_DELETED
    before_state IS NOT NULL
    after_state IS NULL
```

Generic JSON checks remain:

```text
before_state IS NULL
OR jsonb_typeof(before_state) = 'object'

after_state IS NULL
OR jsonb_typeof(after_state) = 'object'
```

SQL does not inspect JSON-embedded property names, value carriers or version ordering. Those guarantees belong to the rigorous persistence decoder.

---

## 13. Public lifecycle DTO union

Introduce:

```text
RelationshipFactualStateDto
    relationship_definition_version
    properties
```

Use exact discriminated response DTOs:

```text
RelationshipCreatedLifecycleEventDto
    kind = RELATIONSHIP_CREATED
    before: null
    after: RelationshipFactualStateDto

RelationshipChangedLifecycleEventDto
    kind = RELATIONSHIP_DATA_CHANGE
         | RELATIONSHIP_SCHEMA_CHANGE
    before: RelationshipFactualStateDto
    after: RelationshipFactualStateDto

RelationshipDeletedLifecycleEventDto
    kind = RELATIONSHIP_DELETED
    before: RelationshipFactualStateDto
    after: null
```

All retain the existing top-level historical metadata:

```text
id
occurred_at
object_id
canonical_name
destination_object_id
destination_canonical_name
relationship_id
relationship_definition_id
relationship_name
```

Do not expose:

```text
RelationshipResolution ID
source/target terminology
complete views[]
property declarations
live model references
```

This mirrors the existing Object CREATED/CHANGED/DELETED DTO separation and keeps nullability exact.

---

## 14. Lifecycle reads and corruption behavior

`LifecycleStore.list_events` retains the existing filters and ordering.

It decodes every selected row rigorously before a page is returned.

```text
all rows valid
    -> canonical discriminated page

one row invalid
    -> RuntimeError at persistence boundary
    -> public internal_error
    -> no partial page
```

The Object-specific lifecycle route should use one coherent read for:

```text
path-target Object existence check
+
selected lifecycle page
```

The global lifecycle route uses one event query and requires no additional current-state join or remediation.

Lifecycle history remains readable after deletion of current resources through global filters. The Object-specific route continues to return path-target not found when the current Object no longer exists.

---

## 15. M1 event compatibility and migration requirement

M1 Relationship events persist no factual snapshot. M2 does not retain a permanent dual decoder.

The migration must backfill every historical M1 Relationship event:

```text
RELATIONSHIP_CREATED
    before_state = null
    after_state = {
        "relationship_definition_version": 1,
        "properties": {}
    }

RELATIONSHIP_DELETED
    before_state = {
        "relationship_definition_version": 1,
        "properties": {}
    }
    after_state = null
```

This applies even when the referenced current RelationshipDefinition or Relationship no longer exists. Historical snapshots have no live FK and describe the M1 contract materialized as M2 version `1` with an empty property state.

After migration:

```text
M2 decoder accepts only canonical M2 event shapes
M2 application refuses to run against the pre-M2 schema
```

No long-lived compatibility branch accepts Relationship event rows with both snapshots null.

---

## 16. Verification obligations

The future verification plan must cover:

```text
pure snapshot codec
    exact keys
    positive version
    generic property carriers
    rejected null/float/object/nested/list-empty values

transition decoder
    all four Relationship kinds
    no-op DATA_CHANGE rejected
    non-forward SCHEMA_CHANGE rejected

PostgreSQL checks
    event vocabulary
    family shape
    state nullability
    DB-generated IDs
    shared transaction timestamp

fan-out
    non-symmetric
    symmetric
    self-loop
    inheritance-overlap deduplication

atomic rollback
    CREATE event failure
    DATA_CHANGE event failure
    SCHEMA_CHANGE event failure
    DELETE event failure

metadata coherence
    concurrent Object rename
    concurrent Resolution rename
    complete all-old/all-new observation

API
    exact discriminated shapes
    new kinds accepted by filters
    cursor and ordering unchanged

migration
    every M1 Relationship event backfilled
    every migrated row decodable by the M2-only codec
```

Existing M1 tests for fan-out deduplication, shared transaction timestamp, metadata races, corrupt snapshot detection and CREATE/DELETE rollback are baseline scenarios to extend rather than replace.

---

## 17. Closed decisions and remaining persistence work

Closed by this addendum:

```text
lifecycle persistence module ownership
Relationship factual snapshot value object
snapshot encoding and rigorous structural decoding
shared Object/Relationship property carrier codec
Relationship transition decoder
coherent metadata projection
semantic-view deduplication
complete event-set batch insertion
atomic rollback policy
event identity and ordering
no event_set_id
four-mutation integration
PostgreSQL lifecycle CHECK boundary
public discriminated DTO union
corrupt-page behavior
M1 event backfill target shape
verification obligations
```

Remaining persistence-design work:

```text
1. exact index inventory justified by concrete paths
2. lossless Alembic migration M1 -> M2
3. persistence consistency closure
4. handoff to semantic concurrency design
```
