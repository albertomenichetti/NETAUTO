# M2 WIP — Relationship Properties Persistence Design

**Status:** PERSISTENCE DESIGN IN PROGRESS — STRUCTURE, MUTATION PIPELINES AND READ COHERENCE CLOSED

**Authority:** DISCOVERY CAPTURE — NON-NORMATIVE

This document captures the persistence-design decisions completed after the API/semantic closure in:

```text
docs/milestones/M2/wip/relationship-properties.md
```

It is an execution aid under `wip/`. It does not replace the current delivered AS-IS, the M2 contract, the normative architecture owners, the semantic concurrency matrix, the PostgreSQL realization document, the migration authority or the verification registries.

The following are intentionally **not yet closed** here:

```text
lifecycle codec implementation details beyond the approved canonical shape
index/read-path realization
Alembic migration M1 -> M2
complete semantic concurrency matrix update
PostgreSQL lock/gate realization
verification scenario registry and implementation plan
final normative-document propagation
```

---

## 1. Governing persistence correspondence

The persistence design follows the same semantic correspondence already approved for the API/domain model:

```text
MODEL PLANE

ObjectTemplate
    <-> RelationshipDefinition

ObjectTemplateVersion
    <-> RelationshipDefinitionVersion

RUNTIME / DATA PLANE

Object
    <-> Relationship
```

Equivalent persistence problems reuse the M1 solution already adopted for `ObjectTemplateVersion` or `Object` unless the Relationship domain has a genuine structural difference.

The material differences are:

- `RelationshipDefinition` owns stable topology/navigation state rather than inheritance, components or abstractness;
- a `RelationshipDefinitionVersion` contains only the exact property-schema snapshot and has no effective-schema or inheritance layer;
- all M2 Relationship properties are optional and non-nullable;
- factual Relationship identity is a unique semantic fact represented through one deterministic runtime-resolution closure;
- Relationship lifecycle records are object-relative projections in the existing Object lifecycle authority.

---

## 2. Persistence authority map

Each concept has exactly one current-state authority.

### 2.1 Stable RelationshipDefinition authority

`relationship_definitions` is authoritative for:

```text
id
symmetric
default_version
```

`default_version` is stable-lineage policy state. It is not copied onto Resolution rows and it does not float into current factual Relationships.

### 2.2 Stable RelationshipResolution authority

`relationship_resolutions` remains authoritative for:

```text
id
relationship_definition_id
from_template_id
to_template_id
name
```

Resolution identity, membership, endpoint lineages and navigation names remain stable Definition-level state. They are not copied into each exact RelationshipDefinitionVersion.

### 2.3 Exact RelationshipDefinitionVersion authority

`relationship_definition_versions` is authoritative for:

```text
relationship_definition_id
version
revision
status
```

Exact identity is:

```text
(relationship_definition_id, version)
```

There is no surrogate version UUID.

### 2.4 Exact property-declaration authority

`relationship_definition_properties` is authoritative for one local declaration in one exact RelationshipDefinitionVersion:

```text
relationship_definition_id
relationship_definition_version
name
position
datatype_id
datatype_version
value_mode
```

Physical declaration identity is version-local:

```text
(
    relationship_definition_id,
    relationship_definition_version,
    name
)
```

Historical semantic continuity remains a domain rule:

```text
(relationship_definition_id, name)
```

The historical key is not a second physical row identity and does not require a surrogate property ID.

### 2.5 Factual Relationship authority

`relationships` is authoritative for:

```text
id
relationship_definition_id
relationship_definition_version
properties
```

The version field is an exact persisted schema pin. `properties` is the complete canonical current factual value state.

### 2.6 Runtime-resolution closure authority

`runtime_relationship_resolutions` remains authoritative only for the complete deterministic resolved-view closure:

```text
relationship_id
relationship_definition_id
resolution_id
from_object_id
to_object_id
```

It does not contain or duplicate:

```text
relationship_definition_version
properties
property values
```

Those values belong once to the factual Relationship header.

### 2.7 Lifecycle history authority

`object_lifecycle_events` remains the sole authority for Object-relative history, including Relationship events.

Relationship lifecycle records contain:

```text
object-relative semantic-view metadata
+
relationship factual before/after state
```

Historical snapshots are self-contained values, not live foreign-key references to current Relationship or model-plane rows.

