# M4 WIP — Working-set navigation index

**Status:** ACTIVE NAVIGATION MAP / M4 WIP / ALWAYS NON-NORMATIVE

## Purpose

This file maps the current M4 working set and the progress of the ongoing review.

Everything under `wip/` remains globally non-normative. `CLOSED`, `FROZEN`, `REVIEWED BASELINE` or similar wording in this directory is only an M4 discovery/review checkpoint and never authorizes implementation by itself.

Navigation role and review state are separate dimensions:

```text
SPINE
    first place to read for current working direction

ACTIVE INPUT
    distributed current discovery not yet consolidated/closed

SUPPORT / HANDOFF
    reusable cross-domain or later-architecture input

SOURCE MATERIAL
    evidence/traceability behind a current owner; not standalone authority

REVIEWED BASELINE
    relevant current owner/support has passed the present review/revalidation
    and may be reused as baseline input for later review steps

ACTIVE REVIEW FRONTIER
    topic currently being revalidated; legacy/open assumptions may still exist
```

`SPINE` answers **where to read**. `REVIEWED BASELINE` / `ACTIVE REVIEW FRONTIER` answers **how far review has progressed**.

The classification in this index is the current navigation/review-state classification. Some owner headers retain wording describing the phase in which the file originated; such header wording does not override the current classification recorded here.

## External interpretation anchors

Read these before interpreting M4 WIP:

- [`AGENTS.md`](../../../../AGENTS.md)
- [`README.md`](../../../../README.md)
- [`docs/general/linee_guida_progetto.md`](../../../general/linee_guida_progetto.md)
- [`docs/milestones/M4/status.md`](../status.md)
- [`docs/architecture/README.md`](../../../architecture/README.md)

Until M4 explicitly freezes/promotes a TO-BE delta, delivered architecture remains the normative AS-IS baseline.

# 1. Current review-state snapshot

## REVIEWED BASELINE

```text
general-domain-principles.md
version-allocation.md

object.md
object-revision.md
object-components-persistence.md

relationship.md
relationshipdefinition.md
```

## REVIEWED BASELINE SUPPORT

```text
object-template-ancestry-cache.md
```

The route-level Object sweep is complete and consolidated in `object.md`, with cross-operation Object generation/component persistence responsibilities remaining in their dedicated reviewed owners.

The factual Relationship sweep is also complete at the discovery/revalidation level and has been losslessly consolidated back into the single owner:

```text
relationship.md
```

The temporary Relationship continuation files were merged back and removed. `relationship.md` contains the ordered post-definition checkpoints through `C-REL-36`, including global/Object-scoped reads, CREATE, DATA_CHANGE, SCHEMA_CHANGE and DELETE.

RelationshipDefinition has likewise completed its REST, technical and bidirectional consistency sweep in `relationshipdefinition.md`; its former intent, distributed discovery and temporary ledger files were absorbed and removed.

`REVIEWED BASELINE` remains a WIP review state only. Object and factual Relationship still contain architecture-closing handoffs; factual Relationship in particular still has the final CREATE Definition-selection request choice and global physical/cache/concurrency realization open.

## CONSISTENCY SWEEP — CLOSED FOR CURRENT REVIEWED BASELINE

A bidirectional consistency sweep has been completed across this index and every current reviewed owner/support listed above.

Checked boundaries include:

```text
version identity/allocation semantics
Object intrinsic revision and mutation freshness
Object component-slot materialization and ownership edge identity
ObjectTemplate stable ancestry cache semantics
factual Relationship root/runtime-cell ownership
factual Relationship revision and migration freshness
Object <-> factual Relationship lifetime composition
operation-owned lifecycle payload boundaries
no-diagnostic-only-work principle
route/cost/cache ownership boundaries
architecture handoffs vs already-ratified semantics
RelationshipDefinition stable topology / semantic-space ownership
RDV history, default-selection and DTV dependency boundaries
```

Current result:

```text
no unresolved semantic contradiction among reviewed owners
no missing reviewed owner from this index
no temporary consolidation file remains
```

Two explicit precedence rules are important when reading the historical sections retained inside `relationship.md`:

```text
C-REL-27
    supersedes earlier factual-root snapshots that predate relationships.revision

C-REL-35
    forbids factual self-reference
    and supersedes every earlier self-loop branch/example/cardinality
```

Therefore the current factual root is:

```text
relationships
    id
    relationship_definition_id
    relationship_definition_version
    properties
    revision
```

and current factual admission requires:

```text
from_object_id != to_object_id
```

Historical pre-supersession passages remain review history; they are not competing current candidates.

The shared version allocator has also been revalidated against identity allocation. Current versioned lineage IDs:

```text
DataType.id
ObjectTemplate.id
RelationshipDefinition.id
```

are kernel-generated UUIDv4 identities treated as belonging to one practical cross-family UUID namespace. Therefore the reviewed logical allocator remains:

```text
last_versions(id, last_version)
```

without a `resource_kind` discriminator. A future change to the UUID allocation invariant reopens that key shape.

# 2. Current review frontier

The RelationshipDefinition model-plane review is now complete at the same M4 discovery/revalidation level as Object and factual Relationship.

Current reviewed current-state families:

```text
Object
factual Relationship
RelationshipDefinition model plane
```

This promotion is a WIP reviewed-baseline state only. It does not mean that any of those families is architecturally closed or that implementation is authorized.

No next family is selected by this consolidation. The remaining model-plane families still classified as active input are:

```text
DataType
ObjectTemplate
```

Their relative review order must be selected explicitly rather than inferred here. Broader physical/concurrency architecture closure also remains pending and must not be treated as automatically started by the RelationshipDefinition promotion.

Lifecycle remains classified separately as historical/audit state rather than current authoritative Object/Relationship data-plane state. Its own family review remains open, but it must not be described as a remaining current-state data-plane gap.

A material future change must reopen only the reviewed dependencies it actually affects.

# 3. Current M4 spine

## Cross-cutting principles and method

### [`general-domain-principles.md`](general-domain-principles.md) — SPINE / REVIEWED BASELINE

Current owner for ratified general M4 principles, including:

```text
version number identifies exact version + allocation order only
validity of one exact version != cross-version migrability
REVISE/PUBLISH do not absorb future runtime-migration responsibility
lifecycle payload = complete operation-owned semantic transition
failure semantics/details derive from the efficient legal execution path
    -> no backend work solely for diagnostic enrichment
```

### [`version-allocation.md`](version-allocation.md) — SPINE / REVIEWED BASELINE

Current owner for shared monotonic/no-reuse version allocation and the logical:

```text
last_versions(id, last_version)
```

direction. The single `id` key relies on the reviewed cross-family UUIDv4 namespace invariant for versioned lineages.

### [`discovery.md`](discovery.md) — SPINE / discovery framing / NOT REVIEWED BASELINE

Initial M4 motivation, workload hypotheses and design exploration.

### [`top-down-api-closure-sweep.md`](top-down-api-closure-sweep.md) — SPINE / operating method / NOT REVIEWED BASELINE

Method used to close routes from public contract through data path, cache, semantic concurrency, persistence implications, cost and architecture handoff.

### [`milestone-relational-schema-closure-requirement.md`](milestone-relational-schema-closure-requirement.md) — SUPPORT / HANDOFF

Governance input requiring milestone closure to document the resulting relational schema; not a current DDL freeze.

# 4. Object current owners

### [`object.md`](object.md) — SPINE / REVIEWED BASELINE / Object family owner

Primary family owner for Object public surfaces and route-local navigation.

Current full-sweep checkpoints include:

```text
POST /objects
GET /objects
GET /objects/{id}
PUT /objects/{id}/canonical-name
POST /objects/{id}/properties
GET /objects/{id}/schema
POST /objects/{id}/schema
GET /objects/{parent}/components/{slot}
POST /objects/{parent}/components/{slot}/attach
POST /objects/{parent}/components/{slot}/detach
GET /objects/{child}/owner
DELETE /objects/{id}
```

Use `object.md` for route contracts/data paths/cost/concurrency/handoffs. Cross-operation responsibilities remain intentionally separate:

```text
object-revision.md
    -> intrinsic Object generation / expected_revision protocol

object-components-persistence.md
    -> current component-slot / ownership persistence boundary

object-template-ancestry-cache.md
    -> reusable stable ObjectTemplate ancestry/compatibility cache support
```

The Object family closure is dependency-aware. Material future changes to certified effective-property/effective-component semantics or stable ancestry trigger only the targeted revalidations recorded by the Object owner.

### [`object-revision.md`](object-revision.md) — SPINE / REVIEWED BASELINE

Owner for the universal intrinsic `objects.revision` generation/CAS protocol:

```text
CREATE -> revision = 1
prepared intrinsic mutation -> expected_revision
persisted intrinsic mutation -> revision + 1 atomically
stale generation -> no mutation/lifecycle + bounded retry
DELETE -> terminates current generation without surviving increment
revision scope excludes ownership/Relationship facts outside objects
```

