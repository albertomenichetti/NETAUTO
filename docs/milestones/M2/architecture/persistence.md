# M2 Persistence Architecture

**Status:** FINAL / FROZEN

**Authority:** NORMATIVE M2 ARCHITECTURE — FINAL / FROZEN

## Authority and boundary

This document owns the M2 persistence delta over the delivered PostgreSQL architecture for:

```text
relational authorities and exact identities
PK / UNIQUE / CHECK / FK / CASCADE / RESTRICT
canonical JSONB current and historical state
aggregate mutation and coherent-read persistence pipelines
lifecycle codec and complete event-set persistence
permanent indexes and access paths
first durable Alembic root baseline
transaction lock planning and deadlock-safety constraints
```

Implementation authority, once the complete M2 architecture set is frozen, is:

```text
docs/architecture/persistence.md
+ docs/architecture/concurrency.md
+ docs/milestones/M2/contract.md
+ relationship.md
+ api.md
+ this document
```

This document does not redefine domain or wire semantics. Pairwise interleavings belong to `concurrency-matrix.md`; concrete SQLAlchemy lock helpers, retry policy and deterministic PostgreSQL realization belong to `concurrency.md`; evidence belongs to `verification.md`.

---

## 1. Governing persistence model

PostgreSQL remains the only persistence backend. One semantic mutation owns one write Unit of Work, one connection and one database transaction. Stores never commit independently or open nested semantic transactions.

M2 preserves four rules:

```text
one authority per state element
exact persisted version-sensitive references
declarative local integrity in PostgreSQL
semantic interpretation in domain/application/concurrency
```

The model correspondence is:

```text
ObjectTemplate                <-> RelationshipDefinition
ObjectTemplateVersion         <-> RelationshipDefinitionVersion
Object                        <-> factual Relationship
```

Equivalent problems reuse the delivered solution unless the Relationship domain has a material difference.

---

## 2. Fifteen authoritative tables

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

Intentionally absent:

```text
runtime Relationship property EAV
Relationship property-value rows
Relationship effective-schema cache
compiled generic schema
reverse-dependency materialization
version provenance / derived_from
surrogate RDV, declaration or runtime-resolution IDs
separate Relationship lifecycle timeline
event-set grouping identity
```

---

## 3. Authority map and schema

### 3.1 Stable Definition and Resolution

`relationship_definitions` owns:

```text
id UUID PRIMARY KEY
symmetric BOOLEAN NOT NULL
default_version INTEGER NULL
```

`default_version` is positive or null. The composite FK:

```text
(id, default_version)
    -> relationship_definition_versions(
           relationship_definition_id,
           version
       )
    ON DELETE RESTRICT
```

protects exact same-Definition existence. PUBLISHED-only default validity remains a UoW/concurrency invariant.

`relationship_resolutions` remains authoritative for stable identity, Definition membership, endpoint ObjectTemplate lineages and mutable non-key `name`. It remains an owned Definition child with `ON DELETE CASCADE`; endpoint lineage references remain `RESTRICT`.

### 3.2 Exact RelationshipDefinitionVersion

```text
relationship_definition_versions
    relationship_definition_id UUID NOT NULL
    version                    INTEGER NOT NULL
    revision                   INTEGER NOT NULL
    status                     TEXT NOT NULL
```

```text
PRIMARY KEY (relationship_definition_id, version)
CHECK version > 0
CHECK revision > 0
CHECK status IN ('DRAFT', 'PUBLISHED', 'DEPRECATED')
relationship_definition_id -> relationship_definitions.id ON DELETE CASCADE
```

There is no surrogate version ID, topology copy, default flag or provenance column.

### 3.3 Exact property declarations

```text
relationship_definition_properties
    relationship_definition_id       UUID NOT NULL
    relationship_definition_version  INTEGER NOT NULL
    name                             TEXT NOT NULL
    position                         INTEGER NOT NULL
    datatype_id                      UUID NOT NULL
    datatype_version                 INTEGER NOT NULL
    value_mode                       TEXT NOT NULL
```