---

## 3. Physical schema changes

### 3.1 New table: `relationship_definition_versions`

Conceptual shape:

```text
relationship_definition_versions
--------------------------------
relationship_definition_id    UUID
version                       INTEGER
revision                      INTEGER
status                        TEXT
```

Constraints:

```text
PRIMARY KEY (
    relationship_definition_id,
    version
)

version > 0
revision > 0
status IN ('DRAFT', 'PUBLISHED', 'DEPRECATED')
```

Ownership FK:

```text
relationship_definition_id
    -> relationship_definitions.id
    ON DELETE CASCADE
```

The table intentionally has no:

```text
surrogate id
symmetric
Resolution state
endpoint state
properties JSON
is_default flag
derived_from/source version
```

Topology belongs to the stable Definition; declarations are child rows; the default belongs to the Definition header; `CREATE_NEXT` does not persist provenance.

### 3.2 New table: `relationship_definition_properties`

Conceptual shape:

```text
relationship_definition_properties
----------------------------------
relationship_definition_id          UUID
relationship_definition_version     INTEGER
name                                TEXT
position                            INTEGER
datatype_id                         UUID
datatype_version                    INTEGER
value_mode                          TEXT
```

Primary key:

```text
PRIMARY KEY (
    relationship_definition_id,
    relationship_definition_version,
    name
)
```

Local constraints:

```text
name matches [a-z][a-z0-9_]*
name maximum length = 64
relationship_definition_version > 0
position > 0
datatype_version > 0
value_mode IN ('SCALAR', 'LIST')
```

Ordering uniqueness:

```text
UNIQUE (
    relationship_definition_id,
    relationship_definition_version,
    position
)
```

Owned-child FK:

```text
(
    relationship_definition_id,
    relationship_definition_version
)
    -> relationship_definition_versions(
           relationship_definition_id,
           version
       )
    ON DELETE CASCADE
```

Exact DataTypeVersion FK:

```text
(datatype_id, datatype_version)
    -> datatype_versions(datatype_id, version)
    ON DELETE RESTRICT
```

The table intentionally has no:

```text
required
migration_default
nullable
default_value
surrogate property id
```

All M2 Relationship properties are optional and non-nullable. No create or migration default exists.

### 3.3 Modified table: `relationship_definitions`

Add:

```text
default_version INTEGER NULL
```

Local constraint:

```text
default_version IS NULL
OR default_version > 0
```

Same-Definition exact FK:

```text
(id, default_version)
    -> relationship_definition_versions(
           relationship_definition_id,
           version
       )
    ON DELETE RESTRICT
```

The FK protects exact existence and same-Definition ownership. The stronger invariant:

```text
default_version is NULL or targets a PUBLISHED version
```

remains a Unit-of-Work/concurrency guarantee, not a cross-row SQL `CHECK` or trigger contract.

The `RESTRICT` protects an individual default-version delete. It does not turn the internal default pointer into a blocker of a semantically admitted root Definition delete, because the pointer-owning header and all owned versions disappear in the same root aggregate deletion.

### 3.4 Modified table: `relationships`

Conceptual M2 shape:

```text
relationships
-------------
id                                  UUID
relationship_definition_id          UUID
relationship_definition_version     INTEGER
properties                          JSONB
```

Constraints:

```text
PRIMARY KEY (id)
relationship_definition_version > 0
properties NOT NULL
jsonb_typeof(properties) = 'object'
```

The application must always materialize `properties` explicitly. There is no server default such as `DEFAULT '{}'::jsonb`; omission-to-`{}` is command semantics and a missing persistence value must not be hidden by the database.

Exact schema FK:

```text
(
    relationship_definition_id,
    relationship_definition_version
)
    -> relationship_definition_versions(
           relationship_definition_id,
           version
       )
    ON DELETE RESTRICT
```

This composite FK replaces the old direct `relationships.relationship_definition_id -> relationship_definitions.id` FK. It guarantees exact-version existence and same-Definition coherence; the target version itself belongs to the Definition.

Retain the technical uniqueness needed by runtime child FKs:

```text
UNIQUE (id, relationship_definition_id)
```

This is not a second factual business identity.

### 3.5 Structurally unchanged table: `runtime_relationship_resolutions`

The table remains:

```text
runtime_relationship_resolutions
--------------------------------
relationship_id
relationship_definition_id
resolution_id
from_object_id
to_object_id
```

Retain the exact resolved-view primary key:

```text
PRIMARY KEY (
    resolution_id,
    from_object_id,
    to_object_id
)
```

Retain the aggregate-membership FK:

```text
(
    relationship_id,
    relationship_definition_id
)
    -> relationships(
           id,
           relationship_definition_id
       )
    ON DELETE CASCADE
```

Retain Resolution/Definition coherence:

```text
(
    resolution_id,
    relationship_definition_id
)
    -> relationship_resolutions(
           id,
           relationship_definition_id
       )
    ON DELETE RESTRICT
```

Endpoint Object FKs remain `RESTRICT`.

No exact RDV pin or property state is duplicated onto runtime-resolution rows.

### 3.6 Modified lifecycle vocabulary and state use

Continue to use:

```text
object_lifecycle_events
```

Add kind values:

```text
RELATIONSHIP_DATA_CHANGE
RELATIONSHIP_SCHEMA_CHANGE
```

Continue to use the existing:

```text
before_state JSONB NULL
after_state  JSONB NULL
```

for factual Relationship snapshots. No Relationship-specific lifecycle table and no duplicate Relationship-specific before/after columns are introduced.

Canonical factual lifecycle snapshot:

```json
{
  "relationship_definition_version": 3,
  "properties": {
    "weight": 10
  }
}
```

Relationship event state shape:

```text
RELATIONSHIP_CREATED
    before_state = NULL
    after_state  = factual snapshot

RELATIONSHIP_DATA_CHANGE
    before_state = factual snapshot
    after_state  = factual snapshot

RELATIONSHIP_SCHEMA_CHANGE
    before_state = factual snapshot
    after_state  = factual snapshot

RELATIONSHIP_DELETED
    before_state = factual snapshot
    after_state  = NULL
```

All Relationship event kinds require the existing Object-relative metadata:

```text
destination_object_id              NOT NULL
destination_canonical_name         NOT NULL
relationship_id                    NOT NULL
relationship_definition_id         NOT NULL
relationship_name                  NOT NULL
slot_declaring_template_id         NULL
slot_name                          NULL
```

The family/state-shape SQL checks are extended accordingly. Existing generic checks continue to require that non-null `before_state` and `after_state` are JSON objects.

The exact snapshot key set, positive version, property-object shape and canonical domain meaning are validated by the persistence decoder. SQL does not duplicate the full kernel codec or compare JSON-embedded source/target versions.

Historical snapshots have no live FK to current RelationshipDefinitionVersion rows.

### 3.7 Authoritative table map

The M1 core has thirteen authoritative tables. M2 adds only:

```text
relationship_definition_versions
relationship_definition_properties
```

The resulting core map is:

```text
Model plane — 10
    datatypes
    datatype_versions
    object_templates
    object_template_versions
    object_template_properties
    object_template_components
    relationship_definitions
    relationship_resolutions
    relationship_definition_versions
    relationship_definition_properties

Data plane — 4
    objects
    object_components
    relationships
    runtime_relationship_resolutions

History — 1
    object_lifecycle_events
```

Total:

```text
15 authoritative tables
```

Intentionally absent:

```text
runtime Relationship property EAV
relationship_property_values
Relationship value child table
Relationship effective-schema cache
separate Relationship lifecycle table
surrogate RelationshipDefinitionVersion id
surrogate declaration id
surrogate runtime-resolution id
```

Current factual values remain one complete canonical `JSONB` snapshot on `relationships`, exactly as current Object values remain on `objects`.

---

## 4. Enforcement boundary

### 4.1 PostgreSQL responsibilities

PostgreSQL protects:

```text
primary/exact identity
positive version/revision/position values
closed status/value-mode vocabulary
identifier grammar
same-Definition composite references
exact DataTypeVersion references
reference lifetime
owned-child cleanup
JSONB top-level object shape
lifecycle family/state nullability
exact runtime-view uniqueness
```

### 4.2 Domain / Unit-of-Work responsibilities

Domain/application logic protects:

```text
DRAFT/PUBLISHED/DEPRECATED command admission
expected_revision freshness
PUBLISHED-only new binding admission
default target is PUBLISHED
active model graph
property historical evolution rules
allowed property names under the exact RDV
SCALAR/LIST runtime shape
non-null runtime values
PrimitiveType parsing/canonicalization
exact DataTypeVersion constraints
optional empty LIST -> absence
complete factual state validation
complete deterministic closure validation
semantic factual uniqueness
```

No trigger or complex JSONB `CHECK` becomes a second partial implementation of the kernel type system.

A locally well-shaped row that violates the exact model/runtime contract is persisted invariant corruption and maps to `internal_error`; it is not a supported legacy state and is not repaired implicitly.

### 4.3 Exact identity versus lifecycle status

Foreign keys guarantee that referenced exact versions exist and belong to the expected lineage/Definition. They do not guarantee that the target is currently `PUBLISHED`.

This distinction preserves historical bindings:

```text
Relationship pinned to a later-DEPRECATED RDV
    -> valid existing binding

RDV declaration pinned to a later-DEPRECATED DTV
    -> valid historical exact dependency
```

New binding, publication and deprecation races remain UoW/concurrency concerns.

---

## 5. Ownership and lifetime policy

### 5.1 RelationshipDefinition aggregate ownership

Owned tree:

```text
RelationshipDefinition
    ├── RelationshipResolution[]
    └── RelationshipDefinitionVersion[]
            └── RelationshipDefinitionProperty[]
```

Root Definition deletion, once semantically admitted, physically removes all owned state via `CASCADE`.

There is no cascade from Definition/RDV deletion to:

```text
factual Relationships
Objects
DataTypeVersions
ObjectTemplates
lifecycle history
```

Current factual Relationships are external references and block root Definition deletion. PostgreSQL `RESTRICT` remains the final authority against a concurrent new/current reference.

### 5.2 Individual RDV delete

Application admission:

```text
exact RDV exists
status = DRAFT
revision = expected_revision
```

Physical delete removes:

```text
exact RDV
+
complete owned declaration set
```

through `ON DELETE CASCADE` from version to declarations.

No external reference is removed implicitly. A Relationship or current default pointer into the RDV would be protected by `RESTRICT`; such a reference into a DRAFT should be impossible in a valid state and therefore indicates an admission/invariant defect.

### 5.3 DataTypeVersion lifetime versus active lifecycle

Every persisted RDV declaration, regardless of RDV status, is a lifetime reference to its exact DataTypeVersion:

```text
DRAFT declaration
PUBLISHED declaration
DEPRECATED declaration
    -> all block physical DataTypeVersion/DataType-lineage deletion
```

Only a `PUBLISHED` RDV is an active-model lifecycle consumer and blocks DataTypeVersion deprecation.

Therefore:

```text
exact DTV lifetime
    -> protected by every persisted declaration through FK RESTRICT

DTV active PUBLISHED status
    -> protected only by PUBLISHED RDV consumers through UoW/concurrency
```

Deleting the consumer RDV removes its declarations and may remove the lifetime blocker. Deprecating the consumer RDV preserves the declaration but removes its active-model blocker.

### 5.4 Exact RDV runtime lifetime versus deprecation

Every current factual Relationship is a lifetime reference to its exact RDV and indirectly to the Definition root.

It blocks:

```text
physical exact RDV deletion
RelationshipDefinition root deletion
```

It does not block:

```text
PUBLISHED -> DEPRECATED
```

A Relationship pinned to a DEPRECATED RDV remains valid, may execute `DATA_CHANGE` under that immutable schema and may use the RDV as the source of a forward `SCHEMA_CHANGE`.

`Relationship.SCHEMA_CHANGE` atomically transfers the live reference from source RDV to target RDV.

### 5.5 Factual Relationship aggregate ownership

Owned tree:

```text
Relationship
    └── RuntimeRelationshipResolution[]
```

Deleting the Relationship header cascades only to its runtime-resolution closure.

There is no cascade to:

```text
RelationshipDefinitionVersion
RelationshipDefinition
RelationshipResolution
endpoint Objects
DataTypeVersions
lifecycle history
```

A successful delete transaction produces exactly:

```text
Relationship absent
complete runtime closure absent
complete RELATIONSHIP_DELETED event set present
```

A failed transaction leaves all current state intact and emits no new event.

---

## 6. Transactional mutation pipelines

### 6.1 `Relationship.CREATE`