### [`object-components-persistence.md`](object-components-persistence.md) — SPINE / REVIEWED BASELINE

Owner for current component/ownership persistence:

```text
object_component_slots
    object_id
    slot_declaring_template_id
    slot_name
    target_template_id

object_components
    child_object_id
    parent_object_id
    slot_declaring_template_id
    slot_name
```

It owns semantic slot identity, materialization invariant, edge -> current semantic-slot dependency, relational blocker arbitration and physical architecture handoff. Route-local semantics/cost remain owned by `object.md`.

### [`object-template-ancestry-cache.md`](object-template-ancestry-cache.md) — SUPPORT / REVIEWED BASELINE SUPPORT

Reusable stable ObjectTemplate lineage ancestry/compatibility cache backed by:

```text
object_template_ancestry
    descendant_template_id
    ancestor_template_id
    depth
```

A source becomes READY only after its complete stable ancestor/neighborship set, including self, is loaded. Exact physical/cache realization remains architecture work.

# 5. Model-plane families

DataType and ObjectTemplate remain non-normative active input. RelationshipDefinition has completed its consolidated review and now appears in this section as a reviewed family owner; no WIP promotion implies architecture freeze.

## DataType — ACTIVE INPUT

```text
datatype-create-next-discovery.md
datatype-delete-draft-discovery.md
datatype-delete-lineage-discovery.md
datatype-deprecate-discovery.md
datatype-get-lineage-discovery.md
datatype-get-version-discovery.md
datatype-list-lineages-discovery.md
datatype-list-versions-discovery.md
datatype-revise-discovery.md
datatype-set-default-discovery.md
datatype-set-description-discovery.md
```

Version allocation is cross-domain and owned by `version-allocation.md`.

## ObjectTemplate — ACTIVE INPUT

```text
objecttemplate-create-discovery.md
objecttemplate-create-next-discovery.md
objecttemplate-delete-draft-discovery.md
objecttemplate-delete-lineage-discovery.md
objecttemplate-deprecate-discovery.md
objecttemplate-get-effective-schema-discovery.md
objecttemplate-get-lineage-discovery.md
objecttemplate-get-version-discovery.md
objecttemplate-list-lineages-discovery.md
objecttemplate-list-versions-discovery.md
objecttemplate-publish-discovery.md
objecttemplate-relationship-capabilities-discovery.md
objecttemplate-revise-discovery.md
objecttemplate-set-default-discovery.md
objecttemplate-set-description-discovery.md
objecttemplate-clear-default-discovery.md
```

Support/handoff:

```text
objecttemplate-validation-loader-handoff.md
```

## RelationshipDefinition — REVIEWED BASELINE / ARCHITECTURE CLOSING PENDING

### [`relationshipdefinition.md`](relationshipdefinition.md) — SPINE / REVIEWED BASELINE / single family owner

This is the sole active M4 WIP owner for the RelationshipDefinition model plane.

It now consolidates:

```text
4 GET capabilities
9 retained mutations
1 removed mutation: RENAME
stable compact Definition semantics
RelationshipDefinitionVersion/property authoring and history
logical persistence and ownership
relationship_definition_space responsibility matrix
route-local data paths and cost direction
immutable exact-RDV cache boundary
RDV -> DTV lifetime/lifecycle distinctions
default-resolution and committed-history concurrency invariants
explicit physical/concurrency architecture handoffs
```

Former semantic-intent, operation-specific discovery and temporary consolidation files have been absorbed and removed; Git history remains the historical record.

Current reviewed direction includes:

```text
NO autonomous RelationshipResolution / resolution_id
stable semantic names and explicit symmetry
compact authored A/B topology without synthetic canonicalization
factored current applicability on Definition detail
global exact-template semantic-cell single ownership
relationship_definition_space as Definition-owned derived closure
shared monotonic/no-reuse exact-version allocation
ordered properties without public position
DRAFT revision / expected_revision semantics
CREATE_NEXT cache-first immutable snapshot cloning
REVISE datatype-lineage-only committed-history continuity
PUBLISH full DTV admission, first-default claim and post-commit cache publication
separate idempotent SET_DEFAULT / CLEAR_DEFAULT
DEPRECATE current-default protection without factual-reference blocking
DELETE_DRAFT owned declaration cleanup without space/allocator changes
root DELETE relational blocker arbitration and owned aggregate cleanup
bounded diagnostics and no response-only reload work
```