```text
PRIMARY KEY (
    relationship_definition_id,
    relationship_definition_version,
    name
)

UNIQUE (
    relationship_definition_id,
    relationship_definition_version,
    position
)

CHECK name ~ '^[a-z][a-z0-9_]{0,63}$'
CHECK position > 0
CHECK datatype_version > 0
CHECK value_mode IN ('SCALAR', 'LIST')

(relationship_definition_id, relationship_definition_version)
    -> relationship_definition_versions(relationship_definition_id, version)
    ON DELETE CASCADE

(datatype_id, datatype_version)
    -> datatype_versions(datatype_id, version)
    ON DELETE RESTRICT
```

The row has no `required`, `nullable`, create default, migration default or surrogate identity. Physical identity is version-local; historical semantic continuity remains `(relationship_definition_id, name)`.

### 3.4 Factual Relationship

```text
relationships
    id                               UUID NOT NULL PRIMARY KEY
    relationship_definition_id       UUID NOT NULL
    relationship_definition_version  INTEGER NOT NULL
    properties                       JSONB NOT NULL
```

```text
UNIQUE (id, relationship_definition_id)
CHECK relationship_definition_version > 0
CHECK jsonb_typeof(properties) = 'object'

(relationship_definition_id, relationship_definition_version)
    -> relationship_definition_versions(relationship_definition_id, version)
    ON DELETE RESTRICT
```

`properties` has no server default. Every INSERT explicitly supplies `{}` or a non-empty canonical object. The composite exact-RDV FK replaces the delivered direct Definition FK; Definition lifetime remains protected through RDV ownership.

### 3.5 Runtime closure

`runtime_relationship_resolutions` remains structurally unchanged and owns only:

```text
relationship_id
relationship_definition_id
resolution_id
from_object_id
to_object_id
```

```text
PRIMARY KEY (resolution_id, from_object_id, to_object_id)

(relationship_id, relationship_definition_id)
    -> relationships(id, relationship_definition_id)
    ON DELETE CASCADE

(resolution_id, relationship_definition_id)
    -> relationship_resolutions(id, relationship_definition_id)
    ON DELETE RESTRICT

from_object_id -> objects.id ON DELETE RESTRICT
to_object_id   -> objects.id ON DELETE RESTRICT
```

Exact RDV pin and properties are never duplicated onto runtime rows.

### 3.6 Lifecycle history

`object_lifecycle_events` remains the sole Object-relative historical authority. Add:

```text
RELATIONSHIP_DATA_CHANGE
RELATIONSHIP_SCHEMA_CHANGE
```

All four Relationship kinds require destination, Relationship and Definition metadata, forbid ownership-slot fields, and use:

```text
RELATIONSHIP_CREATED
    before_state NULL
    after_state  NOT NULL

RELATIONSHIP_DATA_CHANGE
RELATIONSHIP_SCHEMA_CHANGE
    before_state NOT NULL
    after_state  NOT NULL

RELATIONSHIP_DELETED
    before_state NOT NULL
    after_state  NULL
```

Non-null state must be a JSON object. History has no live FK to current resources.

---

## 4. Enforcement and ownership

PostgreSQL protects exact/local identity, positive values, closed vocabularies, identifier grammar, exact references, reference lifetime, owned-child cleanup, JSONB top-level shape, lifecycle nullability and exact runtime-view uniqueness.

Domain/application/concurrency protect lifecycle admission, generation freshness, default validity, active dependency graph, historical evolution, canonical PrimitiveType values, SCALAR/LIST shape, absence of JSON null, complete factual state, complete closure, semantic factual uniqueness and coherent event metadata.

A SQL-shaped but semantically invalid persisted aggregate is corruption and maps to `internal_error`; no read or mutation repairs it.

Owned trees are exactly:

```text
RelationshipDefinition
    -> RelationshipResolution
    -> RelationshipDefinitionVersion
        -> RelationshipDefinitionProperty

Relationship
    -> RuntimeRelationshipResolution
```

`CASCADE` is restricted to those trees. No cascade removes factual Relationships, endpoint Objects, DTVs, endpoint ObjectTemplates or history.