M2 combines the existing M1 factual/closure pipeline with the M1 Object exact-schema/property pipeline.

One semantic Unit of Work performs:

```text
1. load selected RelationshipResolution and complete stable Definition
2. validate the Definition/topology candidate
3. select explicit RDV or resolve Definition.default_version
4. require selected exact same-Definition RDV to remain PUBLISHED through commit
5. load endpoint Objects and validate lineage compatibility
6. derive the complete deterministic runtime-resolution closure
7. load exact RDV declarations and exact DataTypeVersion dependencies
8. validate/canonicalize the complete initial properties state
9. evaluate current factual uniqueness from stable Definition + endpoints/closure
10. if occupied, return relationship_fact_conflict without mutation
11. generate a new relationship_id
12. insert Relationship header with exact RDV pin and canonical properties
13. insert the complete runtime closure
14. derive the complete distinct Object-relative semantic-view set
15. insert all RELATIONSHIP_CREATED events
16. commit atomically
```

Properties and RDV version do not participate in factual uniqueness.

The current-state pre-check improves diagnostics but is not the final concurrency authority. Exact resolved-view uniqueness remains PostgreSQL arbitration.

On an insert collision:

```text
rollback the complete candidate Unit of Work
start a fresh Unit of Work
re-evaluate current state

winner fact still current
    -> 409 relationship_fact_conflict
    -> expose winner relationship_id in bounded details

winner fact removed before re-evaluation
    -> fact is free
    -> CREATE may attempt a new factual identity
```

M2 intentionally returns conflict rather than M1 convergence.

Forbidden partial strategies include:

```text
header without complete closure
partial closure
properties without exact RDV pin
partial lifecycle event set
row-by-row ON CONFLICT DO NOTHING
implicit mutation of an existing fact
successfully returning the existing fact
```

### 6.2 `Relationship.DATA_CHANGE`

Pipeline:

```text
1. lock/load exact relationship_id
2. absent -> 404 resource_not_found
3. load and validate current header, exact RDV, properties, stable Definition and complete closure
4. load exact declarations and DataTypeVersion dependencies
5. verify persisted properties are canonical under the pinned RDV
6. apply the non-empty SET/REMOVE operation set to the fresh complete state
7. derive and validate the complete canonical candidate
8. compare candidate with current properties
```

Semantic no-op:

```text
candidate == current
    -> success
    -> no UPDATE
    -> no lifecycle event
```

Real change:

```text
replace the complete relationships.properties snapshot atomically
preserve exact RDV pin
preserve complete runtime closure
insert one RELATIONSHIP_DATA_CHANGE event per distinct Object-relative view
commit atomically
```

The persistence authority does not implement independent per-key `jsonb_set`/delete operations. Semantic operations produce one complete validated snapshot, which replaces the current snapshot.

### 6.3 `Relationship.SCHEMA_CHANGE`

Pipeline:

```text
1. lock/load exact relationship_id
2. absent -> 404 resource_not_found
3. load/validate source header, exact RDV, source properties, stable Definition and complete closure
4. require source RDV to be PUBLISHED or DEPRECATED, never DRAFT
5. load source declarations and exact DTV dependencies
6. verify current source properties are canonical
7. require target_version > current_version
8. load exact same-Definition target RDV
9. missing target -> referenced_resource_not_found
10. target not PUBLISHED -> dependency_not_admissible
11. stabilize target PUBLISHED admission through commit
12. load target declarations and DTV dependencies
13. migrate directly source -> target using historical semantic keys
14. block on any incompatible current value with schema_change_blocked
15. derive complete canonical target properties
16. atomically update relationship_definition_version and properties on the same Relationship row
17. leave runtime-resolution closure unchanged
18. insert complete RELATIONSHIP_SCHEMA_CHANGE event set
19. commit atomically
```

Migration rules:

```text
continuous property + source value
    -> preserve
    -> apply only allowed SCALAR -> LIST widening
    -> validate/canonicalize under target exact DTV
    -> incompatibility blocks the complete operation

continuous/new target property without source value
    -> absent

source-only property
    -> removed

no migration default
no caller remediation payload
no extras/archive bucket
```

The exact pin and target properties are one atomic state transition. No committed state may combine the new version with old properties or the old version with new properties.