Still open only as architecture/physical realization or cross-family handoff:

```text
final SQL/DDL and PK/FK/UNIQUE/index choices
lock/gate/wait/retry/deadlock realization
ObjectTemplate ancestry-growth maintenance protocol
DataType reverse-consumer realization
factual Relationship CREATE Definition-selector choice
cache implementation topology/capacity/eviction
migration/backfill from autonomous Resolution state
verification design
```

Version allocation remains owned by `version-allocation.md`; general principles remain owned by `general-domain-principles.md`.

# 6. Factual Relationship — REVIEWED BASELINE / ARCHITECTURE CLOSING PENDING

### [`relationship.md`](relationship.md) — SPINE / REVIEWED BASELINE / single factual Relationship WIP owner

`relationship.md` is the single factual Relationship WIP owner. Former temporary continuations have been losslessly absorbed and removed.

The post-definition full sweep covers exactly the M4 factual capabilities:

```text
CREATE
GET global detail by relationship_id
GET Object-scoped Relationship collection
DATA_CHANGE
SCHEMA_CHANGE
DELETE
```

Current reviewed data-plane direction is:

```text
relationships
    id
    relationship_definition_id
    relationship_definition_version
    properties
    revision

runtime_relationship_cells
    relationship_id
    from_object_id
    name
    to_object_id

semantic-cell identity/uniqueness
    (from_object_id, name, to_object_id)
    -> at most one current factual Relationship owner

semantic name
    -> stable runtime semantic state
    -> no autonomous RelationshipResolution / resolution_id

factual self-reference
    -> forbidden
    -> from_object_id != to_object_id
```

Key reviewed route-level conclusions include:

```text
global GET
    -> complete lossless perspectives[]
    -> one authoritative PostgreSQL statement
    -> no model-plane recertification

Object-scoped GET
    -> 1:1 runtime-cell projection
    -> exact name filter
    -> keyset (name, to_object_id)
    -> semantic-cell B-tree reused for navigation

CREATE
    -> required oriented name/from/to semantics
    -> exact/default RDV selection
    -> PUBLISHED-only new binding
    -> immutable exact-RDV validation cache
    -> semantic-cell uniqueness conflict authority
    -> atomic root + complete runtime closure + CREATED lifecycle
    -> final Definition-selection request shape still architecture-closing

DATA_CHANGE
    -> immutable exact-RDV semantic cache
    -> relationships.revision freshness
    -> no new model-plane admission

SCHEMA_CHANGE
    -> exact SOURCE/TARGET pair
    -> numeric version direction has no migration meaning
    -> exact-pair MigrationPlan
    -> lossless conditional LIST -> SCALAR
    -> revision freshness + final TARGET PUBLISHED admission

DELETE
    -> explicit root-only DELETE
    -> owned runtime cells removed by FK ON DELETE CASCADE
    -> no closure recertification
    -> no DELETE revision protocol
    -> one-business-statement target + atomic lifecycle
```

Remaining architecture-closing items include at least:

```text
C-REL-26
    final CREATE request choice:
        Candidate A -> explicit relationship_definition_id
        Candidate B -> derive owning Definition from admitted semantic cell

C-REL-22
    revalidate optional relationship_fact_conflict owner detail
    against the final efficient arbitration path

final relational DDL
    relationships.revision
    runtime_relationship_cells PK/UNIQUE/FKs/CASCADE
    physical indexes

final cache realization
    immutable exact RDV semantics
    migration plans

final concurrency realization
    lock/wait/FK/UNIQUE arbitration
    retry/rendezvous/deadlock proof

final lifecycle physical carriers
    coherent Object canonical-name observations
    batch persistence/decoding

EXPLAIN/BUFFERS/storage/JSONB/WAL/latency/contention evidence
```

These are architecture/physical decisions and do not reopen route-local factual discovery merely to choose a mechanism. A material new model-plane semantic dependency remains a valid targeted reopen trigger.

Global Relationship discovery/query remains deferred to M5 Search API. Object-scoped single-Relationship detail remains unnecessary absent a new caller requirement. Endpoint reassignment/repointing remains DELETE + CREATE with a new factual identity.

# 7. Lifecycle — OPEN HISTORICAL/AUDIT FAMILY

Lifecycle is not current authoritative Object/Relationship data-plane state. It is historical/audit state with its own APIs, persistence and read projections.

Its family review remains open, but that open work does **not** mean that the current-state data-plane sweep is incomplete.