Every persisted declaration protects exact DTV lifetime. Only a PUBLISHED consumer blocks DTV deprecation. Every current Relationship protects exact RDV and Definition lifetime but does not block RDV deprecation.

Whole-Definition delete clears the internal default pointer inside the same locked UoW before root deletion. Any later failure rolls the clear back.

---

## 5. Persistence boundaries and isolation

Conceptual store ownership is:

```text
RelationshipDefinitionStore
    stable header + complete Resolution aggregate + topology reads

RelationshipDefinitionVersionStore
    exact version headers + declarations + history/dependency reads

RuntimeRelationshipStore
    factual header + exact pin + properties + complete closure

LifecycleStore
    every lifecycle family + shared codecs + batch writer + reads
```

All use the caller-owned connection and transaction.

Mutation isolation remains `READ COMMITTED`. Every wait is followed by a fresh read and complete revalidation. Collision restart creates a new whole UoW; no repository fragment retries with stale assumptions.

Multi-statement coherent reads use `REPEATABLE READ READ ONLY`; single-statement reads use ordinary statement snapshots.

---

## 6. Canonical transaction lock plan

Every write UoW follows:

```text
1. non-locking discovery sufficient to build the candidate lock set
2. complete advisory-gate and row-lock plan
3. coalesce repeated row intents to one sufficient initial mode
4. acquire at most one advisory gate
5. acquire every row in canonical order
6. re-read all mutable state after waits
7. rederive/revalidate the semantic candidate
8. deterministic current-state DML
9. complete append-only lifecycle batch
10. commit or complete rollback
```

If the post-lock read reveals a required row absent from the optimistic plan, the UoW rolls back and restarts. It never appends a lower-order lock. Normal lock upgrades are forbidden; the first lock on a row is already sufficient.

### 6.1 Advisory gates

All gates are transaction-scoped and acquired before row locks. One operation acquires at most one:

```text
OWNERSHIP_GRAPH_WRITE_GATE
RELATIONSHIP_DEFINITION_CONFLICT_GATE
MODEL_ROOT_DELETE_GATE
```

`MODEL_ROOT_DELETE_GATE` serializes whole DataType, ObjectTemplate and RelationshipDefinition deletes. It prevents reciprocal incoming-FK delete cycles, including mutually targeting ObjectTemplate components, without changing public semantics.

### 6.2 Row order

```text
10  ObjectTemplate stable headers and exact versions
20  DataType stable headers and exact versions
30  RelationshipDefinition stable headers and exact versions
40  Object rows
50  factual Relationship rows
```

Within one versioned aggregate, header precedes exact versions and versions ascend. ObjectTemplate rows additionally order ancestor lineage before descendant lineage, then lineage UUID, header/version and version number. Invalid ancestry aborts before DML. Object and Relationship rows order by UUID.

This order is persistence-oriented: parent ObjectTemplate lifetime must precede a mutable child-version owner; DTV reverse-consumer checks remain non-locking, so DTV rows can safely follow ObjectTemplate rows and precede RDV consumers.

### 6.3 Minimum modes

```text
lifetime only                         -> FOR KEY SHARE
new/rebound exact PUBLISHED admission -> FOR SHARE + PUBLISHED recheck
non-key current owner mutation        -> FOR NO KEY UPDATE
delete / key change / root delete     -> FOR UPDATE
```

Every exact-version mutation also plans the stable owning header. A target FK stored on an existing owner row is locked before that owner, including ObjectTemplate parent rebind, Object SCHEMA_CHANGE and Relationship SCHEMA_CHANGE.

Every inserted/reinserted FK target is explicitly stabilized before referencing DML. A pure reference removal takes no outgoing target lock.

CREATE_NEXT cloned pins use `FOR KEY SHARE`: cloning is not new PUBLISHED admission, but it is a new physical lifetime reference.

### 6.4 Minimum lock registry