The runtime closure is not rewritten because RDV versioning concerns only the property schema; stable topology remains on the Definition.

A valid forward schema change always emits events even when source and target property maps are equal, because the exact RDV pin changes.

### 6.4 `Relationship.DELETE`

`Relationship.DELETE` follows the runtime semantics of `Object.DELETE`, not the M1 idempotent Relationship delete.

Pipeline:

```text
1. lock/load exact relationship_id
2. absent -> 404 resource_not_found; no event
3. validate header, exact RDV pin, canonical properties, stable Definition and complete closure
4. derive the complete distinct Object-relative view set
5. capture coherent historical names and the final factual before snapshot
6. delete the Relationship header
7. cascade-delete the complete runtime closure
8. insert one RELATIONSHIP_DELETED event per distinct view
9. commit atomically
```

Concurrent same-ID deletes:

```text
first transition
    -> delete + one complete event set

waiter after first commit
    -> exact ID absent
    -> 404 resource_not_found
    -> no duplicate event set
```

ABA safety is exact-ID based. A late `DELETE(X)` cannot delete a later semantically equivalent Relationship `Y` with another UUID.

---

## 7. Persisted aggregate integrity

A factual Relationship is valid only when every layer below is coherent.

### 7.1 Header

```text
relationship_definition_id identifies an existing stable Definition
relationship_definition_version identifies an existing same-Definition exact RDV
pinned RDV status is PUBLISHED or DEPRECATED, never DRAFT
properties is a canonical complete runtime state under that exact RDV
```

### 7.2 Exact property schema

```text
complete declaration set is well formed
names and positions are unique/valid
exact DataTypeVersion pins exist
no exact DTV dependency is DRAFT

PUBLISHED RDV
    -> all exact DTV dependencies are PUBLISHED

DEPRECATED RDV
    -> dependencies may be PUBLISHED or DEPRECATED
```

### 7.3 Runtime closure

Every runtime row must:

```text
belong to the same relationship_id and relationship_definition_id as the header
reference a Resolution owned by the same Definition
reference existing endpoint Objects
satisfy endpoint lineage compatibility
```

The full row set must:

```text
use one factual endpoint pair
be exactly the deterministic closure required by the stable Definition
contain no extra row
omit no required row
produce exactly the expected distinct public semantic-view set
```

### 7.4 Failure boundary

Caller candidate errors remain 400/422/409 according to the API contract.

Any already-persisted violation is:

```text
500 internal_error
```

The kernel does not:

```text
repair a partial closure
rebind to a current default
fall back to latest/highest
remove an unknown property
re-canonicalize and silently persist corrupted state
```

The complete integrity predicate is checked for at least:

```text
Relationship.GET
Relationship.DATA_CHANGE
Relationship.SCHEMA_CHANGE
Relationship.DELETE
fresh CREATE conflict re-evaluation
Object-relative Relationship page validation
```

---

## 8. Read and projection coherence

### 8.1 `Relationship.GET`

Use one read-only `REPEATABLE READ` coherent-read Unit of Work.

Load in the same snapshot:

```text
Relationship header
stable Definition + complete Resolution set
exact pinned RDV + complete declarations
exact DataTypeVersion dependencies
complete runtime-resolution closure
endpoint Object identities and template lineages
```

Outcomes:

```text
exact relationship_id absent in snapshot
    -> 404 resource_not_found

aggregate complete and valid
    -> canonical Relationship projection

header present but any dependency/closure state incoherent
    -> 500 internal_error
```

The read takes no mutation lock, consults no default/latest/highest selector and performs no remediation.

A concurrent mutation may be observed entirely before or after, never as a mixed state.

### 8.2 Object-relative Relationship collection

For:

```text
GET /api/v1/core/objects/{object_id}/relationships
```

use one coherent-read snapshot.

The persistence read joins current runtime views to the factual Relationship authority and produces:

```text
relationship_id
relationship_definition_id
relationship_definition_version
object_id
destination_object_id
name
properties
```

`relationship_definition_version` and `properties` come from `relationships`, not from runtime-resolution rows.

Distinct semantic-view identity and ordering remain M1:

```text
(relationship_id, destination_object_id, name) ASC
```

The keyset cursor contains only that ordering key. Mutable RDV pin/properties do not enter cursor identity and do not move an item through the collection.