Current Lifecycle discovery inputs:

```text
object-lifecycle-read-discovery.md
lifecycle-list-detail-api-discovery.md
lifecycle-summary-data-path-discovery.md
```

Reviewed Object and factual Relationship mutation owners provide the operation-owned lifecycle inputs that the Lifecycle pass must consume rather than redefine.

Object baseline inputs include:

```text
RENAME
    -> exact canonical_name transition

DATA_CHANGE
    -> exact binding context + changed-property delta

SCHEMA_CHANGE
    -> exact binding transition + actual changed-property delta

ATTACH / DETACH
    -> exact ownership-edge semantic identity
    -> required coherent historical Object display metadata
    -> one event per real edge transition

Object CREATE / DELETE
    -> broader creation/deletion snapshot where operation responsibility justifies it
```

Factual Relationship baseline inputs include:

```text
RELATIONSHIP_CREATED
    before_state = null
    after_state  = { relationship_definition_version, properties }

RELATIONSHIP_DATA_CHANGE
    before/after exact factual snapshots
    same exact version

RELATIONSHIP_SCHEMA_CHANGE
    before/after exact factual snapshots
    before.version != after.version
    no numeric direction meaning

RELATIONSHIP_DELETED
    before_state = { relationship_definition_version, properties }
    after_state  = null

Relationship event fan-out
    -> one event row per persisted runtime semantic cell
    -> coherent historical Object canonical-name observations
    -> revision excluded from historical factual state
```

The Lifecycle pass owns final collection/detail DTOs, discriminated event-detail carriers, persistence decoding/read paths, summary-vs-detail payload boundaries and its own physical/read optimization handoff.

# 8. Source-material cleanup notes

Former route-specific Object WIP families and focused component/SCHEMA_CHANGE source files were removed after their lossless absorption into reviewed Object owners. Git history remains historical evidence.

The factual Relationship temporary continuation files were likewise removed after the ordered checkpoints through `C-REL-36` were consolidated into `relationship.md`.

RelationshipDefinition distributed discovery files remain in place while `relationshipdefinition.md` is the active family owner. They are retained as operation-specific evidence until the family review is complete enough for a later consolidation/cleanup decision.

Source material is evidence only. If it conflicts with a reviewed owner/general principle, revalidate explicitly rather than treating the source as authority.

# 9. Maintenance rules

When a new WIP is created:

```text
1. classify navigation role
2. if it participates in current review, classify review state
3. do not imply completion merely by indexing it
```

When a review target closes:

```text
1. complete the route/owner full sweep
2. perform lossless consolidation/comparison
3. remove or demote superseded source material only when safe
4. promote the current owner/support to REVIEWED BASELINE
5. advance ACTIVE REVIEW FRONTIER
6. update this index
```

If a reviewed assumption is materially reopened:

```text
mark the affected topic/owner as ACTIVE REVIEW FRONTIER
state the reopened boundary
retain unaffected reviewed findings where ownership permits
```

If SOURCE MATERIAL conflicts with a SPINE owner or ratified general principle:

```text
DO NOT silently choose one
DO NOT infer a resolution
revalidate the specific point explicitly
record the result in the correct owner
```

# 10. Current-state precedence

Use this order to reconstruct M4 today:

```text
repository governance + M4 status
    -> interpretation boundary

general-domain-principles.md
    -> ratified cross-domain principles

version-allocation.md
    -> shared numeric allocation semantics

cross-operation reviewed owner when relevant
    -> e.g. object-revision.md / object-components-persistence.md

current family/topic owner
    -> reviewed baseline or active review frontier

ACTIVE INPUT set where no owner is consolidated

SUPPORT / HANDOFF

SOURCE MATERIAL
    -> evidence/explicit revalidation only
```

Within one ordered family owner, later explicit ratifications supersede earlier candidate/history passages where they conflict. This is particularly relevant to `relationship.md`, where `C-REL-27` and `C-REL-35` supersede earlier root/self-loop snapshots.

For the current RelationshipDefinition baseline, `relationshipdefinition.md` is the sole active family owner; former semantic-intent and distributed operation notes remain available only through Git history.

Review-state classification never changes topic ownership; it states whether the owner is safe to reuse as a closed baseline for subsequent review work.

## Completeness convention

Explicit filename lists and filename-pattern groups in this index both count as represented working sets. A WIP file outside those represented sets should not be assumed to contribute to current M4 state merely because it exists in the directory. If it becomes relevant again, add/reclassify it explicitly.