| Mutation family | Gate | Pre-DML row order |
|---|---|---|
| model whole-root delete | MODEL_ROOT_DELETE | root UPDATE |
| ObjectTemplate CREATE/REVISE/PUBLISH | none | OT parent/targets + own rows; then DTV targets |
| RD CREATE | DEFINITION_CONFLICT | endpoint OTs; DTV targets |
| RD RENAME | DEFINITION_CONFLICT | Definition header KEY SHARE |
| RDV CREATE_NEXT/REVISE/PUBLISH | none | DTV targets; Definition header; exact RDV |
| Object CREATE/SCHEMA_CHANGE | none | OTV header/version; Object owner when existing |
| Ownership ATTACH | OWNERSHIP_GRAPH_WRITE | parent/child Objects in UUID order |
| Relationship CREATE | none | Definition/RDV; endpoint Objects in UUID order |
| Relationship SCHEMA_CHANGE | none | Definition/target RDV; Relationship owner |
| same-owner data mutation/delete | none | exact Object or Relationship owner |

Additional rows required by a candidate are inserted into the same plan before acquisition.

---

## 7. Differential declaration replacement

REVISE remains complete semantic replacement, but blind physical `delete-all + reinsert-all` is forbidden for ObjectTemplate and RDV declaration sets.

The store must:

```text
load current complete set
resolve desired complete set
classify unchanged / removed / physically replaced / new
include every inserted/reinserted target in the lock plan
leave unchanged rows untouched
delete removed/replaced rows in deterministic PK order
insert replaced/new rows in deterministic PK order
update revision only after the complete child set is written
commit atomically
```

Any persisted field change, including `position`, makes a row physically replaced. Deleting all replaced rows before insertion permits position swaps without transient UNIQUE violation.

New/rebound lifecycle-sensitive targets use SHARE; same exact target reinserted only because another field changed uses KEY SHARE.

This closes the parent-delete/child-reinsert cycle while preserving complete-replacement semantics.

---

## 8. Deterministic write ordering

```text
version declarations
    -> physical PK / member name

RelationshipDefinition Resolutions
    -> Resolution UUID

runtime Relationship closure
    -> (resolution_id, from_object_id, to_object_id)

Relationship lifecycle views
    -> (object_id, destination_object_id, relationship_name)
```

No aggregate candidate uses row-by-row `ON CONFLICT DO NOTHING`. A collision aborts the whole UoW.

---

## 9. Model-plane pipelines

### Definition CREATE

```text
DEFINITION_CONFLICT gate
-> fresh topology certification
-> OT endpoint and DTV target locks in canonical order
-> fresh dependency/topology recheck
-> Definition + complete Resolutions + RDV v1 DRAFT + declarations
-> commit
```

### Definition RENAME

```text
DEFINITION_CONFLICT gate
-> Definition KEY SHARE lifetime hold
-> fresh complete aggregate/certified-set read
-> complete deterministic Resolution-name update
-> commit
```

KEY SHARE blocks root delete while remaining compatible with Relationship CREATE and non-key header operations.

### RDV CREATE_NEXT

Optimistically read the immutable source, plan cloned DTV lifetimes, acquire them, then acquire the Definition version-set owner. Reload source/version set; if the target set changed, restart. Insert one DRAFT revision 1 and cloned declarations atomically.

### RDV REVISE

Acquire desired DTV targets, Definition lifetime and exact DRAFT owner; reload DRAFT and `expected_revision`; validate history; apply differential replacement; increment revision once; commit.

### RDV PUBLISH

Acquire every direct DTV dependency SHARE before the Definition and DRAFT owner rows; reload generation/dependency set; recheck PUBLISHED; activate the version and establish a missing default in one UoW.

### Default/deprecate/delete-DRAFT

Header always precedes exact version. SET_DEFAULT holds target SHARE; DEPRECATE holds header SHARE and version NO KEY UPDATE; DELETE_DRAFT holds header/version-set owner and exact version UPDATE, then cascades declarations. Pure removal takes no DTV lock.

### Whole Definition DELETE

```text
MODEL_ROOT_DELETE gate
-> Definition UPDATE
-> complete aggregate/blocker read
-> transactional default clear
-> root delete + owned CASCADE
-> external RESTRICT arbitration
-> commit or full rollback
```