Within the same snapshot:

```text
1. verify Object path-target existence
2. load limit + 1 distinct views
3. collect distinct relationship_id values
4. validate every represented factual aggregate completely
5. return a page only after all validations succeed
```

Batch loading is preferred to N+1, but the semantic guarantee is complete validation of every represented fact. One corrupt fact fails the complete page with `internal_error`; no partial page is returned.

### 8.3 Relationship capability collection

A public capability requires:

```text
topological applicability
+
at least one PUBLISHED RelationshipDefinitionVersion
```

Use an `EXISTS` predicate over `relationship_definition_versions`, not a direct join to every PUBLISHED version. A direct join would multiply one Resolution/capability by the number of published versions and break limit/cursor cardinality.

Conceptual predicate:

```sql
EXISTS (
    SELECT 1
    FROM relationship_definition_versions AS published_rdv
    WHERE published_rdv.relationship_definition_id = rd.id
      AND published_rdv.status = 'PUBLISHED'
)
```

Join the stable Definition to expose `default_version` and validate it defensively:

```text
default_version NULL
    -> valid if at least one PUBLISHED RDV exists
    -> implicit CREATE unavailable, explicit CREATE available

default_version non-NULL
    -> exact same-Definition target must exist and be PUBLISHED
    -> otherwise internal_error
```

Ordering/cursor remain:

```text
resolution_id ASC
cursor = last resolution_id
```

The capability query does not load full RDV schemas or lists of published versions.

### 8.4 Stable `RelationshipDefinition.GET` and list

Use a coherent-read snapshot to return:

```text
stable header
complete Resolution set
default_version
```

Do not inline versions or declarations.

A Definition is returned even when it currently has no PUBLISHED RDV; model-plane inventory is distinct from runtime capability availability.

If `default_version` is non-null, validate in the same snapshot that the exact target is PUBLISHED. A corrupt item fails the complete GET/page. Collection validation may be batched.

### 8.5 Exact `RelationshipDefinitionVersion.GET`

Use one coherent-read snapshot to load:

```text
exact RDV header
complete declaration set ordered by position
exact DataTypeVersion dependencies in batch
```

Validate:

```text
positive version/revision
closed status
well-formed declarations
exact DTV pins exist
no DTV dependency is DRAFT
PUBLISHED RDV -> every DTV dependency PUBLISHED
DRAFT/DEPRECATED RDV -> dependency may be PUBLISHED or DEPRECATED
```

No inheritance/effective-schema resolver is required. The exact RDV declaration set is already the complete schema.

Do not re-run full historical remove/re-add/evolution certification on each GET; history constraints are mutation/verification invariants.

### 8.6 RelationshipDefinitionVersion list

Pipeline:

```text
1. verify stable Definition path-target exists
2. query only version headers/summaries
3. optional status filter
4. ORDER BY version ASC
5. cursor based only on version
```

Summary shape:

```text
relationship_definition_id
version
revision
status
```

Do not load declarations, DataType dependencies or default policy. A summary endpoint is not a complete schema certification read.

### 8.7 Resolution rename visibility

Current runtime rows continue to store `resolution_id`, not duplicated Resolution names.

Current reads join `relationship_resolutions` and therefore observe the current navigation name.

Lifecycle events retain the historical `relationship_name` captured at event time and are never backfilled after a rename.

The complete Definition rename remains atomic. A coherent read observes the complete old name set or the complete new name set, never a partial mixture. No factual Relationship, RDV, property or runtime-resolution row is rewritten.

### 8.8 Model lifecycle/default changes versus current facts

The following model-plane mutations do not update current factual Relationship rows or closures:

```text
RDV.PUBLISH
RDV.DEPRECATE
RelationshipDefinition.SET_DEFAULT
RelationshipDefinition.CLEAR_DEFAULT
```

Current facts remain governed by their exact pins and do not depend on the current default.

Capability membership is derived from current model state:

```text
at least one PUBLISHED RDV
    -> capability eligible

zero PUBLISHED RDVs
    -> capability absent
```

A Definition with only DRAFT/DEPRECATED versions remains present in model-plane Definition reads.

No materialized `has_published_version` or `capability_enabled` authority is introduced.

### 8.9 Consistency across separate HTTP requests

Each individual read is snapshot-consistent. Separate requests have no shared repeatable snapshot.