The same gate/order discipline applies to whole DataType and ObjectTemplate deletion.

---

## 10. Factual pipelines

### Relationship CREATE

```text
selected Resolution discovery
-> Definition lifetime/default lock
-> exact RDV SHARE
-> endpoint Objects KEY SHARE in UUID order
-> fresh Definition/default/RDV/endpoint reload
-> canonical property validation
-> complete closure derivation in PK order
-> factual conflict precheck
-> header + complete closure
-> one coherent metadata projection
-> complete CREATED event batch
-> commit
```

Explicit selection uses Definition KEY SHARE; implicit selection uses Definition SHARE. Endpoint KEY SHARE is compatible with Object non-key mutation and blocks Object delete. Definition RENAME uses a compatible KEY SHARE hold, so CREATE preserves the AS-IS progress contract and observes one coherent old/new name generation.

Exact-view PK remains final factual arbitration. A collision rolls back the candidate and restarts the complete CREATE in a new UoW; current winner produces `relationship_fact_conflict`, while a disappeared winner permits a fresh candidate.

### DATA_CHANGE

Relationship NO KEY UPDATE owner, fresh aggregate validation, complete candidate derivation, no-op short circuit, whole JSONB replacement, coherent metadata projection, complete DATA_CHANGE event batch, commit. Pin and closure remain unchanged.

### SCHEMA_CHANGE

Optimistically identify the stable Definition, then acquire Definition KEY SHARE and target RDV SHARE before Relationship NO KEY UPDATE. Reload source state and require same-Definition forward target; derive preserve-or-fail properties; update pin and properties in one row operation; keep closure unchanged; append complete event set.

Target-before-owner ordering prevents Definition delete from holding the model root while waiting on the same factual row.

### DELETE

Relationship UPDATE owner; absent means not found. Validate/capture current state and metadata, delete header, cascade complete closure, append complete DELETED event batch, commit. A waiter observes absence and emits no second event.

Object SCHEMA_CHANGE uses the equivalent target-OTV-before-Object-owner order. Object/Relationship DATA_CHANGE and rename-style state changes require only their current owner.

---

## 11. Persisted aggregate and coherent reads

A current Relationship is valid only when:

```text
Definition and same-Definition exact RDV exist
pinned status is PUBLISHED or DEPRECATED, never DRAFT
declarations and exact DTV pins are well formed
properties are canonical under the exact RDV
runtime rows belong to the same aggregate and Definition
endpoint Objects and lineage admission are valid
runtime rows equal the deterministic complete closure
public semantic views are exactly deduplicated
```

Corruption is `internal_error`, never caller validation or remediation.

`Relationship.GET` uses one read-only repeatable snapshot to load header, stable Definition/Resolutions, exact RDV/declarations/DTVs, closure and endpoint lineage state.

Object-relative pages verify the path Object, load `limit + 1` deduplicated views, batch-load every represented aggregate and fail the whole page on one corrupt fact. Ordering/cursor remain `(relationship_id, destination_object_id, name)`; mutable pin/properties never enter cursor identity.

Definition reads return stable aggregate plus default. Exact RDV reads return declarations by position. Version lists return summaries by version. Capability uses `EXISTS` for a PUBLISHED RDV and exposes default separately without multiplying rows.

Lifecycle pages rigorously decode every selected row; one corrupt row fails the whole page.

---

## 12. Lifecycle codec and writer

Introduce one shared `LifecycleStore` boundary over the same mutation UoW. Current-state stores no longer own separate lifecycle SQL.

Canonical Relationship factual state is exactly:

```json
{
  "relationship_definition_version": 3,
  "properties": {}
}
```

The historical decoder is self-contained: exact keys, positive non-boolean version, property-name grammar and canonical JSON carrier shape are validated without current model lookup. Current-state semantic validation remains against live exact RDV/DTV data.

Transition invariants:

```text
CREATED        before null, after factual
DATA_CHANGE    before/after factual, same version, different properties
SCHEMA_CHANGE  before/after factual, forward version
DELETED        before factual, after null
```

The metadata projection is one SQL statement joining closure, Resolution names and endpoint Object names. Structural keys are checked against the validated closure; semantic views are deduplicated and deterministically ordered.

`insert_relationship_event_set` validates the complete non-empty unique view set and performs one batch INSERT. Event rows use DB-generated identity and transaction timestamp. No `event_set_id`, live FK or `ON CONFLICT` behavior exists.

---

## 13. Permanent indexes

Constraint-owned indexes are not duplicated.

New/changed indexes:

```text
ix_relationship_definition_versions_status_definition_version
    (status, relationship_definition_id, version)

ix_relationship_definition_properties_datatype_version
    (datatype_id, datatype_version)

ix_relationship_definition_properties_semantic_history
    (relationship_definition_id, name,
     relationship_definition_version DESC)

ix_relationship_resolutions_definition_id
    (relationship_definition_id, id)

ix_relationship_resolutions_name_id
    (name, id)

ix_relationships_definition_version
    (relationship_definition_id, relationship_definition_version)

ix_runtime_resolutions_from_object_page
    (from_object_id, relationship_id, to_object_id, resolution_id)
    INCLUDE (relationship_definition_id)

ix_runtime_resolutions_to_object_relationship
    (to_object_id, relationship_id)

ix_runtime_resolutions_relationship
    (relationship_id)
```

Cross-domain hardening:

```text
(status, datatype_id, version)
(status, template_id, version)
(template_id, name, template_version DESC) for OT properties/components
```

Lifecycle keeps occurred/object/kind indexes and uses partial non-null indexes for destination Object, Relationship, Definition and relationship name, each followed by `(occurred_at, id)`.

Explicitly absent:

```text
GIN/expression indexes on runtime properties or snapshots
standalone default_version index
duplicate PUBLISHED-only partial index
second factual-identity index
event-set grouping index
```

A typed property-search contract must precede any property-value index.

---

## 14. First durable Alembic baseline

M2 replaces disposable development revisions with one self-contained root revision and one head. It creates the final fifteen-table schema directly, including final constraints, lifecycle vocabulary, indexes, partial predicates and INCLUDE columns.

There is no M1 backfill, in-place upgrade or `stamp` support. Pre-baseline databases are recreated.

Supported transitions:

```text
empty database -> head
head -> base
base -> head -> base -> head
```

Downgrade removes all and only NETAUTO-owned structures. SQLAlchemy metadata and live PostgreSQL must have zero drift. The migration runs offline against an empty database, transactionally, and imports no mutable application metadata.

---

## 15. Transaction validity and deadlock proof

The design preserves:

```text
one mutation / one UoW
READ COMMITTED writes
fresh post-wait revalidation
exact admission through commit
complete state/children/events atomicity
fresh whole-UoW collision restart
REPEATABLE READ read-only coherent projections
FK/PK/UNIQUE final arbitration
```

### 15.1 Existing-owner FK rebind

Target aggregate precedes the mutable child owner. Therefore a rebind cannot hold the child while waiting on a target delete that waits back on that child.

### 15.2 Child-table FK writes

Inserted/reinserted targets are held before child DML; unchanged rows remain untouched; pure removals do not wait on targets. Parent-delete/child-reinsert cycles are excluded.

### 15.3 Multi-resource rows

The complete plan uses one class/intra-class order and no lock upgrade. Overlapping plans meet on the first incompatible common row in the same order.

### 15.4 Model root deletes

`MODEL_ROOT_DELETE_GATE` allows only one model root delete to execute incoming-FK checks/cascades. Reciprocal model references cannot produce delete/delete cycles. Reference creators/rebinders hold the target before the child; removers never wait back on it.

### 15.5 Active dependencies

Publisher locks dependency before activation. Dependency deprecation owns the dependency and reverse-scans consumers without row locks. No dependency/consumer inversion exists.

### 15.6 Unique arbitration

Closure rows use exact-PK insertion order. Competing candidates cannot hold common unique keys in opposite order; loser rollback is complete.

### 15.7 Gates and lifecycle

Every gate precedes rows and each operation takes at most one. A gate waiter holds no row. Lifecycle rows have no live FKs and are appended last, so they cannot close a current-state cycle.