No generic ETag/`If-Match`, cross-request transaction token or session snapshot is introduced.

Discovery reads do not reserve later admission. Mutations re-evaluate current predicates:

```text
CREATE
    -> selected/default RDV still PUBLISHED through commit

REVISE/PUBLISH/DELETE_DRAFT
    -> expected_revision still current

SCHEMA_CHANGE
    -> exact target still PUBLISHED through commit
```

A cursor is a keyset pagination token bound to route/order/filter identity, not a database snapshot or CDC token.

### 8.10 Atomic visibility of aggregate deletes

MVCC, single-transaction ownership cleanup and coherent reads guarantee:

```text
RelationshipDefinition root delete
    -> reader sees complete prior Definition/Resolution/RDV/declaration state
       or Definition absent

RDV DELETE_DRAFT
    -> reader sees complete RDV + declarations
       or exact RDV absent

Relationship DELETE
    -> reader sees complete header + closure
       or Relationship absent
```

Readers must never observe:

```text
Definition with a partially deleted Resolution set
RDV with a partially deleted declaration set
Relationship header without part of its closure
closure rows without their header
```

Lifecycle history is independent and is handled through its own canonical decoder and event-set atomicity.

---

## 9. Lifecycle event persistence decisions already closed

Relationship events continue to fan out one record per distinct Object-relative semantic view.

Canonical event factual state:

```text
before/after snapshot
    relationship_definition_version
    properties
```

Top-level event columns already carry:

```text
relationship_id
relationship_definition_id
object_id
canonical_name
destination_object_id
destination_canonical_name
relationship_name
```

Do not duplicate complete `views[]` inside each snapshot.

Event contracts:

```text
RELATIONSHIP_CREATED
    before = null
    after  = exact version + canonical initial properties

RELATIONSHIP_DATA_CHANGE
    before = same exact version + old properties
    after  = same exact version + new properties
    no semantic-no-op event

RELATIONSHIP_SCHEMA_CHANGE
    before = source version + source properties
    after  = target version + migrated properties
    always emitted for a valid forward version change

RELATIONSHIP_DELETED
    before = final exact version + final properties
    after  = null
```

Every complete event set commits atomically with its factual mutation. No separate Relationship timeline is introduced.

---

## 10. Cross-domain hardening finding

The new Relationship readers explicitly validate that a non-null `default_version` points to a `PUBLISHED` exact version.

The same domain invariant already exists for `DataType` and `ObjectTemplate`, but some current stable readers rely on mutation/concurrency correctness without rechecking the target status on ordinary reads.

M2 consistency sweep finding:

```text
apply the same defensive default-target PUBLISHED validation
uniformly to DataType, ObjectTemplate and RelationshipDefinition readers
```

This is a hardening consistency change, not a new public contract and not permission to remediate corrupt state. Any violated persisted default invariant remains `internal_error`.

---

## 11. Closed versus open persistence work

### Closed in this WIP

```text
authority map
new/modified table responsibility
primary and composite key model
local CHECK/UNIQUE/FK boundary
JSONB factual-state model
no runtime property EAV
ownership and CASCADE/RESTRICT policy
exact DTV/RDV lifetime semantics
CREATE transactional pipeline
DATA_CHANGE transactional pipeline
SCHEMA_CHANGE transactional pipeline
DELETE transactional pipeline
persisted aggregate integrity predicate
Relationship GET coherent read
Object-relative Relationship collection coherence
relationship-capabilities EXISTS read path
stable Definition read coherence
exact RDV read coherence
RDV summary collection behavior
Resolution rename visibility
model lifecycle/default effect on current facts
cross-request consistency boundary
atomic delete visibility
lifecycle table reuse and canonical snapshot shape
```

### Still open before persistence design is complete

```text
7. lifecycle codec/decoder and complete event-set persistence realization
8. exact index inventory justified by concrete read/write paths
9. lossless Alembic migration M1 -> M2, including event backfill and downgrade policy
10. persistence consistency closure and handoff to semantic concurrency design
```

After persistence closure, the next major design phases are:

```text
semantic concurrency census and complete pairwise matrix update
PostgreSQL lock/advisory-gate/retry realization
verification scenario and deterministic concurrency registry
normative architecture propagation
implementation sequencing in steps.md
```