### 15.8 Result

The supported wait-for graph is acyclic by construction under the mandatory complete-plan rules.

PostgreSQL deadlock detection is only a safety net. SQLSTATE `40P01` in a supported deterministic scenario is an architecture/implementation defect, rolls back the whole UoW and is never hidden by store-fragment retry. Any optional whole-UoW retry belongs to `concurrency.md`; correctness may not depend on repeated victim selection.

---

## 16. Required AS-IS hardening

The first durable baseline must also harden delivered paths without public semantic change:

```text
complete pre-DML lock planner
advisory gate before rows
MODEL_ROOT_DELETE_GATE
stable header in every exact-version mutation
parent/model target before existing owner-row FK rebind
differential ObjectTemplate declaration replacement
lifetime holds for CREATE_NEXT cloned pins
gate-first Definition RENAME with header KEY SHARE
gate-first ownership edge addition
endpoint Object holds before Relationship closure insertion
deterministic declaration/closure/event order
non-locking dependency reverse scans
whole-UoW restart for stale lock plans
```

These preserve intended progress, notably Relationship CREATE during Object or Definition rename.

---

## 17. Failure and verification obligations

Known constraint races are translated only after complete rollback:

```text
exact-view collision -> fresh Relationship CREATE re-evaluation
missing FK target    -> referenced not found / defined conflict
root RESTRICT        -> delete_blocked
unexpected mismatch  -> internal_error
```

No SQL, table, column, constraint or stack detail crosses the public boundary.

Deterministic real-PostgreSQL evidence must cover:

```text
existing-owner rebind vs target root delete, both orders
new multi-target reference vs target delete, both orders
mutually referencing ObjectTemplate root deletes
declaration replacement vs DTV/OT delete
CREATE_NEXT clone vs target delete
Relationship CREATE vs both endpoint deletes
Relationship CREATE vs Definition delete
Definition RENAME and Object RENAME progress
ownership gate-before-row behavior
sorted overlapping closure collision
publisher/deprecator rendezvous
root delete vs internal mutation
same-owner factual serialization
all atomic state/event rollback paths
```

Tests assert semantic outcomes and absence of `40P01`; timeouts are hang guards, never scheduling mechanisms. Stress testing is supplementary and every discovered cycle must become a deterministic registered scenario.

---

## 18. WIP-extraction technical closure

The complete WIP extraction audit identified several implementation-significant details that were previously compressed in this owner. They are normative below.

### 18.1 Uniform defensive validation of default pointers

Every stable `DataType`, `ObjectTemplate` and `RelationshipDefinition` GET/list projection that observes a non-null `default_version` must validate, in the same coherent read snapshot, that the exact same-lineage target exists and is `PUBLISHED`.

```text
valid non-null default
    -> exact same-lineage PUBLISHED version

missing, cross-lineage, DRAFT or DEPRECATED target
    -> persisted invariant corruption
    -> internal_error
    -> no fallback, repair or pointer clearing
```

This is cross-domain read hardening only. Mutation and concurrency remain the primary invariant-preservation authority.

### 18.2 Final index replacement, FK-support and plan contract

Constraint-owned PK/UNIQUE indexes are not duplicated. The fresh durable schema contains the final explicit indexes in §13 and does not contain the superseded development structures:

```text
ix_relationships_definition
ix_runtime_resolutions_from_object
ix_runtime_resolutions_to_object
```

Their final replacements are:

```text
ix_relationships_definition_version
ix_runtime_resolutions_from_object_page
ix_runtime_resolutions_to_object_relationship
```

Nullable lifecycle selector indexes for destination Object, Relationship, Definition and relationship name are partial with the exact predicate `WHERE <selector> IS NOT NULL`. The global occurred, object and kind indexes remain non-partial.

Referencing-side FK support is closed as follows:

| Reference | Referencing-side authority |
|---|---|
| RDV -> Definition | RDV PK prefix `(relationship_definition_id, version)` |
| RD property -> RDV | property PK / position-UNIQUE prefix |
| RD property -> DTV | `ix_relationship_definition_properties_datatype_version` |
| Definition default -> RDV | one Definition row selected by Definition PK |
| Relationship -> exact RDV | `ix_relationships_definition_version` |
| runtime row -> Relationship | `ix_runtime_resolutions_relationship` |
| runtime row -> Resolution | runtime PK prefix `(resolution_id, ...)` |
| runtime row -> from Object | `ix_runtime_resolutions_from_object_page` |
| runtime row -> to Object | `ix_runtime_resolutions_to_object_relationship` |
| Resolution -> Definition | `ix_relationship_resolutions_definition_id` |

Representative PostgreSQL plan evidence may force sequential scans off only to prove eligibility of an approved index. It must not freeze cost values, row estimates or one exact plan tree.

### 18.3 Durable-root DDL realization

The first durable graph contains exactly one root revision, no predecessor and one head. The disposable development revision files are absent from the shipped graph.

Dependency-safe creation order is:

```text
1. object_lifecycle_events historical authority
2. stable roots: datatypes, object_templates, relationship_definitions
3. exact versions: datatype_versions, object_template_versions,
   relationship_definition_versions
4. the three optional cyclic default-version FKs
5. declarations/topology children
6. factual roots: objects, relationships
7. owned current-state children
8. explicit non-constraint indexes
```

Equivalent ordering is permitted only when it preserves the same dependency and cyclic-FK guarantees.

The root revision:

```text
is self-contained
uses explicit stable constraint/index names
imports no mutable application metadata or domain code
uses no IF EXISTS / IF NOT EXISTS to conceal drift
performs no stamp, legacy backfill or runtime schema repair
executes transactionally under PostgreSQL
```

Failure leaves the database at base with no committed partial NETAUTO schema. A corrected upgrade can rerun from base. `head -> base` removes all and only NETAUTO-owned structures and preserves unrelated sentinel objects.

### 18.4 Shared historical runtime-property carrier codec

Object and Relationship lifecycle snapshots share one historical runtime-property carrier validator. It validates self-contained JSON carrier integrity without current model lookup.

```text
allowed scalar carrier
    string | integer | boolean

forbidden
    null | float | object | nested list

LIST
    non-empty
    ordered
    homogeneous carrier kind
```

Relationship factual snapshots additionally require exact keys:

```text
relationship_definition_version
properties
```

The version is a positive non-boolean integer and property names satisfy the canonical identifier grammar. Historical decoding never infers a PrimitiveType from a string and never consults a live RDV/DTV. The fresh baseline admits only canonical M2 event shapes; no permanent legacy dual decoder exists.

### 18.5 Superseded migration bridge

Any earlier WIP requirement for synthetic M1 data or event backfill is cancelled by the first durable baseline. It is not an omitted implementation task.

```text
pre-baseline databases
    -> recreate
    -> upgrade empty database to the single head

M2-created data
    -> follows native v1 DRAFT/default-null semantics
```

No contract reopening is required by this extraction closure.

---

## 19. Traceability and closure

Primary ownership:

```text
M2-OUT-03  exact typed factual Relationship state
M2-OUT-07  complete Relationship lifecycle observability
M2-OUT-09  first durable relational kernel baseline
```

The document supplies physical authority for `M2-OUT-02`, `04`, `06`, `08`, `10` and `16`, and for the corresponding Relationship, concurrency, schema and regression acceptance criteria.

Architecture-draft closure:

```text
fifteen-table authority and exact references      CLOSED
constraints, ownership and delete actions         CLOSED
current/historical JSONB boundary                  CLOSED
mutation/read persistence pipelines               CLOSED
lifecycle codec and event writer                   CLOSED
index inventory                                    CLOSED
first durable Alembic baseline                     CLOSED
transaction validity cross-check                   PASS
deadlock wait-graph cross-check                    PASS
required AS-IS physical hardening                  CLOSED
```

Pairwise concurrency, PostgreSQL realization, installed migration/head discovery, evidence design, traceability and consistency closure have passed. This document is `FINAL / FROZEN`. Any semantic or technical change requires formal architecture reopening and a renewed cross-document consistency review.
